# Build System Model

contextd treats agent context as a build artifact. Team knowledge is source material; the CLI compiles a task-specific artifact that agents can consume through Claude, Codex, Cursor, MCP, or plain markdown.

This page explains the product model behind that claim.

## Why A Build System

AI coding agents usually fail on context in predictable ways:

- They read the wrong docs for the current workspace.
- They mix team conventions from different projects.
- They overfit to whatever prompt snippet was pasted most recently.
- They cannot explain why a rule, contract, or runbook was included.
- Their inputs drift across Claude, Codex, Cursor, and MCP clients.

Build systems solve a similar class of problem for software: given declared inputs, produce reproducible outputs, surface missing dependencies, and make failures inspectable. contextd applies that discipline to agent inputs.

## Source Inputs

The main inputs are:

| Input | Purpose |
|---|---|
| `.contextd/config.json` | Selects `knowledge_root`, workspace, and optional per-codebase packs. |
| `workspaces/{workspace}/` | Team-owned source knowledge: contracts, patterns, product docs, requirements, design docs, runbooks, quality evidence, project maps. |
| `packs/{pack}/` | Reusable context rules, component keywords, validation rules, and retrieval maps. |
| `templates/*.schema.json` | Artifact and config contracts used for shape stability. |
| `policy/context-policy.json` | Optional governance rules over selected context. |

Legacy `.claude/wiki.json`, `.Codex/wiki.json`, and `wiki_root` are compatibility adapters. They are inputs only during migration, not the canonical source.

## Build Graph

```text
resolve config
  -> classify task intent and workstream
  -> detect active pack components
  -> collect deterministic candidates
  -> reject unsafe paths and redact sensitive content
  -> rank and slice relevant sections
  -> validate contract paths and gaps
  -> apply policy checks
  -> emit contextd_task_context.v1
  -> optionally render markdown/materialized pack
```

The output is not a memory record and not a search result. It is a compiled artifact with source hashes, selected docs, warnings, gaps, budget information, and governance results.

## Artifact Contract

`contextd context "task" --format json` emits `contextd_task_context.v1`.

Important fields:

| Field | Meaning |
|---|---|
| `workspace` | Active isolated workspace used for retrieval. |
| `intent` | Task type, detected components, workstream, audience, and context goal. |
| `referenced_docs` | Selected source docs with category, path, sliced sections, content, and source hash. |
| `gaps` | Missing or unsafe inputs surfaced explicitly instead of guessed. |
| `warnings` | Compatibility, redaction, adapter, or runtime advisory messages. |
| `contextPack` | Deterministic static context pack reference and source hash. |
| `retrieval_policy` | Retrieval mode, priority, max docs, and advisory-search posture. |
| `budget_report` | Deterministic char-based estimate for selected/considered/dropped docs. |
| `governance_report` | Optional policy-as-code evaluation over selected context. |
| `source_hashes` | Source provenance for selected and static inputs. |

Markdown files such as `.contextd/context/current-task.md` are render targets. The JSON artifact is the source of truth.

## Lifecycle

The useful lifecycle is:

1. **Author** source knowledge: write contracts, requirements, design docs, runbooks, policies, and pack retrieval maps.
2. **Resolve** the active workspace and packs from `.contextd/config.json`.
3. **Build** a task context artifact with `contextd context`.
4. **Explain** selection with `contextd explain` when the output is surprising.
5. **Consume** through CLI, Claude/Codex/Cursor exports, or MCP tools.
6. **Evaluate** with golden tasks when pack or workspace knowledge changes.
7. **Retire** stale docs, old contracts, or broken retrieval-map entries when eval or doctor reports drift.

The loop is intentionally local-first and file-backed so it fits normal code review and git workflows.

## Determinism Boundaries

Deterministic:

- Config resolution order.
- Workspace isolation.
- Pack component detection from declared keywords.
- Retrieval-map expansion and path safety checks.
- Section slicing from selected markdown files.
- Source hashes and pack keys.
- Policy and golden-task evaluation.

Advisory:

- `contextd find` fuzzy discovery.
- Any future RAG/search surface.
- Human interpretation of whether selected context made the final agent output better.

Advisory signals may help discovery, but they must not override deterministic contracts, policies, or workspace isolation.

## What contextd Is Not

contextd is not:

- A vector database.
- A long-term personal memory system.
- An agent orchestrator or queue worker.
- A replacement for Claude, Codex, Cursor, or MCP.
- A hosted control plane.

It is the local governed build layer that prepares reliable inputs for those runtimes.

## Adoption Shape

The smallest useful rollout is one repo and one workspace:

```bash
contextd resolve --format json
contextd doctor --format text
contextd context "debug checkout timeout" --format json --no-materialize
contextd explain "debug checkout timeout" --format text
```

The team rollout adds:

- shared `knowledge_root` in a git repo,
- pack validation in CI,
- policy checks for mandatory docs or forbidden paths,
- golden tasks for known task classes,
- adapter exports for the clients developers actually use.

## Common Failure Modes

| Failure | What It Means | First Command |
|---|---|---|
| Wrong workspace | The codebase resolves to a different workspace than expected. | `contextd resolve --format json` |
| Missing required doc | A contract, requirement, runbook, or pack doc is absent. | `contextd explain "task" --format json` |
| Pack drift | `pack.yaml` and retrieval-map rows no longer agree. | `contextd pack-validate --all --format text` |
| Unsafe path | A retrieval map tried absolute, parent traversal, cross-workspace, or blocked secret paths. | `contextd doctor --format json` |
| Over-broad context | Too many docs are considered or dropped by budget. | `contextd explain "task" --format text` |
| Adapter mismatch | Claude/Codex/Cursor/MCP surfaces no longer describe the canonical artifact. | `contextd doctor --format text` |

## Related

- [Context quality](context-quality.md)
- [Governance](governance.md)
- [Pack validation](pack-validation.md)
- [Evaluation](evaluation.md)
- [MCP adapter](mcp.md)
