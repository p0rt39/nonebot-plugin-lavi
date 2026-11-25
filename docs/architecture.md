# LaVI 架构参考（描述性）

> 本文是**描述性参考**，不是权威指令。约束性条目见各级 [AGENTS.md](../AGENTS.md)。
> 源码与测试始终是最终事实来源。

## 项目形态

```text
src/nonebot_plugin_lavi/
├── __init__.py              # NoneBot 集成：__plugin_meta__、配置、data_dir、matcher 注册
├── config.py                # Config / ScopedConfig（dotenv 前缀 LAVI__）
├── protocol.py              # 决策上下文、Algorithm/Explanation/Decision、算子计量与位派生
├── decision.py              # 参数解析与选择器→算法编排（产出 Decision，无 NoneBot 依赖）
├── selector.py              # 算法注册表校验与选择策略
├── command.py               # /lavi 处理函数（不持有 Matcher）
├── render.py                # 决策答案的单行文本渲染
└── decider_algorithms/
    ├── __init__.py          # 显式算法注册表
    ├── dayan.py             # 大衍筮法算法
    ├── geomancy.py          # 地占盾盘算法
    ├── obi_ifa.py           # Obi / Ifa 宝螺算法
    └── trial.py             # 十三算子合议算法
tests/
├── conftest.py              # NoneBot 初始化、适配器注册、数据目录隔离
├── fake.py                  # OneBot V11 假事件构造
├── test_command.py          # 命令参数分派与算法覆盖
├── test_decision.py         # 二元决策核心契约
├── test_decider_algorithms.py
├── test_render.py           # 回答与参数错误渲染
├── test_selector.py
└── plugin_test.py           # 插件加载与命令交互测试
```

当前状态：参数解析、决策核心、算法选择与 `/lavi` 命令已接通；决策历史与持久化尚未实现。

## 运行时入口

`__init__.py` 是唯一与 NoneBot 生命周期耦合的文件：

- 定义 `__plugin_meta__`（`type="application"`，`config=Config`，`supported_adapters=None`）。
- `require("nonebot_plugin_localstore")` 后用 `store.get_plugin_data_dir()` 取得 `data_dir`。
- 读取 `get_plugin_config(Config).lavi` 得到 `plugin_config`。
- 用 `build_selector()` 构建一次算法选择器；配置的算法名无效时记录 WARNING 并回退到
  `random`，保证插件仍可加载。命令层可在单次调用中按参数临时构建选择器，覆盖该默认值。
- 注册 `/lavi` matcher，并调用 `command.handle_lavi()`；处理函数不持有 `Matcher`，
  返回的文本已经过 `render.render_answer()` 渲染。

新增命令与生命周期钩子也注册在这里，处理逻辑放同级子模块，避免把业务继续堆进入口文件。

## 二元决策骨架

`protocol.py` 与 `decision.py` 构成不依赖 NoneBot 的决策核心；命令层通过
`command.handle_lavi()` 接入。

```text
arguments ──parse_invocation──> (algorithm?, text)
                                   │
              algorithm? ──build_selector(name)──> per-command selector
                                   │
text ──parse_options──> (affirmative, negative)
                                   │
capture_context() ──> DecisionContext ──selector──> Algorithm
                                                       │
                             Algorithm.calculate(context) ──> bool
                             Algorithm.explain(context) ──> Explanation
                                   │
                                   └────── same object ─────┘
                             result: Decision(answer, algorithm, display_name, operators, steps)
                                        │
                          render_answer / render_detailed
                                        │
                                   multi-line reply
```

- `capture_context()` 只采样一次 UTC 时间、进程 `pid` 与三个独立的 64 位 `nonce`，
  封装为 `DecisionContext`。选择器与算法接收同一个对象，看不到命令原文，也不能各自重新采样。
- `derive_seed(context, purpose=...)` 用 BLAKE2b 把上下文哈希为 64 位种子；
  选择器用 `selector:operator:<1..13>`。算法通过 `derive_algorithm_bits(...)` 以
  `algorithm:<name>:v<version>:<stage>:operator:<i>` 为每个爻位/宝螺位单独派生 64 位
  算子并取最高位，使采样数据直接参与运算，且与选择器的 purpose 域分离。
  `derive_algorithm_operators(...)` 使用同一 purpose 约定返回完整 64 位算子，供
  `trial` 这类需要整字而不仅是最高位的算法使用。
