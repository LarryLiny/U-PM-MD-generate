# 脚本使用指南

本 Skill 提供 7 个 Python 脚本辅助执行各步骤。所有脚本均：
- 单文件、纯标准库实现（不需要 pip install）
- 输入 `--help` 查看完整参数
- 默认输出 JSON 到 stdout，可用 `--output` 写入文件
- 摘要信息打印到 stderr，便于 LLM 直接阅读

## 脚本索引

| 脚本 | 对应步骤 | 价值 |
|------|---------|------|
| `extract-elements.py` | 第一步辅助 | 机械化扫描原型组件，避免 LLM 凭印象漏元素 |
| `generate-skeleton.py` | 第三步前置 | 生成 requirements.md / requirements-analysis.md 空模板 |
| `count-coverage.py` | 自检辅助 | 自动统计断言覆盖率，填充 analysis.md 顶部 |
| `cross-check.py` | 第五步核心 | 算法化交叉检查，找出未覆盖的检查点 |
| `validate-requirements.py` | 交付前 | requirements.md 结构合规性校验（17 项） |
| `cleanup-temp.py` | 第六步 | 清理临时文件 |
| `smoke-test.py` | 端到端验证 | 按顺序跑全链路，确保 fixture 全绿 |

---

## 1. extract-elements.py — 机械化扫描原型组件

### 用途

第一步「侦察元素」中，LLM 容易"凭理解归纳式扫描"导致漏元素（如搜索区某筛选项）。本脚本用**四层扫描策略**覆盖不同前端框架/项目结构，逐文件扫描所有交互元素，输出完整清单。

### 四层扫描策略

| 层级 | 扫描对象 | 适用场景 |
|------|---------|---------|
| **L1** (lib) | Antd/Element UI 组件白名单（如 `<Input>` `<Button>` `<Modal>`） | Antd 项目 |
| **L2** (native) | 原生 HTML 交互元素（`<button>` `<a>` `<input>` `<select>` `<form>` `<dialog>` 等） | 原生 DOM 项目 |
| **L3** (custom) | 自定义函数组件（首字母大写但不在 L1 白名单的 JSX 标签） | 自定义组件项目 |
| **L4** (event) | 含 `onClick`/`onChange`/`onSubmit` 等事件绑定的任意元素 | 兜底捕获 |

### 命令行

```bash
# 默认四层全扫
python scripts/extract-elements.py --src ./prototype/

# 用路径过滤聚焦特定模块（推荐）
python scripts/extract-elements.py --src ./prototype/ --include "**/home/**,**/Home.tsx"

# 排除测试和样式文件
python scripts/extract-elements.py --src ./prototype/ --exclude "**/*.test.*,**/*.spec.*"

# 只用某几层（关闭 L4 事件兜底，结果更精炼）
python scripts/extract-elements.py --src ./prototype/ --layers L1,L2,L3

# 输出 JSON 报告
python scripts/extract-elements.py --src ./prototype/ --output elements-scan.json
```

### 关键参数

- `--include`：glob 模式（逗号分隔），只扫描匹配的文件路径。**建议**针对特定模块时使用，避免扫到全项目导致结果稀释
- `--exclude`：glob 模式，排除测试/样式/已生成代码
- `--layers`：选择启用的扫描层。默认 `L1,L2,L3,L4` 全启用；只看精炼结果可用 `L1,L2,L3`

### 输出 schema

```json
{
  "src": "./prototype/",
  "layers": ["L1", "L2", "L3", "L4"],
  "include": ["**/home/**"],
  "exclude": [],
  "files_scanned": 9,
  "files_with_components": 9,
  "total_elements": 93,
  "by_layer": { "L1": 13, "L2": 41, "L3": 39 },
  "by_component": { "native:button": 21, "Link": 13, "custom:ScrollButton": 4 },
  "by_file": { "pages/Home.tsx": 35, "components/Navbar.tsx": 29 },
  "elements": [
    { "layer": "L2", "component": "native:button", "line": 42, "snippet": "<button onClick={...", "file": "pages/Home.tsx" }
  ]
}
```

### 退出码

