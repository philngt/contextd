# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — MCP stdio tools adapter

Added a stdlib-only MCP server surface over the existing contextd runtime:

- `contextd mcp-server --knowledge-root PATH --workspace NAME` runs a newline-delimited stdio JSON-RPC server.
- `contextd mcp-config --client claude|cursor|codex|all --knowledge-root PATH --workspace NAME` prints client snippets without mutating client config files.
- Exposed tools: `contextd.resolve`, `contextd.find`, `contextd.context`, `contextd.contract_path`, and `contextd.bundle`.
- MCP calls are adapter-only: deterministic context artifacts and contracts remain canonical; search remains advisory.

### Changed — Installer knowledge root selection

`scripts/install-to-claude.{sh,py}` now use canonical installer terminology:

- `ENGINE_ROOT` = contextd engine repo used for commands/agents/scripts.
- `KNOWLEDGE_ROOT` = canonical root containing `workspaces/`.
- New `--knowledge-root PATH` flag, with `--knowledge-repo PATH` kept as a compatibility alias.
- New `--default-workspace NAME` and `--print-mcp-config CLIENT` flags.
- Non-interactive installs default `knowledge_root` to the engine repo; interactive shell installs can choose current config root, engine repo root, or a custom path.

### Changed — Release and onboarding MCP guidance

Release installer scripts now print next-step guidance for choosing `knowledge_root`, generating MCP client snippets, and installing source-zip Claude slash-command adapters. Onboarding pages now mention the runtime-neutral CLI and MCP adapter alongside Claude slash commands.

### Changed — Rename three verb commands to `verb-contextd` form

Three slash commands were renamed so the verb leads (matches the legacy `use-wiki / update-wiki / rebase-wiki` aliases the installer already migrates):

| Old | New |
|---|---|
| `/contextd-use` | `/use-contextd` |
| `/contextd-update` | `/update-contextd` |
| `/contextd-rebase` | `/rebase-contextd` |

Other `/contextd-*` commands (setup, detect, eval, trace, viz, report, version, upgrade, backup, restore, explain, admin) are unchanged — they are nouns/admin tools and stay as `contextd-{noun}`.

Definition files renamed under `.claude/commands/`; references updated across pipeline docs, top-level docs (CLAUDE.md, README.md, QUICKSTART.md), pack prompt overrides, onboarding HTML (EN + VI), and the `slash-command-naming.md` contract's evidence list. Installer `LEGACY_MAP` values in `scripts/install-to-claude.{sh,py}` now point to the new names so users upgrading from the `wiki-*` era still land on the right command.

### Changed — Intent + trace schema = single source

`templates/run-trace.schema.json` is now the only place that defines stage payload shape. Removed restated JSON examples from:

- `agents/pipeline/task-to-docs-map.md` — replaced inline intent JSON with a pointer to schema + a clarification that **active packs are not persisted on `intent`** (planner reads `workspace.md ## Packs` directly), eliminating the earlier drift where this doc listed a `packs` field but schema.json didn't.
- `agents/pipeline/multi-agent-pipeline.md` — replaced the Stage 1 intent JSON example with a schema pointer.
- `.claude/agents/contextd-planner.md` — replaced the full output JSON example with a "quick recap" pointing to schema `oneOf[0]`.
- `.claude/agents/contextd-context-selector.md` — same treatment for the `02-context` trace block.
- `.claude/agents/contextd-reviewer.md` — same for `05-review`.

Effect: adding/renaming a field now requires editing one schema file. Examples that used to drift independently across 5 files are gone.

### Changed — Trim `.claude/commands/code-analyze.md` from 506 → 391 lines

Bước 4 (Build snapshot) was duplicating section structure + config-guard logic already defined in `agents/pipeline/code-snapshot-conventions.md` (4.1–4.9 for `variant=code`, 4.A.1–4.A.10 for `variant=agentic-engine`, plus the 4.3.x config-guard sub-steps). Replaced with a variant dispatch table + a config-guard summary, both pointing at the conventions doc for full detail. The unique 4.10 redaction post-pass was preserved.