- `selector(context)` 选出一个 `Algorithm`。普通模式调用一次 `calculate()`；详细模式在
  算法提供 `explain()` 时只调用一次 `explain()`，从同一次演算中取得答案与步骤，避免
  重复派生。两种路径都在 `count_operators()` 内执行，记录算法实际派生的 64 位算子数，
  产出 `Decision(answer, algorithm, display_name, operator_count, steps)`。该计数不含
  选择算法本身使用的算子。
- `parse_invocation()` 按空白分隔后的字段数分派：1 个字段视为算法名，2 个字段保持两个
  候选的原解析，3 个字段视为“算法名 + 两个候选”，0 个或 4 个及以上保持原逻辑。命令层为
  1 字段中的有效算法名构建固定选择器，未知名称静默沿用配置选择器；3 字段中的未知名称
  不推演，直接渲染可用算法列表并中止。`random` 也是合法选择值，表示随机选择。
- `parse_options()` 在恰好两个空白分隔字段时按原样、按顺序返回两个候选；其他情况
  （空串、单字段、三个及以上字段）退化为 `"是"`/`"否"`。引号不解析，重复候选不去重，
  大小写与标点保留。
- 选择器或算法抛出的异常原样向上传播；命令层记录日志并回复降级文案，核心不吞异常。
- `Explanation(answer, steps)` 由算法提供，`steps` 每条一行，只使用同一
  `DecisionContext` 的派生值构造，不重新采样；`Decision.steps` 原样交给渲染层。
- `Decision.display_name` 来自 `Algorithm.label`：优先使用 `Algorithm.display_name`，
  未设置时回退到稳定的 `name`。详细模式渲染该显示名；`Decision.algorithm` 仍保留稳定
  ID，便于日志与后续持久化。
- 命令层用 `render.render_answer()` 生成“🔮 决断仪式：「显示名」”与
  “✨ 决断结果：「答案」”两行，简洁模式也显示算法名；`detailed` 开启时改用
  `render.render_detailed()`，空一行后追加“📊 算子数量：…”与“📜 演算过程：…”及其
  步骤行。两种回复都只用纯文本换行与常见标点/emoji，不做边框、对齐或字体宽度计算，
  避免不同适配器的渲染差异。渲染只影响展示，不改变 `decision.decide()` 返回的答案与
  元数据，也不参与随机性。

## 内置算法

四个算法都不创建 `random.Random`，而是让 `DecisionContext` 直接参与位级运算：
`protocol.derive_algorithm_bits()` 为每个采样点派生一个 64 位 BLAKE2b 算子并取最高位；
`trial` 则通过 `derive_algorithm_operators()` 使用完整的 64 位算子。

- `dayan`：五十根蓍草取一根不用，余四十九根；每爻三变，第一变以 3:1 移除五根或
  九根，后两变各以 1:1 移除四根或八根，三变后余数除以四得到 6/7/8/9。爻值概率为
  1/16、5/16、7/16、3/16，因此变爻、之卦和阳爻多数都不适合直接映射为二元结果；
  但阴阳极性（6/8 对 7/9）恰为 8/16 对 8/16。算法取本卦六爻阳爻数量的奇偶，
  64 种本卦中正好 32 种回答“是”，无需多轮重抽或额外去偏。
- `geomancy`：16 个爻位组成四母图（每图四行，1 表示单点/主动，0 表示双点/被动）；
  四女由四母转置得到，四侄、左右见证与裁判按逐行异或得到。裁判必为偶数图；按传统
  简易是非读法，稳定图回答“是”，流动图回答“否”。`FIGURES` 表同时记录 16 图的传统
  稳定/流动属性。
- `obi-ifa`：每轮四枚宝螺给出 Obi 字母（分布 1:4:6:4:1）。首轮 Eyeife 直接转 Ifa；
  首轮非 Eyeife 时再掷一次 Obi：第二次 Eyeife 则按首轮结果，否则转 Ifa；Ifa 为真按
  首轮结果，Ifa 为假重开一轮。Ifa 由八枚宝螺组成奥杜，以单爻数量奇偶判定。重开时
  每个阶段使用带轮次的 purpose，因此每轮都得到新的采样位；该协议最终先验仍为 50/50。
