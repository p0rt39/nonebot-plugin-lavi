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


def test_fixed_selector_returns_named_algorithm() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    chosen, chosen_calls = _algorithm("chosen", 1, True)
    other, other_calls = _algorithm("other", 1, False)
    selector = build_selector(name="chosen", algorithms=(other, chosen))
    context = _context()

    algorithm = selector(context)

    assert algorithm is chosen
    assert algorithm.calculate(context)
    assert chosen_calls == [context]
    assert other_calls == []


def test_random_selector_is_deterministic_for_the_same_context() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    first, _ = _algorithm("first", 1, True)
    second, _ = _algorithm("second", 1, False)
    selector = build_selector(name="random", algorithms=(first, second))
    context = _context()

    assert selector(context) is selector(context)


def test_random_selector_calls_only_the_chosen_algorithm() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    first, first_calls = _algorithm("first", 1, True)
    second, second_calls = _algorithm("second", 1, True)
    selector = build_selector(name="random", algorithms=(first, second))
    context = _context()

    assert selector(context).calculate(context)
    assert len(first_calls) + len(second_calls) == 1


def test_compose_omega_maps_forward_and_reverse_diagonals() -> None:
    from nonebot_plugin_rawtell.selector import OPERATOR_COUNT, compose_omega

    for omega_position in range(2 * OPERATOR_COUNT):
        operators = [0] * OPERATOR_COUNT
        if omega_position < OPERATOR_COUNT:
            operator_index = omega_position + 1
            operators[operator_index - 1] = 1 << (64 - operator_index)
        else:
            reverse_position = 2 * OPERATOR_COUNT - omega_position
            operator_index = OPERATOR_COUNT + 1 - reverse_position
            operators[operator_index - 1] = 1 << (reverse_position - 1)

        assert compose_omega(operators) == 1 << (
            2 * OPERATOR_COUNT - 1 - omega_position
        )


def test_derive_operators_are_deterministic_and_64_bit() -> None:
    from nonebot_plugin_rawtell.selector import OPERATOR_COUNT, derive_operators

    operators = derive_operators(_context())

    assert len(operators) == OPERATOR_COUNT
    assert all(0 <= operator < 1 << 64 for operator in operators)
    assert operators == derive_operators(_context())


def test_choose_algorithm_uses_lambda_modulo_algorithm_count(monkeypatch) -> None:
    import nonebot_plugin_rawtell.selector as selector_module

    algorithms = tuple(
        _algorithm(f"algorithm-{index}", 1, True)[0] for index in range(4)
    )
    monkeypatch.setattr(selector_module, "derive_lambda", lambda _: 7)

    assert selector_module.choose_algorithm(_context(), algorithms) is algorithms[3]


def test_zero_weight_algorithm_is_disabled() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    disabled, disabled_calls = _algorithm("disabled", 0, True)
    enabled, enabled_calls = _algorithm("enabled", 1, False)
    algorithms = (disabled, enabled)
    selector = build_selector(name="random", algorithms=algorithms)
    context = _context()

    assert not selector(context).calculate(context)
    assert disabled_calls == []
    assert enabled_calls == [context]
    with pytest.raises(ValueError, match="unknown algorithm"):
        build_selector(name="disabled", algorithms=algorithms)


def test_unknown_algorithm_is_rejected() -> None:
    from nonebot_plugin_rawtell.selector import (
        UnknownAlgorithmError,
        build_selector,
    )

    algorithm, _ = _algorithm("known", 1, True)

    with pytest.raises(UnknownAlgorithmError, match="unknown algorithm") as caught:
        build_selector(name="missing", algorithms=(algorithm,))

    assert caught.value.name == "missing"


def test_available_algorithms_are_enabled_and_sorted() -> None:
    from nonebot_plugin_rawtell.selector import available_algorithms

    disabled, _ = _algorithm("disabled", 0, True)
    beta, _ = _algorithm("beta", 1, True)
    alpha, _ = _algorithm("alpha", 1, False)

    enabled = available_algorithms((beta, disabled, alpha))

    assert [algorithm.name for algorithm in enabled] == ["alpha", "beta"]


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
    from nonebot_plugin_rawtell.protocol import derive_seed, derive_algorithm_seed

    context = _context()
    selector_seed = derive_seed(context, purpose="selector:operator:1")
    algorithm_seed = derive_algorithm_seed(context, name="geomancy", version=1)

    assert selector_seed != algorithm_seed


def test_default_selector_uses_the_real_registry() -> None:
    from nonebot_plugin_rawtell.selector import build_selector

    context = _context()
    algorithm = build_selector()(context)

    assert isinstance(algorithm.calculate(context), bool)
