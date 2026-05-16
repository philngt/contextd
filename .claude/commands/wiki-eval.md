# Wiki Eval

Aggregate trace JSON từ nhiều run dưới `{project_dir}/.claude/runs/` → 1 báo cáo Markdown đo **hiệu quả wiki**: coverage, hallucination rate, top knowledge gaps, plan-reviewer block rate, violation hotspots.

> One-shot: 1 lệnh → 1 file Markdown trong `{ws}/reports/`. Read-only — KHÔNG sửa runs/.
> Reference: [observability.md](../../agents/pipeline/observability.md), [run-trace.schema.json](../../templates/run-trace.schema.json).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `--out` | optional | Đường dẫn output. Default: `{ws}/reports/wiki-eval-{YYYY-MM-DD}.md`. Cùng ngày đã có file → suffix `-{HHMMSS}`. |
| `--since` | optional | Filter runs có `ts_start` ≥ ngày này (YYYY-MM-DD). Default: tất cả. |
| `--top` | optional | Top-N cho gap/violation/block ranking. Default: 5. |

---

## Bước 0 — Workspace check

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir` (= `project_dir`), `workspace_active`, `effective_wiki_root`, `{ws}`. Đồng thời:

- Validate `{project_dir}/.claude/runs/` tồn tại. Nếu không → STOP `No runs found. Chạy /use-wiki ít nhất 1 lần trước.`.

---

## Bước 1 — Discover runs

Glob `{project_dir}/.claude/runs/*/`. Mỗi sub-dir = 1 run. Lưu danh sách `run_ids`.

Với mỗi run:
1. Đọc `run.json` (nếu có) — lấy `ts_start`, `user_task`, `workspace_at_run`, `stages_completed`.
2. Filter:
   - **Workspace lock**: bỏ qua run có `workspace_at_run != workspace_active` (KHÔNG leak cross-workspace metric).
   - **Date filter**: nếu `--since` có → bỏ run có `ts_start < since`.
3. Đọc các file stage có (`01-planner.json`, `02-context.json`, `03-plan-review.json`, `04-builder.json`, `05-review.json`). Stage thiếu → bỏ qua field tương ứng, không fail.

Nếu danh sách run sau filter = 0 → STOP `No runs match filter (workspace={ws}, since={since})`.

---

## Bước 2 — Compute metrics

### 2.1 Pipeline health

| Metric | Source | Formula |
|--------|--------|---------|
| Total runs | count run_ids đã filter | n |
| Complete runs | `stages_completed.length == 5` | count |
| Plan-block rate | `03-plan-review.verdict == "BLOCK"` | block / total |
| Final-violations rate | `05-review.verdict == "VIOLATIONS"` | viol / total |

### 2.2 Hallucination

| Metric | Source | Formula |
|--------|--------|---------|
| Planner hallucination rate | `01-planner.unverified_count > 0` | có / total |
| Builder hallucination rate | `05-review.hallucination_count > 0` | có / total |
| Top hallucinated patterns | flatten `01-planner.patterns_verified` where `exists==false` | top-N theo name |
| Top hallucinated refs | flatten `05-review.hallucinated_refs[].ref` | top-N |

### 2.3 Knowledge gaps

| Metric | Source | Formula |
|--------|--------|---------|
| Avg gaps per run | sum `02-context.gap_count` / total | mean |
| Top missing files | flatten `02-context.gaps[].missing` | top-N |
| Blocking gap rate | runs có `gap.blocking_hint == true` | có / total |

### 2.4 Plan-review issues

| Metric | Source | Formula |
|--------|--------|---------|
| Top BLOCK categories | flatten `03-plan-review.issues[]` (severity=blocking) by `category` | top-N |
| Top warnings | flatten `03-plan-review.warnings[]` by category | top-N |

### 2.5 Code violations

| Metric | Source | Formula |
|--------|--------|---------|
| Avg violations per run | sum `05-review.violation_count` / total | mean |
| Top violation rules | flatten `05-review.violations[].rule` | top-N |
| Blocking violation rate | runs có violation severity=blocking | có / total |

### 2.6 Context utilization

| Metric | Source | Formula |
|--------|--------|---------|
| Mean docs retrieved | mean `02-context.file_count` | mean |
| Mean docs used | mean `04-builder.used_docs.length` | mean |
| Utilization ratio | mean (used / retrieved) | mean |

Nếu `04-builder.json` thiếu thì utilization ratio = `n/a`.

---

## Bước 3 — Cross-link evidence

Với mỗi entry trong **Top missing files** (Bước 2.3):

1. Glob `{ws}/evidence/sources/*/source.yaml`.
2. Đọc để tìm evidence nào có thể fill gap (heuristic: `label` chứa keyword của missing file, hoặc `proposals` mention).
3. Nếu match → ghi `evid_id` + `state` (analyzed/qa_done/applied) vào row.

Output bảng "Top Gaps" có thêm cột "Evidence available" → user biết gọi `/evidence-apply` để vá.

---

## Bước 4 — Render report

Output Markdown vào path từ `--out` (default `{ws}/reports/wiki-eval-{YYYY-MM-DD}.md`):

```md
# Wiki Eval — {workspace}

