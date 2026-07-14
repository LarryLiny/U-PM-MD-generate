# U-PM-MD-generate

Unipus 高教产品自动产出 MD 文档的 demotomd skill 开发工程。

## 项目定位

产品经理用 AI 编程工具在本地开发可交互 demo，用于和业务方演示、讨论、确认需求。demo 确认后，需要交给研发、UI、测试继续生产化开发。

这个 skill 的作用，是把本地 demo 翻译成三类核心文档：

| 文档 | 读者 | 作用 |
|------|------|------|
| `PM_Requirement/Requirement_[版本号]/[项目名]_requirement_[版本号].md` | 研发、测试、UI，主要是研发 Agent | 描述完整业务规则、页面流程、状态流转、数据要求、验收标准 |
| `PM_Requirement/Requirement_[版本号]/[项目名]_ui_requirement_[版本号].md` | UI 设计师 | 描述页面、交互状态、弹窗反馈、视觉元素缺口，便于用 Figma 复刻并优化界面 |
| `PM_Requirement/Requirement_[版本号]/[项目名]_test_requirement_[版本号].md` | 测试同学、测试 Agent | 描述测试范围、验收标准、权限矩阵、状态流转、极限场景和数据边界 |
| `PM_Requirement/Requirement_[版本号]/[项目名]_server_requirement_[版本号].md` | 后端研发、后端 Agent | 可选文档。仅当检测到真实服务端/数据库能力，且用户确认线上项目同技术栈并需要输出时生成 |

## 版本管理

每次输出都会统一放到项目根目录下的 `PM_Requirement/` 文件夹中，并在其中创建新的版本目录：

```text
PM_Requirement/
  Requirement_0622001/
  Requirement_0622002/
  Requirement_0622003/
```

版本号规则：当天日期 `MMDD` + 当天自增 3 位。例如 6 月 22 日第一次输出是 `0622001`，第二次输出是 `0622002`。

- 首次交付默认输出全量文档。
- 后续交付默认输出相对上一版的增量文档。
- 增量文档只写本次新增、变更、废弃和待确认内容；未提及内容默认沿用上一版本。
- 每个版本目录必须包含 `version-manifest.md`，`PM_Requirement/` 下保留 `[项目名]_Requirement_log.md` 总日志。

## 关键原则

- demo 是本地演示项目，不是可直接上线的生产工程。
- 前端页面、流程、交互、字段和状态通常代表业务已确认的体验方向，应完整沉淀。
- 后端、接口、权限、数据、大模型返回等经常是 mock、写死或简化实现，只能作为业务意图线索，不能作为研发实现参考。
- 文档必须明确区分“当前 demo 表现”和“正式实现要求”。
- 如果项目包含真实服务端和数据库能力，需要先询问用户线上项目是否同技术栈、是否需要服务端需求文档；用户不需要时不输出服务端内容。
- 每次交付都必须进入 `PM_Requirement/Requirement_[版本号]` 文件夹，不覆盖历史版本。

## 核心文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | skill 主入口，定义触发方式、分析流程、文档生成规则 |
| `references/demo-analysis-guide.md` | demo 代码分析方法论 |
| `references/requirement-template.md` | 三类产出文档的模板结构 |
| `product-workflow.md` | PM 使用 demo 和 demotomd 交付需求的完整工作流 |
