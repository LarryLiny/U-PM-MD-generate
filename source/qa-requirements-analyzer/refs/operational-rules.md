# 执行规则集（operational rules）

> 本文件集中存放 SKILL.md 入口因长度限制无法承载的强制规则。
> SKILL.md 只保留对本文件的链接和一句话摘要，详细规则全部在这里。
> **本文件经过精简（11 条 → 7 条），消除了规则间的隐性矛盾。**

## 规则间优先级（冲突时遵循）

当多条规则同时适用且行为冲突时，按以下优先级决定：

1. **数据完整性 > 流程美感**：缺数字宁可标 ⏳ 占位，不要凭记忆填
2. **脚本结果 > 人工估算**：脚本说 missing=N 就是 N，不能"误报忽略"
3. **续写正确性 > 响应连续性**：上下文中断时，先校验后续写，不抢速度
4. **用户体验 > agent 偷懒**：分段写文档要持续推进，不要 understood 后停
5. **真实场景 > 演练取巧**：禁止 Copy-Item 等旁路绕过 fs_write 规则

---

## 1. 阶段交付前清单（强制）

### 1.1 阶段一交付清单

在输出"阶段一完成"或将 analysis 交给用户前，必须逐项确认：

- [ ] 第零步：**已查项目测试知识库 `ai-test-workspace/rag-bucket/`**——命中本期模块的历史沉淀已转化为额外自检维度（未覆盖项进 D-xx/待确认）、前置条件（进对应 AC）、多文档一致性核对输入；**或**已确认"项目首个需求/无此库/无相关沉淀"并在 analysis 里记一句。（详见 prd-quality-checklist 第零步）
- [ ] 🔴 第一步补充：**沿用/依赖锚点已机械扫描并按风险分流**（防漏读被沿用需求，详见 prd-quality-checklist「第一步补充（二）」）——PRD 里「沿用/复用/不改/本期不做/已在 X 交付/见《Y》/关联知识库/与 X 解耦/同 X 一致」等锚点已逐个列成「被依赖文档清单」；其中本需求**前提/用例前置所依赖的能力**（编辑/状态/权限/前置态）已**去读被引用文档核对其边界**是否反向卡住本需求，命中记 D-xx；**沿用既有逻辑本 PRD 未写不算本需求缺陷、不要求本需求产品补**（等待方优先=QA 自核 / 能力所属需求）；纯数据/展示规格沿用只标"归属方、本需求不测"。清单为空则记一句"无沿用/依赖锚点"。
- [ ] 第一步：**`extract-elements.py` 已执行**（如有原型代码），输出已纳入"侦察元素清单"章节（含按文件分组表格 + 业务级聚合清单）
- [ ] 第一步：12 项 PRD 自检清单已逐项标注 ✅/❌
- [ ] 第一步：所有元素 + 业务规则的检查点表格已逐项展开（不可合并行）
- [ ] 第一步：**元素编号速查表**已输出（位于 analysis "二、断言覆盖详情" 章节开头）
- [ ] 第一步：**`count-coverage.py` 已执行**，统计数字（元素总数、检查点总数、需补充数）已纳入"断言覆盖统计"章节，**且覆盖率 = 100%**（如 < 100% 必须查解析异常具体位置并修复）
- [ ] 🔴 **全量门禁（硬性，不可绕过）**：速查表元素数 **必须等于**「元素归类与检查点」明细表数量，且 `count-coverage.py` 输出的「速查表一致性 = ✓ 一致」。**任一不满足即判阶段一未完成、禁止交付**——严禁只展开"代表性"几个元素（违反 assertion-coverage「不可只列代表性几条」）。体量大时分批全量展开，不得缩小范围；如需缩范围必须先与用户确认。
- [ ] 🔴 **元素完整性（硬性）**：`count-coverage.py` 的「元素完整性」检查必须无告警——① 每个元素的检查点编号 **1..N 连续无断档**（不可像 `1-5,9` 那样跳号）；② 头部「需补充：是/否、待补充：#x」与表格行**自洽**（说"是"必须真有"需补充=是"行；"待补充 #x"那行必须确为"是"）。
- [ ] 🔴 **类型必填覆盖（硬性，标准 B）**：`count-coverage.py` 的「类型必填覆盖」检查必须无告警——每个元素必须展开其归类类型的**全部「必填(是)」检查点**；非必填检查点可在不适用时省略（见 assertion-coverage-checklist「检查点展开标准」）。
- [ ] 🔴 **断言化试金石（硬性）**：必填检查点「PRD/原型内容」无空缺（`count-coverage.py` 的 `empty_required_content = 0`）；只给模糊词（"正常/正确/符合预期"）而无具体值的必填点，已按试金石判为缺口（需补充=是 / D-xx），不许用模糊词蒙混。
- [ ] 第二步：缺陷汇总（D-xx）已输出，每条标注影响（用例/接口/脚本）和状态
- [ ] 待确认事项汇总已列出
- [ ] **临时文件已清理**：阶段一用"临时文件中转法"（5.3.1）产生的中转文件（如 `_tmp_elements.md`、`_tmp_replace.py`、`_tmp_*.md/.py`）必须在交付前删除。**统一跑 `cleanup-temp.py --dir <输出目录> --apply` 清理并复查输出目录，禁止仅靠手动逐个删**——手删极易漏掉 sidecar（如 `extract-elements.py` 在 `--output` 旁额外生成的 `_tmp_*-scan.json`）。清理后输出目录应**只剩交付物**（`requirements-analysis.md` / 阶段二的 `requirements.md` / xlsx 等）。**不要等到阶段二第六步**——阶段一结束即清。
- [ ] **目录树预览**：在交付前必须输出 analysis 的 H2/H3 标题列表 + 每节行数分布
- [ ] **提示通知产品**：`requirements-analysis.md` 每次产出**或更新后**，主动提示用户可触发「通知产品补 PRD」（由 repo-conductor 的 `notify-prd` 剧本发飞书，收件人 = **全员**：repo.roles 全角色 + developers）。不要等用户问；本 skill 不直接发卡片，只负责提示。
- [ ] **token 埋点**：开工已打 `_baseline`（脚本调用计划 Step 0）、`analyze` 由 count-coverage(阶段一) 跑完自动打点（agent 不用手打）、交付前已 `qa-token-flush`（fail-silent，报错忽略；但**漏打则本次运行 token 统计永久丢失、无法事后补**，见 L-22）

