# rAwTell — Agent 指南（根）

`nonebot-plugin-rawtell` 是一个 NoneBot2 插件。当前已实现 `/rawtell` 二元决策命令、
可插拔算法注册表与算法选择策略；决策历史与持久化尚未实现。

本文件只包含**全仓库通用**的指令，以及**阅读各级子目录特化 AGENTS.md 的要求**。

## Scoped 阅读要求（强制）

在修改任何文件**之前**，先阅读与该目录对应的各级 `AGENTS.md`（从本根文件向下逐级深入）：

- 包级约束：`src/nonebot_plugin_rawtell/AGENTS.md`
- 测试：`tests/AGENTS.md`

深层 `AGENTS.md` 只补充其所在子树的定向约束，不重复上层内容；若上下层表述冲突，以更具体（更深）者为准，
但不得违反本根文件的兼容与发布底线。`docs/` 下是描述性参考（非权威指令），约束仍以各级 `AGENTS.md` 为准。

## 开发工作流（L1nk Workflow）

实现类改动遵循以下顺序，失败即停、修好该级再往上爬：

```text
modify -> ruff -> basedpyright -> focused pytest -> (full pytest) -> [本地] 同步测试环境 -> git commit -s
```

- 依次执行 `uv run ruff check .`、`uv run ruff format --check .`，再做类型检查：`uvx basedpyright==1.40.0`。
  `uvx` 自带该工具本身，因此无需把它加进 dev 依赖；但它仍按 `.venv` 解析导入，
  **运行前须先 `uv sync --all-groups`**，否则依赖未解析会报 `reportMissingImports`。
- 先跑变更区域的聚焦 pytest；改动涉及共享行为或跨模块契约时跑全量 pytest。
- 用户环境包含一个本地测试 Bot；涉及运行时验证时按用户说明**本地**同步并人工验收
  （具体路径/方式属本地环境，不在本仓库指令中固化）。
- 完成后本地 `git commit -s`；除非用户明确要求，不要 push 到远端。
- 仅文档改动也至少跑 `ruff` 与 `basedpyright` 这两个能捕捉仓库级问题的低成本检查。

## 编码规范

- 优先在拥有该行为的子模块内做小范围、定向的修改。
- 严格遵守 Pylance 与 Ruff；把静态告警、lint、import 顺序、格式与异步风格问题当作必须处理的工作。
- 跨模块契约用 `protocol.py` 中的 Pydantic 模型表达，不要在子模块之间传递临时拼凑的 dict。
- 持久化时间戳使用时区感知的 UTC datetime。
- 不要阻塞事件循环；阻塞型 IO 用 `asyncio.to_thread` 等方式移出事件循环。
- 面向外部的辅助子系统按 best-effort 处理，失败要记录日志且不应让主插件崩溃。
- `matcher.finish()` 会抛 NoneBot matcher 异常，不要用宽泛的 `except Exception` 包住它。
- 新的用户可见配置放 `ScopedConfig`，dotenv 键保持 `RAWTELL__...`，并同步更新 README 配置表。
- 对说明不足的事项向用户提问澄清——尤其是行为、兼容性、数据安全、测试范围或发布流程。
- 不要随意删除不受版本控制的文件；删除任何未跟踪、被忽略、生成物或本地环境文件前，须向用户明确二次确认。

## 发布与合规约束

详见 `docs/publishing.md`；要点：

- 项目名 `nonebot-plugin-rawtell`（词间 `-`），模块名 `nonebot_plugin_rawtell`（词间 `_`）。
- 依赖用宽松区间 `>=X.Y,<Z.0`；运行期 import 的第三方库必须写进 `pyproject.toml` 的 `dependencies`。
- 运行期数据读写经 `nonebot-plugin-localstore`，不用 `open()` / `os.getcwd()` 直接定位插件数据。
- 插件须零配置可加载；缺少配置时优雅降级。
- 异步路径禁同步阻塞；跨插件依赖先 `require()`。
- 保留 `__init__.py` 的 `__plugin_meta__`；README 继续提供 `nb plugin install`。

## 全局不变量

- `__init__.py` 只承载 NoneBot 集成（元数据、配置读取、数据目录），功能实现放同级子模块。
- 持久化数据保持向后兼容：不随意改 JSON 形状，不做破坏性格式变更。
- 运行期数据由 `nonebot-plugin-localstore` 定位，文件写采用原子替换原则。

## 描述性参考（docs/）

- `docs/architecture.md`：目录结构、运行时入口与模块职责。
- `docs/testing.md`：测试布局、命令与 conftest 约定。
- `docs/publishing.md`：面向 NoneBot 商店的发布合规约束。

权威指令在各级 `AGENTS.md`；`docs/` 为描述性参考。
