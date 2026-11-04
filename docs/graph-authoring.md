# Graph authoring with OES

**New authoring uses native `oes.graph/v1` graphs inside a pending contextd review
proposal.** OES supplies the graph schema, ontology template and evidence checks.
contextd preserves the owner baseline, workspace/project binding and review
lifecycle, then exports the exact checked graph for owner-controlled review.

The three authoring skills (`project-to-graph`, `spec-to-graph`, `docs-to-graph`)
produce this v2 format by default. Existing v1 proposals remain supported by their
legacy validator; no automatic semantic migration is claimed.

## Responsibility and ownership

| Layer | Responsibility |
|---|---|
| OES | Graph envelope, entity/relation definitions, semantic constraints, source hashes and exact excerpt validation. |
| contextd authoring | Workspace/project binding, complete owner baseline, additive diff, reserved IDs, identity-review candidates and issues. |
| Authoring agent | Read authorized sources, propose meaning, preserve uncertainty and produce exact citations. |
| Canonical owner | Supply the real revision and baseline; review and apply changes against current owner state. |
| contextd consumer | Read an admitted OES graph, select governed workspace documents with evidence and compile agent context. |

A Product Graph installation can be the canonical owner, but it is optional and
needs an explicit owner adapter. This kit does not create an independently
editable copy of that application's model. Baseline export and owner apply are
still owner responsibilities.

## Run the native example

The [refund receipt fixture](../examples/graph-authoring/oes-native/README.md)
contains an owner baseline, a complete native graph, a v2 proposal and an exact
local source. Its proposed rule remains `proposed`; the relationship remains a
`hypothesis` even though both evidence spans pass OES checking.

From a contextd checkout, with a trusted OES checkout that supports JSON reports,
exact evidence checking and `contracts/graph-envelope.schema.json`:

```sh
python -m pip install -e '.[authoring,test]'
OES_CLI=/absolute/path/to/oes/bin/oes.mjs

python scripts/cmd_graph_authoring.py \
  --proposal examples/graph-authoring/oes-native/proposal.json \
  --baseline examples/graph-authoring/oes-native/baseline.json \
  --workspace default --project refund-demo \
  --source-root examples/graph-authoring/oes-native/sources \
  --oes-cli "$OES_CLI"
```

This calls the actual OES CLI and should report two checked evidence spans,
zero skipped spans, one added relation and two added nodes. It preserves the
existing owner Service, Source, Evidence and relation. The fixture is synthetic;
its inventory and proposed policy do not establish production behavior.

The installed distribution provides the same command as
`python -m contextd.cmd_graph_authoring`. The source-checkout script and exported
skill validator use the same runtime implementation and schemas.

## Import and export

Use `--graph` to wrap a complete OES graph into a pending v2 review envelope.
The caller supplies the proposal ID, reviewed scope, baseline and binding. This
command performs no semantic extraction or automatic issue classification.

```sh
mkdir -p .contextd/graph-authoring

python scripts/cmd_graph_authoring.py \
  --graph examples/graph-authoring/oes-native/candidate.graph.json \
  --baseline examples/graph-authoring/oes-native/baseline.json \
  --workspace default --project refund-demo \
  --proposal-id proposal:refund-receipts \
  --reviewed 'Complete synthetic refund specification and supplied owner baseline.' \
  --not-reviewed 'Runtime implementation and production behavior.' \
  --source-root examples/graph-authoring/oes-native/sources \
  --oes-cli "$OES_CLI" \
  --output-proposal .contextd/graph-authoring/proposal.v2.json \
  --output-graph .contextd/graph-authoring/candidate.graph.json
```

Both files are created only after successful validation; an existing destination
is refused. For repeated runs choose new paths. The exported graph bytes are
exactly the bytes checked by OES and identified by the report's `graph_hash`.

For an already authored v2 proposal, use `--proposal` and optionally
`--output-graph`; `--output-proposal`, proposal IDs and scope flags are specific
to graph import. Add identity-match candidates and review issues to the pending
proposal when needed, then validate the updated envelope and review its new hash.

