# Pipeline Visual — How the Wiki Works

> Tài liệu trực quan giải thích **wiki-driven pipeline** vận hành thế nào khi user chạy `/contextd-use "..."`.
> Đọc cùng [README.md](README.md), [multi-agent-pipeline.md](multi-agent-pipeline.md), [observability.md](observability.md).

---

## TL;DR — 4 câu hỏi pipeline trả lời

| # | Câu hỏi | Stage trả lời |
|---|---------|----------------|
| 1 | Task này cần pattern/contract nào? | Stage 1 (Planner) |
| 2 | Wiki có gì để dùng cho task này? | Stage 2 (Context Selector) |
| 3 | Plan đủ thông tin để code chưa? | Stage 3 (Plan Reviewer) |
| 4 | Code sinh ra có vi phạm contract không? | Stage 5 (Reviewer) |

Stage 4 (Builder) là main agent dùng kết quả 1-3 để code. Stage 6 (Trace) chạy ngầm, ghi JSON cho mọi stage.

---

## Sequence diagram — flow chi tiết

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant M as Main Agent
    participant P as wiki-planner
    participant H as emit_trace.py<br/>(PostToolUse hook)
    participant CS as wiki-context-selector
    participant PR as wiki-plan-reviewer
    participant R as wiki-reviewer
    participant FS as .claude/runs/{run_id}/

    U->>M: /contextd-use "implement X"
    M->>M: Resolve workspace từ<br/>.claude/wiki.json
    M->>P: Task(subagent=wiki-planner)
    P-->>M: Intent JSON +<br/>```json trace block```
    H-->>FS: 01-planner.json
    M->>CS: Task(subagent=wiki-context-selector)
    CS->>FS: ghi current-task.md
    CS-->>M: confirm + trace block
    H-->>FS: 02-context.json
    M->>PR: Task(subagent=wiki-plan-reviewer)
    PR-->>M: APPROVED / BLOCK + trace
    H-->>FS: 03-plan-review.json
    alt verdict = BLOCK
        M-->>U: STOP, báo issues
    else verdict = APPROVED
        M->>M: đọc current-task.md<br/>→ Edit/Write code
        M->>FS: 04-builder.json (self-write)
        M->>R: Task(subagent=wiki-reviewer)
        R-->>M: APPROVED / VIOLATIONS + trace
        H-->>FS: 05-review.json
        M-->>U: kết quả final
    end
```

**Đọc diagram**: mũi tên đặc = LLM call, mũi tên đứt nét = file I/O. Hook `emit_trace.py` chạy mỗi khi Task tool kết thúc — main agent không phải tự ghi trace cho subagent.

---

## Decision flow — khi nào BLOCK / VIOLATIONS

```mermaid
flowchart TD
    Start([User task]) --> S1[Stage 1: Planner<br/>parse intent, verify patterns/contracts exist]
    S1 --> Q1{unverified_count > 0?}
    Q1 -- yes --> Halluc1[Hallucination<br/>flag in 01-planner.json]
    Q1 -- no --> S2[Stage 2: Context Selector<br/>retrieve docs, slice sections]
    Halluc1 --> S2
    S2 --> S3[Stage 3: Plan Reviewer<br/>4 checks against context]
    S3 --> Q2{verdict?}
    Q2 -- BLOCK --> Stop1([STOP<br/>báo user issues])
    Q2 -- APPROVED --> S4[Stage 4: Main agent Builder<br/>read current-task.md, code]
    S4 --> S5[Stage 5: Reviewer<br/>diff code vs context]
    S5 --> Q3{verdict?}
    Q3 -- VIOLATIONS --> Out1([báo violations<br/>+ hallucinated_refs])
    Q3 -- APPROVED --> Out2([final output])

    classDef block fill:#fee,stroke:#c00
    classDef ok fill:#efe,stroke:#0a0
    classDef warn fill:#ffe,stroke:#cc0
    class Stop1,Out1 block
    class Out2 ok
    class Halluc1 warn
