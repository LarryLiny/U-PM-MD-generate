"""
cross-check.py — 第五步覆盖度交叉检查（算法化）

遍历 requirements-analysis.md 的「断言覆盖详情」中所有"需补充=否"的检查点，
逐项在 requirements.md 的 AC 表格中查找匹配。输出未覆盖项 JSON 报告。

用法:
    python cross-check.py --analysis requirements-analysis.md --requirements requirements.md
    python cross-check.py --analysis ... --requirements ... --output report.json
    python cross-check.py --analysis ... --requirements ... --threshold 0.3
    python cross-check.py --analysis ... --requirements ... --markdown   # 输出可粘贴到 analysis 第十节的 md 块

退出码:
    0  完全覆盖
    1  存在未覆盖项（must-fix）
    2  脚本错误（文件不存在等）
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_element_heading(line: str) -> dict | None:
    """解析单个元素标题行: #### {id}. {name}（归类：xxx）｜需补充：是/否"""
    m = re.match(r"^####\s+([A-Za-z]{0,3}[\-]?\d+)\.?\s*(.+)$", line)
    if not m:
        return None
    element_id = m.group(1).strip()
    rest = m.group(2).strip()
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
    return {"id": element_id, "name": name}


def extract_checkpoints_from_analysis(text: str) -> list[dict]:
    """
    从 analysis.md 中提取所有"需补充=否"的检查点。
    每个 checkpoint 含其编号（element_id + checkpoint_index），格式如 "C13#1"。
    """
    checkpoints = []
    # 表格行：| # | 检查点 | 类型 | 是否必填 | PRD/原型内容 | 是否需要产品补充 | 原因 |
    row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*[^|]+?\s*\|\s*[^|]+?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*[^|]+?\s*\|",
        re.MULTILINE,
    )

    # 找所有 #### 元素，确定每个的开始/结束位置（结束于下一个 #### 元素或 ## / # 章节）
    lines = text.split("\n")
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    elements = []
    last_data = None
    for i, line in enumerate(lines):
        is_section_break = (
            line.startswith("####") and parse_element_heading(line)
        ) or (
            line.startswith("# ") or line.startswith("## ")
        )
        if is_section_break and last_data is not None:
            last_data["end_offset"] = line_offsets[i]
            elements.append(last_data)
            last_data = None

        if line.startswith("####"):
            parsed = parse_element_heading(line)
            if parsed:
                last_data = {
                    "id": parsed["id"],
                    "name": parsed["name"],
                    "start_offset": line_offsets[i + 1],
                    "end_offset": None,
                }

    if last_data is not None:
        last_data["end_offset"] = len(text)
        elements.append(last_data)

    for e in elements:
        section = text[e["start_offset"]:e["end_offset"]]
        element_label = f"{e['id']}. {e['name']}"
        for row in row_pattern.finditer(section):
            cp_index = row.group(1).strip()
            checkpoint = row.group(2).strip()
            source = row.group(3).strip()
            need_supp = row.group(4).strip()
            if checkpoint == "检查点" or checkpoint.startswith("---"):
                continue
            # 收集"需补充=否"（必须在 AC 中体现）和"需补充=是"（应在 AC 中标记待产品确认）
            # 跳过"需补充=—"（不适用，无需体现）
            if need_supp in ("否", "是"):
                # 精确 ID（如 C13#1），用于来源列匹配
                exact_id = f"{e['id']}#{cp_index}"
                checkpoints.append({
                    "element": element_label,
                    "element_id": e["id"],
                    "cp_index": cp_index,
                    "exact_id": exact_id,
                    "checkpoint": checkpoint,
                    "source": source,
                    "need_supplement": need_supp,
                })
    return checkpoints


