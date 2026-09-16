# Experimental semantic graph projection

**Status: opt-in, advisory metadata projection.** This is the first graph-first
slice, not Synapse v2 and not a replacement for `contextd context`.

## What is implemented

`contextd-project` compiles a bounded neighborhood from explicit Synapse seed
IDs. It uses a single existing workspace source snapshot, follows typed edges,
adds semantic roles and region tags, and returns inspectable node/edge metadata,
parent paths, omitted dependencies, source hashes, and a deterministic projection
hash. It never modifies canonical files or materializes a second knowledge store.

```text
human-reviewed Markdown/YAML
  -> existing workspace-scoped Synapse snapshot
  -> explicit seed IDs + traversal policy
  -> bounded neighborhood + dependency/boundary diagnostics
  -> advisory graph metadata (JSON or text)

normal contextd context + policy checks remain the execution-context path
```

See the [normative contract](../workspaces/default/platform/contracts/graph-projection.md)
and [JSON schema](../templates/graph-projection.schema.json).

## Install and inspect

From a checkout containing this change:

```bash
python -m pip install -e ".[test]"
contextd-project --help
contextd-project --cwd . \
  --seed contract.graph-projection.v1 \
  --depth 2 --max-nodes 20 --as-of 2026-09-16 --format text
```

The sample seed contract is intentionally draft and produces a lifecycle warning.
The console entry point is experimental and separate from `contextd`; released
v1.4.0 binaries do not acquire a new subcommand or binary through this PR.
A source-checkout alternative is `python scripts/cmd_graph_project.py` with the
same arguments. Output goes to stdout; the command writes no files.

Seeds must be exact IDs in the active workspace. `contextd synapse --preview`
can be used to inspect available IDs. Missing seeds fail rather than silently
falling back to keyword selection. There is no `--task` seed inference yet.

## Author semantic annotations

Keep the established OKF document type and add independent optional metadata:

```yaml
type: Pattern
status: stable
node_id: strategy.offline-conflict-resolution
knowledge_role: strategy
regions: [storage, sync]
relations:
  - type: depends_on
    target: contract.offline-sync
  - type: derived_from
    target: mechanism.concurrent-updates
```

Create referenced nodes as reviewed canonical sources before using those IDs.
This example is illustrative, not a bundled demo graph.

A `primitive` describes a basic element; a `mechanism` describes interactions;
a `strategy` explains a context-dependent choice; a `skill` describes a reusable
capability; a `guideline` provides guidance; a `procedure` describes ordered
execution. These roles are not an obligatory linear ladder, and a `supports`
edge is an authored claim, not proof of causation or an automatic trust score.

Supported roles are `knowledge`, `primitive`, `mechanism`, `principle`, `strategy`,
`skill`, `pattern`, `guideline`, `constraint`, `procedure`, `decision`, `evidence`,
and `artifact`. Without an explicit role, known document kinds map to the
corresponding role (`contract` to `constraint`, `runbook` to `procedure`), otherwise
`knowledge`. Bad annotations are counted and do not invent a role or region.

## Traversal semantics

Default traversal follows outgoing v1 relations except `related_to`, to depth 2
and at most 20 nodes. Repeated `--seed`, `--edge-type`, and `--region` options are
supported. `--direction incoming` supports reverse inspection without reversing
edge semantics. `--direction both` explores both directions.

All seeds are retained. Within each BFS depth, constraints are considered before
other roles, then dependencies/implementations/derivations/conflicts/replacements/
support/related edges, with stable-ID tie-breaking. The selected node's `parent`,
`via_edge`, `seed`, and `depth` reconstruct one deterministic shortest path.
A semantic annotation cannot demote a document whose kind is `contract`.
This is not all-path enumeration, causal reasoning, or dependency closure.

A region filter is a union of explicitly requested tags. Untagged nodes and nodes
outside those tags are not selected, even when they are dependencies; the missing
dependency is reported. Regions never permit crossing workspace boundaries and
must not be mistaken for permission checks or automatic project boundaries.

Internal edges remain in the output even when the edge filter forbids traversing
them. Boundary edges show `region-boundary`, `edge-filter`, `direction-filter`,
`depth-limit`, or `node-limit`. Missing outgoing dependencies and omitted
implemented constraints become `gaps`. External contradictions and incoming
replacements become warnings. Large boundary, gap, and warning lists are capped
by `--max-boundary-edges` (default 100), with true totals and truncation counters.
The complete internal edge set is bounded by the selected node set, not by this
boundary-report limit. No hard token-budget claim is made.

## Safety, policy and reproducibility

The command uses the current config resolver and safe Synapse builder. It rejects
snapshot errors, validates snapshot identity, reads semantic metadata from the
retained in-memory source records, and exposes no document bodies or titles.
Runtime observations and raw evidence remain excluded; promotion still requires
review and canonical write. Source files remain canonical. A new build is required
to observe source edits; projection never silently re-reads newer files.

`execution_authorized` is always `false`. This artifact does **not** include engine
or pack static context, run policy checks, or provide a complete prompt. It must
not be used to bypass `contextd context`, `contextd policy-check`, or review gates.
IDs/paths are still workspace metadata; do not publish private projections.

For fixed source hashes, evaluation date and normalized policy, selection and the
projection hash are repeatable. Changing semantic annotations changes the source
hashes and projection. Build timestamps are not part of projection identity.
This does not establish that an LLM response is deterministic or more accurate.

Without `--strict`, an inspectable graph with warnings or omitted dependencies
exits 0. With `--strict`, those conditions exit 1. Invalid arguments/ranges exit 2;
resolution, unknown seed, and invalid snapshot failures exit 1. No-issue output
means only no observed diagnostics, not proof that all requirements are present.

## Tests and remaining work

```bash
python scripts/test_graph_projection.py
python scripts/test_graph_projection_integration.py
```

Unit tests cover deterministic multi-seed traversal, cycles, boundaries, invalid
inputs, role separation, contract priority, omitted dependencies, report caps,
nonmutation, hashes, and schema validity. Integration tests cover the actual
snapshot/frontmatter/config/CLI path, no second source read, source drift,
workspace escape, runtime exclusions, and default versus strict exit behavior.
The Graph Projection workflow runs both suites on Python 3.10 and 3.12.

Later slices require separate contracts and evidence before becoming defaults:

1. Integrate reviewed seed selection and dependency-aware context compilation
   while preserving engine/pack policies and budgets; do not silently plug this
   metadata artifact into an agent prompt.
2. Benchmark required-neighbor recall, omission accuracy and final agent outcomes
   against the same workspace/task baseline, not just a prettier graph.
3. Add external graph-source protocols or graph-first editing only with explicit
   source ownership and migration rules. No second mutable source of truth.

Graph databases, automatic runtime-memory promotion, orchestrators, application
generation, new causal edge semantics, and wholesale Synapse-v2 migration are
outside this PR. The existing [build-system model](build-system-model.md) remains
in force.