- `trial`：派生 13 个 64 位算子，每个算子的高 32 位作为主算子份额、低 32 位作为选票。
  13 个高半按位多数得到 32 位主算子（全零时取 1）；主算子与每张低半选票做内积奇偶，
  得到 13 票，7 票及以上回答“是”。主算子只依赖高半、选票只依赖低半，两个位域不相交；
  固定主算子后 13 票独立且各半，奇数票多数在组合上恰为 1/2。

四个内置算法都提供 `explain()`：`dayan` 列出六爻的移除数、余数与阴阳；`geomancy`
列出四母/四女/四侄/见证/裁判；`obi-ifa` 列出每轮 Obi、Ifa 奥杜与确认/重开分支；
`trial` 列出主算子、13 张选票与肯定票数。四个算法分别设置显示名「大衍」「地占」
「宝螺」「裁判」。

## 算法选择与注册

- `decider_algorithms/` 每个文件实现一个算法，导出 `ALGORITHM`；`__init__.py` 是显式
  注册表，不使用自动发现。新增算法需要同时改文件与注册表，保证打包与 review 可控。
- `Algorithm` 元数据包含稳定的 `name`、整数 `version`、整数 `weight`、纯函数
  `calculate`、可选 `display_name` 与可选 `explain`。行为变化时递增 `version`，使派生
  种子随契约变化。`display_name` 只用于展示，`label` 在未设置时回退到 `name`。当前
  `weight` 只作为启用标记：`0` 表示禁用，正值不参与概率分配。
- `LAVI__ALGORITHM` 默认 `random`：`selector.py` 从 `DecisionContext` 派生 13 个
  64 位算子；取第 `i` 个算子的第 `i` 位（MSB 起）填入 26 位 `omega` 的前半，取第
  `14 - i` 个算子的倒数第 `i` 位填入后半；对 `omega` 做 BLAKE2b 哈希得到 `lambda`，
  再以 `lambda % N` 选择算法。也可填具体 `name` 固定算法。配置无效时入口记录 WARNING
  并回退到 `random`。
- `/lavi` 在 1 个或 3 个字段时把首字段交给 `build_selector(name=...)`，为本次决策
  覆盖配置选择器；`random` 也可用。1 字段未知时命令层静默沿用配置选择器，3 字段未知时
  `UnknownAlgorithmError` 转为可用算法列表并中止。`available_algorithms()` 负责注册表
  校验、过滤零权重并按 `name` 排序，供命令层列出可选项。
- 算法必须同步、纯函数化，只读 `DecisionContext`；不得访问 NoneBot、网络、文件或全局
  `random`。需要外部资源的算法应在启动阶段预取，而不是在 `calculate` 里阻塞。
- `tests/test_decider_algorithms.py` 验证注册表、算法确定性与上下文熵，并用固定样本
  检查地占盾盘的转置/异或结构、裁判必为偶数图、大衍筮法的变数分布与阳爻奇偶、
  Obi 字母/Ifa 奥杜奇偶与 Eyeife 转 Ifa 分支，以及 `trial` 的位域拆分、逐位多数、
  内积奇偶与 13 票阈值；`tests/test_selector.py`
  用假算法验证固定/随机/禁用/重名规则、`omega` 位映射与 `lambda % N` 选择，
  避免统计型断言；`tests/test_command.py` 验证 1/2/3/4+ 字段分派、未知算法回退或中止、
  以及命令参数对默认选择器的覆盖。

## 新增功能时的落点

| 需要的能力 | 放到哪里 |
|---|---|
| 新的用户配置 | `config.py` 的 `ScopedConfig`，同步 README 配置表 |
| 跨子模块的数据结构 | `protocol.py` |
| 业务流程 / 外部调用 | 新建同级子模块，并在包级 `AGENTS.md` 记录职责 |
| 新的决策算法 | `decider_algorithms/<name>.py`，并在该包 `__init__.py` 注册 |
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

持久化数据模型、决策历史与适配器支持面在功能设计确定后补充到本文与各级 `AGENTS.md`；
`protocol.py`/`decision.py`/`selector.py` 的公开契约以源码与对应测试为准。
