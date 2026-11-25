# rAwTell

**一个 NoneBot2 插件（开发中）**

> 本仓库目前处于初始化阶段：骨架、工具链、二元决策核心与测试已就位；尚无命令入口，
> 业务功能尚未实现。请勿在生产环境启用。

## 介绍

`nonebot-plugin-rawtell` 是一个面向 NoneBot2 的插件模板与开发起点。它提供：

- 可运行的插件入口（`__plugin_meta__`、scoped config、localstore 数据目录）。
- 不依赖 NoneBot 的二元决策核心：参数解析、共享决策上下文、可注入的选择器/计算器。
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
| _暂无_ | | | 功能落地后在此登记，并与 `config.py` 的默认值保持同步 |

## 命令

| 指令 | 权限 | 说明 |
| :--- | :--- | :--- |
| _暂无_ | | | 命令落地后在此登记 |

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
├── __init__.py      # 插件入口、__plugin_meta__、配置与数据目录
├── config.py        # RAWTELL__ 配置模型
├── decision.py      # 二元决策：参数解析与选择器编排
└── protocol.py      # 共享 Pydantic 模型与决策类型
tests/
├── conftest.py      # NoneBot 初始化与数据目录隔离
├── fake.py          # OneBot V11 假事件
├── test_decision.py # 二元决策骨架验收测试
└── plugin_test.py   # 插件加载冒烟测试
docs/                # 描述性参考（架构、测试、发布）
AGENTS.md            # 分层规则文件（根 / 包 / 测试）
```

实现类改动遵循 `AGENTS.md` 中的阶梯：`modify -> ruff -> basedpyright -> focused pytest ->
full pytest -> 本地同步 -> git commit -s`。

## 许可证

Apache License 2.0 © [p0rt39](https://github.com/p0rt39)
