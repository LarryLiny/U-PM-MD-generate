---
name: demotomd
description: |
  从产品经理本地演示 demo 代码反向生成/同步研发、UI、测试三类 MD 文档，替代传统 PRD/交互标注/测试需求作为跨团队交付物。不限定技术框架，支持 React/Vue/Angular/Svelte/原生HTML 等任何前端 demo。
  Trigger when: sync requirement, update requirement.md, extract requirements from code, demo to requirement, sync spec, update spec, generate requirement from demo, code to spec, reverse-engineer demo.
  触发词: 同步需求, 更新需求文档, 从代码提取需求, 演示转需求, 同步规格, 更新规格, 代码转规格, 需求同步, 同步requirement, 生成需求文档, 需求文档同步, demo转需求.
  Use this skill whenever the user has been iterating on a demo and wants the requirement.md to reflect all changes made during conversations. Also use when the user asks to prepare the requirement document for developer handoff, or when the user mentions they've finished tweaking a demo and need the spec updated.
user-invocable: true
argument-hint: "[project-path]"
metadata:
  author: user
  version: "4.0.0"
---

# DemoToMD

从产品经理本地演示 demo 代码中反向提取产品逻辑、交互状态、规则、边界条件，生成/更新三类 MD 文档，作为产品经理交付给研发、UI、测试的权威说明。不限定技术框架。

---

## 使用场景

产品经理使用 AI 编程工具（Kiro、Claude Code 等）构建可交互 demo。这个 demo 主要用于本地给业务方演示、确认需求，不是线上可直接部署的工程。在 spec 模式下先写 requirement.md，然后通过多轮自然语言对话迭代 demo。每次迭代后，运行本 skill 将 demo 中实际实现的产品逻辑、交互状态和测试重点同步回三类交付文档。

业务确认 demo 后，产品经理通常会把需求交给研发、UI、测试继续生产化。因此本 skill 的核心产出是：

1. **研发需求文档** `PM_Requirement/Requirement_[版本号]/[项目名]_requirement_[版本号].md` — 给研发、测试、UI 都能看，但主要面向研发 Agent，类似 PRD，写清楚业务规则、状态流转、数据要求、验收标准
2. **UI 需求文档** `PM_Requirement/Requirement_[版本号]/[项目名]_ui_requirement_[版本号].md` — 给 UI 设计师，记录 demo 前端如何实现、有哪些页面、交互状态、弹窗、反馈、空状态、视觉元素缺口，便于用 Figma 生成接近 demo 的界面后再优化
3. **测试需求文档** `PM_Requirement/Requirement_[版本号]/[项目名]_test_requirement_[版本号].md` — 给测试同学和测试 Agent，生成测试用例、覆盖极限情况、业务闭环、主流程优先级和可降级测试点

研发同学拿到两样东西：
1. **可交互的 demo** — 操作体验理解需求
2. **三类 MD 文档** — 直接喂给自己的 AI 编程工具，按产品意图开发

研发需求文档的核心读者是**研发的 AI 编程工具**。文档聚焦产品逻辑、业务规则、状态流转、极限场景，不涉及具体技术实现方案和 UI 视觉规格。UI 视觉规格由 UI 需求文档承接，测试验证范围由测试需求文档承接。

---

## 关键背景与分析原则

### 1. Demo 是本地演示项目，不是生产工程

产品经理写 demo 的目的，是尽快让业务方看到可操作界面并确认业务闭环。它可以包含写死数据、前端模拟、伪接口、简化权限、内存状态和临时后端逻辑。不要把 demo 当成可以直接上线的工程。

### 2. 前端交互通常有较高参考价值

demo 中已经做出来的页面结构、操作路径、交互状态、弹窗反馈、空状态、字段展示、流程先后顺序，通常代表 PM 和业务已经确认过的体验方向。生成文档时要尽量完整提取，供研发和 UI 复刻或优化。

### 3. 后端代码只能作为业务意图线索

demo 中的后端逻辑、接口、数据存储、鉴权、算法、大模型调用、定时任务等，经常只是为了演示而写死或简化，不能作为研发实现参考。分析时只提取其中表达的**业务规则和产品意图**，不要要求研发照搬 demo 后端实现。

### 4. 必须区分“当前 demo 表现”和“正式实现要求”

所有文档都要明确标注：
- 当前 demo 如何表现
- 哪些是 mock、硬编码、简化逻辑
- 正式项目需要对接接口、大模型、知识库、权限系统、数据服务或研发后端能力
- 哪些逻辑已经由业务确认，哪些还需要 PM/业务补充

### 5. 三类文档要服务不同角色

- 研发文档回答“要做什么业务能力，以及正式实现需要满足什么规则”
- UI 文档回答“当前 demo 长什么样、怎么交互、有哪些状态需要设计”
- 测试文档回答“怎么验证主流程、边界场景、角色权限和异常处理”

### 6. 线上项目/真实后端改造要单独确认

有些项目不是纯本地演示 demo，而是产品经理拿到线上项目代码后，已经做了服务端和数据库改造。这类项目可以额外输出服务端需求文档，但必须先询问用户：

- 当前检测到的服务端技术栈和数据库是什么
- 线上正式项目是否也是同一套技术栈
- 是否需要按当前服务端/数据库实现输出服务端需求文档