### 1.2 阶段二交付清单

在输出"阶段二完成"之前，必须逐项确认以下步骤已执行：

- [ ] 第三步：**`generate-skeleton.py` 已执行**生成空骨架（不可直接 fs_write 整段写）
- [ ] 第三步：requirements.md 10 章结构已生成
- [ ] 第三步：每条 AC 都填写了"来源"列（指向 analysis 检查点编号 `C{xx}#{n}`），无来源的必须填 `—` 并说明原因
- [ ] 第四步：自迭代修复已执行（**`count-coverage.py` 已执行**统计覆盖率）+ 数据已落盘到 analysis 第八节
- [ ] 第五步：**必须执行 `cross-check.py` 脚本**，且 `missing == 0 && pending_confirmation == 0`（exit_code=0）才视为通过
- [ ] 第五步：脚本 missing 项必须循环修复至清零（参考第 3 节）
- [ ] 第五步：**cross-check 报告已落盘到 analysis 第九节"交叉检查结果"**（含执行过程、新增 AC 项、最终结果统计）
- [ ] 第六步：**`cleanup-temp.py` 已执行**清理临时文件
- [ ] 第七步：消费指南已输出
- [ ] 交付前关卡：**`validate-requirements.py` 已执行**且 exit_code=0
- [ ] 交付前关卡：**validate check 14（AC 验收标准列非空）PASS；check 15（断言具体性）无 WARN**——有 WARN 必须逐条把模糊断言改成具体值或就地标待确认，不允许带 WARN 交付
- [ ] 交付前关卡：**AC 断言为界面可观测现象 + 用户感知语**（无脚本守门，人工核）——无白盒量（取值口径/内部 ID/路由参数/后端字段/是否调接口，应入第七章接口契约，接口 N/A 则不写进功能 AC）、无字段码值当主语（码值进括号/来源列）、PRD 精确文案字面照搬不翻译。详见 [assertion-coverage-checklist.md](assertion-coverage-checklist.md)「白盒越界识别 / 实现术语泄漏」
- [ ] 交付前关卡：**validate 的 11 项 check 详情已落盘到 analysis 第三节 3.2**（每项 name + detail）
- [ ] **token 埋点**：阶段二 generate 子阶段（`generate/read`、`generate/fill`、`generate/verify`）**由门禁脚本（generate-skeleton→read / count-coverage 阶段二→fill / validate→verify；cross-check 不单独打）跑完自动打点，agent 不用手打**（见 `lib/token-metering.md` §2.5 + `scripts/_token_phase.py`）；agent 只需确保交付前 `qa-token-flush` 兜底补推（fail-silent；漏打不可事后补，见 L-22）

**禁止**在上述任何一项未完成时输出"阶段完成"或类似结束语。

**关键原则**：脚本跑通（exit_code=0）≠ 任务完成。**脚本输出必须完整落盘到 analysis 对应章节**才算"真正消费"。

**自动化验证方式（推荐）**：跑 `smoke-test.py --fixture-dir <目录>`，默认开启 R9 落盘验证（步骤 4-5），自动 grep analysis 含 cross-check / validate 报告关键字段，缺失即 FAIL。

**手工 fallback**：若不跑 smoke-test，必须用 grep_search 确认 analysis 含对应章节内容，不能只看终端摘要。

**便捷工具**：
- `cross-check.py --markdown` 直接输出可粘贴到 analysis 第九节的 md 块（执行过程 + 新增 AC 项 + 最终结果统计三段式）
- `validate-requirements.py --markdown` 直接输出可粘贴到 analysis 第三节 3.2 的 md 表格（各项 check 章节/状态/说明；带 `--analysis` 时含 11~13 项）

---

### 1.3 PRD 增量更新交付清单（强制，仅 PRD 版本变更场景）

仅当本次属于 PRD 版本变更场景（触发信号见第 7 节）时执行。逐项确认：

- [ ] 已对比新旧 PRD diff，输出「变更点 → 影响范围」清单
- [ ] analysis 顶部「PRD 版本」字段已更新（如 V1 → V1.1）
- [ ] analysis「变更日志」表已追加一行（旧记录不删）
- [ ] **Step 3.5**：本次被新 PRD 解决的「待补充/待确认」点已盘点（计数规则见第 7 节「测试驱动的 PRD 缺陷修正计数」）
- [ ] 「测试驱动的 PRD 缺陷修正统计」表已追加一行（首次分析填 0）
- [ ] 哨兵 `<!-- PRD_DEFECT_TOTAL: N -->` 已 str_replace 改值（N = 最新累计，全文件唯一）
- [ ] 受影响章节的 analysis 检查点已局部更新（C/BR 元素归位 / D-xx 状态翻 ✅ 等）
- [ ] 受影响 AC 的 requirements.md 已同步（来源列、断言列、待产品确认状态）
- [ ] 本轮新增/改动的 AC 已过**最小可断言关**（验收标准+断言非空、断言能落具体值；见 §1.4）
- [ ] `validate-requirements.py --analysis` 跑过且 exit_code=0（**必含第 12 项「PRD 缺陷修正追踪一致性」PASS**）
- [ ] `cross-check.py` 跑过且 missing+pending=0；`count-coverage.py` 覆盖率 / 速查表一致

