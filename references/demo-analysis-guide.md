# Demo 代码分析指南（通用版）

本指南定义如何从任意前端 demo 代码中提取产品逻辑、规则和边界条件。不限定技术框架，适用于 React、Vue、Angular、Svelte、原生 HTML/JS 等任何前端技术。

---

## 0. 分析前提：PM 本地演示 demo

demotomd 面向的不是生产工程，而是产品经理用 AI 编程工具快速搭建的本地演示 demo。分析时必须先建立以下判断：

1. **demo 的核心价值是业务确认**：页面、流程、交互、字段、状态、提示等，通常是 PM 与业务方沟通后沉淀出的产品意图。
2. **前端实现有较高参考价值**：前端页面结构、导航路径、交互状态、表单字段、提示文案、空状态和异常反馈，应完整提取到研发/UI/测试文档中。
3. **后端实现不可直接复用**：demo 中的后端、伪接口、mock 服务、写死数据、内存存储、简化鉴权、大模型返回、知识库结果等，通常只是演示手段。只能提取业务规则，不能把实现方式写成研发要求。
4. **正式实现要求要单独标注**：凡是代码里出现 mock、硬编码、模拟延迟、固定账号、固定返回、前端计算、前端权限判断，都要写清“当前 demo 处理方式”和“正式实现要求”。
5. **真实服务端项目要先确认**：如果项目包含服务端和数据库能力，不能默认它只是 demo，也不能默认它就是线上技术栈。需要先向用户确认线上项目是否同技术栈、是否需要输出服务端需求文档。

分析输出时遵循这个转换：

| demo 中看到的内容 | 文档中应该表达为 |
|------------------|----------------|
| 本地数组、JSON、fixtures | 当前为 mock 数据；正式需对接真实数据源 |
| setTimeout 模拟接口 | 当前为模拟延迟；正式需有接口 loading、超时、失败、重试处理 |
| 前端写死角色权限 | 当前为演示权限；正式需后端鉴权与接口级权限校验 |
| 前端计算业务结果 | 当前 demo 在前端计算；正式需确认计算归属，通常由后端或服务层返回 |
| 写死大模型回复 | 当前为静态示例；正式需对接模型、提示词、知识库和安全策略 |
| 本地存储登录状态 | 当前为演示登录；正式需对接统一登录、token 续期和失效处理 |

---

## 1. 技术栈识别

### 1.1 框架检测

先扫描项目根目录，识别 demo 使用的技术栈，然后采用对应的提取策略：

| 检测信号 | 技术栈 | 特征文件/依赖 |
|----------|--------|--------------|
| `package.json` 含 `"react"` | React | `*.jsx`, `*.tsx` |
| `package.json` 含 `"vue"` | Vue | `*.vue` |
| `package.json` 含 `"@angular/core"` | Angular | `*.component.ts`, `*.module.ts` |
| `package.json` 含 `"svelte"` | Svelte | `*.svelte` |
| `package.json` 含 `"next"` | Next.js | `app/` 或 `pages/` 目录 |
| `package.json` 含 `"nuxt"` | Nuxt | `pages/` 目录 |
| 无 `package.json`，有 `.html` | 原生 HTML/JS | `*.html`, `*.js`, `*.css` |
| 有 `index.html` + `*.py` | Python Web | Flask/Django/FastAPI |
| 有 `*.java` + 模板引擎 | Java Web | Thymeleaf/JSP |

### 1.2 必读文件（Round 1，并行读取）

| 文件 | 提取内容 |
|------|----------|
| `package.json` / `pom.xml` / `requirements.txt` 等 | 项目名（不提取技术版本，研发有自己的选型） |
| `README.md` | 产品描述 |
| 路由配置文件 | 页面结构、路由映射 |
| `index.html` / 入口文件 | 页面入口结构 |

### 1.3 页面发现（Round 2）

根据识别的框架，搜索路由配置：

| 框架 | 搜索目标 |
|------|----------|
| React Router | `createBrowserRouter`, `<Routes>`, `<Route`, `useRoutes` |
| Vue Router | `createRouter`, `<router-view>`, `routes: [...]` |
| Angular | `RouterModule.forRoot`, `routerLink` |
| Next.js | `app/` 目录结构 / `pages/` 目录结构 |
| Nuxt | `pages/` 目录结构 |
| SvelteKit | `src/routes/` 目录结构 |
| 原生 HTML | 多个 `*.html` 文件，`<a href=...>` 链接关系 |
| 通用 | 文件路径含 `router`, `routes`, `app` 的文件 |

