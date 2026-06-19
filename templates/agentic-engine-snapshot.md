# Agentic-Engine Snapshot — {evid-id}

> Source: agentic-coding engine tại `{repo-path}` @ git SHA `{git_sha}` (branch: `{git_branch}`)
> Snapshotted at: {ISO timestamp}
> Scope: {paths/globs included}
> Variant: agentic-engine
>
> Đây là snapshot METADATA cho engine repo (markdown-heavy: slash commands, sub-agents, prompt templates), KHÔNG phải bản sao file. Mọi citation `(file:line)` trỏ về file thật trong repo (immutable tại git SHA trên).

---

## Section 1 — Engine metadata

- **Engine name**: {từ README first heading / package.json#name / dir name}
- **Purpose**: {≤ 300 chars excerpt từ README.md hoặc CLAUDE.md}
- **Top-level dirs**: {liệt kê 1 cấp đầu, kèm 1-line mô tả mỗi dir nếu rõ}
- **Claude Code version target**: {nếu README/CLAUDE.md ghi rõ — vd "Claude Code ≥ 1.x" — else "_(not stated)_"}
- **Stated purpose excerpt**: {trích đoạn key paragraph nếu có}

Citation: `(README.md:L..-L..)` / `(CLAUDE.md:L..-L..)`

---

## Section 2 — Dependencies

### MCP servers (`mcp.json` / `.mcp.json`)
| Name | Command | Role | Citation |
|------|---------|------|----------|
| {server} | {cmd} | {1-line role} | `(mcp.json:L..)` |

> Skip nếu không có file mcp config → `_(none)_`.

### Runtime / script-tool deps (nếu có)
| Source | Name | Version | Purpose | Citation |
|--------|------|---------|---------|----------|
| package.json | {pkg} | {ver} | {role} | `(package.json:L..)` |
| pyproject.toml | {pkg} | {ver} | {role} | `(pyproject.toml:L..)` |

### External integrations (suy ra từ commands/agents)
- {Obsidian | Confluence | Linear | GitHub | Slack} — inferred from `({command-or-agent-file}:L..)`

---

## Section 3 — Configs

### `{config-file}` (vd settings.json)
```json
// Đã redact: tokens, API keys
{nội dung config với placeholders}
```
Citation: `({path}:L..-L..)`

**Config guard log**:
- Included (user approved, after redaction): {list}
- Hard-blocked: {list}
- Skipped by user: {list}
- Configs not read (--allow-configs not set): {list}

---

## Section 4 — Slash commands

| Name | Purpose (1 line) | Inputs (args) | Outputs (state/file changes) | Mode | Citation |
|------|------------------|---------------|------------------------------|------|----------|
| `/contextd-setup` | Initialize contextd config for new project | none | creates `.contextd/config.json` + optional legacy adapter + workspace skeleton | interactive | `(.claude/commands/contextd-setup.md:L1-L20)` |

---

## Section 5 — Sub-agents & system prompts

| Name | Role (1 line) | Tools allowed | When to use | Citation |
|------|---------------|---------------|-------------|----------|
| {agent-name} | {role} | {tools or "all" or "_(not declared)_"} | {trigger} | `(agents/{file}:L..)` |

> Bao gồm cả `.claude/agents/*.md` (nếu có) và `agents/**/*.md` (system-prompt-style files).

---

## Section 6 — Pipeline stages / Modules

### Pipeline stages (nếu có `agents/pipeline/`)
| Order | Stage | Role | Citation |
|-------|-------|------|----------|
| 1 | task-to-docs-map | Parse user task → intent JSON | `(agents/pipeline/task-to-docs-map.md:L..)` |
| 2 | task-to-docs-map | Map intent → wiki paths to retrieve | `(agents/pipeline/task-to-docs-map.md:L..)` |

### Functional modules (nếu không có pipeline)
| Module | Role | Citation |
|--------|------|----------|
| {module-dir} | {role} | `({path}:L..)` |

---

## Section 7 — Templates

| Name | Output artifact type | Used by | Citation |
|------|----------------------|---------|----------|
| `service.md` | service doc skeleton | `/evidence-apply`, manual create | `(templates/service.md:L..)` |
| `pattern.md` | pattern doc skeleton | `/evidence-apply` | `(templates/pattern.md:L..)` |

---

## Section 8 — Hooks & settings

### Hooks (từ `settings.json` / `.claude/settings.json`)
| Event | Matcher | Command | Purpose | Citation |
|-------|---------|---------|---------|----------|
| PreToolUse | {pattern} | `{cmd}` | {role} | `(settings.json:L..)` |

### Permissions (allow / deny patterns)
| Type | Pattern | Citation |
|------|---------|----------|
| allow | `Bash(git:*)` | `(settings.json:L..)` |

### Env vars khai báo
| Name | Purpose | Citation |
|------|---------|----------|

> Nếu không có `settings.json` được include → `_(not analyzed — pass --allow-configs to include settings.json)_`.

---

## Section 9 — Git summary

### Last 50 commits (oneline)
```
{sha7} {date} {author} — {subject}
...
```

> Repos không git → `_(unmanaged — no git history. git_sha = unmanaged-{...})_`.

### Top contributors (last 1 year)
| Author | Commits |
|--------|---------|
| {name} | {N} |

### Notable commits (mention "decision", "chose", "switch", "deprecate")
| SHA | Date | Subject |
|-----|------|---------|

---

## Section 10 — Notes

{Surprising observations: orphaned commands không có agent reference, agents tham chiếu file không tồn tại, hooks không match command nào, pipeline stage không có downstream consumer. KHÔNG đoán; chỉ ghi observation kèm citation.}
