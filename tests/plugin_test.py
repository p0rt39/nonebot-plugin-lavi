from uuid import UUID
from typing import TYPE_CHECKING

import nonebot
from fake import fake_group_message_event_v11, fake_private_message_event_v11
from nonebug import App

if TYPE_CHECKING:
    from pathlib import Path

    from nonebot_plugin_lavi.protocol import (
        Algorithm,
        Explanation,
        DecisionContext,
    )

_FIXED_ID = UUID("00000000-0000-4000-8000-0000000000aa")
_SECOND_ID = UUID("00000000-0000-4000-8000-0000000000bb")


def _algorithm(
    *,
    result: bool,
    name: str = "test",
    display_name: str | None = "探测",
    operators: int = 0,
    steps: tuple[str, ...] = (),
) -> "Algorithm":
    from nonebot_plugin_lavi.protocol import (
        Algorithm,
        Explanation,
        derive_algorithm_bits,
    )

    def derive(context: "DecisionContext") -> None:
        if operators:
            derive_algorithm_bits(
                context,
                name=name,
                version=1,
                stage="probe",
                count=operators,
            )

    def calculate(context: "DecisionContext") -> bool:
        derive(context)
        return result

    def explain(context: "DecisionContext") -> "Explanation":
        derive(context)
        return Explanation(result, steps)

    return Algorithm(
        name=name,
        version=1,
        weight=1,
        calculate=calculate,
        display_name=display_name,
        explain=explain,
    )


def _isolated_history(monkeypatch, plugin, tmp_path: "Path", limit: int = 1000):
    from nonebot_plugin_lavi.storage import HistoryStore

    store = HistoryStore(tmp_path, limit)
    monkeypatch.setattr(plugin, "history_store", store)
    return store


def _fixed_record_ids(monkeypatch, *record_ids: UUID) -> None:
    import nonebot_plugin_lavi.command as command_module

    remaining = iter(record_ids)
    monkeypatch.setattr(command_module, "uuid4", lambda: next(remaining))


def _reply(body: str, record_id: UUID = _FIXED_ID) -> str:
    return f"{body}\n记录 ID：{record_id}"


async def test_plugin_loads(app: App):
    """The plugin must load with zero configuration."""
    from nonebot_plugin_lavi import __plugin_meta__

    plugin = nonebot.get_plugin("nonebot_plugin_lavi")

    assert plugin is not None
    assert __plugin_meta__.name == "LaVI"
    assert __plugin_meta__.type == "application"
    assert "/lavi-review" in __plugin_meta__.usage