**禁止**：
- ❌ 收到"PRD 改了"就重做全文（违反第 7 节"全量重做合法场景"）
- ❌ 跳过 Step 3.5、靠三套脚本 PASS 误判流程完成（**脚本 PASS ≠ 流程完成**，见 anti-fabrication「脚本 PASS 误当流程完整」/ L-18）
- ❌ 模板已预置统计段但还没补到老 analysis（必须先按第 7 节「老 analysis 升级路径」补建再跑增量）

---

### 1.4 最小可断言关（强制·所有路径不可跳）

> 解决"本该分析阶段抓到的模糊点拖到脚本阶段才暴露"。把测试阶段的断言试金石前移、固化成关卡。

**无论走哪条路径**——全量分析 / PRD 增量局部改 / "一次性全跑" / 小需求快速通道——**每条新建或改动的 AC 至少过两关**：

1. **非空关（硬 fail）**：AC 的「验收标准」列 + 「断言」列都非空（不得为空 / —）。脚本：`validate-requirements.py` check 14（验收标准）+ check 7（断言）。
2. **可断言关（试金石）**：AC 断言能写成 `expect(具体可观测).toBe(具体值)`——含引号文案 / 数字 / 路由 / 枚举 / 布尔 / 可见性等具体锚点；**只有模糊词（正常/正确/符合预期…）= 不达标**，必须改具体值或就地标缺口。脚本：`validate-requirements.py` check 15（warn 级，提示复核）。

> 这道关**不随"小需求/快速通道"豁免**。小改也可能引入模糊 AC，恰恰是漏检高发区。
> 注：跨 skill 的 orchestrator fast-task 通道若也产出 AC，应内嵌同一道关（另案 TODO，本 skill 内先覆盖全部路径）。

---

## 2. AC 来源对应原则（强制）

- 生成每条 AC 时，必须先在 analysis 中找到至少一个对应的检查点编号填入"来源"列
- 找不到对应检查点的（说明是 agent 自行总结的衍生 AC），必须**回到 analysis 中补充该检查点**（作为新发现的元素或业务规则），然后在 AC 来源列填上新增编号
- 仅在以下情况允许"来源 = —"：纯技术规范类 AC（如"网络异常时显示 toast"这类通用约束），且必须在 AC 行后注释说明原因
- 严禁为了"凑齐 AC"而批量填 `—` 跳过对应工作

---

## 3. 交叉检查循环修复机制（强制）

第五步交叉检查不是"跑一次就完事"，必须**循环执行直到通过**：

```
loop:
    1. 运行 cross-check.py
    2. 读取 exit_code 和 missing_items / pending_items
    3. 如果 exit_code == 0：跳出循环，进入第六步
    4. 如果 exit_code != 0：
       a. 对每个 missing_item：判断属于哪种情况
          - 真遗漏 → 在 requirements.md 补对应 AC + 来源列
          - 来源映射缺失 → 在已存在的 AC 上补"来源"列指向该检查点
          - analysis 检查点本身有问题（如重复、归类错误）→ 修正 analysis
       b. 对每个 pending_item：在对应 AC 中加上"⚠️ 待产品确认"标记
       c. 修复完成后回到步骤 1，重新跑脚本
    5. 循环上限：5 次。超过 5 次仍不通过，必须停止并向用户报告具体卡点
```

**循环过程透明化**：每轮循环后必须向用户汇报 `第 N 轮：missing X→Y, pending A→B`，不能静默循环。

**禁止**："反正 missing 都是误报"或"差几条无所谓"等理由跳出循环。脚本结果是硬标准。

---

## 4. 待确认事项主动汇报规则（强制）

**触发条件**（满足任一即触发）：
1. 用户对待确认事项做出决策（确认/修改/驳回）
2. 任何涉及 analysis 的回复（无论用户问什么），只要 analysis 中存在状态为 ⏳ 或 ⚠️ 待产品确认 的项

**触发时 agent 必须在回复末尾附带以下格式的状态摘要**：

```
📋 待确认事项进度：已处理 X/Y，剩余 Z 项待确认：
- #N: {事项简述}
- #M: {事项简述}
```

- 全部处理完毕时输出：`✅ 待确认事项已全部处理（Y/Y），可启动阶段二。`
- 只要还有剩余未处理项，**禁止**省略此摘要，**禁止**只说"已更新"就结束回复
- **主动汇报原则**：用户没问也要主动报，不能等用户发现"还有几项没处理"才补

---

## 5. 执行流程与中断恢复（强制）

> 此节合并了原"上下文恢复机制"+"分段写文档反模式"+"启动前脚本调用计划"。
> 三者本质都是"中断/恢复/续写"问题，统一处理。

### 5.1 启动前必须输出"脚本调用计划"清单

agent 在阶段一/阶段二的第一条响应中**必须**输出（用户不需要确认就开始执行）：

