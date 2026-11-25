"""Observable behavior of the binary decision skeleton."""

import os
from typing import TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from collections.abc import Callable

import pytest

if TYPE_CHECKING:
    from nonebot_plugin_rawtell.protocol import (
        Algorithm,
        Calculator,
        Explanation,
        DecisionContext,
    )

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)


def _context(pid: int = 10) -> "DecisionContext":
    from nonebot_plugin_rawtell.protocol import DecisionContext

    return DecisionContext(timestamp=_TIMESTAMP, pid=pid)


def _constant(value: bool) -> "Calculator":
    def calculator(_: "DecisionContext") -> bool:
        return value

    return calculator


def _algorithm_with(
    calculator: "Calculator",
    *,
    name: str = "test",
    display_name: str | None = None,
    explain: "Callable[[DecisionContext], Explanation] | None" = None,
) -> "Algorithm":
    from nonebot_plugin_rawtell.protocol import Algorithm

    return Algorithm(
        name=name,
        version=1,
        weight=1,
        calculate=calculator,
        display_name=display_name,
        explain=explain,
    )


def _algorithm(value: bool, *, name: str = "test") -> "Algorithm":
    return _algorithm_with(_constant(value), name=name)


@pytest.mark.parametrize(
    "arguments", ["", "   ", "\t\n", "明天会下雨吗？", "今天 要 出门吗"]
)
@pytest.mark.parametrize(("value", "expected"), [(True, "是"), (False, "否")])
def test_yes_no_question_returns_corresponding_reply(
    arguments: str, value: bool, expected: str
) -> None:
    from nonebot_plugin_rawtell.decision import decide

    result = decide(arguments, context=_context(), selector=lambda _: _algorithm(value))

    assert result.answer == expected


def test_two_candidates_are_replied_verbatim() -> None:
    from nonebot_plugin_rawtell.decision import decide

    context = _context()
    arguments = "  Earl-Grey　咖啡！  "

    yes = decide(arguments, context=context, selector=lambda _: _algorithm(True))
    no = decide(arguments, context=context, selector=lambda _: _algorithm(False))

    assert yes.answer == "Earl-Grey"
    assert no.answer == "咖啡！"


def test_repeated_candidates_stay_in_two_option_mode() -> None:
    from nonebot_plugin_rawtell.decision import decide

    context = _context()
    arguments = "茶\t茶"

    yes = decide(arguments, context=context, selector=lambda _: _algorithm(True))
    no = decide(arguments, context=context, selector=lambda _: _algorithm(False))

    assert yes.answer == "茶"
    assert no.answer == "茶"


@pytest.mark.parametrize(
    ("arguments", "algorithm", "text", "require_algorithm"),
    [
        ("", None, "", False),
        ("   ", None, "   ", False),
        ("trial", "trial", "", False),
        ("红茶 咖啡", None, "红茶 咖啡", False),
        ("trial 红茶 咖啡", "trial", "红茶 咖啡", True),
        ("红茶 咖啡 加奶 少糖", None, "红茶 咖啡 加奶 少糖", False),
    ],
)
def test_parse_invocation_splits_by_field_count(
    arguments: str,
    algorithm: str | None,
    text: str,
    require_algorithm: bool,
) -> None:
    from nonebot_plugin_rawtell.decision import parse_invocation

    invocation = parse_invocation(arguments)

    assert invocation.algorithm == algorithm
    assert invocation.text == text
    assert invocation.require_algorithm is require_algorithm


def test_single_field_invocation_keeps_yes_no_options() -> None:
    from nonebot_plugin_rawtell.decision import parse_options, parse_invocation

    invocation = parse_invocation("trial")

    assert parse_options(invocation.text) == ("是", "否")


def test_three_field_invocation_keeps_two_candidates() -> None:
    from nonebot_plugin_rawtell.decision import parse_options, parse_invocation

    invocation = parse_invocation("trial 红茶 咖啡")

    assert parse_options(invocation.text) == ("红茶", "咖啡")