Other long command files were reviewed but not trimmed — `evidence-{qa,apply,analyze}.md`, `obsidian-ingest.md`, `contextd-setup.md` carry genuine orchestration logic (state-machine transitions, router tables, checkpoint sub-step maps) that isn't duplicated elsewhere.

### Removed — Orphan pipeline stubs

Deleted two migration stubs in `agents/pipeline/` that only existed to redirect historical evidence-snapshot citations:

- `intent-parser.md` — redirected to `task-to-docs-map.md`.
- `evidence-state-rules.md` — redirected to `evidence-lifecycle.md`.

Both stubs were kept for backward-compatibility with the `2026-05-08-engine-bootstrap-wiki-template` evidence snapshot. That snapshot was removed in the `workspaces/default/` trim above, so the stubs serve no purpose. Removed the leftover breadcrumb in `task-to-docs-map.md` that referenced `intent-parser.md`.

`concurrency-notes.md` was kept — it has a legitimate active reference in `observability.md:214`.

### Changed — Single source of truth for engine constraints

`agents/constraints.md` is now the only file that defines engine baseline rule text. Each rule has a stable ID (`engine-no-hardcoded-config`, `engine-no-new-workflow-state`, ...). Other files reference rules by ID instead of restating prose.

- `agents/constraints.md` — added ID prefix convention (`engine-*` / `pack-{name}-*` / `ws-*`) and assigned IDs to all 12 engine baseline rules (3 Architecture, 2 Code, 3 Domain, 4 Knowledge). Reorganized as "Engine Rule Catalog".
- `CLAUDE.md` — removed the 7-bullet "Engine baseline — never" prose list. Replaced with a one-paragraph pointer to `agents/constraints.md` and the conflict format.
- `agents/pipeline/validator-rules.md` Layer 2 self-check — replaced the prose "Constraints to Check" section with rule-ID references (`engine-no-new-workflow-state`, `engine-no-unlisted-transition`, etc.) that load definitions from `agents/constraints.md`.
- Pack `constraints.md` files reviewed — they add stack-specific rules (Kafka topic names, rate-limit values from config, ...) without restating engine baseline rules. No edits needed.

Effect: changing a baseline rule now requires editing only one file. Pack/workspace layers stay additive on top.

### Changed — Trim `workspaces/default/` from 64 → 28 files

Workspace `default` was carrying three roles (seed library + engine-self-documentation + frozen evidence record), causing drift every time the engine changed. Reduced to a single role: seed library of generic platform patterns + contracts that new workspaces can copy.

