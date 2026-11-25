# 测试参考（描述性）

> 本文是测试布局与工具链的描述性参考。约束性条目归口于
> [../tests/AGENTS.md](../tests/AGENTS.md) 与根 [AGENTS.md](../AGENTS.md)。

## 工具链

项目使用 `uv`、`pytest`、`pytest-asyncio`、`nonebug`、`ruff`、BasedPyright、`prek` 与 `typos`。
`prek` 读取 `.pre-commit-config.yaml`；不要假设 `pre-commit` 可执行文件已安装。
BasedPyright 与 `prek` 不是声明的 dev 依赖，CI 对齐的类型检查命令用 `uvx` 自带工具本身。

常用命令：

```powershell
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uvx basedpyright==1.40.0   # 先同步环境再跑；uvx 自带工具，但仍依赖 .venv 解析导入
uv run pytest
uv run poe test
prek run --all-files
```

`uv run poe test` 以 xdist（`-n auto`）跑 pytest 并产出 XML 覆盖率与 JUnit 报告。
现阶段未设置覆盖率门槛；功能落地后按实际覆盖情况在 `pyproject.toml` 的
`[tool.coverage.report]` 中加入 `fail_under`。

## 测试布局

- `conftest.py`：注册 OneBot V11 适配器，用 `nonebot.load_from_toml("pyproject.toml")` 加载插件。
- `fake.py`：构造 OneBot V11 群聊/私聊假事件，供 `nonebug` 的 `app.test_matcher` 使用。
- `test_command.py`：`handle_lavi()` 的字段数分派——1 字段算法名与未知名称静默回退、
  2 字段保持两个候选、3 字段算法名加候选与未知名称中止、4 个及以上字段保持原行为，
  以及命令参数对默认选择器的覆盖。
- `test_decision.py`：二元决策核心契约——`parse_invocation()` 的字段数分派与
  `parse_options()` 的两种模式、选择器/算法共享同一
  `DecisionContext` 且各调用一次、`Decision` 的稳定算法名与显示名、算法算子数（不含
  选择器）、`trace` 只调用 `explain` 且不重复调用 `calculate`、`capture_context()` 的
  时间/进程/熵采样、异常传播。
- `test_decider_algorithms.py`：注册表唯一性、算法确定性、算法确实使用上下文熵；
  地占盾盘的参考盘、转置/异或不变量与裁判偶数性；Obi 字母、Ifa 奥杜奇偶与
  Eyeife 转 Ifa、第二次 Obi 确认、Ifa 确认与重开分支；`trial` 的位域拆分、
  逐位多数主算子、内积奇偶、13 票阈值与算法/选择器 purpose 域分离；每个算法的
  `explain()` 与 `calculate()` 答案一致且给出非空、按算法结构组织的步骤；内置算法的
  显示名与回退规则。
- `test_selector.py`：固定/随机选择、零权重禁用、`omega` 位映射与 `lambda % N` 规则、
  `available_algorithms()` 的过滤与排序、未知/重名算法拒绝、种子域分离。
- `test_render.py`：简洁模式的仪式名、结果行、详细模式的空行分隔、算子数量与演算步骤，
  以及未知算法时的可用算法列表；不依赖字体宽度或边框。
- `plugin_test.py`：插件加载与元数据冒烟测试，以及 `/lavi` 的 nonebug 命令交互测试
  （单字段算法覆盖、三字段未知算法中止、详细模式输出与完整换行回复）。

`test_decision.py` 直接调用 `decision.py`/`protocol.py`，不经过 NoneBot matcher。
`test_command.py` 直接调用 `command.handle_lavi()`。命令级测试通过 monkeypatch 替换
插件入口的 `algorithm_selector` 或 `command.capture_context`，使回复可精确断言，同时保留
真实的命令解析与 `finish()` 路径。

新增功能时按 `<subsystem>` 新建 `test_<subsystem>.py`，命令级交互测试留在 `plugin_test.py`。
算法测试使用固定 `DecisionContext` 做确定性断言，不写依赖概率分布的统计测试。

## 隔离约定

`tests/conftest.py` 在 NoneBot 初始化前把 `LOCALSTORE_PLUGIN_DATA_DIR` 指向一次性临时目录，
使套件永远不读写仓库 `data/` 树。`.env.test` 中的 `LOCALSTORE_USE_CWD=true` 会让 localstore
回退到仓库目录，因此隔离的根因是前置的临时目录设置，不是 `.env` 的加载顺序。

从 `nonebot_plugin_lavi` 的 import 放在测试函数内部，避免在 NoneBot 初始化前 import 插件。
