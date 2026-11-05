# AGENTS.md — AI / 智能体贡献者须知

本文件是本仓库 AI 协作规则的唯一真源；`CLAUDE.md` 仅通过 `@AGENTS.md` 导入本文件。

处理本仓库的**提交 / 推送 / PR / Issue 等任务前**，必须先读取 [`CONTRIBUTING.md`](CONTRIBUTING.md)，并把其中的「⚡ AI / 智能体贡献者硬性规则」**注入你的执行约束（提示词）**，在任务全程严格遵循。

## ⛔ 上游只读（最高优先级红线）

**本仓库绝不向 `ardeyouxipianyi/workbuddy2api-hub` 这个上游仓库推送任何内容**：不 push、不发 PR、不开 Issue、不发评论——对上游**只读**。实际 origin 为 `HeWenbin-bobo/workbuddy2api-hub`；若遇到同名 remote 或 fork 网络中的上游地址，一律不得作为推送目标。任何「同步回上游」「给上游提个 PR」的建议都应拒绝并向用户说明本红线。

## 使用导航

| 要做的事 | 先读这里 |
|---|---|
| 提交 / 推送 / PR / Issue / 冒烟门禁 | [`CONTRIBUTING.md`](CONTRIBUTING.md)（硬性规则节必读）+ 下方「Git / GitHub 协作规则」 |
| 项目定位、快速启动、API 端点、测试命令 | [`README.md`](README.md) |
| 历史版本变更与发布口径 | [`docs/CHANGELOG.md`](docs/CHANGELOG.md) |
| 媒体（生图/生视频）实现与测试计划 | `docs/MEDIA-IMPL.md` / `docs/MEDIA-PLAN.md` / `docs/MEDIA-TEST-PLAN.md` |
| 新增 AI 客户端一键配置 | [`docs/CONTRIBUTING-智能体配置.md`](docs/CONTRIBUTING-智能体配置.md)（注册表 + 文本编辑器规范 + 测试清单） |
| 了解模块职责 | 下方「项目结构速查」 |
| 写一次性脚本、杀进程、跑长任务 | 下方「进程与窗口操作安全」+「文档 / 脚本 / 测试治理」 |
| 排查历史缺陷 | 下方「踩过的坑」按编号/函数/错误文本检索，编号不因整理重排 |

## 项目结构速查

- **单文件网关核心**：`wb_proxy.py`（约 2.5 万行，含 `server_version = "wb-proxy/<ver>"`，HTTP 服务、协议转换、看板静态页全部内嵌）。改它之前先定位到目标类/函数再小步编辑，不全文通读。
- **功能模块**（`wb_*.py`，按职能分组）：
  - 账号与身份：`wb_accounts.py`、`wb_identity.py`、`wb_fingerprint.py`（设备指纹）、`wb_ipintel.py`
  - 调度与出口：`wb_scheduler.py`、`wb_egress.py`、`wb_upstream_pool.py`、`wb_tiers.py`、`wb_quota_scan.py`、`wb_probes.py`
  - 协议与提示词：`wb_prompt.py`、`wb_webprompts.py`、`wb_webagent.py`、`wb_webtools.py`
  - CodeArts 出口：`wb_codearts.py`、`wb_codearts_crypto.py`
  - 媒体：`wb_media.py`、`wb_media_client.py`、`wb_media_tasks.py`
  - 用量/定价/目录：`wb_usage_io.py`、`wb_pricing.py`、`pricing/`、`wb_catalog.py`、`catalog/`、`wb_modelsdev.py`
  - 任务与福利：`wb_tasks.py`、`wb_activity.py`
  - 客户端一键配置：`wb_agents.py`（注册表 `CLIENTS` + 文本级 Upserter + 备份回滚，规范见 `docs/CONTRIBUTING-智能体配置.md`）
  - 更新：`wb_updates.py`、`wb_update_apply.py`、`wb_update_external.py`、`wb_update_portable.py`、`wb_update_request.py`
  - 其余：`wb_settings.py`、`wb_logstore.py`、`wb_atrest.py`、`wb_window_probe.py`
