"""The /rawtell command handler, independent of NoneBot matchers."""

from .decision import decide
from .protocol import Selector, capture_context


def handle_rawtell(arguments: str, *, selector: Selector) -> str:
    """Capture one context and return the reply for the command arguments."""
    return decide(arguments, context=capture_context(), selector=selector)
