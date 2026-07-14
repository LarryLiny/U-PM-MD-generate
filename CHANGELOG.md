# CHANGELOG — demotomd skill

> demotomd skill 的演进记录。版本号按**交付节点递增主版本号**编排，日期用北京时间（CST，UTC+8）。每条变更可追溯：标注来源 commit hash，或注明"基于本地与远程版本差异考据"。

## 版本号说明

本 CHANGELOG 按交付节点递增主版本号编排：

- `v1.0.0`（2026-04-21）— 首版主体
- `v2.0.0`（2026-04-22）— 目标设备检测
- `v3.0.0`（2026-04-27）— 大改版：版本化交付目录 + 服务端文档 + demo 定位重构
- `v4.0.0`（2026-07-14）— 补齐测试评分视角的不足：断言化 + 可测性 + 已知 Bug + 并发竞态 + 特殊字符 + 接口错误场景（**当前最新**）

各版本的 `metadata.version` 已与本日志同步。后续新需求将迭代至 `v5.0.0`。

---

## 待修复（已知问题）

以下问题在历次改版中均未处理：

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 1 | **Hook 脚本检测范围过窄** | `scripts/check-sync-needed.sh` | 只查找 `*_requirement.md` / `requirement.md`，不覆盖 UI / 测试 / 服务端文档，也不识别 v3.0.0 新增的 `PM_Requirement/Requirement_[版本号]/` 目录结构，新版 skill 下基本失效 |
| 2 | **Requirement_log 字段双处一致性** | `SKILL.md` vs `requirement-template.md` | v3.0.0 重做了 log 表格字段，需确认 SKILL.md 正文与 template 两处描述一致 |

> v4.0.0 已修复：命令名 `/sync-requirement` → `/demotomd`、SKILL.md 正文 @meta 示例补全为与 template 一致的 10 字段。

---

## [v4.0.0] — 2026-07-14（补齐测试评分视角的不足，当前最新）

> **来源**：基于测试团队 `qa-requirements-analyzer` skill 的 12 项 PRD 质量自检 + 强制试金石对比，补齐 demotomd 产出的 requirement / test_requirement 在「测试可执行性」硬标准上的系统遗漏。

### Added（新增能力）

**测试文档 `_test_requirement.md`（7 章 → 10 章）**：
- **AC 表强化**：新增「断言化」「可测性」「文案溯源」字段；前置条件升级为可引用代号链（P-01/P-02）；新增 AC 质量四项强制要求（断言化禁模糊词、可测性三问、前置条件链、精确文案可溯源）
- **新增第 8 章「已知 Bug 与缺陷标记」**：demo 反向工程发现的 bug / 写死 / TODO，测试时标 xfail
- **第 5 章极限场景新增 E 类「并发与竞态」**：两人同时编辑、库存并发扣减、重复提交幂等、并发状态变更（4 类 → 5 类）
- **新增第 9 章「特殊字符 / 多语言 / Emoji 行为」**：国际化与字符兼容性
- **新增第 10 章「接口错误场景测试（业务级）」**：参数错误 / 无权限 / 不存在 / 冲突 / 超时 / 外部依赖失败的用户可见行为
- **第 6 章数据边界强化**：异常值必含维度（特殊字符 / Emoji / 超长 / SQL 注入 / 不可见字符）

**研发文档 `_requirement.md`**：
- **第 5.3 节扩展**：新增接口能力清单（业务级）、错误场景与错误码（业务级枚举）、性能要求（业务级，标注需产品补充）
- **第 1.3 节扩展**：新增多端行为一致性要求表
- **第 3.N.7 验收标准升级为 Definition of Done**：从"模糊验收条件"改为"能力点 + 完成判据（可观测达成标志）+ 优先级"，借鉴断言化但用研发视角，让研发 Agent 明确"做到什么程度算完成"
- **流程图 / 状态机改用 mermaid**：3.N.2 操作流程用 `flowchart`、3.N.3 状态机用 `stateDiagram-v2`（原 ASCII 图），可被 GitHub / 飞书 / Markdown 编辑器直接渲染；同步更新 SKILL.md 输出原则 4/5、demo-analysis-guide 3.3 的图格式指示

