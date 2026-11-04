# Native OES authoring fixture

This synthetic refund-workflow example exercises the actual native authoring
handoff. The owner baseline already contains `service:refund-worker`, a Source,
an Evidence record and a `documentedIn` assertion. The complete candidate adds
one proposed BusinessRule, one exact Evidence span and one `implementsRule`
assertion marked `hypothesis`.

The source declares a proposed policy. Successful validation does not claim that
the service implements it in production.

| File | Purpose |
|---|---|
| `baseline.json` | Complete synthetic owner graph at `synthetic-owner-revision-1`, with a reserved retired ID. |
| `candidate.graph.json` | Native `oes.graph/v1` snapshot with a pending proposal marker. |
| `proposal.json` | Native v2 review envelope containing that same candidate. |
| `sources/rules/refund-receipts.md` | Full hashed source; inventory at L14 and proposed policy at L15. |

## Validate the supplied proposal

Run from the contextd repository root with Python/jsonschema and Node.js 20+:

```sh
OES_CLI=/absolute/path/to/oes/bin/oes.mjs

python scripts/cmd_graph_authoring.py \
  --proposal examples/graph-authoring/oes-native/proposal.json \
  --baseline examples/graph-authoring/oes-native/baseline.json \
  --workspace default --project refund-demo \
  --source-root examples/graph-authoring/oes-native/sources \
  --oes-cli "$OES_CLI"
```

The report should have `valid: true`, `checked: 2`, `skipped: 0`, two added nodes
and one added edge. `sources_verified` refers to bytes and excerpts;
`live_baseline_verified`, `apply_supported` and `execution_authorized` remain false.

## Import a graph and export checked pending files

```sh
mkdir -p .contextd/graph-authoring

python scripts/cmd_graph_authoring.py \
  --graph examples/graph-authoring/oes-native/candidate.graph.json \
  --baseline examples/graph-authoring/oes-native/baseline.json \
  --workspace default --project refund-demo \
  --proposal-id proposal:refund-receipts \
  --reviewed 'Complete supplied synthetic specification and owner baseline.' \
  --not-reviewed 'Runtime implementation and production behavior.' \
  --source-root examples/graph-authoring/oes-native/sources \
  --oes-cli "$OES_CLI" \
  --output-proposal .contextd/graph-authoring/refund-proposal.v2.json \
  --output-graph .contextd/graph-authoring/refund-candidate.graph.json

node "$OES_CLI" check-graph .contextd/graph-authoring/refund-candidate.graph.json \
  --with-evidence --require-hash --warnings-as-errors --json \
  --source-root examples/graph-authoring/oes-native/sources
```

Outputs must be new files. They carry `metadata.contextdProposal.status: pending`
and remain review candidates even after the standalone OES check passes. contextd
rejects this pending marker when asked to consume the graph. The canonical owner
must separately review/apply the additions and issue the admitted snapshot.

The source URI is unchanged by import/export. For later context consumption,
the owner must place or map it to governed knowledge inside the active workspace
while preserving its locator and byte identity. No approval or source promotion
is performed by this example.

See the [authoring guide](../../../docs/graph-authoring.md) for the complete v2
contract, legacy compatibility and limitations. Automated checks are in
`scripts/test_graph_authoring_oes.py`.
