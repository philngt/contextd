## Apply Report — workspace `wiki` — evidence `2026-05-08-engine-bootstrap-wiki-template` — 2026-05-08

### Mode

`update` (inline mode — main agent direct edit, curator delegation skipped because workspace `wiki` is engine bootstrap and wiki-curator subagent itself being documented).

### Summary

- **28 files created** + **1 file edited** in workspace `wiki`.
- All target paths inside `{ws}/`. F-023 (engine-level path `.claude/commands/README.md`) excluded by design — separate session.
- All P0/P1 facts applied. 5 deferred questions (3 P2 + 2 P3) — informational, not blocking.

### Created

#### Platform Patterns (8)

- [platform/patterns/askuser-confirm-preview.md](../../platform/patterns/askuser-confirm-preview.md) — UX preview/confirm pattern (citation: q-002)
- [platform/patterns/citation-rule.md](../../platform/patterns/citation-rule.md) — citation format implementation skeleton; PAIR with `citation-format` contract (citation: q-006)
- [platform/patterns/evidence-state-machine.md](../../platform/patterns/evidence-state-machine.md) — 7-state DAG implementation; PAIR with `evidence-state-machine-transitions` contract (citation: q-005)
- [platform/patterns/multi-stage-subagent-pipeline.md](../../platform/patterns/multi-stage-subagent-pipeline.md) — 5-stage `/use-wiki` flow; **NOT marked flagship** per user override q-007 (citation: q-007 user override)
- [platform/patterns/redaction-post-pass.md](../../platform/patterns/redaction-post-pass.md) — secret scan post-build (citation: q-004)
- [platform/patterns/secrets-blocklist-gate.md](../../platform/patterns/secrets-blocklist-gate.md) — 5-tier config guard pre-read (citation: q-003)
- [platform/patterns/variant-discriminated-dispatcher.md](../../platform/patterns/variant-discriminated-dispatcher.md) — v1 single-instance pattern (citation: q-008)
- [platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md) — engine-level Bước 0 invariant (citation: q-001)

#### Platform Contracts (8)

- [platform/contracts/citation-format.md](../../platform/contracts/citation-format.md) — citation invariants + validator behavior; PAIR with `citation-rule` pattern (citation: q-006)
- [platform/contracts/evid-id-format.md](../../platform/contracts/evid-id-format.md) — evid-id format `{date}-{src}-{slug}` (citation: q-009)
- [platform/contracts/evidence-file-layout.md](../../platform/contracts/evidence-file-layout.md) — file layout invariant + `_index.md` as SoT (citation: q-010)
- [platform/contracts/evidence-state-machine-transitions.md](../../platform/contracts/evidence-state-machine-transitions.md) — transition ownership + invariants; PAIR (citation: q-005)
- [platform/contracts/raw-md-section-structure.md](../../platform/contracts/raw-md-section-structure.md) — 1 contract đa-variant (code | agentic-engine | bundle) (citation: q-011)
- [platform/contracts/slash-command-naming.md](../../platform/contracts/slash-command-naming.md) — kebab-case + lowercase + hyphens; BOTH conventions documented (citation: q-013)
- [platform/contracts/source-yaml-schema.md](../../platform/contracts/source-yaml-schema.md) — required + conditional fields; KEEP unified (citation: q-012)
- [platform/contracts/sub-agent-frontmatter-schema.md](../../platform/contracts/sub-agent-frontmatter-schema.md) — 4 required fields + non-binding `DÙNG KHI/KHÔNG DÙNG` convention (citation: q-014)

#### Engine project (8 — knowledge map + 7 service docs)

