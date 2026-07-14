"""
count-coverage.py — 统计 requirements-analysis.md 的断言覆盖率

扫描 analysis.md 中所有元素的检查点，统计：
  - 元素总数
  - 检查点总数
  - 需补充数（需补充=是）
  - 已覆盖数（需补充=否 + 不适用）
  - 覆盖率

可用于自动填充到 analysis.md 顶部的「断言覆盖统计」位置。

用法:
    python count-coverage.py --analysis requirements-analysis.md
    python count-coverage.py --analysis ... --output stats.json
    python count-coverage.py --analysis ... --markdown   # 输出可粘贴的 md 表格

退出码:
    0  统计完成
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


def parse_element_heading(line: str) -> dict | None:
    """解析单个元素标题行: #### {id}. {name}（归类：xxx）｜需补充：是/否[, ...] """
    m = re.match(r"^####\s+([A-Za-z]{0,3}[\-]?\d+)\.?\s*(.+)$", line)
    if not m:
        return None
    element_id = m.group(1).strip()
    rest = m.group(2).strip()

    # 提取 name (在第一个 "（归类" 或 "｜" 前)
    name = rest
    cls_idx = rest.find("（归类")
    pipe_idx = rest.find("｜")
    cut_idx = -1
    if cls_idx >= 0 and pipe_idx >= 0:
        cut_idx = min(cls_idx, pipe_idx)
    elif cls_idx >= 0:
        cut_idx = cls_idx
    elif pipe_idx >= 0:
        cut_idx = pipe_idx
    if cut_idx > 0:
        name = rest[:cut_idx].strip()

    # 提取 needs_supplement: 优先看 ｜需补充：是/否，没有则默认 "否"（业务规则不带此字段视为已覆盖）
    needs = "否"
    supp_match = re.search(r"需补充[：:]\s*[*`\s]*([是否])", rest)
    if supp_match:
        needs = supp_match.group(1)
    elif "｜" in rest:
        needs = "未知"  # 有｜但无明确 是/否

    return {"id": element_id, "name": name, "needs_supplement": needs}


def count_elements(text: str) -> dict:
    """逐行扫描 #### 元素标题。"""
    elements = []
    for line in text.split("\n"):
        if line.startswith("####"):
            parsed = parse_element_heading(line)
            if parsed:
                elements.append(parsed)
    return {
        "total": len(elements),
        "needs_supp_yes": sum(1 for e in elements if e["needs_supplement"] == "是"),
        "needs_supp_no": sum(1 for e in elements if e["needs_supplement"] == "否"),
        "elements": elements,
    }


