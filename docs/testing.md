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
- `test_decision.py`：二元决策骨架的行为契约——参数解析的两种模式、选择器/计算器共享同一
  `DecisionContext` 且各调用一次、`capture_context()` 的进程与 UTC 时间采样、异常传播。
- `plugin_test.py`：插件加载与元数据冒烟测试。

`test_decision.py` 直接调用 `decision.py`/`protocol.py`，不经过 NoneBot matcher；命令接入后
再在 `plugin_test.py` 增加端到端交互。

新增功能时按 `<subsystem>` 新建 `test_<subsystem>.py`，命令级交互测试留在 `plugin_test.py`。

## 隔离约定

`tests/conftest.py` 在 NoneBot 初始化前把 `LOCALSTORE_PLUGIN_DATA_DIR` 指向一次性临时目录，
使套件永远不读写仓库 `data/` 树。`.env.test` 中的 `LOCALSTORE_USE_CWD=true` 会让 localstore
回退到仓库目录，因此隔离的根因是前置的临时目录设置，不是 `.env` 的加载顺序。

从 `nonebot_plugin_rawtell` 的 import 放在测试函数内部，避免在 NoneBot 初始化前 import 插件。
