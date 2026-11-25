"""Command-layer field-count handling and selector overrides."""

from typing import TYPE_CHECKING, NoReturn
from datetime import datetime, timezone

import pytest

if TYPE_CHECKING:
    from nonebot_plugin_lavi.protocol import (
        Selector,
        Algorithm,
        DecisionContext,
    )

_TIMESTAMP = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)


def _context() -> "DecisionContext":
    from nonebot_plugin_lavi.protocol import DecisionContext

    return DecisionContext(
        timestamp=_TIMESTAMP,
        pid=10,
        nonce1=1,
        nonce2=2,
        nonce3=3,
    )


def _configured_algorithm(result: bool) -> "Algorithm":
    from nonebot_plugin_lavi.protocol import Algorithm

    return Algorithm(
        name="configured",
        version=1,
        weight=1,
        calculate=lambda _: result,
        display_name="配置",
    )


def _configured_selector(result: bool) -> "Selector":
    algorithm = _configured_algorithm(result)
    return lambda _: algorithm


def _unused_selector(_: "DecisionContext") -> NoReturn:
    raise AssertionError("configured selector must not be used")


def _fail_context() -> NoReturn:
    raise AssertionError("rejected arguments must not sample a decision context")


@pytest.mark.parametrize("argument", ["missing", "明天会下雨吗？"])
def test_single_unknown_argument_falls_back_to_configured_selector(
    argument: str, monkeypatch
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())

    reply = command.handle_lavi(
        argument,
        selector=_configured_selector(False),
    )

    assert reply == "🔮 决断仪式：「配置」\n✨ 决断结果：「否」"


def test_single_argument_selects_algorithm(monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    context = _context()
    monkeypatch.setattr(command, "capture_context", lambda: context)
    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    expected = "是" if trial.calculate(context) else "否"

    reply = command.handle_lavi("trial", selector=_unused_selector)

    assert reply == f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{expected}」"


def test_random_is_accepted_as_a_single_argument(monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    monkeypatch.setattr(command, "capture_context", lambda: _context())

    reply = command.handle_lavi("random", selector=_unused_selector)

    assert any(f"「{algorithm.label}」" in reply for algorithm in ALGORITHMS)


def test_two_arguments_keep_configured_selector_and_candidates(
    monkeypatch,
) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())

    reply = command.handle_lavi(
        "trial 咖啡",
        selector=_configured_selector(False),
    )

    assert reply == "🔮 决断仪式：「配置」\n✨ 决断结果：「咖啡」"


def test_three_arguments_select_algorithm_and_keep_candidates(
    monkeypatch,
) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    context = _context()
    monkeypatch.setattr(command, "capture_context", lambda: context)
    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    expected = "红茶" if trial.calculate(context) else "咖啡"

    reply = command.handle_lavi(
        "trial 红茶 咖啡",
        selector=_unused_selector,
    )

    assert reply == f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{expected}」"


def test_three_arguments_reject_unknown_algorithm(monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", _fail_context)

    reply = command.handle_lavi(
        "missing 红茶 咖啡",
        selector=_unused_selector,
    )

    assert reply == (
        "⚠️ 未知算法：「missing」\n"
        "可用算法：dayan（大衍）、geomancy（地占）、obi-ifa（宝螺）、"
        "trial（裁判）；random（随机）"
    )


def test_four_or_more_arguments_keep_configured_behavior(monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command

    monkeypatch.setattr(command, "capture_context", lambda: _context())

    reply = command.handle_lavi(
        "trial 红茶 咖啡 加奶",
        selector=_configured_selector(True),
    )

    assert reply == "🔮 决断仪式：「配置」\n✨ 决断结果：「是」"


def test_custom_text_and_reply_words_are_used(monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.config import TextConfig

    monkeypatch.setattr(command, "capture_context", lambda: _context())
    text = TextConfig(
        header="🎴 神谕：「{decider}」",
        result="🎯 结果：「{answer}」",
        affirmative="行",
        negative="不行",
    )

    reply = command.handle_lavi(
        "",
        selector=_configured_selector(True),
        text=text,
    )

    assert reply == "🎴 神谕：「配置」\n🎯 结果：「行」"


def test_custom_unknown_algorithm_text_is_used(monkeypatch) -> None:
    import nonebot_plugin_lavi.command as command
    from nonebot_plugin_lavi.config import TextConfig

    monkeypatch.setattr(command, "capture_context", _fail_context)
    text = TextConfig(
        unknown_algorithm="❌ 没有「{requested}」",
        available_algorithms="可选：{available}；random（随机）",
    )

    reply = command.handle_lavi(
        "missing 红茶 咖啡",
        selector=_unused_selector,
        text=text,
    )

    assert reply == (
        "❌ 没有「missing」\n"
        "可选：dayan（大衍）、geomancy（地占）、obi-ifa（宝螺）、"
        "trial（裁判）；random（随机）"
    )
