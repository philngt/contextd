# contextd
**A scoped context daemon for AI coding agents.**

Strict per-project knowledge isolation. Layered packs. Deterministic retrieval.

Designed for developers running Claude Code across multiple projects/companies who need agents that don't mix context between repos. If Claude starts borrowing knowledge from the wrong codebase, `contextd` gives you scoped, repeatable, contract-driven context.

> Repo currently lives at `tanphuc16797/workspace-wiki` on GitHub — rename to `contextd` is pending. URLs below still point to the legacy slug.

## Onboarding

> **Vietnamese:** [Onboarding (VI)](https://tanphuc16797.github.io/workspace-wiki/onboarding/index.html) · [Install Guide (VI)](https://tanphuc16797.github.io/workspace-wiki/onboarding/install.html)

> **English:** [Onboarding (EN)](https://tanphuc16797.github.io/workspace-wiki/onboarding/index.en.html) · [Install Guide (EN)](https://tanphuc16797.github.io/workspace-wiki/onboarding/install.en.html)

## Thesis (non-negotiables)

1. **Workspace isolation is mandatory**  
   Retrieval and context generation are scoped to the active workspace for the current codebase.

2. **Runtime context over static documentation**  
   This repo is built to feed agents with task-relevant context, not just to serve as a human-readable wiki.

3. **Packs are cognitive scaffolds, not just templates**  
   Packs are reusable reasoning modules that shape task framing, validation, and execution quality.

4. **Claude Code-first support**  
   Official support currently targets Claude Code only (CLI + IDE extension).

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

- **Runtime support**: Claude Code only (CLI and IDE extension).
- macOS/Linux: `bash` required.
- Windows: PowerShell + Git Bash or WSL recommended for shell installer execution.
- Write access to `~/.claude/` required.
- Release installer prerequisites: `curl` or `wget`, plus `unzip`.

If broader runtime support is needed later, maintain a clear compatibility matrix per runtime.

## Mental Model

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

Enable packs via:

- Workspace default: `workspaces/{ws}/workspace.md` → `## Packs`
- Per-codebase override: `<cwd>/.claude/wiki.json` → `packs` (replace semantics)

See [packs/README.md](packs/README.md) for the full catalog.

## Engine & Workspace Reference

- Engine folders: [agents/](agents/), [templates/](templates/), [.claude/commands/](.claude/commands/)
- Workspace structure and overrides: [workspaces/README.md](workspaces/README.md)

## How to Use

### First-time setup (run once)

**Short one-liners from GitHub Release assets** (generated per release tag):

```bash
curl -fsSL https://github.com/tanphuc16797/workspace-wiki/releases/latest/download/install.sh | sh
```

PowerShell (Windows):

```powershell
iwr https://github.com/tanphuc16797/workspace-wiki/releases/latest/download/install.ps1 -UseBasicParsing | iex
```

### Secure install (verify SHA256 before run)

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

Or install from source in this repository (developer/local flow):

```bash
bash scripts/install-to-claude.sh
bash scripts/install-to-claude.sh --dry-run
bash scripts/install-to-claude.sh --force
```

### Start a session (inside a codebase)

```text
/list-workspaces
/switch-workspace {name}
```

### When you receive a task

```text
/contextd-use "Add Kafka consumer..."
```

### After coding

```text
/contextd-update
/contextd-rebase
```

### Create a new workspace

```text
/new-workspace {name}
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
- Missing `.claude/wiki.json`: run `/contextd-setup` or `/switch-workspace`.
- Wrong workspace context: verify `workspace` in `<cwd>/.claude/wiki.json`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
