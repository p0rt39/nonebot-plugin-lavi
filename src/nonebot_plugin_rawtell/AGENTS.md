# `nonebot_plugin_rawtell` 包 — Agent 指南

Scope：`src/nonebot_plugin_rawtell/`（Python 包根）。先读根 `AGENTS.md`。

## 子系统职责边界

- `__init__.py`：NoneBot 集成——`__plugin_meta__`、scoped config、插件数据目录。
  目前不放命令与生命周期钩子；新增时先在这里注册，实现留在子模块。
- `config.py`：`Config` 与 `ScopedConfig`（dotenv 前缀 `RAWTELL__`）。配置默认值**必须与
  `../../README.md` 配置表保持一致**——修改默认值的同一时间更新 README 表格。
- `protocol.py`：跨子模块共享的领域 Pydantic 模型。

新增功能时新建子模块（例如 `render.py`、`storage.py`），并在本文件补充其职责一行；
不要把所有逻辑继续堆进 `__init__.py`。

## 包级约束

- Startup 必须零配置可用；缺少任何配置都要优雅降级而非崩溃。
- 配置统一走 `ScopedConfig`，dotenv 键保持 `RAWTELL__...`。
- 持久化路径只从 `__init__.py` 暴露的 `data_dir` 取得，不要自行拼 `Path(__file__).parent`。
- 子模块必须能在驱动初始化之前被 import；不要在模块级调用 `get_driver()` 的运行时属性。
- 面向外部的辅助子系统（网络请求、渲染、定时任务）按 best-effort 处理，失败记录日志即可。
- 新增用户可见配置时带合理的 Pydantic 校验边界，并保留合法的零值语义。

## 入口点约束（__init__.py）

- `require("nonebot_plugin_localstore")` 必须在 `import nonebot_plugin_localstore` 之前。
- `__plugin_meta__` 保持在最外层，`config=Config` 与 `supported_adapters` 与当前支持面一致
  （未绑定具体适配器时用 `None`）。
- 新增命令用 `on_command`/`on_message` 注册在 `__init__.py`，处理函数放子模块并以返回值或
  `finish()` 表达结果；不要在子模块里直接持有 `Matcher` 对象。