def count_checkpoints(text: str) -> dict:
    """统计所有元素 section 内的检查点（按"是否需要产品补充"列分类）。

    严格限定在 #### 元素标题之后的表格行，避免误把 PRD 自检表、缺陷汇总表等
    其他表格的行也当成检查点。section 边界为下一个 #### 元素标题或下一个
    一级/二级标题（## 或 #）。

    使用"行级匹配 + 转义还原"逻辑，正确处理 markdown 表格内的 `\\|`（PRD 内容含 `||` 字面）。
    """
    # 行级匹配：以 | 数字 | 开头的表格行，不再用复杂的列分隔正则
    table_row_pattern = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$", re.MULTILINE)
    total = supp_yes = supp_no = supp_dash = supp_other = 0
    other_locations = []  # 记录"解析异常"的具体位置
    empty_required_items = []  # 必填(是)检查点但"PRD/原型内容"列为空（空字段硬扫）

    # 找所有 #### 元素标题位置，建立 (start, end) 区段
    lines = text.split("\n")
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    element_ranges = []
    last_start = None
    last_eid = None
    for i, line in enumerate(lines):
        # 元素 section 结束于下一个 #### 元素 或 下一个 ## / # 章节
        is_section_break = (
            line.startswith("####") and parse_element_heading(line)
        ) or (
            line.startswith("# ") or line.startswith("## ")
        )
        if is_section_break and last_start is not None:
            element_ranges.append((last_start, line_offsets[i], last_eid))
            last_start = None

        if line.startswith("####") and parse_element_heading(line):
            last_start = line_offsets[i + 1]
            last_eid = parse_element_heading(line)["id"]

    if last_start is not None:
        element_ranges.append((last_start, len(text), last_eid))

    # 在每个 element section 内找表格行
    for start, end, eid in element_ranges:
        section = text[start:end]
        # 在 section 内部追踪行号，便于报"解析异常"的具体位置
        section_start_line = text[:start].count("\n") + 1
        for m in table_row_pattern.finditer(section):
            cp_index = m.group(1).strip()
            inner = m.group(2)
            # 转义还原：把 \| 替换为占位符，分割后再还原
            ESCAPE = "\x00ESCAPED_PIPE\x00"
            inner_safe = inner.replace(r"\|", ESCAPE)
            cols = [c.strip().replace(ESCAPE, "|") for c in inner_safe.split("|")]
            # 表格列结构: 检查点 | 类型 | 是否必填 | PRD/原型内容 | 是否需要产品补充 | 原因
            # cols 应有 6 列
            if len(cols) < 5:
                continue
            checkpoint = cols[0]
            if checkpoint == "检查点" or checkpoint.startswith("---") or checkpoint.startswith(":"):
                continue
            need_supp = cols[4] if len(cols) > 4 else ""
            # 容错：去掉 markdown 强调修饰（**是** / `是` / *否* / 全角空格）再判定
            need_supp = re.sub(r"[*`~_\s\u3000]", "", need_supp)
            # 空字段硬扫：必填(是) 但 "PRD/原型内容"（cols[3]）为空 → 漏填缺口
            is_required = re.sub(r"[*`~_\s\u3000]", "", cols[2] if len(cols) > 2 else "") == "是"
            prd_content = (cols[3] if len(cols) > 3 else "").strip()
            if is_required and prd_content in ("", "—", "-", "–"):
                empty_required_items.append(f"{eid}#{cp_index}")
            # 计算这一行在原文档中的行号
            row_line_in_section = section[:m.start()].count("\n")
            absolute_line = section_start_line + row_line_in_section
            total += 1
            if need_supp == "是":
                supp_yes += 1
            elif need_supp == "否":
                supp_no += 1
            elif need_supp in ("—", "-", "–"):
                supp_dash += 1
            else:
                supp_other += 1
                other_locations.append({
                    "line": absolute_line,
                    "checkpoint": checkpoint[:40],
                    "raw_value": need_supp,
                })

    return {
        "total_checkpoints": total,
        "needs_supplement_yes": supp_yes,
        "needs_supplement_no": supp_no,
        "needs_supplement_dash": supp_dash,
        "needs_supplement_other": supp_other,
        "other_locations": other_locations,
        "empty_required_content": len(empty_required_items),
        "empty_required_items": empty_required_items,
        "covered": supp_no + supp_dash,
        "coverage_rate": round((supp_no + supp_dash) / total, 4) if total else 0.0,
    }


# 通用断言库的 16 类元素归类（精确名称）
CANONICAL_TYPES = {
    1: "上传/导入", 2: "纯文本输入", 3: "提交", 4: "触发",
    5: "新增/编辑", 6: "删除", 7: "列表", 8: "搜索",
    9: "选择", 10: "开关", 11: "富文本输入", 12: "日期/时间选择",
    13: "弹窗/抽屉", 14: "下载/导出", 15: "Tab/标签页", 16: "详情/查看",
}


def _bad_type_reason(label: str) -> "str | None":
    """归类名不合法时返回原因；合法（16 类精确名 / BR / 未归类）返回 None。"""
    label = (label or "").strip()
    if not label or label in ("—", "-", "–", "/", "N/A") or "未归类" in label or label.upper().startswith("BR"):
        return None
    nm = re.match(r"^\s*(\d+)\s*[.\．、]\s*(.+)$", label)
    if not nm:
        return "无编号前缀，且非 BR/未归类"
    num = int(nm.group(1)); name = nm.group(2).strip()
    if num not in CANONICAL_TYPES:
        return f"编号 {num} 不在 1~16"
    if CANONICAL_TYPES[num] not in name and name not in CANONICAL_TYPES[num]:
        return f"编号 {num} 应为「{CANONICAL_TYPES[num]}」，实写「{name}」"
    return None


