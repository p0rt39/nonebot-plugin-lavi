import nonebot
from fake import fake_private_message_event_v11
from nonebug import App


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
        lambda _context: lambda _context: True,
    )
    event = fake_private_message_event_v11(message="/rawtell 红茶 咖啡")

    async with app.test_matcher(plugin.rawtell) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "红茶", result=None, bot=bot)
        ctx.should_finished()


async def test_rawtell_defaults_to_yes_no(app: App, monkeypatch):
    from nonebot.adapters.onebot.v11 import Bot
    from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

    import nonebot_plugin_rawtell as plugin

    monkeypatch.setattr(
        plugin,
        "algorithm_selector",
        lambda _context: lambda _context: False,
    )
    event = fake_private_message_event_v11(message="/rawtell")

    async with app.test_matcher(plugin.rawtell) as ctx:
        adapter = nonebot.get_adapter(OnebotV11Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "否", result=None, bot=bot)
        ctx.should_finished()
