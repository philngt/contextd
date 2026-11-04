---
type: Decision
title: Consumer write recovery
description: Synthetic decision demonstrating evidence-backed context selection.
status: stable
node_id: decision.consumer-write-recovery.v1
freshness: fresh
---

# Consumer write recovery

## Status

Accepted within this synthetic example. This record does not describe a production incident.

## Context

The telemetry ingestion worker receives records that must survive a persistence failure.

## Decision

The telemetry ingestion worker must persist each accepted record before acknowledging delivery.
If persistence fails, the worker must retain the record for retry and report the failure.

## Consequences

Changing producer acknowledgement or retry settings alone does not repair a failed consumer write.
Recovery requires an observable retry or reconciliation path for the failed persistence operation.