提取所有页面/路由 → 获得功能全貌。

### 1.4 源码发现（Round 3）

通用 Glob 模式（按优先级）：

```
优先级 1 — 页面/视图文件:
  src/pages/**/*
  src/views/**/*
  src/screens/**/*
  pages/**/*
  app/**/page.*         (Next.js App Router)
  *.html                (原生项目)

优先级 2 — 组件文件:
  src/components/**/*
  src/shared/**/*
  src/widgets/**/*
  components/**/*

优先级 3 — 业务逻辑:
  src/hooks/**/*
  src/composables/**/*  (Vue)
  src/services/**/*
  src/utils/**/*
  src/store/**/*
  src/api/**/*
  src/stores/**/*       (Pinia)
  src/context/**/*
  src/providers/**/*

优先级 4 — 类型/模型:
  src/types/**/*
  src/models/**/*
  src/interfaces/**/*
  **/*.d.ts
```

---

## 2. 代码分析清单

对每个文件，按以下维度提取产品逻辑。不同框架有不同的实现方式，但提取的产品信息是相同的。

### 2.1 数据入口（Props / Attributes / Properties）

| 框架 | 搜索目标 |
|------|----------|
| React | TypeScript interface/type, PropTypes, 解构的 props |
| Vue | `defineProps()`, `props: {...}`, `withDefaults()` |
| Angular | `@Input()` 装饰器 |
| Svelte | `export let propName` |
| 原生 | 函数参数, data-* 属性 |

记录: 参数名、类型、是否必填、默认值、业务含义。

### 2.2 内部状态（State）

| 框架 | 搜索目标 |
|------|----------|
| React | `useState`, `useReducer`, `useRef`, `useContext` |
| Vue | `ref()`, `reactive()`, `computed()`, `watch()` |
| Angular | 组件属性, `BehaviorSubject`, `Signal` |
| Svelte | `let`, `$:` 响应式声明, `$state` |
| 原生 | 普通变量, `data-*` 属性, `localStorage` |

记录每个状态: 变量名、初始值、何时被修改、修改的触发条件、影响哪些 UI 输出。

### 2.3 事件处理（用户交互）

| 框架 | 搜索目标 |
|------|----------|
| React | `onClick`, `onChange`, `onSubmit`, `onKeyPress` 等 |
| Vue | `@click`, `@input`, `@submit`, `@change` 等 |
| Angular | `(click)`, `(input)`, `(submit)` 等 |
| Svelte | `on:click`, `on:input`, `on:submit` 等 |
| 原生 | `addEventListener`, `onclick=`, `onsubmit=` 等 |

对每个事件处理:
1. 分析完整逻辑链
2. 记录: 触发元素 → 前置条件 → 执行逻辑 → 状态变化 → UI 更新
3. 特别关注链式操作: 事件 → 数据请求 → 状态更新 → UI 变化

### 2.4 条件渲染（业务规则）

这是提取产品规则的核心。所有框架都有条件展示/隐藏的能力：

| 框架 | 搜索目标 |
|------|----------|
| React | `{condition && <X/>}`, `{condition ? <A/> : <B/>}`, `style={{display:...}}` |
| Vue | `v-if`, `v-show`, `v-else`, `v-else-if` |
| Angular | `*ngIf`, `[hidden]`, `[class.active]="condition"` |
| Svelte | `{#if condition}`, `class:active={condition}` |
| 原生 | `display: none`, `visibility: hidden`, `classList.toggle` |
| 通用 | `disabled`, `readOnly`, `hidden` 属性 |

对每个条件:
1. 提取条件表达式（简化为自然语言）
2. 记录: 条件 → 为真时表现 → 为假时表现
3. 归类: 权限规则 / 状态规则 / 数据规则 / 环境规则

### 2.5 数据请求

| 框架/库 | 搜索目标 |
|---------|----------|
| 原生 | `fetch()`, `XMLHttpRequest` |
| Axios | `axios.get/post/put/delete` |
| React Query | `useQuery`, `useMutation` |
| SWR | `useSWR` |
| Vue | `useFetch` (Nuxt), 自定义 composable 中的请求 |
| Angular | `HttpClient`, `this.http.get/post` |
| 通用 | `$.ajax`, `$.get`, 任何返回 Promise 的函数 |

