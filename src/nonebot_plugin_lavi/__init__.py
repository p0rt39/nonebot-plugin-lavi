"""NoneBot integration for LaVI."""

from pathlib import Path

from nonebot import logger, require, on_command, get_plugin_config
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Message

from .config import Config
from .command import handle_lavi, handle_review
from .storage import HistoryStore
from .selector import build_selector

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="LaVI",
    description="一个面向二元问题的 NoneBot2 决策插件",
    usage=(
        "/lavi — 回答“是”或“否”\n"
        "/lavi 算法名 — 用指定算法回答“是”或“否”\n"
        "/lavi 候选1 候选2 — 从两个空白分隔的候选中选择一个\n"
        "/lavi 算法名 候选1 候选2 — 用指定算法从两个候选中选择一个\n"
        "/lavi-review 记录ID — 凭完整记录 ID 复查历史决策"
        "（任意会话的持有者均可）\n"
        "算法名：dayan（大衍）、geomancy（地占）、obi-ifa（宝螺）、"
        "trial（裁判）、random（随机）"
    ),
    type="application",
    homepage="https://github.com/p0rt39/nonebot-plugin-lavi",
    config=Config,
    supported_adapters=None,
)

plugin_config = get_plugin_config(Config).lavi
data_dir = Path(store.get_plugin_data_dir())
history_store = HistoryStore(data_dir, plugin_config.history_limit)

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
lavi_review = on_command("lavi-review", priority=10, block=True)


@lavi.handle()
async def _handle_lavi(args: Message = CommandArg()) -> None:
    try:
        answer = await handle_lavi(
            args.extract_plain_text(),
            history=history_store,
            selector=algorithm_selector,
            detailed=plugin_config.detailed,
            text=plugin_config.text,
        )
    except Exception:
        logger.exception("LaVI failed to decide")
        await lavi.finish(plugin_config.text.unavailable)
    await lavi.finish(answer)


@lavi_review.handle()
async def _handle_review(args: Message = CommandArg()) -> None:
    try:
        answer = await handle_review(
            args.extract_plain_text(),
            history=history_store,
            text=plugin_config.text,
        )
    except Exception:
        logger.exception("LaVI failed to review")
        await lavi_review.finish(plugin_config.text.unavailable)
    await lavi_review.finish(answer)
