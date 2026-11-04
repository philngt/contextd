---
type: Decision
title: Delivery deduplication policy
description: Synthetic local policy for the external-project example.
status: stable
node_id: decision.payments.delivery-policy.v1
freshness: fresh
---

# Delivery deduplication policy

## Status

Accepted within this synthetic example. This record is not a production claim.

## Decision

Record each delivery identifier in the same durable transaction as its payment write.
If that identifier is already recorded, leave the payment unchanged and acknowledge the delivery.
Acknowledge a new delivery only after the transaction commits.

## Consequences

The durable store needs a unique delivery marker and an atomic write boundary.
The runtime must retry failed transactions without recording a successful delivery.