- `0` 扫描完成（无论找到多少元素）
- `2` 脚本错误（src 不存在、layers 参数非法等）

### 失败时的兜底

脚本扫描结果对当前场景不充分时（如只扫到不相关的元素，元素数为 0 或全部不在目标模块），LLM 必须：
1. 在 analysis 第二节"侦察元素清单"明确说明"`extract-elements.py` 因 XXX 改为手工侦察"
2. 用编辑器/grep 工具逐文件搜索目标交互元素
3. 输出文件路径 + 行号 + 元素名清单

---

## 2. generate-skeleton.py — 生成空模板

### 用途

第三步「生成需求规范」前，先用脚本创建符合 10 章结构的空模板，避免 LLM 漏章或章节顺序不一致。

### 命令行

```bash
python scripts/generate-skeleton.py --output-dir ./specs/my-feature/
python scripts/generate-skeleton.py --output-dir ./specs/my-feature/ --feature "购物车"
python scripts/generate-skeleton.py --output-dir ./specs/my-feature/ --force                       # 覆盖（覆盖前自动备份）
python scripts/generate-skeleton.py --output-dir ./specs/my-feature/ --target requirements --force  # 只重生成 requirements.md
python scripts/generate-skeleton.py --output-dir ./specs/my-feature/ --force --no-backup            # 覆盖且不备份
```

> **覆盖安全（P0-2）**：`--force` 会同时覆盖 `requirements.md` 和 `requirements-analysis.md`（默认 `--target all`）。
> - 默认覆盖前自动把被覆盖的非空文件备份为 `<name>.bak-<时间戳>`（确认无误后可手动删；该后缀不会被 validate 残留检查或 cleanup-temp 误清）。
> - 只想重生成其中一个：用 `--target requirements` 或 `--target analysis` 缩小粒度，不碰另一个。
> - 确定不需要备份：加 `--no-backup`。

### 产出

```
./specs/my-feature/
├── requirements.md              （10 章 + 章节用途索引 + AC/状态机/错误码占位）
└── requirements-analysis.md     （PRD 自检表 + 断言覆盖详情 + 9 个分析章节）
```

### 模板来源

模板已移到 cantor 共享文档库 `md/QA/`（多角色共用，脚本经 `Path(__file__).resolve()` 穿透 junction 定位）：

- `~/.cantor-os/md/QA/requirements.md.tpl` → 渲染为 `requirements.md`
- `~/.cantor-os/md/QA/requirements-analysis.md.tpl` → 渲染为 `requirements-analysis.md`

模板用 `{占位符}` 风格（Python `str.format` 兼容），脚本支持的占位符：

| 占位符 | 含义 | 默认值 |
|-------|------|-------|
| `{feature}` | 功能/项目名 | "新功能"（可由 `--feature` 覆盖）|
| `{today}` | 生成日期（ISO 8601） | 今日日期 |
| `{element_name}` | 样例元素名 | "样例元素" |

修改模板**不需要改脚本**——直接编辑 `.tpl` 即可。占位符表与使用说明见 [templates-guide.md](templates-guide.md)。

### 退出码

- `0` 生成成功
- `1` 目标已存在（未指定 `--force`）
- `2` 脚本错误（模板文件不存在等）

### 失败时的兜底

- 模板缺失：直接复制 `~/.cantor-os/md/QA/*.tpl` 到目标目录手工填充
- 占位符替换失败：脚本用 `SafeDict.__missing__` 保留原占位符，不会 KeyError

---

## 3. count-coverage.py — 统计断言覆盖率

### 用途

自动统计 analysis.md 中所有元素和检查点，输出元素总数、需补充数、已覆盖数、覆盖率。可直接填到 analysis.md 顶部「断言覆盖统计」位置。

### 命令行

```bash
python scripts/count-coverage.py --analysis requirements-analysis.md
python scripts/count-coverage.py --analysis ... --output stats.json
python scripts/count-coverage.py --analysis ... --markdown   # 直接输出可粘贴的 md 表格
```

### 输出 schema