def test_selector_picks_one_algorithm_for_the_shared_context() -> None:
    from nonebot_plugin_rawtell.decision import decide

    def run(pid: int) -> str:
        context = _context(pid)
        selected: list["DecisionContext"] = []
        yes_calls: list["DecisionContext"] = []
        no_calls: list["DecisionContext"] = []

        def acknowledge(received: "DecisionContext") -> bool:
            yes_calls.append(received)
            return True

        def reject(received: "DecisionContext") -> bool:
            no_calls.append(received)
            return False

        def selector(received: "DecisionContext") -> "Algorithm":
            selected.append(received)
            calculator = acknowledge if received.pid % 2 == 0 else reject
            return _algorithm_with(calculator)

        result = decide("红茶 咖啡", context=context, selector=selector)

        assert len(selected) == 1
        assert selected[0] is context
        chosen_calls = yes_calls if pid % 2 == 0 else no_calls
        other_calls = no_calls if pid % 2 == 0 else yes_calls
        assert len(chosen_calls) == 1
        assert chosen_calls[0] is context
        assert other_calls == []
        return result.answer

    assert run(10) == "红茶"
    assert run(11) == "咖啡"


def test_decision_reports_algorithm_and_algorithm_operator_count() -> None:
    from nonebot_plugin_rawtell.decision import decide
    from nonebot_plugin_rawtell.protocol import derive_algorithm_bits
    from nonebot_plugin_rawtell.selector import derive_operators

    context = _context()

    def calculate(received: "DecisionContext") -> bool:
        derive_algorithm_bits(
            received,
            name="probe",
            version=1,
            stage="marks",
            count=5,
        )
        return True

    algorithm = _algorithm_with(calculate, name="probe")

    def selector(received: "DecisionContext") -> "Algorithm":
        derive_operators(received)
        return algorithm

    result = decide("红茶 咖啡", context=context, selector=selector)

    assert result.answer == "红茶"
    assert result.algorithm == "probe"
    assert result.display_name == "probe"
    assert result.operator_count == 5


def test_decision_keeps_stable_name_and_uses_display_name_for_replies() -> None:
    from nonebot_plugin_rawtell.decision import decide

    algorithm = _algorithm_with(
        _constant(True),
        name="probe",
        display_name="探测",
    )

    result = decide("红茶 咖啡", context=_context(), selector=lambda _: algorithm)

    assert result.algorithm == "probe"
    assert result.display_name == "探测"


def test_trace_uses_the_explanation_without_calling_calculate() -> None:
    from nonebot_plugin_rawtell.decision import decide
    from nonebot_plugin_rawtell.protocol import Explanation, derive_algorithm_bits

    context = _context()
    calculate_calls: list["DecisionContext"] = []
    explain_calls: list["DecisionContext"] = []

    def calculate(received: "DecisionContext") -> bool:
        calculate_calls.append(received)
        return False

    def explain(received: "DecisionContext") -> "Explanation":
        explain_calls.append(received)
        derive_algorithm_bits(
            received,
            name="probe",
            version=1,
            stage="marks",
            count=3,
        )
        return Explanation(True, ("step one", "step two"))

    algorithm = _algorithm_with(calculate, name="probe", explain=explain)

    traced = decide(
        "红茶 咖啡",
        context=context,
        selector=lambda _: algorithm,
        trace=True,
    )

    assert traced.answer == "红茶"
    assert traced.steps == ("step one", "step two")
    assert traced.operator_count == 3
    assert traced.display_name == "probe"
    assert calculate_calls == []
    assert explain_calls == [context]

    untraced = decide(
        "红茶 咖啡",
        context=context,
        selector=lambda _: algorithm,
        trace=False,
    )

    assert untraced.answer == "咖啡"
    assert untraced.steps == ()
    assert calculate_calls == [context]
    assert explain_calls == [context]


def test_capture_context_samples_process_and_utc_time() -> None:
    from nonebot_plugin_rawtell.protocol import capture_context

    context = capture_context()

    assert context.pid == os.getpid()
    assert context.timestamp.utcoffset() == timedelta(0)
    assert all(
        0 <= nonce < 1 << 64
        for nonce in (context.nonce1, context.nonce2, context.nonce3)
    )


def test_calculator_error_propagates() -> None:
    from nonebot_plugin_rawtell.decision import decide

    def fail(_: "DecisionContext") -> bool:
        raise ValueError("calculator failed")

    algorithm = _algorithm_with(fail)

    with pytest.raises(ValueError, match="calculator failed"):
        decide("红茶 咖啡", context=_context(), selector=lambda _: algorithm)


def test_selector_error_propagates() -> None:
    from nonebot_plugin_rawtell.decision import decide

    def fail(_: "DecisionContext") -> "Algorithm":
        raise ValueError("selector failed")

    with pytest.raises(ValueError, match="selector failed"):
        decide("红茶 咖啡", context=_context(), selector=fail)