Generated: {ISO datetime}
Runs analyzed: {N} (since {since or "all"})

---

## 1. Pipeline Health

| Metric | Value |
|--------|-------|
| Total runs | {n} |
| Complete runs (5/5 stages) | {n} ({pct}%) |
| Plan-block rate | {pct}% |
| Final-violations rate | {pct}% |

---

## 2. Hallucination

| Metric | Value |
|--------|-------|
| Planner hallucination rate | {pct}% |
| Builder hallucination rate | {pct}% |

### Top hallucinated patterns (planner)
| # | Pattern | Times | Suggested action |
|---|---------|-------|------------------|
| 1 | {name} | {n} | Bổ sung `{ws}/platform/patterns/{name}.md` hoặc rename pattern trong intent |

### Top hallucinated refs (builder)
| # | Ref | Times | Found in stage |
|---|-----|-------|----------------|

---

## 3. Knowledge Gaps

| Metric | Value |
|--------|-------|
| Avg gaps / run | {mean} |
| Blocking gap rate | {pct}% |

### Top missing files
| # | File | Times | Evidence available |
|---|------|-------|--------------------|
| 1 | {path} | {n} | {evid-id (state) or "(none)"} |

---

## 4. Plan-Review Issues

### Top BLOCK categories
| # | Category | Times |
|---|----------|-------|

### Top warnings
| # | Category | Times |
|---|----------|-------|

---

## 5. Code Violations

| Metric | Value |
|--------|-------|
| Avg violations / run | {mean} |
| Blocking violation rate | {pct}% |

### Top violation rules
| # | Rule | Times | Source file |
|---|------|-------|-------------|

---

## 6. Context Utilization

| Metric | Value |
|--------|-------|
| Mean docs retrieved | {mean} |
| Mean docs used | {mean} |
| Utilization ratio | {pct}% |

---

## 7. Recommended Actions

(Auto-generated heuristic)

- {Top gap với evidence available} → `/evidence-apply {evid-id}`
- {Top hallucinated pattern} → bổ sung wiki hoặc fix `patterns-index.md`
- {Top BLOCK category = component-uncovered} → bổ sung task-to-docs-map.md
- {Utilization ratio < 60%} → review context-filter ranking, có thể retrieve quá nhiều file thừa
- {Blocking violation rate > 20%} → builder không follow contract — review prompt-template hoặc thêm validator rule

---

## 8. Run List

| Run ID | Date | Task | Stages | Final Verdict |
|--------|------|------|--------|---------------|
| {run_id} | {date} | {task[:60]} | {n}/5 | {APPROVED/BLOCKED/VIOLATIONS/INCOMPLETE} |
```

---

## Bước 5 — Confirm

In ra:
```
✓ Wiki eval written: {path}
  Runs analyzed: {N}
  Top gap: {top_gap_name} ({n} times)
  Plan-block rate: {pct}%
```

Mở file để user review.

---

## Hard rules

- Read-only: KHÔNG sửa file trong `runs/` hoặc trong `{ws}/`.
- Workspace lock: chỉ aggregate run có `workspace_at_run == workspace_active`. KHÔNG mix workspace.
- Trace file lỗi format JSON → log warning ở section cuối "Parse errors", **không fail toàn bộ command**.
- KHÔNG gửi metrics ra ngoài `project_dir` hay `{ws}/reports/`.
- Output là Markdown thuần, KHÔNG embed HTML/JS.
