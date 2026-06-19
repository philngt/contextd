# Prompt Pipeline

## Purpose

Mô tả cách feed knowledge từ wiki cho LLM agent mà không bị hallucination, context overload, hay priority confusion.

> Throwing the whole wiki into a prompt làm agent hoặc hallucinate hoặc ignore 80% knowledge. Pipeline filters, ranks, and structures context trước khi agent thấy.

---

## Quan hệ giữa các tài liệu

| File | Vai trò |
|------|---------|
| **[.claude/commands/use-contextd.md](../../.claude/commands/use-contextd.md)** | **Execution flow chính thức** — slash adapter gọi canonical `contextd context`. Khi conflict với file khác, file này thắng. |
| [multi-agent-pipeline.md](multi-agent-pipeline.md) | Historical/reference: vai trò subagent cũ + mapping sang artifact engine |
| [task-to-docs-map.md](task-to-docs-map.md) | Intent taxonomy + task/component → docs mapping |
| [context-filter.md](context-filter.md) | Rank + slice + budget rules used by context artifact builder |
| [prompt-template.md](prompt-template.md) | Output template main agent dùng sau khi đọc artifact |
| [validator-rules.md](validator-rules.md) | Self-check/reviewer rules — engine defaults + workspace override |

`use-contextd.md` định nghĩa **how**; các file pipeline này định nghĩa **what** từng stage cần.

---

## Pipeline (context artifact v1)

```
User Task
   ↓
[Stage 0] CLI resolver            → resolve workspace + knowledge_root
   ↓
[Stage 1] contextd context        → classify intent + detect components
   ↓
[Stage 2] context artifact engine → retrieve + filter + slice + validate refs
                                  → emit .contextd/context/current-task.json
                                  → render .contextd/context/current-task.md
                                  → materialize .contextd/context/packs/{packKey}.md
   ↓
[Stage 3] Main agent (Builder)    → đọc JSON artifact, code theo prompt-template.md
   ↓
[Stage 4] reviewer (optional)     → check code vs referenced_docs/contextPack
   ↓
Output
```

`current-task.md` là render cho người/adapter; JSON artifact là source of truth. Chi tiết lịch sử subagent cũ: xem [multi-agent-pipeline.md](multi-agent-pipeline.md).

---

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Dump full wiki vào prompt | Noise, wasted tokens, agent ignore phần lớn |
| Skip priority order | Agent chọn sai source khi docs conflict |
| Treat markdown as source of truth | Adapter drift; JSON artifact bị bypass |
| Let `contextd find` override artifact refs | Advisory discovery lấn deterministic contracts/patterns |
| Skip Validator (Stage 4) | Cùng bug lặp lại qua nhiều generation |
| Feed full doc thay vì slice section | Context overflow, signal bị loãng |
| Main agent tự inline parse + retrieve | Context window bị bloat, lost track |

---

## Key Insight

> Prompt pipeline không phải data transfer. Nó là **thiết kế hệ thống reasoning của agent**.

Mỗi stage có 1 job hẹp + output schema cố định. Khi 1 stage fail, biết ngay stage nào sai (vs single-agent fail = phải trace ngược toàn bộ).
