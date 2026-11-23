"""rAwTell — NoneBot2 plugin entry point.

Only the NoneBot integration lives here: plugin metadata, scoped config access
and the plugin data directory. Feature code belongs in submodules next to this
file, and every submodule must stay importable without an initialized driver.
"""

from pathlib import Path

from nonebot import require, get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="rAwTell",
    description="rAwTell — a NoneBot2 plugin (work in progress)",
    usage="功能尚未实现。开发中，请勿在生产环境启用。",
    type="application",
    homepage="https://github.com/p0rt39/nonebot-plugin-rawtell",
    config=Config,
    supported_adapters=None,
)

plugin_config = get_plugin_config(Config).rawtell
data_dir = Path(store.get_plugin_data_dir())
