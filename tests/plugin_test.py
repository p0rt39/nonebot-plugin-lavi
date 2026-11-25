from typing import TYPE_CHECKING

import nonebot
from fake import fake_private_message_event_v11
from nonebug import App

if TYPE_CHECKING:
    from nonebot_plugin_rawtell.protocol import (
        Algorithm,
        Explanation,
        DecisionContext,
    )


def _algorithm(
    *,
    result: bool,
    name: str = "test",
    display_name: str | None = "探测",
    operators: int = 0,
    steps: tuple[str, ...] = (),
) -> "Algorithm":
    from nonebot_plugin_rawtell.protocol import (
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


async def test_plugin_loads(app: App):
    """The plugin must load with zero configuration."""
    from nonebot_plugin_rawtell import __plugin_meta__

    plugin = nonebot.get_plugin("nonebot_plugin_rawtell")

    assert plugin is not None
    assert __plugin_meta__.name == "rAwTell"
    assert __plugin_meta__.type == "application"


async def test_rawtell_replies_with_first_candidate(app: App, monkeypatch):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_rawtell as plugin

    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=True),
    )
    event = fake_private_message_event_v11(message="/rawtell 红茶 咖啡")

    async with app.test_matcher(plugin.rawtell) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "🔮 决断仪式：「探测」\n✨ 决断结果：「红茶」",
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_rawtell_defaults_to_yes_no(app: App, monkeypatch):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_rawtell as plugin

    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: _algorithm(result=False),
    )
    event = fake_private_message_event_v11(message="/rawtell")

    async with app.test_matcher(plugin.rawtell) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "🔮 决断仪式：「探测」\n✨ 决断结果：「否」",
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_rawtell_detailed_mode_shows_decider_count_and_trace(
    app: App, monkeypatch
):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_rawtell as plugin

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
    event = fake_private_message_event_v11(message="/rawtell 红茶 咖啡")

    async with app.test_matcher(plugin.rawtell) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "🔮 决断仪式：「探测」\n"
            "✨ 决断结果：「红茶」\n"
            "\n"
            "📊 算子数量：3\n"
            "📜 演算过程：\n"
            "首掷示例\n"
            "结论示例",
            result=None,
            bot=bot,
        )
        ctx.should_finished()