Removed:
- `workspaces/default/projects/engine/` — entire subtree (services/*.md, THESIS.md, thesis-audit-report.md, knowledge-map.md). The engine spec already lives in `agents/`, `.claude/agents/`, `.claude/commands/`, `scripts/` — duplicating it as workspace content was the main drift source.
- `workspaces/default/decisions/003-self-referential-engine-workspace.md` — ADR that defined the now-removed self-referential role.
- `workspaces/default/platform/patterns/multi-stage-subagent-pipeline.md` — referenced the old 5-stage pipeline (outdated after the plan-reviewer merge).
- `workspaces/default/reports/*.html` + frozen evidence snapshot `evidence/{sources,analysis,qa,applied}/2026-05-08-engine-bootstrap-wiki-template/` — historical artifacts from before the `wiki-template` → `contextd` rebrand.

Kept (the seed library):
- 7 generic platform patterns: citation-rule, evidence-state-machine, secrets-blocklist-gate, redaction-post-pass, askuser-confirm-preview, variant-discriminated-dispatcher, workspace-resolve-step0.
- 8 generic platform contracts: citation-format, evid-id-format, evidence-file-layout, evidence-state-machine-transitions, raw-md-section-structure, slash-command-naming, source-yaml-schema, sub-agent-frontmatter-schema.
- ADRs 001 (agentic-engine variant), 002 (monolithic code-analysis prompts), 004 (pattern-contract pairing).

Updated `workspace.md`, `patterns-index.md`, `evidence/_index.md`, `reports/INDEX.md` to remove "workspace `wiki`" naming and annotate `default` as a seed library, not a self-documenting engine workspace.

Existing `## Source` lines in remaining patterns/contracts still cite the removed evidence ID as textual provenance — this is intentional attribution, not a broken link.

### Changed — Pipeline 5 → 4 stages (merge `contextd-plan-reviewer` into `contextd-context-selector`)

`contextd-plan-reviewer` subagent and its trace stage `03-plan-review` have been removed. The five plan-review checks (planner verify carry-over, pattern/contract in Referenced Docs, component coverage, conflict, gap severity) now run inside `contextd-context-selector`, which already retrieves the docs and writes `current-task.md`. Selector emits `verdict: APPROVED|BLOCK` (plus `issues[]` + `checks_summary`) in the same `02-context.json` trace block.

Rationale: planner + plan-reviewer were both verifying pattern existence (duplicate work); selector already knew what it had retrieved and what was missing. Merging saves one LLM call per `/use-contextd` task and removes ~150 lines of overlapping spec.

Impact:
- **Subagent deleted**: `.claude/agents/contextd-plan-reviewer.md`. `install-to-claude.{py,sh}` now remove it from existing `~/.claude/agents/` installs.
- **Schema**: `templates/run-trace.schema.json` — `03-plan-review` stage removed from enum + oneOf; `02-context` extended with `verdict` (required), `issues[]`, `checks_summary` fields and `pitfalls` category in `referenced_docs`.
- **Scripts**: `emit_trace.py`, `render_trace.py` no longer reference `contextd-plan-reviewer` / `03-plan-review.json`. Rollup detects BLOCK from `02-context.verdict`.
- **Docs**: `agents/pipeline/{multi-agent-pipeline,README,PIPELINE-VISUAL,observability}.md`, `.claude/commands/{use-contextd,contextd-trace,contextd-eval,README}.md`, `templates/task-scorecard.md` updated to 4-stage pipeline.
- **Workspace evidence/reports under `workspaces/default/`** still reference the old 5-stage layout (historical snapshots); will be reconciled via `/update-contextd` in a follow-up.

### Changed — Rebrand `workspace-wiki` → `contextd`

This release rebrands the project. Project name and slash-command prefix change; the *content* layer (workspace knowledge base, still called "wiki") and several legacy filenames are kept for v0.x compatibility.

#### Project name & branding
- Display name `Workspace Wiki` → `contextd` in README, CLAUDE.md, onboarding HTML (VI + EN), GitHub Pages redirect title, and `/contextd-upgrade` / `/contextd-version` command docs.
- New tagline: *"A scoped context daemon for AI coding agents."*
- Added `## Project Identity` section to CLAUDE.md so agents read the new naming on every turn.
- GitHub repo URLs intentionally **unchanged** in this version — still `tanphuc16797/workspace-wiki`. Repo rename and release tagging under the new name were deferred to a follow-up (completed in a later release).

#### Default workspace rename
- Folder `workspaces/wiki/` → `workspaces/default/` (full git rename — history preserved).
- `.claude/wiki.json` pointer field updated to `"workspace": "default"`.
- `workspaces/default/workspace.md` title updated.
- Evidence `manifest.yaml` + `source.yaml` `workspace` fields updated.
- `scripts/package-release.sh` staging filter updated to keep `workspaces/default/`.

#### Slash command rename (`/wiki-*` → `/contextd-*`)
All 14 engine slash commands now use the `/contextd-*` prefix:

| Old | New |
|---|---|
| `/wiki-setup` | `/contextd-setup` |
| `/wiki-detect` | `/contextd-detect` |
| `/wiki-eval` | `/contextd-eval` |
| `/wiki-trace` | `/contextd-trace` |
| `/wiki-viz` | `/contextd-viz` |
| `/wiki-report` | `/contextd-report` |
| `/wiki-explain` | `/contextd-explain` |
| `/wiki-backup` | `/contextd-backup` |
| `/wiki-restore` | `/contextd-restore` |
| `/wiki-upgrade` | `/contextd-upgrade` |
| `/wiki-version` | `/contextd-version` |
| `/use-wiki` | `/contextd-use` |
| `/update-wiki` | `/contextd-update` |
| `/rebase-wiki` | `/contextd-rebase` |

Command H1 titles rewritten to `# /contextd-{verb} — <descriptive>` so the skill listing no longer shows mismatched "Wiki Setup" / "Wiki Eval" labels.

#### Subagent rename
5 subagents in `.claude/agents/` renamed (file + YAML `name:` field + cross-references):

| Old | New |
|---|---|
| `wiki-planner` | `contextd-planner` |
| `wiki-context-selector` | `contextd-context-selector` |
| `wiki-plan-reviewer` | `contextd-plan-reviewer` |
| `wiki-curator` | `contextd-curator` |
| `wiki-reviewer` | `contextd-reviewer` |

#### Release artifacts (migration window)
`scripts/package-release.sh` and `.github/workflows/release.yml` now emit **both** naming conventions in parallel so existing installer URLs keep working:

- Canonical (new): `contextd-{ver}.zip`, `contextd-latest.zip`
- Legacy alias (same content): `wiki-template-{ver}.zip`, `wiki-template-latest.zip`

`install.sh` / `install.ps1` in releases download `contextd-latest.zip`. `SHA256SUMS.txt` includes both.

#### Installer migration
`scripts/install-to-claude.{sh,py}` automatically clean up legacy installs:

- Removes 14 legacy `~/.claude/commands/wiki-*.md` / `~/.claude/commands/{use,update,rebase}-wiki.md` files after syncing the new `contextd-*.md` equivalents.
- Removes 5 legacy `~/.claude/agents/wiki-*.md` subagent files.
- Prints a migration notice telling users to update any codebase `<cwd>/.claude/wiki.json` field `"workspace": "wiki"` → `"default"`.

#### Onboarding HTML
Download buttons in `onboarding/install.{html,en.html}` now point to `contextd-latest.zip`. Titles, headings, and footer branding switched to `contextd` (with `formerly Workspace Wiki` notes in source comments for traceability).

### Kept (deferred to v1.0)
Legacy filenames are intentionally **not** renamed in v0.x to avoid breaking existing user installs and pointer files:

- `<cwd>/.claude/wiki.json` (per-codebase pointer)
- `~/.claude/wiki-global.json` (global pointer)
- `~/.claude/wiki-install-meta.json` (install metadata)
- `wiki-template/` (zip root folder name inside release artifacts)
- `scripts/lint-wiki.py`, `scripts/check-patterns-index.py`
- The noun **"wiki"** as the term for *content* (contracts, patterns, domain docs under `workspaces/{ws}/`). `contextd` = engine; "wiki" = content. See CLAUDE.md `## Project Identity` for the boundary.

### Migration guide

Existing users upgrading to this version:

1. Pull the latest source (or download the new release artifact under either `contextd-latest.zip` or the legacy `wiki-template-latest.zip` — same file).
2. Re-run `bash scripts/install-to-claude.sh` (or `python scripts/install-to-claude.py`). The installer will:
   - Sync the new `contextd-*` slash commands and subagents into `~/.claude/`.
   - Remove the 14 legacy `wiki-*.md` / `*-wiki.md` command files and 5 legacy `wiki-*.md` subagent files.
   - Print a migration notice.
3. For each codebase whose `<cwd>/.claude/wiki.json` references the old default workspace name, update the field:
   ```diff
   - "workspace": "wiki"
   + "workspace": "default"
   ```
   Or re-run `/switch-workspace default` from inside that codebase.
4. Restart Claude Code so the new slash commands are picked up.

No data migration is required for evidence, contracts, patterns, decisions, or runbooks — the folder is renamed in place by git mv.

---

For history before this rebrand, see [git log](https://github.com/philngt/contextd/commits/main).
