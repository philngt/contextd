# Pipeline Observability

## Purpose

Đo và debug **tính hiệu quả của wiki** — không phải đo runtime hiệu năng. 4 câu hỏi cần trả lời được:

1. **Pipeline nào lỗi?** Khi output cuối sai, stage nào divergence?
2. **Agent có hallucinate không?** Có pattern/contract nào agent dùng mà không tồn tại trong wiki?
3. **Wiki còn thiếu gì?** Knowledge gap nào lặp lại nhiều lần qua các task?
4. **Wiki có cải thiện chất lượng?** So sánh output có-wiki vs không-wiki.

Cơ chế: mỗi subagent **output 1 fenced ```json block** ở cuối response. **PostToolUse hook** ([scripts/emit_trace.py](../../scripts/emit_trace.py)) tự động trích block đó và ghi `{cwd}/.claude/runs/{run_id}/{stage}.json`. Subagent KHÔNG dùng Write tool cho trace — code-driven, deterministic, tiết kiệm token.

Builder (main agent, không phải subagent) vẫn tự ghi `04-builder.json` qua Write tool — không có hook cho main agent.

Slash command `/wiki-eval` aggregate runs. Slash command `/wiki-trace` view 1 run cụ thể.

> Đây là **lớp đo lường tách rời** — pipeline chính (`/use-wiki`) vẫn chạy bình thường nếu trace fail. Hook timeout sau 5s, lỗi parse → log stderr, KHÔNG block pipeline.

---

## Run-id convention

`run_id` được sinh bởi `wiki-planner` (Stage 1) ở **đầu pipeline**, format:

```
{YYYY-MM-DD}-{HHMMSS}-{slug}
```

- `slug` = 4-6 từ đầu của `user_task`, lowercase, ký tự không phải `[a-z0-9]` thay bằng `-`, gộp `--` → `-`, trim, max 40 ký tự.
- Ví dụ: `2026-05-07-141503-add-rest-endpoint-admin`

Các stage sau **nhận `run_id` từ caller** (main agent hoặc `/use-wiki` slash command) qua input parameters. KHÔNG sinh lại.

---

## File layout

```
{project_dir}/.claude/runs/{run_id}/
  ├─ run.json              ← roll-up: hook update sau mỗi stage (stages_completed, totals)
  ├─ 01-planner.json       ← hook ghi từ wiki-planner output
  ├─ 02-context.json       ← hook ghi từ wiki-context-selector output
  ├─ 03-plan-review.json   ← hook ghi từ wiki-plan-reviewer output
  ├─ 04-builder.json       ← main agent self-write (no hook for non-Task tools)
  ├─ 05-review.json        ← hook ghi từ wiki-reviewer output
  └─ scorecard.md          ← optional, manual chấm điểm
```

`runs/` là **per-codebase** (`{project_dir}/.claude/runs/`), KHÔNG ghi vào wiki repo. Workspace lock vẫn bắt buộc — mỗi trace chứa `workspace_at_run` để verify.

`.gitignore` của project-root nên thêm `.claude/runs/` (per-machine ephemeral data).

---

## Schema — single source of truth

**[templates/run-trace.schema.json](../../templates/run-trace.schema.json)** định nghĩa toàn bộ shape (common fields + per-stage payload). Doc này chỉ tóm tắt **mục đích & semantic** của từng stage — không lặp lại schema. Khi sửa shape → sửa schema.json, không sửa ở đây.

Common fields (mọi stage): `run_id`, `stage`, `ts`, `workspace_at_run`, `duration_ms` (optional).

Worked example đầy đủ 5 stage cho 1 task: xem 1 run thực tế tại `{project_dir}/.claude/runs/{run_id}/` (sinh bởi `/use-wiki`).

---

## Stage payloads — purpose & key fields

Path tới definition trong schema: `#/oneOf/{n}` (theo thứ tự dưới đây).

### Stage 1 — `01-planner.json` (wiki-planner) → schema oneOf[0]

**Purpose:** Parse user task → intent. Verify patterns/contracts trong `intent.patterns_needed`/`contracts_touched` có thực sự tồn tại trong `{ws}/platform/{patterns,contracts}/`.

**Key fields:** `intent` (full schema xem [task-to-docs-map.md](task-to-docs-map.md)), `patterns_verified[]`, `contracts_verified[]`, `unverified_count`.

