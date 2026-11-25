# 发布约束（提炼）

> 本文提炼与本仓库直接相关的 NoneBot 商店发布/合规约束，供各级 AGENTS.md 引用。
> 本文件只承载约束，不复述教程性内容（Matcher、依赖注入、消息处理等请见官方文档）。

## 商店审核红线（违反将被自动拒绝）

1. **命名**
   - 项目名（PyPI/GitHub）：`nonebot-plugin-rawtell`（词间 `-`）。
   - 模块名（Python import）：`nonebot_plugin_rawtell`（词间 `_`）。

2. **依赖管理**
   - 版本用宽松区间 `>=X.Y,<Z.0`（或 `~=`），不要 `==` 锁死。
   - 必须依赖 `nonebot2`；不要添加 V1 的 `nonebot`。
   - 代码里 import 的第三方库都必须列在 `pyproject.toml` 的 `dependencies`。
   - 直接使用的适配器要显式声明（本仓库以 `nonebot-adapter-onebot` 作为可选 extra）。

3. **本地文件存储**
   - 运行期数据读写必须通过 `nonebot-plugin-localstore`。
   - 不用 `open()`、`Path(__file__).parent`、`os.getcwd()` 等直接定位/读写插件数据。

4. **`__plugin_meta__` 完整**
   - 定义在 `__init__.py` 最外层，提供 `name`、`description`、`usage`、`type`
     （`"application"`）、`homepage`、`config`、`supported_adapters`。

5. **零配置可加载**
   - 无预配置时插件能被 import 且不报错；缺配置时优雅降级而非崩溃。

6. **禁同步阻塞**
   - 异步路径使用 `httpx.AsyncClient` 等异步替代品；长时间同步操作会阻塞整个事件循环。

7. **跨插件依赖用 `require()`**
   - import 可选插件前先 `require("nonebot_plugin_xxx")`。

8. **README 安装方式**
   - 必须展示 `nb plugin install nonebot-plugin-rawtell`；不要以旧式 `bot.py` 配置方式作为安装路径。

## 版本与发布

- 当前版本 `0.1.0`，尚未发布到 PyPI；发布流程在功能落地后确定（版本号、标签与 Release 说明的来源）。
- 构建后端为 `uv_build`；改动包数据/依赖时用 `uv build` 并检查随包分发的内容。
  `pyproject.toml` 的 `[tool.uv.build-backend] source-exclude` 把各级 `AGENTS.md`
  排除出发行包——agent 规则属于开发材料，新增子目录规则文件时沿用该 glob。
- CI 只在 Pull Request 上运行；贡献者流程到创建 PR 为止。
- 标签版本必须与 `pyproject.toml` 的 `version` 一致。