async def test_lavi_replies_with_first_candidate(app: App, monkeypatch, tmp_path):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin

    _isolated_history(monkeypatch, plugin, tmp_path)
    _fixed_record_ids(monkeypatch, _FIXED_ID)
    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=True),
    )
    event = fake_private_message_event_v11(message="/lavi 红茶 咖啡")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            _reply("🔮 决断仪式：「探测」\n✨ 决断结果：「红茶」"),
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_lavi_defaults_to_yes_no(app: App, monkeypatch, tmp_path):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin

    _isolated_history(monkeypatch, plugin, tmp_path)
    _fixed_record_ids(monkeypatch, _FIXED_ID)
    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=False),
    )
    event = fake_private_message_event_v11(message="/lavi")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            _reply("🔮 决断仪式：「探测」\n✨ 决断结果：「否」"),
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_lavi_detailed_mode_shows_decider_count_and_trace(
    app: App, monkeypatch, tmp_path
):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin

    _isolated_history(monkeypatch, plugin, tmp_path)
    _fixed_record_ids(monkeypatch, _FIXED_ID)
    monkeypatch.setattr(plugin.plugin_config, "detailed", True)
    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(
            name="probe",
            display_name="探测",
            result=True,
            operators=3,
            steps=("首掷示例", "结论示例"),
        ),
    )
    event = fake_private_message_event_v11(message="/lavi 红茶 咖啡")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            _reply(
                "🔮 决断仪式：「探测」\n"
                "✨ 决断结果：「红茶」\n"
                "\n"
                "📊 算子数量：3\n"
                "📜 演算过程：\n"
                "首掷示例\n"
                "结论示例"
            ),
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_lavi_single_argument_selects_algorithm(app: App, monkeypatch, tmp_path):
    from datetime import datetime, timezone

    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin
    import nonebot_plugin_lavi.command as command_module
    from nonebot_plugin_lavi.protocol import DecisionContext
    from nonebot_plugin_lavi.decider_algorithms import ALGORITHMS

    _isolated_history(monkeypatch, plugin, tmp_path)
    _fixed_record_ids(monkeypatch, _FIXED_ID)
    context = DecisionContext(
        timestamp=datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc),
        pid=10,
        nonce1=1,
        nonce2=2,
        nonce3=3,
    )
    trial = next(algorithm for algorithm in ALGORITHMS if algorithm.name == "trial")
    expected = "是" if trial.calculate(context) else "否"
    monkeypatch.setattr(command_module, "capture_context", lambda: context)
    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=True),
    )
    event = fake_private_message_event_v11(message="/lavi trial")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            _reply(f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{expected}」"),
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_lavi_three_arguments_reject_unknown_algorithm(
    app: App, monkeypatch, tmp_path
):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin

    _isolated_history(monkeypatch, plugin, tmp_path)
    event = fake_private_message_event_v11(message="/lavi missing 红茶 咖啡")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "⚠️ 未知算法：「missing」\n"
            "可用算法：dayan（大衍）、geomancy（地占）、obi-ifa（宝螺）、"
            "trial（裁判）；random（随机）",
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_lavi_uses_configured_text(app: App, monkeypatch, tmp_path):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin

    _isolated_history(monkeypatch, plugin, tmp_path)
    _fixed_record_ids(monkeypatch, _FIXED_ID)
    monkeypatch.setattr(
        plugin.plugin_config.text,
        "header",
        "🎴 神谕：「{decider}」",
    )
    monkeypatch.setattr(
        plugin.plugin_config.text,
        "result",
        "🎯 结果：「{answer}」",
    )
    monkeypatch.setattr(plugin.plugin_config.text, "affirmative", "行")
    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=True),
    )
    event = fake_private_message_event_v11(message="/lavi")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            _reply("🎴 神谕：「探测」\n🎯 结果：「行」"),
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_lavi_unavailable_uses_configured_text(app: App, monkeypatch):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin

    monkeypatch.setattr(
        plugin.plugin_config.text,
        "unavailable",
        "占卜服务暂时打烊。",
    )

    async def fail(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(plugin, "handle_lavi", fail)
    event = fake_private_message_event_v11(message="/lavi")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "占卜服务暂时打烊。",
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_decision_record_can_be_reviewed_after_restart(
    app: App, monkeypatch, tmp_path
):
    from datetime import datetime, timezone

    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_lavi as plugin
    import nonebot_plugin_lavi.command as command_module
    from nonebot_plugin_lavi.storage import HistoryStore
    from nonebot_plugin_lavi.protocol import DecisionContext
    from nonebot_plugin_lavi.decider_algorithms import trial as trial_module

    def reject(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("review must not sample or reselect")

    context = DecisionContext(
        timestamp=datetime(2024, 5, 6, 7, 8, 9, 123456, tzinfo=timezone.utc),
        pid=10,
        nonce1=1,
        nonce2=2,
        nonce3=3,
    )
    explanation = trial_module.explain(context)
    assert len(explanation.steps) == 3
    winner = "红茶" if explanation.answer else "咖啡"
    position = 1 if explanation.answer else 2
    _isolated_history(monkeypatch, plugin, tmp_path)
    _fixed_record_ids(monkeypatch, _FIXED_ID)
    monkeypatch.setattr(command_module, "capture_context", lambda: context)
    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=True),
    )
    private_event = fake_private_message_event_v11(message="/lavi trial 红茶 咖啡")

    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, private_event)
        ctx.should_call_send(
            private_event,
            _reply(f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{winner}」"),
            result=None,
            bot=bot,
        )
        ctx.should_finished()

    history_path = tmp_path / "history.json"
    before = history_path.read_bytes()
    monkeypatch.setattr(
        plugin,
        "history_store",
        HistoryStore(tmp_path, 1000),
    )
    monkeypatch.setattr(plugin, "algorithm_selector", reject)
    monkeypatch.setattr(command_module, "capture_context", reject)
    monkeypatch.setattr(command_module, "uuid4", reject)
    group_event = fake_group_message_event_v11(
        message=f"/lavi-review {_FIXED_ID}",
        user_id=999,
        group_id=1234,
    )
    steps = "\n".join(explanation.steps)
    expected_review = (
        f"记录 ID：{_FIXED_ID}\n"
        f"决策时间：{context.timestamp.isoformat()}\n"
        "原算法：裁判（trial v1）\n"
        "原候选：1「红茶」 / 2「咖啡」\n"
        f"原结果：第 {position} 项「{winner}」\n"
        "原算子数量：13\n"
        "\n"
        "🔮 决断仪式：「裁判」\n"
        f"✨ 决断结果：「{winner}」\n"
        "\n"
        "📊 算子数量：13\n"
        "📜 演算过程：\n"
        f"{steps}\n"
        "复查一致。"
    )

    async with app.test_matcher(plugin.lavi_review) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, group_event)
        ctx.should_call_send(
            group_event,
            expected_review,
            result=None,
            bot=bot,
        )
        ctx.should_finished()

    assert history_path.read_bytes() == before

    monkeypatch.setattr(command_module, "capture_context", lambda: context)
    _fixed_record_ids(monkeypatch, _SECOND_ID)
    async with app.test_matcher(plugin.lavi) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, private_event)
        ctx.should_call_send(
            private_event,
            _reply(
                f"🔮 决断仪式：「裁判」\n✨ 决断结果：「{winner}」",
                record_id=_SECOND_ID,
            ),
            result=None,
            bot=bot,
        )
        ctx.should_finished()

    assert _SECOND_ID != _FIXED_ID