- **看板**：`dashboard.html`（单文件前端，改文案须同步词典——繁体有测试钉住，英文词典键与 HTML 文本逐字一致）。
- **测试**：`tests/run_all.py`（全量入口，支持名字过滤如 `python tests/run_all.py realm`）；单套件 `tests/_test_xxx.py` 直接跑；JS 套件需 PATH 上有 `node`；`tests/_mobile_check.py` 为独立 Playwright 布局检查（手动跑）。
- **脚本与运维**：`scripts/`（含 `check_clean_checkout.py`）、`ops/`、`tools/`、`release/`（发布工具与门禁）、`wrt/`（OpenWrt 打包，脚本须保 755）。
- **运行产物**：`accounts/`（账号凭据、集成状态账本、配置备份）、`usage/`（用量流水）——**绝不允许入库或夹带进提交**。

## 核心子系统架构要点（改代码前必读）

> 本节按子系统列出「改之前必须知道的不变量与判据」。新增子系统条目时，只写「不看就会改错」的契约，不复述代码。

### 单文件网关核心（`wb_proxy.py`）

- **版本号唯一来源**：`server_version = "wb-proxy/<ver>"`（约 19485 行附近），改版本号只改这一处；`get_version()` 从它派生，不要反向引用。
- **看板静态页内嵌**：dashboard.html 以字符串形式内嵌在 `wb_proxy.py` 中，改看板结构要同步改 Python 侧的 HTML 模板；两者漂移会导致「页面能开但功能错位」。
- **路由与 Handler 分离**：HTTP 路由表在 `wb_proxy.py` 顶部，业务 Handler 在对应 `wb_*.py` 模块；新增端点先注册路由再挂 Handler，不要在一个文件里写全栈。
- **协议转换层**：OpenAI Chat Completions / Responses / Anthropic Messages 三种协议的出入参转换都在 `wb_proxy.py` 与 `wb_prompt.py` 交界处，改协议字段时三种格式都要跑通（冒烟门禁覆盖）。

### 账号池与调度（`wb_accounts.py` / `wb_scheduler.py` / `wb_tiers.py`）

- **设备指纹隔离**：每个账号的 `wb_fingerprint.py` 派生指纹是风控识别的基础，改指纹派生逻辑必须全量回归（上游会按指纹聚类封号）。
- **出口绑定**：账号 → 出口代理槽（`wb_egress.py`）→ 上游（`wb_upstream_pool.py`）是三级绑定，改其中一级要核对另外两级的降级路径（无代理时回落直连、无账号时返回 503）。
- **配额轮转**：`wb_scheduler.py` 的配额模型是「每账号独立额度 + 全局故障转移」，改轮转策略先在 `wb_quota_scan.py` 的探测口径上对齐，不要假设所有账号同余量。

### 智能体一键配置（`wb_agents.py`）

改这个模块前必须先读 [`docs/CONTRIBUTING-智能体配置.md`](docs/CONTRIBUTING-智能体配置.md)，要点：

- **三原则**：纯标准库（不引入 YAML/TOML 三方库）；非破坏性文本级编辑（Upserter 只局部插替，绝不重排/抹除用户未改的行）；备份先行 + 两阶段写入 + 异常回滚。
- **新增客户端三步**：写 `_apply_<id>()` → 注册 `CLIENTS` 字典 → `tests/_test_agents.py` 加往返测试；后端 `/agents` 与看板自动获得新条目，核心调度零改动。
- **首次原件锁定**：状态账本 `accounts/integration-state.json` 记住首次接入前的干净配置，之后无论 apply 多少次，restore 始终回到**首次**备份，绝不把改过的配置误当原件。
- **权限收紧**：写出的文件含 API Key，一律 `0o600` 落盘；用户手动加固过的更严权限（如 `0400`）原样保留，不往回打。
- **CLI 与看板共用一条生成路径**：`plan()` 是纯函数，`integrate()` 先 `plan()` 再两阶段写入——CLI `--dry-run` 与真实写入逐字节一致，改生成逻辑只改一处。

### 看板（`dashboard.html`）

- **单文件前端**：全部 HTML/CSS/JS 在一个文件里，改文案必须同步词典（繁体有测试钉住，英文词典键与 HTML 文本逐字一致，否则英文界面回落中文）。
- **布局检查**：`tests/_mobile_check.py` 是独立的 Playwright 手机/桌面布局检查器，改 CSS 后按需手动跑（不在 `run_all.py` 套件集里）。
- **与后端的契约**：`/agents`、`/v1/models`、`/health` 等端点的返回结构是前后端契约，改字段名或嵌套层级要同步改看板渲染逻辑（`dashboard.html` 顶部有契约注释）。

### 媒体模块（`wb_media.py` / `wb_media_client.py` / `wb_media_tasks.py`）