对每个请求:
1. 记录: 请求目的、何时触发、成功后做什么、失败后做什么
2. 识别是否使用了 mock 数据
3. 判断请求是否只是 demo 演示用伪接口、前端服务函数或写死返回
4. 不提取具体 URL 和 HTTP 方法（研发自己定义接口）
5. 只把请求背后的产品意图写入文档，例如“提交后生成订单并进入待审核状态”“系统根据教材资源返回推荐内容”

特别注意：如果 demo 里存在后端目录、server 脚本或 API route，也不要默认它是正式后端方案。产品经理本地 demo 的后端通常只是为了让演示闭环跑通，文档中应转化为业务能力、数据来源、异常处理和正式实现要求。

### 2.6 导航行为与页面间参数传递

| 框架 | 搜索目标 |
|------|----------|
| React Router | `useNavigate()`, `<Link to>`, `<Navigate to>` |
| Vue Router | `router.push()`, `<router-link to>`, `this.$router` |
| Angular | `Router.navigate()`, `routerLink` |
| SvelteKit | `goto()`, `<a href>` |
| 原生 | `window.location.href`, `<a href>`, `history.push` |

对每个导航:
1. 记录: 从哪个页面触发、目标页面、触发条件、是否携带参数
2. 特别关注参数传递: `useParams`、`useSearchParams`、URL query、state 传递
3. 记录参数的用途和目标页面如何消费这些参数

### 2.7 表单与验证

| 框架/库 | 搜索目标 |
|---------|----------|
| 原生 | `<form onsubmit>`, `required`, `pattern`, `minlength`, `maxlength` |
| React | react-hook-form, formik, zod, yup |
| Vue | vee-validate, vuelidate, `rules` 配置 |
| Angular | Reactive Forms, Template-driven Forms, Validators |
| 通用 | `required`, `minLength`, `maxLength`, `min`, `max`, `pattern` |

对每个表单: 列出所有字段、每个字段的验证规则、提交逻辑、错误提示文案。

### 2.8 交互元素逐个机械化扫描（不漏控件）

> 反向工程时容易"凭理解归纳"而漏掉看似不重要的控件（如某个筛选项、驱动下游逻辑的 Checkbox 组、隐藏的只读字段）。必须机械化逐控件列出，再做合并判断。

**扫描清单（逐个列出，不可凭印象省略）**：

| 控件类型 | 搜索目标 |
|----------|----------|
| 输入类 | `<Input>`, `<InputNumber>`, `<Textarea>`, `<input type=text/number/password/email>` |
| 选择类 | `<Select>`, `<Cascader>`, `<DatePicker>`, `<Radio>`, `<Checkbox>`, `<Switch>` |
| 触发类 | `<Button>`, `<a>`, 可点击的 `<div>/<span>`、图标按钮 |
| 数据展示 | `<Table>`, `<List>`, `<Tree>`, `<Tabs>`, `<Pagination>`, 图表组件 |
| 容器/浮层 | `<Modal>`, `<Drawer>`, `<Popover>`, `<Tooltip>`, `<Alert>` |
| 上传/下载 | `<Upload>`, 文件选择、导出按钮 |

**操作要求**：
1. 逐行检查原型中的每一个上述控件，先全部列出，再做合并判断
2. 搜索/筛选区的每个独立筛选项都是独立元素，不可因交互模式相似就省略
3. 每个控件记录：元素名、所在页面、触发行为、所有状态（默认/hover/激活/loading/禁用/错误/空态）、关联的业务规则
4. 控件驱动下游逻辑的（如某 Checkbox 控制后续字段显隐），必须记录联动关系

---

## 3. 业务规则提取模式

无论使用什么框架，业务规则的提取逻辑是相同的：

### 3.1 条件展示规则

```
任何框架中的条件展示:
条件: user.role === 'admin'
效果: 非管理员看不到管理面板
→ 产品规则: 仅管理员可见管理菜单
```

### 3.2 计算规则

```
任何框架中的计算逻辑:
总价 = Σ(单价 × 数量) × (1 - 折扣/100)
→ 产品规则: 按商品明细汇总后应用折扣
```