```json
{
  "elements": {
    "total": 25,
    "needs_supp_yes": 3,
    "needs_supp_no": 22
  },
  "checkpoints": {
    "total_checkpoints": 187,
    "needs_supplement_yes": 3,
    "needs_supplement_no": 142,
    "needs_supplement_dash": 42,
    "covered": 184,
    "coverage_rate": 0.984,
    "empty_required_content": 0,
    "empty_required_items": []
  }
}
```

> `empty_required_content`（空字段硬扫）：必填(是) 但「PRD/原型内容」列为空的检查点数，**应为 0**；> 0 即漏填，须填具体值或按断言化试金石标缺口（需补充=是）。`empty_required_items` 列出 `{元素ID}#{序号}`。

### 退出码

- `0` 统计完成
- `2` 脚本错误

### 元素编号识别规则

- 支持纯数字编号（`1`、`2`）
- 支持 1-3 字母前缀+数字（`A1`、`C16`、`BR01`、`US-01`）
- 元素标题格式：`#### {ID}. {名称}（归类：{类型}）｜需补充：是/否`
- 若标题不含 `｜需补充：` 字段（如纯业务规则 `BR01. 类目与租户关系规则`），默认按"需补充=否"统计（业务规则视为已覆盖）

### 失败时的兜底

LLM 手动按"需补充"列计数。注意"需补充=—"算覆盖（不适用），不算缺口。

---

## 4. cross-check.py — 第五步交叉检查（最重要）

### 用途

第五步核心。遍历 analysis.md 所有"需补充=否"的检查点，到 requirements.md 的 AC 表格里找匹配（用 Jaccard 相似度），输出未覆盖项清单。

### 命令行

```bash
python scripts/cross-check.py --analysis requirements-analysis.md --requirements requirements.md
python scripts/cross-check.py --analysis ... --requirements ... --output report.json
python scripts/cross-check.py --analysis ... --requirements ... --threshold 0.4
python scripts/cross-check.py --analysis ... --requirements ... --markdown   # 输出可粘贴到 analysis 第九节的 md 块
```

### 输出 schema

```json
{
  "total_checkpoints": 142,
  "covered": 138,
  "missing": 4,
  "pending_confirmation": 2,
  "edge_cases": 25,
  "coverage_rate": 0.972,
  "threshold": 0.3,
  "edge_threshold": 0.45,
  "missing_items": [
    {
      "element": "C01. 搜索筛选下拉框",
      "checkpoint": "搜索失败提示",
      "need_supplement": "否",
      "best_match_ac": "AC-15",
      "best_match_score": 0.18
    }
  ],
  "pending_items": [
    {
      "element": "W22. 商品头图上传",
      "checkpoint": "支持的文件类型",
      "need_supplement": "是",
      "best_match_ac": "AC-10",
      "best_match_score": 0.30,
      "reason": "待产品确认项需在 AC 中标记「⚠️ 待产品确认」"
    }
  ],
  "edge_items": [
    {
      "element": "C02. 搜索按钮",
      "checkpoint": "正常输入并回显",
      "need_supplement": "否",
      "best_match_ac": "AC-03-2",
      "best_match_score": 0.32
    }
  ],
  "ac_count": 67,
  "ac_with_sources_count": 50,
  "ac_without_source_count": 17,
  "ac_without_source": [
    { "id": "AC-01-05", "rule": "未登录显示「登录」按钮 ..." }
  ]
}
```

### 收集规则

cross-check 收集 analysis.md 中以下两类检查点：

| need_supplement | 处理方式 |
|----------------|---------|
| `否` | 用相似度匹配 AC，< 阈值算 missing |
| `是` | 检查最佳匹配 AC 是否含「待产品确认」字符串，没有则算 pending |
| `—` | 跳过（不适用，无需 AC 覆盖） |

### 反向告警：无来源 AC 列表（ac_without_source）

报告含 `ac_without_source_count` + `ac_without_source` 字段，列出所有"来源列为空 / 填了 `—`"的 AC。这些 AC 多半属于以下三类：

| 情形 | 处置 |
|------|------|
| 真属于纯技术规范（如网络异常 toast、URL 跳转格式等通用约束）| 保留 `—`，在 AC 行注释说明 |
| 实际能溯源到 analysis 检查点 | 补全来源列，填 `C{xx}#{n}` 或 `BR{xx}#{n}` |
| agent 凭经验生造（违反 anti-fabrication 规则）| 删除 AC，或补 analysis 检查点后再补来源 |

