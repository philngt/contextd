# pack-devops-iac — Prompt Overrides

Pack-specific additions injected when this pack is active.

## System prompt addition

For infrastructure and deployment work, treat the reviewed change plan, immutable artifact identity, environment scope, drift ownership, and recovery procedure as part of correctness. Separate mechanically detectable defects from design checks. Do not infer provider behavior, production topology, promotion policy, or rollback safety when workspace knowledge is missing.

## Builder prompt self-check (additions)

```md
### DevOps and IaC (pack-devops-iac)
- Remote Terraform/OpenTofu providers and modules are versioned immutably.
- The reviewed plan identifies creates, updates, replacements, destroys, and affected environments.
- Automated apply consumes or follows a reviewed plan.
- Kubernetes workload images are immutable; readiness and resource requests are explicit.
- Production promotes the same artifact verified in the preceding environment.
- Drift detection has a cadence, owner, notification route, and reconciliation workflow.
- Rollback or roll-forward defines trigger, owner, commands, data implications, and verification.
- Generated/rendered infrastructure is validated, not only its template source.
- Security, performance, and database-specific concerns are delegated to their active packs without duplicating or weakening them.
```

## Common Pitfalls

Before completion, check P01–P10 in [`../common-pitfalls.md`](../common-pitfalls.md). Confirm all Layer-1 `pack-devops-iac-*` validators pass and explicitly evaluate each Layer-2-only item.
