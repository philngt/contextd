# Pipeline Visual — How the Wiki Works

> Tài liệu trực quan giải thích **wiki-driven pipeline** vận hành thế nào khi user chạy `/use-contextd "..."`.
> Đọc cùng [README.md](README.md), [multi-agent-pipeline.md](multi-agent-pipeline.md), [observability.md](observability.md).

---

## TL;DR — 4 câu hỏi pipeline trả lời

| # | Câu hỏi | Stage trả lời |
|---|---------|----------------|
| 1 | Task này cần pattern/contract nào? | Stage 1 (Planner) |
| 2 | Wiki có gì để dùng cho task này? + Plan đủ thông tin để code chưa? | Stage 2 (Context Selector — gồm cả verdict) |
| 3 | Code sinh ra có vi phạm contract không? | Stage 4 (Reviewer) |

Stage 3 (Builder) là main agent dùng kết quả 1-2 để code. Trace chạy ngầm, ghi JSON cho mọi stage.

---

## Sequence diagram — flow chi tiết

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant M as Main Agent
    participant P as contextd-planner
    participant H as emit_trace.py<br/>(PostToolUse hook)
    participant CS as contextd-context-selector
    participant R as contextd-reviewer
    participant FS as .contextd/runs/{run_id}/

    U->>M: /use-contextd "implement X"
    M->>M: Resolve workspace từ<br/>.contextd/config.json
    M->>P: Task(subagent=contextd-planner)
    P-->>M: Intent JSON +<br/>```json trace block```
    H-->>FS: 01-planner.json
    M->>CS: Task(subagent=contextd-context-selector)
    CS->>FS: ghi current-task.json
    CS-->>M: APPROVED / BLOCK + trace block (verdict)
    H-->>FS: 02-context.json
    alt verdict = BLOCK
        M-->>U: STOP, báo issues
    else verdict = APPROVED
        M->>M: đọc current-task.json<br/>→ Edit/Write code
        M->>FS: 04-builder.json (self-write)
        M->>R: Task(subagent=contextd-reviewer)
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
    Q1 -- no --> S2[Stage 2: Context Selector<br/>retrieve + 5 checks → verdict]
    Halluc1 --> S2
    S2 --> Q2{verdict?}
    Q2 -- BLOCK --> Stop1([STOP<br/>báo user issues])
    Q2 -- APPROVED --> S4[Stage 3: Main agent Builder<br/>read current-task.json, code]
    S4 --> S5[Stage 4: Reviewer<br/>diff code vs context]
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
- **Context-Selector verdict (Stage 2)** — chặn TRƯỚC khi tốn token cho Builder. Lý do: code đã viết sai → đắt để fix.
- **Reviewer (Stage 4)** — chặn TRƯỚC khi user merge. Phát hiện cả violation lẫn hallucinated reference (code reference doc không có trong context).

---

## Stage cheat sheet

| Stage | Agent file | Input | Output (LLM) | Output (file) | Câu hỏi trả lời |
|-------|-----------|-------|--------------|---------------|------------------|
| 0 | Main agent | user task | resolved workspace | `.contextd/config.json` đọc | Workspace nào active? |
| 1 | [contextd-planner](../../.claude/agents/contextd-planner.md) | user_task, workspace | Intent JSON | `01-planner.json` | Task cần pattern/contract nào? |
| 2 | [contextd-context-selector](../../.claude/agents/contextd-context-selector.md) | intent JSON | APPROVED/BLOCK + retrieval data | `02-context.json` (gồm `verdict`) + `.contextd/context/current-task.json` | Wiki có gì để dùng? + Plan đủ thông tin chưa? |
| 3 | Main agent (Builder) | current-task.json | code + Markdown sections | `04-builder.json` (self-write) | Code thế nào dựa trên context? |
| 4 | [contextd-reviewer](../../.claude/agents/contextd-reviewer.md) | code + context_file | APPROVED/VIOLATIONS | `05-review.json` | Code có vi phạm contract? |
| roll-up | hook | every stage | — | `run.json` | Tổng kết run |

**Các signal đáng debug** (xem nhanh trong trace JSON):
- `01-planner.unverified_count > 0` → planner đề xuất pattern không tồn tại trong wiki
- `02-context.gaps[].blocking_hint == true` → wiki thiếu doc cần thiết
- `02-context.verdict == "BLOCK"` → plan không khả thi với wiki hiện có
- `05-review.hallucinated_refs[]` không rỗng → builder reference doc không có trong context (= hallucination)
- `04-builder.assumptions_count > 0` → builder phải tự đoán, dấu hiệu wiki còn gap

---

## File artifact map — đâu lưu cái gì

```
{project_dir}/
├── .contextd/
│   ├── config.json                     ← workspace active config
│   ├── context/
│   │   └── current-task.json             ← Stage 2 output, Stage 4 input
│   └── runs/
│       └── {run_id}/                   ← per-run trace dir
│           ├── run.json                ← roll-up (hook tự update)
│           ├── 01-planner.json
│           ├── 02-context.json         ← gồm verdict APPROVED|BLOCK
│           ├── 04-builder.json         ← main agent self-write
│           └── 05-review.json
{knowledge_root}/                            ← contextd knowledge root
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
   - Terminal A: chạy `/use-contextd "..."` (pipeline chính)
   - Terminal B: `ls -la .contextd/runs/$(ls -t .contextd/runs/ | head -1)/` — refresh để thấy file JSON drop dần

2. **Sau khi run xong** — debug:
   - `/contextd-trace --last` → Markdown timeline 1 run
   - `/contextd-viz --last` → HTML viewer (Phase 2 — nếu đã setup) với side-by-side retrieved-vs-used, hallucination panel
   - `cat .contextd/runs/{run_id}/05-review.json | jq .hallucinated_refs` → xem hallucination thô

3. **Aggregate nhiều runs**:
   - `/contextd-eval` → Markdown report: hallucination rate, top gaps, block rate
   - `/contextd-viz --all` → HTML browser (Phase 2) với filter

---

## Khi nào pipeline KHÔNG chạy

- Task không có wiki (`.contextd/config.json` thiếu) → main agent yêu cầu `/contextd-setup`
- Task user explicitly bypass: "no pipeline", "quick fix", typo fix
- Task `design`/`review` không sinh code → có thể skip Stage 5

Xem [multi-agent-pipeline.md#L171-L181](multi-agent-pipeline.md#L171-L181) cho exception list.

---

## Related

- [README.md](README.md) — pipeline overview + reference index
- [multi-agent-pipeline.md](multi-agent-pipeline.md) — vai trò + schema từng agent
- [observability.md](observability.md) — trace schema + hook contract
- [run-trace.schema.json](../../templates/run-trace.schema.json) — JSON schema cho mọi trace file
- [.claude/commands/use-contextd.md](../../.claude/commands/use-contextd.md) — execution flow chính thức
- [.claude/commands/contextd-trace.md](../../.claude/commands/contextd-trace.md) — Markdown 1-run viewer
- [.claude/commands/contextd-eval.md](../../.claude/commands/contextd-eval.md) — Markdown aggregate
- `.claude/commands/contextd-viz.md` — HTML viewer (Phase 2, nếu đã add)
