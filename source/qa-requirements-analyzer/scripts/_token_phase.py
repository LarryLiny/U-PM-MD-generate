# -*- coding: utf-8 -*-
"""薄封装：定位共享 lib/token_phase.py，注入本 skill 名后转调。

子阶段打点的全部逻辑（成功才打 / 去重 / fail-silent / --no-flush / AUTOMARK 开关）
集中在 `<cantor-os>/lib/token_phase.py`，本文件只负责把本 skill 名传进去，
保证门禁脚本里的调用 `_token_phase.emit("generate/read", rc, action=...)` 不变。
"""
import sys
from pathlib import Path

SKILL = "qa-requirements-analyzer"


def emit(phase, rc=0, action=None):
    try:
        # scripts(0) -> <skill>(1) -> skills(2) -> cantor-os(3) -> lib
        lib = Path(__file__).resolve().parents[3] / "lib"
        if str(lib) not in sys.path:
            sys.path.insert(0, str(lib))
        import token_phase
        token_phase.emit(SKILL, phase, rc, action)
    except Exception:
        # 埋点旁路，任何异常都不得影响门禁脚本
        pass