**Hallucination gate:** `unverified_count > 0` → wiki-plan-reviewer PHẢI emit `verdict=BLOCK`.

### Stage 2 — `02-context.json` (wiki-context-selector) → schema oneOf[1]

**Purpose:** Map intent → file paths thực tế. Ghi `current-task.md`. Báo cáo gaps.

**Key fields:** `context_file`, `referenced_docs[]` (mỗi entry: `{category, path, sections}`), `gaps[]`, `file_count`, `gap_count`, `total_chars`.

### Stage 3 — `03-plan-review.json` (wiki-plan-reviewer) → schema oneOf[2]

**Purpose:** Gate trước Implementation. BLOCK nếu thiếu pattern/contract, conflict, blocking gap.

**Key fields:** `verdict` (`APPROVED|BLOCK`), `issues[]` (mỗi entry: `{id, category, severity, detail, evidence}`), `checks_summary`.

### Stage 4 — `04-builder.json` (main agent self-write) → schema oneOf[3]

**Purpose:** Main agent tự ghi sau Implementation. KHÔNG có hook (hook chỉ chạy cho `Task` tool — main agent không phải subagent).

**Key fields:** `used_docs[]` (subset của `02-context.referenced_docs` mà builder thực sự reference), `files_modified[]`, `assumptions_count`, `self_check_passed`.

**Context utilization rate:** `len(used_docs) / len(02-context.referenced_docs)`.

`self_check_passed`: builder xác nhận đã chạy "Constraints to check" trong [prompt-template.md](prompt-template.md).

### Stage 5 — `05-review.json` (wiki-reviewer) → schema oneOf[4]

**Purpose:** Soi code thật vs context đã đưa. Phát hiện violation + hallucinated refs.

**Key fields:** `verdict` (`APPROVED|VIOLATIONS|INSUFFICIENT_CONTEXT`), `violations[]`, `hallucinated_refs[]`, `violation_count`, `hallucination_count`.

**Hallucinated ref:** path/pattern xuất hiện trong builder output (vd `## Knowledge Mapping`) NHƯNG không có trong `02-context.referenced_docs`.

### `run.json` (roll-up) → schema oneOf[5]

**Purpose:** Index cho 1 run. Planner ghi khi bắt đầu; `/wiki-trace` cập nhật khi view.

**Key fields:** `ts_start`, `ts_end`, `user_task`, `stages_completed[]`, `final_verdict` (`APPROVED|BLOCKED|VIOLATIONS|INCOMPLETE`), `totals` (counts cho unverified/gaps/violations/hallucinations).

---

## Aggregation rules cho `/wiki-eval`

Đọc tất cả `{project_dir}/.claude/runs/*/`. Lọc theo `workspace_at_run == workspace_active` (workspace isolation).

Metrics output:

| Metric | Source | Formula |
|--------|--------|---------|
| Run count | dirs trong `.claude/runs/` | count |
| Plan-block rate | `03-plan-review.verdict == BLOCK` | block / total |
| Hallucination rate (planner) | `01-planner.unverified_count > 0` | có / total |
| Hallucination rate (builder) | `05-review.hallucination_count > 0` | có / total |
| Avg gaps per run | sum `02-context.gap_count` / total | mean |
| Top gaps | flatten `02-context.gaps[]`, count `missing` | top-N |
| Top BLOCK reasons | flatten `03-plan-review.issues[].category` | top-N |
| Top violation rules | flatten `05-review.violations[].rule` | top-N |
| Context utilization | `04-builder.used_docs.length / 02-context.referenced_docs.length` | mean |

Output: `{ws}/reports/wiki-eval-{YYYY-MM-DD}.md` — markdown bảng.

---

## A/B golden tasks

Golden tasks **per-workspace** — mỗi workspace định nghĩa fixture riêng tại `{ws}/eval/golden-tasks/`. Mỗi task có rubric trong `expected.md`. Lý do: pattern/contract của workspace A không áp dụng cho workspace B → fixture không thể share.

Chạy 2 lần:
- **A — wiki-on**: `/use-wiki` đầy đủ.
- **B — wiki-off**: ghi đè `current-task.md` thành stub trống (`## Referenced Docs: (none)`, `## Knowledge Gaps: all sections missing — wiki-off mode`), rồi gọi builder thẳng.