**分析指南 `demo-analysis-guide.md`**：
- 新增 2.8「交互元素逐个机械化扫描（不漏控件）」
- 新增 5.3「断言化与可测性检查（每条 AC 必过）」
- 新增 8.5「已知 Bug 与代码缺陷识别」
- 第 4 章新增 4.5「并发与竞态」

**`SKILL.md`**：
- Phase B Round 3 加交互元素扫描 + 已知 Bug 识别
- Phase B Round 4 极限场景 4 类 → 5 类（加并发竞态）
- Phase B Round 5 加断言化检查 / 可测性三问 / 精确文案溯源
- Phase C 测试文档生成节 7 章 → 10 章，关键原则强化断言化
- 输出原则 12 → 17 条（新增断言化 / 文案溯源 / 已知 Bug / 可测性 / 前置条件链）
- Red Flags 新增 4 条反模式（模糊词 / 虚构文案 / 漏 bug / 不可测内部态）

### Fixed（修复）

- 命令名 `/sync-requirement` → `/demotomd`（SKILL.md 使用方法，历史 bug）
- SKILL.md 正文 @meta 示例补全 `analyzed-files` / `target-device`，与 template 对齐

### Breaking Changes（破坏性变更）

- 测试文档从 7 章扩展到 10 章（新增已知 Bug、特殊字符、接口错误场景）
- AC 表格新增「断言化」「可测性」「文案溯源」字段，旧 AC 表结构需扩展
- 极限场景从 4 类扩到 5 类（新增并发与竞态 E 类）
- 输出原则从 12 条扩到 17 条

### Notes

- 不改 UI 文档（`_ui_requirement.md`）：QA 把纯视觉归 N/A，且用户未要求
- 不改 `product-workflow.md`：无相关改动
- demotomd 已优于 QA 的维度（数据埋点、UI 交互 7 态矩阵、demo 边界标注）保持不动
- B 类定位冲突处理：接口契约/错误码 → 研发 5.3 业务级 + 服务端文档技术级；性能 → 业务级标注需补充；16 类元素 → 不照搬组织方式，借鉴扫描思路

---

## [v3.0.0] — 2026-04-27（重大改版，破坏性变更，未入版本控制）

> **来源**：本次改版**没有 git commit**，发生在 skill 安装目录（`~/.claude/skills/demotomd/` 等）的持续维护中。确切改版时间不可考，本日志按其被快照进 PM2RDMD 工程的时间（2026-04-27，本地 commit `427d4d9`）标注，实际改版发生在 2026-04-22 之后。
>
> **考据方式**：本地文件与远程 v2.0.0（`7bc3012`）逐文件 diff。差异量：`SKILL.md` 332 行、`requirement-template.md` 257 行、`demo-analysis-guide.md` 78 行、`product-workflow.md` 92 行。
>
> **为什么是定版**：本版引入版本化交付目录，按版本号 + 日期区分多版本产出，解决了"多个版本文件名相同造成混淆"的问题，是成熟定型版本。

### Breaking Changes（破坏性变更）

- **文档输出位置迁移**：从"项目根目录单文件"改为 `PM_Requirement/Requirement_[版本号]/` 目录。旧的单文件产物（如 `[项目名]_requirement.md`）不再直接产生
- **文件名规则变更**：从 `[项目名]_requirement.md` 改为 `[项目名]_requirement_[版本号].md` 并放入版本目录，多版本不再同名混淆
- **增量机制变更**：从"Edit 工具原地改现有文件"改为"每次新建版本目录写入增量文档"，旧的"原地编辑 + `[Updated 日期]` 标记"工作流不再适用
- **全量/增量判断条件变更**：旧（文件 < 20 行 / @meta 超 7 天）→ 新（是否存在上一版交付目录 / 用户是否要求全量）

### Added（新增能力）