def extract_acs_from_requirements(text: str) -> list[dict]:
    """
    从 requirements.md 中提取所有 AC（验收标准）。
    AC 通常以 AC-xx 编号出现在表格中，或作为子标题。

    合法 AC 编号格式：
    - AC-NN-NN（如 AC-01-05）：标准格式
    - AC-NN-NNa（如 AC-01-05a）：补丁后缀（交叉检查后新增 AC 用，单字母后缀）
    - 不支持多层后缀（如 AC-01-05a-i）或含点（如 AC-01-05.1），由 validate-requirements.py 报错

    AC 表格列结构（兼容多种格式）:
    - 5 列：| 规则ID | 规则 | 正向断言 | 反向断言 | 边界值 |
    - 5 列：| AC-ID | 验收标准 | 类型 | 断言 | 来源 |  ← 新增"来源"列
    - 4 列：| AC-ID | 验收标准 | 类型 | 断言 |

    "来源"列含 analysis 中的元素+检查点编号（如 "C13#1" 或 "C13#1, BR04#2"），
    用于精确匹配，无歧义。
    """
    acs = []
    seen = set()

    # 5 列含"来源"格式: | AC-ID | 验收标准 | 类型 | 断言 | 来源 |
    five_col_with_source = re.compile(
        r"^\|\s*(AC-[\w\-\.]+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
        re.MULTILINE,
    )
    for m in five_col_with_source.finditer(text):
        ac_id = m.group(1).strip()
        col2 = m.group(2).strip()
        col3 = m.group(3).strip()
        col4 = m.group(4).strip()
        col5 = m.group(5).strip()
        if not col2 or col2 == "规则" or col2 == "验收标准" or col2.startswith("---"):
            continue
        if ac_id in seen:
            continue
        # 判断是 5 列 AC 表格（验收标准 + 类型 + 断言 + 来源）还是 5 列规则表格（规则 + 正向 + 反向 + 边界）
        # 启发式：col5 形如 "C\d+#\d+" 或 "BR\d+#\d+" 或 "—" 视为来源列
        source_pattern = re.compile(r"^[—\-]$|^([CBRU][A-Z]*\d+#\d+)(\s*[,，]\s*[CBRU][A-Z]*\d+#\d+)*$")
        sources = []
        if source_pattern.match(col5):
            # 5 列含来源格式
            full_rule = " ".join(p for p in [col2, col4] if p and p not in ("—", "-"))
            if col5 not in ("—", "-", ""):
                sources = [s.strip() for s in re.split(r"[,，]", col5) if s.strip()]
        else:
            # 5 列规则格式: 规则 | 正向 | 反向 | 边界
            parts = [col2]
            for p in (col3, col4, col5):
                if p and p not in ("—", "-", ""):
                    parts.append(p)
            full_rule = " ".join(parts)
        acs.append({"id": ac_id, "rule": full_rule, "sources": sources})
        seen.add(ac_id)

    # 4 列 AC 表格: | AC-ID | 验收标准 | 类型 | 断言 |
    four_col_pattern = re.compile(
        r"^\|\s*(AC-[\w\-\.]+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$",
        re.MULTILINE,
    )
    for m in four_col_pattern.finditer(text):
        ac_id = m.group(1).strip()
        col2 = m.group(2).strip()
        col4 = m.group(4).strip()
        if not col2 or col2 == "验收标准" or col2.startswith("---") or ac_id in seen:
            continue
        full_rule = " ".join(p for p in [col2, col4] if p and p not in ("—", "-"))
        acs.append({"id": ac_id, "rule": full_rule, "sources": []})
        seen.add(ac_id)

    # 兜底：表格列数不足 4 列的简化形式（如 | AC-xx | 规则 | ... |）
    short_row_pattern = re.compile(
        r"^\|\s*(AC-[\w\-\.]+)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE
    )
    for m in short_row_pattern.finditer(text):
        ac_id = m.group(1).strip()
        rule = m.group(2).strip()
        if ac_id in seen or not rule or rule == "规则" or rule == "验收标准" or rule.startswith("---"):
            continue
        acs.append({"id": ac_id, "rule": rule, "sources": []})
        seen.add(ac_id)

    # 兜底：AC-xx 作为标题块（## AC-xx 或 ### AC-xx）
    ac_heading_pattern = re.compile(r"^#+\s+(AC-[\w\-\.]+)[：:]?\s*(.*)$", re.MULTILINE)
    for m in ac_heading_pattern.finditer(text):
        ac_id = m.group(1).strip()
        rule = m.group(2).strip()
        if ac_id in seen:
            continue
        acs.append({"id": ac_id, "rule": rule, "sources": []})
        seen.add(ac_id)
    return acs