| Option | Meaning |
|---|---|
| `--proposal` | Validate an existing pending v2 proposal; existing v1 still dispatches to its legacy validator. |
| `--graph` | Import a complete native OES graph; mutually exclusive with `--proposal`. |
| `--baseline` | Explicit owner-supplied baseline. Native v2 requires complete graph records. |
| `--workspace`, `--project` | Explicit expected owner binding, checked in both envelopes and graph metadata. |
| `--source-root` | Authorized local source root, required for native v2. Only Source URIs are captured. |
| `--oes-cli` | Trusted local OES entrypoint; otherwise use `oes` on PATH. The same installation supplies the graph schema. |
| `--oes-timeout` | Positive finite timeout per OES command, default 30 seconds. |
| `--proposal-id`, `--reviewed`, `--not-reviewed` | Import-only review context; scope options are repeatable. |
| `--output-proposal`, `--output-graph` | Explicit new-file destinations. Graph output always carries the pending marker. |
| `--strict` | Treat review warnings as a nonzero exit and prevent exports. |
| `--profile` | Legacy v1 only. Native graphs use their selected OES template. |

Exit 0 means validation passed with possible review warnings, 1 means validation
failed or `--strict` found warnings, and 2 means usage, dependency, input or output
failure. No failure path intentionally overwrites a file. An I/O failure while
creating two new outputs can leave the first pending artifact for inspection.

## Native contracts and validation boundary

Read the [v2 authoring contract](../templates/graph-authoring/authoring-contract.md)
for GA-01 through GA-08 and the
[workspace contract](../workspaces/default/platform/contracts/graph-authoring.md)
for its boundary with ordinary context compilation.

