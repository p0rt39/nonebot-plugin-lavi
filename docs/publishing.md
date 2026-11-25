# 发布约束（提炼）

> 本文提炼与本仓库直接相关的 NoneBot 商店发布/合规约束，供各级 AGENTS.md 引用。
> 本文件只承载约束，不复述教程性内容（Matcher、依赖注入、消息处理等请见官方文档）。

## 商店审核红线（违反将被自动拒绝）

1. **命名**
   - 项目名（PyPI/GitHub）：`nonebot-plugin-lavi`（词间 `-`）。
   - 模块名（Python import）：`nonebot_plugin_lavi`（词间 `_`）。

2. **依赖管理**
   - 版本用宽松区间 `>=X.Y,<Z.0`（或 `~=`），不要 `==` 锁死。
   - 必须依赖 `nonebot2`；不要添加 V1 的 `nonebot`。
   - 代码里 import 的第三方库都必须列在 `pyproject.toml` 的 `dependencies`。
   - 直接使用的适配器要显式声明（本仓库以 `nonebot-adapter-onebot` 作为可选 extra）。

3. **本地文件存储**
   - 运行期数据读写必须通过 `nonebot-plugin-localstore`。
   - 不用 `open()`、`Path(__file__).parent`、`os.getcwd()` 等直接定位/读写插件数据。

4. **`__plugin_meta__` 完整**
   - 定义在 `__init__.py` 最外层，提供 `name`、`description`、`usage`、`type`
     （`"application"`）、`homepage`、`config`、`supported_adapters`。

5. **零配置可加载**
   - 无预配置时插件能被 import 且不报错；缺配置时优雅降级而非崩溃。

6. **禁同步阻塞**
   - 异步路径使用 `httpx.AsyncClient` 等异步替代品；长时间同步操作会阻塞整个事件循环。

7. **跨插件依赖用 `require()`**
   - import 可选插件前先 `require("nonebot_plugin_xxx")`。

8. **README 安装方式**
   - 必须展示 `nb plugin install nonebot-plugin-lavi`；不要以旧式 `bot.py` 配置方式作为安装路径。

## 版本与发布

### 当前状态

- 当前版本 `0.1.0`，首个版本尚未发布到 PyPI。
- 发布统一走 `.github/workflows/release.yml`，由 `v*` 标签触发；本地不执行 `uv publish`。
- PyPI 发布使用 GitHub Actions OIDC Trusted Publishing，作业运行在 `release` environment。
- CI 只在 Pull Request 上运行；release workflow 会对被打标签的提交再跑一次测试。
- 标签版本必须与 `pyproject.toml` 的 `version` 一致；workflow 在发布前校验。

### 首次发布前

在 PyPI 配置 pending publisher：

<https://pypi.org/manage/account/publishing/>

| 字段 | 值 |
| :--- | :--- |
| PyPI Project Name | `nonebot-plugin-lavi` |
| Owner | `p0rt39` |
| Repository name | `nonebot-plugin-lavi` |
| Workflow name | `release.yml` |
| Environment name | `release` |

`Environment name` 必须与 `release.yml` 里的 `environment: release` 完全一致。
如需人工确认，可在 GitHub 仓库的 `release` environment 上配置 required reviewers。

发布前在本地执行：

```powershell
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uvx basedpyright==1.40.0
uv run pytest
```

### 发布

确认 `README.md` 与本文档已反映发布状态，提交并推送 `master` 后打标签：

```powershell
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
```

workflow 依次执行：校验 tag 与 `pyproject.toml` 版本、运行测试、`uv build`、
`uv publish --check-url https://pypi.org/simple/`，最后创建 GitHub Release 并上传
wheel/sdist。发布成功后到 <https://nonebot.dev/store/plugins> 提交商店审核。

### 约束

- PyPI 版本不可覆盖；发布内容有误时递增版本重新发布，不重用已上传的版本号。
- 工作流失败后可用同一个 tag 重跑：`--check-url` 跳过已上传文件，GitHub Release
  已存在时改用 `gh release upload --clobber`。
- 发布作业经 `release` environment 运行；拥有仓库 write 权限即可触发标签发布。
- 构建后端为 `uv_build`；改动包数据/依赖时用 `uv build` 并检查随包分发的内容。
  `pyproject.toml` 的 `[tool.uv.build-backend] source-exclude` 把各级 `AGENTS.md`
  排除出发行包——agent 规则属于开发材料，新增子目录规则文件时沿用该 glob。
