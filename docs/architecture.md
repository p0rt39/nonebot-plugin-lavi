# rAwTell 架构参考（描述性）

> 本文是**描述性参考**，不是权威指令。约束性条目见各级 [AGENTS.md](../AGENTS.md)。
> 源码与测试始终是最终事实来源。

## 项目形态

```text
src/nonebot_plugin_rawtell/
├── __init__.py      # NoneBot 集成：__plugin_meta__、配置、插件数据目录
├── config.py        # Config / ScopedConfig（dotenv 前缀 RAWTELL__）
└── protocol.py      # 跨子模块共享的 Pydantic 模型
tests/
├── conftest.py      # NoneBot 初始化、适配器注册、数据目录隔离
├── fake.py          # OneBot V11 假事件构造
└── plugin_test.py   # 插件加载冒烟测试
```

当前处于初始化阶段：只有骨架与一条「零配置可加载」的冒烟测试，业务功能尚未实现。

## 运行时入口

`__init__.py` 是唯一与 NoneBot 生命周期耦合的文件：

- 定义 `__plugin_meta__`（`type="application"`，`config=Config`，`supported_adapters=None`）。
- `require("nonebot_plugin_localstore")` 后用 `store.get_plugin_data_dir()` 取得 `data_dir`。
- 读取 `get_plugin_config(Config).rawtell` 得到 `plugin_config`。

新增命令与生命周期钩子也注册在这里，处理逻辑放同级子模块，避免把业务继续堆进入口文件。

## 新增功能时的落点

| 需要的能力 | 放到哪里 |
|---|---|
| 新的用户配置 | `config.py` 的 `ScopedConfig`，同步 README 配置表 |
| 跨子模块的数据结构 | `protocol.py` |
| 业务流程 / 外部调用 | 新建同级子模块，并在包级 `AGENTS.md` 记录职责 |
| 命令与事件注册 | `__init__.py`，处理函数在子模块 |
| 持久化文件读写 | 以 `data_dir` 为根，原子替换写入 |

## 持久化

插件数据目录来自 `nonebot-plugin-localstore`（`.env` 中可由 `LOCALSTORE_PLUGIN_DATA_DIR`
覆盖）。读写规则：

- 路径只从入口暴露的 `data_dir` 派生，不用 `Path(__file__).parent` 或 `os.getcwd()`。
- 文件写入使用同目录临时文件加 `os.replace()` 原子替换，避免留下半截 JSON。
- 时间戳使用时区感知的 UTC datetime。
- JSON 形状一旦发布即视为对外契约，字段变更需保持向后兼容或提供迁移路径。

## 待定

适配器支持面、数据模型与命令集在功能设计确定后补充到本文与各级 `AGENTS.md`。