只有用户确认“线上项目技术栈相同，并且需要输出服务端需求”时，才生成 `PM_Requirement/Requirement_[版本号]/[项目名]_server_requirement_[版本号].md`。如果用户不需要，则不要展开服务端实现需求，只在研发文档中保留必要的业务能力和正式实现提示。

---

## Workflow

### Phase A: Detect & Prepare

**Step 1 — 定位项目根目录与确定文件名**

```
IF 用户提供了路径参数:
    PROJECT_ROOT = 参数路径
ELSE:
    PROJECT_ROOT = 当前工作目录
```

验证项目类型：检查 `package.json` 中的依赖（react/vue/angular/svelte 等），或检查是否存在 `*.html` + `*.js`（原生项目），或其他可识别的项目结构。

若未检测到可分析的项目，告知用户并提供帮助。

**确定目标设备类型**：

```
从以下维度综合判断项目的目标设备:

1. 源码线索:
   - 检查 viewport meta: <meta name="viewport" content="width=device-width">
   - 检查 CSS 媒体查询: @media (max-width: 768px) 等
   - 检查响应式框架: Tailwind 断点(sm/md/lg)、Bootstrap 栅格
   - 检查移动端专用库: vant、ant-design-mobile、Framework7
   - 检查路由: 是否有 /m/、/mobile/、/h5/ 等移动端路径
   - 检查 touch 事件: onTouchStart、touchstart 等移动端交互

2. 目录结构线索:
   - 存在 app/ 目录 + Capacitor/Cordova → 混合 App
   - 存在 public/manifest.json → PWA
   - 存在 pages.json (uni-app) → 跨平台小程序/App

3. 判断规则:
   IF 存在移动端UI库 OR CSS以移动端优先 OR viewport以移动端适配:
       DEVICE = "mobile"
   ELIF 存在 @media 移动端适配 AND 桌面端布局:
       DEVICE = "responsive" (PC + 移动端自适应)
   ELIF 存在混合App框架:
       DEVICE = "hybrid-app"
   ELIF 存在小程序框架(uni-app/taro):
       DEVICE = "mini-program"
   ELSE:
       DEVICE = "pc"

4. 确认:
   将判断结果告知用户: "检测到目标设备为 [PC / 移动端 / PC+移动端自适应 / 混合App / 小程序]"
   若用户纠正则以用户为准。
```

DEVICE 信息写入所有文档的 @meta 块: `target-device: pc | mobile | responsive | hybrid-app | mini-program`
同时在研发文档第 1 章"产品概述"中增加"目标设备"子章节，在 UI 文档中影响响应式适配需求的描述。

**检测服务端与数据库能力，并确认是否输出服务端文档**：

```
扫描项目是否存在真实服务端/数据库能力:

1. 服务端技术栈线索:
   - Node.js/Express/Nest/Koa/Fastify: server.ts, app.ts, routes/, controllers/, prisma/
   - Next.js/Nuxt 等全栈框架: app/api, pages/api, server/, nitro
   - Python Flask/Django/FastAPI: app.py, manage.py, main.py, routers/, requirements.txt
   - Java Spring Boot: pom.xml/build.gradle, controller/service/repository/entity
   - Go/Rust/PHP/.NET 等服务端目录和依赖

2. 数据库线索:
   - ORM/schema: prisma/schema.prisma, TypeORM/Sequelize/Drizzle, Django models, SQLAlchemy models
   - migration: migrations/, alembic/, liquibase/, flyway/
   - SQL/DDL: *.sql, schema.sql
   - 配置: DATABASE_URL, db config, docker-compose 中的 mysql/postgres/redis/mongo

3. 判断规则:
   IF 只存在 mock、fixtures、本地 JSON、localStorage:
       SERVER_CAPABILITY = "demo-mock-only"
       不询问服务端文档，按 demo 规则处理
   ELIF 存在服务端路由/控制器/模型/数据库迁移/ORM schema:
       SERVER_CAPABILITY = "detected"
       总结检测结果并询问用户:
       "检测到当前项目包含服务端和数据库能力：[技术栈] + [数据库/ORM]。
        这个项目是否来自线上项目，且正式研发也会使用相同技术栈？
        是否需要额外输出服务端需求文档 `PM_Requirement/Requirement_[版本号]/[项目名]_server_requirement_[版本号].md`？"

4. 用户选择:
   IF 用户确认技术栈相同且需要输出:
       UPDATE_SERVER = true
       SERVER_MODE = "production-stack"
   ELSE:
       UPDATE_SERVER = false
       SERVER_MODE = "skip-server-detail"
       不输出服务端需求文档；研发文档只保留业务规则、接口能力和正式实现要求
```

服务端文档是可选产物，不影响默认的研发、UI、测试三份核心文档。

**确定交付版本号、输出目录与文件名**：

