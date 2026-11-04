# Evaluation

contextd evaluation measures context selection quality with golden tasks. It does not run agents, generate code, or judge implementation output.

## Golden Task Fixtures

Fixtures live under:

```text
workspaces/{workspace}/eval/golden-tasks/*.json
```

Template: `templates/golden-task.json`.

Fields:

- `id`: stable fixture id
- `task`: task prompt to classify and retrieve context for
- `workspace`: optional workspace override
- `as_of`: required ISO evaluation date for deterministic lifecycle/freshness
- `packs`: optional pack override for this fixture; an explicit `[]` disables inherited packs
- `expected_docs`: path globs that must be selected
- `expected_categories`: categories that must appear
- `forbidden_docs`: path globs that must not be selected
- `expected_gaps`: substrings that must appear in gaps
- `expected_referenced_doc_count`: optional exact number of retrieved documents,
  including `0` when a fixture must reject unrelated filler
- `policy_expectation`: expected governance status, usually `ok`

## CLI

```bash
contextd eval --golden --workspace default --format json
contextd eval --golden --workspace default --format text --output .contextd/runs/eval.txt
contextd eval --golden --workspace default --as-of 2026-08-20 --format json
```

Eval builds each task context with materialization disabled, runs policy checks through the normal artifact path, then emits `contextd_evaluation_report.v1`.

Each fixture should pin `as_of`. `--as-of` is a migration fallback for older
fixtures that do not yet contain the field. An invalid or missing effective
date is a load error rather than silently using the wall-clock date.

Result files are runtime artifacts. Keep them under `.contextd/runs/` or another ignored path, not in workspace knowledge.

## Interpreting Failures

- Missing expected docs usually means retrieval-map, keywords, or category budgeting drifted.
- Forbidden docs selected usually means a path rule is too broad or safety filtering is incomplete.
- Policy expectation mismatch means the context may be valid structurally but violates workspace governance.
- A missing expected gap means the runtime did not report the specific limitation
  the fixture requires. An empty `expected_gaps` array makes no assertion about
  absence of gaps. The JSON report includes actual `gaps` and `coverage` for review.

## Tasks without matching support

The `kafka-idempotency-no-task-support` fixture reproduces a task for which the
default workspace's configured retrieval routes supply no matching task-specific
documents. It requires zero retrieved documents and a `knowledge-coverage` gap
containing `No task-specific document matched`. Engine and workspace baseline
guidance can still be included in `static_context`; it does not satisfy this
task-specific expectation.

This is an assertion about the bounded retrieval result, not proof that the
whole corpus lacks the requested knowledge. `coverage.complete` remains `false`.
Unmatched literal terms are diagnostic: synonyms, omitted routes, an incomplete
graph, and selection budgets can all limit a match. When an OES graph is supplied,
its graph coverage is reported separately from ordinary document retrieval.

Use a negative fixture beside positive tasks. A builder that selects nothing for
every query should fail the positive fixtures; a builder that fills every budget
with unrelated documents should fail the negative fixture. The
[external-project example](../examples/external-project/README.md) demonstrates
the same query gaining an exact source citation through a validated OES route in
a separate knowledge workspace.
