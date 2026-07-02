# pack-operator-steering — Retrieval Map

Component → wiki doc mapping for this pack. Merged into engine retrieval map by pipeline.

| Component | Docs to retrieve |
|-----------|------------------|
| `context-audit` | `packs/pack-operator-steering/templates/context-audit-report.md`, `runbooks/context-quality-degradation.md`, `projects/{project}/knowledge-map.md`, `decisions/`, `evidence/` |
| `drift-check` | `packs/pack-operator-steering/templates/drift-report.md`, `decisions/`, `projects/{project}/knowledge-map.md`, `runbooks/`, `evidence/` |
| `remediation-planning` | `packs/pack-operator-steering/templates/remediation-plan.md`, `runbooks/`, `projects/{project}/knowledge-map.md`, `evidence/` |
| `decision-ledger` | `packs/pack-operator-steering/templates/decision-note.md`, `decisions/`, `projects/{project}/knowledge-map.md` |
| `handoff-quality` | `packs/pack-operator-steering/templates/handoff-brief.md`, `decisions/`, `projects/{project}/knowledge-map.md`, `evidence/` |
| `workflow-mental-model` | `packs/pack-operator-steering/templates/workflow-mental-model.md`, `projects/{project}/knowledge-map.md`, `domains/{domain}/`, `decisions/` |

Components must match `pack.yaml#components`. Pipeline fail-fast nếu mismatch.