```
项目名 = package.json 的 name 字段，或目录名
项目名转为 PascalCase（如 order-management → OrderManagement）

版本号规则:
  DATE_CODE = 当前日期 MMDD，例如 6月22日 → 0622
  REQUIREMENT_ROOT = "PM_Requirement"
  扫描 PM_Requirement/ 下已有 Requirement_[0-9]{7} 文件夹
  找到当天 DATE_CODE 开头的最大序号
  IF 今天没有任何交付目录:
      DELIVERY_VERSION = DATE_CODE + "001"
  ELSE:
      DELIVERY_VERSION = DATE_CODE + (最大序号 + 1，补足3位)

输出目录:
  OUTPUT_ROOT = "PM_Requirement"
  OUTPUT_DIR = "PM_Requirement/Requirement_" + DELIVERY_VERSION
  示例: PM_Requirement/Requirement_0622001, PM_Requirement/Requirement_0622002

输出文件:
  REQUIREMENT_FILE = "PM_Requirement/Requirement_[版本号]/[项目名]_requirement_[版本号].md"
  UI_REQUIREMENT_FILE = "PM_Requirement/Requirement_[版本号]/[项目名]_ui_requirement_[版本号].md"
  TEST_REQUIREMENT_FILE = "PM_Requirement/Requirement_[版本号]/[项目名]_test_requirement_[版本号].md"
  SERVER_REQUIREMENT_FILE = "PM_Requirement/Requirement_[版本号]/[项目名]_server_requirement_[版本号].md" ← 可选，仅 UPDATE_SERVER = true 时生成
  VERSION_MANIFEST = "PM_Requirement/Requirement_[版本号]/version-manifest.md"
  LOG_FILE = "PM_Requirement/[项目名]_Requirement_log.md" ← PM_Requirement 下的总变更日志，每次同步追加
```

**确定基线版本与交付类型**：

```
BASELINE_DIR = PM_Requirement/ 下最新的 Requirement_[0-9]{7} 文件夹

IF BASELINE_DIR 不存在:
    DELIVERY_TYPE = "full"
    BASELINE_VERSION = "none"
    输出完整三类核心文档（以及可选服务端文档）
ELSE:
    DELIVERY_TYPE = "incremental"
    BASELINE_VERSION = BASELINE_DIR 去掉 "Requirement_" 后的版本号
    本次文档只写相对 BASELINE_VERSION 的新增、变更、废弃、待确认内容

用户明确要求“全量重新交付”时:
    DELIVERY_TYPE = "full"
    BASELINE_VERSION = 最新版本号（用于说明本次是重新全量交付）
```

**Step 2 — 读取 `references/requirement-template.md`**

获取 requirement.md 的完整模板结构。这一步是必须的，不要跳过。

**Step 3 — 判断更新模式与更新范围**

**3a. 判断更新模式**（对每个交付目录独立判断）：

```
IF BASELINE_DIR 不存在:
    MODE = "full-rewrite"

ELSE IF 用户明确要求全量重新交付:
    MODE = "full-refresh"

ELSE:
    MODE = "incremental"
    以 PM_Requirement/ 下上一个 Requirement_[版本号] 目录作为基线
    识别基线版本后被修改的源文件、对话意图和文档缺口
```

**3b. 检测变更来源**（三种来源，按优先级叠加）：

```
来源 1 — 源码文件变更:
  比较源文件 hash 与 @meta.source-hash，列出变更文件列表。
  若源文件有改动 → CODE_CHANGED = true

来源 2 — 对话上下文意图:
  分析当前对话中用户的 prompt，判断用户让 AI 做了什么。
  即使源码没有改动，用户的 prompt 也可能描述了后端逻辑调整。
  判断维度:
  - 用户 prompt 是否涉及业务规则/计算逻辑/权限/状态流转 → LOGIC_INTENT = true
  - 用户 prompt 是否涉及交互/视觉/icon/布局调整 → UI_INTENT = true
  - 用户 prompt 是否涉及测试用例/验收标准/边界值 → TEST_INTENT = true
  - 用户 prompt 是否只是调整文档措辞，不涉及功能 → DOC_ONLY = true

来源 3 — 文档与源码一致性校验:
  快速扫描: 如果 UPDATE_xxx 标记为 false，但对应文档中缺少源码中已存在的逻辑，
  则强制修正为 UPDATE_xxx = true。
  这是一致性兜底，防止 demo 中有但文档中丢失。
```

**3c. 综合判断更新范围**：

```
初始化: UPDATE_DEV = false, UPDATE_UI = false, UPDATE_TEST = false, UPDATE_SERVER = false

根据变更来源叠加更新标记:

纯业务逻辑变更（源码或对话上下文）:
  - 触发条件: CODE_CHANGED(业务文件) OR LOGIC_INTENT
  - 例如: 修改价格计算、审批流程、表单验证、新增角色权限
  - 例如: 用户 prompt 说"加一个满减规则"但 demo 可能只改了显示，计算逻辑在后端
  → UPDATE_DEV = true, UPDATE_UI = false, UPDATE_TEST = true

纯交互/视觉变更:
  - 触发条件: CODE_CHANGED(交互/视觉文件) OR UI_INTENT
  - 例如: 新增确认弹窗、换了 icon 库、加了骨架屏
  → UPDATE_DEV = false, UPDATE_UI = true, UPDATE_TEST = false

新增功能/页面:
  - 触发条件: 新增页面/路由/组件
  → UPDATE_DEV = true, UPDATE_UI = true, UPDATE_TEST = true

修改极限场景处理:
  - 触发条件: 新增 loading/空状态/错误处理
  → UPDATE_DEV = true, UPDATE_UI = false, UPDATE_TEST = true

首次生成:
  → UPDATE_DEV = true, UPDATE_UI = true, UPDATE_TEST = true

服务端/数据库变更:
  - 触发条件: SERVER_CAPABILITY = detected AND 用户确认需要按相同技术栈输出服务端需求
  - 例如: 新增数据库表、修改字段、改造鉴权、增加真实 API、调整 ORM schema、改造服务端任务
  → UPDATE_SERVER = true
  → 同时根据业务影响判断 UPDATE_DEV / UPDATE_TEST 是否需要更新

纯文档调整（DOC_ONLY）:
  - 触发条件: 用户只要求调整文档措辞/格式，无功能变更
  - 仅更新用户指定的文档，不触发代码分析

兜底一致性修正:
  IF UPDATE_TEST = false AND UPDATE_DEV = true:
      检查测试文档是否覆盖了当前所有业务逻辑
      若有遗漏 → UPDATE_TEST = true
  IF UPDATE_UI = false AND (UPDATE_DEV = true OR UPDATE_TEST = true):
      检查 UI 文档是否覆盖了当前所有交互状态
      若有遗漏 → UPDATE_UI = true
```