def _prefix_cls_mismatch(eid: str, label: str) -> "str | None":
    """编号前缀 ↔ 归类语义一致性：
    C = UI 可交互元素（归类必须是 16 类之一）；BR/U = 业务规则/未归类（不占 C 号）。
    C 编号却标「未归类 / BR / —」→ 语义错配，应改用 BR 或 U 编号。"""
    pm = re.match(r"^\s*([A-Za-z]+)", eid or "")
    if not pm:
        return None
    label = (label or "").strip()
    unclassified = ("未归类" in label) or label.upper().startswith("BR") or label in ("—", "-", "–", "")
    if pm.group(1).upper() == "C" and unclassified:
        return "C 编号(UI 可交互元素)却标未归类/BR/—，应改用 BR 或 U 编号"
    return None


def check_classification_labels(text: str) -> dict:
    """校验归类——①归类名是否 16 类精确名 ②编号前缀与归类语义是否自洽。
    同时扫【明细 #### 标题】和【速查表归类列】。
    """
    bad = []
    lines = text.split("\n")
    # ① 明细元素标题：#### {id}. xxx（归类：yyy）
    for i, line in enumerate(lines, start=1):
        if not line.startswith("####"):
            continue
        idm = re.match(r"^####\s+([A-Za-z]{1,3}\d+)", line)
        m = re.search(r"（归类[：:]\s*(.+?)）", line)
        if not m:
            continue
        label = m.group(1).strip()
        eid = idm.group(1) if idm else ""
        r1 = _bad_type_reason(label)
        if r1:
            bad.append({"line": i, "where": "明细标题", "label": label, "reason": r1})
        r2 = _prefix_cls_mismatch(eid, label)
        if r2:
            bad.append({"line": i, "where": f"明细 {eid}", "label": label, "reason": r2})
    # ② 速查表「归类类型」列：| 编号 | 名称 | 归类类型 | 检查点数 | 需补充数 | 模块 |
    in_qr = False
    for i, line in enumerate(lines, start=1):
        if line.startswith("### "):
            in_qr = "元素编号速查表" in line
            continue
        if line.startswith("## "):
            in_qr = False
            continue
        if in_qr and re.match(r"^\|\s*(?:C\d+|BR\d+|U\d+)\b", line):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) >= 3:
                eid, label = cols[0], cols[2]
                r1 = _bad_type_reason(label)
                if r1:
                    bad.append({"line": i, "where": f"速查表 {eid}", "label": label, "reason": r1})
                r2 = _prefix_cls_mismatch(eid, label)
                if r2:
                    bad.append({"line": i, "where": f"速查表 {eid}", "label": label, "reason": r2})
    return {"ok": not bad, "bad_labels": bad}


def check_quickref_table(text: str, actual_element_count: int, actual_needs_supp: int | None = None) -> dict:
    """检查"元素编号速查表"是否存在且行数与实际元素数一致。

    速查表结构：
        ### 元素编号速查表
        ...
        | 编号 | 元素/业务规则名称 | 归类类型 | 检查点数 | 需补充数 | 模块归属 |

    返回：
        {
            "exists": bool,
            "row_count": int,             # 速查表中实际元素行数
            "actual_count": int,          # 实际 #### 元素数量
            "match": bool,                # 行数是否匹配
            "warning": str or None
        }
    """
    has_quickref = "元素编号速查表" in text
    if not has_quickref:
        return {
            "exists": False,
            "row_count": 0,
            "actual_count": actual_element_count,
            "match": False,
            "warning": "缺少「元素编号速查表」章节（阶段一交付前清单要求必填）",
        }

    # 提取速查表区段（从"元素编号速查表"开始，到下一个 ### 标题结束）
    qr_match = re.search(
        r"###\s*元素编号速查表(.*?)(?=\n###\s|\n##\s|\Z)",
        text,
        re.DOTALL,
    )
    if not qr_match:
        return {
            "exists": True,
            "row_count": 0,
            "actual_count": actual_element_count,
            "match": False,
            "warning": "找到「元素编号速查表」标题但无法提取章节内容",
        }
    qr_section = qr_match.group(1)

    # 数表格行 + 同时累加"需补充数"列：| 编号 | 名称 | 归类 | 检查点数 | 需补充数 | 模块 |
    row_pattern = re.compile(r"^\|\s*(?:C\d+|BR\d+|US\-?\d+|U\d+)\b.*\|\s*$", re.MULTILINE)
    actual_rows = [m.group(0) for m in row_pattern.finditer(qr_section)]
    row_count = len(actual_rows)

    # 累加速查表"需补充数"列（第 5 个数据列）
    qr_supp_sum = 0
    qr_supp_parsed = True
    for row in actual_rows:
        cols = [c.strip() for c in row.strip().strip("|").split("|")]
        # cols: [编号, 名称, 归类, 检查点数, 需补充数, 模块]
        if len(cols) >= 5:
            cell = re.sub(r"[*`~_\s\u3000]", "", cols[4])
            if cell.isdigit():
                qr_supp_sum += int(cell)
            else:
                qr_supp_parsed = False
        else:
            qr_supp_parsed = False

    match = (row_count == actual_element_count)
    warnings = []
    if not match:
        diff = actual_element_count - row_count
        if diff > 0:
            warnings.append(f"速查表少 {diff} 行（实际 {actual_element_count} 个元素，速查表只列了 {row_count} 行）")
        else:
            warnings.append(f"速查表多 {-diff} 行（实际 {actual_element_count} 个元素，速查表列了 {row_count} 行）")

    supp_match = None
    if actual_needs_supp is not None and qr_supp_parsed:
        supp_match = (qr_supp_sum == actual_needs_supp)
        if not supp_match:
            warnings.append(
                f"速查表「需补充数」列合计={qr_supp_sum}，与明细实际「需补充=是」总数={actual_needs_supp} 不一致"
            )

    return {
        "exists": True,
        "row_count": row_count,
        "actual_count": actual_element_count,
        "match": match,
        "quickref_supp_sum": qr_supp_sum if qr_supp_parsed else None,
        "actual_needs_supp": actual_needs_supp,
        "supp_match": supp_match,
        "warning": "；".join(warnings) if warnings else None,
    }


