# OES → contextd: select documents with evidence

[OES](https://github.com/philngt/oes) is the ontology and evidence layer of the
contextd ecosystem. It owns semantic templates, typed assertions, provenance
and graph/evidence validation. contextd consumes those artifacts to build
task-specific agent context within one workspace.

This integration is an opt-in input to `context`, `task-context` and `explain`.
It uses the existing document ranking, category budgets, lifecycle metadata,
source hashes and Markdown pack output. A normal build without `--oes-graph`
has no Node.js or OES dependency.

For a project outside contextd's own default workspace, start with the
[separate payment application](../examples/external-project/README.md). It
demonstrates a missing route and a successful evidence route for the same task.

## Runnable example

Use Python 3.10+ and Node.js 20+. These commands assume you are in a source
checkout of contextd and clone OES beside it. OES must support `check-graph
--with-evidence --json`; the integration tests pin OES commit
`4ca3f62432099091ecd6a109c053bf83292534c0`.

```bash
python3 -m pip install -e .
git clone https://github.com/philngt/oes.git ../oes

# Inspect both graph structure and the exact cited source bytes.
node ../oes/bin/oes.mjs check-graph \
  workspaces/default/ontology/consumer-recovery.graph.json \
  --with-evidence --source-root workspaces/default \
  --require-hash --warnings-as-errors --json

# Baseline: the ordinary task route does not include the decision below.
contextd context "Investigate ingest-worker lost writes" --preview

# Add ontology-based routing and keep the output read-only.
contextd context "Investigate ingest-worker lost writes" \
  --oes-graph workspaces/default/ontology/consumer-recovery.graph.json \
  --oes-cli ../oes/bin/oes.mjs --preview

# Inspect selection scores, citations, budget drops and validation status.
contextd explain "Investigate ingest-worker lost writes" \
  --oes-graph workspaces/default/ontology/consumer-recovery.graph.json \
  --oes-cli ../oes/bin/oes.mjs --text
```

The bundled `.contextd/config.json` selects the `default` workspace. The example
is synthetic and intentionally small:

| Artifact | Purpose |
|---|---|
| [`consumer-recovery.graph.json`](../workspaces/default/ontology/consumer-recovery.graph.json) | A `Service` with ID `ingest-worker` implements a `BusinessRule`, supported by a local `Evidence` node. |
| [`consumer-write-recovery.md`](../workspaces/default/decisions/consumer-write-recovery.md) | An accepted example decision requiring persistence before acknowledgement and an observable recovery path. |
| `persist-before-ack-evidence` | Exact quotation of lines `L22-L23` in that decision, bound to the source's SHA-256. |

The source calls the service the “telemetry ingestion worker”; `ingest-worker`
is its graph ID. The graph makes that identity usable for retrieval without
requiring the document to repeat the ID. In the OES-enabled output, find:

- `referenced_docs[].path` equal to
  `workspaces/default/decisions/consumer-write-recovery.md`;
- that document's `oes_evidence`, including edge `worker-implements-recovery`,
  relation `implementsRule`, status `asserted` and evidence
  `persist-before-ack-evidence`;
- `oes.validation` showing structural and evidence checks passed with zero
  skipped evidence checks;
- the same citation in the document's rendered `content` and, when materialized,
  in the Markdown pack consumed by the agent.

Omit `--preview` to write the existing `.contextd/context/current-task.json`,
`current-task.md`, `synapse.json` and content-addressed `packs/*.md` artifacts.
The source graph and workspace documents are not modified by the build.

## What happens during the build

1. contextd resolves the active workspace and takes its existing governed
   source snapshot.
2. It checks the selected graph's workspace identity and local source paths.
   The graph bytes and required retained source bytes are placed in a temporary
   validation snapshot.
3. It invokes the configured OES CLI with `check-graph --with-evidence
   --warnings-as-errors --json` against that snapshot. A failed or incomplete
   check stops the requested build before materialization.
4. Task keywords match semantic node IDs or their `label`, `name`, `title`,
   `statement` and `summary` fields. Source URIs and evidence excerpts are not
   matching seeds. Incident edges one hop from matching nodes route the task
   to the documents cited by their Evidence nodes.
5. Those documents enter the ordinary ranking pipeline. A document receives
   one bounded OES score contribution, even if many assertions cite it;
   existing category limits and the seven-document limit still apply.
6. The compiler keeps citation metadata and appends its rendered form to the
   selected document. This makes evidence visible to agent adapters and
   includes it in token estimates and context-pack identity.
7. It reports the support actually selected. No category score can make an
   unrelated document eligible. Coverage and actionable gaps enter both the
   task artifact and compiled pack, and are bound to its identity and budget.

The manual precheck is useful for inspecting the graph independently. contextd
always revalidates the exact snapshot used for the build; it does not trust a
previous command's exit status or an unbound “validated” flag in JSON.

## Coverage and Missing Routes

`coverage.status` is `evidence_match` when selected context contains checked
evidence for a matched graph assertion. Without that route it may instead be a
`declared_route`, `lexical_match`, `no_match` or `unassessed` query. General static
guidance does not count as task-specific support. A no-support build may select
zero referenced documents and emits a `knowledge-coverage` gap.

The independent `coverage.graph.status` is `matched`, `no_match`, `not_selected`
or `not_requested`. A valid supplied graph with no evidenced match emits an
`oes-coverage` gap scoped to that graph. Matching assertions omitted by document
budgets yield `not_selected`, rather than pretending the assertions were absent.
The report preserves matched node and edge IDs in either case.

`coverage.complete` is always false. Matched literal terms are retrieval signals,
and unmatched terms can have aliases. Neither a small graph nor an empty gap
list establishes complete knowledge or semantic entailment. These distinctions
also appear in `explain --text` and the actual agent context pack.

## Supported input contract

| Field/input | Contract |
|---|---|
| `--oes-graph` | A JSON graph inside the active workspace. Relative paths resolve from the knowledge root. |
| `--oes-cli` | Trusted local OES JavaScript entrypoint, such as `/path/to/oes/bin/oes.mjs`. Relative paths resolve from the invocation directory; when omitted, contextd uses `oes` on `PATH`. |
| `--oes-timeout` | Positive validator timeout in seconds; default 30. |
| Graph header | `apiVersion: "oes.graph/v1"`, a string naming an installed OES template, nonempty `metadata.id` and `metadata.workspace` matching the active workspace. `metadata.ontologyVersion`, when supplied, is a string. |
| `Source.properties.uri` | Literal path relative to the active workspace, for example `decisions/consumer-write-recovery.md`. |
| `Source.properties.sha256` | Optional expected SHA-256 of the complete raw source bytes. If present it must match. The demo supplies it. |
| Evidence | Exact core `Evidence` node with `sourceId`, a one-based inclusive `Lx` or `Lx-Ly` locator and a nonempty excerpt equal to the complete selected lines. OES normalizes line endings for the excerpt comparison. |
| Assertion evidence | `evidenceIds`, or the Evidence target of a `supportedBy` edge when `evidenceIds` is omitted. Assertions without usable evidence cannot route a document. |

The adapter accepts graphs up to 5 MiB and a combined source snapshot up to
50 MiB. OES also applies its 5 MiB limit to each local evidence source.

Only files already admitted by the workspace's Synapse source scan can be
referenced. Current governed sources include Markdown and contract JSON/YAML;
raw `evidence/sources/` payloads, runtime output, hidden files and excluded
reports cannot enter through this adapter. Absolute paths, traversal, encoded
paths, URLs, another workspace and symlink escapes are rejected. Evidence
checks do not fetch remote sources.

Output `source_path` values are knowledge-root-relative, matching contextd's
existing citation format. Output hashes describe the exact retained graph and
source bytes; random temporary paths are not part of artifact identity.
The demo source is pinned to LF line endings through `.gitattributes`, so its
stored SHA-256 also survives a Windows checkout with automatic EOL conversion.

See the normative [OES context contract](../workspaces/default/platform/contracts/oes-context.md)
and [task-context schema](../templates/task-context.schema.json).

## Trust and lifecycle boundaries

There are three distinct results:

| Check | What it establishes |
|---|---|
| OES structural validation | The graph satisfies its selected ontology contract, including references and supported constraints. |
| OES evidence validation | A quotation matches the specified local lines; an expected source hash, when supplied, matches the full bytes. |
| contextd selection | Those assertions made a governed document relevant enough to enter the existing context ranking and budgets. |

These checks do not prove a quotation entails an assertion, a speaker was
correct, a hypothesis has been verified or a runtime operation occurred.
Assertion status, claim status, confidence, time bounds and relation properties
remain provenance supplied by the graph. `hypothesis` and `inferred` labels
remain visible, as do rejected or superseded claim states.

OES graph input does not replace Synapse or automatically promote contextd
[graph-authoring proposals](graph-authoring.md) into canonical knowledge.
New authoring proposals embed the same `oes.graph/v1` model and delegate ontology
and source checks to OES. Their contextd envelope carries review workflow and
owner revision data, not a separate ontology. The exported graph retains
`metadata.contextdProposal.status: pending`; consumption rejects this marker and
malformed markers. Approval is an external owner responsibility, and a marker is
a declaration rather than authenticated approval proof. Legacy v1 proposals are
explicitly separate compatibility inputs and cannot be silently converted.
Source documents remain authoritative inputs; the resulting context is a
derived artifact. No claim approval, workspace write, graph merge or inference
step is performed by this integration.

## Verification

Install the test extra and point the dedicated suite at a real OES checkout:

```bash
python3 -m pip install -e ".[test]"
OES_CLI="$(pwd)/../oes/bin/oes.mjs" python3 scripts/test_oes_context.py
OES_CLI="$(pwd)/../oes/bin/oes.mjs" python3 scripts/test_task_coverage.py
OES_CLI="$(pwd)/../oes/bin/oes.mjs" python3 scripts/test_graph_authoring_oes.py
```

The suite compares baseline and graph-assisted selection, runs the real OES
validator, checks JSON and both Markdown outputs, exercises invalid graphs and
source evidence, and verifies workspace boundaries, determinism, source
snapshot coherence and budget handling. CI checks out the pinned OES commit
and runs this suite with Node.js 20 on the supported Python test matrix.

The suite reports a skip when no local OES checkout is available and `OES_CLI`
is unset. CI supplies the path explicitly, so a missing validator is a test
failure there. It does not substitute a fake validator for this integration.