告知用户："将更新 [研发需求 / UI需求 / 测试需求] 文档"，并说明触发原因（源码变更 / 对话意图 / 一致性修正）。

**Step 4 — 利用对话上下文**

如果当前对话中有关于 demo 修改的上下文（用户刚做了什么改动），优先利用这些信息来确定分析范围和变更内容。这比纯文件分析更准确。

**重点**: 即使用户的 prompt 描述的是后端逻辑（不体现在前端 demo 上），需求文档和测试文档也必须更新。例如:
- 用户说"加一个满200减20的促销规则"，demo 可能只显示结果，但计算逻辑、边界值、测试 AC 都需要更新
- 用户说"管理员可以删除任何人的订单"，demo 可能没改页面，但权限矩阵、测试用例需要更新
- 用户说"接口超时要弹提示"，demo 可能没加，但极限场景、测试清单需要补充

---

### Phase B: Analyze Demo Code

读取 `references/demo-analysis-guide.md` 获取详细的分析方法论，然后按以下顺序执行：

**Round 1 — 配置文件（并行读取）**

```
并行读取:
- package.json → 项目名（不需要提取技术栈，研发有自己的技术选型）
- 路由配置文件 → 页面结构
```

**Round 2 — 页面结构发现**

```
根据项目类型找到页面/路由配置:
- React: createBrowserRouter, Routes, Route
- Vue: createRouter, router-view, routes
- Angular: RouterModule
- Next.js: app/ 或 pages/ 目录
- 原生 HTML: 多个 .html 文件
→ 提取完整的页面映射表
→ 识别每个页面对应的源文件
→ 提取页面间参数传递规则（URL参数、query参数、state传递）
```

**Round 3 — 源码分析（按优先级）**

```
优先级 1: 页面/视图文件
优先级 2: 布局文件
优先级 3: 共享组件
优先级 4: 业务逻辑（hooks/composables/services/utils）

对每个文件提取:
- 数据入口（props / attributes / properties）
- 内部状态（state / ref / reactive）
- 事件处理函数及其逻辑
- 条件渲染 → 业务规则
- 数据请求（fetch / axios / 等）
- 页面导航触发及参数传递
- 表单验证逻辑
- demo 后端、mock、硬编码、伪 AI 返回、固定权限等演示逻辑
- 交互元素逐个机械化扫描（Input/Select/Upload/Button/Table 等，不漏控件，详见 demo-analysis-guide 2.8）
- 已知 Bug 识别（TODO/FIXME/写死返回/明显逻辑错误，详见 demo-analysis-guide 8.5）

注意：如果项目中存在后端目录、API route、server 脚本或本地数据库文件，只把它们当作“业务意图线索”。不要把 demo 后端结构、接口路径、存储方式、鉴权方式写成正式研发实现方案。
如果 Phase A 中用户确认这是线上同技术栈项目，并要求输出服务端文档，则额外进入“服务端分析”：
- 服务端路由/Controller/API handler
- Service/use case/domain 层业务逻辑
- ORM schema/entity/model
- migration/DDL
- 鉴权、角色权限、数据范围控制
- 后台任务、定时任务、消息队列、文件处理、AI/知识库调用
```

**Round 4 — 业务规则与极限场景提取**

从代码中识别以下模式：
- `if/else` 渲染链 → 条件展示规则
- `useMemo` 复杂计算 → 业务计算规则
- 验证 schema (zod/yup) → 输入约束规则
- `disabled`, `hidden`, `readOnly` 条件 → 权限/状态规则
- `useReducer` / `switch-case` 状态流转 → **状态机**（用 mermaid `stateDiagram-v2` 描述状态及转换）
- 多步骤事件处理链 → **流程图**（用 mermaid `flowchart` 描述步骤和分支）
- Loading/Empty/Error 状态处理 → 异常场景
- 内容溢出、空数据、网络异常、操作异常、并发竞态 → **极限场景**（必须覆盖5类：内容溢出、空内容、网络异常、用户操作异常、并发与竞态）

**Round 5 — 验收标准、数据埋点与 UI 交互分析**

```
对每个功能:
- 从操作流程、交互规则、校验规则、极限场景中提炼验收标准
- 标注优先级: P0(核心路径) / P1(重要非阻塞) / P2(边界异常)
- **断言化检查**: 每条 AC 必须能写成 expect(可观测).toBe(具体值)，禁模糊词（正常/正确/符合预期等）
- **可测性三问**: 前置态可构造 / 断言可观测 / 清单有限集，不通过的标 🚫不可测+等待方
- **精确文案溯源**: AC 中精确文案必须溯源到 demo/PRD，禁虚构

从产品核心指标出发:
- 推断核心业务指标（转化率、留存率、操作效率等）
- 识别页面浏览埋点（每个路由页面）
- 识别用户行为埋点（关键交互事件）
- 识别业务事件埋点（状态流转终态、核心流程完成节点）

UI 交互分析（如果 UPDATE_UI = true）:
- 提取每个交互元素的所有状态（默认、hover、激活、loading、禁用、错误、空态）
- 识别 Modal/Dialog/Toast/Tooltip 等弹窗与浮层
- 识别 icon 使用情况（文字替代、emoji、icon 库）
- 识别空状态、占位图、默认图的缺失
- 标注交互问题（不一致的跳转、缺失的反馈、不合理的操作流）
- 识别响应式适配需求
```

