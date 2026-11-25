"""Selection policy for decider algorithms."""

from typing import TYPE_CHECKING
from datetime import datetime, timezone

import pytest

if TYPE_CHECKING:
    from nonebot_plugin_rawtell.protocol import Algorithm, DecisionContext

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)


def _context(nonce: int = 1) -> "DecisionContext":
    from nonebot_plugin_rawtell.protocol import DecisionContext

    return DecisionContext(
        timestamp=_TIMESTAMP,
        pid=10,
        nonce1=nonce,
        nonce2=nonce + 1,
        nonce3=nonce + 2,
    )


def _algorithm(
    name: str, weight: int, result: bool
) -> tuple["Algorithm", list["DecisionContext"]]:
    from nonebot_plugin_rawtell.protocol import Algorithm

    calls: list["DecisionContext"] = []

    def calculate(context: "DecisionContext") -> bool:
        calls.append(context)
        return result

    return (
        Algorithm(name=name, version=1, weight=weight, calculate=calculate),
        calls,
    )


def test_fixed_selector_returns_named_calculator() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    chosen, chosen_calls = _algorithm("chosen", 1, True)
    other, other_calls = _algorithm("other", 1, False)
    selector = build_selector(name="chosen", algorithms=(other, chosen))
    context = _context()

    calculator = selector(context)

    assert calculator is chosen.calculate
    assert calculator(context)
    assert chosen_calls == [context]
    assert other_calls == []


def test_random_selector_is_deterministic_for_the_same_context() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    first, _ = _algorithm("first", 1, True)
    second, _ = _algorithm("second", 1, False)
    selector = build_selector(name="random", algorithms=(first, second))
    context = _context()

    assert selector(context) is selector(context)


def test_random_selector_calls_only_the_chosen_calculator() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    first, first_calls = _algorithm("first", 1, True)
    second, second_calls = _algorithm("second", 1, True)
    selector = build_selector(name="random", algorithms=(first, second))
    context = _context()

    assert selector(context)(context)
    assert len(first_calls) + len(second_calls) == 1


def test_choose_algorithm_uses_cumulative_weights(monkeypatch) -> None:
    import nonebot_plugin_rawtell.selector as selector_module

    class FixedRandom:
        def __init__(self, _seed: int) -> None:
            pass

        def randrange(self, total: int) -> int:
            assert total == 3
            return 2

    first, _ = _algorithm("first", 1, True)
    second, _ = _algorithm("second", 2, False)

    monkeypatch.setattr(selector_module, "Random", FixedRandom)

    assert selector_module.choose_algorithm(_context(), (first, second)) is second


def test_zero_weight_algorithm_is_disabled() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    disabled, disabled_calls = _algorithm("disabled", 0, True)
    enabled, enabled_calls = _algorithm("enabled", 1, False)
    algorithms = (disabled, enabled)
    selector = build_selector(name="random", algorithms=algorithms)
    context = _context()

    assert not selector(context)(context)
    assert disabled_calls == []
    assert enabled_calls == [context]
    with pytest.raises(ValueError, match="unknown algorithm"):
        build_selector(name="disabled", algorithms=algorithms)


def test_unknown_algorithm_is_rejected() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    algorithm, _ = _algorithm("known", 1, True)

    with pytest.raises(ValueError, match="unknown algorithm"):
        build_selector(name="missing", algorithms=(algorithm,))


def test_duplicate_algorithm_names_are_rejected() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    first, _ = _algorithm("same", 1, True)
    second, _ = _algorithm("same", 1, False)

    with pytest.raises(ValueError, match="duplicate algorithm name"):
        build_selector(name="random", algorithms=(first, second))


def test_all_zero_weights_are_rejected() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    first, _ = _algorithm("first", 0, True)
    second, _ = _algorithm("second", 0, False)

    with pytest.raises(ValueError, match="positive weight"):
        build_selector(name="random", algorithms=(first, second))


def test_random_name_is_reserved() -> None:
    from nonebot_plugin_rawtell.protocol import Algorithm

    with pytest.raises(ValueError, match="invalid algorithm name"):
        Algorithm(name="random", version=1, weight=1, calculate=lambda _: True)


def test_selector_and_algorithm_seeds_are_independent() -> None:
    from nonebot_plugin_rawtell.protocol import derive_seed

    context = _context()

    assert derive_seed(context, purpose="selector:v1") != derive_seed(
        context, purpose="algorithm:coin:v1"
    )


def test_default_selector_uses_the_real_registry() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    context = _context()
    calculator = build_selector()(context)

    assert isinstance(calculator(context), bool)