def check_element_integrity(text: str) -> dict:
    """逐元素校验：① 检查点编号连续(1..N 无断档) ② 头部「需补充/待补充」与表格行自洽。"""
    issues = []
    lines = text.split("\n")
    cur = None

    def flush(c):
        if not c:
            return
        idxs = [r[0] for r in c["rows"]]
        if idxs:
            missing = [n for n in range(1, max(idxs) + 1) if n not in idxs]
            if missing:
                issues.append({"id": c["id"], "line": c["line"],
                               "reason": f"检查点编号断档：缺 {missing}（现有 {idxs}）"
                                         f"。修复：非必填检查点省略后，须把保留项重新编号为 1..N 连续，"
                                         f"不要沿用通用断言库的原始编号"})
        has_yes = any(s == "是" for _, s in c["rows"])
        if c["needs"] == "是" and not has_yes:
            issues.append({"id": c["id"], "line": c["line"],
                           "reason": "头部「需补充：是」但表格无任何「需补充=是」行"})
        if c["needs"] == "否" and has_yes:
            issues.append({"id": c["id"], "line": c["line"],
                           "reason": "头部「需补充：否」但表格存在「需补充=是」行"})
        row_supp = {i: s for i, s in c["rows"]}
        for p in c["pending"]:
            if row_supp.get(p) != "是":
                issues.append({"id": c["id"], "line": c["line"],
                               "reason": f"头部「待补充：#{p}」但该行需补充≠是（实际 {row_supp.get(p, '不存在')}）"})

    for i, line in enumerate(lines, start=1):
        if line.startswith("####"):
            flush(cur); cur = None
            idm = re.match(r"^####\s+([A-Za-z]{1,3}\d+)", line)
            if idm:
                needs = "否"
                sm = re.search(r"需补充[：:]\s*[*`\s]*([是否])", line)
                if sm:
                    needs = sm.group(1)
                pend = set()
                if "待补充" in line:
                    pend = set(int(x) for x in re.findall(r"#(\d+)", line.split("待补充", 1)[1]))
                cur = {"id": idm.group(1), "line": i, "needs": needs, "pending": pend, "rows": []}
            continue
        if line.startswith("## ") or line.startswith("# "):
            flush(cur); cur = None; continue
        if cur is not None:
            rm = re.match(r"^\|\s*(\d+)\s*\|(.+)\|\s*$", line)
            if rm:
                cols = [c.strip() for c in rm.group(2).split("|")]
                supp = re.sub(r"[*`~_\s\u3000]", "", cols[4]) if len(cols) >= 5 else ""
                cur["rows"].append((int(rm.group(1)), supp))
    flush(cur)
    return {"ok": not issues, "issues": issues}


