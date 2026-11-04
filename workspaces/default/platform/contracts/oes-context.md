---
type: Contract
title: "Contract: oes-context"
description: "Opt-in OES graph validation, workspace source mapping and evidence-preserving context selection."
status: draft
node_id: contract.oes-context.v1
freshness: unknown
---

# Contract: oes-context

## Rule

OES owns the ontology and evidence validation contract. contextd consumes an
explicitly selected `oes.graph/v1` graph as an additional retrieval input and
compiles the resulting documents through its existing context pipeline.

## Input boundary

- The graph MUST reside inside the active workspace. Relative graph paths are
  resolved from the knowledge root; `metadata.workspace` MUST match the active
  workspace exactly.
- `Source.properties.uri` MUST be a literal path relative to that workspace.
  Absolute paths, URI schemes, parent traversal, foreign workspaces and symlink
  escapes MUST be rejected. A source MUST already exist in the governed Synapse
  source snapshot; raw evidence and generated/runtime files are not admissible.
- The requested OES CLI is trusted executable configuration. Graph and source
  contents MUST NOT choose executables or be interpreted as instructions.
- An explicitly pending `metadata.contextdProposal` marker MUST be rejected.
  Malformed markers MUST NOT fall back to unmarked graph handling. This is a
  declarative workflow boundary, not authenticated proof of owner approval.
- OES MUST validate the exact graph bytes and retained workspace source bytes
  consumed by the build, with structural and evidence checks enabled and
  warnings treated as errors. A failed, incomplete or skipped validation MUST
  fail the requested build before materialization.
- Evidence uses a nonempty excerpt equal to the entire `Lx` or `Lx-Ly` span,
  with line endings normalized by OES. A supplied source SHA-256 binds the
  complete raw source bytes. Output citations always include the actual source
  hash, whether or not the graph supplies an expected hash.

## Selection and output

Task keywords may match semantic node IDs, labels, names, titles, statements or
summaries. Source paths and evidence quotations are not semantic search seeds.
Only incident assertions one edge away from matched nodes supply retrieval
evidence; this contract does not authorize unbounded traversal or inference.

Matching assertions route their Evidence nodes to governed source documents.
The documents MUST retain existing categories, lifecycle handling, ranking and
document budgets. Graph evidence contributes one bounded score adjustment per
document, regardless of the number of matching assertions.

JSON and emitted Markdown MUST preserve graph identity/hash, assertion and
endpoint IDs, relation type, assertion/claim status, confidence and time bounds
when present, evidence/source IDs, source path/hash, locator and excerpt.
The rendered evidence MUST contribute to both token estimates and context-pack
identity. The selection trace MUST show the graph contribution.

A supplied graph that contributes no selected task evidence MUST produce an
`oes-coverage` gap under the [retrieval coverage contract](retrieval-coverage.md).
No-match and budget-omitted routes MUST remain distinct. A graph-route miss MUST
NOT assert that the entire workspace lacks relevant knowledge.

Text integrity does not establish semantic entailment or truth. `inferred`,
`hypothesis`, `proposed`, `rejected` and `superseded` information MUST remain
explicitly labeled. Validation MUST NOT promote pending authoring proposals,
approve claims or write canonical workspace knowledge.

## Related

- [Integration guide](../../../../docs/oes-integration.md)
- [Citation format](citation-format.md)
- [Synapse source and projection contract](synapse-node-edge-schema.md)
- [Graph authoring boundary](graph-authoring.md)