```markdown
📋 阶段{一/二}脚本调用计划（按时序）：

0. ⏳ Step 0: cantor qa-token-mark --skill qa-requirements-analyzer --phase _baseline --action start --feature "<需求名>"（开工打基线，token 埋点，fail-silent）
1. ⏳ Step A: {脚本名}.py — {用途}
2. ⏳ Step B: {脚本名}.py — {用途}
3. ⏳ Step C: 填充各章节（顺序：xxx）
4. ⏳ Step D: {脚本名}.py — {用途}
5. ⏳ Step E: 阶段交付前清单核对 +（`analyze` 由 count-coverage 阶段一自动打点、阶段二 generate 子阶段同样由门禁脚本自动打点，均无需手打）+ 收尾 cantor qa-token-flush
```

每完成一步就改 ⏳ 为 ✅，让用户看到进度。

> 🔴 **token 埋点 Step 0 不可省**（详见 `_lib/token-metering.md` 强制铁律 + L-22）：`_baseline` 是计划第一步、与必跑脚本并列；阶段一 `analyze` 由 count-coverage(阶段一) 跑完自动打点（agent 不用手打）；**阶段二 generate 子阶段（read/fill/verify）同样由门禁脚本自动打点、agent 不用手打**；交付前 `qa-token-flush` 兜底补推。fail-silent，报错忽略不阻断，但 `_baseline` / `flush` **不能不打**（`analyze` 由脚本自动打点兜底）——漏打 `_baseline`/`flush` 则该次运行的 token 明细永久丢失、无法事后补。

### 5.2 阶段一脚本调用时序

```
Step A0: 查测试 rag（ai-test-workspace/rag-bucket/）→ 命中条目转化为自检维度/前置/D-xx；无库/首个需求则跳过（见 prd-quality-checklist 第零步）
   ↓
Step A: extract-elements.py     → analysis 第二节「侦察元素清单」
   ↓
Step B: generate-skeleton.py --target analysis → 只建 analysis 空骨架（requirements.md 留到阶段二建；阶段一不触发 generate/read）
   ↓ (read_file 一遍骨架确认章节顺序)
Step C: str_replace + fs_append → 渐进式填充各章节
   ↓
Step D: count-coverage.py       → 回填 ⏳ 占位
   ↓
Step D2: 清理阶段一临时文件      → 删除中转法产生的 _tmp_*.md / _tmp_*.py
   ↓
Step E: 阶段一交付前清单核对（见第 1.1 节）
```

**Step D2 必做**：阶段一若用了"临时文件中转法"（5.3.1）填充元素大段，中转文件（`_tmp_elements.md`、`_tmp_replace.py` 等）在锚点替换完成后即失效。**阶段一收尾就要清掉，不要拖到阶段二第六步**——否则会把临时产物留在输出目录里污染交付。删除方式：`delete_file` 逐个删，或 `cleanup-temp.py --dir <输出目录> --pattern "_tmp_*" --apply`。

**Step A 失败兜底**：扫描结果不充分（如本场景）→ 必须在 analysis 第二节明确说明"`extract-elements.py` 因 XXX 改为手工侦察"。

**Step A 补充：原型展示文案扫描（必跑，仅当原型代码可访问时）**

`extract-elements.py` 只扫交互元素（button/Link/onClick 等），不扫展示型文本节点。跑完脚本后必须额外通读关键 tsx 文件，提取**功能性展示要素**：

```
扫描对象：
- 容器组件（书架/弹窗/列表/卡片的根 tsx）
- 空状态/错误态条件渲染段（如 `{xxx.length === 0 ? ... : ...}`）

提取目标：
- 中文字符串字面量（如 '共 N 本教程'、'所有教程已领取完毕'）
- 由 props/state 拼接的动态文案（如 `共 {n} 本教程`）
- 状态映射文案（如 STATUS_META 的 label 字段）

分流处理（详见 anti-fabrication-rules.md 第 14 条）：
1. 视觉规范（颜色/字号/间距）→ 默认跳过（除非 PRD 明确定义）
2. 文案/状态/动态数据 → 按优先级归位：
   a. 优先挂到现有 C/BR 元素的某条检查点的"PRD/原型内容"列
   b. 关联不上才新增 BR 到"未归类业务规则"段
```

**Step A 必跑产物**（在 analysis 第二节侦察清单后追加一段）：

```markdown
**原型展示要素补充扫描**（来自通读 tsx 文件）：

| 展示要素 | 来源文件 | 归位 |
|---------|---------|------|
| 「共 N 本教程」总数展示 | Bookshelf.tsx:70/169 | C14#1 + C17#1 |
| 「所有教程已领取完毕」空状态 | ClaimBooksModal.tsx:107 | C21#2 |
| 颜色规范（绿/蓝/红标签）| Bookshelf.tsx:24-29 STATUS_META | 跳过（视觉规范，PRD 未定义） |
```

**Step B 关键约束**：
- ✅ 必须：跑完后 read_file 一遍骨架，确认章节顺序
- ✅ 必须：用 str_replace 替换 `{占位符}`，用 fs_append 补章节
- ✅ **阶段二重做时**：必须用 `--target=requirements`，避免覆盖已有 analysis（analysis 是阶段二的输入源）
- ❌ 禁止：fs_write 整段覆盖骨架（骨架白跑）
- ❌ 禁止：用 `Copy-Item` / `cp` / `Move-Item` 等命令复制其他文件覆盖骨架（旁路绕过）

### 5.3 首次分析 vs 增量更新的填充流程

**首次分析（无备份）**：Step C 必须按以下子步骤渐进式填充：

