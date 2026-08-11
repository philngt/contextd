# pack-devops-iac — Constraints

Hard DevOps and infrastructure-as-code rules. Additive on the engine constraints; strict-only.

## Terraform and OpenTofu

- `pack-devops-iac-terraform-provider-pinned` — Every non-local provider dependency MUST declare a version constraint. Provider upgrades are reviewed changes, not ambient resolver behavior.
- `pack-devops-iac-terraform-module-pinned` — Every remote module MUST use an immutable version or Git ref. Floating branches and unversioned registry modules are forbidden.
- `pack-devops-iac-plan-before-apply` — Automated apply workflows MUST produce or consume a reviewed plan before changing infrastructure.

## Kubernetes workloads

- `pack-devops-iac-k8s-immutable-image` — Workload images MUST use an immutable tag or digest. `latest` is forbidden.
- `pack-devops-iac-k8s-readiness-probe` — Long-running workload containers MUST define a readiness probe or document why an external readiness mechanism applies.
- `pack-devops-iac-k8s-resource-requests` — Long-running workload containers MUST declare resource requests based on measured or explicitly provisional values.

## Releases and operations

- `pack-devops-iac-production-promotion` — Production changes MUST be promoted from a previously verified artifact; production MUST NOT rebuild a different artifact from the same source.
- `pack-devops-iac-rollback-required` — Deployment design and runbooks MUST define rollback or roll-forward criteria, commands, ownership, and verification.
- `pack-devops-iac-drift-owned` — Managed infrastructure MUST have a documented drift detection cadence, owner, and reconciliation path.
- `pack-devops-iac-blast-radius-reviewed` — Infrastructure changes MUST identify affected environments/resources and destructive or replacement operations before approval.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Validator catalog: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Working rules: [coding-rules.md](coding-rules.md)