**作用**：cross-check 默认只检查"analysis → requirements"方向（防漏 AC）。`ac_without_source` 反向检查"requirements → analysis"方向，**抓 agent 偷懒批量填 `—` 的"假突破"**。

`--markdown` 输出时，仅在 `ac_without_source_count > 0` 时显示"10.4 ⚠️ 无来源 AC 待复核"段，列出每条 AC-ID + 规则摘要供人工复核。

### 退出码

- `0` 完全覆盖（或 analysis.md 不含 #### 元素标题，跳过 cross-check）
- `1` 存在 missing items 或 pending confirmation items（must-fix）
- `2` 脚本错误

### 阈值调整建议

- `--threshold 0.3`（默认）：宽松，只在显著不相关时报缺
- `--threshold 0.4`：严格，更倾向报缺，需 LLM 二次判断
- `--threshold 0.5`：非常严格，仅高度相关才算覆盖

### 边缘案例（edge_cases）

输出报告含 `edge_cases` 字段，统计相似度处于 `[threshold, threshold * 1.5]` 区间的项。这些被视为已覆盖但接近阈值，建议人工复核。

### 关于 jaccard + overlap 综合得分

脚本用 `max(jaccard, overlap)` 作为最终得分：
- jaccard：交集 / 并集，对长文本友好
- overlap：min(交集/A, 交集/B)，对短文本友好

中文 AC 描述通常较短，单一 jaccard 会让覆盖率失真。综合得分能让"AC 是检查点子集"的情形也被算覆盖。

### 失败时的兜底

LLM 必须**遍历每个元素的每个"需补充=否"检查点**到 requirements.md 找对应。**禁止抽样**——此前迭代验证过抽样会漏项。

### 跟同步检查清单的关系

cross-check.py 只覆盖**逐元素逐检查点**的对比。**全局一致性检查**（状态机/AC 文案一致、权限矩阵命名、用户故事对应、附录边界值）必须 LLM 手动做，详见 [cross-check-rubric.md](cross-check-rubric.md)。

---

## 5. validate-requirements.py — 结构合规性校验

### 用途

requirements.md 交付前的最后关卡：校验 17 项结构合规性（含 warn 级规则版本戳比对），避免 LLM "质量标准自检"漏项。

### 命令行

```bash
python scripts/validate-requirements.py requirements.md
python scripts/validate-requirements.py requirements.md --analysis requirements-analysis.md
python scripts/validate-requirements.py requirements.md --output validation.json
python scripts/validate-requirements.py requirements.md --analysis ... --markdown   # 输出可粘贴到 analysis 第三节 3.2 的 md 表格
```

### 校验项