```
C.1 顶部元信息（变更日志、PRD 版本）→ str_replace 替换 5 个占位符
C.2 第一节 PRD 自检清单 → str_replace 替换 12 行 ⏳
C.3 第二节断言覆盖详情：
    C.3.1 元素编号速查表 → str_replace 替换骨架表格
    C.3.2 侦察元素清单 → str_replace 替换骨架占位（基于 Step A 输出）
    C.3.3 元素归类与检查点 → ⚠️ 用"临时文件中转法"替换 BEGIN/END 锚点之间的整段（> 200 行时必须用）
    C.3.4 业务规则 → 同 C.3.3，与 C.3.3 合并到同一个临时文件中
C.4 第三~七节 → 各章节用 str_replace 替换骨架占位
C.5 第八节断言覆盖统计 → 数字字段全部 ⏳ 占位
C.6 第九节 交叉检查结果 → 此处仅占位，实际内容在阶段二由 cross-check.py --markdown 落盘
```

**C.4 关键规则：str_replace 骨架章节时 oldStr 必须覆盖完整章节**

替换第三~七节的骨架占位时，oldStr 必须从**章节标题行**开始，到**下一个 `---` 分隔线或下一个 `## ` 二级标题**之前结束（含该章节的所有子节）。

**正确做法**：先 read_file 看目标章节的完整范围（从 `## 三、` 到 `## 四、` 之前），把整段作为 oldStr 替换。

**错误做法**：
- ❌ 只取章节标题 + 表格前 2 行作为 oldStr（后面的骨架行会残留）
- ❌ 不看骨架就动手替换（不知道骨架有多少行）
- ❌ 假设"骨架只有表头 + 1 行示例"（实际可能有子节、注释、多行示例）

**C.5 关键规则：count-coverage 输出必须回填 3+1 个位置**

跑完 count-coverage.py 后，必须把统计数字回填到以下位置（不能只填第八节）：

| 位置 | 回填内容 | 方式 |
|------|---------|------|
| 第一节自检第 1 项"说明"列 | "断言覆盖统计：N 元素 / M 检查点 / 覆盖率 X%" | str_replace |
| 第二节速查表底部统计行 | "检查点总数 M 个" | str_replace |
| 第八节断言覆盖统计表 | 完整 6 行统计表 | str_replace |
| **第二节速查表每行"检查点数"列** | 每个元素的实际检查点数（数 `#### {ID}.` 下方表格行数） | 脚本自动扫描回填 |

**速查表检查点数回填方法**：

```python
# 扫描每个 #### {ID}. 下方的表格行数，替换速查表对应行的 ⏳
for elem_id in all_ids:
    count = 数该元素下方 "| N |" 开头的行数
    速查表对应行的 "⏳" → str(count)
```

这一步可以合并到 count-coverage 回填脚本中一起做，不需要单独跑。

### 5.3.1 关键规则：锚点替换 vs fs_append

模板的"二、断言覆盖详情"内有 `<!-- BEGIN_ELEMENTS_AND_RULES -->` / `<!-- END_ELEMENTS_AND_RULES -->` 锚点，标记"元素归类与检查点"+"未归类业务规则"的填充位置。

**正确做法**：用 str_replace 替换两个锚点之间的整段内容（含锚点本身），保证内容嵌入第二节内、第三节之前。

**错误做法（已踩坑）**：
- ❌ 用 fs_append 追加元素表格——内容会到文件末尾（在第九节之后），结构错位
- ❌ 不读骨架就动手——不知道锚点在哪，乱填位置

**操作示例**：
```python
# 正确：锚点替换
str_replace(
    oldStr="<!-- BEGIN_ELEMENTS_AND_RULES -->\n... 模板样例 ...\n<!-- END_ELEMENTS_AND_RULES -->",
    newStr="### 模块 A\n#### C01. ...\n\n#### C02. ...\n\n... 全部模块和业务规则 ..."
)
```

**大内容锚点替换标准流程（> 200 行时必须用）**：

当锚点之间需要填充的内容超过 200 行（如 40 个元素 × 8 检查点 = 600+ 行）时，单次 str_replace 容易超时/截断。必须用以下"临时文件中转"流程：

```
Step 1: fs_write("_tmp_elements.md", 模块 A 内容)     — 创建临时文件（≤ 50 行）
Step 2: fs_append("_tmp_elements.md", 模块 B 内容)    — 追加（每次 50-80 行）
Step 3: fs_append("_tmp_elements.md", 模块 C 内容)    — 追加
  ...重复直到全部模块 + 业务规则写完...
Step N: 跑 3 行 Python 脚本做文件级替换：
        读 analysis → 替换 BEGIN/END 之间内容为临时文件全文 → 写回
Step N+1: 删除全部临时文件（_tmp_elements.md + 替换脚本 _tmp_replace.py 等所有 _tmp_*）
```

> ⚠️ Step N+1 要删的不止 `_tmp_elements.md`，还包括替换脚本本身（如 `_tmp_replace.py`）和任何 `_tmp_*` 中转产物。**阶段一收尾即删，不要拖到阶段二第六步 cleanup-temp.py**（见 1.1 阶段一交付清单"临时文件已清理"项）。

**替换脚本模板**（每次复用，不需要重写）：

```python
# _tmp_replace_anchor.py
import re
from pathlib import Path

analysis = Path(r'<analysis路径>')
content = Path(r'<临时文件路径>').read_text(encoding='utf-8')
text = analysis.read_text(encoding='utf-8')

# 替换 BEGIN 到 END 之间的全部内容（含锚点本身）
new_text = re.sub(
    r'<!-- BEGIN_ELEMENTS_AND_RULES -->.*?<!-- END_ELEMENTS_AND_RULES -->',
    content,
    text,
    flags=re.DOTALL,
)
analysis.write_text(new_text, encoding='utf-8')
print(f"替换完成: {analysis} ({len(new_text)} 字符)")
```