- [projects/engine/knowledge-map.md](../../projects/engine/knowledge-map.md) — project map with 7 service docs + 8 patterns + 8 contracts cross-references (citations: q-015, q-016)
- [projects/engine/services/workspace-ops.md](../../projects/engine/services/workspace-ops.md) — 5 commands (`/wiki-setup`, `/wiki-detect`, `/switch-workspace`, `/new-workspace`, `/list-workspaces`) (citation: F-017a)
- [projects/engine/services/wiki-usage.md](../../projects/engine/services/wiki-usage.md) — 3 commands (`/use-wiki`, `/update-wiki`, `/rebase-wiki`) (citation: F-017b)
- [projects/engine/services/codebase-analysis.md](../../projects/engine/services/codebase-analysis.md) — `/code-analyze` with 5 patterns applied (citation: F-017c)
- [projects/engine/services/reporting.md](../../projects/engine/services/reporting.md) — `/wiki-report` (citation: F-017d)
- [projects/engine/services/observability.md](../../projects/engine/services/observability.md) — 3 commands (`/wiki-trace`, `/wiki-eval`, `/wiki-viz`) (citation: F-017e)
- [projects/engine/services/evidence-pipeline.md](../../projects/engine/services/evidence-pipeline.md) — 5 commands (`/evidence-{ingest,analyze,qa,apply}`, `/obsidian-ingest`) (citation: F-017f)
- [projects/engine/services/agents.md](../../projects/engine/services/agents.md) — 5 sub-agents catalog (citation: F-017g)

#### Decisions (4 ADRs)

- [decisions/001-introduce-agentic-engine-variant.md](../../decisions/001-introduce-agentic-engine-variant.md) — status=ACCEPTED (citation: q-017)
- [decisions/002-keep-code-analysis-prompts-monolithic.md](../../decisions/002-keep-code-analysis-prompts-monolithic.md) — status=ACCEPTED with revisit triggers (citation: q-018)
- [decisions/003-self-referential-engine-workspace.md](../../decisions/003-self-referential-engine-workspace.md) — workspace `wiki` boundary rule (citations: q-016, raw.md note 5)
- [decisions/004-pattern-contract-pairing-convention.md](../../decisions/004-pattern-contract-pairing-convention.md) — PAIR convention rationale (citations: q-005, q-006)

### Updated

- [patterns-index.md](../../patterns-index.md): Populated 8 pattern rows + 8 contract rows replacing empty placeholders. Order: alphabetical. F-007 `multi-stage-subagent-pipeline` NOT marked flagship (per user override q-007). Domain Workflows section: `(none — workspace wiki is engine-level)` (citations: F-022, q-007 user override).

### Skipped (no actionable fact)

_(none — all 22 in-scope facts applied)_

### Excluded (out of apply scope)

- F-023 — `.claude/commands/README.md` (`/wiki-viz` orphan README index fix). Engine-level path, NOT in `{ws}/`. Marked in verified-facts.md "NOT in this apply manifest". Run separately:
  ```
  /update-wiki --scope .claude/commands/README.md
  ```

### Warnings

- ⚠ **No `templates/contract.md` exists** — 8 contracts created with inline construction (adapted from `templates/pattern.md` semantics). **Action item**: consider adding `templates/contract.md` template for future contract creates.
- ⚠ **No `templates/knowledge-map.md` exists** — `projects/engine/knowledge-map.md` constructed inline. **Action item**: consider adding template.
- ⚠ **F-007 user override** — verified `multi-stage-subagent-pipeline` row trong `patterns-index.md` ở alphabetical position (NOT top), `workspace.md` NOT edited.
- ⚠ **F-008 v1 confidence note** — pattern doc includes inline note "single instance — pattern shape may evolve khi variant thứ 3 được introduce".
- ⚠ **Inline apply mode** — wiki-curator delegation skipped (engine workspace bootstrap; curator subagent itself being documented). Main agent verified each path inside `{ws}/` before write. Documented in `manifest.yaml#inline_apply: true`.

### Deferred (P2/P3 — informational)

- q-020 (P2): Pipeline support docs README table extend (`agents/pipeline/README.md` — engine-level, separate `/update-wiki` session)
- q-021 (P2): Tools allowlist principle C-008a — defer until sample ≥ 8 sub-agents
- q-022 (P2): Rerun `/code-analyze --allow-configs` for Section 3/8 — separate session, will create new evid-id `refresh-wiki-template-{date}`
- q-023 (P3): Counter-arg overlap với engine spec docs — boundary rule documented in ADR-003
- q-024 (P3): Counter-arg source_type=engine alternative — addressed in ADR-001 alternatives table

### State transition

`qa_done → applied` confirmed in `_index.md`.

### Next

```
# Action item F-023 (separate session):
/update-wiki --scope .claude/commands/README.md

# Future improvements:
/code-analyze --ref . --variant agentic-engine --allow-configs    # populate Section 3/8 (q-022)

# Optional retention cleanup later:
# Mark row (manual) in _index.md when ready to archive evidence
```
