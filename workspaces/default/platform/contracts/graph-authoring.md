---
type: Contract
title: "Contract: graph-authoring"
description: "Opt-in source-to-proposal authority, identity and isolation boundary; does not replace Synapse or task context."
status: draft
node_id: contract.graph-authoring.v1
freshness: unknown
---

# Contract: graph-authoring

The normative authoring rules are [GA-01 through GA-08](../../../../templates/graph-authoring/authoring-contract.md).
The machine-readable [proposal](../../../../templates/graph-authoring/graph-proposal.schema.json),
[baseline](../../../../templates/graph-authoring/graph-baseline.schema.json) and
[product-software profile](../../../../templates/graph-authoring/product-software.v1.json)
are the additive review-input contract. [The guide](../../../../docs/graph-authoring.md)
describes capabilities, usage, limitations and later exit gates.

This contract is an opt-in authoring extension. It does not alter
[synapse-node-edge-schema](synapse-node-edge-schema.md) or
[graph-projection](graph-projection.md), authorize model/code execution, or turn proposals
into canonical workspace knowledge. Follow the source-isolation, reviewed-write and
immutable-evidence boundaries of those existing contracts and engine rules.

A new proposal is not a task-context artifact or a memory promotion record. Exact review
and current owner revision checks are required outside this first-slice validator.
