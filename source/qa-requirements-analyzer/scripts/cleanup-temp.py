"""
cleanup-temp.py — 第六步清理临时文件

删除执行过程中产生的临时文件（调试脚本、中间产物等），保持项目整洁。
默认 dry-run 模式只打印待删除文件，加 --apply 才真正删除。

匹配规则：
  - debug-*.py / debug-*.js / scratch-*.* / temp-*.* / tmp-*.*
  - _*.py / _*.js / _*.ts（下划线开头的临时脚本）
  - _tmp_*（锚点替换中转法产生的临时文档/脚本，如 _tmp_elements.md、_tmp_replace.py）
  - *.bak / *~ / .DS_Store / Thumbs.db
  - test-output-* / temp-output-*
  - cross-check-report.json / validate-report.json 等脚本中间报告（*-report.json）
  - 用户可通过 --pattern 添加自定义匹配

保护（不删，可溯源交付辅料）：
  - elements.json / elements-scan.json / *-scan.json（extract-elements 扫描产物）
    数据虽已落 analysis，但保留用于溯源；如确需删除请显式 --pattern "*-scan.json"

用法:
    python cleanup-temp.py --dir ./specs/my-feature/                   # dry-run
    python cleanup-temp.py --dir ./specs/my-feature/ --apply           # 真正删除
    python cleanup-temp.py --dir . --pattern "scratch-*,*.tmp" --apply

退出码:
    0  完成（dry-run 或 apply 都返回 0）
    2  脚本错误
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# Windows GBK fallback: force UTF-8 stdout/stderr
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


DEFAULT_PATTERNS = [
    "debug-*.py",
    "debug-*.js",
    "debug-*.ts",
    "scratch-*.*",
    "temp-*.*",
    "tmp-*.*",
    "*.bak",
    ".DS_Store",
    "Thumbs.db",
    "test-output-*",
    "temp-output-*",
    "scratch.md",
    "scratch.txt",
    # 下划线开头的临时脚本（如 _show_xxx.py、_backfill_xxx.py、_check_xxx.py）
    "_*.py",
    "_*.js",
    "_*.ts",
    # 锚点替换中转法（5.3.1）产生的临时文档/脚本（如 _tmp_elements.md、_tmp_replace.py）
    "_tmp_*",
    "_tmp_*.*",
    # 本 Skill 脚本生成的中间报告（report json 属中间产物，可删）
    "cross-check-report.json",
    "count-coverage-report.json",
    "validate-report.json",
    "*-report.json",
    # 注意（P1-2）：extract-elements 的扫描产物 elements.json / elements-scan.json /
    # *-scan.json 属"可溯源交付辅料"，已从删除清单移除，cleanup 不再清它们。
    # 如确实想删，显式用 --pattern "*-scan.json" 传入。
]

PROTECTED_DIRS = {".git", "node_modules", ".kiro", "dist", "build"}


def find_temp_files(root: Path, patterns: list[str]) -> list[Path]:
    """递归查找匹配 patterns 的文件（跳过 PROTECTED_DIRS）。"""
    found = set()
    # 自己实现遍历以提前剪枝 PROTECTED_DIRS（避免 rglob 进入 node_modules）
    def walk(d: Path):
        try:
            entries = list(d.iterdir())
        except (PermissionError, OSError, FileNotFoundError):
            return
        for entry in entries:
            try:
                if entry.is_dir():
                    if entry.name in PROTECTED_DIRS:
                        continue
                    walk(entry)
                elif entry.is_file():
                    for pattern in patterns:
                        if entry.match(pattern):
                            found.add(entry)
                            break
            except (PermissionError, OSError, FileNotFoundError):
                continue

    walk(root)
    return sorted(found)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", required=True, help="要清理的目录")
    p.add_argument("--pattern", help="额外的 glob 模式（逗号分隔）")
    p.add_argument("--apply", action="store_true", help="真正删除（默认 dry-run）")
    args = p.parse_args()

    root = Path(args.dir)
    if not root.exists() or not root.is_dir():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 2

    patterns = list(DEFAULT_PATTERNS)
    if args.pattern:
        patterns += [p.strip() for p in args.pattern.split(",") if p.strip()]

    files = find_temp_files(root, patterns)

    if not files:
        print(f"No temporary files found in {root}.")
        return 0

    print(f"Found {len(files)} temporary file(s):")
    for f in files:
        print(f"  {f}")

    if not args.apply:
        print("\n(dry-run mode. Add --apply to actually delete.)")
        return 0

    deleted = 0
    failed = []
    for f in files:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            failed.append((f, str(e)))

    print(f"\nDeleted {deleted} file(s).")
    if failed:
        print(f"Failed to delete {len(failed)}:", file=sys.stderr)
        for f, err in failed:
            print(f"  {f}: {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