**增量模式优化**: 如果是 incremental 模式，只分析变更文件及其直接依赖。

**服务端分析（仅 UPDATE_SERVER = true 时执行）**:

```
对服务端代码提取:
- 技术栈: 框架、ORM、数据库、中间件、任务调度、消息队列、文件服务、AI/知识库依赖
- API 能力: 业务能力名称、触发场景、输入输出业务字段、成功/失败结果、权限要求
- 数据模型: 表/实体、字段、关系、索引、唯一约束、软删除、审计字段
- 业务规则: 服务端计算、状态流转、权限判断、数据范围、幂等规则
- 数据库改造: 新增/修改表字段、迁移脚本、历史数据兼容、回滚风险
- 异常处理: 参数错误、无权限、数据不存在、并发冲突、超时、外部服务失败

注意:
- 服务端文档可以描述当前技术栈相关的实现约束，但仍要用产品和研发都能理解的语言。
- 不生成具体代码，不要求研发逐行照搬。
- 如果线上项目技术栈不同，或者用户不需要服务端文档，则跳过本轮服务端分析。
```

---

### Phase C: Generate / Update Documents

根据 Phase A 中判断的 UPDATE_DEV、UPDATE_UI、UPDATE_TEST、UPDATE_SERVER 标志，生成/更新对应文档。**同一次代码分析，输出不同侧重点的文档**。

#### 研发需求文档（`PM_Requirement/Requirement_[版本号]/[项目名]_requirement_[版本号].md`）— UPDATE_DEV = true 时执行

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中研发文档的结构，生成完整的文档。7 个章节：

1. **产品概述** — 产品描述 + 目标用户 + **目标设备**（PC/移动端/自适应/混合App/小程序）
2. **页面结构与导航** — 页面清单 + 导航关系 + **页面间参数传递**
3. **功能逻辑** — 每个功能：目的 + 操作流程（mermaid）+ 状态机（mermaid）+ 交互规则 + 校验规则 + 极限场景 + **验收标准（Definition of Done：能力点 + 完成判据）**
4. **业务规则** — 计算规则 + 条件逻辑 + 数据处理规则
5. **数据模型** — 核心实体 + Mock 数据说明 + **后端与服务能力正式实现要求**（接口能力清单 + 错误场景与错误码 + 性能要求，业务级）
6. **已知缺口** — 简化逻辑 + 缺失功能 + TODO
7. **数据埋点** — 核心指标 + 页面浏览 + 用户行为 + 业务事件

每个章节必须有实质内容，不得留空占位符。如果某项信息在代码中未检测到，标注 "代码中未检测到，需产品经理补充"。

研发文档必须明确区分：
- demo 中已确认的产品规则和交互流程
- demo 为演示而写死、mock 或简化的内容
- 正式项目需要研发重新实现的接口、权限、数据、AI、知识库、文件、审计等服务能力

**增量模式 (incremental)**

1. 读取上一版本目录中的 requirement.md 作为基线
2. 分析变更文件、对话意图和一致性缺口，确定本次影响哪些功能/章节
3. 在新的 `PM_Requirement/Requirement_[版本号]/` 目录中写入一份**增量研发需求文档**
4. 增量文档只包含：
   - 本次新增功能
   - 本次修改的业务规则、状态流转、校验、数据模型、埋点
   - 本次废弃/替换的旧规则
   - 对上一版本文档的引用和影响说明
5. 不重复写上一版本已交付且本次未变化的完整内容
6. 必须在文档开头写明：
   - 本次版本号
   - 基线版本号
   - 本文档为增量交付
   - 未提及内容默认沿用基线版本

#### UI 需求文档（`PM_Requirement/Requirement_[版本号]/[项目名]_ui_requirement_[版本号].md`）— UPDATE_UI = true 时执行

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中 UI 文档的结构，生成完整的文档。5 个章节：

1. **页面结构与导航** — 页面清单 + 导航关系 + 参数传递对 UI 的影响
2. **交互状态清单** — 每个功能的交互状态矩阵 + 弹窗浮层清单 + 反馈提示清单
3. **视觉元素需求清单** — Icon 需求 + 插图/空状态图 + 占位图/默认图
4. **交互问题标注** — 交互逻辑问题 + 缺失的交互反馈 + 响应式适配需求
5. **组件复用说明** — 重复 UI 模式 + 现有设计系统复用

**增量模式 (incremental)**

1. 读取上一版本目录中的 ui_requirement.md 作为基线
2. 分析本次变更对页面、交互状态、弹窗、反馈、视觉元素的影响
3. 在新的 `PM_Requirement/Requirement_[版本号]/` 目录中写入一份**增量 UI 需求文档**
4. 只描述本次新增/调整/废弃的 UI 内容
5. 未变化页面、未变化组件、未变化交互状态不重复展开，只写“沿用基线版本 [版本号]”

