# contextd
**A scoped context daemon for AI coding agents.**

Strict per-project knowledge isolation. Layered packs. Deterministic retrieval.

Designed for developers using AI coding agents across multiple projects/companies who need agents that don't mix context between repos. The canonical runtime namespace is `.contextd`; Claude Code, Codex, Cursor, and plain markdown exports are adapters over the same deterministic context engine.


## Onboarding

> **Vietnamese:** [Onboarding (VI)](https://philngt.github.io/contextd/onboarding/index.html) · [Install Guide (VI)](https://philngt.github.io/contextd/onboarding/install.html)

> **English:** [Onboarding (EN)](https://philngt.github.io/contextd/onboarding/index.en.html) · [Install Guide (EN)](https://philngt.github.io/contextd/onboarding/install.en.html)

## Thesis (non-negotiables)

1. **Workspace isolation is mandatory**  
   Retrieval and context generation are scoped to the active workspace for the current codebase.

2. **Runtime context over static documentation**  
   This repo is built to feed agents with task-relevant context, not just to serve as a human-readable wiki.

3. **Packs are cognitive scaffolds, not just templates**  
   Packs are reusable reasoning modules that shape task framing, validation, and execution quality.

4. **Runtime-neutral core, adapter-specific surfaces**
   `.contextd/config.json` and the CLI are canonical. Claude Code slash commands, Codex skills, Cursor rules, and plain bundles consume the same workspace knowledge through adapters.

5. **Deterministic knowledge priority**  
   Contracts > Platform Patterns > Project Documentation > Domain Knowledge.

## Who This Is For

- Teams using Claude Code across multiple projects/companies and needing strict workspace-level isolation.
- Engineers/tech leads who want reusable patterns + commands so agent output is consistent.
- Product/ops/domain teams who need structured knowledge that agents can execute against.
- Also useful for solo builders and platform/documentation owners who want repeatable AI-assisted workflows.

Not a good fit if you only need a static human-readable wiki without agent workflows.

## Project Status

This project is maintained on a **best-effort** basis.

- Community contributions are welcome
- If maintainer capacity changes, the project may move to maintenance mode or archive status

Use is provided under the repository license ([MIT](LICENSE)) and is offered **"AS IS"**, without warranty.

## Support & Compatibility

| Capability | Status |
|---|---|
| Claude Code slash commands | Stable |
| Claude Code subagents | Stable |
| Workspace/packs markdown engine | Stable |
| CLI: resolve/find/bundle | Available (`pip install -e .`) |
| CLI: deterministic task context | Available (`contextd context`) |
| Plain markdown bundle export | Available |
| Codex skill/plugin export | Available |
| Cursor rules export | Available |
| MCP stdio tools adapter | Available (`contextd mcp-server`) |

**System requirements**
- macOS/Linux: `bash` required.
- Windows: PowerShell + Git Bash or WSL recommended for shell installer execution.
- Write access to `~/.contextd/` for global config. Claude Code adapters still write to `~/.claude/`.
- Release installer prerequisites: `curl` or `wget`, plus `unzip`.

## Roadmap: Runtime-Agnostic Context

contextd is a markdown-first context engine:

1. **CLI core**: `contextd resolve`, `contextd find`, `contextd bundle`
2. **Task context artifact**: `contextd context "task" --format json`
3. **Manifest index**: `.contextd/manifest.json`
4. **Runtime export/adapters**: plain markdown, Codex skill/plugin, Cursor rules, Claude Code artifacts, MCP stdio tools

Existing `.claude/commands` and `.claude/agents` remain supported adapters during the migration window, but `.contextd/config.json` is the canonical project config.

## Non-goals

- contextd is not a vector database.
- MCP is optional. contextd does not require an MCP SDK, remote MCP server, or orchestrator runtime.
- contextd does not replace the coding agent; it prepares scoped, auditable context for the agent.

## Mental Model

contextd = **engine** (shared) + **N workspaces** (independent sandboxes).

```text
contextd/
├── agents/         ← ENGINE — system prompt, pipeline, coding rules (workspace-agnostic)
├── templates/      ← ENGINE — templates for new workspaces and docs
├── .contextd/      ← ENGINE — manifest/config/context runtime namespace
├── .claude/        ← ADAPTER — Claude Code slash commands
└── workspaces/     ← N workspaces, each with platform/domains/projects/... data
    └── {name}/...

# Active workspace is per-codebase, stored in <project>/.contextd/config.json.
```

### Compatibility: Legacy Adapters

Legacy `<project>/.claude/wiki.json` and `<project>/.Codex/wiki.json` are read as adapters during the migration window. They are not the source of truth.

## Packs (Stack-specific Knowledge)

Packs are stack/use-case knowledge layers between engine and workspace:

- Engine: shared, stack-agnostic rules and pipeline.
- Packs: stack-specific rules/patterns/contracts (web-api, event-driven, frontend, agentic, product, ...).
- Workspace: company/project-specific domain and implementation knowledge.

Enable packs via:

- Workspace default: `workspaces/{ws}/workspace.md` → `## Packs`
- Per-codebase override: `<cwd>/.contextd/config.json` → `packs` (replace semantics)

See [packs/README.md](packs/README.md) for the full catalog.

## Engine & Workspace Reference

- Engine folders: [agents/](agents/), [templates/](templates/), [.claude/commands/](.claude/commands/)
- Workspace structure and overrides: [workspaces/README.md](workspaces/README.md)

## How to Use

### First-time setup (run once)

**Short one-liners from GitHub Release assets** (generated per release tag):

```bash
curl -fsSL https://github.com/philngt/contextd/releases/latest/download/install.sh | sh
```

PowerShell (Windows):

```powershell
iwr https://github.com/philngt/contextd/releases/latest/download/install.ps1 -UseBasicParsing | iex
```

### Secure install (verify SHA256 before run)

```bash
TAG="vX.Y.Z"
BASE_URL="https://github.com/philngt/contextd/releases/download/${TAG}"
curl -fL -o install.sh "${BASE_URL}/install.sh"
curl -fL -o SHA256SUMS.txt "${BASE_URL}/SHA256SUMS.txt"
grep ' install.sh$' SHA256SUMS.txt | shasum -a 256 -c -
sh install.sh
```

PowerShell (Windows):

```powershell
$Tag = "vX.Y.Z"
$BaseUrl = "https://github.com/philngt/contextd/releases/download/$Tag"
Invoke-WebRequest "$BaseUrl/install.ps1" -OutFile "install.ps1"
Invoke-WebRequest "$BaseUrl/SHA256SUMS.txt" -OutFile "SHA256SUMS.txt"
$expected = (Select-String -Path .\SHA256SUMS.txt -Pattern ' install.ps1$').Line.Split(' ')[0].Trim()
$actual = (Get-FileHash .\install.ps1 -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $expected.ToLower()) { throw "SHA256 mismatch for install.ps1" }
.\install.ps1
```

Or install from source in this repository (developer/local flow):

```bash
bash scripts/install-to-claude.sh
bash scripts/install-to-claude.sh --knowledge-root ~/contextd --default-workspace default
bash scripts/install-to-claude.sh --dry-run
bash scripts/install-to-claude.sh --force
```

If your workspaces live in a separate team repo:

```bash
bash scripts/install-to-claude.sh --knowledge-root ~/company-wiki --default-workspace shared
```

### Migrate an existing codebase config

```bash
contextd migrate-config --dry-run
contextd migrate-config
```

This creates `<project>/.contextd/config.json` from an existing `.claude/wiki.json` or `.Codex/wiki.json`. The legacy file may remain in place for compatibility.

### Start a session (inside a codebase)

```text
/list-workspaces
/switch-workspace {name}
```

### When you receive a task

```text
/use-contextd "Add Kafka consumer..."
```

Or with the runtime-neutral CLI:

```bash
contextd context "Add Kafka consumer..." --format json
contextd contract-path citation-format
```

### MCP Adapter

Run contextd as a local stdio MCP tools server:

```bash
contextd mcp-server --knowledge-root ~/contextd --workspace default
contextd mcp-config --client codex --knowledge-root ~/contextd --workspace default
```

See [docs/mcp.md](docs/mcp.md) for Claude, Cursor, Codex snippets, security notes, and tool details.

### After coding

```text
/update-contextd
/rebase-contextd
```

### Create a new workspace

```text
/new-workspace {name}
```

## Codex Usage

contextd can also be used with OpenAI Codex CLI via the exported skill.

1. Install the CLI:
   ```bash
   pip install -e .
   ```
2. Install the Codex skill:
   ```bash
   bash scripts/setup-codex-skills.sh
   ```
   Or, if contextd CLI is already installed:
   ```bash
   contextd export --runtime codex-plugin --install
   ```
3. In any project with `.contextd/config.json`, Codex can now use contextd:
   ```bash
   codex 'Run contextd resolve and find the relevant contract for this task'
   ```

## Deploy GitHub Pages

Workflow: [deploy-pages.yml](.github/workflows/deploy-pages.yml)

- Trigger:
  - `push` to `main` when `onboarding/**` changes
  - manual `workflow_dispatch`
- Build flow:
  1. `bash scripts/package-release.sh`
  2. collect `onboarding/` and `release/`
  3. deploy to `github-pages`

## Release

Workflow: [release.yml](.github/workflows/release.yml)

- Trigger:
  - semver tag push `v*.*.*`
  - manual `workflow_dispatch`
- Flow: package release artifacts, then publish GitHub Release assets.

## Troubleshooting

- Slash commands not visible: re-run `bash scripts/install-to-claude.sh` and restart Claude Code.
- Missing `.contextd/config.json`: run `contextd migrate-config`, `/contextd-setup`, or `/switch-workspace`.
- Wrong workspace context: verify `workspace` in `<cwd>/.contextd/config.json`; legacy adapters are lower priority during migration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
