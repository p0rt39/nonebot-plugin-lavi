"""Behavior of the built-in decision algorithms and their registry."""

from typing import TYPE_CHECKING
from datetime import datetime, timezone

import pytest

if TYPE_CHECKING:
    from nonebot_plugin_rawtell.protocol import DecisionContext

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)


def _context(nonce: int) -> "DecisionContext":
    from nonebot_plugin_rawtell.protocol import DecisionContext

    return DecisionContext(
        timestamp=_TIMESTAMP,
        pid=10,
        nonce1=nonce,
        nonce2=nonce + 1,
        nonce3=nonce + 2,
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


def test_algorithm_bits_are_derived_from_the_shared_context() -> None:
    from nonebot_plugin_rawtell.protocol import derive_algorithm_bits

    def derive(context: "DecisionContext") -> tuple[int, ...]:
        return derive_algorithm_bits(
            context,
            name="geomancy",
            version=1,
            stage="mothers",
            count=16,
        )

    first = derive(_context(1))

    assert first == derive(_context(1))
    assert first != derive(_context(2))
    assert set(first) <= {0, 1}
    assert len(first) == 16


def test_geomancy_derives_the_reference_shield_chart() -> None:
    from nonebot_plugin_rawtell.decider_algorithms.geomancy import build_chart

    chart = build_chart((0b1111, 0b0101, 0b0110, 0b1000))

    assert chart.mothers == (0b1111, 0b0101, 0b0110, 0b1000)
    assert chart.daughters == (0b1001, 0b1110, 0b1010, 0b1100)
    assert chart.nieces == (0b1010, 0b1110, 0b0111, 0b0110)
    assert chart.right_witness == 0b0100
    assert chart.left_witness == 0b0001
    assert chart.judge == 0b0101


def test_geomancy_judge_is_always_even() -> None:
    from itertools import product

    from nonebot_plugin_rawtell.decider_algorithms.geomancy import (
        FIGURES,
        build_chart,
    )

    for mothers in product(range(16), repeat=4):
        judge = build_chart(mothers).judge

        assert judge in FIGURES
        assert judge.bit_count() % 2 == 0


def test_geomancy_has_four_stable_and_four_mobile_judges() -> None:
    from nonebot_plugin_rawtell.decider_algorithms.geomancy import FIGURES

    judges = {
        pattern: stable
        for pattern, (_, stable) in FIGURES.items()
        if pattern.bit_count() % 2 == 0
    }

    assert len(judges) == 8
    assert list(judges.values()).count(True) == 4


def test_geomancy_answers_from_the_judge_quality(monkeypatch) -> None:
    import nonebot_plugin_rawtell.decider_algorithms.geomancy as geomancy

    stable_marks = (1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0)
    mobile_marks = (1, 1, 1, 1) + (0, 0, 0, 0) * 3

    def use_marks(marks: tuple[int, ...]):
        monkeypatch.setattr(
            geomancy,
            "derive_algorithm_bits",
            lambda *_args, **_kwargs: marks,
        )

    use_marks(stable_marks)
    assert geomancy.calculate(_context(1)) is True

    use_marks(mobile_marks)
    assert geomancy.calculate(_context(1)) is False


def test_obi_letters_and_verdicts() -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import (
        ETAWA,
        OKANA,
        ALAFIA,
        EYEIFE,
        OYEKUN,
        obi_letter,
        obi_verdict,
    )

    assert [obi_letter(count) for count in range(5)] == [
        OYEKUN,
        OKANA,
        EYEIFE,
        ETAWA,
        ALAFIA,
    ]
    assert obi_verdict(4) is True
    assert obi_verdict(3) is True
    assert obi_verdict(2) is None
    assert obi_verdict(1) is False
    assert obi_verdict(0) is False


def test_obi_and_ifa_casts_preserve_mark_order() -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import cast_ifa, cast_obi

    assert cast_obi((1, 0, 1, 1)) == 3
    assert cast_ifa((1, 0, 1, 0, 0, 0, 0, 0)) == 0b00000101


@pytest.mark.parametrize(
    ("odu", "expected"),
    [
        (0b00000000, False),
        (0b00000001, True),
        (0b00000011, False),
        (0b01111111, True),
        (0b11111111, False),
    ],
)
def test_ifa_verdict_uses_mark_parity(odu: int, expected: bool) -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import ifa_verdict

    assert ifa_verdict(odu) is expected


def test_obi_ifa_consults_ifa_for_eyeife(monkeypatch) -> None:
    import nonebot_plugin_rawtell.decider_algorithms.obi_ifa as obi_ifa

    stages: list[str] = []

    def fake_bits(_context, *, stage: str, **_kwargs):
        stages.append(stage)
        if stage == "obi":
            return (1, 1, 0, 0)
        return (1, 0, 0, 0, 0, 0, 0, 0)

    monkeypatch.setattr(obi_ifa, "derive_algorithm_bits", fake_bits)

    assert obi_ifa.calculate(_context(1)) is True
    assert stages == ["obi", "ifa"]


def test_obi_ifa_skips_ifa_for_decisive_letters(monkeypatch) -> None:
    import nonebot_plugin_rawtell.decider_algorithms.obi_ifa as obi_ifa

    stages: list[str] = []

    def fake_bits(_context, *, stage: str, **_kwargs):
        stages.append(stage)
        return (1, 1, 1, 0)

    monkeypatch.setattr(obi_ifa, "derive_algorithm_bits", fake_bits)

    assert obi_ifa.calculate(_context(1)) is True
    assert stages == ["obi"]
