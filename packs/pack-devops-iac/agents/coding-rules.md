# pack-devops-iac — Working Rules

## Infrastructure changes

- Keep reusable modules small, versioned, and explicit about inputs, outputs, and ownership.
- Separate environment-specific values from reusable infrastructure definitions.
- Attach the plan/diff and summarize creates, updates, replacements, and destroys in review.
- Prefer staged changes when provider, state, networking, or identity boundaries change.
- Treat generated plans as review evidence, not as durable secrets-safe artifacts by default.

## Kubernetes workloads

- Use digest-pinned images for long-running workloads; resolve release tags to digests before deployment.
- Base requests and autoscaling thresholds on observed demand; label provisional values for follow-up.
- Design probes around service readiness rather than process existence.
- Validate rendered manifests when Helm, Kustomize, or another generator is used.

## Delivery and operations

- Build once, attest once, and promote the same artifact through environments.
- Make concurrency and cancellation behavior explicit for environment-changing workflows.
- Record drift findings separately from approved changes; reconcile them through the normal review path.
- Test rollback commands and verification signals before relying on a runbook during an incident.
