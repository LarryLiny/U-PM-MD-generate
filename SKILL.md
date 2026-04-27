---
name: demotomd
description: |
  从 demo 代码反向生成/同步 requirement.md，替代传统 PRD 作为产品经理交付给研发的需求文档。不限定技术框架，支持 React/Vue/Angular/Svelte/原生HTML 等任何前端 demo。
  Trigger when: sync requirement, update requirement.md, extract requirements from code, demo to requirement, sync spec, update spec, generate requirement from demo, code to spec, reverse-engineer demo.
  触发词: 同步需求, 更新需求文档, 从代码提取需求, 演示转需求, 同步规格, 更新规格, 代码转规格, 需求同步, 同步requirement, 生成需求文档, 需求文档同步, demo转需求.
  Use this skill whenever the user has been iterating on a demo and wants the requirement.md to reflect all changes made during conversations. Also use when the user asks to prepare the requirement document for developer handoff, or when the user mentions they've finished tweaking a demo and need the spec updated.
user-invocable: true
argument-hint: "[project-path]"
metadata:
  author: user
  version: "2.0.0"
---

# DemoToMD

从 demo 代码中反向提取产品逻辑、规则、边界条件，生成/更新 requirement.md，作为产品经理交付给研发的权威需求文档。不限定技术框架。

---

## 使用场景

产品经理使用 AI 编程工具（Kiro、Claude Code 等）构建可交互 demo。在 spec 模式下先写 requirement.md，然后通过多轮自然语言对话迭代 demo。每次迭代后，运行本 skill 将 demo 中实际实现的产品逻辑同步回 requirement.md。

研发同学拿到两样东西：
1. **可交互的 demo** — 操作体验理解需求
2. **requirement.md** — 直接喂给自己的 AI 编程工具，按产品意图开发

requirement.md 的核心读者是**研发的 AI 编程工具**，不是研发本人，也不是 UI 设计师。因此文档聚焦产品逻辑、业务规则、状态流转、极限场景，不涉及技术实现细节和 UI 视觉规格。

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

**确定文件名**：

```
项目名 = package.json 的 name 字段，或目录名
项目名转为 PascalCase（如 order-management → OrderManagement）
REQUIREMENT_FILE = "[项目名]_requirement.md"         ← 例如 AIPPT_requirement.md（给研发）
UI_REQUIREMENT_FILE = "[项目名]_ui_requirement.md"    ← 例如 AIPPT_ui_requirement.md（给 UI）
TEST_REQUIREMENT_FILE = "[项目名]_test_requirement.md" ← 例如 AIPPT_test_requirement.md（给测试）
LOG_FILE = "[项目名]_Requirement_log.md"              ← 例如 AIPPT_Requirement_log.md
```

**Step 2 — 读取 `references/requirement-template.md`**

获取 requirement.md 的完整模板结构。这一步是必须的，不要跳过。

**Step 3 — 判断更新模式与更新范围**

**3a. 判断更新模式**（对每个文档独立判断）：

```
IF 文档不存在 OR 文件 < 20 行 OR 文件中没有 @meta 块:
    MODE = "full-rewrite"

ELSE IF @meta 中 last-full-rewrite 距今超过 7 天:
    MODE = "full-refresh"

ELSE:
    MODE = "incremental"
    识别哪些源文件在上次同步后被修改
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
初始化: UPDATE_DEV = false, UPDATE_UI = false, UPDATE_TEST = false

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
```

**Round 4 — 业务规则与极限场景提取**

从代码中识别以下模式：
- `if/else` 渲染链 → 条件展示规则
- `useMemo` 复杂计算 → 业务计算规则
- 验证 schema (zod/yup) → 输入约束规则
- `disabled`, `hidden`, `readOnly` 条件 → 权限/状态规则
- `useReducer` / `switch-case` 状态流转 → **状态机**（用 ASCII 图描述状态及转换）
- 多步骤事件处理链 → **流程图**（用 ASCII 图描述步骤和分支）
- Loading/Empty/Error 状态处理 → 异常场景
- 内容溢出、空数据、网络异常、操作异常 → **极限场景**（必须覆盖4类：内容溢出、空内容、网络异常、用户操作异常）

