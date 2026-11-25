"""Select one decision algorithm for a :class:`DecisionContext`."""

from random import Random
from collections.abc import Sequence

from .protocol import Selector, Algorithm, DecisionContext, derive_seed
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


def choose_algorithm(
    context: DecisionContext, algorithms: Sequence[Algorithm]
) -> Algorithm:
    """Pick one algorithm by integer weight using the context-derived seed.

    ``algorithms`` must be non-empty and ordered; the caller is responsible for
    filtering zero weights and sorting when reproducibility matters.
    """
    total_weight = sum(algorithm.weight for algorithm in algorithms)
    if total_weight <= 0:
        raise ValueError("at least one algorithm must have a positive weight")

    offset = Random(derive_seed(context, purpose="selector:v1")).randrange(total_weight)
    for algorithm in algorithms:
        offset -= algorithm.weight
        if offset < 0:
            return algorithm
    raise AssertionError("unreachable")


def build_selector(
    *,
    name: str = RANDOM_SELECTION,
    algorithms: Sequence[Algorithm] = ALGORITHMS,
) -> Selector:
    """Build a selector for a configured name or per-decision random choice."""
    enabled = _enabled(algorithms)

    if name == RANDOM_SELECTION:
        return lambda context: choose_algorithm(context, enabled).calculate

    for algorithm in enabled:
        if algorithm.name == name:
            chosen = algorithm
            return lambda _context: chosen.calculate

    raise ValueError(f"unknown algorithm: {name!r}")
