# LaVI

**一个面向二元问题的 NoneBot2 决策插件（开发中）**

## 介绍

`nonebot-plugin-lavi` 是一个面向 NoneBot2 的二元决策插件。它提供：

- `/lavi` 命令：回答“是/否”，或从两个空白分隔的候选项中选一个。
- 可插拔算法：内置 `dayan`（大衍筮法）、`geomancy`（地占盾盘）、`obi-ifa`（Obi 宝螺 / Ifa 奥杜）与 `trial`（十三裁判）。

## 安装

使用：

```bash
nb plugin install nonebot-plugin-lavi
```

也可以使用常见 Python 包管理器：

```bash
uv add nonebot-plugin-lavi
```

当前尚未发布到 PyPI，请从源码安装：

```bash
git clone https://github.com/p0rt39/nonebot-plugin-lavi.git
cd nonebot-plugin-lavi
uv sync --all-groups
```

## 配置

所有配置位于 `.env` 中的 `LAVI__...` 作用域。

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `LAVI__ALGORITHM` | `str` | `random` | 默认算法；`random` 为每次决策随机选择，也可填 `dayan`、`geomancy`、`obi-ifa` 或 `trial`。|
| `LAVI__DETAILED` | `bool` | `false` | 详细模式：在简洁回复后追加算法算子数量与演算过程 |

配置的算法名无效时，插件会记录 WARNING 并回退到 `random`。

## 内置算法

- `dayan`（大衍）：模拟大衍筮法。五十根蓍草中取一根不用，余四十九根；每爻三变，第一变按 3:1 移除五根或九根，后两变各按 1:1 移除四根或八根，三变后余数除以四得到 6/7/8/9。爻值概率为 1/16、5/16、7/16、3/16，阴阳各占 8/16。变爻、之卦与阳爻多数都不是 50/50，因此只取本卦六爻阳爻数量的奇偶；六爻阴阳各半，64 种本卦中恰有 32 种回答“是”。
- `geomancy`（地占）：以 16 个由决策上下文直接派生的爻位起四母图，按地占加法（逐行异或）推导四女、四侄、左右见证与裁判。裁判必然是偶数图；按传统简易是非读法，稳定图回答“是”，流动图回答“否”。
- `obi-ifa`（宝螺）：每轮先掷四枚宝螺得到 Obi 字母。首轮 Alafia（4 枚开口）与 Etawa（3 枚开口）为肯定，Okana（1 枚）与 Oyekun（0 枚）为否定。若首轮是 Eyeife（2:2），直接转 Ifa；否则再掷一次 Obi：第二次为 Eyeife 时按首轮结果，第二次不是 Eyeife 时转 Ifa；Ifa 判定为真时按首轮结果，为假则重新开始一轮。Ifa 以八枚宝螺组成奥杜，按单爻数量的奇偶判定。
- `trial`（裁判）：从 `DecisionContext` 派生 13 个 64 位算子；每个算子的高 32 位作为主算子份额，低 32 位作为选票。13 个高半按位多数选出 32 位主算子（全零时取 1），主算子再与每张选票做内积奇偶，得到 13 票；7 票及以上回答“是”。

## 命令

| 指令 | 权限 | 说明 |
| :--- | :--- | :--- |
| `/lavi` | 无 | 按配置算法回答“是”或“否” |
| `/lavi 算法名` | 无 | 用指定算法回答“是”或“否” |
| `/lavi 候选1 候选2` | 无 | 按配置算法从两个候选中选择一个 |
| `/lavi 算法名 候选1 候选2` | 无 | 用指定算法从两个候选中选择一个 |

参数按空白分隔后的字段数解释：

- 0 个字段（`/lavi`）：按配置算法回答“是/否”。
- 1 个字段：视为算法名，未知名称会静默回退到配置算法。
- 2 个字段：始终视为两个候选。
- 3 个字段：视为“算法名 + 两个候选”；首个字段不是已知算法名时拒绝。
- 4 个及以上字段：静默丢弃，按配置算法回答“是/否”。

在 1 或 3 字段形式中，命令参数优先于 `LAVI__ALGORITHM`。指定单次算法时，把算法 ID 放在最前，例如：

```text
/lavi trial 红茶 咖啡    # 使用「裁判」从“红茶”和“咖啡”中选择
/lavi dayan              # 使用「大衍」回答“是/否”
```

## 使用示例

配置算法为 `dayan`（大衍）时，`/lavi 红茶 咖啡` 会从两个候选中选择一个：

```text
🔮 决断仪式：「大衍」
✨ 决断结果：「红茶」
```

设置 `LAVI__DETAILED=true` 后，回复内容后会追加本次算法派生的 64 位算子数量（不含选择算法本身使用的算子）与演算过程。例如：

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

开启详细模式后，各算法会提供：

- 大衍（`dayan`）：六爻逐爻的蓍草移除数、余数与本爻阴阳。
- 地占（`geomancy`）：四母、四女、四侄、左右见证与裁判的图形及稳定/流动。
- 宝螺（`obi-ifa`）：每轮 Obi 字母、Ifa 奥杜、确认或重开。
- 裁判（`trial`）：主算子、13 张选票与肯定票数。

## 开发

推荐使用 `uv`：

```powershell
uv sync --all-groups
```

常用检查：

```powershell
uv run ruff check .
uv run ruff format --check .
uvx basedpyright==1.40.0
uv run pytest
uv run poe test
prek run --all-files
```

### 目录结构

```text
src/nonebot_plugin_lavi/
├── __init__.py              # 插件入口、__plugin_meta__、配置、matcher 注册
├── config.py                # LAVI__ 配置模型
├── protocol.py              # 决策上下文、Algorithm/Explanation/Decision、算子计量与位派生
├── decision.py              # 参数解析与 decide() 编排（产出 Decision）
├── selector.py              # 算法选择策略与注册表校验
├── command.py               # /lavi 处理函数
├── render.py                # 简洁与详细回复的文本渲染
└── decider_algorithms/
    ├── __init__.py          # 显式算法注册表
    ├── dayan.py             # 大衍筮法算法
    ├── geomancy.py          # 地占盾盘算法
    ├── obi_ifa.py           # Obi / Ifa 宝螺算法
    └── trial.py             # 十三裁判算法
tests/
├── conftest.py              # NoneBot 初始化与数据目录隔离
├── fake.py                  # OneBot V11 假事件
├── test_command.py          # 命令参数分派与算法覆盖
├── test_decision.py         # 决策核心契约
├── test_decider_algorithms.py
├── test_render.py           # 回答与参数错误渲染
├── test_selector.py
└── plugin_test.py           # 插件加载与命令交互测试
docs/                        # 描述性参考（架构、测试、发布）
AGENTS.md                    # 分层规则文件（根 / 包 / 测试）
```

## 许可证

Apache License 2.0 © [p0rt39](https://github.com/p0rt39)