def tokenize(s: str) -> set[str]:
    """简单中文分词：按字符 + 英文单词。"""
    s = s.lower()
    # 英文/数字单词
    en_tokens = set(re.findall(r"[a-z0-9]+", s))
    # 中文字符（每个字作为一个 token，过滤常见停用词）
    stopwords = set("的了是在和与或及若非不为以及等中或当则否之或者就将是被把对从到无有")
    cn_tokens = {c for c in s if "\u4e00" <= c <= "\u9fff" and c not in stopwords}
    return en_tokens | cn_tokens


def jaccard_similarity(a: str, b: str) -> float:
    """Jaccard 相似度：用于检查点 vs AC 规则文本的模糊匹配。"""
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def overlap_score(a: str, b: str) -> float:
    """重叠系数：min(|交集|/|a|, |交集|/|b|)，对短文本更友好。"""
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    return min(len(inter) / len(sa), len(inter) / len(sb))


def combined_score(a: str, b: str) -> float:
    """综合得分：jaccard 和 overlap 取最大值，兼顾长短文本。"""
    return max(jaccard_similarity(a, b), overlap_score(a, b))


def cross_check(checkpoints: list[dict], acs: list[dict], threshold: float) -> dict:
    """对每个检查点查找对应 AC。

    匹配策略（优先级降序）：
    1. 精确来源匹配：检查点的 exact_id (如 "C13#1") 出现在某个 AC 的 sources 列表中 → 命中
    2. 文本相似度匹配：用 Jaccard + overlap 综合得分，>= threshold 视为命中

    特殊规则：
    - need_supplement=是 的检查点：AC 必须含「待产品确认」标记，否则报缺
    - need_supplement=否 的检查点：精确匹配命中视为高置信，文本匹配命中视为低置信
    """
    missing = []
    edge = []
    covered = []
    pending = []  # need_supp=是 但 AC 缺"待产品确认"标记的项
    edge_threshold = round(threshold * 1.5, 3)

    # 建立 exact_id -> AC 索引（精确来源映射）
    source_index = {}  # exact_id -> [ac_id, ac_id, ...]
    for ac in acs:
        for src in ac.get("sources", []):
            source_index.setdefault(src, []).append(ac["id"])

    for cp in checkpoints:
        # 优先：精确来源匹配
        exact_matches = source_index.get(cp.get("exact_id", ""), [])
        if exact_matches:
            record = {
                "element": cp["element"],
                "checkpoint": cp["checkpoint"],
                "exact_id": cp.get("exact_id"),
                "need_supplement": cp.get("need_supplement", "否"),
                "match_type": "exact_source",
                "matched_acs": exact_matches,
                "best_match_score": 1.0,
            }
            if cp.get("need_supplement") == "是":
                # 待产品确认项需检查 AC 是否含"待产品确认"标记
                ac_lookup = {a["id"]: a for a in acs}
                has_pending_marker = any(
                    "待产品确认" in ac_lookup.get(aid, {}).get("rule", "")
                    for aid in exact_matches
                )
                if has_pending_marker:
                    covered.append(record)
                else:
                    record["reason"] = "待产品确认项需在 AC 中标记「⚠️ 待产品确认」"
                    pending.append(record)
            else:
                covered.append(record)
            continue

        # 兜底：文本相似度匹配
        cp_text = f"{cp['element']} {cp['checkpoint']}"
        best_score = 0.0
        best_ac = None
        for ac in acs:
            ac_text = f"{ac['id']} {ac['rule']}"
            score = combined_score(cp_text, ac_text)
            if score > best_score:
                best_score = score
                best_ac = ac
        record = {
            "element": cp["element"],
            "checkpoint": cp["checkpoint"],
            "exact_id": cp.get("exact_id"),
            "need_supplement": cp.get("need_supplement", "否"),
            "match_type": "fuzzy",
            "best_match_ac": best_ac["id"] if best_ac else None,
            "best_match_score": round(best_score, 3),
        }
        if cp.get("need_supplement") == "是":
            if best_ac and "待产品确认" in best_ac.get("rule", ""):
                covered.append(record)
            else:
                record["reason"] = "待产品确认项需在 AC 中标记「⚠️ 待产品确认」"
                pending.append(record)
        else:
            if best_score < threshold:
                missing.append(record)
            elif best_score < edge_threshold:
                edge.append(record)
                covered.append(record)
            else:
                covered.append(record)

    total = len(checkpoints)
    exact_count = sum(1 for r in covered if r.get("match_type") == "exact_source")
    fuzzy_count = sum(1 for r in covered if r.get("match_type") == "fuzzy")

    # 反向告警：列出无来源的 AC（来源列为空 / 填了 — 或 4 列简化表格）
    # 这些 AC 多半属于 agent 自行总结的"衍生 AC"，需要人工复核是否真属于"纯技术规范"
    ac_without_source = [
        {"id": ac["id"], "rule": ac.get("rule", "")[:80]}
        for ac in acs
        if not ac.get("sources")
    ]

    return {
        "total_checkpoints": total,
        "covered": len(covered),
        "covered_by_exact_source": exact_count,
        "covered_by_fuzzy_match": fuzzy_count,
        "missing": len(missing),
        "pending_confirmation": len(pending),
        "edge_cases": len(edge),
        "coverage_rate": round(len(covered) / total, 3) if total else 0.0,
        "threshold": threshold,
        "edge_threshold": edge_threshold,
        "missing_items": missing,
        "pending_items": pending,
        "edge_items": edge,
        "ac_count": len(acs),
        "ac_with_sources_count": sum(1 for ac in acs if ac.get("sources")),
        "ac_without_source_count": len(ac_without_source),
        "ac_without_source": ac_without_source,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--analysis", required=True, help="requirements-analysis.md 路径")
    p.add_argument("--requirements", required=True, help="requirements.md 路径")
    p.add_argument("--output", help="JSON 报告输出路径（默认打印到 stdout）")
    p.add_argument("--threshold", type=float, default=0.3, help="相似度阈值，默认 0.3")
    p.add_argument(
        "--markdown",
        action="store_true",
        help="输出可粘贴到 analysis 第十节的 md 块（执行过程 + 新增 AC 项 + 最终结果统计三段式）",
    )
    args = p.parse_args()

    analysis_path = Path(args.analysis)
    req_path = Path(args.requirements)

    if not analysis_path.exists():
        print(f"ERROR: analysis file not found: {analysis_path}", file=sys.stderr)
        return 2
    if not req_path.exists():
        print(f"ERROR: requirements file not found: {req_path}", file=sys.stderr)
        return 2

    analysis_text = read_text(analysis_path)
    req_text = read_text(req_path)

    checkpoints = extract_checkpoints_from_analysis(analysis_text)
    acs = extract_acs_from_requirements(req_text)

    if not checkpoints:
        print(
            "WARNING: no checkpoints extracted from analysis.md.\n"
            "  This usually means the analysis.md does not use the standard\n"
            "  '#### {ID}. {name}（归类：x）｜需补充：是/否' element heading format.\n"
            "  This is OK for simplified analysis.md without 「断言覆盖详情」 section.\n"
            "  Skipping cross-check; please review coverage manually.",
            file=sys.stderr,
        )

    report = cross_check(checkpoints, acs, args.threshold)
    report["analysis_file"] = str(analysis_path)
    report["requirements_file"] = str(req_path)

    # markdown 模式：输出可粘贴的三段式 md 块
    if args.markdown:
        md_lines = [
            "## 九、交叉检查结果",
            "",
            "### 9.1 执行过程",
            "",
            f"- 脚本：`cross-check.py`",
            f"- 输入：analysis 检查点 {report['total_checkpoints']} 个 / requirements AC {report['ac_count']} 条（含来源标注 {report['ac_with_sources_count']} 项）",
            f"- 阈值：threshold={report['threshold']}, edge_threshold={report['edge_threshold']}",
            f"- 退出码：{0 if report['missing'] == 0 and report['pending_confirmation'] == 0 else 1}",
            "",
            "### 9.2 本轮新增 / 修正的 AC 项",
            "",
        ]
        if report["missing"] == 0 and report["pending_confirmation"] == 0:
            md_lines.append("| # | 类型 | 元素 | 检查点 | 处理 |")
            md_lines.append("|---|------|------|--------|------|")
            md_lines.append("| — | — | — | — | 本轮无新增 / 修正项（覆盖率 100%）|")
        else:
            md_lines.append("| # | 类型 | 元素 | 检查点 | 处理 |")
            md_lines.append("|---|------|------|--------|------|")
            i = 1
            for item in report["missing_items"]:
                md_lines.append(
                    f"| {i} | missing | {item.get('element', '—')} | {item.get('checkpoint', '—')} | "
                    f"⏳ 待补充 AC（best_match={item.get('best_match_ac', '—')}, score={item.get('best_match_score', 0):.2f}）|"
                )
                i += 1
            for item in report["pending_items"]:
                md_lines.append(
                    f"| {i} | pending | {item.get('element', '—')} | {item.get('checkpoint', '—')} | "
                    f"⚠️ AC 缺「待产品确认」标记（best_match={item.get('best_match_ac', '—')}）|"
                )
                i += 1

        md_lines.extend([
            "",
            "### 9.3 最终结果统计",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 检查点总数 | {report['total_checkpoints']} |",
            f"| 已覆盖数 | {report['covered']} |",
            f"| ├─ 精确 ID 匹配 | {report['covered_by_exact_source']} |",
            f"| └─ 文本相似度匹配 | {report['covered_by_fuzzy_match']} |",
            f"| 遗漏数（missing）| {report['missing']} |",
            f"| 待产品确认数（pending）| {report['pending_confirmation']} |",
            f"| 边缘相似度数（edge）| {report['edge_cases']} |",
            f"| 覆盖率 | {report['coverage_rate']:.1%} |",
            f"| AC 总数 | {report['ac_count']} |",
            f"| ├─ 含来源标注 | {report['ac_with_sources_count']} |",
            f"| └─ 无来源（待复核）| {report['ac_without_source_count']} |",
            "",
        ])

        # 反向告警：无来源 AC 列表（仅 > 0 时显示）
        if report["ac_without_source_count"] > 0:
            md_lines.extend([
                "### 9.4 ⚠️ 无来源 AC 待复核",
                "",
                f"以下 {report['ac_without_source_count']} 条 AC 来源列为 `—` 或为空。需人工复核：",
                "- 真属于纯技术规范（如网络异常 toast 等通用约束）→ 保留 `—` 并在 AC 行注释说明",
                "- 实际能溯源到 analysis 检查点 → 补全来源列",
                "- 属于 agent 凭经验生造（违反 anti-fabrication 规则）→ 删除 AC 或补 analysis 检查点后再补来源",
                "",
                "| # | AC-ID | 规则摘要 |",
                "|---|-------|---------|",
            ])
            for i, item in enumerate(report["ac_without_source"], 1):
                rule = item["rule"].replace("|", "\\|")
                md_lines.append(f"| {i} | {item['id']} | {rule} |")
            md_lines.append("")

        print("\n".join(md_lines))
        return 1 if (report["missing"] > 0 or report["pending_confirmation"] > 0) else 0

    output_json = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_json)

    # 摘要
    print(
        f"\n--- Summary ---\n"
        f"  Total checkpoints:       {report['total_checkpoints']}\n"
        f"  Covered:                 {report['covered']}\n"
        f"    - by exact source:     {report['covered_by_exact_source']}（精确 ID 匹配，零误报）\n"
        f"    - by fuzzy match:      {report['covered_by_fuzzy_match']}（文本相似度，可能有误报）\n"
        f"  Missing:                 {report['missing']}\n"
        f"  Pending product confirm: {report['pending_confirmation']}\n"
        f"  Edge cases:              {report['edge_cases']}\n"
        f"  Coverage rate:           {report['coverage_rate']:.1%}\n"
        f"  Threshold:               {report['threshold']} (edge: {report['edge_threshold']})\n"
        f"  AC count in req:         {report['ac_count']}（含来源标注 {report['ac_with_sources_count']} 项，无来源 {report['ac_without_source_count']} 项待复核）\n"
        f"\n注意：missing_items 中 score 接近阈值（>{report['threshold'] * 0.7:.2f}）的可能是误报，建议人工复核。\n"
        f"      pending_items 是「需补充=是」但 AC 中未标记「⚠️ 待产品确认」的项。\n"
        f"      ac_without_source 是来源列为'—'或为空的 AC，需复核是否真属于纯技术规范（防 agent 偷懒填'—'）。\n"
        f"      建议在 requirements.md AC 表格中加'来源'列（如 C13#1），可大幅减少误报。\n"
        f"      Tip：使用 --markdown 输出可粘贴到 analysis 第十节的 md 块。",
        file=sys.stderr,
    )

    # 退出码：missing 或 pending 任一非零都算需修复
    return 1 if (report["missing"] > 0 or report["pending_confirmation"] > 0) else 0


if __name__ == "__main__":
    sys.exit(main())