- **改之前必读**：`docs/MEDIA-IMPL.md`（实现）、`docs/MEDIA-PLAN.md`（计划）、`docs/MEDIA-TEST-PLAN.md`（测试计划）——三份文档覆盖生图/生视频的完整链路与验收口径。
- **异步任务**：生视频是异步任务（`wb_media_tasks.py` 本地并发排队与空闲调度），改任务生命周期要核对 `usage/` 流水与 `accounts/` 状态的落盘点。

## Git / GitHub 协作规则（提交 / 推送 / PR 前必读）

### 三条底线

1. **一个 PR 一件事**：可独立评审、可独立回滚；跨主题拆成多个 PR。
2. **分支基于最新 main**：开 PR 前先 rebase / 重放补丁；分支落后且与 main 改过同一批文件时，解冲突**必须两边都留**。
3. **不许弄丢 main 的近期改动**：合并结果里 base 自 merge-base 以来新增的代码必须还在（revert guard CI 自动核对，红了先 rebase；确认无碍由维护者加 `revert-confirmed` 标签放行）。

> 由来看踩坑 1（issue #270）：一次解冲突「取一侧」让 `dashboard.html` 整块消失、CI 6 红。

### 提交文本

- **主题**（commit subject / PR 标题）：`<type>(<scope>): 中文摘要`，type 用 `feat` / `fix` / `perf` / `test` / `docs` / `refactor` / `wrt`；简洁，中文或中英双语。
- **正文与评论**（commit 正文、PR 描述、Review / Issue 回复）：**中英双语**。
- **PR 正文至少写清五件事**：① 动机（关联 issue / 用户场景 / 上一 PR 跟进）；② 做了什么（字段名、默认值、开关、边界条件，别只写「优化了 X」）；③ 怎么验证（跑过的命令 + 数字）；④ 影响面与回滚；⑤ 与其他 PR 的关系（互斥 / 互补 / 依赖）。

### 冲突与合并

- 冲突**在分支上解、两边都留**（不要「取一侧」）；解完 push 回分支让 CI 重跑。**不要**在本地解完直接 push main——PR 触发的 CI 看不到那条路。
- **合并后 main 的 CI 必须保持绿**；发现坏了优先**确定性回退**（`git read-tree -u --reset <good-sha>` 后提交，或 revert），不要在红的基础上「前向补」。
- **别用改测试消红**：测试红了先判断是自己的回归还是测试本身写错；删断言 / 改预期必须有明确理由并写进 PR 说明。

### 发布门禁

- release 流水线是强门禁：打 `v*` 标签时必须拿到该提交**完整测试矩阵逐腿通过**才允许写 release——**main 红了 = 全项目发不出新版**，「把 CI 修绿」不是可选项。
- 推 `v*` tag 时 CI 额外断言 **tag == 源码版本**（`server_version`，`-ci` 演练 tag 豁免）。

## 通用协作与交付纪律

- **文档与代码不一致时，以可执行现状为准**并同步修文档，不凭文档臆断实现。
- **只做当前任务必要改动**，优先复用现有模块；处理反馈时先还原完整业务契约，检查同语义涉及的路由、调度、看板、测试和文档，禁止逐点堆补丁。
- **未经明确确认不执行 `git commit/tag/push`**；`reset/rebase`、强推、删历史必须明确指示。提交前检查 `git status` 与 `git diff --cached`。
- **凭据/隐私零入库**：`accounts/`、`usage/`、密钥、token、本机绝对路径、个人信息一律不进提交；验收报告不复制敏感原值。
- **依赖口径**：纯 Python 标准库、兼容 Python 3.9（CI 矩阵 3.9/3.12 × Ubuntu/Windows）——新增第三方依赖基本等于违规。
- **配置派生值在运行时计算，不持久化**；新增配置须同步示例配置与文档，并核对「UI 控件 → 环境变量/配置文件 → 模块读取 → 运行时生效」的完整传递链。
- **行为变更给开关、默认关**；老安装行为不变。
- **版本号三处一致**：`wb_proxy.py` 的 `server_version`、打包脚本、tag（release 门禁核对）。
- **用户可见能力、启动/部署或交付结构变化须同步专题文档与 README「六、版本更新记录」`### Unreleased` 段**；新增/删除测试套件须同步 README 套件计数（有测试钉住）。
- **文本卫生**：文本文件 LF；可执行脚本保 755（`wrt/` 尤其）。
- **异步/流式任务失败必须写日志且对用户可见**；外部调用必须有硬超时，非幂等提交不得盲目自动重试，应先核查是否已执行及产物状态。
- **UI 改动必须做真实渲染冒烟**（截图与关键交互）；引用实测数据时注明样本量、环境和条件。
- **长文件优先小块 Edit**；较大 Write/Edit 后检查 diff，出现乱码、重复或异常截断立即停止并恢复，不带病提交。
- **较大改动收官时说明**：改了什么、原因、验证、未验证项、风险和回滚方式；纯文档改动可不跑代码测试，但须核对命令、路径和文件名。