### 3.3 状态机规则

```
任何框架中的 switch-case 或 if-else 状态判断:
draft → pending → approved / rejected
→ 用 mermaid stateDiagram-v2 + 状态表格描述完整的状态流转
→ 每个状态记录: UI表现、可执行操作、转换条件
```

### 3.4 权限控制规则

```
任何框架中的权限判断:
条件: 用户是管理员 OR 用户是记录所有者
效果: 控制编辑按钮的可见性和可操作性
→ 产品规则: 明确列出每个角色的权限范围
```

---

## 4. 极限场景检测（必须覆盖5类）

> 每个功能都必须检查以下5类极限场景。代码中有处理的记录实现，未处理的标注"代码中未处理，需补充"。

### 4.1 内容溢出

```
搜索: pagination, pageSize, currentPage → 数据量大时的处理
     text-overflow, line-clamp, truncate → 长文本处理
     overflow-x, scroll → 宽内容处理
     object-fit, resize → 大图处理

提取: 是否有分页/虚拟滚动，文本是否截断，表格是否可滚动
```

### 4.2 空内容/无数据

```
搜索: .length === 0, !data, data === null, isEmpty
     空状态组件: Empty, NoData, "暂无数据", "no results"
     v-if="list.length === 0" (Vue), *ngIf="!data.length" (Angular)

提取: 什么条件下显示空状态 → 空状态 UI → 用户可执行的操作
```

### 4.3 网络与接口异常

```
搜索: try/catch 块 → 错误处理
     onError 回调 → 错误回调
     toast.error, notification.error → 错误提示
     retry, refetch → 重试机制
     navigator.onLine → 网络状态检测
     beforeunload → 页面离开确认

提取: 是否处理了请求失败、超时、断网、重复提交
```

### 4.4 用户操作异常

```
搜索: isLoading, isFetching, isPending → 防重复提交
     disabled, readonly → 操作限制
     debounce, throttle → 防抖/节流
     beforeunload → 页面离开确认
     Math.min, Math.max → 数值边界限制

提取: 是否有防重复提交、防丢失数据、防并发冲突机制
```

### 4.5 并发与竞态

```
搜索: version / updatedAt / etag → 乐观锁字段
     幂等键 idempotencyKey / requestId → 去重机制
     事务/原子操作 transaction, atomic → 数据一致性保障
     库存扣减 stock, inventory, decrement → 防超卖

提取: 是否处理了两人同时编辑、并发扣减、重复提交幂等、并发状态变更
```

---

## 5. 验收标准提炼

> 从每个功能的操作流程、交互规则、校验规则、极限场景中提炼可验证的验收条件。

### 5.1 提炼方法

对每个功能，从以下维度生成验收标准：

| 维度 | 提炼来源 | 示例 |
|------|----------|------|
| 正向路径 | 操作流程中成功路径的每一步 | "用户填写完整表单后点击提交，能成功创建订单" |
| 逆向路径 | 校验规则和错误处理 | "手机号为空时提交，显示'请输入手机号'错误提示" |
| 边界条件 | 极限场景中的边界值 | "列表加载超过1000条数据时，使用分页加载而非一次全量" |
| 状态约束 | 状态机中每个状态的权限 | "订单状态为'已取消'时，不显示'再次购买'按钮" |
| 权限控制 | 条件逻辑中的权限规则 | "非管理员用户看不到'删除'按钮" |

### 5.2 优先级标注

- **P0**: 核心业务路径，必须通过否则功能不可用
- **P1**: 重要但非阻塞性条件
- **P2**: 边界情况和异常处理

### 5.3 断言化与可测性检查（每条 AC 必过）

提炼出 AC 后，逐条过两道检查，不通过的在测试文档标注：

**断言化试金石**：AC 的预期结果能否写成 `expect(可观测).toBe(具体值)`？
- 具体值 = 字面文案 / 数字 / 路由 / 枚举 / 布尔 / 可见·隐藏 / 启用·禁用 / 跳转目标
- 模糊词（正常/正确/符合预期/合理/清晰/良好/准确）= 视同未定义，需补具体值或标待确认
- 精确文案必须溯源到 demo 代码 / PRD，禁止虚构

