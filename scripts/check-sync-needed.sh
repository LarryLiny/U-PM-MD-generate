#!/bin/bash
# check-sync-needed.sh
# Claude Code Stop hook: 提醒用户同步需求文档
# 在源码项目中检测源文件是否比需求文档更新，如果是则输出提醒

python3 -c "
import json, sys, os

try:
    data = json.load(sys.stdin)
    cwd = os.environ.get('PWD', data.get('cwd', ''))
    if not cwd:
        import subprocess
        cwd = subprocess.getoutput('pwd')

    # 检查是否有可分析的源码文件
    source_patterns = ['.html', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte', '.css']
    has_source = False
    src_dir = os.path.join(cwd, 'src')

    if os.path.exists(src_dir):
        has_source = True
    else:
        # 检查根目录是否有 HTML/JS 文件
        for f in os.listdir(cwd):
            if any(f.endswith(ext) for ext in source_patterns):
                has_source = True
                break

    if not has_source:
        print(json.dumps({}))
        sys.exit(0)

    # 查找 requirement 文件：优先 *_requirement.md，回退 requirement.md
    req_path = None
    for f in os.listdir(cwd):
        if f.endswith('_requirement.md') or f == 'requirement.md':
            req_path = os.path.join(cwd, f)
            break
    has_req = req_path is not None

    # 检查源文件修改时间
    req_mtime = 0
    if has_req:
        req_mtime = os.path.getmtime(req_path)

    # 查找更新的源文件
    src_newer = False
    search_dirs = [cwd] if not os.path.exists(src_dir) else [src_dir]

    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            for f in files:
                if any(f.endswith(ext) for ext in source_patterns):
                    fpath = os.path.join(root, f)
                    if os.path.getmtime(fpath) > req_mtime:
                        src_newer = True
                        break
            if src_newer:
                break

    if src_newer or not has_req:
        if has_req:
            msg = 'Demo 源文件已更新但需求文档尚未同步。运行 /demotomd 更新需求文档。'
        else:
            msg = '检测到源码项目但未找到需求文档。运行 /demotomd 从 demo 代码生成需求文档。'
        print(json.dumps({'systemMessage': msg}))
    else:
        print(json.dumps({}))

except Exception:
    print(json.dumps({}))
"
