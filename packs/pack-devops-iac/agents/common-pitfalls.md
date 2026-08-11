# pack-devops-iac — Top 10 Common Pitfalls

Anti-patterns for infrastructure changes and deployment operations. Additive on [constraints.md](constraints.md).

## P01 — Floating Terraform provider
- **NG**: declare a provider source without a version constraint.
- **OK**: constrain the provider and upgrade it in a reviewed dependency change.
- **Why**: an unrelated initialization can select an incompatible provider.
- **Detect**: Layer-1 `pack-devops-iac-terraform-unpinned-provider`.
- **Severity**: error

## P02 — Floating remote module
- **NG**: use an unversioned registry module or Git branch.
- **OK**: set a registry `version` or immutable Git `ref`.
- **Why**: identical source code can produce different infrastructure plans over time.
- **Detect**: Layer-1 `pack-devops-iac-terraform-unpinned-module`.
- **Severity**: error

## P03 — Mutable workload image
- **NG**: deploy `image: service:latest`.
- **OK**: deploy a release tag or digest that identifies one artifact.
- **Why**: rollback and audit evidence become nondeterministic.
- **Detect**: Layer-1 `pack-devops-iac-k8s-mutable-image-tag`.
- **Severity**: error

## P04 — Traffic before readiness
- **NG**: a long-running workload has containers but no readiness probe.
- **OK**: define a readiness signal aligned with the service dependency contract.
- **Why**: schedulers can route traffic before the workload can serve it safely.
- **Detect**: Layer-1 `pack-devops-iac-k8s-missing-readiness-probe`.
- **Severity**: warn

## P05 — Unschedulable resource intent
- **NG**: omit resource requests from a long-running workload.
- **OK**: declare evidence-based or explicitly provisional CPU and memory requests.
- **Why**: placement and capacity behavior becomes accidental.
- **Detect**: Layer-1 `pack-devops-iac-k8s-missing-resource-requests`.
- **Severity**: warn

## P06 — Apply without a plan gate
- **NG**: CI runs `terraform apply` without producing or consuming a plan.
- **OK**: review a plan and apply the reviewed plan artifact.
- **Why**: reviewers cannot see the actual infrastructure mutation.
- **Detect**: Layer-1 `pack-devops-iac-terraform-apply-without-plan`.
- **Severity**: error

## P07 — Rebuild during promotion
- **NG**: production rebuilds an artifact from the same commit.
- **OK**: promote the exact artifact verified in the previous environment.
- **Why**: the production artifact may differ from the tested artifact.
- **Detect**: Layer-2 self-check.
- **Severity**: error

## P08 — Drift with no owner
- **NG**: periodic plan output exists but nobody owns triage or reconciliation.
- **OK**: define cadence, owner, notification route, and reconciliation workflow.
- **Why**: unmanaged drift silently invalidates the declared desired state.
- **Detect**: Layer-2 self-check.
- **Severity**: warn

## P09 — Rollback as a slogan
- **NG**: a release runbook says “rollback if needed” without criteria or verification.
- **OK**: name trigger, owner, commands, data implications, and success signals.
- **Why**: an incident is the worst time to invent recovery mechanics.
- **Detect**: Layer-1 `pack-devops-iac-deployment-no-rollback` plus Layer-2 self-check.
- **Severity**: warn

## P10 — Hidden blast radius
- **NG**: approve a plan without calling out replacements, destroys, or environment reach.
- **OK**: summarize affected resources, environments, dependencies, and irreversible operations.
- **Why**: a syntactically small change can have a large operational impact.
- **Detect**: Layer-2 self-check.
- **Severity**: error

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 provider pinning | `pack-devops-iac-terraform-unpinned-provider` | ✓ |
| P02 module pinning | `pack-devops-iac-terraform-unpinned-module` | ✓ |
| P03 image immutability | `pack-devops-iac-k8s-mutable-image-tag` | ✓ |
| P04 readiness | `pack-devops-iac-k8s-missing-readiness-probe` | ✓ |
| P05 resource requests | `pack-devops-iac-k8s-missing-resource-requests` | ✓ |
| P06 plan gate | `pack-devops-iac-terraform-apply-without-plan` | ✓ |
| P07 promotion | — | ✓ |
| P08 drift | — | ✓ |
| P09 rollback | `pack-devops-iac-deployment-no-rollback` | ✓ |
| P10 blast radius | — | ✓ |
