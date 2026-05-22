# /contextd-trace — Inspect Pipeline Trace

View 1 run cụ thể của pipeline đã chạy (qua `/use-contextd`). Đọc các trace JSON dưới `{project_dir}/.claude/runs/{run_id}/` → render Markdown timeline để debug nhanh.

> Read-only. KHÔNG sửa file run nào.
> Cần HTML viewer (collapsible cards, side-by-side retrieved-vs-used, Mermaid)? Dùng [`/contextd-viz`](contextd-viz.md) — sister command output HTML thay vì Markdown.
> Reference: [observability.md](../../agents/pipeline/observability.md).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `{run_id}` | required | Run ID (vd `2026-05-08-141503-add-rest-endpoint`). Có thể prefix-match nếu duy nhất. |
| `--last` | optional | Thay vì run_id, lấy run mới nhất. `/contextd-trace --last`. |
| `--out` | optional | Nếu có → ghi report ra file thay vì in stdout. |

---

## Bước 0 — Resolve project + run

Theo [workspace-resolution.md Profile C](../../agents/pipeline/workspace-resolution.md#profile-c--project-dir-only-no-workspace-lock). Set: `project_dir`, `runs_dir`. Sau đó resolve `run_id`:

- Nếu `--last` → Glob `runs_dir/*/` sorted theo dirname (run_id chứa timestamp ASC) → lấy cuối.
- Ngược lại: Glob `runs_dir/{run_id}*` → nếu có 1 match → dùng. Nhiều match → STOP, in danh sách. 0 match → STOP.

Set `run_dir = {runs_dir}/{resolved_run_id}/`.

---

## Bước 1 — Read all stages

Đọc các file (skip nếu thiếu):
- `run.json`
- `01-planner.json`
- `02-context.json` (gồm cả plan-review verdict)
- `04-builder.json`
- `05-review.json`

File JSON parse lỗi → ghi vào "Parse errors" section, không fail.

---

## Bước 2 — Render timeline

Output Markdown:

```md
# Wiki Trace — {run_id}

Workspace: {workspace_at_run}
Started: {ts_start}
Ended: {ts_end or "(in progress)"}
Task: {user_task}
Stages completed: {n}/4
Final verdict: {final_verdict}

---

## Stage 1 — Planner

⏱ {ts}  ⌛ {duration_ms}ms

**Intent:**
- type: {intent.type}
- domain: {intent.domain}
- components: {intent.components}
- patterns_needed: {intent.patterns_needed}
- contracts_touched: {intent.contracts_touched}

**Verification:**
| Pattern | Exists | Path |
|---------|--------|------|
| {name} | ✓ / ✗ | {path or "—"} |

**Unverified count:** {n}
{nếu > 0: "⚠ Hallucination detected — context-selector should BLOCK."}

---

## Stage 2 — Context Selector (+ Plan Review)

⏱ {ts}  ⌛ {duration_ms}ms

Context file: `{context_file}`
Docs retrieved: {file_count}
Total chars: {total_chars}

**Verdict:** {APPROVED / BLOCK}

**Referenced Docs:**
| # | Category | Path | Sections |
|---|----------|------|----------|

**Knowledge Gaps:** {gap_count}
| Category | Missing | Blocking? |
|----------|---------|-----------|

**Issues:** {n}
| ID | Category | Severity | Detail | Evidence |
|----|----------|----------|--------|----------|

**Checks summary:**
- Patterns verified: {n}
- Contracts verified: {n}
- Components covered: {list}
- Blocking gaps: {n}
- Conflicts: {n}

---

## Stage 3 — Builder

⏱ {ts}

**Files modified:**
{list}

**Used docs:** {n} / {total from stage 2} ({pct}%)
| Path | Section |
|------|---------|

**Assumptions count:** {n}
**Self-check passed:** {true/false}

---

## Stage 4 — Reviewer

⏱ {ts}  ⌛ {duration_ms}ms

**Verdict:** {APPROVED / VIOLATIONS / INSUFFICIENT_CONTEXT}

**Files reviewed:** {n}

**Violations:** {n}
| ID | Rule | File:Line | Severity | Fix |
|----|------|-----------|----------|-----|

**Hallucinated refs:** {n}
| ID | Ref | Found in | Reason |
|----|-----|----------|--------|

---

## Divergence Analysis

(Auto-heuristic — chỉ render nếu có divergence)

- Planner đề xuất pattern `{X}` nhưng context-selector không retrieve được → check `task-to-docs-map.md` mapping cho component `{Y}`.
- Context-selector APPROVED nhưng final reviewer thấy violations → check builder có ignore Referenced Docs không (xem stage 3 used_docs).
- Builder reference `{Z}` không có trong context → hallucination, có thể wiki thiếu hoặc agent tự nghĩ.

---

## Parse errors

(skip nếu rỗng)
- {file}: {error}
```

Nếu `--out` có → Write file. Ngược lại in stdout.

---

## Bước 3 — Confirm

```
✓ Trace: {run_id}
  Stages: {n}/4  Final: {verdict}
  Issues: {plan_block_issues} block, {warnings} warn
  Violations: {n}  Hallucinations: {n}
```

---

## Hard rules

- Read-only.
- Nếu run_dir không tồn tại → STOP, in danh sách run gần nhất (top 5 sorted desc) để user chọn.
- KHÔNG render content của `current-task.md` — chỉ stats từ trace JSON. (User mở context file riêng nếu muốn.)
- Workspace check: in cảnh báo nếu `run.workspace_at_run != workspace_active` (có thể user đã `/switch-workspace` sau khi run xong).
