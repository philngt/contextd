# Patterns Index — wiki

Quick lookup table for AI agents. Find the pattern name, follow the link, read before generating code.

> Paths are relative to this file (workspace root).

## Platform Patterns

| Pattern | When to Use | Path |
|---------|-------------|------|
| `askuser-confirm-preview` | Command có side effects filesystem (tạo evidence, edit wiki, scaffold workspace) — preview block + 3-option AskUserQuestion (continue/edit/cancel) | [platform/patterns/askuser-confirm-preview.md](platform/patterns/askuser-confirm-preview.md) |
| `citation-rule` | Sinh analysis output / snapshot / report — mọi claim PHẢI có citation `({path}:L<start>-L<end>)` relative tới repo root. PAIR with `citation-format` contract. | [platform/patterns/citation-rule.md](platform/patterns/citation-rule.md) |
| `evidence-state-machine` | Track evidence lifecycle (ingest → analyze → qa → apply) qua 7-state DAG. Storage: `{ws}/evidence/_index.md`. PAIR with `evidence-state-machine-transitions` contract. | [platform/patterns/evidence-state-machine.md](platform/patterns/evidence-state-machine.md) |
| `multi-stage-subagent-pipeline` | Task wiki-aware code generation — 5-stage flow (planner → context-selector → plan-reviewer GATE → Builder → reviewer). Used by `/contextd-use`. | [platform/patterns/multi-stage-subagent-pipeline.md](platform/patterns/multi-stage-subagent-pipeline.md) |
| `redaction-post-pass` | Sau build output — scan secrets (password/token/api-key/email/URL-with-creds) → STOP-on-secret. Companion với `secrets-blocklist-gate`. | [platform/patterns/redaction-post-pass.md](platform/patterns/redaction-post-pass.md) |
| `secrets-blocklist-gate` | Pre-read config files — 5-tier defense (hard blocklist + AskUser gate + redaction + log + workspace override). Default block-all. | [platform/patterns/secrets-blocklist-gate.md](platform/patterns/secrets-blocklist-gate.md) |
| `variant-discriminated-dispatcher` | (v1, single-instance) Command/pipeline phục vụ nhiều variants — discriminate qua field `variant`, dispatch internally. Hiện áp dụng cho `/code-analyze` `code_variant ∈ {code, agentic-engine}`. | [platform/patterns/variant-discriminated-dispatcher.md](platform/patterns/variant-discriminated-dispatcher.md) |
| `workspace-resolve-step0` | Bước 0 universal cho mọi slash command — resolve `.claude/wiki.json` → set `{ws}` → validate workspace.md. Engine-level invariant. | [platform/patterns/workspace-resolve-step0.md](platform/patterns/workspace-resolve-step0.md) |

## Contracts

| Contract | What It Governs | Path |
|----------|----------------|------|
| `citation-format` | Format invariant cho citations + validator behavior (reject absolute / cwd-relative / cross-workspace paths). PAIR with `citation-rule` pattern. | [platform/contracts/citation-format.md](platform/contracts/citation-format.md) |
| `evid-id-format` | Evidence ID format `{date}-{src}-{slug}[-{n}]` với `src ∈ {paste, api, mcp, code, engine, platform}`. | [platform/contracts/evid-id-format.md](platform/contracts/evid-id-format.md) |
| `evidence-file-layout` | Layout invariant cho `{ws}/evidence/{sources,analysis,qa,applied}/{evid-id}/...` + `_index.md`. | [platform/contracts/evidence-file-layout.md](platform/contracts/evidence-file-layout.md) |
| `evidence-state-machine-transitions` | Invariant rules + ownership table cho state transitions. PAIR with `evidence-state-machine` pattern. | [platform/contracts/evidence-state-machine-transitions.md](platform/contracts/evidence-state-machine-transitions.md) |
| `raw-md-section-structure` | 10-section structure invariant cho raw.md với 3 variants: code / agentic-engine / bundle. | [platform/contracts/raw-md-section-structure.md](platform/contracts/raw-md-section-structure.md) |
| `slash-command-naming` | Naming invariant cho slash commands: kebab-case + lowercase + hyphens. Recommendation (non-binding): subject-verb cho commands mới. | [platform/contracts/slash-command-naming.md](platform/contracts/slash-command-naming.md) |
| `source-yaml-schema` | Required + conditional fields cho `source.yaml`. Workspace lock invariant via `workspace_at_ingest`. | [platform/contracts/source-yaml-schema.md](platform/contracts/source-yaml-schema.md) |
| `sub-agent-frontmatter-schema` | Required frontmatter (name, description, tools, model) cho `.claude/agents/*.md`. Convention (non-binding): description chứa `DÙNG KHI` + `KHÔNG DÙNG`. | [platform/contracts/sub-agent-frontmatter-schema.md](platform/contracts/sub-agent-frontmatter-schema.md) |

## Domain Workflows

| Domain | Path |
|--------|------|
| _(none — workspace `wiki` is engine-level, no business domain workflows)_ | |
