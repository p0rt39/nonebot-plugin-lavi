"""Parse ``/rawtell`` arguments and orchestrate one decision."""

from .protocol import Selector, DecisionContext

DEFAULT_OPTIONS = ("是", "否")


def parse_options(arguments: str) -> tuple[str, str]:
    """Return the two texts ``decide`` may reply with.

    Exactly two whitespace-separated fields are kept verbatim and in order.
    Any other count is a single yes/no question: the wording is discarded and
    the replies are ``"是"``/``"否"``. Quotes are not interpreted, nothing is
    deduplicated, and case/punctuation are preserved.
    """
    parts = arguments.split(maxsplit=2)
    if len(parts) == 2:
        return parts[0], parts[1]
    return DEFAULT_OPTIONS


def decide(arguments: str, *, context: DecisionContext, selector: Selector) -> str:
    """Select a calculator once, evaluate it once, and return its option.

    ``selector`` and the calculator it returns both receive ``context`` as-is;
    nothing is sampled here. Errors raised by either callable propagate.
    """
    affirmative, negative = parse_options(arguments)
    calculator = selector(context)
    return affirmative if calculator(context) else negative
