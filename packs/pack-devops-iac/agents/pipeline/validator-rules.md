# pack-devops-iac — Validator Rules

Layer-1 static checks implemented in [`scripts/rules.py`](../../scripts/rules.py). Rule IDs use the `pack-devops-iac-` prefix.

## Catalog

| Rule ID | Severity | Triggers on | Detects |
|---------|----------|-------------|---------|
| `pack-devops-iac-terraform-unpinned-provider` | error | `*.tf` | A `required_providers` entry with `source` but no version constraint in the same provider block. |
| `pack-devops-iac-terraform-unpinned-module` | error | `*.tf` | A remote module block without a registry version or immutable Git `ref`. |
| `pack-devops-iac-k8s-mutable-image-tag` | error | `*.yaml`, `*.yml` | A Kubernetes workload image using the `latest` tag. |
| `pack-devops-iac-k8s-missing-readiness-probe` | warn | `*.yaml`, `*.yml` | A Deployment, StatefulSet, or DaemonSet with containers but no readiness probe. |
| `pack-devops-iac-k8s-missing-resource-requests` | warn | `*.yaml`, `*.yml` | A Deployment, StatefulSet, or DaemonSet with containers but no resource requests. |
| `pack-devops-iac-terraform-apply-without-plan` | error | CI workflow YAML | A workflow invokes `terraform`/`tofu apply` without a plan command or saved-plan input. |
| `pack-devops-iac-deployment-no-rollback` | warn | deployment/release/runbook Markdown | Deployment instructions with no rollback, roll-back, roll-forward, or rollout-undo path. |

## Layer-2 checks

- Provider/module constraints are compatible with the committed lockfile policy.
- Plan review names replacements, destroys, environment reach, and irreversible effects.
- Production promotes the exact artifact tested earlier.
- Drift detection has an owner and reconciliation path.
- Rollback accounts for stateful resources, schema compatibility, and verification signals.
- Rendered manifests are validated when templates or reusable workflows hide final output.

## Heuristic limitations

- HCL checks use brace-local text inspection and do not evaluate expressions.
- Kubernetes checks inspect complete YAML files, not individual multi-document workload boundaries.
- CI checks recognize common workflow paths and explicit `plan` commands or plan-file inputs.
- Markdown rollback checks only target filenames or directories associated with deployments, releases, or runbooks.