- **版本化交付目录体系**
  - 版本号规则：`MMDD` + 3 位当日自增序号，如 `0622001`、`0622002`
  - 交付类型：`full` / `incremental`
  - 基线版本（`baseline-version`）概念
  - 新增 `version-manifest.md`：记录交付版本、输出目录、交付类型、基线版本、输出文件清单、变更摘要、与上一版本关系
- **服务端需求文档**（第四类可选文档）
  - `SERVER_CAPABILITY` 检测：扫描 Node/Express/Nest/Koa/Fastify、Next.js/Nuxt API、Python Flask/Django/FastAPI、Java Spring Boot、Go/Rust/PHP/.NET，及 Prisma/TypeORM/Sequelize/Drizzle、Django/SQLAlchemy models、migration、SQL/DDL、`DATABASE_URL`
  - 区分 `demo-mock-only`（纯 mock）与 `detected`（真实服务端/数据库）
  - 检测到后必须询问用户：线上正式项目是否同技术栈、是否需要输出 `_server_requirement.md`
  - 新增 `UPDATE_SERVER` 标志
  - 新增服务端分析 Round：技术栈 / API 能力 / 数据模型 / 业务规则 / 数据库改造 / 异常处理 / 外部依赖集成
  - `requirement-template.md` 新增整套 `_server_requirement.md` 模板（7 章）
  - `product-workflow.md` 流程图新增"可选服务端文档"分支，指向后端研发 / 后端 Agent
- **demo 定位重构**：明确"demo 是产品经理的本地演示项目，不是可部署的生产工程"，可含写死数据、前端模拟、伪接口、简化权限、内存状态
- **"关键背景与分析原则"整章**（`SKILL.md`）：6 条原则
  - demo 是本地演示，不是生产工程
  - 前端交互参考价值高，尽量完整提取
  - 后端只能作业务意图线索，不可照搬
  - 必须区分"当前 demo 表现"与"正式实现要求"
  - 三类文档服务不同角色
  - 线上项目/真实后端改造要单独确认
- **`demo-analysis-guide.md` 新增第 0 章"分析前提"** + 8.3"后端演示逻辑识别"，给出"demo 中看到的内容 → 文档中应表达为"的转换表
- **`product-workflow.md` 新增"背景定位"章**：demo 与正式研发项目在后端/AI/权限上的差异对照表
- **`requirement-template.md` 新增结构**：
  - "版本说明"表（交付版本 / 类型 / 基线 / 增量规则）
  - "Demo 与正式项目边界"表（前端 / 后端 / AI 能力 / 权限）
  - 第 5.3 节"后端与服务能力正式实现要求"（登录 / 权限 / 数据查询 / AI 生成 / 文件处理，各列 demo 表现 vs 正式要求 vs 待确认）
- **`@meta` 块字段补全**：`requirement-template.md` 三处 @meta 扩展为 **10 字段**——新增 `delivery-root` / `delivery-folder` / `delivery-type` / `baseline-version`，并保留 `analyzed-files` / `target-device`（服务端模板因不涉及设备，无 `target-device`）
- **Red Flags / 输出原则新增条目**：后端不照搬 demo / 版本目录交付（不输出在根目录）/ 后续默认增量 / 忽略 mock 与硬编码需标注

### Changed（变更）

- **增量文档新要求**：必须引用基线版本、说明"未提及内容默认沿用基线"、对废弃旧规则要标注"替换基线版本中的哪个条目"
- **`Requirement_log.md` 字段重做**：旧（序号 / 时间 / Git Commit / 更新模式 / 修改章节 / 修改内容 / requirement.md 版本）→ 新（序号 / 时间 / 交付版本 / 输出目录 / 基线版本 / 交付类型 / Git Commit / 输出文件 / 修改内容）
- **`description`、使用场景、各文档开头说明全部重写**：核心读者从"研发 AI 工具"扩展到研发 / UI / 测试三角色
- **数据请求分析改写**：从"提取请求"改为"判断是否只是 demo 演示用伪接口、前端服务函数或写死返回"，只把背后的产品意图写入文档

### Notes