**可测性三问**：
1. 前置态可构造吗（测试员能否自己切到该状态）
2. 断言点可观测吗（结果在可见 UI，还是内部态/日志/埋点）
3. 核对清单是有限确定集吗（非"其它/…等/各种"开放集）
- 命中且无法补全 → 标 🚫不可测 + 等待方（产品/研发）

> 目的：把"写测试脚本时才发现测不了 / 填不出 toBe(?)"的痛，提前到分析阶段暴露。

---

## 6. 数据埋点识别

> 从产品核心指标出发，梳理需要追踪的用户行为和业务事件。

### 6.1 核心指标推断

从产品描述和目标用户中推断核心业务指标：
- 电商类: 转化率、客单价、复购率
- 工具类: 使用频次、功能覆盖率、留存率
- 社交类: 发帖量、互动率、活跃度
- 管理类: 操作效率、审批时效、数据准确率

### 6.2 埋点事件提取

从代码中识别可埋点的用户行为：

```
页面浏览: 每个路由页面的加载 → 页面浏览埋点
用户操作: 关键 onClick/onSubmit 事件 → 行为埋点
状态流转: 状态机的关键转换节点 → 业务事件埋点
```

提取时记录:
- 事件名称（用 `category_action_target` 格式）
- 触发时机（什么时候发送）
- 采集参数（事件携带哪些上下文信息）
- 关联指标（该事件用于计算哪个核心指标）

### 6.3 埋点优先级

优先覆盖与核心指标直接相关的事件：
1. 转化漏斗中的每一步操作
2. 核心业务流程的完成事件
3. 用户主动触发的关键操作
4. 异常场景的发生（用于监控）

---

## 7. 分析优化策略

### 7.1 大型项目分批分析

当源码文件超过 30 个时：

1. **Round 1**: 只读路由配置 + 入口页面 → 获得功能全貌
2. **Round 2**: 根据用户关注点或变更文件，选择性深入分析
3. **Round 3**: 共享组件和工具函数按需补充

### 7.2 增量模式优化

当更新模式为 `incremental` 时：

1. 扫描 `PM_Requirement/` 下最新的 `Requirement_[版本号]` 文件夹作为基线版本
2. 从基线版本的 `version-manifest.md` 和各文档 `@meta.analyzed-files` 获取上次分析范围
3. 比较源文件 hash / 修改时间 / 对话意图，识别本次新增、变更、废弃内容
4. 只重新分析变更文件及其直接依赖链
5. 输出时只写相对基线版本的增量需求，未变化内容不重复展开

### 7.3 利用对话上下文

如果当前对话中存在关于 demo 修改的讨论：

1. 从对话中提取: 修改了什么、修改了什么逻辑、修改原因
2. 直接定位到相关文件和逻辑
3. 跳过未涉及的部分
4. 这比纯文件分析更准确、更高效

### 7.4 非 JS/TS 项目的分析

对于非 JavaScript/TypeScript 项目（如 Python Flask、Java Thymeleaf）：

1. 识别模板文件中的 HTML 结构
2. 从后端路由定义中提取页面映射
3. 从模板中的条件判断提取业务规则（如 `{% if %}`, `<c:if>`, `<th:if>`）
4. 从表单元素中提取验证规则
5. 产品逻辑提取原则与前端框架完全相同

---

## 8. Mock 数据识别

### 8.1 Mock 模式识别

| 模式 | 搜索目标 |
|------|----------|
| 本地数据文件 | `mocks/**/*.json`, `fixtures/**/*`, `seed/**/*` |
| 内存 mock | 返回固定数据的函数, `Math.random` 生成的假数据 |
| 条件式 mock | `if (process.env.NODE_ENV === 'development')`, `IS_MOCK` |
| 硬编码数据 | 组件/页面内的 `const data = [...]`, 内联数组/对象 |
| 模拟延迟 | `setTimeout(() => resolve(data), N)`, `await delay(N)` |

### 8.2 记录 Mock 产物

对每个 mock 数据源：
- 记录当前 mock 的数据内容和结构
- 标注正式实现时应该对接的真实数据源
- 记录 mock 中的特殊处理（如延迟、随机数据）
- 标注它影响哪些角色文档：
  - 研发文档：写入“Mock 数据说明”“已知缺口”“正式实现要求”
  - UI 文档：如果 mock 影响页面状态、空状态、错误态或加载态，写入交互状态矩阵
  - 测试文档：为 mock 对应的正式接口、异常返回、空数据、权限失败补充测试点

