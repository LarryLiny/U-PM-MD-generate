# 项目指令：demotomd skill 开发

## 同步规则

本项目是 `demotomd` skill 的开发工程。每次修改本项目中的文件后，**自动同步**到以下四个 skill 安装目录：

- Codex: `~/.Codex/skills/demotomd/`
- Codex lowercase: `~/.codex/skills/demotomd/`
- Claude Code: `~/.claude/skills/demotomd/`
- Kiro: `~/.kiro/skills/demotomd/`

### 同步映射

| 本项目文件 | 同步目标路径 |
|-----------|-------------|
| `SKILL.md` | `SKILL.md` |
| `references/demo-analysis-guide.md` | `references/demo-analysis-guide.md` |
| `references/requirement-template.md` | `references/requirement-template.md` |
| `product-workflow.md` | `product-workflow.md` |

以下文件仅同步到 Codex / codex，不同步到 Claude / Kiro：
- `project-instructions/AGENTS.md` → Codex / codex skill 目录（如果该文件存在）
- `scripts/check-sync-needed.sh` → Codex / codex skill 目录

以下文件仅同步到 Claude，不同步到 Codex / codex / Kiro：
- `project-instructions/CLAUDE.md` → Claude skill 目录（如果该文件存在）

以下文件仅同步到 Kiro，不同步到 Codex / codex / Claude：
- `project-instructions/kiro-steering.md` → Kiro skill 目录

### 执行方式

每次修改上述文件后，在回复用户之前，使用 `mkdir -p` 确保四个目标目录存在，再使用 `cp` 命令将变更文件同步到目标目录。不需要询问用户，直接执行。
