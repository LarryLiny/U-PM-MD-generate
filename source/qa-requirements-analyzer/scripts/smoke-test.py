"""
smoke-test.py — 端到端冒烟测试

按 7 步流程顺序调用 6 个脚本，验证 skill 全链路可跑通。
使用真实 fixture（默认 ./fixtures/）或用户指定的 analysis/requirements 文件对。

每步独立汇报通过/失败，最后输出总结。

测试步骤：
  1. count-coverage.py（统计 analysis 覆盖率）
  2. cross-check.py（交叉检查覆盖度）
  3. validate-requirements.py（结构合规性 + 同步检查）
  4. R9 落盘验证：grep analysis 含 cross-check 第九节关键字段
  5. R9 落盘验证：grep analysis 含 validate 第三节 3.2 关键字段
  6. cleanup-temp.py（dry-run）

可选步骤（默认跳过，需 --prototype-dir 启用）：
  - extract-elements.py（机械化扫描原型）

用法:
    python smoke-test.py                       # 用默认 fixtures（如有）
    python smoke-test.py --fixture-dir ./knowledge/U校园/U5首页/
    python smoke-test.py --fixture-dir ... --skip extract-elements
    python smoke-test.py --fixture-dir ... --no-check-landing  # 跳过落盘验证

退出码:
    0  全链路通过
    1  存在失败步骤
    2  脚本错误（fixtures 不存在等）
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
from pathlib import Path

# Windows GBK fallback
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


SCRIPT_DIR = Path(__file__).resolve().parent

# 强制 UTF-8 环境，避免 Windows GBK 乱码
# CANTOR_TOKEN_AUTOMARK=0：冒烟测试里跑门禁脚本不打 token 子阶段点（避免污染账本）
PY_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "CANTOR_TOKEN_AUTOMARK": "0"}


def run_step(name: str, cmd: list[str], expected_exit: tuple = (0,)) -> dict:
    """执行一个脚本步骤并返回结果。"""
    print(f"\n=== 执行: {name} ===", file=sys.stderr)
    print(f"    {' '.join(cmd)}", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=PY_ENV,
            timeout=60,
        )
        passed = result.returncode in expected_exit
        # stderr 摘要（取最后 5 行）
        stderr_tail = "\n".join(result.stderr.strip().split("\n")[-5:]) if result.stderr else ""
        print(f"    exit_code: {result.returncode} ({'✅ PASS' if passed else '❌ FAIL'})", file=sys.stderr)
        if stderr_tail:
            print(f"    stderr 末尾:\n      {stderr_tail.replace(chr(10), chr(10) + '      ')}", file=sys.stderr)
        return {
            "name": name,
            "cmd": " ".join(cmd),
            "exit_code": result.returncode,
            "passed": passed,
            "stderr_tail": stderr_tail,
        }
    except subprocess.TimeoutExpired:
        print(f"    ❌ TIMEOUT (60s)", file=sys.stderr)
        return {"name": name, "cmd": " ".join(cmd), "exit_code": -1, "passed": False, "stderr_tail": "timeout"}
    except FileNotFoundError as e:
        print(f"    ❌ FileNotFoundError: {e}", file=sys.stderr)
        return {"name": name, "cmd": " ".join(cmd), "exit_code": -1, "passed": False, "stderr_tail": str(e)}


def check_landing(name: str, file_path: Path, required_keywords: list[str]) -> dict:
    """落盘验证：检查指定文件是否含必需的关键词，避免 R9 反模式（脚本跑了但报告没落盘）。"""
    print(f"\n=== 落盘验证: {name} ===", file=sys.stderr)
    print(f"    文件: {file_path}", file=sys.stderr)
    print(f"    要求关键词: {required_keywords}", file=sys.stderr)

    if not file_path.exists():
        print(f"    ❌ FAIL - 文件不存在", file=sys.stderr)
        return {
            "name": name,
            "passed": False,
            "exit_code": -1,
            "stderr_tail": f"file not found: {file_path}",
        }

    text = file_path.read_text(encoding="utf-8")
    missing = [kw for kw in required_keywords if kw not in text]

    passed = len(missing) == 0
    if passed:
        print(f"    ✅ PASS - 全部 {len(required_keywords)} 个关键词均找到", file=sys.stderr)
    else:
        print(f"    ❌ FAIL - 缺失关键词: {missing}", file=sys.stderr)
        print(f"        提示：跑 cross-check / validate 后必须把 --markdown 输出粘贴到 analysis 对应章节", file=sys.stderr)

    return {
        "name": name,
        "passed": passed,
        "exit_code": 0 if passed else 1,
        "stderr_tail": "" if passed else f"missing keywords: {missing}",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--fixture-dir",
        default=None,
        help="包含 requirements-analysis.md 和 requirements.md 的目录",
    )
    p.add_argument(
        "--prototype-dir",
        default=None,
        help="原型代码目录（可选，用于 extract-elements 测试）",
    )
    p.add_argument(
        "--skip",
        default="",
        help="跳过的步骤名（逗号分隔），如 'extract-elements,cleanup-temp,check-landing'",
    )
    p.add_argument(
        "--no-check-landing",
        action="store_true",
        help="跳过 R9 落盘验证（默认开启，验证 analysis 含 cross-check / validate 报告内容）",
    )
    args = p.parse_args()

    skipped = set(s.strip() for s in args.skip.split(",") if s.strip())

    # 解析 fixture 路径
    if args.fixture_dir:
        fix_dir = Path(args.fixture_dir).resolve()
        if not fix_dir.exists():
            print(f"ERROR: fixture-dir not found: {fix_dir}", file=sys.stderr)
            return 2
        analysis_path = fix_dir / "requirements-analysis.md"
        req_path = fix_dir / "requirements.md"
        if not analysis_path.exists() or not req_path.exists():
            print(f"ERROR: fixture-dir 缺少 requirements-analysis.md 或 requirements.md", file=sys.stderr)
            return 2
    else:
        # 默认尝试 ../fixtures/
        fix_dir = SCRIPT_DIR.parent / "fixtures"
        analysis_path = fix_dir / "requirements-analysis.md"
        req_path = fix_dir / "requirements.md"
        if not analysis_path.exists():
            print("ERROR: --fixture-dir 未指定且默认 fixtures/ 不存在", file=sys.stderr)
            print("       至少需要 requirements-analysis.md 和 requirements.md 两个真实文件", file=sys.stderr)
            return 2

    print(f"使用 fixture: {fix_dir}", file=sys.stderr)
    print(f"  analysis:     {analysis_path}", file=sys.stderr)
    print(f"  requirements: {req_path}", file=sys.stderr)

    results = []

    # Step 1: extract-elements (可选，需要原型代码)
    if "extract-elements" not in skipped and args.prototype_dir:
        results.append(run_step(
            "extract-elements.py（机械化扫描原型）",
            ["python", str(SCRIPT_DIR / "extract-elements.py"), "--src", args.prototype_dir],
            expected_exit=(0,),
        ))

    # Step 2: count-coverage（用于自检）
    if "count-coverage" not in skipped:
        results.append(run_step(
            "count-coverage.py（统计断言覆盖率）",
            ["python", str(SCRIPT_DIR / "count-coverage.py"), "--analysis", str(analysis_path)],
            expected_exit=(0,),
        ))

    # Step 3: cross-check（核心）
    if "cross-check" not in skipped:
        results.append(run_step(
            "cross-check.py（交叉检查覆盖度）",
            [
                "python", str(SCRIPT_DIR / "cross-check.py"),
                "--analysis", str(analysis_path),
                "--requirements", str(req_path),
            ],
            expected_exit=(0,),  # 完整覆盖才算通过
        ))

    # Step 4: validate-requirements（结构校验，含 analysis 同步检查）
    if "validate-requirements" not in skipped:
        results.append(run_step(
            "validate-requirements.py（结构合规性 + 同步检查）",
            [
                "python", str(SCRIPT_DIR / "validate-requirements.py"),
                str(req_path),
                "--analysis", str(analysis_path),
            ],
            expected_exit=(0,),
        ))

    # Step 5: R9 落盘验证（防止 cross-check / validate 跑了但报告没落到 analysis）
    if not args.no_check_landing and "check-landing" not in skipped:
        # cross-check 报告应落到 analysis 第九节
        results.append(check_landing(
            "cross-check 报告落盘到 analysis 第九节",
            analysis_path,
            ["九、交叉检查结果", "覆盖率", "检查点总数"],
        ))
        # validate 报告应落到 analysis 第三节 3.2
        results.append(check_landing(
            "validate 报告落盘到 analysis 第三节 3.2",
            analysis_path,
            ["3.2", "validate-requirements", "AC 编号"],
        ))
        # PRD 缺陷修正追踪段 + 哨兵落盘验证（operational-rules §7，防 Step 3.5 漏跑）
        results.append(check_landing(
            "PRD 缺陷修正追踪段落盘到 analysis",
            analysis_path,
            ["测试驱动的 PRD 缺陷修正统计", "PRD_DEFECT_TOTAL"],
        ))

    # Step 6: cleanup-temp（dry-run 验证不出错）
    if "cleanup-temp" not in skipped:
        results.append(run_step(
            "cleanup-temp.py（dry-run 清理）",
            ["python", str(SCRIPT_DIR / "cleanup-temp.py"), "--dir", str(fix_dir)],
            expected_exit=(0,),
        ))

    # 汇总
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"端到端冒烟测试结果：{len(passed)}/{len(results)} 通过", file=sys.stderr)
    if failed:
        print(f"\n失败步骤：", file=sys.stderr)
        for r in failed:
            print(f"  ❌ {r['name']} (exit={r['exit_code']})", file=sys.stderr)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
