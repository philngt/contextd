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
  -> build workspace synapse nodes, edges, lifecycle, and freshness
  -> retain that immutable build snapshot for projection/materialization
  -> collect deterministic candidates
  -> reject unsafe paths and redact sensitive content
  -> rank and slice relevant sections
  -> validate contract paths and gaps
  -> apply policy checks
  -> emit contextd_task_context.v1
  -> optionally render markdown/materialized pack and the same synapse snapshot
```

The output is not a memory record and not a search result. It is a context projection compiled from governed source knowledge and its rebuildable synapse index, with source hashes, selected docs, warnings, gaps, budget information, and governance results.

A context build performs one full synapse scan over the active workspace. Each
governed source is read as raw bytes once; its byte hash, decoded text, and
precomputed graph lookups are reused by projection. Materialization consumes
the matching in-memory graph and is write-only, so it never rescans canonical
sources. Before writing `synapse.json`, it checks the resolved knowledge root,
graph identity, and selected/static workspace source hashes. A later command
rebuild detects source changes through the resulting hashes.

## Synapse And Memory Boundaries

The source files, graph index, context artifact, and agent runtime have distinct
roles:

| Layer | Meaning |
|---|---|
| Long-term governed knowledge | Canonical workspace files reviewed and versioned by their owners. |
| Synapse | Rebuildable node/edge index with lifecycle and freshness; never a second source of truth. |
| Context | Task-specific projection selected from the synapse and static engine/pack inputs. |
| Runtime memory | Host conversation state, observations, and workflow checkpoints; not automatically promoted. |

Stale, deprecated, and superseded knowledge remains in the synapse for history.
The context compiler lowers its default priority and emits a warning when such a
node is selected.

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
| `synapse` | Reference, hash, evaluation date, and summary for the workspace lifecycle graph. |
| `context_projection` | Selected long-term node IDs, lifecycle/freshness states, and relevant typed edges. |
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
7. **Classify** old knowledge as stale, deprecated, or superseded; retain it for audit and connect replacements with typed edges.

The loop is intentionally local-first and file-backed so it fits normal code review and git workflows.

## Determinism Boundaries

Deterministic:

- Config resolution order.
- Workspace isolation.
- Pack component detection from declared keywords.
- Retrieval-map expansion and path safety checks.
- Section slicing from selected markdown files.
- Source hashes and pack keys.
- Synapse nodes, validated edges, lifecycle scoring, and graph hashes for a fixed evaluation date.
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
| Pack drift | Manifest routing, canonical knowledge, legacy adapters, or validator IDs no longer agree. | `contextd pack-validate --all --format text` |
| Unsafe path | A retrieval map tried absolute, parent traversal, cross-workspace, or blocked secret paths. | `contextd doctor --format json` |
| Over-broad context | Too many docs are considered or dropped by budget. | `contextd explain "task" --format text` |
| Adapter mismatch | Claude/Codex/Cursor/MCP surfaces no longer describe the canonical artifact. | `contextd doctor --format text` |

## Related

- [Context quality](context-quality.md)
- [Governance](governance.md)
- [Pack validation](pack-validation.md)
- [Evaluation](evaluation.md)
- [MCP adapter](mcp.md)
