# Context for a separate application

This runnable example uses an application checkout and its own knowledge root.
It does not load contextd's default knowledge workspace. All application facts
are synthetic.

The project config selects the `payments` workspace under `../knowledge`.
Relative knowledge roots resolve from the project directory, including when the
command starts in `project/src`.

## Run the same task without and with graph evidence

Install contextd using the repository's installation instructions and make an
OES checkout with `check-graph --with-evidence` available. From the contextd
checkout, enter the example application:

```bash
cd examples/external-project/project/src
contextd explain "add idempotency to kafka consumer" --json
```

The ordinary implementation routes consider the generic logging pattern, but it
has no substantive match for this task. Expected results are zero
`referenced_docs`, `coverage.status: "no_match"`, and a `knowledge-coverage` gap
beginning `No task-specific document matched`. The workspace profile remains
available as static guidance.

Supply the graph, using an absolute path to your OES CLI:

```bash
contextd context "add idempotency to kafka consumer" \
  --oes-graph workspaces/payments/ontology/delivery-policy.graph.json \
  --oes-cli /absolute/path/to/oes/bin/oes.mjs \
  --json
```

The graph connects a service labeled `Kafka payment consumer` to a declared
idempotency rule. The relation cites the exact three decision lines in
`decisions/delivery-policy.md`, including the source's SHA-256 hash. The source
uses the application's delivery terminology rather than repeating the task's
keywords. It is outside the ordinary implementation routes and becomes selected
through this graph relation.

contextd runs the real OES structural and evidence checks against captured
source bytes before accepting this route. Expected results are:

- `coverage.status: "evidence_match"` and `coverage.graph.status: "matched"`.
- One selected document, `workspaces/payments/decisions/delivery-policy.md`.
- `oes.validation` with structural and evidence checks passed, one evidence item
  checked, and zero skipped.
- Citation identifiers, full excerpt, source locator, and graph/source hashes in
  the task JSON and rendered agent context.

Generated files are under the example **application's** `.contextd/context/`,
including its `packs/` directory, even though the command ran in `project/src`. Add
`--preview` to the context command to inspect the artifact without writing it.

## Interpret the limits

`coverage.complete` is `false` in both runs. A matching route establishes what
support was retrieved; it does not prove the task is fully answerable, the graph
is complete, or the application implements the policy. The first run describes
a limitation of its configured retrieval routes, not absence of relevant
knowledge from every file. A valid supplied graph with no matching evidenced
assertion produces a separate `oes-coverage` gap scoped to that graph.

## Reproduce the integration checks

From the contextd checkout:

```bash
OES_CLI=/absolute/path/to/oes/bin/oes.mjs \
  python scripts/test_task_coverage.py ExternalProjectCoverageTests
```

The tests copy this example into a temporary directory, invoke contextd from the
application's nested source directory, run the real OES CLI, and inspect both
the emitted JSON and compiled agent pack. They also check a valid graph without
matching routes and a graph whose evidence is omitted by selection budgets.