**临时文件内容规范**：
- ✅ 从第一个模块标题开始（如 `### 模块 A：全局布局`），不含 `### 元素归类与检查点` 标题
- ✅ 到最后一个业务规则结束，不含 `<!-- END_ELEMENTS_AND_RULES -->` 标记
- ❌ **禁止**在临时文件开头重复写 `### 元素归类与检查点` 标题——该标题在骨架的 BEGIN 锚点之前已存在
- ❌ **禁止**在临时文件中包含 BEGIN/END 锚点标记

**优点**：
- ✅ 每次 fs_write/fs_append 只处理 50-80 行，不超时
- ✅ 中断后临时文件保留，恢复时从断点继续 fs_append
- ✅ 不改模板结构
- ✅ 替换脚本是固定模板，不需要每次重写

**中断恢复**：如果中途断了，先 read_file `_tmp_elements.md` 看写到哪个模块了，从下一个模块继续 fs_append。

### 5.3.2 章节填充判定流程

每个章节填充前必须先判定：

| 章节占位形态 | 填充方法 |
|------------|---------|
| 短占位（< 30 行，如自检清单 12 行）| str_replace 替换整节 |
| 长占位含 BEGIN/END 锚点 | str_replace 替换锚点之间内容 |
| 文件末尾且无后续章节 | fs_append 追加（仅适用于"九"节及之后）|
| 章节标题已存在但内容为空 | str_replace 在标题后追加内容 |

**增量更新（已有 analysis）**：参见第 7 节"PRD 版本变更追踪"。

### 5.3.3 阶段二渐进式填充流程（D.1 ~ D.6）

阶段二填充 requirements.md 必须按以下子步骤推进。**所有需要嵌入到模板内部的内容必须用 str_replace 替换 BEGIN/END 锚点之间的整段，不能用 fs_append**（否则内容会被追加到文件末尾，结构错位）。

模板已内置 8 个锚点（详见 `~/.cantor-os/md/QA/requirements.md.tpl`）：

| 锚点对 | 章节 | 内容 |
|--------|------|------|
| `PROJECT_OVERVIEW` | 一、项目概览 | 系统目标、用户角色概述、范围 |
| `ROLES_AND_PERMISSIONS` | 三、角色权限 | 角色矩阵、能力清单 |
| `STATE_MACHINES` | 四、状态机 | YAML 状态流转定义 |
| `ACCEPTANCE_CRITERIA` | 五、验收标准 | 各模块 AC 表格（5.1 ~ 5.N）|
| `BUSINESS_ENTITIES` | 六、业务实体 | 实体字段表 + 关系图 |
| `API_CONTRACT` | 七、接口契约 | 接口列表 / "不测试"声明 |
| `PRECONDITIONS` | 九、前置条件 | 测试数据、账号、环境 / "不测试"声明 |
| `PERFORMANCE_AND_ENV` | 八、性能 + 十、环境 | 性能要求 / 环境矩阵 |

**子步骤**：

```
D.1  顶部元信息 + 一、项目概览 + 二、章节用途索引 + 三、角色权限
     ├─ str_replace 顶部占位（PRD版本/分析日期/AC总数等）
     ├─ str_replace PROJECT_OVERVIEW 锚点 → 系统目标 + 范围
     ├─ str_replace 二、章节用途索引表格（10 行 × 3 列）
     └─ str_replace ROLES_AND_PERMISSIONS 锚点 → 角色矩阵

D.2  四、状态机（YAML 块）
     └─ str_replace STATE_MACHINES 锚点 → 含 from/to/trigger/assertion 的 YAML
        ⚠️ 必填字段：from / to / trigger / assertion（缺一项 validate 报错）

D.3  五、验收标准（按 5.1 ~ 5.N 子节分组）
     └─ str_replace ACCEPTANCE_CRITERIA 锚点 → 全部子节合并的 AC 表格
        ⚠️ 表格 5 列必填：AC-ID | 验收标准 | 类型 | 断言 | 来源
        ⚠️ "断言"列必须给具体可执行步骤（≥ 10 字），禁止"待补充"/为空
        ⚠️ "来源"列必须填 C{xx}#{n} 或 BR{xx}#{n}；纯技术规范允许"—"但需注释

D.4  六、业务实体
     └─ str_replace BUSINESS_ENTITIES 锚点 → 实体字段表 + ER 关系说明

D.5  七、接口契约 + 九、前置条件（按"不测试"决策处理）
     ├─ str_replace API_CONTRACT 锚点 → 声明"本期不测试，由后端集成测试覆盖"
     └─ str_replace PRECONDITIONS 锚点 → 测试数据/账号/环境清单

D.6  八、性能 + 十、环境矩阵 + 附录 AC 索引
     ├─ str_replace PERFORMANCE_AND_ENV 锚点 → 性能"不测试"声明 + 环境矩阵
     └─ fs_append 附录章节（AC 索引、变更日志等，仅追加到文件末尾）
```

**关键约束**：

- ✅ **D.1 ~ D.5 全部用 str_replace 替换锚点**，每个锚点替换一次到位
- ✅ 仅 D.6 末尾的"附录"允许 fs_append（因为附录在文件末尾，无后续章节）
- ❌ **禁止**用 fs_append 写五章 AC 表格——会被追加到文件末尾、跳出第五章范围
- ❌ **禁止**多次 str_replace 同一锚点拼接内容——锚点替换后就消失了
- ✅ 每完成一个 D.x 子步骤，立即跑一次 `validate-requirements.py` 看进度（不强制，但推荐）
- ✅ D.3 完成后必须立即跑 `cross-check.py`，进入"5.1.2 阶段二交付清单"中的"循环修复"

