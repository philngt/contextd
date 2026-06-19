# Product Brief: Reliable Agent Inputs

## Problem

Teams already have decisions, contracts, requirements, and runbooks, but agents consume them inconsistently. The result is duplicated prompting, stale rules, and reviews that depend on whichever docs the agent happened to read.

## Target User

Maintainers and staff engineers rolling AI coding agents into a team codebase.

## Success Metric

- A new contributor can run `contextd context` or `contextd explain` and see the same selected source docs as a teammate.
- Golden task evaluation catches a missing required product, requirement, or design doc before rollout.

## Acceptance Criteria

- The build artifact lists selected docs, gaps, warnings, source hashes, and budget estimates.
- Product, requirement, and design docs are selected as first-class context when the relevant packs are active.
- The default workspace demo does not enable extra packs globally.