def check_type_coverage(text: str) -> dict:
    """标准 B：每个元素必须覆盖其归类类型的全部「必填(是)」检查点（非必填可在不适用时省略）。
    用「必填=是 行数 >= 该类型必填检查点数」做代理校验，揪出漏掉必填项的元素。"""
    # 各 16 类「是否必填=是」的检查点数（统计自 common-assertion-checklist.md）
    REQ = {1:4, 2:3, 3:5, 4:1, 5:6, 6:4, 7:5, 8:6, 9:3, 10:2, 11:4, 12:3, 13:3, 14:6, 15:2, 16:3}
    issues = []
    lines = text.split("\n")
    cur = None

    def flush(c):
        if not c or c["type"] is None:
            return
        need = REQ.get(c["type"])
        if need is not None and c["req"] < need:
            issues.append({"id": c["id"], "line": c["line"], "type": c["type"],
                           "reason": f"必填检查点覆盖不足：必填行 {c['req']} < 类型 {c['type']} 应有必填 {need}（缺 {need - c['req']}）"})

    for i, line in enumerate(lines, start=1):
        if line.startswith("####"):
            flush(cur); cur = None
            idm = re.match(r"^####\s+([A-Za-z]{1,3}\d+)", line)
            if idm:
                m = re.search(r"（归类[：:]\s*(.+?)）", line)
                numm = re.match(r"^\s*(\d+)", m.group(1)) if m else None
                cur = {"id": idm.group(1), "line": i,
                       "type": int(numm.group(1)) if numm else None, "req": 0}
            continue
        if line.startswith("## ") or line.startswith("# "):
            flush(cur); cur = None; continue
        if cur is not None:
            rm = re.match(r"^\|\s*\d+\s*\|(.+)\|\s*$", line)
            if rm:
                cols = [c.strip() for c in rm.group(1).split("|")]
                if len(cols) >= 3 and re.sub(r"[*`\s\u3000]", "", cols[2]) == "是":
                    cur["req"] += 1
    flush(cur)
    return {"ok": not issues, "issues": issues}


# 信息密集只读元素「字段级数据规则定义」巡检关键词（避开通用检查点高频词如"排序规则"）
FIELD_DEF_KEYWORDS = ["口径", "计算", "数据来源", "取值范围", "统计范围", "色阶",
                      "阈值", "公式", "小数位", "含义", "枚举值", "单位"]


def check_field_definition_audit(text: str) -> dict:
    """巡检 warn：归类为 7.列表 / 16.详情/查看（含图表）的元素，若其 section 内
    不含任何"数据规则定义"信号词（口径/计算/数据来源/取值范围/色阶/阈值…），
    提示疑似漏了字段级定义核对。warn 级——靠关键词，可能误报/漏报，仅提示人工复核。"""
    suspects = []
    lines = text.split("\n")
    cur = None      # {"id","line","type"}
    cur_start = None

    def flush(c, seg):
        if not c or c["type"] not in (7, 16):
            return
        if not any(k in seg for k in FIELD_DEF_KEYWORDS):
            suspects.append({"id": c["id"], "line": c["line"], "type": c["type"]})

    for idx, line in enumerate(lines):
        if line.startswith("####"):
            if cur is not None:
                flush(cur, "\n".join(lines[cur_start:idx]))
            cur = None; cur_start = None
            idm = re.match(r"^####\s+([A-Za-z]{1,3}\d+)", line)
            if idm:
                m = re.search(r"（归类[：:]\s*(.+?)）", line)
                numm = re.match(r"^\s*(\d+)", m.group(1)) if m else None
                cur = {"id": idm.group(1), "line": idx + 1,
                       "type": int(numm.group(1)) if numm else None}
                cur_start = idx
        elif line.startswith("## ") or line.startswith("# "):
            if cur is not None:
                flush(cur, "\n".join(lines[cur_start:idx]))
            cur = None; cur_start = None
    if cur is not None:
        flush(cur, "\n".join(lines[cur_start:]))
    return {"ok": not suspects, "suspects": suspects}


# 可测性巡检信号词（命中→疑似不可测，需分流：改造成可观测/可构造 或 标 🚫 不可测进第四章）
TESTABILITY_SIGNALS = {
    "前置态不可构造": ["下线", "灰度", "后端开关", "开关控制", "暂未实现", "本期不实现", "需后端配置"],
    "断言不可观测": ["不渲染", "不发送"],
    "开放集": ["其它", "其他", "各种", "若干"],
}


