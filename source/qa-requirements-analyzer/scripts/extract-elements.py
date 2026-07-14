"""
extract-elements.py — 机械化扫描原型代码，输出可交互元素清单

四层扫描策略，覆盖不同前端框架/项目结构：
  L1 (lib): Antd/Element UI 组件白名单（首字母大写，如 <Input> <Button>）
  L2 (native): 原生 HTML 交互元素（<button> <a> <input> <select> <form> 等）
  L3 (custom): 自定义函数组件（首字母大写但不在 L1 白名单的 JSX 标签）
  L4 (event): 兜底——含 onClick/onChange/onSubmit 等事件绑定的任意元素

支持路径过滤：--include / --exclude 用 glob 模式聚焦特定模块。

用法:
    # 默认四层全扫
    python extract-elements.py --src ./prototype/

    # 只扫 home 模块
    python extract-elements.py --src ./prototype/ --include "**/home/**,**/Home.tsx"

    # 排除测试和样式文件
    python extract-elements.py --src ./prototype/ --exclude "**/*.test.*,**/*.spec.*"

    # 只用某几层
    python extract-elements.py --src ./prototype/ --layers L1,L2,L3

    # 输出 JSON
    python extract-elements.py --src ./prototype/ --output elements.json

退出码:
    0  扫描完成（无论找到多少）
    2  脚本错误
"""
from __future__ import annotations

import argparse
import fnmatch
import io
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

# Windows GBK fallback: force UTF-8 stdout/stderr
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# L1: Antd / Element UI 组件白名单
L1_COMPONENTS = {
    "Input", "InputNumber", "TextArea", "Select", "Cascader",
    "Switch", "Checkbox", "Radio", "Upload", "Button",
    "Table", "Tabs", "Tree", "Modal", "Drawer", "Form",
    "TimePicker", "DatePicker", "RangePicker", "Slider",
    "Tooltip", "Popover", "Tag", "Pagination", "Steps",
    "Menu", "Dropdown", "List", "Card",
    # react-router 相关
    "Link", "NavLink", "Outlet",
}

# L2: 原生 HTML 交互元素
L2_NATIVE_TAGS = {
    "button", "a", "input", "select", "textarea", "form",
    "dialog", "details", "summary", "label",
}

# L4: 事件属性（用于兜底捕获）
L4_EVENT_ATTRS = {
    "onClick", "onChange", "onSubmit", "onBlur", "onFocus",
    "onMouseEnter", "onMouseLeave", "onKeyDown", "onKeyPress",
    "onSelect", "onToggle",
}

DEFAULT_EXTS = ["tsx", "jsx", "vue", "ts", "js", "html"]
SKIP_DIRS = {"node_modules", "dist", "build", ".git", ".next", ".vite", ".vite-temp", "coverage"}


def matches_any(path_str: str, patterns: list[str]) -> bool:
    """检查路径是否匹配任意 glob 模式。"""
    if not patterns:
        return False
    for pat in patterns:
        if fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path_str.replace("\\", "/"), pat):
            return True
    return False


