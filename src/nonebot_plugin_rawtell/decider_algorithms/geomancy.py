"""Geomantic shield-chart decision algorithm."""

from dataclasses import dataclass
from collections.abc import Sequence

from ..protocol import (
    Algorithm,
    Explanation,
    DecisionContext,
    derive_algorithm_bits,
)

NAME = "geomancy"
VERSION = 1
WEIGHT = 1

MOTHER_COUNT = 4
FIGURE_BITS = 4
CAST_BITS = MOTHER_COUNT * FIGURE_BITS

# Patterns read from the top (Fire) line to the bottom (Earth) line, where 1
# is a single/active line and 0 a double/passive line. The flag is the
# traditional stable/mobile quality: in a simple yes/no reading a stable Judge
# answers affirmatively and a mobile Judge negatively.
FIGURES: dict[int, tuple[str, bool]] = {
    0b1111: ("Via", False),
    0b0000: ("Populus", True),
    0b0110: ("Coniunctio", False),
    0b1001: ("Carcer", True),
    0b0011: ("Fortuna Maior", True),
    0b1100: ("Fortuna Minor", False),
    0b0101: ("Acquisitio", True),
    0b1010: ("Amissio", False),
    0b1000: ("Laetitia", False),
    0b0001: ("Tristitia", True),
    0b0010: ("Albus", True),
    0b0100: ("Rubeus", False),
    0b1011: ("Puella", True),
    0b1101: ("Puer", False),
    0b0111: ("Caput Draconis", True),
    0b1110: ("Cauda Draconis", False),
}


@dataclass(frozen=True, slots=True)
class Chart:
    """The four Mothers and every figure derived from them."""

    mothers: tuple[int, int, int, int]
    daughters: tuple[int, int, int, int]
    nieces: tuple[int, int, int, int]
    right_witness: int
    left_witness: int
    judge: int


def _validate_figure(figure: int) -> int:
    if not 0 <= figure < 1 << FIGURE_BITS:
        raise ValueError(f"figure must be a 4-bit unsigned integer: {figure}")
    return figure


def _validated_mothers(mothers: Sequence[int]) -> tuple[int, int, int, int]:
    if len(mothers) != MOTHER_COUNT:
        raise ValueError(f"expected {MOTHER_COUNT} mothers")
    return (
        _validate_figure(mothers[0]),
        _validate_figure(mothers[1]),
        _validate_figure(mothers[2]),
        _validate_figure(mothers[3]),
    )


def cast_mothers(marks: Sequence[int]) -> tuple[int, int, int, int]:
    """Assemble four four-line Mothers from sixteen sampled line marks.

    The first four marks are the first Mother's lines from top (Fire) to bottom
    (Earth), the next four are the second Mother, and so on. Each mark is one
    context-derived bit, so the cast is reproducible without a separate PRNG.
    """
    if len(marks) != CAST_BITS:
        raise ValueError(f"expected {CAST_BITS} line marks")
    mothers: list[int] = []
    for mother_index in range(MOTHER_COUNT):
        figure = 0
        for line in range(FIGURE_BITS):
            mark = marks[mother_index * FIGURE_BITS + line] & 1
            figure |= mark << (FIGURE_BITS - 1 - line)
        mothers.append(figure)
    return (mothers[0], mothers[1], mothers[2], mothers[3])


def derive_daughters(mothers: Sequence[int]) -> tuple[int, int, int, int]:
    """Transpose the four Mothers into the four Daughters."""
    first, second, third, fourth = _validated_mothers(mothers)
    sources = (first, second, third, fourth)
    daughters: list[int] = []
    for line in range(FIGURE_BITS):
        daughter = 0
        for column, mother in enumerate(sources):
            active = (mother >> (FIGURE_BITS - 1 - line)) & 1
            daughter |= active << (FIGURE_BITS - 1 - column)
        daughters.append(daughter)
    return (daughters[0], daughters[1], daughters[2], daughters[3])


def build_chart(mothers: Sequence[int]) -> Chart:
    """Derive the shield chart from four Mothers by line-wise XOR addition."""
    first, second, third, fourth = _validated_mothers(mothers)
    daughters = derive_daughters((first, second, third, fourth))
    nieces = (
        first ^ second,
        third ^ fourth,
        daughters[0] ^ daughters[1],
        daughters[2] ^ daughters[3],
    )
    right_witness = nieces[0] ^ nieces[1]
    left_witness = nieces[2] ^ nieces[3]
    judge = right_witness ^ left_witness
    if judge not in FIGURES:
        raise ValueError(f"derived Judge is not an even figure: {judge:#06b}")
    return Chart(
        mothers=(first, second, third, fourth),
        daughters=daughters,
        nieces=nieces,
        right_witness=right_witness,
        left_witness=left_witness,
        judge=judge,
    )


def judge_is_stable(judge: int) -> bool:
    """Return whether an even Judge is stable (affirmative) or mobile (negative)."""
    try:
        return FIGURES[judge][1]
    except KeyError:
        raise ValueError(f"not an even Judge figure: {judge:#06b}") from None


def _chart(context: DecisionContext) -> Chart:
    marks = derive_algorithm_bits(
        context,
        name=NAME,
        version=VERSION,
        stage="mothers",
        count=CAST_BITS,
    )
    return build_chart(cast_mothers(marks))


def _figure(value: int) -> str:
    name, _ = FIGURES[value]
    return f"{name}({value:04b})"


def calculate(context: DecisionContext) -> bool:
    """Cast a shield chart and answer from the Judge's stable/mobile quality."""
    return judge_is_stable(_chart(context).judge)


def explain(context: DecisionContext) -> Explanation:
    """Return the shield chart figures and the Judge's stable/mobile verdict."""
    chart = _chart(context)
    stable = judge_is_stable(chart.judge)
    steps = (
        f"四母：{' / '.join(_figure(figure) for figure in chart.mothers)}",
        f"四女：{' / '.join(_figure(figure) for figure in chart.daughters)}",
        f"四侄：{' / '.join(_figure(figure) for figure in chart.nieces)}",
        f"右见证：{_figure(chart.right_witness)}，"
        f"左见证：{_figure(chart.left_witness)}",
        f"裁判：{_figure(chart.judge)}，"
        f"{'稳定' if stable else '流动'} → {'肯定' if stable else '否定'}",
    )
    return Explanation(stable, steps)


ALGORITHM = Algorithm(
    name=NAME,
    version=VERSION,
    weight=WEIGHT,
    calculate=calculate,
    display_name="地占",
    explain=explain,
)
