# 项目指令：DemoToMD 自动同步

> 将此文件放置于项目根目录，命名为 `CLAUDE.md`

## 自动同步需求文档

本项目使用 demotomd skill 管理需求文档。每次修改 demo 源码后，自动同步需求文档。

### 触发规则

修改以下文件后，自动执行 `/demotomd`：

- `src/` 目录下任何文件
- 根目录 HTML / JS 文件
- 路由配置文件
- 表单验证 schema

### 执行方式

代码修改完成后，在回复用户之前自动调用 demotomd skill。不需要询问用户，直接执行。

### 变更判断

- 改了业务逻辑 / 计算规则 / 权限 → 更新 `_requirement.md` + `_test_requirement.md`
- 改了交互 / 视觉 → 更新 `_ui_requirement.md`
- 新增页面 / 新增功能 → 三个文档都更新
- 用户 prompt 描述了后端逻辑但 demo 未改动 → 仍更新 `_requirement.md` + `_test_requirement.md`

### 约束

- 使用增量更新（Edit 工具），不要全量重写
- 保留用户手动添加的自定义内容
- 除非用户明确说"先不同步"，否则每次改完都执行