- 本次改版**从未进入版本控制**，无 commit 记录，是 skill 安装目录内的"野生改版"
- 继承 v2.0.0 的目标设备检测能力
- 改版未修复 v2.0.0 遗留的 `/sync-requirement` 命令名错误
- **v3.0.0 定版时同步将 skill 的 `metadata.version` 从 `2.0.0` 更新为 `3.0.0`**，与本日志版本号一致

---

## [v2.0.0] — 2026-04-22（远程 commit `7bc3012`）

> 来源：GitHub `LarryLiny/U-PM-MD-generate`。改动量：`SKILL.md` +39/-1、`requirement-template.md` +21。

### Added

- **目标设备自动检测**（`SKILL.md` Phase A Step 1）：从 viewport meta、CSS 媒体查询断点、移动端 UI 库（vant / ant-design-mobile）、混合 App 框架（Capacitor / Cordova）、小程序框架（uni-app / taro）综合判断
- 设备类型枚举：`pc | mobile | responsive | hybrid-app | mini-program`
- 3 份文档模板的 `@meta` 块统一新增 `target-device` 字段
- 研发文档模板第 1 章新增 1.3"目标设备"子章节 + 设备类型对照表
- `SKILL.md` Phase C：研发文档第 1 章"产品概述"纳入"目标设备"

---

## [v1.0.0] — 2026-04-21（远程 commit `56cdb10` + `7bb113b`，首版主体）

> 来源：GitHub。一次性提交完整 skill 体系，7 个文件共约 2200 行。`56cdb10` 为功能主体，`7bb113b` 为 merge 补 README。

### Added

- `SKILL.md`（491 行）— 核心 4 阶段工作流（Phase A 检测 → B 分析 → C 生成 → D 校验）
- `references/requirement-template.md`（868 行）— 研发文档 7 章 / UI 文档 5 章 / 测试文档 7 章三套模板 + Requirement_log 机制
- `references/demo-analysis-guide.md`（409 行）— 多框架代码分析方法论
- `product-workflow.md`（294 行）— 产品经理视角的完整工作流（含 mermaid 流程图）
- `project-instructions/CLAUDE.md`（33 行）— Claude 项目级自动同步指令
- `project-instructions/kiro-steering.md`（37 行）— Kiro steering 指令
- `scripts/check-sync-needed.sh`（74 行）— Stop hook 脚本
- `README.md`（2 行）— 仓库说明（`7bb113b`）
- **核心能力**（commit body 自述）：
  - 三份需求文档生成（研发 / UI / 测试）
  - 三维变更检测（源码变更 + 对话语图分析 + 一致性兜底）
  - 增量更新（Edit 不重写全文）
  - 4 项一致性校验
  - 多框架支持（React / Vue / Angular / Svelte / 原生 HTML 等）

---

## 仓库初始化 — 2026-04-21（远程 commit `031331d`）

- 空仓库初始化，无实质内容

---

## 演进总览

| 版本 | 日期 | 性质 | 来源 | skill 的 metadata.version |
|------|------|------|------|--------------------------|
| 初始化 | 2026-04-21 | 空仓库 | `031331d` | — |
| v1.0.0 | 2026-04-21 | 首版主体（一次性全量） | `56cdb10` + `7bb113b` | `2.0.0`（失真） |
| v2.0.0 | 2026-04-22 | 目标设备检测 | `7bc3012` | `2.0.0`（失真） |
| v3.0.0 | 2026-04-27 | 大改版（破坏性）：交付目录化 + 服务端文档 + demo 定位重构 | 未入版本控制（diff 考据） | `3.0.0` |
| v4.0.0 | 2026-07-14 | 补齐测试评分视角：断言化 + 可测性 + 已知 Bug + 并发 + 特殊字符 + 接口错误场景（**当前最新**） | 本次会话 | `4.0.0` |

> **一句话**：demotomd 真实演进为「4/21 首版（v1.0.0）→ 4/22 设备检测（v2.0.0）→ 4/27 大改版（v3.0.0）→ 7/14 补齐测试可执行性（v4.0.0）」。v4.0.0 使产出的 requirement / test_requirement 能通过 qa-requirements-analyzer 的 12 项质量自检。