## 文档 / 脚本 / 测试治理

- **一次性脚本不归档**：调试用的一次性脚本、探针、截图，跑完即删；仓库只留可复用的。临时产物放 `tests/_mobile_check.py` 级别的正式工具才入库，其余走 `archive/` 之外的临时目录。
- **文档改动核对三件套**：命令、路径、文件名——纯文档 PR 不跑代码测试，但这三样必须逐一验证存在。
- **套件计数钉住**：新增/删除 `tests/_test_*.py` / `tests/_test_*.js` 后，README 的「N 个套件：X 个 Python + Y 个 JS」必须同步更新（`tests/run_all.py` 顶部注释与 CI 都会核对）。
- **测试文件命名**：`tests/_test_<主题>.py` 或 `tests/_test_<主题>.js`，下划线前缀是 `run_all.py` 的发现约定。
- **文档归位**：指南类文档放 `docs/`（如 `docs/CONTRIBUTING-智能体配置.md`），历史版本记录放 `docs/CHANGELOG.md`；README 只保留项目定位、快速开始、主要入口和「六、版本更新记录」的 `### Unreleased` 段。

## 进程与窗口操作安全

- **绝不按进程名全局匹配杀进程**（`taskkill /IM python.exe` / `Stop-Process -Name python*` 等一律禁止）——本机可能同时跑着多个网关实例、测试套件和其他 Python 服务。只按 PID 精确终止，且先确认 `CommandLine` 含本仓库路径或目标端口。
- **杀进程前先看端口归属**：`netstat -ano | findstr :<port>` 或 `Get-NetTCPConnection -LocalPort <port>` 拿到 PID 再终止；端口 8788 上的活跃实例可能是用户正在用的对话链路，冒烟测试一律换隔离端口（8799 等），不要动它。
- **长任务/测试脱离会话跑**：`run_in_background` 有 2h 上限；需要更久就用 `powershell Start-Process -WindowStyle Hidden` 起独立进程，日志落盘。

## 编辑与补丁纪律

- **补丁脚本用 Write 工具落盘再执行**，不走 Bash heredoc——Git Bash 的 heredoc 会把 `\\n` 折半成真换行、把 `\\x00` 折成 NUL 字节写进 .py（AGENTS_.md 踩坑 23/28），精确字符串锚点因此静默失效。含反斜杠的锚点改用 r 原始字符串，或按行号/行前缀定位再插入。
- **Python 写源码文件统一 `open(p, "w", encoding="utf-8", newline="\\n")`**，或按字节 `replace(b"\\r\\n", b"\\n")` 后 `write_bytes`——`Path.write_text()` 默认 `newline=None` 会把已含 `\\r\\n` 的文本再翻译一次成 `\\r\\r\\n`（AGENTS_.md 踩坑 28）。写完必须 `ast.parse` 验证。
- **每个 assert 失败都会让其后的编辑全部不落盘**——补丁脚本里事后要逐项 grep 核验关键锚点真的写进去了，不能只看脚本退出码。

## 验证与验收

- **冒烟测试是提交前硬性门禁**（全过才允许提交/推送），详见 CONTRIBUTING 硬性规则第 2 条：
  - 端口 8788 被占用时**不要停它**（可能是活跃对话链路），换隔离端口（如 8799）起测试实例；
  - Web 面板能打开、可登录、无 JS 报错；
  - 服务能启动、日志无报错；
  - **端到端真实请求**：网关 → WorkBuddy 上游完整链路，收到真实模型回复才算通过。本地测试全绿 ≠ 链路可用。
- **CI 三条腿全绿才算过**：ubuntu 3.9 / ubuntu 3.12 / windows 3.12；`tag matches source version` 只在打标签时跑，PR 上 skipped 属正常。
- 跑完全量矩阵后执行 `python scripts/check_clean_checkout.py`（套件不许写脏仓库）。
- 测试套件超时要主动调：`python tests/run_all.py --timeout 300` 起步，长跑套件别把默认超时当 bug 信号。

## 踩过的坑（Bug 教训，勿重蹈）