#### 测试需求文档（`PM_Requirement/Requirement_[版本号]/[项目名]_test_requirement_[版本号].md`）— UPDATE_TEST = true 时执行

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中测试文档的结构，生成完整的文档。10 个章节：

1. **测试范围与优先级** — 功能清单 + 优先级 + 变更 vs 未变更
2. **业务逻辑验收标准** — 每个功能的详细 AC（前置条件链代号、测试步骤、测试数据、预期结果、断言化、可测性、文案溯源）
3. **角色与权限测试矩阵** — 每个角色在每个功能点的权限状态
4. **状态流转测试** — 每个合法/非法状态转换的测试用例
5. **极限场景测试清单** — 5 类极限场景的具体测试步骤（内容溢出、空内容、网络异常、操作异常、并发与竞态）
6. **数据边界测试** — 每个字段的正常值/边界值/异常值（异常值含特殊字符/Emoji/超长/注入）
7. **回归测试建议** — 冒烟测试清单 + 关联功能回归
8. **已知 Bug 与缺陷标记** — demo 中发现的 bug/写死/TODO，测试时标 xfail
9. **特殊字符/多语言/Emoji 行为** — 国际化与字符兼容性测试
10. **接口错误场景测试（业务级）** — 参数错误/无权限/不存在/冲突/超时/外部依赖失败的用户可见行为

**关键原则**：每个 AC 都必须包含具体的测试步骤、测试数据和预期结果，且必须过断言化试金石（能写成 `expect().toBe(具体值)`，禁模糊词）与可测性三问，精确文案必须可溯源。测试老师的 Agent 能直接转化为测试用例。

**增量模式 (incremental)**

1. 读取上一版本目录中的 test_requirement.md 作为基线
2. 分析本次变更对验收标准、极限场景、权限矩阵、状态流转、数据边界、已知 Bug、特殊字符、接口错误场景的影响
3. 在新的 `PM_Requirement/Requirement_[版本号]/` 目录中写入一份**增量测试需求文档**
4. 只输出本次新增/变更/废弃测试点
5. 如果修改了旧规则，要明确标注“替换基线版本 [版本号] 中的哪个 AC/测试点”
6. 未受影响的测试范围不重复写，标注“沿用基线版本”

#### 服务端需求文档（`PM_Requirement/Requirement_[版本号]/[项目名]_server_requirement_[版本号].md`）— UPDATE_SERVER = true 时执行

服务端文档是可选文档。只有检测到真实服务端/数据库能力，且用户确认线上正式项目使用相同技术栈并需要输出时，才生成。

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中服务端文档的结构，生成完整文档。建议章节：

1. **服务端范围与技术栈确认** — 当前检测到的框架、ORM、数据库、运行方式，以及用户确认结果
2. **API/服务能力清单** — 按业务能力描述输入、输出、权限、成功/失败结果，不写具体 URL 约束
3. **数据模型与数据库改造** — 表/实体、字段、关系、索引、迁移、兼容和回滚风险
4. **服务端业务规则** — 计算规则、状态流转、权限、数据范围、幂等、并发处理
5. **外部依赖与集成能力** — 大模型、知识库、文件服务、消息队列、第三方系统
6. **异常与降级策略** — 参数错误、无权限、超时、外部服务失败、数据库异常
7. **研发交接注意事项** — 当前实现可参考点、不可照搬点、待确认问题

**增量模式 (incremental)**

1. 读取上一版本目录中的 server_requirement.md 作为基线（若存在）
2. 分析本次变更的服务端/数据库文件，确定影响能力、数据表、迁移、权限、异常和集成
3. 在新的 `PM_Requirement/Requirement_[版本号]/` 目录中写入一份**增量服务端需求文档**
4. 只输出本次新增/变更/废弃的服务端内容
5. 若本次用户明确取消服务端文档，则不输出该文件，并在 `version-manifest.md` 中记录跳过原因

**元数据块**

在文件开头更新 `@meta` 块：

```
<!--
@meta
version: [交付版本号，如 0622002]
delivery-root: PM_Requirement
delivery-folder: PM_Requirement/Requirement_[版本号]
delivery-type: full | incremental
baseline-version: [none 或上一交付版本号]
last-updated: [当前日期时间，格式 YYYY-MM-DD HH:mm:ss]
last-full-rewrite: [全量模式时更新为当前日期时间，增量模式保持不变]
update-mode: [当前模式]
source-hash: [所有源文件路径+大小的哈希]
analyzed-files: [分析的文件列表，逗号分隔]
target-device: pc | mobile | responsive | hybrid-app | mini-program
@/meta
-->
```

**同步生成 version-manifest.md 与 Requirement_log.md**

每次同步时，必须在本次输出目录中生成 `version-manifest.md`，同时更新 `PM_Requirement/` 下的总日志 `Requirement_log.md`：

