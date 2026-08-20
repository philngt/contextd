# contextd
**Build system for AI coding-agent context.**

contextd compiles workspace knowledge, packs, contracts, and policies into deterministic context artifacts for Claude, Codex, Cursor, and MCP.

## What contextd Does in One Task

contextd turns team knowledge into a build artifact an agent can actually consume:

```mermaid
flowchart LR
  Config["Project config<br/>.contextd/config.json"]
  Knowledge["Workspace knowledge<br/>contracts, patterns, project docs"]
  Static["Shared inputs<br/>packs, engine policies"]
  Synapse["Synapse<br/>lifecycle nodes + typed edges"]
  Build["Build<br/>contextd context &quot;task&quot;"]
  Artifact["Artifact<br/>current-task.json"]
  Agents["Agents<br/>Claude, Codex, Cursor, MCP"]

  Config --> Build
  Knowledge --> Synapse
  Synapse --> Build
  Static --> Build
  Build --> Artifact
  Artifact --> Agents
```

The artifact records what was selected, what was dropped, what is missing, and which source hashes produced the result. `contextd explain` makes that build trace human-readable:

```text
$ contextd explain "prepare agent context for product requirements" --text
Workspace: default
Intent: <detected intent> / <detected workstream>
Context Pack: <context-pack-hash>
Synapse: <synapse-hash>
Budget: <selected>/<limit> docs, ~<estimated> tokens

Selected Docs
- <workspace-scoped contract, pattern, or project document> [category]

Dropped Docs
- <candidate excluded by budget or policy> [category]

Gaps
- <missing knowledge, or (none)>

Warnings
- <lifecycle, freshness, configuration, or safety warning, if any>
```

This is an abbreviated output shape rather than a golden result: selected documents
change when governed knowledge changes. For the same task, `--format json` includes
selected and dropped docs, warning count, budget report, synapse projection, and
`source_hashes` for reproducibility.


## Onboarding

