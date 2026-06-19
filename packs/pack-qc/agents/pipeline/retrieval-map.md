# pack-qc — Retrieval Map

Component → wiki doc mapping for this pack.

| Component | Docs to retrieve (relative `{ws}/`) |
|-----------|-------------------------------------|
| `test-case-design` | `quality/`, `projects/{project}/services/`, `platform/contracts/`, `domains/{domain}/` |
| `test-execution` | `quality/`, `runbooks/`, `projects/{project}/services/`, `evidence/` |
| `defect-triage` | `quality/`, `runbooks/`, `projects/{project}/services/`, `domains/{domain}/` |
| `regression-plan` | `quality/`, `projects/{project}/knowledge-map.md`, `platform/contracts/`, `runbooks/` |
| `performance-profiling` (perf) | `quality/`, `projects/{project}/services/`, `runbooks/`, `decisions/` |
| `bottleneck-analysis` (perf) | `platform/architecture/`, `projects/{project}/services/` |
| `optimization-safety` (perf) | `platform/contracts/`, `domains/{domain}/workflow.md` |
| `regression-guard` (perf) | `quality/`, `runbooks/`, `projects/{project}/knowledge-map.md` |

Components must match `pack.yaml#components`.
