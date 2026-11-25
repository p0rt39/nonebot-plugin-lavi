# rAwTell

**一个面向二元问题的 NoneBot2 决策插件（开发中）**

> 当前已提供 `/rawtell` 命令、可插拔决策算法与选择策略；决策历史尚未持久化。
> 仍在开发中，请勿在生产环境启用。

## 介绍

`nonebot-plugin-rawtell` 是一个面向 NoneBot2 的二元决策插件。它提供：

- `/rawtell` 命令：回答“是/否”，或从两个空白分隔的候选项中选一个。
- 不依赖 NoneBot 的决策核心：参数解析、共享决策上下文、选择器/计算器编排。
- 可插拔算法：`decider_algorithms/` 下每个算法一个文件，内置 `coin` 与 `dice`。
- 算法选择策略：默认每次随机，也可通过 `RAWTELL__ALGORITHM` 固定算法。
- 分层 `AGENTS.md` 规则文件与 `docs/` 描述性参考。
- ruff、BasedPyright、pytest/nonebug、prek 的检查链。
- 测试环境隔离：套件不读写仓库内的 `data/`。

## 安装

```bash
nb plugin install nonebot-plugin-rawtell
```

也可以使用常见 Python 包管理器：

```bash
uv add nonebot-plugin-rawtell
```

由于尚未发布到 PyPI，当前实际使用方式是从源码安装：

```bash
git clone https://github.com/p0rt39/nonebot-plugin-rawtell.git
cd nonebot-plugin-rawtell
uv sync --all-groups
```

## 配置

所有配置位于 `.env` 中的 `RAWTELL__...` 作用域。插件可以零配置加载。

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `RAWTELL__ALGORITHM` | `str` | `random` | 选择算法；`random` 为每次决策随机选择，也可填 `coin` 或 `dice` |

## 命令

| 指令 | 权限 | 说明 |
| :--- | :--- | :--- |
| `/rawtell` | 无 | 回答“是”或“否” |
| `/rawtell 候选1 候选2` | 无 | 从两个空白分隔的候选中选择一个；其他字段数量按“是/否”处理 |

## 开发

推荐使用 `uv`：

```powershell
uv sync --all-groups
```

常用检查（先执行上面的 `uv sync --all-groups`；`uvx basedpyright` 自带工具，但仍按 `.venv`
解析导入）：

```powershell
uv run ruff check .
uv run ruff format --check .
uvx basedpyright==1.40.0
uv run pytest
uv run poe test
prek run --all-files
```

测试会把插件的插件数据目录指向一次性临时目录，不会读写仓库内的 `data/`。

### 目录结构

```text
src/nonebot_plugin_rawtell/
├── __init__.py              # 插件入口、__plugin_meta__、配置、matcher 注册
├── config.py                # RAWTELL__ 配置模型
├── protocol.py              # 决策上下文、Algorithm、选择器/计算器类型
├── decision.py              # 参数解析与 decide() 编排
├── selector.py              # 算法选择策略与注册表校验
├── command.py               # /rawtell 处理函数
└── decider_algorithms/
    ├── __init__.py          # 显式算法注册表
    ├── coin.py
    └── dice.py
tests/
├── conftest.py              # NoneBot 初始化与数据目录隔离
├── fake.py                  # OneBot V11 假事件
├── test_decision.py         # 决策核心契约
├── test_decider_algorithms.py
├── test_selector.py
└── plugin_test.py           # 插件加载与命令交互测试
docs/                        # 描述性参考（架构、测试、发布）
AGENTS.md                    # 分层规则文件（根 / 包 / 测试）
```

实现类改动遵循 `AGENTS.md` 中的阶梯：`modify -> ruff -> basedpyright -> focused pytest ->
full pytest -> 本地同步 -> git commit -s`。

## 许可证

Apache License 2.0 © [p0rt39](https://github.com/p0rt39)