> **Vietnamese:** [Onboarding (VI)](https://philngt.github.io/contextd/onboarding/index.html) · [Install Guide (VI)](https://philngt.github.io/contextd/onboarding/install.html)

> **English:** [Onboarding (EN)](https://philngt.github.io/contextd/onboarding/index.en.html) · [Install Guide (EN)](https://philngt.github.io/contextd/onboarding/install.en.html)

## Thesis (non-negotiables)

1. **Agent context is a build artifact**
   Team knowledge is source material; `contextd context` compiles the task-specific artifact consumed by agent adapters.

2. **Workspace isolation is mandatory**
   Retrieval and context generation are scoped to the active workspace for the current codebase.

3. **Packs are cognitive scaffolds, not just templates**  
   Packs are reusable reasoning modules that shape task framing, validation, and execution quality.

4. **Runtime-neutral core, adapter-specific surfaces**
   `.contextd/config.json` and the CLI are canonical. Claude Code slash commands, Codex skills, Cursor rules, and plain bundles consume the same workspace knowledge through adapters.

5. **Deterministic knowledge priority**  
   Contracts > Platform Patterns > Project Documentation > Domain Knowledge.

6. **Old knowledge remains inspectable**
   Synapse lifecycle and freshness metadata lower stale guidance during context
   compilation without deleting the historical node.

## Who This Is For

- Teams using AI coding agents across multiple projects/companies and needing strict workspace-level isolation.
- Engineers/tech leads who want reusable patterns + runtime adapters so agent output is consistent.
- Product/ops/domain teams who need structured knowledge that agents can execute against.
- Also useful for solo builders and platform/documentation owners who want repeatable AI-assisted workflows.

Not a good fit if you only need a static human-readable wiki without agent workflows.

## Project Status

This project is maintained on a **best-effort** basis.

- Community contributions are welcome
- If maintainer capacity changes, the project may move to maintenance mode or archive status

Use is provided under the repository license ([MIT](LICENSE)) and is offered **"AS IS"**, without warranty.

## Support & Compatibility

contextd is local-first: it requires no hosted service, API key, vector database,
or remote memory service. For the complete command inventory, run
`contextd help --all`.

| Surface | Level | Notes |
|---|---|---|
| Core CLI and deterministic context artifacts | Stable | Primary, release-validated runtime |
| Workspace and pack engine | Stable | Workspace isolation plus manifest-v2/v3 pack support |
| Claude Code adapter | Stable | Slash commands and subagents |
| Markdown, Codex, and Cursor exports | Supported | Generated from the canonical context runtime |
| MCP stdio adapter | Supported | Local stdio transport; no remote MCP service required |
| Legacy `.claude/wiki.json` and `.Codex/wiki.json` | Migration only | Compatibility adapters; `.contextd/config.json` is canonical |

**Support levels**

- **Stable** — primary surfaces covered by release validation.
- **Supported** — shipped and tested, but adapter details may continue to evolve.
- **Migration only** — retained temporarily for existing installations.

For operating-system support, prerequisites, and binary availability, see the
[Install Matrix](#install-matrix). For maintenance expectations, see
[Project Status](#project-status).

## Mental Model: Build Agent Context

contextd is a local build system for agent inputs:

1. **Start/check**: `contextd init`, `contextd check`
2. **Lifecycle graph**: `contextd synapse --preview` builds the workspace-scoped, rebuildable knowledge index
3. **Daily task artifact**: `contextd context "task" --preview`, with `contextd explain "task" --text` for selection trace
4. **Manifest index**: `.contextd/manifest.json`
5. **Runtime export/adapters**: `contextd connect`, plain markdown, Codex skill/plugin, Cursor rules, Claude Code artifacts, MCP stdio tools

Existing `.claude/commands` and `.claude/agents` remain supported adapters during the migration window, but `.contextd/config.json` is the canonical project config.

For the deeper model, see [docs/build-system-model.md](docs/build-system-model.md). It explains source inputs, build graph, artifact lifecycle, determinism boundaries, and common failure modes.

## Non-goals

- contextd is not a vector database.
- contextd is not a code graph indexer or AST/LSP analysis engine.
- MCP is optional. contextd does not require an MCP SDK, remote MCP server, or orchestrator runtime.
- contextd does not replace the coding agent; it builds scoped, auditable inputs for the agent.

## Works With Code Intelligence Tools

Tools such as code graph MCP servers help agents understand code structure: symbols, call paths, routes, dependencies, and blast radius. contextd solves a different layer: it makes agents use the right team knowledge, contracts, policies, workspace boundaries, and task-specific evidence.

Use them together when useful:

- Code intelligence answers "what does this codebase contain?"
- contextd answers "what rules, decisions, docs, and constraints should the agent use for this task?"

See [docs/comparison.md](docs/comparison.md) for positioning against MCP, code graph tools, Cursor rules, Claude memory, vector DBs, and knowledge bases.

## Repository Model

contextd = **build engine** (shared) + **N workspaces** (source knowledge) + **adapter outputs**.

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

## OKF (Open Knowledge Format)

Knowledge files in `workspaces/{ws}/` follow [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) — an open, human- and agent-friendly format for knowledge metadata. Every concept file (pattern, contract, decision, runbook, ...) carries a small YAML frontmatter with `type` (required) plus `title`/`description`/`status`/provenance (recommended).

**Why OKF**:

- Agents and tools can parse, filter, and route on `type` without bespoke SDKs or regex over headings.
- Provenance is first-class: `generated: {by, at}`, `verified: [{by, at}]` record who produced and confirmed a concept — trust becomes traceable, not assumed.
- Diffable in version control, portable across tools and organizations, with no registry or central authority.
- Before OKF, frontmatter keys were ad-hoc (`name`, `slug`, `owner`, `source_type`, ...) — the same concept was described differently in every file.

**Mental model when using it**:

- **Frontmatter = metadata, body = knowledge.** The body stays plain markdown for humans; the frontmatter is the machine-readable handle.
- **Every concept file answers three questions**: what kind of thing is this (`type`), what is it (`title`/`description`), and how trustworthy is it (`status` + provenance). If a file can't answer them, it isn't a concept file yet.
- **Write new concepts from templates** in [templates/](templates/) — they already carry the OKF fields; just fill them in.
- **Trust is derived, not claimed**: `status: draft | stable | deprecated`; `verified` by a `human:` actor outranks process-only confirmation.
- **Index and config files are the exception** (`README.md`, `INDEX.md`, `_index.md`, `patterns-index.md`, `workspace.md`) — they are navigation, not concepts, so no frontmatter is required.
- **The linter keeps you honest**: `python scripts/lint-wiki.py` warns on missing/unknown `type`, bad `status`, and unreferenced `sources[].id` — warnings never fail the run (exit 0), per OKF's "tolerate unknown" stance; pass `--strict` for warnings-as-errors.

Full mapping, type set, and enforcement rules: [docs/wiki-reference.md#okf-open-knowledge-format](docs/wiki-reference.md).

## Packs (Stack-specific Knowledge)

Packs are stack/use-case knowledge layers between engine and workspace:

- Engine: shared, stack-agnostic rules and pipeline.
- Packs: stack-specific rules/patterns/contracts (web-api, event-driven, frontend, agentic, product, ...).
- Workspace: company/project-specific domain and implementation knowledge.

New packs use manifest v3: `pack.yaml` owns routing and `knowledge.md` owns
Global Principles plus component-scoped Mental Models, Standards, Failure
Signals, and Evidence/Stop Conditions. Runtime loads only the matched component
sections and reports their static token cost. Existing manifest-v2 packs remain
supported during staged migration. Stable IDs and documented/executable
validator parity are checked by `contextd pack-validate`.

Enable packs via:

- Workspace default: `workspaces/{ws}/workspace.md` → `## Packs`
- Per-codebase override: `<cwd>/.contextd/config.json` → `packs` (replace semantics)

Prefer the smallest pack set that owns the task. Pack context is included in
`budget_report.estimated_tokens_total`; precise selection and routing reduce
noise, while enabling every pack can increase context cost.

When a user can no longer name the current stage, next decision, or reason to
continue, `pack-operator-steering` provides an evidence-backed wayfinding
checkpoint. It makes the AI recommendation visible while keeping material
direction and the `continue|pause|pivot|stop` decision with the human operator.

```bash
contextd pack-validate --all --format text
contextd explain "Review retry-safe payment endpoint" --format text
```

See [packs/README.md](packs/README.md) for the maturity model, current versions,
scope boundaries, selection guide, and authoring checklist.

## Engine & Workspace Reference

- Engine folders: [agents/](agents/), [templates/](templates/), [.claude/commands/](.claude/commands/)
- Workspace structure and overrides: [workspaces/README.md](workspaces/README.md)

## Documentation Map

- This README owns the product thesis, support matrix, architecture, and reference links.
- [QUICKSTART.md](QUICKSTART.md) owns the runnable CLI-first setup and demo flow.
- [onboarding/](onboarding/) owns persona guidance and the bilingual browser-friendly install summary.
- [packs/README.md](packs/README.md) is the canonical pack catalog; onboarding summaries are CI-checked mirrors.
- `contextd help --all` is the canonical CLI command inventory.

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

These install prebuilt `contextd` binaries from GitHub Releases. Users do not need to build the CLI locally.

### Install Matrix

| Platform | Release installer behavior |
|---|---|
| macOS arm64 | Installs `contextd-darwin-arm64`. |
| macOS x86_64 | Installs `contextd-darwin-x86_64`. |
| Linux x86_64 | Installs `contextd-linux-x86_64`. |
| Linux arm64 | No prebuilt binary yet; installer exits with source-install guidance. |
| Windows x86_64 | Installs `contextd-windows-x86_64.exe` via PowerShell. |
| Source checkout | `pip install -e .` works anywhere Python >= 3.10 and Git are available. |

The macOS/Linux installer requires `bash` plus `curl` or `wget`. The Windows
installer requires PowerShell and `Invoke-WebRequest`; use Git Bash or WSL only
when running the shell installer. Global config is written to `~/.contextd/`,
while optional Claude Code adapters write to `~/.claude/`.

### Try the default demo in 2 minutes

The release installer installs the CLI. Clone this repo as a sample `knowledge_root` to try the bundled default workspace:

```bash
git clone https://github.com/philngt/contextd.git ~/contextd
cd ~/contextd
contextd init
contextd check
contextd context "prepare agent context for product requirements" --preview
contextd explain "prepare agent context for product requirements" --text
```

Expected signal: a clean check report, a `contextd_task_context.v1` artifact, focused selected docs, explicit gaps or `(none)`, a budget estimate, and source hashes in JSON output. Maintainers can run `contextd eval --golden --workspace default --text` when validating retrieval quality.

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

For source/developer installation, Claude adapters, and a separate team knowledge
repository, follow [QUICKSTART.md](QUICKSTART.md). The CLI install and host adapter
install are intentionally separate operations.

### Set up a codebase config

```bash
contextd init
contextd check
```

`contextd init` confirms an existing canonical config, migrates a local legacy `.claude/wiki.json` or `.Codex/wiki.json`, or creates a minimal config when the current directory already contains a `workspaces/` tree. For separate team knowledge repos, pass `--knowledge-root /path/to/contextd-or-team-knowledge-root --workspace {name}`.

### Start a session (inside a codebase)

```text
/list-workspaces
/switch-workspace {name}
```

Verify the runtime before asking an agent to work:

```bash
contextd check
```

### When you receive a task

```text
/use-contextd "Add Kafka consumer..."
```

Or with the runtime-neutral CLI:

```bash
contextd context "Add Kafka consumer..." --preview
contextd explain "Add Kafka consumer..." --text
contextd synapse --preview --text
contextd contract-path citation-format
```

`contextd context` emits the canonical JSON artifact. `contextd explain` shows why docs were selected or dropped, including lifecycle score adjustments, gaps, warnings, source hashes, and the lightweight budget report. `contextd synapse` exposes the complete rebuildable lifecycle index; materialized task context stores its task-specific projection. A materializing context build reads and raw-byte-hashes each governed workspace source once, reuses transient source/lookup state during projection, then identity-checks and writes that same graph instead of rebuilding it.

See [docs/context-quality.md](docs/context-quality.md) for budget semantics, safety guard behavior, and rollout scorecards.
See [docs/synapse-context-management.md](docs/synapse-context-management.md) for node authoring, lifecycle review, loading workflows, cost controls, and promotion boundaries.
See [docs/effectiveness.md](docs/effectiveness.md) for measurable signals contextd can prove today without synthetic benchmark claims.

### Production Governance Loop

Use this loop before rolling contextd into a team workflow or after changing packs/workspace knowledge:

```bash
contextd doctor --json
contextd pack-validate --all --json
contextd context "debug context quality" --json --preview
contextd explain "debug context quality" --json
contextd policy-check "debug context quality" --json
contextd eval --golden --workspace default --json
```

- [docs/governance.md](docs/governance.md): policy-as-code over selected context.
- [docs/pack-validation.md](docs/pack-validation.md): versioned pack API, knowledge, routing, and validator checks.
- [docs/evaluation.md](docs/evaluation.md): golden-task evaluation for context selection quality.
- [docs/effectiveness.md](docs/effectiveness.md): adoption metrics and proof signals.
- [docs/build-system-model.md](docs/build-system-model.md): deeper product and artifact model.

### MCP Adapter

Run contextd as a local stdio MCP tools server:

```bash
contextd connect --client codex --knowledge-root ~/contextd --workspace default
contextd connect --client all --knowledge-root ~/company-wiki --workspace shared
```

See [docs/mcp.md](docs/mcp.md) for Claude, Cursor, Codex snippets, security notes, tools, resources, and prompts.

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

contextd can also be used with OpenAI Codex CLI via the exported skill or MCP adapter.

1. Install the `contextd` CLI with the release binary installer above. For source checkout development only:
   ```bash
   pip install -e .
   ```
2. Install the Codex skill from the CLI:
   ```bash
   contextd export --runtime codex-plugin --install
   ```
   If you are working from this source checkout, the helper script is equivalent:
   ```bash
   bash scripts/setup-codex-skills.sh
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
  - manual `workflow_dispatch` with a version matching `pyproject.toml`
- Flow: validate release metadata, run the Python 3.10/3.12 verification
  matrix, package source and binaries, smoke each binary, then publish GitHub
  Release assets.

## Troubleshooting

- Slash commands not visible: re-run `bash scripts/install-to-claude.sh` and restart Claude Code.
- Missing `.contextd/config.json`: run `contextd init`; for legacy-only projects it delegates to `contextd migrate-config`.
- Wrong workspace context: verify `workspace` in `<cwd>/.contextd/config.json`; legacy adapters are lower priority during migration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
