"""Thirteen-operator trial by a principal mask and a quorum vote.

Each 64-bit operator is split into a high 32-bit principal share and a low
32-bit ballot. The 13 principal shares elect a single 32-bit principal mask by
bitwise majority; the mask then interrogates every ballot through an
inner-product parity. Seven or more affirmative ballots answer True.

Principal shares and ballots use disjoint bit fields, so, conditional on the
principal, the 13 ballots are independent fair bits. With 13 votes the quorum
is exactly 50/50; sharing bits between the two roles would not preserve that
guarantee.
"""

from collections.abc import Sequence

from ..protocol import (
    OPERATOR_COUNT,
    Algorithm,
    Explanation,
    DecisionContext,
    derive_algorithm_operators,
)

NAME = "trial"
VERSION = 1
WEIGHT = 1

PRINCIPAL_BITS = 32
BALLOT_BITS = 32
BALLOT_MASK = (1 << BALLOT_BITS) - 1
QUORUM = OPERATOR_COUNT // 2 + 1


def _validate_operator(operator: int) -> int:
    if not 0 <= operator < 1 << (PRINCIPAL_BITS + BALLOT_BITS):
        raise ValueError("operator must be a 64-bit unsigned integer")
    return operator


def split_operator(operator: int) -> tuple[int, int]:
    """Split one 64-bit operator into its principal share and ballot."""
    operator = _validate_operator(operator)
    return operator >> BALLOT_BITS, operator & BALLOT_MASK


def principal(operators: Sequence[int]) -> int:
    """Return the bitwise-majority principal mask for the 13 operators.

    A zero majority is replaced with one so the mask is never degenerate.
    """
    if len(operators) != OPERATOR_COUNT:
        raise ValueError(f"expected {OPERATOR_COUNT} operators")
    shares = [split_operator(operator)[0] for operator in operators]
    mask = 0
    for bit in range(PRINCIPAL_BITS):
        ones = sum((share >> bit) & 1 for share in shares)
        if ones >= QUORUM:
            mask |= 1 << bit
    return mask or 1


def vote(mask: int, ballot: int) -> int:
    """Return one ballot's inner-product parity against the principal mask."""
    if not 0 < mask < 1 << PRINCIPAL_BITS:
        raise ValueError("mask must be a non-zero 32-bit unsigned integer")
    if not 0 <= ballot <= BALLOT_MASK:
        raise ValueError("ballot must be a 32-bit unsigned integer")
    return (mask & ballot).bit_count() & 1


def verdict(votes: Sequence[int]) -> bool:
    """Return whether at least seven of the thirteen votes are affirmative."""
    if len(votes) != OPERATOR_COUNT:
        raise ValueError(f"expected {OPERATOR_COUNT} votes")
    if any(vote not in (0, 1) for vote in votes):
        raise ValueError("vote must be 0 or 1")
    return sum(votes) >= QUORUM


def _principal_and_votes(operators: Sequence[int]) -> tuple[int, tuple[int, ...]]:
    mask = principal(operators)
    votes = tuple(vote(mask, split_operator(operator)[1]) for operator in operators)
    return mask, votes


def decide(operators: Sequence[int]) -> bool:
    """Run the principal/ballot vote over one set of 13 operators."""
    _, votes = _principal_and_votes(operators)
    return verdict(votes)


def _operators(context: DecisionContext) -> tuple[int, ...]:
    return derive_algorithm_operators(
        context,
        name=NAME,
        version=VERSION,
        stage="operators",
        count=OPERATOR_COUNT,
    )


def calculate(context: DecisionContext) -> bool:
    """Derive 13 operators and decide by their 13-vote quorum."""
    _, votes = _principal_and_votes(_operators(context))
    return verdict(votes)


def explain(context: DecisionContext) -> Explanation:
    """Return the principal mask, all votes and the quorum verdict."""
    mask, votes = _principal_and_votes(_operators(context))
    affirmative = verdict(votes)
    steps = (
        f"主算子：0x{mask:08X}",
        f"选票：{' '.join(str(ballot) for ballot in votes)}",
        f"肯定票：{sum(votes)}/{OPERATOR_COUNT}"
        f"（阈值 {QUORUM}）→ {'肯定' if affirmative else '否定'}",
    )
    return Explanation(affirmative, steps)


ALGORITHM = Algorithm(
    name=NAME,
    version=VERSION,
    weight=WEIGHT,
    calculate=calculate,
    display_name="裁判",
    explain=explain,
)
