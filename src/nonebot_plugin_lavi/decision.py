"""Parse ``/lavi`` arguments and orchestrate one decision."""

from dataclasses import dataclass

from .protocol import Decision, Selector, DecisionContext, count_operators

DEFAULT_OPTIONS = ("是", "否")


@dataclass(frozen=True, slots=True)
class ParsedInvocation:
    """One ``/lavi`` invocation split into an optional algorithm selector."""

    algorithm: str | None
    text: str
    require_algorithm: bool = False


def parse_invocation(arguments: str) -> ParsedInvocation:
    """Split arguments into an optional algorithm selector and option text.

    A single whitespace-separated field is an algorithm selector and leaves
    the yes/no question empty. Exactly three fields select an algorithm and
    keep the last two as candidates; an unknown name there is a user error.
    Every other field count (including zero and four or more) keeps the
    configured selector and the original option parsing. Whitespace in the
    returned option text is collapsed; ``parse_options`` only looks at
    fields, so this is equivalent.
    """
    parts = arguments.split()
    if len(parts) == 1:
        return ParsedInvocation(algorithm=parts[0], text="")
    if len(parts) == 3:
        return ParsedInvocation(
            algorithm=parts[0],
            text=" ".join(parts[1:]),
            require_algorithm=True,
        )
    return ParsedInvocation(algorithm=None, text=arguments)


def parse_options(
    arguments: str,
    *,
    options: tuple[str, str] = DEFAULT_OPTIONS,
) -> tuple[str, str]:
    """Return the two texts ``decide`` may reply with.

    Exactly two whitespace-separated fields are kept verbatim and in order.
    Any other count is a single yes/no question: the wording is discarded and
    ``options`` supplies the replies, defaulting to ``"是"``/``"否"``. Quotes
    are not interpreted, nothing is deduplicated, and case/punctuation are
    preserved.
    """
    parts = arguments.split(maxsplit=2)
    if len(parts) == 2:
        return parts[0], parts[1]
    return options


def decide(
    arguments: str,
    *,
    context: DecisionContext,
    selector: Selector,
    trace: bool = False,
    options: tuple[str, str] = DEFAULT_OPTIONS,
) -> Decision:
    """Select one algorithm, evaluate it once, and return its answer.

    ``selector`` and the algorithm both receive ``context`` as-is; nothing is
    sampled here. ``operator_count`` counts only the 64-bit operators derived
    by the selected algorithm, not those used to select it. When ``trace`` is
    true and the algorithm provides ``explain``, the same single evaluation
    also returns its calculation steps. Errors raised by either callable
    propagate.
    """
    affirmative, negative = parse_options(arguments, options=options)
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
