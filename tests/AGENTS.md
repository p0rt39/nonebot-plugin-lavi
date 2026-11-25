# `tests` — Agent 指南

Scope：`tests/`。先读根 `AGENTS.md`。

## 隔离与环境

- `conftest.py` 初始化 NoneBot 并从 `pyproject.toml` 加载插件；在 NoneBot 初始化前把
  `LOCALSTORE_PLUGIN_DATA_DIR` 指向一次性临时目录，使套件**不读写仓库 `data/` 树**。
  修改 fixture 时必须保持该隔离。
- 异步测试在 session 级事件循环上。
- 从 `nonebot_plugin_lavi` 的 import 放在测试函数内部，避免在 NoneBot 初始化前 import 插件。
- 用 `tmp_path` 获得隔离的持久化目录。

## 命令

- `uv run pytest` 跑全量；`uv run poe test` 以 xdist 跑并产出覆盖率/JUnit。

## 变更约束

- 改动涉及持久化形状、命令行为或跨模块契约时，**新增或更新相应回归测试**并跑全量 pytest。
- 测试命名与现有文件对齐（`test_<subsystem>.py`、`plugin_test.py` 承载命令级交互）。
- `fake.py` 只放事件构造函数；新增适配器时同一文件内按 `fake_<type>_<platform>_v11` 命名。
