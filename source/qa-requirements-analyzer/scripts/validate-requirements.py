"""
validate-requirements.py — requirements.md 结构合规性校验

检查项：
  1. 章节用途索引表格存在
  2. 10 个章节齐全（一~十）
  3. 状态机 YAML 语法合法 + 含 from/to/trigger/assertion 字段 + 状态闭包
     （每个 from 状态必须在 states 列表中声明，避免引用未定义状态）
  4. AC 表格列齐全（规则概念认双叫法「验收标准|规则」+ 结构列「类型/断言」新格式
     或「正向/反向/边界」旧格式；正/反/边界属覆盖度，归 count-coverage/cross-check）
  5. AC 来源列必填（每条 AC 必须填写指向 analysis 的检查点编号）
  6. AC 编号格式合规 + 唯一性（AC-NN-NN 或 AC-NN-NNa，禁止多层后缀，禁止重复）
  7. AC 断言列完整性（每条 AC 的"断言"列必须有具体内容，长度 ≥ 5 字，
     禁止为空 / "待补充" / "TODO" / "—" 等占位符）
  8. AC "待产品确认"与来源列一致性（标记"待产品确认"的 AC 来源列可为 `—`/空，
     也可填指向 analysis 检查点的合法 ID（如 C01#1，提供溯源，与 cross-check
     精确来源匹配口径一致）；仅当来源列既非 `—`/空、又不含任何合法检查点 ID
     （纯垃圾文本）时才判不合规）
  9. 接口契约含错误码枚举
  10. 不允许出现 "TBD" / "待确认"（除了"⚠️ 待产品确认，暂不测试"豁免）
  11. （可选，需 --analysis）analysis 与 requirements 同步：
      analysis 中"需补充=否"的检查点必须在 requirements.md AC 来源列引用至少一次
  12. （可选，需 --analysis）PRD 缺陷修正追踪一致性：
      analysis 必须含「## 测试驱动的 PRD 缺陷修正统计」章节 + <!-- PRD_DEFECT_TOTAL: N --> 哨兵；
      哨兵 N 必须 = 统计表最后一行的"累计"列数值；统计表行数 >= 变更日志行数。
  13. （可选，需 --analysis）临时文件残留检查：
      analysis 同目录不得残留 _tmp_* / *.bak / *.pyc 中转文件（阶段一收尾即清）。
  14. AC 验收标准列非空（空字段硬扫，硬 fail）：每条 AC 的「验收标准」列不得为空 / —。
  15. AC 断言具体性（断言化试金石，warn 级）：AC 断言列若只有模糊词（正确/正常/符合预期…）
      且无任何具体锚点（引号文案/数字/路由/枚举/布尔/可见性…）→ 警告，应改具体值或标缺口。
      warn 级不翻 verdict、不影响退出码，仅提示复核。
  16. （可选，需 --analysis）第五章 PRD 位置非自指章节号（warn 级）：
      analysis「五、待确认事项汇总」的「PRD 位置」列（兼容旧「章节」列）禁填本文档章节号
      （一~十，尤其"五"自指）；应填 PRD 功能点/章节号（如 §3.7 口语能力图谱 C11）。
  17. 规则版本一致性（warn 级）：读取产物顶部 <!-- RULESET_VERSION: X --> 戳，与脚本
      CURRENT_RULESET_VERSION 比对；缺失/不一致则提示"规则已升级，建议重生成受影响章节"。

用法:
    python validate-requirements.py requirements.md
    python validate-requirements.py requirements.md --analysis requirements-analysis.md
    python validate-requirements.py requirements.md --output report.json
    python validate-requirements.py requirements.md --markdown   # 输出可粘贴到 analysis 第三节的 md 块

退出码:
    0  全部通过
    1  存在校验错误
    2  脚本错误
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

# Windows GBK fallback: force UTF-8 stdout/stderr
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


REQUIRED_CHAPTERS = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

# 规则集版本（P2-2）：升级硬校验规则时 +1，并在【三处同步】此值：
#   1. 本常量 CURRENT_RULESET_VERSION
#   2. md/QA/requirements.md.tpl 顶部 <!-- RULESET_VERSION: X --> 戳
#   3. md/QA/requirements-analysis.md.tpl 顶部 <!-- RULESET_VERSION: X --> 戳
# 产物里记生成时的版本戳，validate 用 check_ruleset_version（warn 级）比对，
# 版本不一致时提示"规则已升级，建议重生成受影响章节"，让 agent 主动决策。
CURRENT_RULESET_VERSION = "2026.07"
FUZZY_TERMS_BLOCKED = ["TBD", "tbd", "待确认"]
FUZZY_TERMS_ALLOWED_CONTEXT = [
    "待产品确认",
    "⚠️ 待产品确认",
    "⚠️ 待确认",  # 表格中作为状态标识
    "暂不测试",
    "确认后完善",
]


def extract_chapter(text: str, chapter_num: str, next_chapter_num: str) -> str:
    """提取「{chapter_num}、xxx」章节的完整内容（直到「{next_chapter_num}、」或文末）。"""
    start_pattern = re.compile(rf"(?m)^#+\s+{chapter_num}、")
    start_match = start_pattern.search(text)
    if not start_match:
        return ""
    start = start_match.start()
    end_pattern = re.compile(rf"(?m)^#+\s+{next_chapter_num}、")
    end_match = end_pattern.search(text, pos=start_match.end())
    end = end_match.start() if end_match else len(text)
    return text[start:end]


def check_index_table(text: str) -> dict:
    has_index = "章节用途索引" in text
    return {
        "name": "章节用途索引表格",
        "passed": has_index,
        "detail": "找到「章节用途索引」表格" if has_index else "未找到「章节用途索引」表格",
    }


def check_chapters(text: str) -> dict:
    found, missing = [], []
    for ch in REQUIRED_CHAPTERS:
        if re.search(rf"(?m)^#+\s+{ch}、|^{ch}、", text):
            found.append(ch)
        else:
            missing.append(ch)
    return {
        "name": "10 章齐全",
        "passed": len(missing) == 0,
        "detail": f"找到 {len(found)}/10 章, 缺失: {', '.join(missing) if missing else '无'}",
    }


def check_state_machine_yaml(text: str) -> dict:
    sm_section = extract_chapter(text, "四", "五")
    if not sm_section:
        return {"name": "状态机 YAML", "passed": False, "detail": "未找到「四、状态机」章节"}
    yaml_blocks = re.findall(r"```ya?ml\n(.*?)```", sm_section, re.DOTALL)
    if not yaml_blocks:
        return {"name": "状态机 YAML", "passed": False, "detail": "「四、状态机」章节中无 YAML 代码块"}
    required_fields = ["from", "to", "trigger", "assertion"]
    yaml_text = "\n".join(yaml_blocks)
    missing_fields = [f for f in required_fields if f not in yaml_text]

    # 状态闭包检测：每个 from / to 引用的状态必须在某个 states: 列表中声明过
    # 处理多个独立 YAML 块（每块独立闭包）
    closure_issues: list[str] = []
    for idx, block in enumerate(yaml_blocks, 1):
        # 解析 states: 列表（YAML list 形式：- StateName）
        # 注意：可能含中文 + 注释
        declared_states: set[str] = set()
        in_states_block = False
        for line in block.split("\n"):
            stripped = line.strip()
            if stripped.startswith("states:"):
                in_states_block = True
                continue
            if in_states_block:
                # 列表项 "- 名称"
                m = re.match(r"^\s*-\s+([^\s#].*?)(?:\s*#.*)?$", line)
                if m:
                    state = m.group(1).strip().strip('"\'')
                    declared_states.add(state)
                elif stripped and not line.startswith(" ") and not line.startswith("\t"):
                    # 顶格非空行、非列表项 → states 块结束
                    in_states_block = False

        if not declared_states:
            # 该 YAML 块没有 states 列表，跳过闭包检查（不强制每块都有）
            continue

        # 提取所有 from / to 引用的状态
        # 形式：{ from: 状态A, to: 状态B, ... } 或 from: 状态A
        # 兼容"状态(注解)"形式：把 `个人教程(领取来源)` 提取为 `个人教程` 再比对
        # （注解用于参数化同一状态在不同上下文，不视为新状态）
        referenced_states: set[str] = set()
        for m in re.finditer(r"(?:from|to)\s*:\s*([^\s,}#]+(?:\s+[^\s,}#]+)*?)(?=\s*[,}#\n]|\s*$)", block):
            ref = m.group(1).strip().strip('"\'').strip()
            if ref:
                # 去掉尾部 "(...)" 注解部分
                bare = re.sub(r"\([^)]*\)\s*$", "", ref).strip()
                referenced_states.add(bare if bare else ref)

        # 闭包：referenced - declared 应为空集
        undeclared = referenced_states - declared_states
        if undeclared:
            sample = sorted(undeclared)[:3]
            closure_issues.append(
                f"YAML 块 {idx}: from/to 引用了未在 states 中声明的状态 {sample}"
                + (f"（共 {len(undeclared)}）" if len(undeclared) > 3 else "")
            )

    passed = len(missing_fields) == 0 and len(closure_issues) == 0
    detail_parts = [f"YAML 块数: {len(yaml_blocks)}"]
    detail_parts.append(f"缺失字段: {', '.join(missing_fields) if missing_fields else '无'}")
    if closure_issues:
        detail_parts.append("状态闭包: " + "; ".join(closure_issues))
    else:
        detail_parts.append("状态闭包: 通过")

    return {
        "name": "状态机 YAML 字段齐全 + 状态闭包",
        "passed": passed,
        "detail": ", ".join(detail_parts),
        "issues": closure_issues if closure_issues else None,
    }


def check_ac_columns(text: str) -> dict:
    section_text = extract_chapter(text, "五", "六")
    if not section_text:
        return {"name": "AC 表格列齐全", "passed": False, "detail": "未找到「五、验收标准」章节"}
    # 规则概念认双叫法：新模板列名「验收标准」/ 旧格式列名「规则」，任一命中即可。
    #   （历史 bug：模板已从「规则」改名为「验收标准」，旧校验器死抠「规则」→ 新产物稳定误报
    #    「缺失列: 规则」。见 lessons-learned。此处统一认双叫法治根。）
    has_rule_col = ("验收标准" in section_text) or ("规则" in section_text)
    # 断言/类型维度接受两种结构：
    #   新格式（当前模板，一行一 AC）：用「类型」列（行取值为 正向/反向/边界/异常）+「断言」列
    #   旧格式（遗留，一行一规则）：用「正向 / 反向 / 边界」分列
    #   正/反/边界属"覆盖度"而非"结构"，覆盖度由 count-coverage / cross-check 负责，
    #   这里只判结构列是否齐全。
    new_style = ("类型" in section_text) and ("断言" in section_text)
    old_style = all(w in section_text for w in ("正向", "反向", "边界"))
    missing = []
    if not has_rule_col:
        missing.append("验收标准|规则")
    if not (new_style or old_style):
        missing.append("类型+断言（新格式）或 正向/反向/边界（旧格式）")
    return {
        "name": "AC 表格列齐全（验收标准|规则 + 类型/断言 或 正向/反向/边界）",
        "passed": len(missing) == 0,
        "detail": f"缺失列: {', '.join(missing) if missing else '无'}",
    }


def check_ac_source_column(text: str) -> dict:
    """检查 AC 表格是否包含'来源'列，且每条 AC 都填写了来源。"""
    section_text = extract_chapter(text, "五", "六")
    if not section_text:
        return {
            "name": "AC 来源列必填",
            "passed": False,
            "detail": "未找到「五、验收标准」章节",
        }

    # 1. 表头必须含"来源"列
    has_source_header = "来源" in section_text
    if not has_source_header:
        return {
            "name": "AC 来源列必填",
            "passed": False,
            "detail": "AC 表格表头缺少「来源」列。每条 AC 必须填写来源（指向 analysis 检查点编号）",
        }

    # 2. 检查每条 AC 行是否有来源（最后一列）
    # AC 行 pattern: | AC-xx | ... | ... | <来源> |
    ac_row_pattern = re.compile(
        r"^\|\s*(AC-[\w\-]+)\s*\|.*?\|\s*([^|]*)\s*\|\s*$",
        re.MULTILINE,
    )
    missing_source = []
    for m in ac_row_pattern.finditer(section_text):
        ac_id = m.group(1).strip()
        source = m.group(2).strip()
        # 来源不能为空字符串。"—"（破折号）是合法值，表示无对应检查点
        if not source:
            missing_source.append(ac_id)

    return {
        "name": "AC 来源列必填",
        "passed": len(missing_source) == 0,
        "detail": (
            f"全部 AC 已填写来源列"
            if len(missing_source) == 0
            else f"以下 AC 来源列为空（需填写 C{{xx}}#{{n}} 或 —）: {', '.join(missing_source[:5])}"
            + (f" ...(共 {len(missing_source)} 条)" if len(missing_source) > 5 else "")
        ),
        "issues": missing_source if missing_source else None,
    }


def check_ac_id_format(text: str) -> dict:
    """检查 AC 编号格式合规性 + 唯一性。

    格式：AC-NN-NN 或 AC-NN-NNa（单字母后缀，用于补丁）
    非法：多层后缀（AC-01-05a-i）、含点（AC-01-05.1）、含下划线
    重复：同一编号在 AC 行首列出现 ≥ 2 次（说明 agent 复制 AC 行漏改）
    """
    section_text = extract_chapter(text, "五", "六")
    if not section_text:
        return {"name": "AC 编号格式 + 唯一性", "passed": True, "detail": "未找到「五、验收标准」章节"}

    # 提取所有出现的 AC ID（用于格式检查）
    ac_ids = re.findall(r"\bAC-[\w\-\.]+", section_text)
    illegal = []
    legal_pattern = re.compile(r"^AC-\d+-\d+[a-z]?$")
    seen = set()
    for ac_id in ac_ids:
        if ac_id in seen or ac_id == "AC-ID":
            continue
        seen.add(ac_id)
        if not legal_pattern.match(ac_id):
            illegal.append(ac_id)

    # 唯一性检测：扫 AC 表格行首列，看每个 ID 出现次数
    # 行首列匹配：| AC-xx | ... 排除"| AC-ID |"表头
    ac_row_pattern = re.compile(r"^\|\s*(AC-\d+-\d+[a-z]?)\s*\|", re.MULTILINE)
    id_counts: dict[str, int] = {}
    for m in ac_row_pattern.finditer(section_text):
        aid = m.group(1)
        id_counts[aid] = id_counts.get(aid, 0) + 1
    duplicates = [(aid, cnt) for aid, cnt in id_counts.items() if cnt > 1]

    issues_summary = []
    if illegal:
        issues_summary.append(f"非法格式: {', '.join(illegal[:5])}")
    if duplicates:
        dup_str = ", ".join(f"{aid}×{cnt}" for aid, cnt in sorted(duplicates)[:5])
        issues_summary.append(f"重复编号: {dup_str}")

    passed = len(illegal) == 0 and len(duplicates) == 0
    return {
        "name": "AC 编号格式 + 唯一性",
        "passed": passed,
        "detail": (
            f"全部 AC 编号符合 AC-NN-NN 或 AC-NN-NNa 格式且唯一（共 {len(id_counts)} 条）"
            if passed
            else "; ".join(issues_summary)
        ),
        "issues": {
            "illegal_format": illegal if illegal else None,
            "duplicates": [{"ac_id": aid, "count": cnt} for aid, cnt in duplicates] if duplicates else None,
        } if not passed else None,
    }


def check_ac_assertion_completeness(text: str) -> dict:
    """检查每条 AC 的"断言"列必须有具体内容（长度 ≥ 5 字符，禁止占位符）。

    AC 表格 5 列结构: | AC-ID | 验收标准 | 类型 | 断言 | 来源 |
    断言列在第 4 列（倒数第 2 列）。
    """
    section_text = extract_chapter(text, "五", "六")
    if not section_text:
        return {
            "name": "AC 断言列完整性",
            "passed": False,
            "detail": "未找到「五、验收标准」章节",
        }

    # 占位符黑名单（断言列出现以下内容视为未填写）
    BLOCKED_PLACEHOLDERS = {
        "—", "-", "待补充", "待填", "待确认", "TODO", "todo", "TBD", "tbd",
        "?", "？", "...", "暂无", "N/A", "n/a", "NA",
    }
    MIN_LENGTH = 5  # 最少 5 个字符（含中英文）

    # AC 行 5 列匹配: | AC-xx | 验收标准 | 类型 | 断言 | 来源 |
    ac_5col_pattern = re.compile(
        r"^\|\s*(AC-[\w\-]+)\s*\|([^\n]+?)\|([^\n]+?)\|([^\n]+?)\|([^\n]+?)\|\s*$",
        re.MULTILINE,
    )

    issues = []  # list of (ac_id, reason, content_preview)
    for m in ac_5col_pattern.finditer(section_text):
        ac_id = m.group(1).strip()
        assertion = m.group(4).strip()

        # 跳过表头行
        if assertion in ("断言", "Assertion"):
            continue

        # 检查 1: 为空
        if not assertion:
            issues.append((ac_id, "断言列为空", ""))
            continue

        # 检查 2: 命中占位符黑名单
        if assertion in BLOCKED_PLACEHOLDERS:
            issues.append((ac_id, f"断言列为占位符'{assertion}'", assertion))
            continue

        # 检查 3: 命中可疑关键词（部分匹配）
        suspicious_keywords = ["待补充", "待填", "TODO", "TBD", "待确认"]
        for kw in suspicious_keywords:
            if kw.lower() in assertion.lower():
                issues.append((ac_id, f"断言列含可疑关键词'{kw}'", assertion[:50]))
                break
        else:
            # 检查 4: 长度过短（无可疑关键词时才检查）
            if len(assertion) < MIN_LENGTH:
                issues.append((ac_id, f"断言列长度过短 ({len(assertion)} < {MIN_LENGTH})", assertion))

    return {
        "name": "AC 断言列完整性",
        "passed": len(issues) == 0,
        "detail": (
            f"全部 AC 断言列已填写（最短 ≥ {MIN_LENGTH} 字、无占位符）"
            if len(issues) == 0
            else f"发现 {len(issues)} 处问题: "
            + "; ".join(f"{aid}({reason})" for aid, reason, _ in issues[:5])
            + (f" ...(共 {len(issues)} 条)" if len(issues) > 5 else "")
        ),
        "issues": [
            {"ac_id": aid, "reason": reason, "content": content}
            for aid, reason, content in issues
        ] if issues else None,
    }


def check_pending_confirmation_consistency(text: str) -> dict:
    """检查标记"待产品确认"的 AC 行其来源列合规性。

    统一口径（P0-1：与 cross-check.py 解锁）：
    待产品确认 AC 的来源列**既可以是 `—`/空，也可以填指向 analysis 检查点的
    合法 ID**（如 C01#1）。填 ID 表示"该待确认点源自哪个元素检查点"，是有价值的
    溯源信息，且与 cross-check.py 的"精确来源匹配"分支口径一致（need=是 项命中
    精确 ID 后再校验是否含「待产品确认」marker）。

    合规：
        | AC-01-05 | xx 待产品确认 | 正向 | xxx | — |       ✓（无对应检查点）
        | AC-01-05 | xx 待产品确认 | 正向 | xxx | C01#1 |   ✓（溯源到 C01#1）

    不合规（仅此一种）：来源列既非 `—`/空、又不含任何合法检查点 ID 的纯垃圾文本：
        | AC-01-05 | xx 待产品确认 | 正向 | xxx | 随便写的 |  ✗
    """
    section_text = extract_chapter(text, "五", "六")
    if not section_text:
        return {
            "name": "AC 待产品确认 vs 来源列一致性",
            "passed": True,
            "detail": "未找到「五、验收标准」章节",
        }

    # 5 列 AC 行: | AC-xx | 验收标准 | 类型 | 断言 | 来源 |
    ac_5col_pattern = re.compile(
        r"^\|\s*(AC-[\w\-]+)\s*\|([^\n]+?)\|([^\n]+?)\|([^\n]+?)\|([^\n]+?)\|\s*$",
        re.MULTILINE,
    )

    # 触发"待产品确认"语义的关键词
    PENDING_KEYWORDS = ["待产品确认", "待确认（产品）", "待产品", "暂不测试"]
    # 来源列合法的"无引用"标记
    NO_SOURCE_MARKERS = {"—", "-", ""}
    # analysis 检查点 ID pattern（用于检测来源列是否含真实 ID）
    SOURCE_ID_PATTERN = re.compile(r"[CB][A-Z]*\d+#\d+|US-\d+")

    issues = []
    for m in ac_5col_pattern.finditer(section_text):
        ac_id = m.group(1).strip()
        ac_text = (m.group(2) + m.group(4)).strip()  # 把"验收标准"+"断言"两列合并判断
        source = m.group(5).strip()

        # 跳过表头行
        if "来源" in source and "|" not in source:
            continue

        # 命中"待产品确认"关键词
        is_pending = any(kw in ac_text for kw in PENDING_KEYWORDS)
        if not is_pending:
            continue

        # 来源列为"—"/空 → 合规（无对应检查点）
        if source in NO_SOURCE_MARKERS:
            continue

        # 统一口径（P0-1）：来源列含合法检查点 ID → 合规（溯源，与 cross-check 一致）；
        # 既非 — / 空、又不含任何合法 ID 的纯垃圾文本 → 才判不合规
        ids_in_source = SOURCE_ID_PATTERN.findall(source)
        if not ids_in_source:
            issues.append({
                "ac_id": ac_id,
                "reason": f"AC 文本含'待产品确认'，来源列既非 '—' 也不含合法检查点 ID：{source[:30]!r}",
                "source": source[:50],
            })

    return {
        "name": "AC 待产品确认 vs 来源列一致性",
        "passed": len(issues) == 0,
        "detail": (
            "合规：'待产品确认'AC 来源列均为 '—' 或合法检查点 ID"
            if len(issues) == 0
            else f"发现 {len(issues)} 处不合规: "
            + "; ".join(f"{x['ac_id']}({x['reason']})" for x in issues[:3])
            + (f" ...(共 {len(issues)} 条)" if len(issues) > 3 else "")
        ),
        "issues": issues if issues else None,
    }


def check_error_codes(text: str) -> dict:
    section_text = extract_chapter(text, "七", "八")
    if not section_text:
        return {
            "name": "接口契约含错误码枚举",
            "passed": True,
            "detail": "未找到「七、接口契约」章节（可能标记为「不测试」, 跳过）",
        }
    # 豁免：章节内容明确声明"不测试"或"暂不测试"时跳过
    if re.search(r"不测试|暂不测试|不在(本期|测试)范围", section_text):
        return {
            "name": "接口契约含错误码枚举",
            "passed": True,
            "detail": "「七、接口契约」标记为不测试，跳过错误码检查",
        }
    # 接受多种形式：错误码列表 / errorCode 字段 / code=xxx 简化形式
    has_error_code = bool(re.search(
        r"错误码|error[\s_]?code|errorCode|code\s*[=:]\s*\d+",
        section_text,
        re.IGNORECASE,
    ))
    return {
        "name": "接口契约含错误码枚举",
        "passed": has_error_code,
        "detail": "找到错误码相关字段" if has_error_code else "「七、接口契约」中未发现错误码枚举或 code 字段",
    }


def check_fuzzy_terms(text: str) -> dict:
    issues = []
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        for term in FUZZY_TERMS_BLOCKED:
            if term in line:
                if any(allowed in line for allowed in FUZZY_TERMS_ALLOWED_CONTEXT):
                    continue
                issues.append({"line": i, "term": term, "content": line.strip()[:80]})
    return {
        "name": "无模糊表述（TBD/待确认）",
        "passed": len(issues) == 0,
        "detail": f"发现 {len(issues)} 处模糊表述",
        "issues": issues if issues else None,
    }


def check_analysis_sync(req_text: str, analysis_path: Path) -> dict:
    """检查 analysis 与 requirements 的同步性。

    规则：analysis 中所有"需补充=否"的检查点必须在 requirements.md 的 AC
    来源列中被引用至少一次。如果 analysis 改了某检查点状态但 requirements
    没跟上，此处报警。
    """
    if not analysis_path.exists():
        return {
            "name": "analysis 与 requirements 同步",
            "passed": False,
            "detail": f"analysis 文件不存在: {analysis_path}",
        }

    analysis_text = analysis_path.read_text(encoding="utf-8")

    # 1. 提取 analysis 中所有"需补充=否"且有定义的检查点 ID（exact_id 格式 C13#1）
    expected_ids = set()
    # 复用与 cross-check.py 一致的元素 + 检查点解析逻辑
    elem_pattern = re.compile(r"^####\s+([A-Za-z]{0,3}[\-]?\d+)\.?\s*(.+)$", re.MULTILINE)
    # 注意：列内容可能含转义的 `\|`（markdown 表格里的 `||` 字面），需要先把转义还原
    # 处理方式：行级匹配，对每一行先 replace 再用简单的列分割
    table_row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|(.+)\|\s*$",
        re.MULTILINE,
    )

    # 找元素 sections
    matches = list(elem_pattern.finditer(analysis_text))
    for i, m in enumerate(matches):
        elem_id = m.group(1).strip()
        section_start = m.end()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(analysis_text)
        # 也要在遇到 ## 或 # 一级章节时截断
        h2_match = re.search(r"^#{1,2}\s", analysis_text[section_start:section_end], re.MULTILINE)
        if h2_match:
            section_end = section_start + h2_match.start()
        section = analysis_text[section_start:section_end]

        for row in table_row_pattern.finditer(section):
            cp_index = row.group(1).strip()
            inner = row.group(2)
            # 先把转义的 \| 替换为占位符，分割后再还原
            ESCAPE = "\x00ESCAPED_PIPE\x00"
            inner_safe = inner.replace(r"\|", ESCAPE)
            cols = [c.strip().replace(ESCAPE, "|") for c in inner_safe.split("|")]
            # 表格列结构: 检查点 | 类型 | 是否必填 | PRD/原型内容 | 是否需要产品补充 | 原因
            # cols 应有 6 列（不含开头编号列）
            if len(cols) < 5:
                continue
            need_supp = cols[4].strip() if len(cols) > 4 else ""
            if need_supp == "否":
                expected_ids.add(f"{elem_id}#{cp_index}")

    # 2. 提取 requirements.md 来源列中引用的所有 ID
    actual_ids = set()
    # AC 行（4 列）: | AC-xx | ... | ... | <来源> |
    # AC 行（5 列）: | AC-xx | ... | ... | ... | <来源> |
    ac_5col = re.compile(
        r"^\|\s*AC-[\w\-]+\s*\|[^\n]+?\|[^\n]+?\|[^\n]+?\|\s*([^|]+)\s*\|\s*$",
        re.MULTILINE,
    )
    ac_6col = re.compile(
        r"^\|\s*AC-[\w\-]+\s*\|[^\n]+?\|[^\n]+?\|[^\n]+?\|[^\n]+?\|\s*([^|]+)\s*\|\s*$",
        re.MULTILINE,
    )

    source_id_pattern = re.compile(r"[CB][A-Z]*\d+#\d+")
    for pattern in (ac_6col, ac_5col):
        for m in pattern.finditer(req_text):
            source_field = m.group(1).strip()
            if source_field in ("—", "-", "来源", ""):
                continue
            for sid in source_id_pattern.findall(source_field):
                actual_ids.add(sid)

    # 3. 对比
    missing_in_req = expected_ids - actual_ids  # analysis 中"需补充=否"但 requirements 没引用
    extra_in_req = actual_ids - expected_ids    # requirements 引用了但 analysis 中没有（或已改为"需补充=是"）

    issues = []
    if missing_in_req:
        sample = sorted(missing_in_req)[:5]
        more = f"...(共 {len(missing_in_req)})" if len(missing_in_req) > 5 else ""
        issues.append(f"analysis 有但 requirements 未引用: {', '.join(sample)}{more}")
    if extra_in_req:
        sample = sorted(extra_in_req)[:5]
        more = f"...(共 {len(extra_in_req)})" if len(extra_in_req) > 5 else ""
        issues.append(f"requirements 引用但 analysis 中无效: {', '.join(sample)}{more}")

    passed = len(missing_in_req) == 0 and len(extra_in_req) == 0
    return {
        "name": "analysis 与 requirements 同步",
        "passed": passed,
        "detail": (
            f"双向一致（{len(expected_ids)} 个需求点全部映射）"
            if passed
            else "; ".join(issues)
        ),
        "stats": {
            "analysis_expected": len(expected_ids),
            "requirements_actual": len(actual_ids),
            "missing_in_req": len(missing_in_req),
            "extra_in_req": len(extra_in_req),
        },
        "issues": {
            "missing_in_req": sorted(missing_in_req)[:20] if missing_in_req else None,
            "extra_in_req": sorted(extra_in_req)[:20] if extra_in_req else None,
        } if not passed else None,
    }


def check_prd_defect_tracking(analysis_path: Path) -> dict:
    """检查 analysis 是否含「测试驱动的 PRD 缺陷修正统计」表 + 哨兵 PRD_DEFECT_TOTAL，
    且哨兵数值与统计表最后一行的"累计"列一致（详见 operational-rules.md §7）。

    规则：
    1. 必须存在 ## 测试驱动的 PRD 缺陷修正统计 章节
    2. 必须存在 <!-- PRD_DEFECT_TOTAL: N --> 哨兵（全文件唯一）
    3. 哨兵 N = 统计表最后一行的「累计」列（第 5 列，索引 4；兼容 5/6 列模板）
    4. 统计表行数 >= 变更日志行数（每次增量必计一笔；首次填 0 也算一行）
    """
    if not analysis_path.exists():
        return {"name": "PRD 缺陷修正追踪一致性", "passed": False,
                "detail": f"analysis 文件不存在: {analysis_path}"}

    text = analysis_path.read_text(encoding="utf-8")
    issues = []

    if "## 测试驱动的 PRD 缺陷修正统计" not in text:
        return {"name": "PRD 缺陷修正追踪一致性", "passed": False,
                "detail": "缺少「## 测试驱动的 PRD 缺陷修正统计」章节（模板已预置；老 analysis 需按 operational-rules §7 老 analysis 升级路径补建）"}

    sentinel_pattern = re.compile(r"<!--\s*PRD_DEFECT_TOTAL:\s*(\d+)\s*-->")
    sentinels = sentinel_pattern.findall(text)
    if len(sentinels) == 0:
        issues.append("缺少 <!-- PRD_DEFECT_TOTAL: N --> 哨兵")
    elif len(sentinels) > 1:
        issues.append(f"哨兵 PRD_DEFECT_TOTAL 出现 {len(sentinels)} 次（应全文件唯一）")

    def _data_rows(section_text):
        rows = []
        for line in section_text.splitlines():
            line = line.strip()
            if not line.startswith("|") or set(line) <= {"|", "-", " ", ":"}:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and "更新日期" in cells[0]:
                continue
            if len(cells) >= 5:
                rows.append(cells)
        return rows

    section_match = re.search(r"##\s*测试驱动的 PRD 缺陷修正统计.*?(?=^##\s|\Z)",
                              text, re.MULTILINE | re.DOTALL)
    table_rows = _data_rows(section_match.group(0)) if section_match else []
    if not table_rows:
        issues.append("统计表无数据行（应至少有「首次分析」行）")

    if sentinels and table_rows:
        try:
            if int(sentinels[0]) != int(table_rows[-1][4]):
                issues.append(f"哨兵 PRD_DEFECT_TOTAL={sentinels[0]} 与统计表最后一行累计={table_rows[-1][4]} 不一致")
        except (ValueError, IndexError) as e:
            issues.append(f"无法解析哨兵或累计列数值（{e}）；请确认统计表第 5 列为整数")

    changelog_match = re.search(r"##\s*变更日志.*?(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    if changelog_match:
        cl_rows = len(_data_rows(changelog_match.group(0)))
        if cl_rows > 0 and len(table_rows) < cl_rows:
            issues.append(f"变更日志有 {cl_rows} 行但统计表只有 {len(table_rows)} 行（每次 PRD 增量必须在统计表追加一行；首次填 0 也算一行）")

    return {"name": "PRD 缺陷修正追踪一致性", "passed": len(issues) == 0,
            "detail": "; ".join(issues) if issues else f"双向一致（统计表 {len(table_rows)} 行；累计={sentinels[0] if sentinels else '?'}）"}


def check_no_temp_files(analysis_path: Path) -> dict:
    """检查 analysis 同目录是否残留 _tmp_* 中转文件（阶段一收尾即清，
    详见 operational-rules.md §1.1 + §5.3.1）。"""
    if not analysis_path.exists():
        return {"name": "临时文件残留检查", "passed": True, "detail": "analysis 路径不存在，跳过"}
    leftover = []
    for f in analysis_path.parent.iterdir():
        name = f.name.lower()
        if name.startswith("_tmp_") or name.endswith(".bak") or f.suffix == ".pyc":
            leftover.append(f.name)
    return {"name": "临时文件残留检查", "passed": len(leftover) == 0,
            "detail": "无残留" if not leftover else f"发现残留 {len(leftover)} 个：{', '.join(leftover[:5])}{'...' if len(leftover) > 5 else ''}（跑 cleanup-temp.py --apply 清理）"}


# AC 5 列行：| AC-ID | 验收标准 | 类型 | 断言 | 来源 |
_AC_5COL = re.compile(
    r"^\|\s*(AC-[\w\-]+)\s*\|([^\n]+?)\|([^\n]+?)\|([^\n]+?)\|([^\n]+?)\|\s*$",
    re.MULTILINE,
)

# 断言化试金石：模糊词黑名单（克制）+ 具体锚点豁免
VAGUE_WORDS = ["正确", "正常", "符合预期", "符合要求", "无误", "友好",
               "合理", "适当", "恰当", "清晰", "流畅", "良好", "准确"]
CONCRETE_ANCHOR = re.compile(
    r"[「」『』“”\"']"           # 引号字面文案
    r"|\d"                        # 数字
    r"|/[A-Za-z]"                 # 路由 /login
    r"|启用|禁用|可见|隐藏|展开|收起|置灰|高亮|选中|勾选|"
    r"跳转|toast|Toast|弹窗|显示|消失|出现|true|false"
    r"|[=<>≥≤]"                   # 比较/赋值符
)


def check_ac_criteria_nonempty(text: str) -> dict:
    """AC「验收标准」列（第 2 列）非空（空字段硬扫，硬 fail）。"""
    section = extract_chapter(text, "五", "六")
    if not section:
        return {"name": "AC 验收标准列非空", "passed": True, "detail": "未找到「五、验收标准」章节"}
    empties = []
    for m in _AC_5COL.finditer(section):
        aid, crit = m.group(1).strip(), m.group(2).strip()
        if crit == "验收标准":  # 跳表头
            continue
        if crit in ("", "—", "-"):
            empties.append(aid)
    return {
        "name": "AC 验收标准列非空",
        "passed": len(empties) == 0,
        "detail": "全部 AC 验收标准列非空" if not empties
                  else f"以下 AC 验收标准列为空：{', '.join(empties[:8])}" + (f" …(共{len(empties)})" if len(empties) > 8 else ""),
        "issues": empties if empties else None,
    }


def check_ac_assertion_concreteness(text: str) -> dict:
    """断言化试金石（warn）：AC 断言列若只有模糊词、无任何具体锚点 → 疑似填不出
    具体值，应改具体或就地标缺口。warn 级，不卡交付，提示人工/agent 复核。"""
    section = extract_chapter(text, "五", "六")
    if not section:
        return {"name": "AC 断言具体性(可断言试金石)", "passed": True, "severity": "warn",
                "detail": "未找到「五、验收标准」章节"}
    suspects = []
    for m in _AC_5COL.finditer(section):
        aid, assertion = m.group(1).strip(), m.group(4).strip()
        if assertion in ("断言", ""):
            continue
        has_vague = any(w in assertion for w in VAGUE_WORDS)
        has_anchor = bool(CONCRETE_ANCHOR.search(assertion))
        if has_vague and not has_anchor:
            suspects.append((aid, assertion[:40]))
    return {
        "name": "AC 断言具体性(可断言试金石)",
        "passed": len(suspects) == 0,
        "severity": "warn",
        "detail": "全部 AC 断言含具体值" if not suspects
                  else f"⚠️ {len(suspects)} 条断言疑似只有模糊词（应改具体值或标缺口）："
                       + "; ".join(f"{a}「{s}」" for a, s in suspects[:5]),
        "issues": [{"ac_id": a, "assertion": s} for a, s in suspects] if suspects else None,
    }


# analysis 第五章章节号自指黑名单：填本分析文档/需求文档的章节号都视为自指错误
_SELFREF_CHAPTERS = {"一", "二", "三", "四", "五", "六", "七", "八", "九", "十"}


def check_analysis_pending_location(analysis_path: Path) -> dict:
    """第五章「待确认事项汇总」的「PRD 位置」列禁填本文档章节号（warn）。

    历史问题：旧模板该列名为「章节」、语义未定义，agent 普遍填成本分析文档的
    章节号（尤其"五"——待确认事项汇总本身就是第五章，自指等于没填），产品看了
    无法定位去补哪段 PRD。正确应填 PRD 功能点/章节号（如 §3.7 口语能力图谱 C11）。

    兼容新旧表头：定位含「PRD 位置」或「章节」的列；对该列每个单元格取首段
    （按 / ／ 切分），若首段是纯中文章节号（一~十）→ 标 suspect。warn 级。
    """
    if not analysis_path.exists():
        return {"name": "第五章 PRD 位置非自指章节号", "passed": True, "severity": "warn",
                "detail": "analysis 路径不存在，跳过"}
    analysis_text = analysis_path.read_text(encoding="utf-8")
    section = extract_chapter(analysis_text, "五", "六")
    if not section:
        return {"name": "第五章 PRD 位置非自指章节号", "passed": True, "severity": "warn",
                "detail": "未找到「五、待确认事项汇总」章节"}

    # 解析表格：找表头列索引（PRD 位置 / 章节），再扫数据行该列
    loc_idx = None
    suspects = []  # (行号标识, 单元格值)
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if set(s) <= {"|", "-", " ", ":"}:  # 分隔行
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if loc_idx is None:
            # 表头行：定位列
            for i, c in enumerate(cells):
                if "PRD 位置" in c or "PRD位置" in c or c == "章节":
                    loc_idx = i
                    break
            continue  # 表头行不当数据
        # 数据行
        if loc_idx is None or loc_idx >= len(cells):
            continue
        row_id = cells[0] if cells else "?"
        loc = cells[loc_idx]
        head = re.split(r"[/／]", loc)[0].strip()
        if head in _SELFREF_CHAPTERS:
            suspects.append((row_id, loc[:30]))

    if loc_idx is None:
        return {"name": "第五章 PRD 位置非自指章节号", "passed": True, "severity": "warn",
                "detail": "未识别到「PRD 位置」/「章节」列，跳过"}
    return {
        "name": "第五章 PRD 位置非自指章节号",
        "passed": len(suspects) == 0,
        "severity": "warn",
        "detail": "「PRD 位置」列均指向 PRD 功能点/章节" if not suspects
                  else f"⚠️ {len(suspects)} 行「PRD 位置」填了本文档章节号（应改 PRD 功能点/章节号，如 §3.7 xxx）："
                       + "; ".join(f"#{r}「{v}」" for r, v in suspects[:6]),
        "issues": [{"row": r, "value": v} for r, v in suspects] if suspects else None,
    }


def check_ruleset_version(text: str) -> dict:
    """规则版本一致性（warn，P2-2）：读取产物顶部 <!-- RULESET_VERSION: X --> 戳，
    与当前脚本规则集版本 CURRENT_RULESET_VERSION 比对。缺失或不一致 → warn，
    提示"规则已升级，建议重生成受影响章节"，不卡交付、不翻 verdict。"""
    m = re.search(r"<!--\s*RULESET_VERSION:\s*([\w.\-]+)\s*-->", text)
    if not m:
        return {"name": "规则版本一致性", "passed": False, "severity": "warn",
                "detail": f"产物缺少 <!-- RULESET_VERSION --> 戳（当前规则集 {CURRENT_RULESET_VERSION}）；"
                          f"疑似旧模板生成，建议确认是否需按最新规则重生成受影响章节"}
    stamped = m.group(1)
    if stamped != CURRENT_RULESET_VERSION:
        return {"name": "规则版本一致性", "passed": False, "severity": "warn",
                "detail": f"产物规则版本 {stamped} ≠ 当前 {CURRENT_RULESET_VERSION}；"
                          f"规则集已升级，建议复核/重生成受影响章节后刷新版本戳"}
    return {"name": "规则版本一致性", "passed": True, "severity": "warn",
            "detail": f"规则版本一致（{stamped}）"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("requirements", help="requirements.md 路径")
    p.add_argument("--analysis", help="可选：requirements-analysis.md 路径，传入则做同步检查")
    p.add_argument("--output", help="JSON 报告输出路径")
    p.add_argument(
        "--markdown",
        action="store_true",
        help="输出可粘贴到 analysis 第三节 3.2 的 md 表格（各项 check 章节/状态/说明；含基础 12 项 + 带 --analysis 时 +4 项同步检查）",
    )
    args = p.parse_args()

    req_path = Path(args.requirements)
    if not req_path.exists():
        print(f"ERROR: file not found: {req_path}", file=sys.stderr)
        return 2

    text = req_path.read_text(encoding="utf-8")
    checks = [
        check_index_table(text),                   # 1
        check_chapters(text),                      # 2
        check_state_machine_yaml(text),            # 3 (含状态闭包)
        check_ac_columns(text),                    # 4
        check_ac_source_column(text),              # 5
        check_ac_id_format(text),                  # 6 (含唯一性)
        check_ac_assertion_completeness(text),     # 7
        check_pending_confirmation_consistency(text),  # 8 (新增)
        check_error_codes(text),                   # 9
        check_fuzzy_terms(text),                   # 10
        check_ac_criteria_nonempty(text),          # 14 (空字段硬扫，硬 fail)
        check_ac_assertion_concreteness(text),     # 15 (断言化试金石，warn)
        check_ruleset_version(text),               # 17 (规则版本一致性，warn，P2-2)
    ]

    # 可选：与 analysis 同步检查
    if args.analysis:
        analysis_p = Path(args.analysis)
        checks.append(check_analysis_sync(text, analysis_p))      # 11
        checks.append(check_prd_defect_tracking(analysis_p))      # 12 (PRD 增量更新追踪，operational-rules §7)
        checks.append(check_no_temp_files(analysis_p))            # 13 (临时文件残留，§1.1/§5.3.1)
        checks.append(check_analysis_pending_location(analysis_p))  # 16 (第五章 PRD 位置禁自指章节号，warn)

    # warn 级 check（severity=warn）不翻 verdict、不影响退出码，只提示复核
    fails = [c for c in checks if not c["passed"] and c.get("severity") != "warn"]
    warns = [c for c in checks if not c["passed"] and c.get("severity") == "warn"]
    report = {
        "file": str(req_path),
        "total_checks": len(checks),
        "passed": len([c for c in checks if c["passed"]]),
        "failed": len(fails),
        "warnings": len(warns),
        "verdict": "PASS" if not fails else "FAIL",
        "checks": checks,
    }
    # 供 __main__ 的 token 子阶段打点用业务化 action（结论/通过数/警告数）
    globals()["_PHASE_ACTION"] = (
        f"validate {report['verdict']} {report['passed']}/{report['total_checks']} warn{report['warnings']}"
    )

    # markdown 模式：输出可粘贴的 md 表格
    if args.markdown:
        md_lines = [
            "### 3.2 各章节诊断（validate-requirements.py 输出）",
            "",
            f"- 脚本：`validate-requirements.py`",
            f"- 退出码：{0 if report['verdict'] == 'PASS' else 1}",
            f"- 结论：**{report['verdict']}**（通过 {report['passed']}/{report['total_checks']}，警告 {report['warnings']}）",
            "",
            "| # | 检查项 | 状态 | 说明 |",
            "|---|--------|------|------|",
        ]
        for i, c in enumerate(checks, 1):
            if c["passed"]:
                status = "✅ PASS"
            elif c.get("severity") == "warn":
                status = "⚠️ WARN"
            else:
                status = "❌ FAIL"
            # 截断 detail 防止表格列过宽
            detail = c["detail"].replace("\n", " ").replace("|", "\\|")
            if len(detail) > 200:
                detail = detail[:197] + "..."
            md_lines.append(f"| {i} | {c['name']} | {status} | {detail} |")
        md_lines.append("")
        print("\n".join(md_lines))
        return 1 if fails else 0

    output_json = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_json)

    print(f"\n--- Summary ---\n  Verdict: {report['verdict']}\n  Passed: {report['passed']}/{report['total_checks']}  Warnings: {report['warnings']}", file=sys.stderr)
    for c in fails:
        print(f"  FAIL: {c['name']} - {c['detail']}", file=sys.stderr)
    for c in warns:
        print(f"  WARN: {c['name']} - {c['detail']}", file=sys.stderr)

    return 1 if fails else 0


if __name__ == "__main__":
    _rc = 1
    try:
        _rc = main()
    finally:
        try:
            import os as _os
            sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
            import _token_phase
            _token_phase.emit("generate/verify", _rc,
                              action="交叉检查+修复+校验 " + (globals().get("_PHASE_ACTION") or ("rc=%d" % _rc)))
        except Exception:
            pass
    sys.exit(_rc)
