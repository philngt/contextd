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
- `packs`: optional pack override for this fixture
- `expected_docs`: path globs that must be selected
- `expected_categories`: categories that must appear
- `forbidden_docs`: path globs that must not be selected
- `expected_gaps`: substrings that must appear in gaps
- `policy_expectation`: expected governance status, usually `ok`

## CLI

```bash
contextd eval --golden --workspace default --format json
contextd eval --golden --workspace default --format text --output .contextd/runs/eval.txt
```

Eval builds each task context with materialization disabled, runs policy checks through the normal artifact path, then emits `contextd_evaluation_report.v1`.

Result files are runtime artifacts. Keep them under `.contextd/runs/` or another ignored path, not in workspace knowledge.

## Interpreting Failures

- Missing expected docs usually means retrieval-map, keywords, or category budgeting drifted.
- Forbidden docs selected usually means a path rule is too broad or safety filtering is incomplete.
- Policy expectation mismatch means the context may be valid structurally but violates workspace governance.
- Unexpected gaps mean either the fixture should accept the gap or the workspace/pack source is missing required docs.