**Round 5 — 验收标准、数据埋点与 UI 交互分析**

```
对每个功能:
- 从操作流程、交互规则、校验规则、极限场景中提炼验收标准
- 标注优先级: P0(核心路径) / P1(重要非阻塞) / P2(边界异常)

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

---

### Phase C: Generate / Update Documents

根据 Phase A 中判断的 UPDATE_DEV、UPDATE_UI、UPDATE_TEST 标志，生成/更新对应文档。**同一次代码分析，输出不同侧重点的文档**。

#### 研发需求文档（`[项目名]_requirement.md`）— UPDATE_DEV = true 时执行

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中研发文档的结构，生成完整的文档。7 个章节：

1. **产品概述** — 产品描述 + 目标用户 + **目标设备**（PC/移动端/自适应/混合App/小程序）
2. **页面结构与导航** — 页面清单 + 导航关系 + **页面间参数传递**
3. **功能逻辑** — 每个功能：目的 + 操作流程 + 状态机 + 交互规则 + 校验规则 + 极限场景 + **验收标准**
4. **业务规则** — 计算规则 + 条件逻辑 + 数据处理规则
5. **数据模型** — 核心实体 + Mock 数据说明
6. **已知缺口** — 简化逻辑 + 缺失功能 + TODO
7. **数据埋点** — 核心指标 + 页面浏览 + 用户行为 + 业务事件

每个章节必须有实质内容，不得留空占位符。如果某项信息在代码中未检测到，标注 "代码中未检测到，需产品经理补充"。

**增量模式 (incremental)**

1. 读取现有 requirement.md
2. 分析变更文件，确定影响哪些章节
3. 用 **Edit 工具**只更新受影响的章节（不要重写全文）
4. 在更新的章节标题后追加 `[Updated YYYY-MM-DD]`
5. 保留用户手动添加的自定义内容（模板之外的部分）

#### UI 需求文档（`[项目名]_ui_requirement.md`）— UPDATE_UI = true 时执行

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中 UI 文档的结构，生成完整的文档。5 个章节：

1. **页面结构与导航** — 页面清单 + 导航关系 + 参数传递对 UI 的影响
2. **交互状态清单** — 每个功能的交互状态矩阵 + 弹窗浮层清单 + 反馈提示清单
3. **视觉元素需求清单** — Icon 需求 + 插图/空状态图 + 占位图/默认图
4. **交互问题标注** — 交互逻辑问题 + 缺失的交互反馈 + 响应式适配需求
5. **组件复用说明** — 重复 UI 模式 + 现有设计系统复用

**增量模式 (incremental)**

1. 读取现有 ui_requirement.md
2. 分析变更文件对交互状态/视觉元素的影响
3. 用 **Edit 工具**只更新受影响的章节（不要重写全文）
4. 在更新的章节标题后追加 `[Updated YYYY-MM-DD]`

#### 测试需求文档（`[项目名]_test_requirement.md`）— UPDATE_TEST = true 时执行

**全量模式 (full-rewrite / full-refresh)**

按照 `references/requirement-template.md` 中测试文档的结构，生成完整的文档。7 个章节：

1. **测试范围与优先级** — 功能清单 + 优先级 + 变更 vs 未变更
2. **业务逻辑验收标准** — 每个功能的详细 AC（前置条件、测试步骤、测试数据、预期结果）
3. **角色与权限测试矩阵** — 每个角色在每个功能点的权限状态
4. **状态流转测试** — 每个合法/非法状态转换的测试用例
5. **极限场景测试清单** — 4 类极限场景的具体测试步骤
6. **数据边界测试** — 每个字段的正常值/边界值/异常值
7. **回归测试建议** — 冒烟测试清单 + 关联功能回归

**关键原则**：每个 AC 都必须包含具体的测试步骤、测试数据和预期结果，测试老师的 Agent 能直接转化为测试用例。

**增量模式 (incremental)**

1. 读取现有 test_requirement.md
2. 分析变更对验收标准、极限场景、数据边界的影响
3. 用 **Edit 工具**只更新受影响的章节（不要重写全文）
4. 在更新的章节标题后追加 `[Updated YYYY-MM-DD]`
5. 如果新增了功能，在对应章节追加新的 AC 条目
6. 如果修改了业务规则，更新对应的 AC 预期结果

**元数据块**

在文件开头更新 `@meta` 块：

```
<!--
@meta
version: [递增]
last-updated: [当前日期时间，格式 YYYY-MM-DD HH:mm:ss]
last-full-rewrite: [全量模式时更新为当前日期时间，增量模式保持不变]
update-mode: [当前模式]
source-hash: [所有源文件路径+大小的哈希]
@/meta
-->
```

**同步生成 Requirement_log.md**

每次同步 requirement.md 时，同步更新 `Requirement_log.md`：

```
1. 获取 git commit hash:
   - 运行 git rev-parse --short HEAD 获取短 hash
   - 运行 git status --porcelain 检查是否有未提交变更
   - 有未提交变更则 hash 后追加 " (dirty)"
   - 非 git 仓库则填 "N/A"

