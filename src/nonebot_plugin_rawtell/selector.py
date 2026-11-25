"""Select one decision algorithm for a :class:`DecisionContext`."""

import hashlib
from collections.abc import Sequence

from .protocol import (
    OPERATOR_BITS,
    OPERATOR_COUNT,
    Selector,
    Algorithm,
    DecisionContext,
    derive_seed,
)
from .decider_algorithms import ALGORITHMS

RANDOM_SELECTION = "random"


def _enabled(algorithms: Sequence[Algorithm]) -> tuple[Algorithm, ...]:
    """Validate the registry and return enabled algorithms in stable order."""
    names = [algorithm.name for algorithm in algorithms]
    if len(names) != len(set(names)):
        raise ValueError("duplicate algorithm name")
    enabled = tuple(
        sorted(
            (algorithm for algorithm in algorithms if algorithm.weight > 0),
            key=lambda algorithm: algorithm.name,
        )
    )
    if not enabled:
        raise ValueError("at least one algorithm must have a positive weight")
    return enabled


def derive_operators(context: DecisionContext) -> tuple[int, ...]:
    """Derive 13 independent 64-bit operators from the decision context."""
    return tuple(
        derive_seed(context, purpose=f"selector:operator:{index}")
        for index in range(1, OPERATOR_COUNT + 1)
    )


def _msb_bit(value: int, position: int) -> int:
    """Return the 1-based bit at ``position`` counted from the 64-bit MSB."""
    return (value >> (OPERATOR_BITS - position)) & 1


def _lsb_bit(value: int, position: int) -> int:
    """Return the 1-based bit at ``position`` counted from the LSB."""
    return (value >> (position - 1)) & 1


def compose_omega(operators: Sequence[int]) -> int:
    """Compose the 26-bit ``omega`` from 13 64-bit operators.

    The upper 13 bits take operator ``i``'s ``i``-th bit from the MSB. The
    lower 13 bits take operator ``14 - i``'s ``i``-th bit from the LSB, so the
    second half reads the reverse diagonal.
    """
    if len(operators) != OPERATOR_COUNT:
        raise ValueError(f"expected {OPERATOR_COUNT} operators")

    omega = 0
    for position in range(1, OPERATOR_COUNT + 1):
        operator = operators[position - 1]
        if not 0 <= operator < 1 << OPERATOR_BITS:
            raise ValueError("operator must be a 64-bit unsigned integer")
        omega |= _msb_bit(operator, position) << (2 * OPERATOR_COUNT - position)
        reverse = operators[OPERATOR_COUNT - position]
        omega |= _lsb_bit(reverse, position) << (position - 1)
    return omega


def hash_omega(omega: int) -> int:
    """Hash the 26-bit ``omega`` into a 64-bit ``lambda``."""
    if not 0 <= omega < 1 << (2 * OPERATOR_COUNT):
        raise ValueError("omega must be a 26-bit unsigned integer")
    digest = hashlib.blake2b(
        omega.to_bytes(4, "big"),
        digest_size=8,
        person=b"rawtell",
    )
    return int.from_bytes(digest.digest(), "big")


def derive_lambda(context: DecisionContext) -> int:
    """Derive the selection value ``lambda`` from one decision context."""
    return hash_omega(compose_omega(derive_operators(context)))


def choose_algorithm(
    context: DecisionContext, algorithms: Sequence[Algorithm]
) -> Algorithm:
    """Pick one algorithm by ``lambda % len(algorithms)``.

    ``algorithms`` must be non-empty and ordered; the caller is responsible for
    filtering disabled entries and sorting when reproducibility matters.
    """
    if not algorithms:
        raise ValueError("at least one algorithm is required")
    return algorithms[derive_lambda(context) % len(algorithms)]


def build_selector(
    *,
    name: str = RANDOM_SELECTION,
    algorithms: Sequence[Algorithm] = ALGORITHMS,
) -> Selector:
    """Build a selector for a configured name or per-decision random choice."""
    enabled = _enabled(algorithms)

    if name == RANDOM_SELECTION:
        return lambda context: choose_algorithm(context, enabled)

    for algorithm in enabled:
        if algorithm.name == name:
            chosen = algorithm
            return lambda _context: chosen

    raise ValueError(f"unknown algorithm: {name!r}")
