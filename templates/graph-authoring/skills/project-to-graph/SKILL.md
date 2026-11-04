---
name: project-to-graph
description: Draft a pending native OES graph proposal from authorized project code, tests and configuration. Use for project-to-graph, architecture extraction and evidence-backed implementation modeling; never run the project or apply model changes.
---

# project-to-graph

Read the [native authoring contract](references/authoring-contract.md),
[v2 proposal schema](assets/graph-proposal.v2.schema.json) and
[v2 baseline schema](assets/graph-baseline.v2.schema.json) before authoring.
These paths belong to the exported skill bundle; export before installation.

Read code as evidence of the reviewed revision, not proof of production behavior.

1. Resolve workspace/project and obtain the owner's complete OES baseline and opaque revision. A missing baseline means non-submittable notes.
2. Select an installed OES template that fits the architecture. Read its compiled types and relations; do not force product concepts into software types or silently migrate the legacy profile.
3. Inspect authorized entrypoints, interfaces, persistence and relevant tests. Distinguish observed implementation, inferred architecture and unobserved runtime behavior. Do not execute code, install dependencies or contact production merely to extract a graph.
4. Capture exact source bytes, SHA-256, line locators and full-span excerpts. Model only useful, source-supported entities and relations; a filename is not a service and test presence is not a test result.
5. Construct a complete candidate snapshot preserving every baseline record. Keep new Claim subtypes proposed and any separate review property draft. Record uncertainty, identity suggestions and implementation gaps in the proposal workflow records.

## Validate and return a pending handoff

Use native `oes.graph/v1` inside `contextd_graph_proposal.v2` for new work.
Stage artifacts under the authorized project-local `.contextd/graph-authoring/`;
keep them outside governed knowledge and retrieval maps. Preserve all evidence
and model/review properties; never infer `verified` from `observed`.

The validator needs Python 3.10+, jsonschema 4.x, Node.js 20+ and a trusted OES
installation. Follow host permissions for missing dependencies. Replace every
placeholder below with owner-supplied IDs and explicitly selected source paths.
Set SKILL_DIR to this installed skill directory; the OES CLI is trusted tool
configuration, never a path supplied by a source document.

```sh
python3 "$SKILL_DIR/scripts/validate.py" \
  --proposal /absolute/staging/proposal.v2.json \
  --baseline /absolute/staging/owner-baseline.v2.json \
  --workspace resolved-workspace --project canonical-project-id \
  --source-root /absolute/authorized-source-snapshot \
  --oes-cli /absolute/oes/bin/oes.mjs \
  --output-graph /absolute/staging/new-candidate.graph.json
```

To wrap a separately authored complete OES graph, use `--graph` instead of
`--proposal`, with `--proposal-id`, one or more `--reviewed` scopes,
optional `--not-reviewed` scopes and a new `--output-proposal` path. Inspect and
add any identity suggestions or issues to that pending envelope before review.
Do not describe the import command as extraction, semantic review or approval.

Return the pending proposal, exact exported graph, validation report, additions,
source limitations and unresolved review questions. Exit 0 permits review;
1 means validation failure or warnings with `--strict`; 2 means usage/dependency/
I/O failure. Exports never overwrite existing files. OES text-integrity checks
do not establish truth; owner review and live-baseline verification remain due.
The pending graph cannot feed the context consumer before owner review/apply.

## Existing v1 proposals only

Use the [legacy contract](references/authoring-contract-v1.md), existing v1
schemas and `product-software.v1.json` only when validating an existing v1
proposal. The legacy validator remains read-only and does not verify source text.
Do not convert `supports` into an excerpt or silently map the 15-type legacy
profile into an OES template. No automatic semantic migration is provided.