def check_testability_audit(text: str) -> dict:
    """巡检 warn：扫元素 section 内检查点文本，含"不可测信号词"（下线/灰度/后端开关/
    不渲染/不发送/其它/各种…）→ 提示疑似不可测，需分流。warn 级，靠关键词，仅提示。"""
    suspects = []
    table_row_pattern = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")
    lines = text.split("\n")
    cur = None  # {"id"}
    in_elem = False
    for idx, line in enumerate(lines):
        if line.startswith("####"):
            idm = re.match(r"^####\s+([A-Za-z]{1,3}\d+)", line)
            cur = idm.group(1) if idm else None
            in_elem = cur is not None
            continue
        if line.startswith("## ") or line.startswith("# "):
            in_elem = False; cur = None
            continue
        if not in_elem or cur is None:
            continue
        m = table_row_pattern.match(line)
        if not m:
            continue
        row_text = m.group(2)
        # 结尾"…等"单独判（避免"等待/等于"误命中）：以 等/等。/等） 结尾的短语
        cats = []
        for cat, kws in TESTABILITY_SIGNALS.items():
            if any(k in row_text for k in kws):
                cats.append(cat)
        if re.search(r"等[。.\s）)|]*$", row_text.strip()):
            cats.append("开放集")
        if cats:
            suspects.append({"id": cur, "line": idx + 1,
                             "cats": sorted(set(cats)), "checkpoint": row_text.split("|")[0].strip()[:30]})
    return {"ok": not suspects, "suspects": suspects}


# 白盒越界信号词（界面看不见的内部量：前后端分工 / 内部匹配键 / 是否调接口 / 后端字段）。
# 命中→疑似把系统/开发视角写进黑盒功能断言，需按 assertion-coverage-checklist「白盒越界识别」分流：
#   ①功能层只留可观测现象 ②取值/参数/是否调接口下沉接口层 ③接口 N/A 则不作功能阻塞。
# warn 级——正则巡检，可能误报/漏报，仅提示人工复核。作用域=元素 section 内的检查点表格行，
# 不扫业务实体结构/来源标注列（那里保留字段名是数据契约的权威记录，见 checklist「作用域」）。
WHITEBOX_SIGNALS = {
    "前后端分工": [
        r"前端不[做重排序分组参与]",
        r"不在前端[重排序分组做参与]",
        r"(排序|渲染)?落点在后端",
        r"前端按.{0,8}(后端)?返回.{0,6}(顺序|渲染)",
        r"按后端返回.{0,6}顺序",
    ],
    "内部匹配键/取值口径": [
        r"按.{0,6}ID\s*[（(]非",
        r"按院校\s*ID\s*匹配",
        r"内部\s*ID(?!\s*匹配以)",
    ],
    "是否调接口/后端字段": [
        r"是否调用?.{0,8}接口",
        r"调用了.{0,8}接口",
        r"接口(入参|出参|入出参)",
        r"后端字段(?!清晰)",
    ],
}
_WHITEBOX_COMPILED = {cat: [re.compile(p) for p in pats] for cat, pats in WHITEBOX_SIGNALS.items()}


