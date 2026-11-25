# rAwTell 架构参考（描述性）

> 本文是**描述性参考**，不是权威指令。约束性条目见各级 [AGENTS.md](../AGENTS.md)。
> 源码与测试始终是最终事实来源。

## 项目形态

```text
src/nonebot_plugin_rawtell/
├── __init__.py              # NoneBot 集成：__plugin_meta__、配置、data_dir、matcher 注册
├── config.py                # Config / ScopedConfig（dotenv 前缀 RAWTELL__）
├── protocol.py              # 决策上下文、Algorithm、选择器/计算器类型、种子与位派生
├── decision.py              # 参数解析与选择器→计算器编排（无 NoneBot 依赖）
├── selector.py              # 算法注册表校验与选择策略
├── command.py               # /rawtell 处理函数（不持有 Matcher）
└── decider_algorithms/
    ├── __init__.py          # 显式算法注册表
    ├── dayan.py             # 大衍筮法算法
    ├── geomancy.py          # 地占盾盘算法
    └── obi_ifa.py           # Obi / Ifa 宝螺算法
tests/
├── conftest.py              # NoneBot 初始化、适配器注册、数据目录隔离
├── fake.py                  # OneBot V11 假事件构造
├── test_decision.py         # 二元决策核心契约
├── test_decider_algorithms.py
├── test_selector.py
└── plugin_test.py           # 插件加载与命令交互测试
```

当前状态：参数解析、决策核心、算法选择与 `/rawtell` 命令已接通；决策历史与持久化尚未实现。

## 运行时入口

`__init__.py` 是唯一与 NoneBot 生命周期耦合的文件：

- 定义 `__plugin_meta__`（`type="application"`，`config=Config`，`supported_adapters=None`）。
- `require("nonebot_plugin_localstore")` 后用 `store.get_plugin_data_dir()` 取得 `data_dir`。
- 读取 `get_plugin_config(Config).rawtell` 得到 `plugin_config`。
- 用 `build_selector()` 构建一次算法选择器；配置的算法名无效时记录 WARNING 并回退到
  `random`，保证插件仍可加载。
- 注册 `/rawtell` matcher，并调用 `command.handle_rawtell()`；处理函数不持有 `Matcher`。

新增命令与生命周期钩子也注册在这里，处理逻辑放同级子模块，避免把业务继续堆进入口文件。

## 二元决策骨架

`protocol.py` 与 `decision.py` 构成不依赖 NoneBot 的决策核心；命令层通过
`command.handle_rawtell()` 接入。

```text
arguments ──parse_options──> (affirmative, negative)
                                   │
capture_context() ──> DecisionContext ──selector──> Algorithm
                                                       │
                                        Algorithm.calculate(context) ──> bool
                                   │
                                   └────── same object ─────┘
                                   result: affirmative / negative
```

- `capture_context()` 只采样一次 UTC 时间、进程 `pid` 与三个独立的 64 位 `nonce`，
  封装为 `DecisionContext`。选择器与算法接收同一个对象，看不到命令原文，也不能各自重新采样。
- `derive_seed(context, purpose=...)` 用 BLAKE2b 把上下文哈希为 64 位种子；
  选择器用 `selector:operator:<1..13>`。算法通过 `derive_algorithm_bits(...)` 以
  `algorithm:<name>:v<version>:<stage>:operator:<i>` 为每个爻位/宝螺位单独派生 64 位
  算子并取最高位，使采样数据直接参与运算，且与选择器的 purpose 域分离。
- `selector(context)` 选出一个 `Algorithm`；`decide()` 只调用选择器一次、算法一次。
- `parse_options()` 在恰好两个空白分隔字段时按原样、按顺序返回两个候选；其他情况
  （空串、单字段、三个及以上字段）退化为 `"是"`/`"否"`。引号不解析，重复候选不去重，
  大小写与标点保留。
- 选择器或算法抛出的异常原样向上传播；命令层记录日志并回复降级文案，核心不吞异常。

## 内置算法

三个算法都不创建 `random.Random`，而是让 `DecisionContext` 直接参与位级运算：
`protocol.derive_algorithm_bits()` 为每个采样点派生一个 64 位 BLAKE2b 算子并取最高位。

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

## 算法选择与注册

- `decider_algorithms/` 每个文件实现一个算法，导出 `ALGORITHM`；`__init__.py` 是显式
  注册表，不使用自动发现。新增算法需要同时改文件与注册表，保证打包与 review 可控。
- `Algorithm` 元数据包含稳定的 `name`、整数 `version`、整数 `weight` 与纯函数
  `calculate`。行为变化时递增 `version`，使派生种子随契约变化。当前 `weight` 只作为
  启用标记：`0` 表示禁用，正值不参与概率分配。
- `RAWTELL__ALGORITHM` 默认 `random`：`selector.py` 从 `DecisionContext` 派生 13 个
  64 位算子；取第 `i` 个算子的第 `i` 位（MSB 起）填入 26 位 `omega` 的前半，取第
  `14 - i` 个算子的倒数第 `i` 位填入后半；对 `omega` 做 BLAKE2b 哈希得到 `lambda`，
  再以 `lambda % N` 选择算法。也可填具体 `name` 固定算法。配置无效时入口记录 WARNING
  并回退到 `random`。
- 算法必须同步、纯函数化，只读 `DecisionContext`；不得访问 NoneBot、网络、文件或全局
  `random`。需要外部资源的算法应在启动阶段预取，而不是在 `calculate` 里阻塞。
- `tests/test_decider_algorithms.py` 验证注册表、算法确定性与上下文熵，并用固定样本
  检查地占盾盘的转置/异或结构、裁判必为偶数图、大衍筮法的变数分布与阳爻奇偶，
  以及 Obi 字母、Ifa 奥杜奇偶与 Eyeife 转 Ifa 的分支；`tests/test_selector.py`
  用假算法验证固定/随机/禁用/重名规则、`omega` 位映射与 `lambda % N` 选择，
  避免统计型断言。

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
