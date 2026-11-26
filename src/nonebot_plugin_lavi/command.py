"""The ``/lavi`` and ``/lavi-review`` handlers, independent of NoneBot matchers."""

import logging
from uuid import UUID, uuid4

from .config import TextConfig
from .render import (
    render_answer,
    render_review,
    render_detailed,
    render_unknown_algorithm,
)
from .storage import HistoryStore, DuplicateRecordId, HistoryUnavailable
from .decision import decide, parse_invocation
from .protocol import (
    Decision,
    Selector,
    Algorithm,
    DecisionRecord,
    DecisionContext,
    capture_context,
)
from .selector import UnknownAlgorithmError, build_selector, available_algorithms
from .decider_algorithms import ALGORITHMS

logger = logging.getLogger(__name__)


def _available_choices() -> tuple[str, ...]:
    return tuple(
        f"{algorithm.name}（{algorithm.label}）" for algorithm in available_algorithms()
    )


def _record_for(
    record_id: UUID,
    context: DecisionContext,
    decision: Decision,
) -> DecisionRecord:
    return DecisionRecord(
        record_id=record_id,
        context=context,
        options=decision.options,
        algorithm=decision.algorithm,
        algorithm_version=decision.algorithm_version,
        display_name=decision.display_name,
        affirmative_wins=decision.affirmative_wins,
        operator_count=decision.operator_count,
    )


async def handle_lavi(
    arguments: str,
    *,
    history: HistoryStore,
    selector: Selector,
    detailed: bool = False,
    text: TextConfig | None = None,
) -> str:
    """Resolve an optional per-command algorithm, decide, and persist the result."""
    text = text or TextConfig()
    request = parse_invocation(arguments)
    if request.algorithm is not None:
        try:
            selector = build_selector(name=request.algorithm)
        except UnknownAlgorithmError:
            if request.require_algorithm:
                return render_unknown_algorithm(
                    request.algorithm,
                    available=_available_choices(),
                    text=text,
                )

    context = capture_context()
    decision = decide(
        request.text,
        context=context,
        selector=selector,
        trace=detailed,
        options=(text.affirmative, text.negative),
    )
    record = _record_for(uuid4(), context, decision)
    notice: str | None = None
    if history.limit <= 0:
        notice = text.history_disabled_decision
    else:
        while True:
            try:
                await history.append(record)
            except DuplicateRecordId:
                record = _record_for(uuid4(), context, decision)
                continue
            except HistoryUnavailable:
                logger.warning("LaVI could not persist a decision record")
                notice = text.history_write_failed
            break

    if detailed:
        reply = render_detailed(
            decision.answer,
            decider=decision.display_name,
            operator_count=decision.operator_count,
            steps=decision.steps,
            text=text,
        )
    else:
        reply = render_answer(
            decision.answer,
            decider=decision.display_name,
            text=text,
        )
    lines = [reply, text.record_id.format(record_id=str(record.record_id))]
    if notice is not None:
        lines.append(notice)
    return "\n".join(lines)


def _parse_record_id(arguments: str) -> UUID | None:
    candidate = arguments.strip()
    if not candidate or any(character.isspace() for character in candidate):
        return None
    try:
        parsed = UUID(candidate)
    except ValueError:
        return None
    if parsed.version != 4 or str(parsed) != candidate.lower():
        return None
    return parsed


def _find_algorithm(name: str, version: int) -> Algorithm | None:
    for algorithm in ALGORITHMS:
        if algorithm.name == name and algorithm.version == version:
            return algorithm
    return None


async def handle_review(
    arguments: str,
    *,
    history: HistoryStore,
    text: TextConfig | None = None,
) -> str:
    """Look up one record by full ID and replay it without sampling again."""
    text = text or TextConfig()
    record_id = _parse_record_id(arguments)
    if record_id is None:
        return text.review_usage
    if history.limit <= 0:
        return text.history_disabled
    try:
        record = await history.get(record_id)
    except HistoryUnavailable:
        logger.warning("LaVI could not read the decision history")
        return text.history_unavailable
    if record is None:
        return text.record_missing

    algorithm = _find_algorithm(record.algorithm, record.algorithm_version)
    if algorithm is None:
        return render_review(
            record,
            replay=None,
            status=text.review_version_unavailable,
            text=text,
        )
    try:
        replay = decide(
            "",
            context=record.context,
            options=record.options,
            selector=lambda _context: algorithm,
            trace=True,
        )
    except Exception:
        logger.warning(
            "LaVI could not replay algorithm %s v%s",
            record.algorithm,
            record.algorithm_version,
        )
        return render_review(
            record,
            replay=None,
            status=text.review_failed,
            text=text,
        )

    matched = (
        replay.affirmative_wins == record.affirmative_wins
        and replay.operator_count == record.operator_count
    )
    return render_review(
        record,
        replay=replay,
        status=text.review_match if matched else text.review_mismatch,
        text=text,
    )
