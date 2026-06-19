# Runbook: Golden Eval Regression

## Symptoms

- `contextd eval --golden --workspace default` exits non-zero.
- A fixture reports missing expected docs, unexpected forbidden docs, missing categories, missing gaps, or policy mismatch.

## Triage

1. Run the failing task with `contextd explain "{task}" --format json`.
2. Compare `selection_trace.selected_docs` and `selection_trace.dropped_docs` with the fixture expectations.
3. Check whether a pack `retrieval-map.md` row changed, a keyword stopped matching, or a category budget dropped the expected doc.
4. Open `governance_report` if the fixture has `policy_expectation`.
5. Confirm whether the fixture represents product truth or an outdated expectation.

## Common Fixes

- Update pack keywords or retrieval-map paths when deterministic context should still include the doc.
- Add a more specific runbook, requirement, product, design, or quality evidence doc when the task needs non-code context.
- Change the fixture only when the desired retrieval behavior intentionally changed.
- Keep eval outputs under `.contextd/runs/`; do not commit generated evaluation reports as workspace knowledge.

## Stop Conditions

Do not accept a golden regression because advisory search still finds the doc. Golden eval measures deterministic context selection, and advisory search is not allowed to override it.
