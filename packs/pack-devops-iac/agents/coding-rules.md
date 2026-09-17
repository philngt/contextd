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

## Domain Decision Lens

Use within this pack's scope; existing constraints remain authoritative.

- **Observe:** Inspect desired configuration, actual state, the reviewed saved plan, immutable artifact identity, environment ownership, failure domains, and rollback/roll-forward conditions.
- **Mechanism:** State drift or rebuilding an artifact changes what was approved. A running process may still be unable to serve traffic; readiness and deployment success are different observations.
- **Choose:** Prefer a bounded change with observable promotion gates. Investigate drift before proposing reconciliation; promote the verified artifact rather than silently regenerating production inputs.
- **Exception:** Reverting code does not necessarily reverse schema or external effects. A successful plan or probe is limited evidence, not a blanket guarantee that rollout and recovery are safe.
- **Verify:** Check that apply consumes the reviewed plan, promoted digests match, rendered workloads meet policy, and service-level signals recover. Rehearse the documented rollback or forward-fix path.
- **Stop:** Pause when actual state invalidates approval, replacement/destruction exceeds scope, or the recovery path is unproven. Request the missing owner decision instead of force-reconciling state.