1. 章节用途索引表格存在
2. 10 个章节齐全（一~十）
3. **状态机 YAML 字段齐全 + 状态闭包**（含 from/to/trigger/assertion；每个 from/to 引用的状态必须在某个 `states:` 列表中声明，避免引用未定义状态。`状态(注解)` 形式自动忽略括号注解再比对）
4. **AC 表格列齐全（认新旧两种格式）**：规则概念认双叫法（新模板「验收标准」/ 旧格式「规则」，任一命中）；结构列认新格式「类型」+「断言」或旧格式「正向/反向/边界」分列。正向/反向/边界属**覆盖度**（归 count-coverage/cross-check），本项只判**结构列齐全**。（修复历史 bug：模板列名从「规则」改为「验收标准」后，旧校验器死抠「规则」导致新产物稳定误报「缺失列: 规则」）
5. AC 来源列必填（每条 AC 必须填写指向 analysis 的检查点编号）
6. **AC 编号格式 + 唯一性**（AC-NN-NN 或 AC-NN-NNa，禁止多层后缀；同一编号在 AC 表格行首列出现 ≥ 2 次视为重复，多见于复制行漏改 ID）
7. AC 断言列完整性（每条 AC 的"断言"列必须有具体内容，长度 ≥ 5 字，禁止 `—`/`待补充`/`TODO` 等占位符）
8. **AC "待产品确认" vs 来源列一致性**（AC 文本若含"待产品确认/暂不测试"等关键词，来源列**可为 `—`/空，也可填指向 analysis 检查点的合法 ID**（如 C01#1，提供溯源，与 cross-check 精确来源匹配口径一致）；仅当来源列既非 `—`/空、又不含任何合法检查点 ID 的纯垃圾文本时才判不合规）
9. 接口契约含错误码枚举（标记为"不测试"则跳过）
10. 不允许出现 "TBD"/"待确认"（豁免"⚠️ 待产品确认"）
11. （可选，需 `--analysis`）analysis 与 requirements 同步：analysis 中"需补充=否"的检查点必须在 requirements.md AC 来源列引用至少一次
12. （可选，需 `--analysis`）**PRD 缺陷修正追踪一致性**：analysis 必须含「## 测试驱动的 PRD 缺陷修正统计」章节 + 哨兵 `<!-- PRD_DEFECT_TOTAL: N -->`，且哨兵 N = 统计表最后一行"累计"列、统计表行数 ≥ 变更日志行数。触发场景=PRD 增量更新（Step 3.5）；老 analysis 缺段按 operational-rules §7「老 analysis 升级路径」补建；哨兵全文件唯一（防漏 str_replace 留双标记）。
13. （可选，需 `--analysis`）**临时文件残留检查**：analysis 同目录不得残留 `_tmp_*` / `*.bak` / `*.pyc`（阶段一收尾即清，跑 cleanup-temp.py --apply）。
14. **AC 验收标准列非空**（空字段硬扫，硬 fail）：每条 AC 的「验收标准」列不得为空 / —。
15. **AC 断言具体性（断言化试金石，warn 级）**：AC 断言列若只有模糊词（正确/正常/符合预期/友好/合理/清晰…）且无任何具体锚点（引号文案/数字/路由/枚举/布尔/可见性等）→ WARN，应改具体值或回 analysis 标缺口。**warn 级不翻 verdict、不影响退出码**，只在 markdown/stderr 提示复核（防"提示正确"这类填不出 `toBe()` 的断言混过）。
16. （可选，需 `--analysis`）**第五章 PRD 位置非自指章节号（warn 级）**：analysis「五、待确认事项汇总」的「PRD 位置」列禁填本文档章节号（一~十），应填 PRD 功能点/章节号。
17. **规则版本一致性（warn 级，P2-2）**：读取产物顶部 `<!-- RULESET_VERSION: X -->` 戳，与脚本 `CURRENT_RULESET_VERSION` 比对；缺失或不一致 → WARN，提示"规则已升级，建议重生成受影响章节"。升级规则集时三处同步：本脚本常量 + 两个 `.tpl` 模板顶部戳。

### 输出 schema

```json
{
  "file": "requirements.md",
  "total_checks": 11,
  "passed": 10,
  "failed": 1,
  "verdict": "FAIL",
  "checks": [
    { "name": "章节用途索引表格", "passed": true, "detail": "找到「章节用途索引」表格" },
    { "name": "状态机 YAML 字段齐全 + 状态闭包", "passed": false, "detail": "YAML 块 2: from/to 引用了未在 states 中声明的状态 ['未审核']" }
  ]
}
```

### 退出码

- `0` 全部通过
- `1` 存在校验错误（must-fix）
- `2` 脚本错误

### 失败时的兜底

LLM 手工对照 [output-format-cheatsheet.md](output-format-cheatsheet.md) 的格式要求逐一核对。重点关注：
- **状态机 YAML**：每个 `from:` / `to:` 引用必须在 `states:` 列表中能找到（注解形式 `状态(子上下文)` 自动放过）
- **AC 编号唯一性**：同一编号不能在表格行首列出现两次（agent 复制 AC 行漏改 ID 的典型 bug）
- **AC 断言列**：必须给可执行步骤（≥ 5 字），不能用 `—`/空 等占位符
- **待产品确认一致性**：AC 文本含"待产品确认"关键词时，来源列可为 `—`，也可填指向 analysis 检查点的合法 ID（如 C01#1，溯源用，与 cross-check 一致）；只有填了既非 `—` 又不含合法 ID 的纯垃圾文本才算不合规

