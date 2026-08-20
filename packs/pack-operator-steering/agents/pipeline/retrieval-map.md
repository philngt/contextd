# pack-operator-steering — Retrieval Map

> Manifest-v2 compatibility adapter. `pack.yaml#retrieval` is canonical in v3;
> pack validation fails if this table drifts from it.

| Component | Docs to retrieve |
|-----------|------------------|
| `context-audit` | `packs/pack-operator-steering/templates/context-audit-report.md`, `runbooks/context-quality-degradation.md`, `projects/{project}/knowledge-map.md`, `decisions/`, `evidence/` |
| `drift-check` | `packs/pack-operator-steering/templates/drift-report.md`, `decisions/`, `projects/{project}/knowledge-map.md`, `runbooks/`, `evidence/` |
| `remediation-planning` | `packs/pack-operator-steering/templates/remediation-plan.md`, `runbooks/`, `projects/{project}/knowledge-map.md`, `evidence/` |
| `decision-ledger` | `packs/pack-operator-steering/templates/decision-note.md`, `decisions/`, `projects/{project}/knowledge-map.md` |
| `handoff-quality` | `packs/pack-operator-steering/templates/handoff-brief.md`, `decisions/`, `projects/{project}/knowledge-map.md`, `evidence/` |
| `workflow-mental-model` | `packs/pack-operator-steering/templates/workflow-mental-model.md`, `projects/{project}/knowledge-map.md`, `domains/{domain}/`, `decisions/` |
| `operator-wayfinding` | `packs/pack-operator-steering/templates/wayfinding-checkpoint.md`, `projects/{project}/knowledge-map.md`, `decisions/`, `evidence/`, `runbooks/` |

Components must match `pack.yaml#components`. Pipeline fail-fast nếu mismatch.
