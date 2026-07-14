# 模板使用指南

本指南说明 skill 的输出模板——已移到 cantor 共享文档库 `md/QA/`（多角色共用）。

## 位置与结构

```
cantor-os/md/QA/
├── requirements.md.tpl                    需求规范模板（10 章结构 + 行内注释）
└── requirements-analysis.md.tpl           需求分析报告模板（9 节结构）
```

运行时引用路径：`~/.cantor-os/md/QA/*.tpl`。脚本 `generate-skeleton.py` 经 `Path(__file__).resolve()` 穿透 junction 定位到仓库 `md/QA`。

## 模板格式

- 纯 Markdown
- 用 `{占位符}` 表示变量（中文友好，便于识别）
- 占位符分两类：
  - **脚本管理**：`generate-skeleton.py` 自动替换（feature/today/element_name）
  - **用户级**：保留原样供 LLM/用户手填（如 `{项目名称}` `{角色1}` `{状态A}`）

## 占位符总表

### 脚本管理占位符（自动替换）

| 占位符 | 含义 | 默认值 |
|-------|------|-------|
| `{feature}` | 功能/项目名 | `--feature` 参数（默认"新功能"）|
| `{today}` | 生成日期（ISO 8601）| 今日日期 |
| `{element_name}` | 样例元素名 | "样例元素" |

### 用户级占位符（手填，保留原样）

模板中其他形如 `{项目名称}`、`{角色1}`、`{操作1}`、`{状态A}`、`{触发动作}`、`{规则描述}` 等占位符，脚本**不会替换**，会保留 `{xxx}` 字面留给用户/LLM 手填。

这样设计的原因：
- 中文占位符自带语义，用户一看就知道该填什么
- 避免与模板里 YAML 块的 `{ key: value }` 嵌套语法冲突
- LLM 在第三步「生成 requirements.md」时按章节逐一替换占位符

### AC 来源列约定（关键）

`requirements.md.tpl` 在「五、验收标准」章节定义了带"来源"列的 AC 表格。来源列的填写规则：

| 占位符模式 | 含义 | 实际填写示例 |
|---------|------|------------|
| `C{xx}#{n}` | 来自 analysis 中元素 C{xx} 的第 {n} 条检查点 | `C13#1` |
| `BR{xx}#{n}` | 来自业务规则 BR{xx} 的第 {n} 条 | `BR06#3` |
| 多个来源 | 半角逗号 + 空格分隔 | `C13#1, BR04#2` |
| `—` | 纯技术规范类 AC，无对应 analysis 检查点 | `—`（需在 AC 行后注释原因） |

来源列是 `cross-check.py` 做精确 ID 匹配的依据。`validate-requirements.py` 会校验：
- 每条 AC 的来源列是否填写（不能为空）
- AC 编号格式是否合规（`AC-NN-NN` 或 `AC-NN-NNa`，禁止多层后缀）

详细规则见 [output-format-cheatsheet.md](output-format-cheatsheet.md#ac-来源列-id-命名规则强制)。

## 模板内容来源

`requirements.md.tpl` 融合自：
- **`.kiro/steering/requirements-template.md`（V1）**：内容主体（10 章 + 行内强制性注释 + 用户级占位符）
- **skill 工程化外壳**：`{feature}` `{today}` 顶部元信息

steering 模板保留作为人工手动 `#requirements-template` 触发的复制源，本模板与 steering 内容同源。如 steering 模板更新，需手动同步 `md/QA/` 下对应文件。

## 谁在消费

| 消费方 | 用途 |
|--------|------|
| `scripts/generate-skeleton.py` | 读取模板 → 替换脚本管理占位符 → 生成空骨架文件 |
| LLM（手动） | 直接复制 .tpl 内容做参考，按章节手填用户级占位符 |

## 如何修改模板

1. 直接编辑对应的 `.tpl` 文件（纯 markdown，无需任何工具）
2. **保留所有 `{xxx}` 占位符**——脚本会按字面 substitute 已知占位符，未知占位符保留
3. 改完跑 `python scripts/generate-skeleton.py --output-dir test/ --feature "test"` 验证模板能被正常渲染
4. 如需新增**脚本管理**占位符：
   - 模板里加 `{new_var}`
   - 在本指南占位符表添加
   - 在 `generate-skeleton.py` 的 `SCRIPT_MANAGED_PLACEHOLDERS` tuple + `template_vars` dict 同步添加
5. 如需新增**用户级**占位符：
   - 直接在模板里加 `{中文占位符}`
   - 在本指南用户级占位符段落里说明（可选）
   - **不需要改脚本**

## 设计原则

- **模板与脚本解耦**：模板独立成文件，脚本只负责读+替换。改用户级占位符不改脚本。
- **纯 markdown**：不引入 Jinja2 等第三方模板引擎（违反 skill「纯标准库」原则）。
- **占位符两层分级**：脚本管理 vs 用户级，避免 YAML 嵌套花括号冲突。
- **行内注释保留**：steering 模板的 `>` 强制性注释（如"每条规则必须有正向断言"）必须保留，这是项目实战经验沉淀。

## 反模式

- ❌ 不要在模板里写死项目名（如"我的教程"）——只能用 `{feature}` 占位符
- ❌ 不要用 `str.format` / `format_map` 替换——遇到 YAML `{ key: {var} }` 会触发 `Invalid format specifier`，必须用 `str.replace` 精确替换
- ❌ 不要在模板里放真实 PRD 内容——只放结构性骨架，避免后续 cross-check 把样板内容当成真实数据
- ❌ 不要删除 `>` 行内注释——这些是 steering 模板沉淀的项目实战经验
