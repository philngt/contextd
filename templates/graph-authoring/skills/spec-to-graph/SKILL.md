---
name: spec-to-graph
description: Turn a PRD, SRS, user story or feature specification into a requirement graph proposal with acceptance criteria and evidence. Use for spec-to-graph. Not for claiming implementation or generating application code.
compatibility: An agent with authorized source tools; optional validator requires Python 3.10+ and jsonschema 4.x.
metadata:
  version: "0.1.0"
  contract: "contextd_graph_proposal.v1"
---

# spec-to-graph

Read [the common contract](references/authoring-contract.md) before authoring.
Use [the profile](assets/product-software.v1.json),
[proposal schema](assets/graph-proposal.schema.json) and
[baseline schema](assets/graph-baseline.schema.json). Paths are relative to this skill.
These resources are assembled by the repository exporter; do not install the bare template.

Extract intended product behavior without filling missing requirements with best practices.

1. Resolve/bind workspace and product; read the owner baseline and shared profile.
2. Read full relevant sections, including tables, definitions and exceptions. Maintain
   reviewed/not-reviewed scope. Use host document tools for attachments; inspect embedded
   figures when necessary. Never claim a universal parser or silently skip unreadable pages.
3. Identify Problem, Feature, Spec, Actor, Action, Workflow, DomainType and BusinessRule
   only when supported. Extract AcceptanceCriterion without inventing thresholds.
   One file can produce many objects; multiple files can describe one Spec.
4. Preserve source requirement IDs in scoped statements/source locators. Preserve polarity,
   must/should/may, preconditions and exceptions. Missing acceptance conditions are gaps.
5. Reuse explicit/reviewed owner IDs. Keep target claims as to-be even when a requirement is
   approved. A document's historical description can be as-is/reference; source kind alone
   does not determine the model.
6. Compare with existing implementation claims. Distinguish target gaps, version/scope
   differences and genuine incompatible assertions. Do not silently change either source.
7. Stage a pending proposal, validate, report exact additions and unresolved decisions.

No source spec: return a clearly labeled scaffold or note; do not fabricate requirements.

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
