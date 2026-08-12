# Raw — OKF standardization of QA templates (PR #3 diff excerpt)

Source: `git diff upstream/main...feat/okf-standardization`, filtered to the three evidence QA templates. This is the change under test: QA templates with OKF frontmatter must not break the `/evidence-qa` pipeline.

## templates/evidence-qa-answers.md

```diff
+---
+type: Evidence
+title: "Q&A Answers — Batch {N}"
+description: "Append-only answers cho batch {N} của evidence {evid-id}"
+generated: { by: process:evidence-qa, at: {ISO timestamp} }
+---
+
 # Q&A Answers — Batch {N}
```

Pipeline usage (evidence-qa.md#L107): render as `batch-{N}-questions.md` (question-only state) and `batch-{N}-answers.md` (append answers under `## q-XXX`).

## templates/evidence-qa-recommendations.md

```diff
+---
+type: Evidence
+title: "QA Recommendations — {evid-id}"
+description: "QA recommendations cho evidence {evid-id} — read-only trong QA session"
+generated: { by: process:evidence-qa, at: {ISO timestamp} }
+---
+
 # QA Recommendations — {evid-id}
```

Pipeline usage (code-analysis-prompts-code.md#L481): C8 QA Recommender output schema cho `qa/{id}/recommendations.md` khi `source_type=code`.

## templates/evidence-pending-external.md

```diff
+---
+type: Evidence
+title: "Pending External — {evid-id}"
+description: "Câu hỏi đang chờ expert trả lời cho evidence {evid-id}"
+generated: { by: process:evidence-qa, at: {ISO timestamp} }
+---
+
 # Pending External — {evid-id}
```

Pipeline usage (evidence-qa.md#L184): tạo/append `qa/{id}/pending-external.md` khi ≥1 question `awaiting_external` (I-7 lifecycle).

## Related change

`scripts/lint-wiki.py` — OKF checks exclude `evidence/` subtree (runtime artifacts không phải concept files). Test: `test_okf_skips_evidence_runtime_artifacts`.
