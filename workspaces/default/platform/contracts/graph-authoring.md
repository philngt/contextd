---
type: Contract
title: "Contract: graph-authoring"
description: "Native OES source-to-proposal authority, complete owner baseline and pending review isolation."
status: draft
node_id: contract.graph-authoring.v1
freshness: unknown
---

# Contract: graph-authoring

New proposals follow [GA-01 through GA-08, v2](../../../../templates/graph-authoring/authoring-contract.md).
The native [proposal](../../../../templates/graph-authoring/graph-proposal.v2.schema.json)
and [baseline](../../../../templates/graph-authoring/graph-baseline.v2.schema.json)
define the review envelope and binding metadata. Each embeds a complete
`oes.graph/v1` snapshot; OES owns the graph schema, ontology vocabulary and
structural/textual evidence checks. contextd owns additive baseline preservation,
reserved IDs, identity-review candidates, issues and pending status.

The [legacy v1 contract](../../../../templates/graph-authoring/authoring-contract-v1.md),
schemas and product-software profile remain solely for existing v1 proposals.
No automatic semantic migration to OES is provided.
[The guide](../../../../docs/graph-authoring.md) describes native import/export,
the runnable example and the remaining owner-review boundary.

This contract is an opt-in authoring extension. It does not alter
[synapse-node-edge-schema](synapse-node-edge-schema.md) or
[graph-projection](graph-projection.md), authorize model/code execution, or turn proposals
into canonical workspace knowledge. Follow the source-isolation, reviewed-write and
immutable-evidence boundaries of those existing contracts and engine rules.

A native export preserves the exact checked graph bytes and carries a pending
proposal marker. The [OES consumer](oes-context.md) rejects that marker before
source selection. It is a declaration rather than an authenticated approval
receipt. Exact review, live owner revision/source checks and owner apply remain
external; validation never authorizes promotion or code execution.
