"""Observable behavior of the binary decision skeleton."""

import os
from typing import TYPE_CHECKING
from datetime import datetime, timezone, timedelta

import pytest

if TYPE_CHECKING:
    from nonebot_plugin_rawtell.protocol import Calculator, DecisionContext

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)


def _context(pid: int = 10) -> "DecisionContext":
    from nonebot_plugin_rawtell.protocol import DecisionContext

    return DecisionContext(timestamp=_TIMESTAMP, pid=pid)


def _constant(value: bool) -> "Calculator":
    def calculator(_: "DecisionContext") -> bool:
        return value

    return calculator


@pytest.mark.parametrize(
    "arguments", ["", "   ", "\t\n", "明天会下雨吗？", "今天 要 出门吗"]
)
@pytest.mark.parametrize(("value", "expected"), [(True, "是"), (False, "否")])
def test_yes_no_question_returns_corresponding_reply(
    arguments: str, value: bool, expected: str
) -> None:
    from nonebot_plugin_rawtell.decision import decide

    result = decide(arguments, context=_context(), selector=lambda _: _constant(value))

    assert result == expected


def test_two_candidates_are_replied_verbatim() -> None:
    from nonebot_plugin_rawtell.decision import decide

    context = _context()
    arguments = "  Earl-Grey　咖啡！  "

    yes = decide(arguments, context=context, selector=lambda _: _constant(True))
    no = decide(arguments, context=context, selector=lambda _: _constant(False))

    assert yes == "Earl-Grey"
    assert no == "咖啡！"


def test_repeated_candidates_stay_in_two_option_mode() -> None:
    from nonebot_plugin_rawtell.decision import decide

    context = _context()
    arguments = "茶\t茶"

    yes = decide(arguments, context=context, selector=lambda _: _constant(True))
    no = decide(arguments, context=context, selector=lambda _: _constant(False))

    assert yes == "茶"
    assert no == "茶"


def test_selector_picks_one_calculator_for_the_shared_context() -> None:
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

        def selector(received: "DecisionContext") -> "Calculator":
            selected.append(received)
            return acknowledge if received.pid % 2 == 0 else reject

        result = decide("红茶 咖啡", context=context, selector=selector)

        assert len(selected) == 1
        assert selected[0] is context
        chosen_calls = yes_calls if pid % 2 == 0 else no_calls
        other_calls = no_calls if pid % 2 == 0 else yes_calls
        assert len(chosen_calls) == 1
        assert chosen_calls[0] is context
        assert other_calls == []
        return result

    assert run(10) == "红茶"
    assert run(11) == "咖啡"


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

    with pytest.raises(ValueError, match="calculator failed"):
        decide("红茶 咖啡", context=_context(), selector=lambda _: fail)


def test_selector_error_propagates() -> None:
    from nonebot_plugin_rawtell.decision import decide

    def fail(_: "DecisionContext") -> "Calculator":
        raise ValueError("selector failed")

    with pytest.raises(ValueError, match="selector failed"):
        decide("红茶 咖啡", context=_context(), selector=fail)
