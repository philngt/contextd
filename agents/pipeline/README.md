# Prompt Pipeline

## Purpose

Mô tả cách feed knowledge từ wiki cho LLM agent mà không bị hallucination, context overload, hay priority confusion.

> Throwing the whole wiki into a prompt làm agent hoặc hallucinate hoặc ignore 80% knowledge. Pipeline filters, ranks, and structures context trước khi agent thấy.

---

## Quan hệ giữa các tài liệu

| File | Vai trò |
|------|---------|
| **[.claude/commands/use-contextd.md](../../.claude/commands/use-contextd.md)** | **Execution flow chính thức** — spec sống main agent dùng để gọi pipeline. Khi conflict với file khác, file này thắng. |
| [multi-agent-pipeline.md](multi-agent-pipeline.md) | Reference: vai trò + I/O schema + lý do tách của từng subagent |
| [task-to-docs-map.md](task-to-docs-map.md) | Schema của intent JSON (output Stage 1) |
| [task-to-docs-map.md](task-to-docs-map.md) | Map intent type/component → file wiki cụ thể (input cho Stage 2) |
| [context-filter.md](context-filter.md) | Rank + slice + budget rules (input cho Stage 2) |
| [prompt-template.md](prompt-template.md) | Output template main agent dùng ở Stage 3 |
| [validator-rules.md](validator-rules.md) | Rules cho Stage 4 (contextd-reviewer) — engine defaults + workspace override |

`use-contextd.md` định nghĩa **how**; các file pipeline này định nghĩa **what** từng stage cần.

---

## Pipeline (4 stage)

```
User Task
   ↓
[Stage 0] Main agent              → resolve workspace + wiki_root
   ↓
[Stage 1] contextd-planner            → parse intent (xem task-to-docs-map.md)
   ↓
[Stage 2] contextd-context-selector   → retrieve + filter + slice (xem task-to-docs-map.md, context-filter.md)
                                  → ghi {project_dir}/.claude/context/current-task.md
                                  → emit verdict APPROVED|BLOCK (5 check)
   ↓
[Stage 3] Main agent (Builder)    → đọc current-task.md, code theo prompt-template.md
   ↓
[Stage 4] contextd-reviewer (optional)→ check code vs context theo validator-rules.md
   ↓
Output
```

> Pipeline gộp từ 5 → 4 stage: `contextd-plan-reviewer` đã được merge vào `contextd-context-selector` (giảm trùng việc verify pattern). Xem CHANGELOG.

Chi tiết I/O schema từng stage: xem [multi-agent-pipeline.md](multi-agent-pipeline.md).

---

## Anti-Patterns

| Anti-Pattern | Consequence |
|-------------|-------------|
| Dump full wiki vào prompt | Noise, wasted tokens, agent ignore phần lớn |
| Skip priority order | Agent chọn sai source khi docs conflict |
| Skip Context-Selector verdict (Stage 2) | Sai sót lọt xuống Builder, fix tốn token gấp 5–10× |
| Skip Validator (Stage 4) | Cùng bug lặp lại qua nhiều generation |
| Feed full doc thay vì slice section | Context overflow, signal bị loãng |
| Main agent tự inline parse + retrieve | Context window bị bloat, lost track |

---

## Key Insight

> Prompt pipeline không phải data transfer. Nó là **thiết kế hệ thống reasoning của agent**.

Mỗi stage có 1 job hẹp + output schema cố định. Khi 1 stage fail, biết ngay stage nào sai (vs single-agent fail = phải trace ngược toàn bộ).
