# Demo 代码分析指南（通用版）

本指南定义如何从任意前端 demo 代码中提取产品逻辑、规则和边界条件。不限定技术框架，适用于 React、Vue、Angular、Svelte、原生 HTML/JS 等任何前端技术。

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
3. 不提取具体 URL 和 HTTP 方法（研发自己定义接口）

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
→ 用 ASCII 状态机图 + 状态表格描述完整的状态流转
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

## 4. 极限场景检测（必须覆盖4类）

> 每个功能都必须检查以下4类极限场景。代码中有处理的记录实现，未处理的标注"代码中未处理，需补充"。

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

1. 从 `@meta` 中的 `analyzed-files` 获取上次分析的文件列表
2. 比较每个文件的修改时间与 `last-updated`
3. 只重新分析变更文件
4. 追踪变更文件的依赖链，标记间接影响的文件

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
