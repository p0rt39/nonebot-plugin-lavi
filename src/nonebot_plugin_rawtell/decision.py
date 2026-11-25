"""Parse ``/rawtell`` arguments and orchestrate one decision."""

from .protocol import Decision, Selector, DecisionContext, count_operators

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


def decide(
    arguments: str,
    *,
    context: DecisionContext,
    selector: Selector,
    trace: bool = False,
) -> Decision:
    """Select one algorithm, evaluate it once, and return its answer.

    ``selector`` and the algorithm both receive ``context`` as-is; nothing is
    sampled here. ``operator_count`` counts only the 64-bit operators derived
    by the selected algorithm, not those used to select it. When ``trace`` is
    true and the algorithm provides ``explain``, the same single evaluation
    also returns its calculation steps. Errors raised by either callable
    propagate.
    """
    affirmative, negative = parse_options(arguments)
    algorithm = selector(context)
    with count_operators() as tally:
        if trace and algorithm.explain is not None:
            explanation = algorithm.explain(context)
            affirmative_wins = explanation.answer
            steps = explanation.steps
        else:
            affirmative_wins = algorithm.calculate(context)
            steps = ()
    return Decision(
        answer=affirmative if affirmative_wins else negative,
        algorithm=algorithm.name,
        display_name=algorithm.label,
        operator_count=tally.count,
        steps=steps,
    )
