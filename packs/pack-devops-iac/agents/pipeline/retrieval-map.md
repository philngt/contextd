# pack-devops-iac — Retrieval Map

Component → workspace knowledge mapping for this pack. Merged into the engine retrieval map.

| Component | Docs to retrieve |
|-----------|------------------|
| `terraform-safety` | `platform/patterns/terraform-change-management.md`, `platform/contracts/infrastructure-state-contract.md`, `decisions/`, `runbooks/` |
| `kubernetes-workload` | `platform/patterns/kubernetes-workload.md`, `platform/contracts/deployment-contract.md`, `projects/{project}/knowledge-map.md`, `runbooks/` |
| `ci-cd-release` | `platform/patterns/ci-cd-release.md`, `platform/contracts/deployment-contract.md`, `projects/{project}/knowledge-map.md`, `runbooks/` |
| `environment-promotion` | `platform/patterns/environment-promotion.md`, `platform/contracts/deployment-contract.md`, `decisions/`, `runbooks/` |
| `infrastructure-drift` | `platform/patterns/infrastructure-drift.md`, `projects/{project}/knowledge-map.md`, `runbooks/`, `evidence/` |
| `rollback-readiness` | `platform/contracts/deployment-contract.md`, `runbooks/`, `projects/{project}/knowledge-map.md`, `evidence/` |

Components must match `pack.yaml#components`. Missing workspace documents are explicit knowledge gaps; the pack does not borrow another workspace's infrastructure decisions.
