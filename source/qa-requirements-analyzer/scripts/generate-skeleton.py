"""
generate-skeleton.py — 生成 requirements.md 和 requirements-analysis.md 的空模板

读取 cantor-os/md/QA/ 下的模板文件，替换脚本管理的占位符（{feature} {today} {element_name}），
其他用户级占位符（如 {项目名称} {角色}）保留原样供用户手填。
模板独立维护，本脚本只负责读取 + 选择性替换。

用法:
    python generate-skeleton.py --output-dir ./specs/my-feature/
    python generate-skeleton.py --output-dir ./specs/my-feature/ --feature "购物车"
    python generate-skeleton.py --output-dir ./specs/my-feature/ --force            # 覆盖已有文件（覆盖前自动备份）
    python generate-skeleton.py --output-dir ./specs/my-feature/ --target requirements --force  # 只重生成 requirements.md，不碰 analysis
    python generate-skeleton.py --output-dir ./specs/my-feature/ --force --no-backup # 覆盖且不备份

注意（P0-2）:
    --force 默认会先把被覆盖的已有文件备份为 <name>.bak-<时间戳> 再覆盖，避免误删已填好的 analysis。
    只想重生成其中一个文件时，用 --target requirements / --target analysis 缩小粒度，避免动到另一个。

退出码:
    0  生成成功
    1  目标文件已存在且未指定 --force
    2  脚本错误（模板文件不存在等）
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from datetime import date, datetime

# Windows GBK fallback: force UTF-8 stdout/stderr
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# 模板路径：模板已移到 cantor-os/md/QA/（多角色共享文档库）。
# 本脚本通过 ~/.claude/skills/ junction 运行时，Path(__file__).resolve() 会穿透
# junction 到仓库真实路径，再上溯三级 (scripts→skill→skills→repo root) 定位 md/QA。
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "md" / "QA"

# 输出文件 → 模板文件 映射
TEMPLATE_MAP = {
    "requirements.md": TEMPLATES_DIR / "requirements.md.tpl",
    "requirements-analysis.md": TEMPLATES_DIR / "requirements-analysis.md.tpl",
}

# 脚本管理的占位符（运行时替换为真实值）
# 其他形如 {项目名称} {角色1} {状态A} 等用户级占位符保留原样供手填
SCRIPT_MANAGED_PLACEHOLDERS = ("feature", "today", "element_name")


def render(template_path: Path, **vars) -> str:
    """读取模板并按字面替换脚本管理的占位符。

    用 str.replace 精确替换 SCRIPT_MANAGED_PLACEHOLDERS，避开 str.format
    与模板中 YAML `{ key: {var} }` 等花括号嵌套场景的冲突。
    其他 {用户占位符} 保留原样，提示用户手填。
    """
    text = template_path.read_text(encoding="utf-8")
    for key in SCRIPT_MANAGED_PLACEHOLDERS:
        if key in vars:
            text = text.replace("{" + key + "}", str(vars[key]))
    return text


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output-dir", required=True, help="输出目录")
    p.add_argument("--feature", default="新功能", help="功能/项目名")
    p.add_argument("--force", action="store_true", help="覆盖已有文件（覆盖前自动备份，除非 --no-backup）")
    p.add_argument(
        "--no-backup",
        action="store_true",
        help="--force 覆盖时不自动备份（默认会先备份为 <name>.bak-<时间戳>）",
    )
    p.add_argument(
        "--target",
        choices=["all", "requirements", "analysis"],
        default="all",
        help="生成目标：all=两个文件（默认），requirements=仅 requirements.md，analysis=仅 analysis.md",
    )
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 根据 --target 过滤要生成的文件
    if args.target == "requirements":
        active_map = {"requirements.md": TEMPLATE_MAP["requirements.md"]}
    elif args.target == "analysis":
        active_map = {"requirements-analysis.md": TEMPLATE_MAP["requirements-analysis.md"]}
    else:
        active_map = dict(TEMPLATE_MAP)

    # 验证模板存在
    missing_templates = [name for name, path in active_map.items() if not path.exists()]
    if missing_templates:
        print(f"ERROR: missing template files:", file=sys.stderr)
        for name in missing_templates:
            print(f"  {active_map[name]}", file=sys.stderr)
        print(f"Templates should be in: {TEMPLATES_DIR}", file=sys.stderr)
        return 2

    # 验证输出文件不存在（除非 --force）
    if not args.force:
        existing = [name for name in active_map if (out_dir / name).exists()]
        if existing:
            print(f"ERROR: target files exist. Use --force to overwrite:", file=sys.stderr)
            for name in existing:
                print(f"  {out_dir / name}", file=sys.stderr)
            return 1

    # 渲染所有模板
    today = date.today().isoformat()
    template_vars = {
        "feature": args.feature,
        "today": today,
        "element_name": "样例元素",
    }

    # --force 覆盖前自动备份已有的非空目标文件（P0-2：防止覆盖已填好的 analysis）。
    # 备份名用 .bak-<时间戳> 后缀：既不被 validate 第 13 项（endswith ".bak"）误报为残留，
    # 也不被 cleanup-temp 的 "*.bak" glob 匹配清掉。
    backed_up = []
    if args.force and not args.no_backup:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        for output_name in active_map:
            target = out_dir / output_name
            if target.exists() and target.stat().st_size > 0:
                backup = out_dir / f"{output_name}.bak-{ts}"
                backup.write_bytes(target.read_bytes())
                backed_up.append(backup)

    generated = []
    for output_name, template_path in active_map.items():
        rendered = render(template_path, **template_vars)
        out_file = out_dir / output_name
        out_file.write_text(rendered, encoding="utf-8")
        generated.append(out_file)

    if backed_up:
        print("⚠️  已备份被覆盖的原文件（确认新文件无误后可手动删除这些备份）：")
        for b in backed_up:
            print(f"  {b}")
        print()

    print("Generated:")
    for f in generated:
        print(f"  {f}")

    print("\nNext steps:")
    print("  1. 用 LLM 完成 PRD 自检（第一步）")
    print("  2. python scripts/extract-elements.py --src ./prototype/ → 元素清单")
    print("  3. LLM 填充各章节内容（手填模板里的 {占位符}）")
    print("  4. python scripts/count-coverage.py --analysis ... → 统计覆盖率")
    print("  5. python scripts/cross-check.py --analysis ... --requirements ... → 交叉检查")
    print("  6. python scripts/validate-requirements.py requirements.md → 结构校验")
    return 0


if __name__ == "__main__":
    _rc = 1
    try:
        _rc = main()
    finally:
        try:
            # 凡生成 requirements 骨架（阶段二：--target requirements/all，或默认无 --target=all）都打 generate/read；
            # 仅 --target analysis（阶段一 analysis-only）不在此打——阶段一按单点 analyze（count-coverage 载体）处理。
            _tgt = ""
            if "--target" in sys.argv:
                _i = sys.argv.index("--target")
                if _i + 1 < len(sys.argv):
                    _tgt = sys.argv[_i + 1]
            if _tgt != "analysis":
                import os as _os
                sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
                import _token_phase
                _token_phase.emit("generate/read", _rc,
                                  action=("读 refs/分析 + 建 requirements 骨架" if _rc == 0 else "建骨架失败 rc=%d" % _rc))
        except Exception:
            pass
    sys.exit(_rc)
