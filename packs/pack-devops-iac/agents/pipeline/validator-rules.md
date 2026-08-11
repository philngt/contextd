# pack-devops-iac — Validator Rules

Layer-1 static checks implemented in [`scripts/rules.py`](../../scripts/rules.py). Rule IDs use the `pack-devops-iac-` prefix.

## Catalog

| Rule ID | Severity | Triggers on | Detects |
|---------|----------|-------------|---------|
| `pack-devops-iac-terraform-unpinned-provider` | error | `*.tf` | A `required_providers` entry with `source` but no version constraint in the same provider block. |
| `pack-devops-iac-terraform-unpinned-module` | error | `*.tf` | A remote module block without a registry version or full 40-hex Git commit `ref`. |
| `pack-devops-iac-k8s-image-not-digest-pinned` | error | `*.yaml`, `*.yml` | A workload container image that is not pinned by a 64-hex `sha256` digest. |
| `pack-devops-iac-k8s-missing-readiness-probe` | warn | `*.yaml`, `*.yml` | An individual container in a Deployment, StatefulSet, or DaemonSet document without a readiness probe. |
| `pack-devops-iac-k8s-missing-resource-requests` | warn | `*.yaml`, `*.yml` | An individual container in a Deployment, StatefulSet, or DaemonSet document without resource requests. |
| `pack-devops-iac-terraform-apply-without-saved-plan` | error | CI workflow YAML | An individual `terraform`/`tofu apply` command without an explicit positional saved-plan argument. |
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
- Kubernetes checks split standard `---` documents and use indentation to scope `containers`; generated templates still require rendered-manifest validation.
- CI checks inspect each apply independently. They verify an explicit positional plan argument, but cannot prove that an external artifact was reviewed.
- Markdown rollback checks only target filenames or directories associated with deployments, releases, or runbooks.
