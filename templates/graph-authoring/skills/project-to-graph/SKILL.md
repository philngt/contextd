---
name: project-to-graph
description: Turn an existing code project into an evidence-backed graph proposal. Use for project-to-graph, workflow/domain recovery or source-to-model mapping. Not for implementation, refactoring or spec-only extraction.
compatibility: An agent with authorized source tools; optional validator requires Python 3.10+ and jsonschema 4.x.
metadata:
  version: "0.1.0"
  contract: "contextd_graph_proposal.v1"
---

# project-to-graph

Read [the common contract](references/authoring-contract.md) before authoring.
Use [the profile](assets/product-software.v1.json),
[proposal schema](assets/graph-proposal.schema.json) and
[baseline schema](assets/graph-baseline.schema.json). Paths are relative to this skill.
These resources are assembled by the repository exporter; do not install the bare template.

Recover one useful workflow, not a tree of files. Project inputs are read-only.

1. Resolve/bind the workspace and canonical project, and obtain an owner baseline (GA-01/02).
   Inspect any existing evidence intake record before creating a second source intake.
   The existing code-analyze/evidence pipeline can provide sources; do not duplicate or
   bypass its immutable-source and review gates. Do not invoke host-specific slash commands
   as if they were executable CLI binaries.
2. Inventory entry points, meaningful components, interfaces, migrations and tests within scope.
   Use names as search leads, not identity proof. Pick the user's workflow or one bounded,
   explicitly justified workflow with readable sources.
3. Trace trigger, Actor, Action, DomainType, BusinessRule, outcome and failure cases found.
   Preserve branches/repeated actions in source-backed claims. Missing behavior is an issue.
4. Map Component/Interface and Screen only where evidence exists. A test definition is not
   a passing test; a framework annotation is not proof of production behavior.
5. Reuse baseline IDs. Record code behavior as as-is; an inferred Problem, Feature or
   Decision remains inferred. A spec embedded in the repo can instead support to-be.
6. Propose additive changes and identity matches. Separate implementation gaps from actual
   source conflicts. Preserve assertions from other sources and accepted owner data.
7. Stage, validate and report under GA-06/07. Never refactor, commit, push or auto-apply.

No accessible code: report that none was inspected. Do not invent paths or repository revisions.

## Output and verification

Return one pending proposal with source ledger, typed additions, scoped claims, evidence,
identity-match candidates and issues. All model writes remain unapproved. Prefer an authorized
project-local `.contextd/graph-authoring/` staging directory, never canonical workspace Markdown.
A missing owner baseline means non-submittable draft notes, not invented baseline fields.

The following are validator arguments, not instructions to perform extraction. Set SKILL_DIR
to the actual installed skill directory and replace the example paths and IDs with resolved
values. Check the optional dependency before running; do not install it without permission.

```sh
python3 "$SKILL_DIR/scripts/validate.py" \
  --proposal /absolute/staging/proposal.json \
  --baseline /absolute/staging/baseline.json \
  --workspace resolved-workspace --project canonical-product-id
```

Exit 0 means structurally valid with possible warnings; 1 means validation failure
(or warnings with --strict); 2 means usage/dependency/I/O/JSON/profile failure.
Report semantic review and source/live-baseline verification as NOT performed by the validator.
This skill has no apply permission and provides no complete execution context.
