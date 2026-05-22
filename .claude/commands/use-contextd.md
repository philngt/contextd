# /use-contextd — Sử dụng wiki cho task mới

Chạy pipeline này trước khi viết bất kỳ dòng code nào. Pipeline delegate hai bước nặng (intent parsing + context retrieval) cho subagent chuyên biệt để giữ context window của main agent sạch và tránh agent chính tự "trượt" vai trò.

```
[main]   Bước 0 — resolve workspace + wiki_root
   ↓
[contextd-planner]            Bước 1 — phân tích task → intent JSON
   ↓
[contextd-context-selector]   Bước 2 — retrieve + slice + ghi current-task.md
                                       + emit verdict APPROVED|BLOCK
   ↓
[main]   Bước 3 — verify gap, code theo prompt template
   ↓
[contextd-reviewer]           Bước 4 — (manual/optional) review code đã sinh
```

> **Lưu ý**: Plan-review (verdict APPROVED/BLOCK) đã được gộp vào `contextd-context-selector` ở Bước 2. Pipeline trước đây có thêm Bước 2.5 (`contextd-plan-reviewer`) — đã bị xoá để giảm 1 LLM call và loại trùng việc verify pattern (planner + plan-reviewer cùng check). Xem CHANGELOG.

---

## Bước 0 — Resolve workspace & wiki root (main agent)

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir`, `workspace`, `effective_wiki_root`, `{ws}`. Đồng thời:

- `project_dir = wiki_json_dir` (= project root, parent của `.claude/`).
- Parse section `## Packs` trong `{ws}/workspace.md` → list pack names. Lưu thành `active_packs`. Verify mỗi pack có `{effective_wiki_root}/packs/{pack-name}/pack.yaml` — pack thiếu → warning, vẫn tiếp tục với danh sách đã filter. Pass `active_packs` vào prompt của các subagent ở Bước 1, 2 để planner/selector biết keyword set + retrieval map nào áp dụng.

KHÔNG retrieve hay đọc file pattern/contract ở bước này — đó là việc của subagent.

---

## Bước 1 — Invoke `contextd-planner` (subagent)

Gọi Agent tool với `subagent_type=contextd-planner`. Prompt phải chứa:

- `user_task`: task gốc của user (nguyên văn)
- `effective_wiki_root`: đường dẫn tuyệt đối
- `workspace`: tên workspace active
- `project_dir`: project root (để planner ghi trace vào `.claude/runs/`)
- `config_hint`: nội dung `.claude/wiki.json` (nếu có), hoặc "none"

**Output mong đợi**: JSON intent đúng schema trong [agents/contextd-planner.md](.claude/agents/contextd-planner.md), kèm 1 dòng `Trace: ...`.

Nếu planner trả `MISSING INPUT` hoặc JSON có `missing_knowledge` không rỗng → review với user trước khi tiếp tục, KHÔNG tự đoán.

Lưu `intent_json` (bao gồm `run_id`) vào context của main agent. Mọi stage sau đều cần `run_id`.

---

## Bước 2 — Invoke `contextd-context-selector` (subagent)

Gọi Agent tool với `subagent_type=contextd-context-selector`. Prompt phải chứa:

- `intent_json`: output JSON từ Bước 1
- `effective_wiki_root`
- `project_dir`
- `user_task` (để gắn vào header context file)

Subagent sẽ:
- Map intent → file wiki cụ thể theo `agents/pipeline/task-to-docs-map.md`
- Slice section liên quan theo `agents/pipeline/context-filter.md`
- Ghi đè `{project_dir}/.claude/context/current-task.md` (gồm cả section `## Plan Review`)
- **Chạy 5 check** (pattern/contract verify carry-over, pattern/contract có trong Referenced Docs, context đủ component, conflict nội tại, gap blocking severity) và emit `verdict: APPROVED|BLOCK` trong trace.
- Emit trace `{project_dir}/.claude/runs/{run_id}/02-context.json`

**Output mong đợi**: 1 dòng `APPROVED` hoặc `BLOCK: {reason}` ở đầu output, kèm trace JSON cuối.

Nếu confirm không xuất hiện hoặc file `current-task.md` không được tạo → STOP, báo lỗi cho user.

**Xử lý verdict**:
- `APPROVED` → tiếp tục Bước 3. Nếu có `## Warnings` → đọc trước khi code.
- `BLOCK` → STOP pipeline, báo user. KHÔNG tự sửa context.
  - BLOCK do pattern/contract thiếu → đề xuất user `/update-contextd` để tạo trước, hoặc brief lại task.
  - BLOCK do conflict nội tại → cần update wiki giải quyết conflict, KHÔNG tự bypass.

---

## Bước 3 — Verify gap & xác nhận trước khi code (main agent)

1. Đọc lại `{project_dir}/.claude/context/current-task.md`.
2. Trả lời 6 câu hỏi:
   - Workspace nào đang active?
   - Pattern nào sẽ được áp dụng?
   - Contract nào bị ràng buộc?
   - Project có override gì không?
   - Domain workflow có ràng buộc gì?
   - Section `## Knowledge Gaps` có entry nào không?

3. Nếu `## Knowledge Gaps` không rỗng → DỪNG, báo user, KHÔNG đoán, KHÔNG fallback workspace khác.

4. Nếu pass → tiếp tục Bước 4.

---

## Bước 4 — Code theo prompt template (main agent)

Main agent đóng vai builder. Output theo cấu trúc cố định trong `agents/pipeline/prompt-template.md`:

```
## Understanding
## Knowledge Mapping   ← link tới các section trong .claude/context/current-task.md
## Design
## Implementation
## Edge Cases
## Assumptions
```

Mọi quyết định kỹ thuật phải reference được vào 1 entry trong `## Referenced Docs` của `current-task.md`. Nếu phải vượt ra ngoài → ghi vào `## Assumptions`, không im lặng.

---

## Bước 5 — Review (subagent, tuỳ task)

Sau khi code đã sinh và file đã sửa, **trước hết** ghi `04-builder.json` (xem [prompt-template.md](../../agents/pipeline/prompt-template.md) section "TRACE EMIT"). Sau đó gọi Agent tool với `subagent_type=contextd-reviewer`:

- `solution_files`: danh sách file vừa Edit/Write
- `context_file`: `{project_dir}/.claude/context/current-task.md`
- `effective_wiki_root`
- `project_dir`: để emit trace
- `builder_output`: section `## Knowledge Mapping` từ Bước 4 (cho hallucination check)

Output:
- `APPROVED` → chuyển user
- `Violations Found` → append vào cuối `current-task.md` dưới section `## Violations`, báo user trước khi commit. KHÔNG tự sửa khi user chưa duyệt.

Sau Bước 5, có thể chạy `/contextd-trace {run_id}` để xem toàn bộ pipeline đã chạy thế nào, hoặc `/contextd-eval` để aggregate metric qua nhiều run.

**Bỏ qua Bước 5 khi**: task chỉ là `design`/`review` không sinh code, hoặc fix bug 1 dòng quá nhỏ.

---

## Quy tắc cứng

- KHÔNG inline làm việc của planner/context-selector trong main agent — luôn delegate qua Agent tool. Lý do: subagent có context window riêng, output có schema cố định, dễ audit.
- KHÔNG skip Bước 2 — `current-task.md` là single source of truth cho session này; thiếu nó thì reviewer cũng không hoạt động đúng.
- KHÔNG đọc file ngoài `workspaces/{workspace}/` (trừ `agents/` chung của wiki).
- Sau Bước 4, nếu phát hiện cần thêm context mới → re-run từ Bước 1, KHÔNG patch tay vào `current-task.md`.
