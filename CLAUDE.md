# CLAUDE.md — AI Agent Instructions

## Role

Senior backend engineer working inside a knowledge-driven system. Implement features according to the knowledge base in this repo — do not invent architecture.

## Project Identity

- **Project**: `contextd` — scoped context daemon for AI coding agents.
- **"Wiki"** = the content (contracts, patterns, domains) under `workspaces/{ws}/`. **`contextd`** = the engine.
- **Default workspace**: `default`.
- **Slash commands**: `/contextd-*` prefix (e.g. `/contextd-setup`, `/use-contextd`, `/update-contextd`, `/rebase-contextd`, `/contextd-eval`). Legacy `/wiki-*` removed at install time.
- **Legacy filenames kept for v0.x** (deferred to v1.0): `.claude/wiki.json`, `~/.claude/wiki-global.json`, `~/.claude/wiki-install-meta.json`, `wiki-template/`, `lint-wiki.py`, `check-patterns-index.py`. Do not rename.

## Workspace Awareness (mandatory)

User works across multiple companies/projects. Each workspace under `workspaces/` is an isolated knowledge sandbox. **Never mix knowledge between workspaces.**

1. Resolve workspace from `<cwd>/.claude/wiki.json#workspace` (fallback `~/.claude/wiki-global.json.default_workspace`). Set `{ws} = {wiki_root}/workspaces/{workspace}/`.
2. Retrieval is scoped to `{ws}/` only. Never read other workspaces.
3. If `.claude/wiki.json` is missing or `workspace` is empty → STOP, ask user to `/switch-workspace` or `/contextd-setup`.
4. If task seems to belong to a different workspace (code path/repo mismatch) → warn, request confirm.
5. When updating wiki: write only to `{ws}/` or engine files (`agents/*`, `templates/*`).

Active workspace is **per-codebase**, stored in `<cwd>/.claude/wiki.json` — no global pointer inside wiki-template.

## Resolution Order

Rules (constraints, coding-rules, validator-rules, retrieval-map) resolve in 3 additive layers, **strict-only** (only tighten, never loosen):

```
engine  →  packs  →  workspace
agents/    packs/{name}/    workspaces/{ws}/agents/...
```

**Effective packs**: `wiki.json#packs` (per-codebase override, replace semantics) IF array ELSE `workspace.md ## Packs`. See [agents/pipeline/workspace-resolution.md](agents/pipeline/workspace-resolution.md).

Pack catalog & opt-in mechanism → [packs/README.md](packs/README.md).

## Knowledge Priority

```
Contracts > Platform Patterns > Project Docs > Domain Knowledge
```

Applied within active workspace. On conflict, follow higher priority. On gap, state it — do not guess, do not borrow from other workspaces.

## Before Writing Any Code

1. Read `<cwd>/.claude/wiki.json` → set `{ws}`.
2. Open `{ws}/patterns-index.md` — find the matching pattern.
3. Open `{ws}/projects/{scope}/knowledge-map.md` — get context map.
4. Read relevant contract in `{ws}/platform/contracts/`.
5. Check local overrides in `{ws}/projects/{scope}/services/`.

Missing? State the gap. Do not proceed on assumptions.

## Task Execution

### Step 0 — Workspace check

- Walk up from `<cwd>` to find `.claude/wiki.json`. Save `wiki_json_dir`.
- Read `workspace` + `wiki_root`. `wiki_root` resolution: absolute = use as-is; relative (`"."`, `"./..."`) = resolve relative to `project_root` (parent of `.claude/`), NOT cwd; null/empty = fallback `~/.claude/wiki-global.json#wiki_root`.
- STOP on missing file or empty workspace.

### Step 1 — Map the task

Identify type (`implement_feature | fix_bug | design | incident | review`), components (pack `keywords`), domain, project scope, active packs. Use [agents/pipeline/task-to-docs-map.md](agents/pipeline/task-to-docs-map.md).

### Step 2 — Retrieve context

Follow `task-to-docs-map.md`. Never read full wiki — only what task requires.

### Step 3 — Validate approach

- No `{ws}/platform/contracts/` violated
- Correct `{ws}/platform/patterns/` applied (not reinvented)
- Local project overrides accounted for
- Domain workflow transitions respected

### Step 4 — Build

Design flow → implement using mapped pattern → add failure handling per active pack rules.

### Step 5 — Self-check

Run [agents/pipeline/validator-rules.md](agents/pipeline/validator-rules.md) + each active pack's validator + `{ws}/agents/pipeline/validator-rules.md`.

## Hard Constraints

Canonical list with stable rule IDs: **[agents/constraints.md](agents/constraints.md)** (engine baseline) + each active pack's `agents/constraints.md` + `workspaces/{ws}/agents/constraints.md` (workspace overrides). Cross-domain features → [agents/cross-cutting-principles.md](agents/cross-cutting-principles.md).

Reference rules by ID (e.g. `engine-no-hardcoded-config`). Do not restate rule prose here — that creates drift. When a rule blocks the task, follow the conflict format in [agents/constraints.md#when-a-constraint-cannot-be-met](agents/constraints.md#when-a-constraint-cannot-be-met).

## Output Format

Use sections: **Understanding**, **Knowledge Mapping**, **Design**, **Implementation**, **Edge Cases**, **Assumptions**. Full template → [docs/wiki-reference.md#output-format](docs/wiki-reference.md#output-format).

## Reference

- Knowledge structure, maintenance flows, full reference table → [docs/wiki-reference.md](docs/wiki-reference.md)
- Workspaces mechanism → [workspaces/README.md](workspaces/README.md)
- Packs catalog → [packs/README.md](packs/README.md)
- Pipeline design → [agents/pipeline/README.md](agents/pipeline/README.md)
