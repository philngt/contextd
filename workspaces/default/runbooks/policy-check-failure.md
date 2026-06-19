# Runbook: Policy Check Failure

## Symptoms

- `contextd policy-check "task"` exits `1` or `2`.
- `contextd context ... --format json` includes `governance_report.status=error` or `warning`.
- `contextd eval --golden` fails because `policy_expectation` does not match.

## Triage

1. Run `contextd explain "task" --format json` and inspect selected docs, gaps, and `budget_report`.
2. Open the policy source named in `governance_report.violations[].source`.
3. Check whether the rule is matching the intended `intent.type`, `workstream`, or `components`.
4. Verify required docs or categories exist in the active workspace and are reachable through deterministic retrieval.
5. If the policy denies a path/category, confirm the selected doc is genuinely unsafe or irrelevant before changing the rule.

## Common Fixes

- Add or repair the missing contract, requirement, runbook, or quality evidence in the active workspace.
- Tighten pack keywords so the right component and retrieval-map row are selected.
- Update an over-broad policy glob such as `*contract*` into a workspace-relative path.
- Adjust `deny.max_selected_docs` or `deny.max_estimated_tokens` only after confirming the context budget is intentionally larger.

## Stop Conditions

Do not suppress a policy error by deleting the rule unless the rule is obsolete. If the policy is correct and the workspace lacks required knowledge, treat the missing knowledge as the root cause.
