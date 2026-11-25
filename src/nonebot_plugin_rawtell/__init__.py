"""NoneBot integration for rAwTell."""

from pathlib import Path

from nonebot import logger, require, on_command, get_plugin_config
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message

from .config import Config
from .command import handle_rawtell
from .selector import build_selector

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="rAwTell",
    description="rAwTell — a NoneBot2 plugin for binary decisions",
    usage=("/rawtell — 回答“是”或“否”\n/rawtell 选项A 选项B — 在两个候选中选择一个"),
    type="application",
    homepage="https://github.com/p0rt39/nonebot-plugin-rawtell",
    config=Config,
    supported_adapters=None,
)

plugin_config = get_plugin_config(Config).rawtell
data_dir = Path(store.get_plugin_data_dir())

try:
    algorithm_selector = build_selector(name=plugin_config.algorithm)
except ValueError as error:
    logger.warning(
        "Invalid RAWTELL__ALGORITHM={!r}: {}; falling back to random selection",
        plugin_config.algorithm,
        error,
    )
    algorithm_selector = build_selector()

rawtell = on_command("rawtell", priority=10, block=True)


@rawtell.handle()
async def _handle_rawtell(args: Message = CommandArg()) -> None:
    try:
        answer = handle_rawtell(args.extract_plain_text(), selector=algorithm_selector)
    except Exception:
        logger.exception("rAwTell failed to decide")
        await rawtell.finish("决策算法暂时不可用，请稍后再试。")
    await rawtell.finish(answer)