```

**Hai gate quan trọng**:
- **Plan Reviewer (Stage 3)** — chặn TRƯỚC khi tốn token cho Builder. Lý do: code đã viết sai → đắt để fix.
- **Reviewer (Stage 5)** — chặn TRƯỚC khi user merge. Phát hiện cả violation lẫn hallucinated reference (code reference doc không có trong context).

---

## Stage cheat sheet

| Stage | Agent file | Input | Output (LLM) | Output (file) | Câu hỏi trả lời |
|-------|-----------|-------|--------------|---------------|------------------|
| 0 | Main agent | user task | resolved workspace | `.claude/wiki.json` đọc | Workspace nào active? |
| 1 | [wiki-planner](../../.claude/agents/wiki-planner.md) | user_task, workspace | Intent JSON | [01-planner.json](../../templates/run-trace.schema.json#L36-L82) | Task cần pattern/contract nào? |
| 2 | [wiki-context-selector](../../.claude/agents/wiki-context-selector.md) | intent JSON | confirm 1 dòng | [02-context.json](../../templates/run-trace.schema.json#L84-L118) + `.claude/context/current-task.md` | Wiki có gì để dùng? |
| 3 | [wiki-plan-reviewer](../../.claude/agents/wiki-plan-reviewer.md) | intent + context_file | APPROVED/BLOCK | [03-plan-review.json](../../templates/run-trace.schema.json#L120-L152) | Plan đủ thông tin chưa? |
| 4 | Main agent (Builder) | current-task.md | code + Markdown sections | [04-builder.json](../../templates/run-trace.schema.json#L154-L174) (self-write) | Code thế nào dựa trên context? |
| 5 | [wiki-reviewer](../../.claude/agents/wiki-reviewer.md) | code + context_file | APPROVED/VIOLATIONS | [05-review.json](../../templates/run-trace.schema.json#L176-L213) | Code có vi phạm contract? |
| roll-up | hook | every stage | — | [run.json](../../templates/run-trace.schema.json#L215-L238) | Tổng kết run |

**Các signal đáng debug** (xem nhanh trong trace JSON):
- `01-planner.unverified_count > 0` → planner đề xuất pattern không tồn tại trong wiki
- `02-context.gaps[].blocking_hint == true` → wiki thiếu doc cần thiết
- `03-plan-review.verdict == "BLOCK"` → plan không khả thi với wiki hiện có
- `05-review.hallucinated_refs[]` không rỗng → builder reference doc không có trong context (= hallucination)
- `04-builder.assumptions_count > 0` → builder phải tự đoán, dấu hiệu wiki còn gap

---

## File artifact map — đâu lưu cái gì

```
{project_dir}/
├── .claude/
│   ├── wiki.json                       ← workspace active config
│   ├── context/
│   │   └── current-task.md             ← Stage 2 output, Stage 4 input
│   └── runs/
│       └── {run_id}/                   ← per-run trace dir
│           ├── run.json                ← roll-up (hook tự update)
│           ├── 01-planner.json
│           ├── 02-context.json
│           ├── 03-plan-review.json
│           ├── 04-builder.json         ← main agent self-write
│           └── 05-review.json
{wiki_root}/                            ← repo này (wiki-template)
├── agents/                             ← engine prompts (chung mọi workspace)
├── scripts/emit_trace.py               ← PostToolUse hook
└── workspaces/{workspace}/             ← scope retrieval Stage 2
    ├── patterns-index.md               ← Stage 1 đọc để verify
    ├── platform/contracts/             ← Stage 2 retrieve, Stage 5 check
    ├── platform/patterns/              ← Stage 2 retrieve
    └── domains/                        ← Stage 2 retrieve
```

`run_id` format: `{YYYY-MM-DD}-{HHMMSS}-{slug}`. Slug = 4-6 từ đầu task, lowercase, `[a-z0-9-]` only. Chi tiết: [observability.md#L22-L33](observability.md#L22-L33).

---

## Cách "thấy" pipeline đang chạy gì

1. **Mở 2 terminal**:
   - Terminal A: chạy `/contextd-use "..."` (pipeline chính)
   - Terminal B: `ls -la .claude/runs/$(ls -t .claude/runs/ | head -1)/` — refresh để thấy file JSON drop dần

2. **Sau khi run xong** — debug:
   - `/contextd-trace --last` → Markdown timeline 1 run
   - `/contextd-viz --last` → HTML viewer (Phase 2 — nếu đã setup) với side-by-side retrieved-vs-used, hallucination panel
   - `cat .claude/runs/{run_id}/05-review.json | jq .hallucinated_refs` → xem hallucination thô

3. **Aggregate nhiều runs**:
   - `/contextd-eval` → Markdown report: hallucination rate, top gaps, block rate
   - `/contextd-viz --all` → HTML browser (Phase 2) với filter

---

## Khi nào pipeline KHÔNG chạy

- Task không có wiki (`.claude/wiki.json` thiếu) → main agent yêu cầu `/contextd-setup`
- Task user explicitly bypass: "no pipeline", "quick fix", typo fix
- Task `design`/`review` không sinh code → có thể skip Stage 5

Xem [multi-agent-pipeline.md#L171-L181](multi-agent-pipeline.md#L171-L181) cho exception list.

---

## Related

- [README.md](README.md) — pipeline overview + reference index
- [multi-agent-pipeline.md](multi-agent-pipeline.md) — vai trò + schema từng agent
- [observability.md](observability.md) — trace schema + hook contract
- [run-trace.schema.json](../../templates/run-trace.schema.json) — JSON schema cho mọi trace file
- [.claude/commands/contextd-use.md](../../.claude/commands/contextd-use.md) — execution flow chính thức
- [.claude/commands/contextd-trace.md](../../.claude/commands/contextd-trace.md) — Markdown 1-run viewer
- [.claude/commands/contextd-eval.md](../../.claude/commands/contextd-eval.md) — Markdown aggregate
- `.claude/commands/contextd-viz.md` — HTML viewer (Phase 2, nếu đã add)
