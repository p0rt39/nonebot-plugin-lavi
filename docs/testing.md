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
  命令参数对默认选择器的覆盖，以及自定义文案与肯定/否定词的渲染；记录 ID 行、详细
  回复末行、`history_limit=0` 与写入失败提示、ID 冲突重签且不重算；`handle_review()`
  的 UUIDv4 格式校验、停止历史、记录缺失、损坏文件、大小写等价、原记录/复算/核对
  状态、版本缺失、复算异常、历史文案变更后的候选还原与滚动淘汰。
- `test_config.py`：`TextConfig` 的嵌套构造、`LAVI__TEXT__...` 环境变量解析、必填占位符、
  非法占位符/花括号、空白纯文本字段、允许空步骤标题，以及 `LAVI__HISTORY_LIMIT` 的
  默认值、环境变量解析与负数拒绝。
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
  未知算法时的可用算法列表，复查的原记录块、可选复算块、核对状态与动态值折叠，以及
  `TextConfig` 自定义模板、空步骤标题与转义花括号；不依赖字体宽度或边框。
- `test_storage.py`：记录字段与 JSON 形状往返、UTC 微秒与 64 位整数精度、滚动窗口与
  调小上限后的只读窗口、ID 冲突、损坏/空/未知版本/重复 ID 文件保留、`limit=0` 暂停、
  多 store 并发追加、`os.replace` 失败后的原件与临时文件清理，以及 context 完整性校验。
- `plugin_test.py`：插件加载与元数据冒烟测试、`/lavi` 的 nonebug 命令交互测试
  （单字段算法覆盖、三字段未知算法中止、详细模式输出、自定义文案/肯定词与异常降级
  文案），以及固定采样下的决策 → 重启 store → 另一用户跨群复查、历史文件字节不变与
  同一采样重复决策签发不同 ID。

`test_decision.py` 直接调用 `decision.py`/`protocol.py`，不经过 NoneBot matcher。
`test_command.py` 直接 `await command.handle_lavi()` / `command.handle_review()`，为每个
测试构造 `tmp_path` 下的 `HistoryStore`，并用固定的 `command.uuid4` 控制记录 ID。
命令级测试通过 monkeypatch 替换插件入口的 `algorithm_selector`、`plugin.history_store`、
`command.capture_context` 或 `command.uuid4`，使回复可精确断言，同时保留真实的命令解析、
持久化与 `finish()` 路径。复查测试把 `capture_context`、默认选择器与 `uuid4` 替换为
直接失败的函数，以证明复查不重新采样、不重选算法、不签发新 ID。

新增功能时按 `<subsystem>` 新建 `test_<subsystem>.py`，命令级交互测试留在 `plugin_test.py`。
算法测试使用固定 `DecisionContext` 做确定性断言，不写依赖概率分布的统计测试。

## 隔离约定

`tests/conftest.py` 在 NoneBot 初始化前把 `LOCALSTORE_PLUGIN_DATA_DIR` 指向一次性临时目录，
使套件永远不读写仓库 `data/` 树。`.env.test` 中的 `LOCALSTORE_USE_CWD=true` 会让 localstore
回退到仓库目录，因此隔离的根因是前置的临时目录设置，不是 `.env` 的加载顺序。

从 `nonebot_plugin_lavi` 的 import 放在测试函数内部，避免在 NoneBot 初始化前 import 插件。
