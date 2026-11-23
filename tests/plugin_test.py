import nonebot
from nonebug import App


async def test_plugin_loads(app: App):
    """The plugin must load with zero configuration."""
    from nonebot_plugin_rawtell import __plugin_meta__

    plugin = nonebot.get_plugin("nonebot_plugin_rawtell")

    assert plugin is not None
    assert __plugin_meta__.name == "rAwTell"
    assert __plugin_meta__.type == "application"
