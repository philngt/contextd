# Service: evidence-pipeline

## Purpose

4-stage state machine pipeline (ingest → analyze → qa → apply) đưa raw data từ MCP/API/paste/code vào wiki structured docs. Universal pipeline áp dụng mọi `source_type` ∈ {paste, api, mcp, code}.

## Input

5 commands:
- `/evidence-ingest --source {type} ...` — pull raw data
- `/obsidian-ingest --vault ...` — batch wrapper for Obsidian vault
- `/evidence-analyze --id {evid-id}` — sinh CORE analysis prompts
- `/evidence-qa --id {evid-id}` — Q&A loop user verification
- `/evidence-apply --id {evid-id} --mode {update|rebase}` — push verified facts vào wiki

## Output

Per evid-id:
```
{ws}/evidence/sources/{evid-id}/{source.yaml, raw.{ext}, raw.normalized.md?}
{ws}/evidence/analysis/{evid-id}/{NN|cNN|aNN}-*.md
{ws}/evidence/qa/{evid-id}/{recommendations.md, todo.json, batches/, verified-facts.md, pending-external.md?}
{ws}/evidence/applied/{evid-id}/{checkpoint.json, manifest.yaml, diff-summary.md}
{ws}/evidence/_index.md     # state row
```

Plus: `/evidence-apply` edits files trong `{ws}/{platform, projects, domains, decisions, runbooks}/` per verified-facts.

## Flow

Applies platform patterns (4):
- → [../../platform/patterns/evidence-state-machine.md](../../platform/patterns/evidence-state-machine.md) (DAG transitions across 5 commands)
- → [../../platform/patterns/citation-rule.md](../../platform/patterns/citation-rule.md) (cite format trong analysis output)
- → [../../platform/patterns/variant-discriminated-dispatcher.md](../../platform/patterns/variant-discriminated-dispatcher.md) (`/evidence-analyze` dispatch)
- → [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md) (Bước 0 in all 5)

State transitions per command:
```
(none) → /evidence-ingest, /code-analyze, /obsidian-ingest → ingested
ingested → /evidence-analyze (CORE complete) → analyzed
analyzed → /evidence-qa → qa_in_progress ⇄ qa_awaiting_external → qa_done
qa_done → /evidence-apply → applied
applied → manual → archived
```

## Config

```yaml
state_storage: "{ws}/evidence/_index.md"     # SoT per contract C-005
file_layout: per_contract_evidence_file_layout

dispatch_table:
  paste/api/mcp:
    core_set: ["01", "02", "04", "08"]
    on_demand: ["03", "05", "06", "07", "09", "10"]
  code (variant=code):
    core_set: ["c01", "c02", "c03", "c04", "04", "08"]
    on_demand: ["c05", "c06", "c07"]
  code (variant=agentic-engine):
    core_set: ["a01", "a02", "a03", "a04", "04", "08"]
    on_demand: ["a05", "a06", "a07"]

qa_batch_size: 4                             # AskUserQuestion max 4 questions/call
qa_recommender_blocking: true                # C8/A8 pre-batch-1 cho source_type=code

apply_curator_delegation: required           # default; --inline only when curator unavailable
apply_checkpoint_enabled: true               # resume support
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| `/evidence-ingest` duplicate sha256 | STOP, reuse existing evid-id |
| `/evidence-analyze` CORE set incomplete | STOP, NOT transition to analyzed |
| `/evidence-qa` P0 awaiting_external | State transitions tới `qa_awaiting_external`, paused — `/evidence-qa --resume` after expert reply |
| `/evidence-apply` validator gate fail (P0/P1 deferred without `--ignore-deferred`) | STOP với hint resume Q&A |
| `/evidence-apply` cross-workspace violation (I-2) | STOP với explicit error (workspace_at_ingest mismatch) |
| `/evidence-apply` curator unavailable | STOP với `CURATOR UNAVAILABLE`; rerun `--inline` if test/CI |
| `/evidence-apply` interrupt mid-run | Checkpoint preserved; `--resume` picks up từ current_file |

## Notes

- 4-stage pipeline = state machine (per ADR/contract). KHÔNG được skip stage.
- Workspace lock (I-2): mọi command CHỈ thao tác evidence khi active workspace = `source.yaml#workspace_at_ingest`. Cross-workspace = STOP.
- Variant dispatch (I-2 companion): `/evidence-analyze` reads `source.yaml#code_variant` → CORE-CODE vs CORE-AGENTIC. Cross-variant prompts rejected.
- QA Recommender (C8/A8) blocking pre-batch-1 cho source_type=code — gives user pre-suggested answers cho P0/P1 questions.
- `/evidence-apply` checkpoint persist across crash/Ctrl+C; `--resume` continues from `current_file` per `checkpoint.json`.

## Related

- Pattern: [../../platform/patterns/evidence-state-machine.md](../../platform/patterns/evidence-state-machine.md)
- Pattern: [../../platform/patterns/citation-rule.md](../../platform/patterns/citation-rule.md)
- Pattern: [../../platform/patterns/variant-discriminated-dispatcher.md](../../platform/patterns/variant-discriminated-dispatcher.md)
- Pattern: [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)
- Contract: [../../platform/contracts/evidence-state-machine-transitions.md](../../platform/contracts/evidence-state-machine-transitions.md)
- Contract: [../../platform/contracts/evidence-file-layout.md](../../platform/contracts/evidence-file-layout.md)
- Contract: [../../platform/contracts/evid-id-format.md](../../platform/contracts/evid-id-format.md)
- Contract: [../../platform/contracts/source-yaml-schema.md](../../platform/contracts/source-yaml-schema.md)
- Contract: [../../platform/contracts/raw-md-section-structure.md](../../platform/contracts/raw-md-section-structure.md)
- Contract: [../../platform/contracts/citation-format.md](../../platform/contracts/citation-format.md)
- Service: [codebase-analysis.md](codebase-analysis.md) (`/code-analyze` dưới capô gọi `/evidence-ingest`)
- Service: [agents.md](agents.md) (`wiki-curator` invoked by `/evidence-apply`)
- Engine source: `.claude/commands/evidence-{ingest,analyze,qa,apply}.md`, `obsidian-ingest.md`
- Engine spec: `agents/pipeline/{evidence-lifecycle,raw-storage-conventions,critical-analysis-prompts,code-analysis-prompts,qa-batching}.md`
- Templates: `evidence-source.yaml`, `evidence-index.md`, `evidence-qa-{recommendations,answers,todo}.{md,json}`, `evidence-pending-external.md`, `evidence-apply-checkpoint.json`, `evidence-manifest.yaml`
- Source: F-017f, evidence `2026-05-08-engine-bootstrap-wiki-template`