def check_whitebox_audit(text: str) -> dict:
    """巡检 warn：扫元素 section 内检查点文本，含"白盒越界信号词"（前端不重排/按ID匹配/
    是否调接口/后端字段…）→ 提示疑似把界面看不见的内部量写进了功能断言，需按
    assertion-coverage-checklist「白盒越界识别」分流（下沉接口层 / 改可观测等价 / 删）。
    warn 级，靠正则，仅提示不翻退出码。作用域与 testability_audit 相同：只扫元素检查点表格行。"""
    suspects = []
    table_row_pattern = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")
    lines = text.split("\n")
    cur = None
    in_elem = False
    for idx, line in enumerate(lines):
        if line.startswith("####"):
            idm = re.match(r"^####\s+([A-Za-z]{1,3}\d+)", line)
            cur = idm.group(1) if idm else None
            in_elem = cur is not None
            continue
        if line.startswith("## ") or line.startswith("# "):
            in_elem = False; cur = None
            continue
        if not in_elem or cur is None:
            continue
        m = table_row_pattern.match(line)
        if not m:
            continue
        row_text = m.group(2)
        cats = [cat for cat, pats in _WHITEBOX_COMPILED.items() if any(p.search(row_text) for p in pats)]
        if cats:
            suspects.append({"id": cur, "line": idx + 1,
                             "cats": sorted(set(cats)), "checkpoint": row_text.split("|")[0].strip()[:30]})
    return {"ok": not suspects, "suspects": suspects}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--analysis", required=True, help="requirements-analysis.md 路径")
    p.add_argument("--output", help="JSON 报告输出路径")
    p.add_argument("--markdown", action="store_true", help="输出可粘贴的 markdown 表格")
    args = p.parse_args()

    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"ERROR: file not found: {analysis_path}", file=sys.stderr)
        return 2

    text = analysis_path.read_text(encoding="utf-8")
    elements_stats = count_elements(text)
    checkpoint_stats = count_checkpoints(text)
    quickref_stats = check_quickref_table(
        text, elements_stats["total"], checkpoint_stats["needs_supplement_yes"]
    )
    classification_stats = check_classification_labels(text)
    integrity_stats = check_element_integrity(text)
    type_cov_stats = check_type_coverage(text)
    field_audit_stats = check_field_definition_audit(text)
    testability_stats = check_testability_audit(text)
    whitebox_stats = check_whitebox_audit(text)

    report = {
        "file": str(analysis_path),
        "elements": elements_stats,
        "checkpoints": checkpoint_stats,
        "quickref_table": quickref_stats,
        "classification": classification_stats,
        "integrity": integrity_stats,
        "type_coverage": type_cov_stats,
        "field_def_audit": field_audit_stats,
        "testability_audit": testability_stats,
        "whitebox_audit": whitebox_stats,
    }

    if args.markdown:
        cs = checkpoint_stats
        es = elements_stats
        md = (
            "| 指标 | 数值 |\n"
            "|------|------|\n"
            f"| 元素总数 | {es['total']} |\n"
            f"| 检查点总数 | {cs['total_checkpoints']} |\n"
            f"| 需补充数（需补充=是）| {cs['needs_supplement_yes']} |\n"
            f"| 已覆盖数（需补充=否）| {cs['needs_supplement_no']} |\n"
            f"| 不适用数（需补充=—）| {cs['needs_supplement_dash']} |\n"
            f"| 覆盖率 | {cs['coverage_rate']:.1%} |\n"
            f"| 必填检查点内容空（应为 0）| {cs.get('empty_required_content', 0)} |\n"
        )
        print(md)
        return 0

    output_json = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_json)

    cs = checkpoint_stats
    qr = quickref_stats
    print(
        f"\n--- Summary ---\n"
        f"  Elements:           {elements_stats['total']}\n"
        f"  Total checkpoints:  {cs['total_checkpoints']}\n"
        f"  Needs supplement:   {cs['needs_supplement_yes']}\n"
        f"  Covered:            {cs['covered']}\n"
        f"  Coverage rate:      {cs['coverage_rate']:.1%}\n"
        f"  Quickref table:     {'✓ 一致' if qr['match'] else '✗ ' + (qr.get('warning') or '不一致')}",
        file=sys.stderr,
    )
    if qr.get("warning"):
        print(f"\n⚠️  WARNING: {qr['warning']}", file=sys.stderr)
    cls = classification_stats
    if not cls["ok"]:
        print(f"\n⚠️  发现 {len(cls['bad_labels'])} 个归类名不符合 16 类库（禁止自造类名）：", file=sys.stderr)
        for b in cls["bad_labels"][:10]:
            print(f"    行 {b['line']} [{b.get('where','')}]: 「{b['label']}」— {b['reason']}", file=sys.stderr)
        if len(cls["bad_labels"]) > 10:
            print(f"    ... 共 {len(cls['bad_labels'])} 处", file=sys.stderr)
    integ = integrity_stats
    if not integ["ok"]:
        print(f"\n⚠️  发现 {len(integ['issues'])} 个元素完整性问题（编号断档 / 需补充与表格不自洽）：", file=sys.stderr)
        for it in integ["issues"][:20]:
            print(f"    行 {it['line']} [{it['id']}]: {it['reason']}", file=sys.stderr)
        if len(integ["issues"]) > 20:
            print(f"    ... 共 {len(integ['issues'])} 处", file=sys.stderr)
    tc = type_cov_stats
    if not tc["ok"]:
        print(f"\n⚠️  发现 {len(tc['issues'])} 个元素未覆盖类型必填检查点（标准 B）：", file=sys.stderr)
        for it in tc["issues"][:20]:
            print(f"    行 {it['line']} [{it['id']}]: {it['reason']}", file=sys.stderr)
    fa = field_audit_stats
    if not fa["ok"]:
        print(f"\n⚠️  发现 {len(fa['suspects'])} 个 列表/详情类元素疑似漏「字段级数据规则定义核对」（warn，关键词巡检，请人工复核每列/字段的 含义·来源·计算口径·显示规则 是否 PRD 定义）：", file=sys.stderr)
        for s in fa["suspects"][:20]:
            print(f"    行 {s['line']} [{s['id']}] 归类{s['type']}：检查点未现 含义/来源/口径/计算/取值/色阶/阈值 等定义信号词", file=sys.stderr)
    ta = testability_stats
    if not ta["ok"]:
        print(f"\n⚠️  发现 {len(ta['suspects'])} 处检查点疑似不可测（warn，关键词巡检，需分流：改造成可观测/可构造断言 或 标 🚫 不可测进第四章）：", file=sys.stderr)
        for s in ta["suspects"][:20]:
            print(f"    行 {s['line']} [{s['id']}] {'/'.join(s['cats'])}：{s['checkpoint']}", file=sys.stderr)
    wb = whitebox_stats
    if not wb["ok"]:
        print(f"\n⚠️  发现 {len(wb['suspects'])} 处检查点疑似白盒越界（warn，正则巡检，界面看不见的内部量当成了功能断言，需分流：下沉接口层 / 改可观测等价 / 删；接口 N/A 则不作功能阻塞）：", file=sys.stderr)
        for s in wb["suspects"][:20]:
            print(f"    行 {s['line']} [{s['id']}] {'/'.join(s['cats'])}：{s['checkpoint']}", file=sys.stderr)
    if cs.get("needs_supplement_other", 0) > 0:
        print(f"\n⚠️  发现 {cs['needs_supplement_other']} 个解析异常的检查点（'需补充'列既不是 '是/否/—'）：", file=sys.stderr)
        for loc in cs.get("other_locations", [])[:10]:
            print(f"    行 {loc['line']}: {loc['checkpoint']}... | 原值 = {loc['raw_value']!r}", file=sys.stderr)
    if cs.get("empty_required_content", 0) > 0:
        print(f"\n⚠️  发现 {cs['empty_required_content']} 个必填检查点「PRD/原型内容」为空（空字段硬扫，应为 0；填具体值或按试金石标缺口）：", file=sys.stderr)
        for it in cs.get("empty_required_items", [])[:20]:
            print(f"    {it}", file=sys.stderr)
        if len(cs.get("empty_required_items", [])) > 20:
            print(f"    ... 共 {len(cs['empty_required_items'])} 处", file=sys.stderr)
    return 0


