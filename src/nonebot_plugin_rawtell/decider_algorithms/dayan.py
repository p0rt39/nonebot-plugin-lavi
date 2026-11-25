"""大衍筮法 (Dayan yarrow-stalk) decision algorithm.

The traditional procedure sets one of fifty stalks aside, then performs three
changes for each of six lines. The first change removes five stalks with
probability 3/4 or nine with 1/4; the second and third remove four or eight
stalks with probability 1/2 each. After three changes the remaining count is
24/28/32/36, yielding line values 6/7/8/9 with probabilities
1/16/5/16/7/16/3/16.

Those line values, the changed hexagram and the number of changing lines are
all skewed, so none of them can drive a fair binary answer directly. Yin/yang
polarity (6/8 versus 7/9), however, is exactly 8/16 each. This algorithm
therefore casts one primary hexagram and answers from the parity of its yang
lines: with six fair polarity bits, exactly half of the 64 primary hexagrams
answer True. Majority voting (22/64 for four or more yang lines) and
changed-hexagram readings (5/8 yin) are deliberately not used.
"""

from collections.abc import Sequence

from ..protocol import (
    Algorithm,
    Explanation,
    DecisionContext,
    derive_algorithm_bits,
)

NAME = "dayan"
VERSION = 1
WEIGHT = 1

STALKS = 50
SET_ASIDE = 1
ACTIVE_STALKS = STALKS - SET_ASIDE

LINE_COUNT = 6
CHANGES_PER_LINE = 3
FIRST_CHANGE_MARKS = 2
LATER_CHANGE_MARKS = 1
LATER_CHANGES = CHANGES_PER_LINE - 1
LINE_MARKS = FIRST_CHANGE_MARKS + LATER_CHANGES * LATER_CHANGE_MARKS
CAST_MARKS = LINE_COUNT * LINE_MARKS
LINE_NAMES = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")

OLD_YIN = 6
YOUNG_YANG = 7
YOUNG_YIN = 8
OLD_YANG = 9

# A two-bit value selects the first-change removal: 5 with probability 3/4 and
# 9 with probability 1/4. Later changes consume one bit each: 4 or 8.
FIRST_CHANGE_REMOVALS = (5, 5, 5, 9)
LATER_CHANGE_REMOVALS = (4, 8)


def first_change_removal(marks: Sequence[int]) -> int:
    """Return the stalks removed by the first of the three changes."""
    if len(marks) != FIRST_CHANGE_MARKS:
        raise ValueError(f"expected {FIRST_CHANGE_MARKS} first-change marks")
    choice = ((marks[0] & 1) << 1) | (marks[1] & 1)
    return FIRST_CHANGE_REMOVALS[choice]


def later_change_removal(mark: int) -> int:
    """Return the stalks removed by the second or third change."""
    return LATER_CHANGE_REMOVALS[mark & 1]


def line_changes(marks: Sequence[int]) -> tuple[int, int, int, int]:
    """Return the three removals and the remaining stalk count for one line."""
    if len(marks) != LINE_MARKS:
        raise ValueError(f"expected {LINE_MARKS} line marks")
    first = first_change_removal(marks[:FIRST_CHANGE_MARKS])
    second = later_change_removal(marks[FIRST_CHANGE_MARKS])
    third = later_change_removal(marks[FIRST_CHANGE_MARKS + LATER_CHANGE_MARKS])
    remaining = ACTIVE_STALKS - first - second - third
    return first, second, third, remaining


def cast_line(marks: Sequence[int]) -> int:
    """Cast one line value from its first-change and later-change marks."""
    _, _, _, remaining = line_changes(marks)
    line = remaining // 4
    if line not in (OLD_YIN, YOUNG_YANG, YOUNG_YIN, OLD_YANG):
        raise ValueError(f"derived invalid line value: {line}")
    return line


def cast_hexagram(marks: Sequence[int]) -> tuple[int, ...]:
    """Cast six line values, four marks each, in bottom-to-top order."""
    if len(marks) != CAST_MARKS:
        raise ValueError(f"expected {CAST_MARKS} cast marks")
    return tuple(
        cast_line(marks[offset : offset + LINE_MARKS])
        for offset in range(0, CAST_MARKS, LINE_MARKS)
    )


def is_yang(line: int) -> bool:
    """Return whether a line value is yang (7 or 9)."""
    if line not in (OLD_YIN, YOUNG_YANG, YOUNG_YIN, OLD_YANG):
        raise ValueError(f"invalid line value: {line}")
    return line in (YOUNG_YANG, OLD_YANG)


def yang_parity(lines: Sequence[int]) -> bool:
    """Return whether a primary hexagram has an odd number of yang lines."""
    return sum(is_yang(line) for line in lines) % 2 == 1


def _cast(context: DecisionContext) -> tuple[tuple[int, ...], tuple[int, ...]]:
    marks = derive_algorithm_bits(
        context,
        name=NAME,
        version=VERSION,
        stage="hexagram",
        count=CAST_MARKS,
    )
    return marks, cast_hexagram(marks)


def calculate(context: DecisionContext) -> bool:
    """Cast one hexagram and answer from the parity of its yang lines."""
    return yang_parity(_cast(context)[1])


def explain(context: DecisionContext) -> Explanation:
    """Return the line-by-line stalk removals and the yang parity verdict."""
    marks, lines = _cast(context)
    steps: list[str] = []
    for index, line in enumerate(lines):
        chunk = marks[index * LINE_MARKS : (index + 1) * LINE_MARKS]
        first, second, third, remaining = line_changes(chunk)
        polarity = "阳" if is_yang(line) else "阴"
        steps.append(
            f"{LINE_NAMES[index]}：去 {first}+{second}+{third}，"
            f"余 {remaining}，{remaining}÷4={line}（{polarity}）"
        )

    yang_count = sum(is_yang(line) for line in lines)
    affirmative = yang_parity(lines)
    steps.append(
        f"阳爻 {yang_count} 枚，奇偶：{'奇' if affirmative else '偶'} → "
        f"{'肯定' if affirmative else '否定'}"
    )
    return Explanation(affirmative, tuple(steps))


ALGORITHM = Algorithm(
    name=NAME,
    version=VERSION,
    weight=WEIGHT,
    calculate=calculate,
    display_name="大衍",
    explain=explain,
)