def scan_file(path: Path, layers: set[str], custom_only_uppercase: bool = True) -> list[dict]:
    """扫描单个文件，按启用的 layers 返回元素列表。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return []

    results = []

    # L1: Antd/Element 组件白名单
    if "L1" in layers:
        l1_pattern = re.compile(r"<\s*(" + "|".join(L1_COMPONENTS) + r")(\b|\.[A-Z]\w*)")
        for line_no, line in enumerate(text.split("\n"), 1):
            for m in l1_pattern.finditer(line):
                comp = m.group(1) + (m.group(2) if m.group(2).startswith(".") else "")
                results.append({
                    "layer": "L1",
                    "component": comp,
                    "line": line_no,
                    "snippet": line.strip()[:120],
                })

    # L2: 原生 HTML 交互元素
    if "L2" in layers:
        l2_pattern = re.compile(r"<\s*(" + "|".join(L2_NATIVE_TAGS) + r")(\b|\s|>|/)")
        for line_no, line in enumerate(text.split("\n"), 1):
            for m in l2_pattern.finditer(line):
                tag = m.group(1)
                results.append({
                    "layer": "L2",
                    "component": f"native:{tag}",
                    "line": line_no,
                    "snippet": line.strip()[:120],
                })

    # L3: 自定义函数组件（首字母大写但不在 L1 白名单）
    if "L3" in layers:
        l3_pattern = re.compile(r"<\s*([A-Z][a-zA-Z0-9]+)(\b|\s|>|/)")
        for line_no, line in enumerate(text.split("\n"), 1):
            for m in l3_pattern.finditer(line):
                comp = m.group(1)
                if comp in L1_COMPONENTS:
                    continue  # 已被 L1 捕获
                results.append({
                    "layer": "L3",
                    "component": f"custom:{comp}",
                    "line": line_no,
                    "snippet": line.strip()[:120],
                })

    # L4: 含事件绑定的任意元素（兜底）
    if "L4" in layers:
        l4_pattern = re.compile(r"\b(" + "|".join(L4_EVENT_ATTRS) + r")\s*=")
        for line_no, line in enumerate(text.split("\n"), 1):
            for m in l4_pattern.finditer(line):
                attr = m.group(1)
                results.append({
                    "layer": "L4",
                    "component": f"event:{attr}",
                    "line": line_no,
                    "snippet": line.strip()[:120],
                })

    return results


def scan_directory(
    src: Path,
    exts: list[str],
    layers: set[str],
    include: list[str],
    exclude: list[str],
) -> dict:
    """递归扫描目录。"""
    all_results = []
    files_scanned = 0
    files_with_components = 0

    def walk(d: Path):
        nonlocal files_scanned, files_with_components
        try:
            entries = list(d.iterdir())
        except (PermissionError, OSError, FileNotFoundError):
            return
        for entry in entries:
            try:
                if entry.is_dir():
                    if entry.name in SKIP_DIRS:
                        continue
                    walk(entry)
                elif entry.is_file():
                    if entry.suffix.lstrip(".") not in exts:
                        continue
                    rel = str(entry.relative_to(src)).replace("\\", "/")
                    # include 过滤（有则必须匹配）
                    if include and not matches_any(rel, include):
                        continue
                    # exclude 过滤（匹配则跳过）
                    if exclude and matches_any(rel, exclude):
                        continue
                    files_scanned += 1
                    findings = scan_file(entry, layers)
                    if findings:
                        files_with_components += 1
                        for f in findings:
                            f["file"] = rel
                            all_results.append(f)
            except (PermissionError, OSError, FileNotFoundError):
                continue

    walk(src)

    # 按层级聚合
    by_layer = defaultdict(int)
    for r in all_results:
        by_layer[r["layer"]] += 1

    # 按组件类型聚合
    by_component = defaultdict(list)
    for r in all_results:
        by_component[r["component"]].append(r)
    by_component_summary = {k: len(v) for k, v in sorted(by_component.items(), key=lambda x: -len(x[1]))}

    # 按文件聚合
    by_file = defaultdict(list)
    for r in all_results:
        by_file[r["file"]].append(r)
    by_file_summary = {k: len(v) for k, v in sorted(by_file.items())}

    return {
        "src": str(src),
        "layers": sorted(layers),
        "include": include,
        "exclude": exclude,
        "files_scanned": files_scanned,
        "files_with_components": files_with_components,
        "total_elements": len(all_results),
        "by_layer": dict(by_layer),
        "by_component": by_component_summary,
        "by_file": by_file_summary,
        "elements": all_results,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", required=True, help="原型代码目录")
    p.add_argument("--ext", default=",".join(DEFAULT_EXTS), help=f"文件扩展名（逗号分隔，默认 {','.join(DEFAULT_EXTS)}）")
    p.add_argument("--layers", default="L1,L2,L3,L4", help="启用的扫描层（L1=Antd/L2=原生/L3=自定义组件/L4=事件兜底）")
    p.add_argument("--include", default="", help="只扫描匹配的路径（glob 模式，逗号分隔，如 '**/home/**'）")
    p.add_argument("--exclude", default="", help="排除匹配的路径（glob 模式，逗号分隔）")
    p.add_argument("--output", help="JSON 报告输出路径（默认 stdout）")
    args = p.parse_args()

    src = Path(args.src)
    if not src.exists() or not src.is_dir():
        print(f"ERROR: src directory not found: {src}", file=sys.stderr)
        return 2

    exts = [e.strip().lstrip(".") for e in args.ext.split(",") if e.strip()]
    layers = set(l.strip() for l in args.layers.split(",") if l.strip())
    include = [p.strip() for p in args.include.split(",") if p.strip()]
    exclude = [p.strip() for p in args.exclude.split(",") if p.strip()]

    valid_layers = {"L1", "L2", "L3", "L4"}
    invalid = layers - valid_layers
    if invalid:
        print(f"ERROR: invalid layers: {invalid}. Valid: {valid_layers}", file=sys.stderr)
        return 2

    report = scan_directory(src, exts, layers, include, exclude)

    output_json = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_json)

    print(
        f"\n--- Summary ---\n"
        f"  Layers enabled:        {','.join(sorted(layers))}\n"
        f"  Include filters:       {include or '(all)'}\n"
        f"  Exclude filters:       {exclude or '(none)'}\n"
        f"  Files scanned:         {report['files_scanned']}\n"
        f"  Files with elements:   {report['files_with_components']}\n"
        f"  Total elements:        {report['total_elements']}",
        file=sys.stderr,
    )
    if report.get("by_layer"):
        print("  By layer:", file=sys.stderr)
        for layer in sorted(report["by_layer"]):
            print(f"    {layer}: {report['by_layer'][layer]}", file=sys.stderr)
    if report["by_component"]:
        print("  Top 10 components:", file=sys.stderr)
        for name, count in list(report["by_component"].items())[:10]:
            print(f"    {name}: {count}", file=sys.stderr)
    if report["by_file"]:
        print(f"  Top 10 files:", file=sys.stderr)
        top_files = sorted(report["by_file"].items(), key=lambda x: -x[1])[:10]
        for f, n in top_files:
            print(f"    {f}: {n}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