### 8.3 后端演示逻辑识别

| 模式 | 搜索目标 | 文档处理方式 |
|------|----------|-------------|
| 本地 server/API route | `server.js`, `api/`, `routes/`, `app/api` | 只提取业务行为，不要求研发复用接口结构 |
| 固定返回 | `return {...}`, `res.json(fixedData)` | 标注为写死返回，正式需真实数据服务 |
| 简化鉴权 | 固定 token、固定用户、前端 role 判断 | 标注为演示鉴权，正式需统一登录和后端权限 |
| 模拟 AI 能力 | 写死生成结果、mock LLM response | 标注为演示结果，正式需对接模型、提示词、知识库、安全审核 |
| 本地文件读写 | JSON 文件读写、localStorage、IndexedDB | 标注为本地存储，正式需数据库或业务系统数据源 |

后端演示逻辑的提取目标不是“研发如何实现”，而是“正式系统必须提供什么业务能力，以及哪些 demo 简化点不能遗漏”。

### 8.4 真实服务端/数据库能力识别

当项目中出现以下信号时，标记 `SERVER_CAPABILITY = detected`，并在主流程中询问用户是否输出服务端需求文档：

| 类型 | 识别信号 | 可能技术栈 |
|------|----------|------------|
| 服务端入口 | `server.ts`, `app.ts`, `main.py`, `manage.py`, `Application.java`, `main.go` | Node/Python/Java/Go 等 |
| API 路由 | `routes/`, `controllers/`, `app/api`, `pages/api`, `routers/` | Express/Nest/Next/FastAPI/Spring |
| 业务层 | `services/`, `usecases/`, `domain/`, `repository/` | 分层后端项目 |
| ORM/模型 | `schema.prisma`, `models.py`, `entity/`, `*.model.ts`, `*.entity.ts` | Prisma/Django/TypeORM/JPA |
| 数据库迁移 | `migrations/`, `alembic/`, `flyway/`, `liquibase/`, `*.sql` | 关系型数据库改造 |
| 数据库配置 | `DATABASE_URL`, `docker-compose` 中的 postgres/mysql/mongo/redis | 数据服务 |

确认用户需要服务端文档后，额外提取：

- 当前服务端技术栈、数据库、ORM、迁移工具
- API/服务能力清单：业务目的、输入输出业务字段、权限、成功/失败结果
- 数据模型：表/实体、字段、关系、索引、唯一约束、审计字段
- 数据库改造：新增/修改字段、迁移脚本、历史数据兼容、回滚风险
- 服务端业务规则：计算、权限、状态流转、数据范围、幂等、并发冲突
- 外部依赖：大模型、知识库、文件服务、第三方系统、消息队列、定时任务

如果用户确认线上项目不是同技术栈，或不需要服务端内容，则不要输出服务端需求文档；只在研发文档中保留必要的业务能力说明。

### 8.5 已知 Bug 与代码缺陷识别

> demo 反向工程时会发现 demo 本身的 bug、写死逻辑、明显错误。这些不是正式版本的需求，但必须记录到测试文档第 8 章「已知 Bug 与缺陷标记」，测试时标 xfail，避免把 demo 已知问题误报为正式版本 bug。

**扫描信号**：

| 信号类型 | 搜索目标 | 判定 |
|----------|----------|------|
| 待办标记 | `TODO`, `FIXME`, `HACK`, `XXX`, `@ts-ignore` | 标记为已知缺陷，注明意图 |
| 写死返回 | `return { ... }` 固定数据、`res.json(fixedData)` | 写死返回，正式需真实数据 |
| 逻辑错误 | 条件反了、边界 off-by-one、空数组未处理、catch 吞错误 | 记录 bug 行为 vs 期望行为 |
| 与业务规则矛盾 | 代码实现与 PRD/注释描述不一致 | 记录矛盾点，等待方=产品/研发 |
| 临时调试代码 | `console.log`、注释掉的代码块、调试开关 | 标记为临时代码，正式需清理 |

**记录格式**：每个已知 bug 记录 BUG-ID、所在文件:行、bug 行为（实际）、期望行为（正确）、是否 xfail、等待方。输出到测试文档第 8 章。
