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


def test_dayan_change_removals_follow_canonical_counts() -> None:
    from nonebot_plugin_rawtell.decider_algorithms.dayan import (
        first_change_removal,
        later_change_removal,
    )

    first = [
        first_change_removal((first_bit, second_bit))
        for first_bit in (0, 1)
        for second_bit in (0, 1)
    ]

    assert sorted(first) == [5, 5, 5, 9]
    assert [later_change_removal(mark) for mark in (0, 1)] == [4, 8]


def test_dayan_line_values_have_canonical_distribution_and_balance() -> None:
    from itertools import product
    from collections import Counter

    from nonebot_plugin_rawtell.decider_algorithms.dayan import is_yang, cast_line

    lines = [cast_line(marks) for marks in product((0, 1), repeat=4)]

    assert Counter(lines) == {6: 1, 7: 5, 8: 7, 9: 3}
    assert sum(is_yang(line) for line in lines) == 8


def test_dayan_cast_hexagram_preserves_line_order() -> None:
    from nonebot_plugin_rawtell.decider_algorithms.dayan import cast_hexagram

    marks = (
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
    )

    assert cast_hexagram(marks) == (9, 8, 7, 6, 9, 6)


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        ((9, 9, 9, 9, 9, 9), False),
        ((9, 9, 9, 9, 9, 6), True),
        ((9, 9, 9, 6, 6, 6), True),
        ((9, 9, 6, 6, 6, 6), False),
    ],
)
def test_dayan_answers_from_yang_line_parity(
    monkeypatch, lines: tuple[int, ...], expected: bool
) -> None:
    import nonebot_plugin_rawtell.decider_algorithms.dayan as dayan

    line_marks = {
        9: (0, 0, 0, 0),
        8: (0, 0, 0, 1),
        7: (0, 0, 1, 1),
        6: (1, 1, 1, 1),
    }
    marks = tuple(mark for line in lines for mark in line_marks[line])

    monkeypatch.setattr(
        dayan,
        "derive_algorithm_bits",
        lambda *_args, **_kwargs: marks,
    )

    assert dayan.calculate(_context(1)) is expected


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


def _use_stage_bits(monkeypatch, stages: dict[str, tuple[int, ...]]) -> list[str]:
    import nonebot_plugin_rawtell.decider_algorithms.obi_ifa as obi_ifa

    calls: list[str] = []

    def fake_bits(_context, *, stage: str, **_kwargs):
        calls.append(stage)
        return stages[stage]

    monkeypatch.setattr(obi_ifa, "derive_algorithm_bits", fake_bits)
    return calls


@pytest.mark.parametrize(
    ("ifa_marks", "expected"),
    [
        ((1, 0, 0, 0, 0, 0, 0, 0), True),
        ((0, 0, 0, 0, 0, 0, 0, 0), False),
    ],
)
def test_obi_ifa_first_eyeife_defers_to_ifa(
    monkeypatch, ifa_marks: tuple[int, ...], expected: bool
) -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import calculate

    stages = _use_stage_bits(
        monkeypatch,
        {
            "obi:first:0": (1, 1, 0, 0),
            "ifa:0": ifa_marks,
        },
    )

    assert calculate(_context(1)) is expected
    assert stages == ["obi:first:0", "ifa:0"]


@pytest.mark.parametrize(
    ("first_marks", "expected"),
    [
        ((1, 1, 1, 0), True),
        ((1, 0, 0, 0), False),
    ],
)
def test_obi_ifa_second_eyeife_confirms_first_obi(
    monkeypatch, first_marks: tuple[int, ...], expected: bool
) -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import calculate

    stages = _use_stage_bits(
        monkeypatch,
        {
            "obi:first:0": first_marks,
            "obi:second:0": (1, 1, 0, 0),
        },
    )

    assert calculate(_context(1)) is expected
    assert stages == ["obi:first:0", "obi:second:0"]


@pytest.mark.parametrize(
    ("first_marks", "second_marks", "expected"),
    [
        ((1, 1, 1, 1), (1, 0, 0, 0), True),
        ((1, 0, 0, 0), (1, 1, 1, 1), False),
    ],
)
def test_obi_ifa_true_ifa_confirms_first_obi(
    monkeypatch,
    first_marks: tuple[int, ...],
    second_marks: tuple[int, ...],
    expected: bool,
) -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import calculate

    stages = _use_stage_bits(
        monkeypatch,
        {
            "obi:first:0": first_marks,
            "obi:second:0": second_marks,
            "ifa:0": (1, 0, 0, 0, 0, 0, 0, 0),
        },
    )

    assert calculate(_context(1)) is expected
    assert stages == ["obi:first:0", "obi:second:0", "ifa:0"]


def test_obi_ifa_false_ifa_restarts_the_round(monkeypatch) -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import calculate

    stages = _use_stage_bits(
        monkeypatch,
        {
            "obi:first:0": (1, 1, 1, 1),
            "obi:second:0": (1, 0, 0, 0),
            "ifa:0": (0, 0, 0, 0, 0, 0, 0, 0),
            "obi:first:1": (1, 1, 0, 0),
            "ifa:1": (1, 0, 0, 0, 0, 0, 0, 0),
        },
    )

    assert calculate(_context(1)) is True
    assert stages == [
        "obi:first:0",
        "obi:second:0",
        "ifa:0",
        "obi:first:1",
        "ifa:1",
    ]


def test_obi_ifa_restart_uses_the_new_first_verdict(monkeypatch) -> None:
    from nonebot_plugin_rawtell.decider_algorithms.obi_ifa import calculate

    stages = _use_stage_bits(
        monkeypatch,
        {
            "obi:first:0": (1, 1, 1, 1),
            "obi:second:0": (1, 0, 0, 0),
            "ifa:0": (0, 0, 0, 0, 0, 0, 0, 0),
            "obi:first:1": (1, 0, 0, 0),
            "obi:second:1": (1, 1, 0, 0),
        },
    )

    assert calculate(_context(1)) is False
    assert stages == [
        "obi:first:0",
        "obi:second:0",
        "ifa:0",
        "obi:first:1",
        "obi:second:1",
    ]
