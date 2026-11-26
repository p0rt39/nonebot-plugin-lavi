# LaVI

**一个面向二元问题的 NoneBot2 决策插件**

[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-lavi.svg)](https://pypi.python.org/pypi/nonebot-plugin-lavi)

## 介绍

`nonebot-plugin-lavi` 是一个面向 NoneBot2 的二元决策插件。它提供：

- `/lavi` 命令：回答“是/否”，或从两个空白分隔的候选项中选一个。
- `/lavi-review <记录ID>` 命令：凭完整记录 ID 复查历史决策，展示原始记录与复算步骤。
- 滚动历史：最近 1000 条决策原子保存到插件数据目录，可配置上限或暂停。
- 可插拔算法：内置 `dayan`（大衍筮法）、`geomancy`（地占盾盘）、`obi-ifa`（Obi 宝螺 / Ifa 奥杜）与 `trial`（十三裁判）。

## 安装

推荐使用 nb-cli：

```bash
nb plugin install nonebot-plugin-lavi
```

也可以使用常见 Python 包管理器：

```bash
uv add nonebot-plugin-lavi
```

若**不使用** nb-cli 安装，需要自行在 NoneBot 项目的 `pyproject.toml` 中注册插件：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_lavi"]
```

## 配置

所有配置位于 `.env` 中的 `LAVI__...` 作用域。

### 基础配置

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `LAVI__ALGORITHM` | `str` | `random` | 默认算法；`random` 为每次决策随机选择，也可填 `dayan`、`geomancy`、`obi-ifa` 或 `trial`。|
| `LAVI__DETAILED` | `bool` | `false` | 详细模式：在简洁回复后追加算法算子数量与演算过程 |
| `LAVI__HISTORY_LIMIT` | `int` | `1000` | 全部会话共享的最近决策记录上限；`0` 暂停历史读写并保留已有文件。|

配置的算法名无效时，插件会记录 WARNING 并回退到 `random`。

### 自定义文案

回复文案位于 `LAVI__TEXT__...` 作用域：

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `LAVI__TEXT__HEADER` | `str` | `🔮 决断仪式：「{decider}」` | 简洁与详细回复的首行；必须包含 `{decider}`（算法显示名）。|
| `LAVI__TEXT__RESULT` | `str` | `✨ 决断结果：「{answer}」` | 结果行；必须包含 `{answer}`。|
| `LAVI__TEXT__OPERATOR_COUNT` | `str` | `📊 算子数量：{operator_count}` | 详细模式的算子数行；必须包含 `{operator_count}`。|
| `LAVI__TEXT__STEPS_HEADER` | `str` | `📜 演算过程：` | 详细模式的步骤标题；设为空字符串可隐藏该行。|
| `LAVI__TEXT__UNKNOWN_ALGORITHM` | `str` | `⚠️ 未知算法：「{requested}」` | 未知算法错误的标题行；必须包含 `{requested}`。|
| `LAVI__TEXT__AVAILABLE_ALGORITHMS` | `str` | `可用算法：{available}；random（随机）` | 未知算法错误的可用列表行；必须包含 `{available}`。|
| `LAVI__TEXT__UNAVAILABLE` | `str` | `决策算法暂时不可用，请稍后再试。` | 处理异常时的降级回复。|
| `LAVI__TEXT__AFFIRMATIVE` | `str` | `是` | 是/否模式中的肯定回复。|
| `LAVI__TEXT__NEGATIVE` | `str` | `否` | 是/否模式中的否定回复。|
| `LAVI__TEXT__RECORD_ID` | `str` | `记录 ID：{record_id}` | 决策回复与复查首行的记录 ID；必须包含 `{record_id}`。|
| `LAVI__TEXT__RECORD_TIME` | `str` | `决策时间：{timestamp}` | 复查的决策时间行；必须包含 `{timestamp}`。|
| `LAVI__TEXT__RECORD_ALGORITHM` | `str` | `原算法：{algorithm}` | 复查的原算法行；必须包含 `{algorithm}`。|
| `LAVI__TEXT__RECORD_OPTIONS` | `str` | `原候选：{options}` | 复查的原候选行；必须包含 `{options}`。|
| `LAVI__TEXT__RECORD_RESULT` | `str` | `原结果：{result}` | 复查的原结果行；必须包含 `{result}`。|
| `LAVI__TEXT__RECORD_COUNT` | `str` | `原算子数量：{operator_count}` | 复查的原算子数行；必须包含 `{operator_count}`。|
| `LAVI__TEXT__HISTORY_DISABLED_DECISION` | `str` | `历史记录已关闭，本次决策无法复查。` | `LAVI__HISTORY_LIMIT=0` 时附加在决策回复末行。|
| `LAVI__TEXT__HISTORY_WRITE_FAILED` | `str` | `记录未保存，本次决策无法复查。` | 历史写入失败时附加在决策回复末行。|
| `LAVI__TEXT__REVIEW_USAGE` | `str` | `用法：/lavi-review <记录ID>` | 记录 ID 格式错误时的回复。|
| `LAVI__TEXT__HISTORY_DISABLED` | `str` | `历史记录已关闭。` | 暂停历史时复查的回复。|
| `LAVI__TEXT__RECORD_MISSING` | `str` | `记录不存在或已滚动移除。` | 记录不在当前窗口时的回复。|
| `LAVI__TEXT__HISTORY_UNAVAILABLE` | `str` | `历史记录暂时不可用，请稍后再试。` | 历史文件不可读时的回复。|
| `LAVI__TEXT__REVIEW_VERSION_UNAVAILABLE` | `str` | `无法复算：原算法版本不可用。` | 原算法版本缺失时的复查状态。|
| `LAVI__TEXT__REVIEW_MATCH` | `str` | `复查一致。` | 结果与算子数都一致时的复查状态。|
| `LAVI__TEXT__REVIEW_MISMATCH` | `str` | `复查不一致。` | 结果或算子数不一致时的复查状态。|
| `LAVI__TEXT__REVIEW_FAILED` | `str` | `复算失败。` | 复算抛错时的复查状态。|

模板字段使用 Python 标准 `str.format` 语法：必填占位符必须出现，字面量花括号写成 `{{` 和 `}}`；不支持 `!r` 转换或 `:...` 格式说明符。

若缺少必填占位符、使用不支持的占位符或花括号不配对，插件会拒绝加载。

例如：

```dotenv
LAVI__TEXT__HEADER="🎴 神谕：「{decider}」"
LAVI__TEXT__RESULT="🎯 结果：「{answer}」"
LAVI__TEXT__AFFIRMATIVE="行"
LAVI__TEXT__NEGATIVE="不行"
```

之后 `/lavi` 的默认回复会变成：

```text
🎴 神谕：「大衍」
🎯 结果：「行」
```

## 内置算法

- `dayan`（大衍）：模拟大衍筮法。五十根蓍草中取一根不用，余四十九根；每爻三变，第一变按 3:1 移除五根或九根，后两变各按 1:1 移除四根或八根，三变后余数除以四得到 6/7/8/9。爻值概率为 1/16、5/16、7/16、3/16，阴阳各占 8/16。变爻、之卦与阳爻多数都不是 50/50，因此只取本卦六爻阳爻数量的奇偶；六爻阴阳各半，64 种本卦中恰有 32 种回答“是”。
- `geomancy`（地占）：以 16 个由决策上下文直接派生的爻位起四母图，按地占加法（逐行异或）推导四女、四侄、左右见证与裁判。裁判必然是偶数图；按传统简易是非读法，稳定图回答“是”，流动图回答“否”。
- `obi-ifa`（宝螺）：每轮先掷四枚宝螺得到 Obi 字母。首轮 Alafia（4 枚开口）与 Etawa（3 枚开口）为肯定，Okana（1 枚）与 Oyekun（0 枚）为否定。若首轮是 Eyeife（2:2），直接转 Ifa；否则再掷一次 Obi：第二次为 Eyeife 时按首轮结果，第二次不是 Eyeife 时转 Ifa；Ifa 判定为真时按首轮结果，为假则重新开始一轮。Ifa 以八枚宝螺组成奥杜，按单爻数量的奇偶判定。
- `trial`（裁判）：从 `DecisionContext` 派生 13 个 64 位算子；每个算子的高 32 位作为主算子份额，低 32 位作为选票。13 个高半按位多数选出 32 位主算子（全零时取 1），主算子再与每张选票做内积奇偶，得到 13 票；7 票及以上回答“是”。

## 命令

| 指令 | 权限 | 说明 |
| :--- | :--- | :--- |
| `/lavi` | 无 | 按配置算法给出肯定/否定回复（默认“是/否”） |
| `/lavi 算法名` | 无 | 用指定算法给出肯定/否定回复（默认“是/否”） |
| `/lavi 候选1 候选2` | 无 | 按配置算法从两个候选中选择一个 |
| `/lavi 算法名 候选1 候选2` | 无 | 用指定算法从两个候选中选择一个 |
| `/lavi-review <记录ID>` | 无（持有完整 ID 即可，可跨会话） | 展示原决策并用原始采样与算法版本复算 |

参数按空白分隔后的字段数解释：

- 0 个字段（`/lavi`）：按配置算法给出肯定/否定回复（默认“是/否”）。
- 1 个字段：视为算法名，未知名称会静默回退到配置算法。
- 2 个字段：始终视为两个候选。
- 3 个字段：视为“算法名 + 两个候选”；首个字段不是已知算法名时拒绝。
- 4 个及以上字段：静默丢弃，按配置算法给出肯定/否定回复（默认“是/否”）。

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

## 决策记录与复查

每次成功的 `/lavi` 决策都会在回复末行返回记录 ID，并默认把最近 1000 条记录保存到插件数据目录的 `history.json`。上限由 `LAVI__HISTORY_LIMIT` 控制，全部会话共享。

```text
🔮 决断仪式：「裁判」
✨ 决断结果：「红茶」
记录 ID：3f1c2a9e-5f0d-4c1b-9a77-2d6f1e8b4c30
```

任何持有完整记录 ID 的人都可以在任意会话中复查：

```text
/lavi-review 3f1c2a9e-5f0d-4c1b-9a77-2d6f1e8b4c30
```

复查只读取记录，不采样新的随机数，也不重新选择算法：它按记录中的算法名与版本定位实现，用原始 `DecisionContext`、原候选与原文案重新演算。回复先展示记录 ID、UTC 决策时间、原算法（显示名与稳定标识）、原候选、原结果与原算子数，再展示复算的胜方、算子数与步骤，末行给出核对状态（`复查一致。`、`复查不一致。`、`无法复算：原算法版本不可用。` 或 `复算失败。`）。

记录只包含复算所需的采样（时间、进程与三个 nonce）、候选、胜方和算法元数据；不保存用户/群/适配器身份，也不保存聊天原文与可再生的演算步骤。ID 必须完整且为标准 36 字符 UUIDv4，插件不提供可枚举的记录列表。

`LAVI__HISTORY_LIMIT=0` 会暂停历史读写：决策仍返回答案与一次性 ID，但会附加“历史记录已关闭”提示，已有 `history.json` 保持不变；重新启用后，仍在当前窗口内的旧记录可继续复查。历史文件损坏或写入失败不会阻止本次决策，回复会附加“记录未保存”提示并保留原文件。

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
├── protocol.py              # 决策上下文、DecisionRecord、Algorithm/Decision、算子计量与位派生
├── decision.py              # 参数解析与 decide() 编排（产出 Decision）
├── selector.py              # 算法选择策略与注册表校验
├── command.py               # /lavi 与 /lavi-review 处理函数
├── storage.py               # 决策记录的原子滚动持久化
├── render.py                # 简洁、详细与复查回复的文本渲染
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
├── test_config.py           # 文案配置默认值与校验
├── test_decision.py         # 决策核心契约
├── test_decider_algorithms.py
├── test_render.py           # 回答、详细回复与复查渲染
├── test_selector.py
├── test_storage.py          # 滚动存储、锁、原子替换与损坏恢复
└── plugin_test.py           # 插件加载、命令交互与跨会话复查
docs/                        # 描述性参考（架构、测试、发布）
AGENTS.md                    # 分层规则文件（根 / 包 / 测试）
```

## 许可证

Apache License 2.0 © [p0rt39](https://github.com/p0rt39)