---

## 6. cleanup-temp.py — 第六步清理临时文件

### 用途

第六步执行：删除调试脚本、中间产物、备份文件等。默认 dry-run，加 `--apply` 才删。

### 命令行

```bash
python scripts/cleanup-temp.py --dir ./specs/my-feature/                  # dry-run
python scripts/cleanup-temp.py --dir ./specs/my-feature/ --apply          # 真删
python scripts/cleanup-temp.py --dir . --pattern "scratch-*,*.tmp" --apply
```

### 默认匹配规则

```
debug-*.py / debug-*.js / debug-*.ts
scratch-*.* / temp-*.* / tmp-*.*
*.bak / .DS_Store / Thumbs.db
test-output-* / temp-output-*
scratch.md / scratch.txt
_*.py / _*.js / _*.ts / _tmp_*
cross-check-report.json / count-coverage-report.json / validate-report.json / *-report.json
```

> **保护（不删）**：`elements.json` / `elements-scan.json` / `*-scan.json`（extract-elements 扫描产物）属可溯源交付辅料，已从默认删除清单移除（P1-2）。如确需删除，显式传 `--pattern "*-scan.json"`。

### 保护目录（永远跳过）

`.git`, `node_modules`, `.kiro`, `dist`, `build`

### 退出码

- `0` 完成（dry-run 或 apply 都返回 0）
- `2` 脚本错误

### 失败时的兜底

LLM 用 `Get-ChildItem` (Windows) 或 `find` (Unix) 手工列出临时文件，逐个评估后删除。

---

## 集成到 7 步流程

| 步骤 | 调用脚本 | 替代方案 |
|------|---------|---------|
| 第一步 PRD 自检 | `extract-elements.py`（侦察元素） | LLM 手动扫描 |
| 第二步 缺陷发现 | — | LLM 推理 |
| 第三步 生成 requirements.md | `generate-skeleton.py`（先建模板） | LLM 直接写 |
| 第四步 自迭代修复 | — | LLM 改文档 |
| **第五步 交叉检查** | **`cross-check.py`（核心）** + `count-coverage.py`（统计） | LLM 手工对比（高漏检风险） |
| 第六步 清理临时文件 | `cleanup-temp.py` | 手动删 |
| 第七步 输出消费指南 | — | LLM 写文档 |
| 交付前 | `validate-requirements.py`（最后关卡） | LLM 自检（高漏项风险） |

---

## 推荐执行序列

```bash
# 第一步：侦察元素
python scripts/extract-elements.py --src ./prototype/ --output elements.json

# 第三步前置：生成空模板
python scripts/generate-skeleton.py --output-dir ./specs/my-feature/ --feature "购物车"

# (LLM 填充 PRD 自检结论、断言覆盖、AC、状态机...)

# 自检辅助：统计覆盖率
python scripts/count-coverage.py --analysis ./specs/my-feature/requirements-analysis.md --markdown

# 第五步：交叉检查
python scripts/cross-check.py \
  --analysis ./specs/my-feature/requirements-analysis.md \
  --requirements ./specs/my-feature/requirements.md \
  --output ./specs/my-feature/cross-check-report.json

# (LLM 根据报告补 AC)

# 交付前：结构校验
python scripts/validate-requirements.py ./specs/my-feature/requirements.md

# 第六步：清理
python scripts/cleanup-temp.py --dir ./specs/my-feature/ --apply
```

---

## 维护说明

- **Python 版本：3.7+ 即可跑**。脚本虽用了 `list[dict]` 这类内建泛型注解（PEP 585，运行时求值需 3.9+），但每个脚本首行都加了 `from __future__ import annotations`，注解变惰性字符串、不在运行时求值，因此 3.7+ 均可运行。**新增脚本时务必照抄这行 future import**，否则低版本 Python 会 `TypeError`/语法报错。
  - 推荐仍用 3.11+（更快、错误信息更好），但**不强制、不自动升级**——future import 已从根上消除版本约束。
