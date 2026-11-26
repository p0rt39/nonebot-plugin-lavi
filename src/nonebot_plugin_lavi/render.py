"""Render decision answers and detailed traces as adapter-safe text."""

from collections.abc import Sequence

from .config import TextConfig
from .protocol import Decision, DecisionRecord

_DEFAULT_TEXT = TextConfig()


def _single_line(text: str) -> str:
    return " ".join(text.split())


def render_unknown_algorithm(
    requested: str,
    *,
    available: Sequence[str],
    text: TextConfig = _DEFAULT_TEXT,
) -> str:
    """Return the usable algorithm names after an unknown selection."""
    options = "、".join(available)
    return "\n".join(
        (
            text.unknown_algorithm.format(requested=_single_line(requested)),
            text.available_algorithms.format(available=options),
        )
    )


def render_answer(
    answer: str,
    *,
    decider: str,
    text: TextConfig = _DEFAULT_TEXT,
) -> str:
    """Return the ritual heading and a clearly labelled result."""
    return "\n".join(
        (
            text.header.format(decider=_single_line(decider)),
            text.result.format(answer=_single_line(answer)),
        )
    )


def render_detailed(
    answer: str,
    *,
    decider: str,
    operator_count: int,
    steps: tuple[str, ...] = (),
    text: TextConfig = _DEFAULT_TEXT,
) -> str:
    """Separate concise text from the operator count and optional steps."""
    lines = [
        render_answer(answer, decider=decider, text=text),
        "",
        text.operator_count.format(operator_count=operator_count),
    ]
    if steps:
        if text.steps_header:
            lines.append(text.steps_header)
        lines.extend(_single_line(step) for step in steps)
    return "\n".join(lines)


def render_review(
    record: DecisionRecord,
    *,
    replay: Decision | None,
    status: str,
    text: TextConfig = _DEFAULT_TEXT,
) -> str:
    """Return one original record, an optional replay and the check verdict.

    ``replay`` is omitted when the recorded algorithm version is unavailable
    or its replay raised; the original record is always shown in full.
    """
    position = 1 if record.affirmative_wins else 2
    answer = record.options[position - 1]
    options = " / ".join(
        f"{index}「{_single_line(option)}」"
        for index, option in enumerate(record.options, start=1)
    )
    algorithm = _single_line(
        f"{record.display_name}（{record.algorithm} v{record.algorithm_version}）"
    )
    lines = [
        text.record_id.format(record_id=str(record.record_id)),
        text.record_time.format(timestamp=record.context.timestamp.isoformat()),
        text.record_algorithm.format(algorithm=algorithm),
        text.record_options.format(options=options),
        text.record_result.format(result=f"第 {position} 项「{_single_line(answer)}」"),
        text.record_count.format(operator_count=record.operator_count),
    ]
    if replay is not None:
        lines.append("")
        lines.append(
            render_detailed(
                replay.answer,
                decider=replay.display_name,
                operator_count=replay.operator_count,
                steps=replay.steps,
                text=text,
            )
        )
    lines.append(status)
    return "\n".join(lines)