```
version-manifest.md 内容:
  - 交付版本号: DELIVERY_VERSION
  - 输出目录: OUTPUT_DIR
  - 交付类型: full / incremental
  - 基线版本: BASELINE_VERSION
  - 本次输出文件清单
  - 本次变更摘要
  - 本次未输出/跳过的文档及原因
  - 与上一版本的关系: 新增 / 修改 / 废弃 / 沿用

1. 获取 git commit hash:
   - 运行 git rev-parse --short HEAD 获取短 hash
   - 运行 git status --porcelain 检查是否有未提交变更
   - 有未提交变更则 hash 后追加 " (dirty)"
   - 非 git 仓库则填 "N/A"

2. 更新 PM_Requirement 下的总日志:
   - 若 PM_Requirement/[项目名]_Requirement_log.md 不存在: 创建文件，写入表头 + 第一条记录
   - 若已存在: 用 Edit 工具在表格末尾追加一行新记录
   - 不要重写整个 log 文件

3. 日志格式:
   | 序号 | 时间 | 交付版本 | 输出目录 | 基线版本 | 交付类型 | Git Commit | 输出文件 | 修改内容 |
```

---

### Phase D: Validate & Confirm

**Step 1 — 一致性校验（写入前必检）**

在写入文件前，执行以下交叉校验，确保 demo 中的逻辑没有在文档中丢失：

```
校验 1 — Demo vs 研发文档:
  扫描源码中的关键逻辑点（状态变量、条件渲染、事件处理、校验规则），
  逐条确认是否在 requirement.md 中有对应描述。
  若发现遗漏 → 追加到"已知缺口"章节，并告知用户。

校验 2 — 研发文档 vs 测试文档:
  对比 requirement.md 中的每个功能逻辑（校验规则、极限场景、状态流转），
  确认 test_requirement.md 中有对应的 AC 覆盖。
  若发现遗漏 → 在测试文档对应章节补充 AC。

校验 3 — Demo vs UI 文档:
  扫描源码中的交互状态（disabled/loading/error/empty 条件渲染），
  确认 ui_requirement.md 的交互状态矩阵中有对应行。
  若发现遗漏 → 在 UI 文档对应章节补充。

校验 4 — 跨文档引用一致性:
  确认三个文档中的功能名称、状态名称、角色名称保持一致。
  例如: requirement.md 叫"审批中"，test_requirement.md 不能写成"审核中"。
```

**Step 2 — 生成摘要报告**

```
Requirement 同步摘要
├── 交付版本: PM_Requirement/Requirement_[版本号]
├── 基线版本: none / Requirement_[上一版本号]
├── 交付类型: full / incremental
├── 更新模式: full-rewrite / incremental / full-refresh
├── 更新范围: [研发文档] / [UI文档] / [测试文档] / [研发+UI+测试]
├── 研发文档: N 个页面, M 条业务规则, K 个状态机, F 个流程图
│   ├── 极限场景: 内容溢出[X项], 空内容[X项], 网络异常[X项], 操作异常[X项], 并发竞态[X项]
│   ├── 验收标准: 共 X 条 (P0: Y, P1: Z, P2: W)
│   └── 数据埋点: 核心指标[X个], 页面浏览[X项], 用户行为[X项], 业务事件[X项]
├── UI文档: N 个交互状态矩阵, M 个弹窗/浮层, K 个Icon需求, F 个交互问题
│   ├── 视觉元素需求: Icon[X个], 插图[X个], 占位图[X个]
│   └── 交互问题: 逻辑问题[X项], 缺失反馈[X项], 响应式[X项]
├── 测试文档: N 个验收标准(AC), M 个权限测试点, K 个状态转换测试, F 个极限场景
│   ├── 业务逻辑AC: 共 X 条
│   ├── 权限AC: 共 X 条
│   ├── 状态流转AC: 共 X 条 (合法 X, 非法 X)
│   └── 数据边界: X 个字段 × 3 类测试值
├── 变更章节: [列出受影响的章节]
├── 已知缺失: [列出无法从代码提取的信息]
├── 输出文件夹: PM_Requirement/Requirement_[版本号]/
├── 输出文件: [列出本次会写入的 md 文件]
└── 变更摘要: [一句话描述主要变化]
```

**Step 3 — 用户确认**

向用户展示摘要，询问是否确认写入。用户可以：
- 确认写入
- 要求修改特定部分
- 取消操作

**Step 4 — 写入文件**

确认后创建本次交付目录并写入文档：

```
mkdir -p PM_Requirement/Requirement_[版本号]

写入:
- `PM_Requirement/Requirement_[版本号]/[项目名]_requirement_[版本号].md` — 研发需求文档
- `PM_Requirement/Requirement_[版本号]/[项目名]_ui_requirement_[版本号].md` — UI 需求文档
- `PM_Requirement/Requirement_[版本号]/[项目名]_test_requirement_[版本号].md` — 测试需求文档
- `PM_Requirement/Requirement_[版本号]/[项目名]_server_requirement_[版本号].md` — 服务端需求文档（可选）
- `PM_Requirement/Requirement_[版本号]/version-manifest.md` — 本次交付说明与版本关系

追加更新:
- `PM_Requirement/[项目名]_Requirement_log.md` — 总变更日志
```

写入规则：
- 不覆盖历史 `PM_Requirement/Requirement_[版本号]` 文件夹
- 如果即将创建的版本目录已存在，重新计算下一个自增版本号
- 增量交付文档必须引用基线版本，并说明“未提及内容沿用基线版本”
- 不在项目根目录直接输出任何需求 MD，所有交付 MD 必须放入 `PM_Requirement/` 下

---

## Hook 自动提醒（可选配置）

