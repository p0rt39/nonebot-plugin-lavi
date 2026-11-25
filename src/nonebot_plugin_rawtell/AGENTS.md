# `nonebot_plugin_rawtell` 包 — Agent 指南

Scope：`src/nonebot_plugin_rawtell/`（Python 包根）。先读根 `AGENTS.md`。

## 子系统职责边界

- `__init__.py`：NoneBot 集成——`__plugin_meta__`、scoped config、插件数据目录、`/rawtell`
  matcher 注册。命令与生命周期钩子只在这里注册，实现留在子模块。
- `config.py`：`Config` 与 `ScopedConfig`（dotenv 前缀 `RAWTELL__`）。配置默认值**必须与
  `../../README.md` 配置表保持一致**——修改默认值的同一时间更新 README 表格。
- `protocol.py`：跨子模块共享的领域模型、决策上下文、`Algorithm` 元数据、选择器/计算器
  类型与种子派生。不得反向 import 插件入口或算法包。
- `decision.py`：`/rawtell` 参数解析（单项问题/两个候选项）和选择器→计算器的编排；
  不依赖 NoneBot，也不内置占卜算法。
- `selector.py`：算法注册表校验与固定/随机/加权选择策略；不执行算法、不采样熵。
- `command.py`：`/rawtell` 处理函数，接收参数与已构建的选择器并返回回复文本；不得持有
  `Matcher` 或 import 插件入口。
- `decider_algorithms/`：每个算法一个文件，导出 `ALGORITHM`；`__init__.py` 是显式注册表。
  算法必须同步、纯函数化，只读 `DecisionContext`，不得访问 NoneBot、网络、文件或全局
  `random`。

新增功能时新建子模块（例如 `render.py`、`storage.py`），并在本文件补充其职责一行；
不要把所有逻辑继续堆进 `__init__.py`。

## 包级约束

- Startup 必须零配置可用；缺少任何配置都要优雅降级而非崩溃。
- 配置统一走 `ScopedConfig`，dotenv 键保持 `RAWTELL__...`。
- 持久化路径只从 `__init__.py` 暴露的 `data_dir` 取得，不要自行拼 `Path(__file__).parent`。
- 子模块必须能在驱动初始化之前被 import；不要在模块级调用 `get_driver()` 的运行时属性。
- 面向外部的辅助子系统（网络请求、渲染、定时任务）按 best-effort 处理，失败记录日志即可。
- 新增用户可见配置时带合理的 Pydantic 校验边界，并保留合法的零值语义。
- 新增算法：新建 `decider_algorithms/<name>.py`，导出 `NAME`/`VERSION`/`WEIGHT`/
  `ALGORITHM`，并在 `decider_algorithms/__init__.py` 的 `ALGORITHMS` 中登记；不要使用
  import 时自动发现。算法行为变化时递增 `VERSION`，`name` 一经发布不得改名。
- 算法只能从 `DecisionContext` 派生随机性；禁止在算法或选择器内调用 `secrets`/全局
  `random`，以免每次决策出现第二份熵、破坏可复现性。

## 入口点约束（__init__.py）

- `require("nonebot_plugin_localstore")` 必须在 `import nonebot_plugin_localstore` 之前。
- `__plugin_meta__` 保持在最外层，`config=Config` 与 `supported_adapters` 与当前支持面一致
  （未绑定具体适配器时用 `None`）。
- 新增命令用 `on_command`/`on_message` 注册在 `__init__.py`，处理函数放子模块并以返回值或
  `finish()` 表达结果；不要在子模块里直接持有 `Matcher` 对象。