- 不依赖任何 pip 包
- 修改脚本后，建议用 `requirements-analyzer` 自身做 fixture 跑一遍验证
- 新增脚本请在本文档「脚本索引」表格补充

---

## 脚本输出落盘到 analysis 的强制规则

> 此节回应 [operational-rules.md#7-脚本优先原则](operational-rules.md#7-脚本优先原则) 中的"脚本输出必须以表格形式纳入 analysis 对应章节"。

每个必跑脚本的输出有明确的"应该落到 analysis 哪一节"，不能只在终端展示后丢弃。

| 脚本 | 关键输出字段 | 应落到 analysis 的位置 | 落盘格式 |
|------|------------|----------------------|---------|
| `extract-elements.py` | `total_elements`、`by_component`、`by_file`、`elements[]` | 二、断言覆盖详情 → 「侦察元素清单」子节 | 见下方"对接规范" |
| `count-coverage.py` | `elements.total`、`checkpoints.total_checkpoints`、`coverage_rate` | 八、断言覆盖统计（独立章节）| 4 列表格：指标 / 数值 / 占比 / 备注 |
| `cross-check.py` | `total_checkpoints`、`covered_by_exact_source`、`covered_by_fuzzy_match`、`missing`、`missing_items[]` | 九、交叉检查结果 | 三个子节：①执行过程 ②本轮新增/修正的 AC 项 ③最终结果统计表 |
| `validate-requirements.py` | `total_checks`、`passed`、`failed`、`checks[]` | 三、各章节诊断（每条 check 对应一行）| 表格：章节 / 状态（✅/❌）/ 说明（脚本 detail 字段） |

### extract-elements 输出对接 analysis 第二节的具体规范

跑完 `extract-elements.py --output elements-scan.json` 后，必须把脚本输出按以下结构整合到 analysis 第二节"侦察元素清单"：

```markdown
### 侦察元素清单

> 通过 extract-elements.py 4 层扫描（{layers}）+ 路径过滤（{include}）扫描原型代码（{src}）。
> 扫描结果：{files_with_components} 个文件 / {total_elements} 个代码元素，业务级聚合后等价于本节列出的 N 个 PRD 元素。

**按文件分组的代码元素清单（来自脚本扫描）：**

| 文件 | 代码元素数 | 主要组件类型 |
|------|---------|------------|
| pages/Home.tsx | 35 | native:button × 4, custom:BannerSection 等 |
| components/Navbar.tsx | 11 | Link × 4, native:button × 6 |
| ... | ... | ... |

**按业务模块归类（手工聚合）：**

> 把脚本扫到的 {total_elements} 个代码元素聚合为业务级 PRD 元素。每个 PRD 元素对应原型中的若干代码元素。

**模块 A：全局布局（Navbar.tsx + Footer.tsx）**
- A1. Logo 点击回首页（对应代码元素：Link@Navbar.tsx:70）
- A2. 导航菜单项（对应代码元素：Link×4 @Navbar.tsx:120-186）
- ...

**模块 B：Banner 区域（Home.tsx - BannerSection）**
- B1. Banner 横向滚动容器
- ...
```

**关键约束：**
- 必须列"按文件分组"表格（数据来自 `by_file`）
- 必须列"按业务模块归类"清单（手工聚合，但每条要标注对应的代码元素位置）
- 脚本扫到但 PRD 显式排除的文件（如本次的 TeacherModules.tsx 子模块）必须在末尾"排除文件说明"中列出，避免下游误以为漏侦察

**反模式：**
- ❌ 只写"扫到 N 个文件 M 个元素"一句话，不列具体清单（脚本输出被丢弃）
- ❌ 只用脚本数据填业务模块归类，不做"代码元素 → PRD 元素"的聚合（粒度错位）
- ❌ 脚本扫到的文件没全部出现在表格里（可能漏侦察）

**禁止做法：**

- ❌ 只在终端打印 JSON 后说"已检查"，不写入 analysis
- ❌ 把脚本数字与 LLM 估算的数字混用（如脚本说 280，LLM 写"约 280"）
- ❌ cross-check 结果只写"覆盖率 100%"一行，不列具体数字和遗漏明细

**正确做法**：脚本跑完后，把 stderr 里的 Summary 表 + missing_items 列表完整粘到 analysis 对应章节，再把人工补充的解释（如"误报原因"）作为附注。

---

## 7. smoke-test.py — 端到端冒烟测试

### 用途

按 7 步流程顺序调用 6 个核心脚本（extract-elements / count-coverage / cross-check / validate-requirements / cleanup-temp 等），验证 skill 全链路可在指定 fixture 上跑通且全绿。

### 命令行

```bash
python scripts/smoke-test.py --fixture-dir ./knowledge/U校园/U5首页/
python scripts/smoke-test.py --fixture-dir ... --prototype-dir ./prototype/
python scripts/smoke-test.py --fixture-dir ... --skip extract-elements,cleanup-temp
python scripts/smoke-test.py --fixture-dir ... --no-check-landing  # 跳过 R9 落盘验证
```

### fixture 要求

`--fixture-dir` 指定的目录必须包含：
- `requirements-analysis.md`（阶段一产出）
- `requirements.md`（阶段二产出，含来源列）

### 默认执行步骤

1. `count-coverage.py`（统计 analysis 覆盖率）
2. `cross-check.py`（交叉检查，必须 exit_code=0）
3. `validate-requirements.py`（结构合规性 17 项检查）
4. **R9 落盘验证（默认开启）**：grep analysis 是否含 cross-check 第九节关键字段（"九、交叉检查结果"/"覆盖率"/"检查点总数"）
5. **R9 落盘验证（默认开启）**：grep analysis 是否含 validate 第三节 3.2 关键字段（"3.2"/"validate-requirements"/"AC 编号"）
6. `cleanup-temp.py`（dry-run，不实际删除）

可选步骤（默认跳过，需显式 `--prototype-dir` 启用）：
- `extract-elements.py`（需要原型代码目录）

可选关闭：
- `--no-check-landing` 跳过步骤 4-5（不推荐，落盘验证是 L-14 / R9 反模式的根治措施）

### 输出 schema

stderr 输出每步的执行命令、exit_code、stderr 摘要，最后输出汇总：

```
端到端冒烟测试结果：3/3 通过

或：

端到端冒烟测试结果：2/3 通过
失败步骤：
  ❌ validate-requirements.py（结构合规性） (exit=1)
```

### 退出码

- `0` 全链路通过
- `1` 存在失败步骤
- `2` 脚本错误（fixtures 不存在等）

### 何时跑

- skill 任意脚本/规则修改后，回归验证现有 fixture 不退化
- 新增 fixture 时，验证 skill 能正确处理新 fixture
- CI/CD 集成（如有）

### 失败时的兜底

逐步运行各个脚本（按 smoke-test 输出的失败步骤），单独定位问题。如果是 fixture 数据问题（如状态机缺 assertion 字段），修复 fixture；如果是脚本问题，修复脚本。

---

## Windows 运行注意

在 Windows / PowerShell 下跑本目录脚本，注意三点（踩过的坑）：

1. **用 `python` 而不是 `python3`**：Windows 上 `python3` 常是微软商店的占位别名（App Execution Alias），运行直接 exit 9009 什么都不干。确认用真 Python：`python --version`（本 skill 脚本已加 `from __future__ import annotations`，3.7+ 即可跑；推荐 3.11+）。
2. **强制 UTF-8 双端**：跑脚本前设 `$env:PYTHONIOENCODING="utf-8"` 且 `[Console]::OutputEncoding=[Text.Encoding]::UTF8`，否则中文输出在 GBK 控制台乱码（脚本内已做 stdout/stderr UTF-8 兜底，但输入侧仍建议设）。
3. **含中括号的路径用 `-LiteralPath`**：输出目录名形如 `<title>[<id>]`，PowerShell 的 `Test-Path`/`Get-ChildItem` 会把 `[...]` 当通配符，必须加 `-LiteralPath` 才能正确命中。

示例：
```powershell
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding=[Text.Encoding]::UTF8
python count-coverage.py --analysis "ai-test-workspace/docs-bucket/<title>[<id>]/requirements-analysis.md" --markdown
```