- [Native proposal schema](../templates/graph-authoring/graph-proposal.v2.schema.json)
- [Native baseline schema](../templates/graph-authoring/graph-baseline.v2.schema.json)
- [OES graph envelope](https://github.com/philngt/oes/blob/main/contracts/graph-envelope.schema.json)

The contextd schemas contain review and binding fields. Native node types,
relation names, endpoint rules and evidence semantics come from OES. The graph
metadata identifies its graph ID, workspace, project ID and ontology version.
The version must match the compiled template from the selected OES installation.
After checking the candidate, the compiled fingerprint is checked again. A
template change during validation fails the handoff even if the declared version
is unchanged. This is a concurrent-update check, not executable attestation;
the caller selects and trusts the local OES installation.

A baseline is a complete OES graph with a real opaque owner revision and reserved
IDs. The complete proposed snapshot must preserve every existing node and edge
and all graph header metadata except the new proposal marker. This first slice
supports additive records only. A v1 baseline's ID/type stubs cannot supply the
missing canonical properties; an owner must provide the complete native snapshot.

Both supplied graph envelopes are schema-checked. OES validates the complete
candidate, including unchanged baseline records. This does not independently
verify baseline ownership, obtain a new baseline or check a live owner revision.

Each Source declares the SHA-256 of its full raw bytes. Files are captured once
from the selected source root and copied into a temporary validation tree. OES
checks the exact candidate bytes with
`check-graph --with-evidence --require-hash --warnings-as-errors --json`.
`Lx` / `Lx-Ly` excerpts must match the entire selected span after OES line-ending
normalization. Every Evidence must be checked; skipped sources fail the request.

Source paths are literal and local. Traversal, remote URLs, encoded paths,
blocked secret files and source descendant symlinks are rejected. The explicit
root and output parent may resolve platform aliases such as macOS `/var`.
JSON inputs are bounded to 4 MiB, each source to 5 MiB and total source bytes to
50 MiB. No source code is executed and no remote source is fetched.

## Review and handoff to the consumer

A successful report includes the graph hash, review-input hash, compiled ontology
hash, added IDs, captured source hashes and separate validation results.
`review_input_hash` binds the proposal, baseline, workflow schemas, OES schema,
compiled template and captured source identities. Review scope or ontology changes
therefore change the review input even when the graph bytes remain identical.

| Field | Interpretation after successful native validation |
|---|---|
| `sources_verified: true` | Local source hashes and exact excerpts passed; semantic truth is still unreviewed. |
| `semantic_review_required: true` | A reviewer must assess meaning, scope, evidence relevance and uncertainty. |
| `live_baseline_verified: false` | The supplied owner revision was compared; the current owner was not queried. |
| `apply_supported: false` | No canonical graph write or promotion command ran. |
| `execution_authorized: false` | Model review does not authorize application execution or deployment. |

New OES Claim nodes and subtypes remain `proposed`; a separate claim `review`
property remains `draft` when supplied. `model`, `verification`, scope, freshness,
relation assertionStatus, confidence and time bounds are preserved. Observing a
statement in a source does not promote a hypothesis to verified behavior.

Exported graphs contain `metadata.contextdProposal: {id, status: "pending"}`.
The context consumer rejects that marker before validation or source selection.
It is a declarative boundary, not an authenticated approval mechanism; editing a
flag cannot demonstrate that owner review occurred.

The canonical owner reviews the exact proposal and source snapshots, rechecks
live revision/source preconditions, applies separately authorized additions and
produces the accepted graph. The owner records an approved marker after that
review/apply. Then use the existing [OES consumer integration](oes-integration.md)
to build agent context from a graph inside the active workspace.

Authoring accepts explicitly selected code and documentation sources. Consumption
requires governed workspace documents already captured by Synapse; code files or
external snapshots do not automatically qualify. Any owner-controlled source
promotion must preserve the applicable source identity, locator and excerpt.

## Export the three authoring skills

```sh
python scripts/export_graph_authoring.py --output /absolute/new-graph-authoring-plugin
```

The installed equivalent is `python -m contextd.export_graph_authoring` with the
same option. The destination must be new and its parent must already exist.
The export creates a local Claude-compatible plugin and three independent Agent
Skills. Each skill contains the native schemas, common contract and portable
validator. The external OES installation remains the ontology/schema authority;
no copy of its domain ontology is maintained by the exporter.

Review before installing into a host. Copy the required directories under
`skills/` to a host-supported skills directory without overwriting existing skills,
or inspect/load the plugin using the host's documented plugin workflow.
Invoke `project-to-graph`, `spec-to-graph` or `docs-to-graph` through that host.
The bare template SKILL.md files are repository sources; export before installation
so their relative resources exist. No personal skill is installed by this command.

## Legacy v1 compatibility

The original [v1 proposal](../templates/graph-authoring/graph-proposal.schema.json),
[identity baseline](../templates/graph-authoring/graph-baseline.schema.json),
[product-software/1 profile](../templates/graph-authoring/product-software.v1.json)
and [v1 contract](../templates/graph-authoring/authoring-contract-v1.md) remain
available for existing proposals. Their structural validator remains read-only;
source locators are inert and `sources_verified` remains false.

Use the existing command without native OES/source/output flags:

```sh
python scripts/cmd_graph_authoring.py \
  --proposal examples/graph-authoring/proposal.json \
  --baseline examples/graph-authoring/baseline.json \
  --workspace default --project order-demo
```

Do not convert by renaming fields. Legacy `supports` is a supported assertion,
not an exact excerpt. Legacy entities have independently scoped claims; OES
BusinessRule and Decision types can themselves be Claim subtypes. Legacy relation
signature alternatives also cannot be flattened into a larger endpoint cross
product. A future migration needs an explicit OES template and reviewed mapping.

## Verification and remaining scope

```sh
python scripts/test_graph_authoring.py -v
OES_CLI=/absolute/path/to/oes/bin/oes.mjs python scripts/test_graph_authoring_oes.py -v
python scripts/test_graph_projection.py
python scripts/test_graph_projection_integration.py
```

The native suite invokes real OES, validates CLI import/export and independent
skill bundles, rejects paraphrased excerpts and source drift, preserves baseline
records, tests review-state separation, checks retained bytes after live files
change and exercises the consumer's pending-marker boundary. CI uses Node.js 20
and a pinned OES commit with both Python 3.10 and 3.12.

Agent extraction quality, semantic entailment, authenticated owner review,
owner-specific baseline/apply adapters and better final agent outcomes still
need separate evaluation. Graph size, deterministic hashes and successful checks
do not by themselves demonstrate reduced review effort or token savings.
