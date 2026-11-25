"""NoneBot integration for LaVI."""

from pathlib import Path

from nonebot import logger, require, on_command, get_plugin_config
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message

from .config import Config
from .command import handle_lavi
from .selector import build_selector

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="LaVI",
    description="LaVI — a NoneBot2 plugin for binary decisions",
    usage=(
        "/lavi — 回答“是”或“否”\n"
        "/lavi 算法名 — 用指定算法回答“是”或“否”\n"
        "/lavi 选项A 选项B — 在两个候选中选择一个\n"
        "/lavi 算法名 选项A 选项B — 用指定算法在两个候选中选择一个"
    ),
    type="application",
    homepage="https://github.com/p0rt39/nonebot-plugin-lavi",
    config=Config,
    supported_adapters=None,
)

plugin_config = get_plugin_config(Config).lavi
data_dir = Path(store.get_plugin_data_dir())

try:
    algorithm_selector = build_selector(name=plugin_config.algorithm)
except ValueError as error:
    logger.warning(
        "Invalid LAVI__ALGORITHM={!r}: {}; falling back to random selection",
        plugin_config.algorithm,
        error,
    )
    algorithm_selector = build_selector()

lavi = on_command("lavi", priority=10, block=True)


@lavi.handle()
async def _handle_lavi(args: Message = CommandArg()) -> None:
    try:
        answer = handle_lavi(
            args.extract_plain_text(),
            selector=algorithm_selector,
            detailed=plugin_config.detailed,
        )
    except Exception:
        logger.exception("LaVI failed to decide")
        await lavi.finish("决策算法暂时不可用，请稍后再试。")
    await lavi.finish(answer)