**起步检查（D.1 之前）**：
- read_file 读模板生成的骨架，**用 grep_search 确认 8 个锚点对全部存在**
- 如果有缺失锚点 → 模板出错，stop and report，不要继续填充

### 5.4 分段写文档：fs_append 不是里程碑

当任务需要把一个长文档（>150 行 / 多章节）分多次 fs_append 写入时：

- ❌ 每次 fs_append **不是里程碑**——即使一次写了 200 行表格，也只是部分进度
- ❌ 禁止 fs_append 后回 "understood" / "ok" / "done" 然后停止
- ✅ 任务开始前必须输出"写入计划"清单：`本文档分 N 批写入，批次 1=第 X 节...`
- ✅ 每次 fs_append 后立即继续下一次 fs_append，直到目标文件**所有计划章节全部完成**
- ✅ 中间停顿必须输出 `📝 写入进度：X/N 段已完成，下一段：xxx`

### 5.5 上下文中断恢复机制

**触发信号**（满足任一即必须走恢复流程）：
1. 用户消息含"继续"、"接着写"、"接着做"、"断了"、"重连"、"context lost"等关键词
2. 当前对话深度 ≥ 30 轮，且最近 10 轮有 file write 操作
3. 用户上一条消息提到的文件已存在但内容不完整（read_file 返回 < 模板预期行数）
4. agent 自己感觉"记不清此前进度了"

**恢复操作 5 步**（必跑）：

```
Step 1: 读取已生成文件
  - read_file analysis.md → 计算行数 N1
  - read_file requirements.md → 计算行数 N2
  - 用 grep_search "^## " 列出所有二级标题

Step 2: 对照模板检查完整性
  - analysis.md 应有 9 节
  - requirements.md 应有 10 章 + 章节用途索引 + 附录 AC 索引

Step 3: 对比脚本输出
  - 跑 count-coverage.py 看实际元素数与速查表是否一致
  - 跑 cross-check.py 看 missing 数

Step 4: 行动决策
  - 完整 + 脚本通过 → 续写最后一节或下一阶段
  - 章节缺失 → 从最早缺失点续写
  - 章节齐全但脚本失败 → 修复脚本失败项，不要继续往下写

Step 5: 输出"恢复诊断"摘要（强制）
  📂 已生成文件：
    - analysis.md: {行数} 行（应至少 {N} 行）→ {完整/缺失}
  📊 脚本状态：
    - count-coverage.py: 元素 {N}, 检查点 {M}, 速查表 {一致/不一致}
  🎯 下一步行动：{具体描述}
```

**禁止**：
- 收到"继续"就直接 fs_append 写新内容
- 假设"上轮我已经写完了 X 节"
- 不读已生成文件就说"已完成"
- 跳过 Step 5 的恢复诊断报告

---

## 6. 脚本使用规范（强制）

> 此节合并了原"脚本优先原则"+"统计数字字段"+"Windows 终端编码"。

### 6.1 脚本优先原则

- 完整步骤表中标注"必跑"的脚本，必须用 `execute_pwsh` 实际执行，不可"凭经验代替"
- 脚本失败/不可用时，必须先尝试修复脚本本身（依赖、参数、文件路径）
- 仅在确认脚本无法运行时才允许 fallback 到手工流程，并且必须在 analysis 中说明
- 脚本输出必须以表格形式纳入 analysis 对应章节，不能只在终端展示后丢弃

### 6.2 统计数字字段必须先跑脚本再填

含数字的章节字段必须遵循以下顺序：

1. **写章节内容时不填数字字段，用 `⏳ 待 count-coverage.py` 占位**
2. 整个 analysis 章节内容完成后，跑 `count-coverage.py`
3. **把脚本输出表格直接复制粘贴到对应章节**（不允许"约 N"等估算）
4. 二次跑 `count-coverage.py` 确认 analysis 中数字与脚本输出一致

**禁止**：
- ❌ 凭记忆估算填数字（"应该是 29 个吧"）
- ❌ 用"约 N"、"大约 N"模糊表述
- ❌ 跑了脚本但只在终端展示，不更新 analysis

### 6.3 Windows 终端中文乱码处理

在 Windows + PowerShell/cmd 下执行 Python 脚本时，必须**同时**设置以下两项编码：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING='utf-8'; python <脚本> <参数>
```

两个都必须设置，缺一会乱码。把这两条作为脚本调用的标准前缀。

### 6.4 脚本输出 → analysis 对接（详见 scripts-usage.md）

| 脚本 | 输出落到 |
|------|---------|
| `extract-elements.py` | 二、侦察元素清单（按文件分组表格 + 业务级聚合清单）|
| `count-coverage.py` | 八、断言覆盖统计 |
| `cross-check.py` | 九、交叉检查结果 |
| `validate-requirements.py` | 三、各章节诊断 |

---

## 7. PRD 版本变更追踪与增量更新（强制）

PRD 是迭代演进的（如"首页框架 V1.0 → V1.13"）。当用户要求"按新版 PRD 更新"或"PRD 改了"时，agent **必须做增量更新**而非重新生成全文。

### 触发信号识别

满足任一条件视为"PRD 变更场景"：
1. 用户明确说"PRD 改了"、"PRD 更新了"、"按新版本重做"
2. PRD 文档头部版本号高于 analysis 顶部记录的"PRD 版本"
3. analysis 已存在且完整，但用户要求重新分析同一个 PRD

### 增量更新流程

```
Step 1: 版本对比 — 读取 analysis 顶部"PRD 版本"+ 新 PRD 版本，计算 diff
Step 2: 影响范围评估 — 列出 PRD 变更点 + 每条标注影响范围
Step 3: 局部更新 analysis — 仅修改受影响的元素/规则；变更日志追加一行
Step 3.5: 测试驱动 PRD 缺陷修正计数 — 统计本次被新 PRD 补充/确认的「待补充/待确认」点数，
          追加「测试驱动的 PRD 缺陷修正统计」表一行 + 刷新哨兵（见下"测试驱动的 PRD 缺陷修正计数"）