if __name__ == "__main__":
    _rc = 1
    try:
        _rc = main()
    finally:
        try:
            import os as _os
            # count-coverage 是阶段一/二共用载体（按同目录 requirements.md 状态分流）：
            #   阶段一（requirements.md 不存在或仍是骨架）→ 打 analyze；
            #   阶段二（requirements.md 已填充、锚点已消费）→ 打 generate/fill。
            _stage2 = False
            if "--analysis" in sys.argv:
                _ai = sys.argv.index("--analysis")
                if _ai + 1 < len(sys.argv):
                    _req = _os.path.join(_os.path.dirname(sys.argv[_ai + 1]), "requirements.md")
                    if _os.path.isfile(_req):
                        try:
                            _txt = open(_req, encoding="utf-8").read()
                            _stage2 = "BEGIN_ACCEPTANCE_CRITERIA" not in _txt  # 锚点已消费=已填充
                        except Exception:
                            _stage2 = False
            if "--analysis" in sys.argv:
                sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
                import _token_phase
                if _stage2:
                    _token_phase.emit("generate/fill", _rc, action="填充 10 章/AC + 覆盖统计")
                else:
                    _token_phase.emit("analyze", _rc, action="PRD自检+断言覆盖+缺陷（阶段一）")
        except Exception:
            pass
    sys.exit(_rc)
