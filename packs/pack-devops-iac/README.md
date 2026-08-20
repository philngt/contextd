# pack-devops-iac

DevOps and infrastructure-as-code guardrails for Terraform/OpenTofu, Kubernetes workloads, CI/CD releases, environment promotion, drift control, and rollback readiness.

## When to enable

Add `- pack-devops-iac` under `## Packs` in `workspaces/{ws}/workspace.md` when a workspace:

- Manages infrastructure with Terraform or OpenTofu.
- Deploys Kubernetes workloads or Helm-rendered manifests.
- Owns CI/CD workflows that change shared or production environments.
- Needs explicit promotion, drift, blast-radius, or rollback controls.

## What it adds

- **Constraints** (`agents/constraints.md`) — hard infrastructure and deployment safety rules.
- **Working rules** (`agents/coding-rules.md`) — reviewable IaC and release conventions.
- **Common pitfalls** (`agents/common-pitfalls.md`) — ten recurring operational failure modes.
- **Validator rules** (`agents/pipeline/validator-rules.md`, `scripts/rules.py`) — narrow static checks for common unsafe changes.
- **Retrieval map** (`agents/pipeline/retrieval-map.md`) — component-to-workspace knowledge mapping.
- **Prompt overrides** (`agents/pipeline/prompt-overrides.md`) — DevOps/IaC self-checks.

## Components declared

- `terraform-safety`
- `kubernetes-workload`
- `ci-cd-release`
- `environment-promotion`
- `infrastructure-drift`
- `rollback-readiness`

## Composition

- Pair with `pack-security` for IAM, secret handling, image vulnerability, and supply-chain controls.
- Pair with `pack-qc` for performance baselines and release-quality evidence.
- Pair with `pack-dba` when a deployment includes schema changes, backup, or restore obligations.

This pack does not duplicate those concerns. It owns infrastructure change mechanics and operational deployment safety.

## Heuristic scope

Layer-1 validators intentionally cover only reliable textual signals. They do not attempt to fully parse HCL, YAML templating, reusable workflows, or rendered Helm output. Complex changes require the Layer-2 self-checks.

## Conflicts with

(none)

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)

## When not to enable

- Task chỉ sửa application behavior và không thay đổi infrastructure, deployment hoặc promotion.
- Schema migration/restore internals hoặc security assessment; dùng pack sở hữu domain đó.

## Retrieval behavior

Keyword route riêng Terraform/OpenTofu, Kubernetes, CI/CD, promotion, drift, và rollback. Retrieval map chỉ nạp tài liệu workspace liên quan component được phát hiện; Helm/template phức tạp vẫn cần Layer-2 review sau khi render.

## Verification

```bash
contextd pack-validate --pack pack-devops-iac --format text
contextd context "Review Terraform production rollout and rollback" --preview --format json
python scripts/validate.py --file <iac-fixture> --workspace <workspace-with-pack>
```