> 编号是历史交叉引用的稳定标识，不因整理而重排；新增教训从当前最大编号 +1 开始（当前下一条为 8）。
>
> **分段索引**：1～2 合并与提交｜3～5 配置写入与权限｜6 进程与窗口操作｜7 编辑与补丁。

### 1～2：合并与提交

1. **解冲突「取一侧」会把别人已合进 main 的工作整块弄丢**（issue #270）：一次合并让 `dashboard.html` 的 #265 表头排序 / #261 签到记录 / #262 更新检查 / #263 优先调度设置 UI 整块消失，CI 6 红。判据：合并结果里 base 自 merge-base 以来新增的代码必须还在；分支落后先 rebase，冲突解在分支上、push 回分支让 CI 重跑，**不要**本地解完直接 push main。

2. **本地测试全绿 ≠ 网关链路可用**：一次「拉最新后请求全挂」事故催生了冒烟硬性门禁——必须覆盖到上游真实响应（token 注入、上游应答、真实模型回复），面板能开不算通过。

### 3～5：配置写入与权限

3. **凭据文件权限不能沿用 `open()` 默认**（issue #345 背景）：DSH 桌面端会因凭据文件可被属主之外读取而拒绝启动；一键配置写出的文件必须 `0o600` 落盘，且用户手动加固过的更严权限（`0400`）不得被打回。备份文件与 `restore()` 写回同规。

4. **非交互环境缺 Key 时禁止 `getpass` 阻塞**：Windows 上 NUL 设备的 `isatty()` 也为真，而 `getpass` 会直接读 `CONIN$`——在被拉起、没有控制台的进程里会造成永久阻塞。判据：stdin/stdout **都是终端**才提示，否则报错退出（码 1）。

5. **共享可变子表必须深拷贝**：同一份 provider 字典会分别写进 DSH 各 profile 的 `cordis.patch.yml`——`_apply_dsh()` 用 `json.loads(json.dumps(...))` 逐 profile 深拷贝。凡「一份生成结果写多处」的路径，先问引用是否被共享。

### 6：进程与窗口操作

6. **「杀掉占用端口的进程」前必须先确认归属**：本机可能同时存在多个网关实例、测试套件 spawner 和其他 Python 服务。`Get-Process python*` / `taskkill /IM python.exe` 这类按进程名全局匹配的做法会误杀无关服务。判据：先 `netstat -ano | findstr :<port>` 或 `Get-NetTCPConnection -LocalPort <port>` 锁定 PID，再 `taskkill /PID <pid>`；终止前 `Get-CimInstance Win32_Process -Filter "ProcessId=<pid>"` 核对 `CommandLine` 含本仓库路径或目标端口。

### 7：编辑与补丁

7. **heredoc 补丁的锚点静默失效**：Git Bash 的 heredoc 会把脚本源码里的 `\\n` 折半成真换行、`\\x00` 折成 NUL 字节写进 .py，导致精确字符串锚点 count=0 但脚本退出码仍为 0。判据：补丁脚本一律用 Write 工具落盘再执行；含反斜杠的锚点改用 r 原始字符串；补丁脚本跑完必须逐项 grep 核验关键锚点真的写进去了，不能只看退出码（AGENTS_.md 踩坑 23/28，Windows 上 Python 编辑源码的通用坑）。

## 用户偏好

- **沟通语言**：中文交流；文档、prompt、提交主题全部用简体中文（中英双语仅限 PR 正文 / Review / Issue 回复等对外协作场景）。
- **界面审美**：现代 / 简洁 / 高级的专业产品感，不要后台模板味；动效克制（只动 opacity / transform，统一时长与缓动，尊重 prefers-reduced-motion，手机端简化）；首页要有第一屏冲击力。新页面 / 新组件先复用现有 token 与组件，颜色不要散落在页面里。
- **对「界面显示与实际执行不一致」零容忍**：做过的操作必须在界面上留得下证据（影响执行的 UI 选择一律落盘 / 注册表，不能只存 session_state / 内存态）。
- **重视「先理解全流程再动手」**：网关链路边界多（账号 → 指纹 → 出口 → 上游 → 协议转换 → 看板），改任何一环前先追完整条链路的所有调用方。
- **项目处于低频维护期**（2026-10-23 起）：改动要更保守，优先修复性、低风险变更，不主动发起大型重构。
- **上游持续收紧非官方客户端识别**：涉及 WAF/指纹/风控规避的改动，先确认不会放大账号风险，并在 PR 说明里写清影响面。