如果用户希望每次结束 session 时自动提醒同步 requirement.md，可以将以下配置添加到 `~/.claude/settings.json`：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/skills/demotomd/scripts/check-sync-needed.sh"
          }
        ]
      }
    ]
  }
}
```

该脚本仅在检测到源码项目且源文件比 requirement.md 更新时，输出提醒信息。不会自动执行同步。

---

## Red Flags

| 错误做法 | 正确做法 |
|---------|---------|
| 跳过 Phase A 直接分析代码 | 先确认项目类型和更新模式 |
| 不读取 reference 文件直接生成 | 必须先读 requirement-template.md |
| requirement.md 留空占位符 | 所有章节填入实质内容，无法提取的标注"需补充" |
| 增量模式覆盖历史文档 | 每次创建新的 `PM_Requirement/Requirement_[版本号]` 文件夹，历史交付不覆盖 |
| 增量文档重复写全量内容 | 只写本次新增/变更/废弃内容，未变化内容引用基线版本 |
| 直接把 MD 输出在项目根目录 | 所有需求 MD 必须放入 `PM_Requirement/` 下 |
| 不经过用户确认直接写入 | Phase D 的确认步骤不可跳过 |
| 分析所有文件导致上下文溢出 | 按优先级分轮读取，增量模式只读变更文件 |
| 包含技术实现细节 | 不写技术栈、API接口契约、色值字号等，研发有自己的选型 |
| 把 demo 后端当成正式实现参考 | 后端代码只作为业务意图线索，正式实现要求写成服务能力和业务规则 |
| 忽略 mock/硬编码/写死返回 | 在研发文档标注正式实现要求，在测试文档补充接口异常和边界测试 |
| 过度描述 UI 视觉细节 | 不描述布局、组件树等，UI 设计师负责视觉规格 |
| 省略验收标准 | 每个功能必须有可验证的验收条件 |
| 只看源码变更不看对话上下文 | 用户 prompt 描述的后端逻辑即使没改 demo，也必须更新文档 |
| 文档间逻辑丢失 | Phase D 一致性校验不可跳过，确保 demo 逻辑在文档中不丢失 |
| 省略数据埋点 | 必须从核心指标梳理埋点事件 |
| AC 用模糊词（正常/正确/符合预期） | 预期结果必须能写成 expect(X).toBe(具体值)，模糊词视同未定义 |
| 虚构 demo 里没有的精确文案 | 精确文案必须溯源到 demo/PRD，未定义的写结构性断言 |
| 漏掉 demo 已知 bug | 扫描 TODO/FIXME/写死返回，记入测试文档第 8 章并标 xfail |
| AC 写成不可测的内部态 | 过可测性三问，不可观测的下沉接口层或标 🚫不可测 |

---

## 使用方法

### 方式一：手动触发
```
/demotomd
/demotomd /path/to/project
```

### 方式二：自然语言触发
```
"帮我同步一下需求文档"
"demo改完了，更新一下requirement"
"把代码里的产品逻辑写到requirement.md里"
```

### 方式三：Hook 自动提醒
配置后，每次 session 结束时自动检测并提醒。

---

## 输出原则

1. **不涉及技术实现细节** — 不写技术栈、API 接口契约、色值字号等，研发有自己的技术选型和 UI 设计规范
2. **不描述 UI 视觉细节** — 不写布局结构、组件树、CSS 类名等，UI 设计师负责视觉规格
3. **聚焦产品逻辑** — 写清楚每个功能"做什么"和"为什么"，不写"怎么实现"
4. **复杂逻辑必须有状态机** — 涉及多个状态流转（审批流、订单状态、工作流）时，用 mermaid `stateDiagram-v2` + 状态表格描述
5. **复杂流程必须有流程图** — 涉及多步骤操作或条件分支时，用 mermaid `flowchart` 描述完整路径
6. **极限场景必须覆盖** — 每个功能必须考虑 5 类极限场景：内容溢出、空内容/无数据、网络与接口异常、用户操作异常、并发与竞态。代码中未处理的要标注"需补充"
7. **验收标准必须可验证** — 每个功能必须有具体的、可测试的验收条件，覆盖正向路径、逆向路径、边界条件
8. **数据埋点从指标出发** — 从核心业务指标反推需要埋点的事件，不盲目罗列
9. **Demo 产物必须标注** — 明确告知哪些是 mock 数据、简化逻辑、缺失功能
10. **后端实现不照搬 demo** — demo 后端、接口、数据、AI 返回、权限控制只能说明业务意图；正式项目需要研发重新设计可上线的服务能力
11. **版本目录交付** — 每次输出必须创建 `PM_Requirement/Requirement_MMDDNNN` 文件夹，所有交付 MD 放入该文件夹
12. **后续版本默认增量** — 如果已有上一版交付，本次默认只输出相对上一版的增量需求，未提及内容沿用上一版
13. **AC 必须断言化** — 每条验收标准的预期结果必须能写成 `expect(可观测).toBe(具体值)`，禁止"正常/正确/符合预期"等模糊词，只有模糊词视同未定义
14. **精确文案可溯源** — AC 中的精确文案断言必须能在 demo 代码或 PRD 中找到对应字符串，禁止虚构；未定义的写结构性断言
15. **已知 Bug 必须标记** — demo 中发现的 bug、写死返回、TODO/FIXME 必须记录到测试文档第 8 章并标 xfail，不当回归失败
16. **可测性三问必须过** — 每条 AC 过前置态可构造 / 断言可观测 / 清单有限集三问，不通过的标 🚫不可测 + 等待方
17. **前置条件链可引用** — AC 的前置条件用代号（P-01/P-02）集中列出，测试 AI 可据此定位测试起点
