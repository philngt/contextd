# Multi-Agent Pipeline

## Purpose

Tách công việc của một task wiki-aware ra nhiều agent có vai trò hẹp, thay vì để 1 agent vừa parse intent vừa retrieve context vừa code. Lý do:

- Mỗi subagent có context window riêng → main agent không bị nhiễu.
- Output mỗi stage có schema cố định → dễ audit, dễ resume khi fail.
- Plan-Reviewer chặn sai sót trước khi Builder viết code (rẻ hơn fix sau khi đã có code).

> Đây là **reference document** mô tả vai trò + schema của từng agent. **Flow execution thực tế (cách main agent gọi subagent) định nghĩa trong [.claude/commands/contextd-use.md](../../.claude/commands/contextd-use.md)** — đó là spec sống. Khi conflict, contextd-use.md thắng.

---

## Pipeline (5 stage)

```
User Task
   ↓
[Stage 0] Main agent       → resolve workspace + wiki_root từ <cwd>/.claude/wiki.json
   ↓
[Stage 1] wiki-planner     → parse task → intent JSON
   ↓
[Stage 2] wiki-context-selector → retrieve + slice → ghi current-task.md
   ↓
[Stage 2.5] wiki-plan-reviewer → APPROVED hoặc BLOCK
   ↓
[Stage 3] Main agent (Builder) → đọc current-task.md → code theo prompt-template
   ↓
[Stage 4] wiki-reviewer (optional) → review code đã sinh vs context
   ↓
Final Output
```

**Lưu ý vai trò Builder**: Builder KHÔNG phải subagent độc lập — đó là main agent đóng vai. Lý do: main agent đã có ToolUse permission để Edit/Write code, không cần delegate. Subagent chỉ dùng cho công việc không-code (parse, retrieve, review).

---

## Stage 1 — `wiki-planner`

**Subagent file**: [.claude/agents/wiki-planner.md](../../.claude/agents/wiki-planner.md)

**Input** (từ main agent):
- `user_task`: task gốc của user (nguyên văn)
- `effective_wiki_root`: absolute path tới wiki-template
- `workspace`: tên workspace active
- `config_hint`: nội dung `<cwd>/.claude/wiki.json` (nếu có)

**Job**: Đọc `{ws}/patterns-index.md` + `{ws}/workspace.md`, suy ra patterns/contracts/domain/components cần dùng. KHÔNG đọc file pattern detail, KHÔNG sinh code.

**Output schema**: Intent JSON theo `agents/pipeline/task-to-docs-map.md`:
```json
{
  "workspace": "example-surgery",
  "type": "implement_feature",
  "domain": "surgery",
  "components": ["kafka", "mqtt", "batch"],
  "scope": "surgery-service",
  "patterns_needed": ["kafka-event-processing", "mqtt-routing"],
  "contracts_touched": ["mqtt-topic-contract"],
  "missing_knowledge": []
}
```

Nếu `missing_knowledge` không rỗng → main agent STOP, hỏi user, KHÔNG tự đoán.

---

## Stage 2 — `wiki-context-selector`

**Subagent file**: [.claude/agents/wiki-context-selector.md](../../.claude/agents/wiki-context-selector.md)

**Input** (từ main agent):
- `intent_json`: output của Stage 1
- `effective_wiki_root`
- `project_dir`: cwd hiện tại
- `user_task`: để gắn vào header context file

**Job**: Map intent → file path cụ thể theo [task-to-docs-map.md](task-to-docs-map.md), slice section theo [context-filter.md](context-filter.md), ghi đè `{project_dir}/.claude/context/current-task.md`.

Subagent này có thể rule-based (deterministic lookup) — không cần LLM heavy.

**Output**: 1 dòng confirm `Context written: {path}, {N} docs, {M} gaps`. File `current-task.md` chứa toàn bộ context ranked + sliced.

---

## Stage 2.5 — `wiki-plan-reviewer`

**Subagent file**: [.claude/agents/wiki-plan-reviewer.md](../../.claude/agents/wiki-plan-reviewer.md)

**Input** (từ main agent):
- `intent_json`: output của Stage 1
- `context_file`: path tới `current-task.md` vừa ghi
- `effective_wiki_root`
- `user_task`

**Job**: Chạy 4 check:
1. Pattern và contract Stage 1 nêu có thực sự tồn tại trong workspace không.
2. Context có đủ docs cho mọi component trong intent không.
3. Có conflict nội tại trong context (vd 2 patterns hướng dẫn ngược nhau) không.
4. Có gap blocking trong `## Knowledge Gaps` của context_file không.

**Output**:
- `APPROVED` (có thể kèm `## Warnings` block) → main agent tiếp tục Stage 3.
- `BLOCK` kèm `## Issues` block → main agent STOP pipeline, báo user, KHÔNG tự sửa context.

Đây là gate quan trọng — đẩy issue ra phía trước trước khi tốn token cho Stage 3.

