"""The /lavi command handler, independent of NoneBot matchers."""

from .config import TextConfig
from .render import render_answer, render_detailed, render_unknown_algorithm
from .decision import decide, parse_invocation
from .protocol import Selector, capture_context
from .selector import UnknownAlgorithmError, build_selector, available_algorithms


def _available_choices() -> tuple[str, ...]:
    return tuple(
        f"{algorithm.name}（{algorithm.label}）" for algorithm in available_algorithms()
    )


def handle_lavi(
    arguments: str,
    *,
    selector: Selector,
    detailed: bool = False,
    text: TextConfig | None = None,
) -> str:
    """Resolve an optional per-command algorithm and render one decision."""
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

    decision = decide(
        request.text,
        context=capture_context(),
        selector=selector,
        trace=detailed,
        options=(text.affirmative, text.negative),
    )
    if not detailed:
        return render_answer(decision.answer, decider=decision.display_name, text=text)
    return render_detailed(
        decision.answer,
        decider=decision.display_name,
        operator_count=decision.operator_count,
        steps=decision.steps,
        text=text,
    )
