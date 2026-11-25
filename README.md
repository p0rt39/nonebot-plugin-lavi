# rAwTell

**一个面向二元问题的 NoneBot2 决策插件（开发中）**

> 当前已提供 `/rawtell` 命令、可插拔决策算法与选择策略；决策历史尚未持久化。
> 仍在开发中，请勿在生产环境启用。

## 介绍

`nonebot-plugin-rawtell` 是一个面向 NoneBot2 的二元决策插件。它提供：

- `/rawtell` 命令：回答“是/否”，或从两个空白分隔的候选项中选一个。
- 不依赖 NoneBot 的决策核心：参数解析、共享决策上下文、选择器/算法编排与详细结果。
- 可插拔算法：`decider_algorithms/` 下每个算法一个文件，内置 `dayan`（大衍筮法）、
  `geomancy`（地占盾盘）、`obi-ifa`（Obi 宝螺 / Ifa 奥杜）与 `trial`（十三算子合议）。
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
| `RAWTELL__ALGORITHM` | `str` | `random` | 选择算法；`random` 为每次决策随机选择，也可填 `dayan`、`geomancy`、`obi-ifa` 或 `trial` |
| `RAWTELL__DETAILED` | `bool` | `false` | 详细模式：在简洁回复后空行追加算法算子数量与演算过程 |

## 内置算法

- `dayan`（大衍）：模拟大衍筮法。五十根蓍草中取一根不用，余四十九根；每爻三变，第一变按
  3:1 移除五根或九根，后两变各按 1:1 移除四根或八根，三变后余数除以四得到
  6/7/8/9。爻值概率为 1/16、5/16、7/16、3/16，阴阳各占 8/16；变爻、之卦与
  阳爻多数都不是 50/50。因此本插件只取本卦六爻阳爻数量的奇偶：每个爻阴阳各半，
  64 种本卦中恰有 32 种回答“是”。多轮重抽或统计去偏不会带来额外公平性，故不采用。
- `geomancy`（地占）：以 16 个由决策上下文直接派生的爻位起四母图，按地占加法（逐行异或）
  推导四女、四侄、左右见证与裁判。裁判必然是偶数图；按传统简易是非读法，稳定图回答
  “是”，流动图回答“否”。
- `obi-ifa`（宝螺）：每轮先掷四枚宝螺得到 Obi 字母。首轮 Alafia（4 枚开口）与 Etawa（3 枚开口）
  为肯定，Okana（1 枚）与 Oyekun（0 枚）为否定。若首轮是 Eyeife（2:2），直接转 Ifa；
  否则再掷一次 Obi：第二次为 Eyeife 时按首轮结果，第二次不是 Eyeife 时转 Ifa；Ifa 为真
  按首轮结果，Ifa 为假则重新开始一轮。Ifa 以八枚宝螺组成奥杜，按单爻数量的奇偶判定。
- `trial`（裁判）：从 `DecisionContext` 派生 13 个 64 位算子；每个算子的高 32 位作为主算子份额，
  低 32 位作为选票。13 个高半按位多数选出 32 位主算子（全零时取 1），主算子再与每张
  选票做内积奇偶，得到 13 票；7 票及以上回答“是”。主算子与选票使用不相交的位域，
  因此在理想 BLAKE2b 模型下，13 票在给定主算子后独立且各半，最终结果严格 50/50。

前三个算法是对传统占卜结构的程序化模拟，`trial` 是位级合议结构；它们都用于决策娱乐，
不构成宗教实践建议。每个爻位/宝螺位/蓍草变数/选票都从 `DecisionContext` 单独派生的
BLAKE2b 算子取值，与选择器使用同一类位级采样方式，但 purpose 域与算法身份绑定，互不相关。

详细模式中，四个内置算法分别显示为用户友好名称「大衍」「地占」「宝螺」「裁判」；
`RAWTELL__ALGORITHM` 配置仍使用稳定 ID（`dayan`、`geomancy`、`obi-ifa`、`trial`）。

## 命令

| 指令 | 权限 | 说明 |
| :--- | :--- | :--- |
| `/rawtell` | 无 | 回答“是”或“否” |
| `/rawtell 候选1 候选2` | 无 | 从两个空白分隔的候选中选择一个；其他字段数量按“是/否”处理 |

回复使用纯文本换行，不依赖字体宽度、边框或对齐；简洁回复也始终包含算法显示名。
例如 `/rawtell 红茶 咖啡` 选中“红茶”时：

```text
🔮 决断仪式：「大衍」
✨ 决断结果：「红茶」
```

设置 `RAWTELL__DETAILED=true` 后，简洁信息与详细信息之间空一行，追加本次算法派生的
64 位算子数量（不含选择算法本身使用的算子）以及演算过程：

```text
🔮 决断仪式：「大衍」
✨ 决断结果：「红茶」

📊 算子数量：24
📜 演算过程：
初爻：去 5+4+8，余 32，32÷4=8（阴）
二爻：去 5+4+4，余 36，36÷4=9（阳）
三爻：去 5+8+4，余 32，32÷4=8（阴）
四爻：去 5+4+8，余 32，32÷4=8（阴）
五爻：去 9+4+4，余 32，32÷4=8（阴）
上爻：去 5+4+8，余 32，32÷4=8（阴）
阳爻 1 枚，奇偶：奇 → 肯定
```

内置算法的演算过程：

- 大衍（`dayan`）：六爻逐爻的蓍草移除数、余数与本爻阴阳。
- 地占（`geomancy`）：四母、四女、四侄、左右见证与裁判的图形及稳定/流动。
- 宝螺（`obi-ifa`）：每轮 Obi 字母、Ifa 奥杜、确认或重开。
- 裁判（`trial`）：主算子、13 张选票与肯定票数。

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
├── protocol.py              # 决策上下文、Algorithm/Explanation/Decision、算子计量与位派生
├── decision.py              # 参数解析与 decide() 编排（产出 Decision）
├── selector.py              # 算法选择策略与注册表校验
├── command.py               # /rawtell 处理函数
├── render.py                # 决策答案的单行文本渲染
└── decider_algorithms/
    ├── __init__.py          # 显式算法注册表
    ├── dayan.py             # 大衍筮法算法
    ├── geomancy.py          # 地占盾盘算法
    ├── obi_ifa.py           # Obi / Ifa 宝螺算法
    └── trial.py             # 十三算子合议算法
tests/
├── conftest.py              # NoneBot 初始化与数据目录隔离
├── fake.py                  # OneBot V11 假事件
├── test_decision.py         # 决策核心契约
├── test_decider_algorithms.py
├── test_render.py           # 回答单行渲染
├── test_selector.py
└── plugin_test.py           # 插件加载与命令交互测试
docs/                        # 描述性参考（架构、测试、发布）
AGENTS.md                    # 分层规则文件（根 / 包 / 测试）
```

实现类改动遵循 `AGENTS.md` 中的阶梯：`modify -> ruff -> basedpyright -> focused pytest ->
full pytest -> 本地同步 -> git commit -s`。

## 许可证

Apache License 2.0 © [p0rt39](https://github.com/p0rt39)
