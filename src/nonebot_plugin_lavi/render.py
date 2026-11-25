"""Render decision answers and detailed traces as adapter-safe text."""

from collections.abc import Sequence

from .config import TextConfig

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
