# Workspace Wiki
> **Vietnamese:** [Onboarding (VI)](https://tanphuc16797.github.io/workspace-wiki/onboarding/index.html) · [Install Guide (VI)](https://tanphuc16797.github.io/workspace-wiki/onboarding/install.html)

> **English:** [Onboarding (EN)](https://tanphuc16797.github.io/workspace-wiki/onboarding/index.en.html) · [Install Guide (EN)](https://tanphuc16797.github.io/workspace-wiki/onboarding/install.en.html)

> **Quick start:** New to this repo? Go straight to [QUICKSTART.md](QUICKSTART.md) — from `git clone` to your first `/use-wiki` in about 5 minutes.

## Purpose

*A workspace-isolated knowledge engine for Claude Code.*

A single source of truth for system knowledge, consumed by both developers and AI agents, organized by workspace for users operating across multiple companies/projects.

## Who This Is For

- You use Claude Code across multiple projects/companies and need strict workspace-level knowledge isolation.
- You are an engineer/tech lead and want an engine + slash commands + patterns so AI agents can retrieve context consistently.
- You are a product manager, operations lead, business analyst, or domain expert who needs structured, reusable team knowledge without writing code every day.
- You are a solo builder using Claude Code as a no-code/low-code IDE and want guided tool design before implementation.
- You maintain onboarding, runbooks, and process docs and want AI outputs to follow team standards by default.
- Not a good fit if you only need a static human-readable wiki without agent workflows.

## Current Support Scope

This plugin currently supports **Claude Code only** (CLI and IDE extension). Other agent/tooling runtimes are not officially supported yet.

If broader runtime support is needed later, maintain a clear compatibility matrix per runtime.

## Prerequisites / Compatibility

- Claude Code is installed and runs locally.
- macOS/Linux: `bash` is required. Windows: PowerShell + Git Bash or WSL for shell installer execution.
- Write access to the user home directory for `~/.claude/`.
- For release installer usage: `curl` or `wget`, plus `unzip`.

## Quick Start Paths

- Fastest path: [QUICKSTART.md](QUICKSTART.md)
- Visual onboarding (EN): [onboarding/index.en.html](onboarding/index.en.html)
- Step-by-step install (EN): [onboarding/install.en.html](onboarding/install.en.html)

## Mental Model

> AI agents consume this wiki as **runtime context**, not static docs. Each workspace is an isolated knowledge sandbox and must never leak into another workspace.

Wiki = **engine** (shared) + **N workspaces** (independent sandboxes).

```text
wiki-template/
├── agents/         ← ENGINE — system prompt, pipeline, coding rules (workspace-agnostic)
├── templates/      ← ENGINE — templates for new workspaces and docs
├── .claude/        ← ENGINE — slash commands
└── workspaces/     ← N workspaces, each with platform/domains/projects/... data
    └── {name}/...

# Active workspace is per-codebase, stored in <project>/.claude/wiki.json.workspace
# (there is no global pointer file inside wiki-template)
```

## Packs (Stack-specific Knowledge)

Packs are stack/use-case knowledge layers between engine and workspace:

- Engine: shared, stack-agnostic rules and pipeline.
- Packs: stack-specific rules/patterns/contracts (web-api, event-driven, frontend, agentic, product, ...).
- Workspace: company/project-specific domain and implementation knowledge.

How to enable packs:

- Workspace default: declare packs in `workspaces/{ws}/workspace.md` under `## Packs`.
- Per-codebase override: set `<cwd>/.claude/wiki.json` field `packs` (replace semantics).

See current catalog at [packs/README.md](packs/README.md).

## Engine — Folder Reference

| Folder | Purpose |
|--------|---------|
| [agents/](agents/) | System prompt, coding rules, constraints, pipeline (intent → retrieval → filter → validate). Engine defaults apply to all workspaces; a workspace may override via `{ws}/agents/`. |
| [templates/](templates/) | Templates for new workspace docs ([workspace.md](templates/workspace.md), [service.md](templates/service.md), [adr.md](templates/adr.md), [runbook.md](templates/runbook.md)) |
| [.claude/commands/](.claude/commands/) | Slash commands for Claude Code |

## Workspaces — Folder Reference

See [workspaces/README.md](workspaces/README.md) for workspace structure, active pointer behavior, and overrides.

Each workspace includes:

| Folder | Purpose |
|--------|---------|
| `platform/` | Shared technical knowledge for a company/project: patterns, contracts, architecture, infrastructure |
| `domains/` | Business domain rules and workflows |
| `projects/` | Per-system implementation knowledge |
| `runbooks/` | Incident handling procedures |
| `decisions/` | Workspace-level ADRs |
| `patterns-index.md` | Quick lookup for workspace patterns/contracts |
| `workspace.md` | Metadata: company, role, period, stack |
| `agents/` (optional) | Workspace overrides for constraints/validator rules |

## How to Use

### First-time setup (run once)

**Short one-liners from release assets:**

```bash
curl -fsSL https://github.com/tanphuc16797/workspace-wiki/releases/latest/download/install.sh | sh
```

PowerShell (Windows):

```powershell
iwr https://github.com/tanphuc16797/workspace-wiki/releases/latest/download/install.ps1 -UseBasicParsing | iex
```

### Secure install (verify SHA256 before run)

Download installer + checksum file from release assets, verify SHA256, then run.

```bash
TAG="vX.Y.Z"
BASE_URL="https://github.com/tanphuc16797/workspace-wiki/releases/download/${TAG}"
curl -fL -o install.sh "${BASE_URL}/install.sh"
curl -fL -o SHA256SUMS.txt "${BASE_URL}/SHA256SUMS.txt"
grep ' install.sh$' SHA256SUMS.txt | shasum -a 256 -c -
sh install.sh
```

PowerShell (Windows):

```powershell
$Tag = "vX.Y.Z"
$BaseUrl = "https://github.com/tanphuc16797/workspace-wiki/releases/download/$Tag"
Invoke-WebRequest "$BaseUrl/install.ps1" -OutFile "install.ps1"
Invoke-WebRequest "$BaseUrl/SHA256SUMS.txt" -OutFile "SHA256SUMS.txt"
$expected = (Select-String -Path .\SHA256SUMS.txt -Pattern ' install.ps1$').Line.Split(' ')[0].Trim()
$actual = (Get-FileHash .\install.ps1 -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $expected.ToLower()) { throw "SHA256 mismatch for install.ps1" }
.\install.ps1
```

Or install from source in the current repository:

```bash
bash scripts/install-to-claude.sh             # sync everything
bash scripts/install-to-claude.sh --dry-run   # preview only
bash scripts/install-to-claude.sh --force     # overwrite global config if needed
```

Re-run after each `git pull` to sync latest commands/agents. The script is idempotent and does not touch user-created files under `~/.claude/commands/`.

### Start a session (inside a codebase)

```text
/list-workspaces                    # list available workspaces and current mapping for this codebase
/switch-workspace {name}            # switch workspace for this codebase (writes <cwd>/.claude/wiki.json)
```

> Each codebase declares its workspace in `.claude/wiki.json`. Run `/wiki-setup` once to create it.

### When you receive a task

```text
/use-wiki "Add Kafka consumer..."   # parse intent → retrieve {ws}/... → write .claude/context/current-task.md
```

Use this at the start of a new task; expected output is a correctly mapped context file for the active workspace.

### After coding

```text
/update-wiki                        # sync wiki with code changes (active workspace only)
```

Use this when logic/code changes materially; expected output is updated pattern/contract/service docs.

### Onboard a new project or validate stale wiki

```text
/rebase-wiki                        # verify wiki vs codebase in active workspace
```

Use this to reconcile drift between code and knowledge; expected output is a gap list with update recommendations.

### Promote Obsidian notes to evidence pipeline

```text
/obsidian-ingest                    # scan vault RAW/, dedupe, ingest ready items → {ws}/evidence/sources/
/obsidian-ingest --dry-run          # preview only
```

> Requires `obsidian.vault_path` in `~/.claude/wiki-global.json` (see [templates/wiki-global.json](templates/wiki-global.json)).

### Create a new workspace (new company/project)

```text
/new-workspace {name}               # scaffold from templates/workspace.md
```

## Priority Order (for AI agents)

```text
Contracts > Platform Patterns > Project Documentation > Domain Knowledge
```

This priority applies **within the active workspace scope only** — never mix knowledge across workspaces.

## Maintenance Rules

- **Single source of truth per workspace**: keep patterns in `{ws}/platform/patterns/`; do not duplicate across workspaces.
- **Link, don’t duplicate**: cross-reference using relative links within the same workspace.
- **Rebase continuously**: run `/update-wiki` when code changes.
- **Agent-first design**: write for machine retrieval, not just human reading.
- **Workspace isolation is sacred**: global rules go to engine; workspace-specific rules stay in `{ws}/agents/`.

## Deploy GitHub Pages

This repo uses workflow [deploy-pages.yml](.github/workflows/deploy-pages.yml):

- Trigger: `push` to `main` or manual `workflow_dispatch`
- Build flow:
  1. run `bash scripts/package-release.sh`
  2. collect `onboarding/` and `release/` for Pages artifact
  3. deploy to `github-pages` environment
- Published paths:
  - `https://tanphuc16797.github.io/workspace-wiki/onboarding/...`
  - `https://tanphuc16797.github.io/workspace-wiki/release/...`

Enable Pages via **Settings → Pages → Build and deployment → Source: GitHub Actions**.

## Release

This repo uses workflow [release.yml](.github/workflows/release.yml):

- Trigger:
  - semver tag push `v*.*.*` (example: `v1.2.0`)
  - manual `workflow_dispatch`
- Workflow runs `scripts/package-release.sh`, then creates a GitHub Release and uploads release assets.

Recommended tag flow:

```bash
git tag v1.2.0
git push origin v1.2.0
```

## Troubleshooting

- **Slash commands not visible after install**: run `bash scripts/install-to-claude.sh` again, then restart Claude Code session.
- **Missing `.claude/wiki.json` in a codebase**: run `/wiki-setup` or `/switch-workspace`.
- **Commands run but context is empty/wrong workspace**: verify `workspace` in `<cwd>/.claude/wiki.json` matches the current repo.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution workflow, PR guidelines, and wiki quality expectations.

## License

This repository is released under the [MIT](LICENSE) license.
