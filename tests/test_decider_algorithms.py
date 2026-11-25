"""Behavior of the built-in decision algorithms and their registry."""

from typing import TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from nonebot_plugin_rawtell.protocol import DecisionContext

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)


def _context(nonce: int) -> "DecisionContext":
    from nonebot_plugin_rawtell.protocol import DecisionContext

    return DecisionContext(
        timestamp=_TIMESTAMP,
        pid=10,
        nonce=nonce,
        monotonic_ns=123,
    )


def test_registry_is_explicit_and_valid() -> None:
    from nonebot_plugin_rawtell.decider_algorithms import ALGORITHMS

    names = [algorithm.name for algorithm in ALGORITHMS]

    assert names
    assert len(names) == len(set(names))
    assert all(algorithm.version >= 1 for algorithm in ALGORITHMS)
    assert all(algorithm.weight > 0 for algorithm in ALGORITHMS)


def test_each_algorithm_is_deterministic_for_the_same_context() -> None:
    from nonebot_plugin_rawtell.decider_algorithms import ALGORITHMS

    context = _context(7)

    for algorithm in ALGORITHMS:
        assert algorithm.calculate(context) == algorithm.calculate(context)


def test_each_algorithm_uses_context_entropy() -> None:
    from nonebot_plugin_rawtell.decider_algorithms import ALGORITHMS

    for algorithm in ALGORITHMS:
        results = {algorithm.calculate(_context(nonce)) for nonce in range(64)}

        assert results == {True, False}, algorithm.name
