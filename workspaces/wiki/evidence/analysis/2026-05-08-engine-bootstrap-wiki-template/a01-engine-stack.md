# a01 — Engine Stack Inventory

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Inputs: `raw.md` Section 1, 2, 8 + `source.yaml`

## Host runtime

- Claude Code version: _(not stated)_ `(raw.md#section-1)`
  - Engine không khai báo Claude Code version target trong README hay CLAUDE.md.

## MCP servers required

| Name | Transport | Command/URL | Role | Citation |
|------|-----------|-------------|------|----------|

_(none — không có `mcp.json` hoặc `.mcp.json` ở repo root)_ `(raw.md#section-2)`

## External integrations (inferred from commands/agents)

| Integration | Inferred from | Citation |
|-------------|---------------|----------|
| Obsidian (Second Brain vault) | `/obsidian-ingest` slash command — batch wrapper for Obsidian vault scan | `(.claude/commands/obsidian-ingest.md:L1)` |
| Confluence (mentioned, not implemented) | listed in evidence pipeline source examples | `(.claude/commands/README.md:L72)` |
| Linear (mentioned, not implemented) | listed in evidence pipeline source examples | `(.claude/commands/README.md:L72)` |
| Slack (mentioned, not implemented) | listed in evidence pipeline source examples | `(.claude/commands/README.md:L72)` |
| MCP (generic) | `source_type=mcp` first-class in evidence pipeline | `(templates/evidence-source.yaml:L6)`, `(agents/pipeline/critical-analysis-prompts.md:L1)` |
| HTTP API (generic) | `source_type=api` first-class in evidence pipeline | `(templates/evidence-source.yaml:L6-L7)` |
| Git CLI | `/code-analyze` uses `git rev-parse`, `git log`, `git status` | `(.claude/commands/code-analyze.md:L43-L46)` |

## Script-tool deps

_(none in default scope — no `package.json`, `pyproject.toml`, `requirements.txt` at repo root)_ `(raw.md#section-2)`

> Note: `scripts/` dir contains 9 Python scripts (`build-report-with-dialog.py`, `emit_trace.py`, `install-to-claude.py`, `lint-wiki.py`, `render_trace.py`, `validate.py`, `test_lint_wiki.py`) but không khai báo deps file ở root. Out of default scope `(raw.md#section-1)`.

## Configurable surface

_(not analyzed — pass `--allow-configs` to include `settings.json`, `wiki.json`, `wiki-global.json`)_ `(raw.md#section-8)`

Expected sources nếu rerun với `--allow-configs`:
- `.claude/settings.json` — hooks, permissions, env vars
- `.claude/wiki.json` — per-codebase active workspace pointer
- `~/.claude/wiki-global.json` — global default workspace + wiki_root fallback

## Risks

- [HIGH] **Configs unanalyzed** — không thể validate hook strategy / permission scope / env var khai báo. Engine có thể có hooks runtime mà CORE-AGENTIC không nhìn thấy. Mitigation: rerun `/code-analyze --ref . --variant agentic-engine --allow-configs`. `(raw.md#section-8)`
- [HIGH] **Claude Code version target unspecified** — engine prompts dựa vào features (slash commands, sub-agents, AskUserQuestion, ToolSearch) có thể đổi giữa Claude Code releases. Khi Claude Code upgrade, engine có thể vỡ silently. `(raw.md#section-1)`
- [MED] **Engine repo unmanaged-by-git** — không có history, không có branch, snapshot reproducibility dựa vào `unmanaged-{sha256}` của tree manifest. Nếu user edit file local, snapshot mới sẽ có sha khác → analysis cần rerun thủ công. `(source.yaml#git_sha)`
- [MED] **No MCP servers declared** — engine có nhiều prompt mention MCP (`/evidence-ingest --source mcp`, `source_type=mcp`) nhưng KHÔNG có `mcp.json` ở repo root. MCP integration là responsibility của user codebase, không phải engine. Cần document rõ trong onboarding. `(raw.md#section-2)`
- [LOW] **External integrations đa số "mentioned, not implemented"** — Confluence/Linear/Slack được list trong README nhưng không có implementation code thực tế. Nguy cơ user kỳ vọng integration sẵn sàng. `(.claude/commands/README.md:L72)`