---

## Stage 3 — Main Agent (Builder)

**Không phải subagent.** Main agent đóng vai builder vì cần ToolUse (Edit/Write/Bash) không có ở subagent.

**Input**: `current-task.md` (single source of truth cho session) + user_task.

**Prompt structure**: Dùng [prompt-template.md](prompt-template.md) — fill các slot từ `## Referenced Docs` của `current-task.md`.

**Output format** (bắt buộc):
```
## Understanding
## Knowledge Mapping   ← link tới section trong current-task.md
## Design
## Implementation
## Edge Cases
## Assumptions
```

Mọi quyết định kỹ thuật phải reference được vào 1 entry trong `## Referenced Docs`. Nếu phải vượt ngoài → ghi vào `## Assumptions`.

---

## Stage 4 — `wiki-reviewer` (optional)

**Subagent file**: [.claude/agents/wiki-reviewer.md](../../.claude/agents/wiki-reviewer.md)

**Input** (từ main agent, sau khi đã Edit/Write file):
- `solution_files`: danh sách file vừa sửa
- `context_file`: `current-task.md`
- `effective_wiki_root`

**Job**: So sánh code đã sinh với contracts/patterns/domain rules trong context. Báo violation, KHÔNG tự sửa.

**Output**:
- `APPROVED` → main agent báo user.
- `Violations Found` → main agent append vào `## Violations` section của `current-task.md`, báo user trước khi commit.

**Bỏ qua Stage 4 khi**: task chỉ là `design`/`review` không sinh code, hoặc fix bug 1 dòng quá nhỏ.

---

## Stage 6 — Trace (observability, code-driven)

Mỗi subagent **output 1 fenced ```json block** ở cuối response. **PostToolUse hook** ([scripts/emit_trace.py](../../scripts/emit_trace.py)) tự động trích block đó và ghi `{cwd}/.claude/runs/{run_id}/{stage}.json`. Subagent KHÔNG dùng Write tool cho trace — tiết kiệm token, deterministic. Chi tiết: [observability.md](observability.md).

| Stage | File | Emit mechanism |
|-------|------|----------------|
| 1 | `01-planner.json` | hook trích từ wiki-planner output |
| 2 | `02-context.json` | hook trích từ wiki-context-selector output |
| 2.5 | `03-plan-review.json` | hook trích từ wiki-plan-reviewer output |
| 3 | `04-builder.json` | main agent self-write (Write tool — main agent không qua hook Task tool) |
| 4 | `05-review.json` | hook trích từ wiki-reviewer output |
| roll-up | `run.json` | hook update sau mỗi stage |

Trace **KHÔNG block pipeline**: hook timeout 5s, parse fail → exit 0, log stderr. Trace là lớp đo lường tách rời.

Aggregate qua nhiều run: `/contextd-eval`. View 1 run: `/contextd-trace {run_id}`. Chi tiết: [observability.md](observability.md).

---

## When to use this pipeline

Pipeline này dùng cho **mọi task wiki-aware** (implement_feature, fix_bug, design, incident, review). Lý do dùng nhất quán thay vì "single agent cho task đơn giản":

- Plan-Reviewer phát hiện sai sớm → giá trị lớn ngay cả task nhỏ.
- `current-task.md` ghi lại context → resume session, audit dễ dàng.
- Subagent có context window riêng → main agent không bị bloat.

**Exception** (single-agent OK):
- Task không liên quan wiki (typo fix, format file).
- Task user explicitly nói "no pipeline" hoặc "quick fix".

---

## Cost vs Quality trade-off

Pipeline này tốn 2-4 LLM calls cho subagent + main agent call. Đắt hơn single-agent. Đáng khi:

- Codebase có ràng buộc contract chặt (Kafka topic, MQTT format, workflow state).
- Wiki đã đầy đủ → agent có cái để retrieve thật.
- Task đủ phức tạp để hallucination tốn kém để fix sau.

Khuyến nghị model:
- Planner / Context-Selector / Plan-Reviewer / Reviewer: model fast/cheap (Haiku, Sonnet) — output schema cố định, không cần creative.
- Builder (main agent): strongest model có sẵn — chỗ này cần reasoning + code generation chất lượng.

---

## Related

- [README.md](README.md) — Pipeline overview + reference index
- [.claude/commands/contextd-use.md](../../.claude/commands/contextd-use.md) — **Execution flow chính thức** (spec sống)
- [task-to-docs-map.md](task-to-docs-map.md) — Intent schema chi tiết
- [task-to-docs-map.md](task-to-docs-map.md) — Map intent → file path
- [context-filter.md](context-filter.md) — Rank + slice rules
- [prompt-template.md](prompt-template.md) — Builder prompt structure
- [validator-rules.md](validator-rules.md) — Rule-based + self-check rules cho Reviewer
- [observability.md](observability.md) — Trace schema, run-id convention, /contextd-eval & /contextd-trace
