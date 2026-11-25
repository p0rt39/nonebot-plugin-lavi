"""Obi / Ifa cowrie-shell decision algorithm.

A round casts Obi once. Eyeife sends that round straight to Ifa. Otherwise a
second Obi confirms the first: if the second is Eyeife, the first Obi decides;
if it is not, Ifa must answer True for the first Obi to decide. A False Ifa
restarts the round with freshly derived marks.
"""

from collections.abc import Sequence

from ..protocol import Algorithm, DecisionContext, derive_algorithm_bits

NAME = "obi-ifa"
VERSION = 2
WEIGHT = 1

OBI_SHELLS = 4
IFA_MARKS = 8

ALAFIA = "Alafia"
ETAWA = "Etawa"
EYEIFE = "Eyeife"
OKANA = "Okana"
OYEKUN = "Oyekun"

# The five Obi letters in ascending order of mouth-up cowries.
OBI_LETTERS = (OYEKUN, OKANA, EYEIFE, ETAWA, ALAFIA)


def cast_obi(marks: Sequence[int]) -> int:
    """Return how many of four sampled cowries land mouth-up.

    Each mark is one context-derived bit, so the count follows the binomial
    distribution 1:4:6:4:1 without a separate PRNG.
    """
    if len(marks) != OBI_SHELLS:
        raise ValueError(f"expected {OBI_SHELLS} cowrie marks")
    return sum(mark & 1 for mark in marks)


def obi_letter(open_count: int) -> str:
    """Return the Obi letter for a number of mouth-up cowries."""
    if not 0 <= open_count <= OBI_SHELLS:
        raise ValueError(f"open_count must be between 0 and {OBI_SHELLS}")
    return OBI_LETTERS[open_count]


def obi_verdict(open_count: int) -> bool | None:
    """Map an Obi letter to yes, no, or ``None`` for Eyeife's confirmation.

    Alafia and Etawa carry the affirmative side (Etawa conditionally); Okana
    and Oyekun carry the negative side. Eyeife is the perfectly balanced cast
    and is resolved by Ifa.
    """
    letter = obi_letter(open_count)
    if letter in (ALAFIA, ETAWA):
        return True
    if letter in (OKANA, OYEKUN):
        return False
    return None


def cast_ifa(marks: Sequence[int]) -> int:
    """Assemble one eight-mark Odu from sampled cowrie marks."""
    if len(marks) != IFA_MARKS:
        raise ValueError(f"expected {IFA_MARKS} cowrie marks")
    odu = 0
    for index, mark in enumerate(marks):
        odu |= (mark & 1) << index
    return odu


def ifa_verdict(odu: int) -> bool:
    """Reduce an Odu to a bit by the parity of its single marks."""
    if not 0 <= odu < 1 << IFA_MARKS:
        raise ValueError(f"odu must be an {IFA_MARKS}-bit unsigned integer: {odu}")
    return odu.bit_count() % 2 == 1


def _derive_marks(
    context: DecisionContext, *, stage: str, count: int
) -> tuple[int, ...]:
    return derive_algorithm_bits(
        context,
        name=NAME,
        version=VERSION,
        stage=stage,
        count=count,
    )


def calculate(context: DecisionContext) -> bool:
    """Resolve one round, restarting with fresh marks when Ifa rejects it."""
    attempt = 0
    while True:
        first_open = cast_obi(
            _derive_marks(
                context,
                stage=f"obi:first:{attempt}",
                count=OBI_SHELLS,
            )
        )
        first_verdict = obi_verdict(first_open)
        if first_verdict is None:
            return ifa_verdict(
                cast_ifa(
                    _derive_marks(
                        context,
                        stage=f"ifa:{attempt}",
                        count=IFA_MARKS,
                    )
                )
            )

        second_open = cast_obi(
            _derive_marks(
                context,
                stage=f"obi:second:{attempt}",
                count=OBI_SHELLS,
            )
        )
        if obi_letter(second_open) == EYEIFE:
            return first_verdict

        if ifa_verdict(
            cast_ifa(
                _derive_marks(
                    context,
                    stage=f"ifa:{attempt}",
                    count=IFA_MARKS,
                )
            )
        ):
            return first_verdict

        attempt += 1


ALGORITHM = Algorithm(
    name=NAME,
    version=VERSION,
    weight=WEIGHT,
    calculate=calculate,
)
