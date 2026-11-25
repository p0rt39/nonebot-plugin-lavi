"""The /rawtell command handler, independent of NoneBot matchers."""

from .render import render_answer, render_detailed
from .decision import decide
from .protocol import Selector, capture_context


def handle_rawtell(
    arguments: str, *, selector: Selector, detailed: bool = False
) -> str:
    """Capture one context and return the rendered reply for the arguments."""
    decision = decide(
        arguments,
        context=capture_context(),
        selector=selector,
        trace=detailed,
    )
    if not detailed:
        return render_answer(decision.answer, decider=decision.display_name)
    return render_detailed(
        decision.answer,
        decider=decision.display_name,
        operator_count=decision.operator_count,
        steps=decision.steps,
    )