Sau khi cả A và B chạy xong, copy [templates/task-scorecard.md](../../templates/task-scorecard.md) (skeleton chung của engine), chấm theo 10 tiêu chí. Lưu kết quả vào `{ws}/eval/results/{date}-{task-id}.md`.

Delta `score_A − score_B` = wiki contribution. Nếu delta ≤ 1 (trên thang 30) → wiki không đóng góp đáng kể cho task đó → review wiki.

---

## Hook setup

Trace emit cho 4 subagent (`wiki-planner`, `wiki-context-selector`, `wiki-plan-reviewer`, `wiki-reviewer`) chạy qua **PostToolUse hook** trên tool `Task`. Hook script: [scripts/emit_trace.py](../../scripts/emit_trace.py) (Python 3.9+).

### Trong wiki-template repo (self-test)

`.claude/settings.json` đã có sẵn:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          { "type": "command", "command": "python scripts/emit_trace.py", "timeout": 5 }
        ]
      }
    ]
  }
}
```

Khi user chạy `/use-wiki` từ trong wiki-template, mỗi lần Task tool kết thúc → hook chạy, parse subagent output, ghi trace.

### Trong codebase khác (production usage)

Codebase A có `.claude/wiki.json` trỏ tới wiki-template ở `D:\tool\wiki-template\`. Để bật trace:

1. Sao chép `.claude/settings.json` của wiki-template vào codebase A, đổi command thành **absolute path**:
   ```json
   { "type": "command", "command": "python D:\\tool\\wiki-template\\scripts\\emit_trace.py", "timeout": 5 }
   ```
2. Verify `python` trong PATH (`python --version` ≥ 3.9).
3. Chạy 1 task qua `/use-wiki`. Sau khi Task tool đầu tiên xong → kiểm `{codebase A}/.claude/runs/{run_id}/01-planner.json`.

### Hook payload (tham khảo)

Hook nhận JSON qua stdin với format Claude Code chuẩn:
```json
{
  "tool_name": "Task",
  "tool_input": { "subagent_type": "wiki-planner", "prompt": "..." },
  "tool_response": "...subagent output text...",
  "cwd": "/path/to/codebase"
}
```

Script extract fenced ```json block cuối từ `tool_response`, validate có `run_id` + `stage`, ghi vào `{cwd}/.claude/runs/{run_id}/{stage}.json`. Không match → exit 0 (no-op).

### Disable trace

Comment block `hooks` trong `settings.json` (hoặc xoá file). Pipeline vẫn chạy bình thường, chỉ không có trace data.

---

## Hard rules

- **Trace KHÔNG block pipeline.** Nếu Write file fail, subagent log warning và tiếp tục output bình thường.
- **Trace KHÔNG đọc file ngoài project_dir + effective_wiki_root.** Workspace lock vẫn bắt buộc.
- **Một run = một workspace.** Nếu user `/switch-workspace` giữa pipeline → run abort (out of scope).
- **Run dir append-only** trong session. KHÔNG sửa file đã ghi của stage trước.
- **`/wiki-eval` chỉ đọc**, không sửa runs/.
- **Run ID không leak ra ngoài project_dir** — không gắn vào commit message, không log lên external service.

---

## Related

- [concurrency-notes.md](concurrency-notes.md) — atomic write + advisory lock cho `run.json` (xử lý concurrent hook calls).
- [run-trace.schema.json](../../templates/run-trace.schema.json) — JSONSchema for trace files
- [task-scorecard.md](../../templates/task-scorecard.md) — manual rubric for A/B
- [.claude/commands/wiki-eval.md](../../.claude/commands/wiki-eval.md) — aggregator command (Markdown)
- [.claude/commands/wiki-trace.md](../../.claude/commands/wiki-trace.md) — single-run viewer (Markdown)
- [.claude/commands/wiki-viz.md](../../.claude/commands/wiki-viz.md) — HTML viewer + run browser + live watch
- [PIPELINE-VISUAL.md](PIPELINE-VISUAL.md) — Mermaid diagram giải thích pipeline cho human
- [scripts/render_trace.py](../../scripts/render_trace.py) — Python renderer (stdlib only)
- `{ws}/eval/golden-tasks/README.md` — fixture catalog (per-workspace)
- [multi-agent-pipeline.md](multi-agent-pipeline.md) — pipeline doc, có Stage 6 — Trace