Step 4: 同步更新 requirements.md — 受影响的 AC 修改/新增/删除
Step 5: 跑 validate-requirements.py --analysis 验证同步性
```

### 变更日志格式

在 analysis 顶部"分析日期"下方维护：

```markdown
> 分析日期：2026-05-19
> PRD 版本：V1.14（基于 V1.13 增量更新）

## 变更日志

| 更新日期 | 基础版本 | 新版本 | 变更点 | 影响范围 | 状态 |
|---------|---------|--------|--------|---------|------|
| 2026-05-25 | V1.13 | V1.14 | 新增"游客态轮播间隔可配置" | C06.Banner + AC-02-07 | ✅ |
| 2026-05-19 | — | V1.13 | 初始分析 | 全量 | ✅ |
```

### 测试驱动的 PRD 缺陷修正计数

> 用途：度量"测试需求分析"对 PRD 质量的贡献——由测试分析发现、并经后续 PRD 更新补充/确认的缺陷点数量。
> 报告（qa-test-report）的「测试驱动 PRD 缺陷修正数」直接取此处累计。

**计数规则**（一个被解决的待办点 = 1）：

- 计 1 的条件：上一版 analysis 里某个标记为「待补充 / 待确认」（即缺陷汇总 D-xx 状态为 ⏳、或待确认事项汇总中的一条）的点，被**新版 PRD 补充或确认**而得以闭环。
- 不计：本次分析新发现但 PRD 尚未解决的点（仍是待办，不算"已修正"）；非测试驱动的 PRD 自身改动（如产品自行新增功能）。
- **首次分析填 0**（尚无任何 PRD 更新解决待办点）。
- 每次按新 PRD 增量更新时，统计本次被解决的点数 `本次修正点数`，`累计 = 上次累计 + 本次修正点数`。

**落库位置**：analysis 顶部「## 测试驱动的 PRD 缺陷修正统计」表 + 表下哨兵 `<!-- PRD_DEFECT_TOTAL: N -->`（N = 最新累计）。

**Step 3.5 操作**：

1. 对比上一版 analysis 的「待补充/待确认」点清单 与 新 PRD：逐点判断是否已被补充/确认。
2. 数出本次被解决的点数 `k`（k 可为 0）。
3. 在「测试驱动的 PRD 缺陷修正统计」表追加一行：`| 更新日期 | 基础PRD | 新PRD | k | 累计+ k |`。
4. 刷新表下哨兵为最新累计：`<!-- PRD_DEFECT_TOTAL: <累计> -->`（哨兵全文件只保留一处，用 str_replace 改值，不要新增）。

### 老 analysis 升级路径（接入本流程前生成的旧骨架）

旧骨架不含「## 测试驱动的 PRD 缺陷修正统计」段。**首次跑 PRD 增量更新时必须先补建**，否则 `validate-requirements.py` 第 12 项 check（PRD 缺陷修正追踪一致性）会 FAIL：

1. **判断**：grep_search analysis 是否含 `<!-- PRD_DEFECT_TOTAL`。没有就要补建。
2. **补建位置**：在「## 变更日志」表末与「## 一、PRD 质量自检清单」之间，插入与最新模板（`md/QA/requirements-analysis.md.tpl`）一致的「## 测试驱动的 PRD 缺陷修正统计」段（含表 + 哨兵）。
3. **盘点累计**：若历史增量已发生但未记录，按「上一版『待补充/待确认』点被新版 PRD 补充/确认 = 计 1」**人工盘点**填首建累计；无法盘点则从 0 起算，并在「解决明细」列写「首建（历史无追溯）」。
4. **当次增量**：补建后正常按 Step 3.5 统计本次被解决的点数 + 追加新行 + 刷新哨兵。

> 不补建的后果：qa-test-report「测试驱动 PRD 缺陷修正数」字段显示「—」（不阻塞但失真）；`validate-requirements.py` 第 12 项 FAIL（阻塞交付，**强制升级**）。

### 全量重做的合法场景（仅这 3 种）

1. PRD 大改（版本跳跃 ≥ 2 个大版本，如 V1.x → V3.0）
2. analysis 文件本身有结构性错误（章节顺序错、模板格式不兼容）
3. 用户明确说"重新做一遍，之前的不要了"

### 唯一允许的"复用已有 analysis 内容"场景

1. **PRD 增量更新**（本节）：在已有 analysis 上做局部 str_replace 修改受影响章节
2. **上下文恢复**（参考 5.5）：从已生成的部分 analysis 续写
3. **明确的演练/迁移场景**：用户明确说"用旧 analysis 内容做起点演练新流程"——agent 必须显式标注"这是演练复用，不是真实首次分析"

**禁止**：
- ❌ 收到"PRD 改了"就重新生成全文 → 丢失人工修订
- ❌ 不更新顶部"PRD 版本"字段，下次无法识别基线
- ❌ 用 `Copy-Item` 等旁路命令复制覆盖