2. 写入日志记录:
   - 若 Requirement_log.md 不存在: 创建文件，写入表头 + 第一条记录
   - 若已存在: 用 Edit 工具在表格末尾追加一行新记录
   - 不要重写整个 log 文件

3. 日志格式:
   | 序号 | 时间 | Git Commit | 更新模式 | 修改章节 | 修改内容 | requirement.md 版本 |
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
├── 更新模式: full-rewrite / incremental / full-refresh
├── 更新范围: [研发文档] / [UI文档] / [测试文档] / [研发+UI+测试]
├── 研发文档: N 个页面, M 条业务规则, K 个状态机, F 个流程图
│   ├── 极限场景: 内容溢出[X项], 空内容[X项], 网络异常[X项], 操作异常[X项]
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
└── 变更摘要: [一句话描述主要变化]
```

**Step 3 — 用户确认**

向用户展示摘要，询问是否确认写入。用户可以：
- 确认写入
- 要求修改特定部分
- 取消操作

**Step 4 — 写入文件**

确认后将更新的文档写入项目根目录。可能的文件：
- `[项目名]_requirement.md` — 研发需求文档
- `[项目名]_ui_requirement.md` — UI 需求文档
- `[项目名]_test_requirement.md` — 测试需求文档
- `[项目名]_Requirement_log.md` — 变更日志（每次同步都追加）

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
| 增量模式覆盖用户手动添加的内容 | 保留模板之外的自定义内容 |
| 不经过用户确认直接写入 | Phase D 的确认步骤不可跳过 |
| 分析所有文件导致上下文溢出 | 按优先级分轮读取，增量模式只读变更文件 |
| 包含技术实现细节 | 不写技术栈、API接口契约、色值字号等，研发有自己的选型 |
| 过度描述 UI 视觉细节 | 不描述布局、组件树等，UI 设计师负责视觉规格 |
| 省略验收标准 | 每个功能必须有可验证的验收条件 |
| 只看源码变更不看对话上下文 | 用户 prompt 描述的后端逻辑即使没改 demo，也必须更新文档 |
| 文档间逻辑丢失 | Phase D 一致性校验不可跳过，确保 demo 逻辑在文档中不丢失 |
| 省略数据埋点 | 必须从核心指标梳理埋点事件 |

---

## 使用方法

### 方式一：手动触发
```
/sync-requirement
/sync-requirement /path/to/project
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
4. **复杂逻辑必须有状态机** — 涉及多个状态流转（审批流、订单状态、工作流）时，用 ASCII 状态机图 + 状态表格描述
5. **复杂流程必须有流程图** — 涉及多步骤操作或条件分支时，用 ASCII 流程图描述完整路径
6. **极限场景必须覆盖** — 每个功能必须考虑 4 类极限场景：内容溢出、空内容/无数据、网络与接口异常、用户操作异常。代码中未处理的要标注"需补充"
7. **验收标准必须可验证** — 每个功能必须有具体的、可测试的验收条件，覆盖正向路径、逆向路径、边界条件
8. **数据埋点从指标出发** — 从核心业务指标反推需要埋点的事件，不盲目罗列
9. **Demo 产物必须标注** — 明确告知哪些是 mock 数据、简化逻辑、缺失功能
