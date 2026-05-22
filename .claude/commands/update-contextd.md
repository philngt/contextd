# /update-contextd — Cập nhật wiki sau khi code thay đổi

Chạy skill này sau khi thay đổi code để giữ wiki **của workspace active** đồng bộ với thực tế. Phần ghi/sửa file wiki được delegate cho subagent `contextd-curator` — main agent chỉ làm khâu khám phá thay đổi và xác nhận.

```
[main]   Bước 0 — resolve workspace
   ↓
[main]   Bước 1 — collect change_summary (git diff + user input)
   ↓
[main]   Bước 2 — quyết định engine-level vs workspace-level
   ↓
[contextd-curator]   Bước 3 — apply changes vào wiki
   ↓
[main]   Bước 4 — verify output, báo user
```

---

## Bước 0 — Resolve workspace (main agent)

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `wiki_json_dir`, `workspace`, `effective_wiki_root`, `{ws}`. Đồng thời:

- `project_dir = wiki_json_dir` (curator đọc tham chiếu, KHÔNG ghi).
- Sanity check: nếu thay đổi code rõ ràng thuộc workspace khác (branch name, path patterns trỏ tới project trong workspace khác) → STOP, cảnh báo user `/switch-workspace` trước. KHÔNG ghi vào sai workspace.

---

## Bước 0.5 — Evidence-driven mode (optional, main agent)

Trước khi đi vào Bước 1 (collect change_summary từ git diff), kiểm tra evidence flow:

1. Nếu được invoke với flag `--evidence <evid-id>` → load evidence đó (bắt buộc).
2. Nếu KHÔNG có flag → đọc `{effective_wiki_root}/workspaces/{workspace}/evidence/_index.md` (nếu tồn tại). Tìm entry state=`qa_done` chưa applied.
   - Nếu có ≥1 → hỏi user 1 lần qua AskUserQuestion: "Có evidence `{id1}, {id2}, ...` ở state qa_done. Apply trước khi update từ git diff?" Options: ["Apply via /evidence-apply", "Skip evidence, dùng git diff", "Cancel"].
   - Nếu chỉ có 0 → bỏ qua bước này, đi tiếp Bước 1.

3. Nếu user chọn dùng evidence:
   - Load `{ws}/evidence/{id}/qa/verified-facts.md` + `analysis/{id}/02-contradiction.md` + `analysis/{id}/08-knowledge-gaps.md`.
   - Augment `change_summary` ở Bước 1 bằng "Verified facts" block (mỗi fact → 1 dòng action cho curator).
   - **Authority order**: Contracts > Verified facts > Platform Patterns > Project Docs > Domain Knowledge.
   - Ưu tiên cách: chạy `/evidence-apply --id {id} --mode update` (wrap update-contextd và tự ghi `applied/{id}/manifest.yaml` audit trail).

Reference: [agents/pipeline/evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md), [evidence-apply.md](evidence-apply.md).

---

## Bước 1 — Collect change_summary (main agent)

Mục tiêu: build 1 mô tả structured đủ chi tiết để curator biết cần tạo/sửa file nào.

1. Chạy `git diff` (hoặc `git log` nếu thay đổi đã commit) để lấy danh sách file đã đổi.
2. Phân loại theo bảng:

| Loại thay đổi (detect) | Hint cho curator |
|-----------------------|------------------|
| File code mới trong project | `service mới` hoặc `pattern mới` (hỏi user nếu không rõ) |
| Thêm/sửa Kafka consumer | service update |
| Thêm/sửa MQTT topic/handler | service update + có thể contract update (MQTT type mới) |
| Thay đổi config (batch_size, timeout, concurrency) | Config Overrides update |
| Code lặp lại pattern hiện có ở project khác | candidate pattern mới (cần xác nhận) |
| Quyết định kiến trúc lớn (đổi DB, đổi protocol) | ADR mới |
| Bug agent lặp lại nhiều lần | constraint mới + validator rule mới |
| Đã xử lý sự cố production | runbook mới |

3. Nếu chưa rõ phân loại → hỏi user 1 câu cụ thể, KHÔNG đoán.

4. Build `change_summary` dạng:

```md
## Changes
- {mô tả ngắn 1 dòng cho mỗi thay đổi}

## Files changed in code
- {path}: {what changed}

## Suggested wiki actions
- {action 1: tạo pattern X / update contract Y / add service Z}
- {action 2}

## Open questions
- {nếu có}
```

---

## Bước 2 — Quyết định engine-level vs workspace-level (main agent)

Curator mặc định ghi vào `{ws}/...`. Nếu thay đổi là **rule/constraint áp dụng cho mọi workspace** (không phải chỉ workspace này) → đánh dấu rõ trong `change_summary`:

```
## Scope
- engine-level: agents/constraints.md, agents/pipeline/validator-rules.md
- workspace-level (default): mọi thứ khác
```

Quy tắc nhanh:
- Constraint riêng cho domain/project trong workspace này → workspace-level
- Constraint cho cách dùng wiki, format pattern, structure ADR → engine-level
- Khi không chắc → workspace-level (an toàn hơn, không ảnh hưởng workspace khác)

---

## Bước 3 — Invoke `contextd-curator` (subagent)

Gọi Agent tool với `subagent_type=contextd-curator`. Prompt phải chứa:

- `change_summary`: nội dung Markdown từ Bước 1+2 (bao gồm `## Scope`)
- `effective_wiki_root`
- `workspace`
- `project_dir` (để curator có thể Read tham khảo, KHÔNG được Write)

**Output mong đợi**: bảng `## Wiki Updated` liệt kê file đã created/edited + section `## Knowledge Map Diffs` + `## Next Steps for User`.

Nếu curator trả `OUT-OF-SCOPE EDIT BLOCKED` → STOP, báo user (đây là dấu hiệu change_summary có path sai).

---

## Bước 4 — Verify & báo user (main agent)

1. **Path sandbox verification (BẮT BUỘC trước mọi thứ)**:
   - Parse `## Wiki Updated` table từ output của curator.
   - Với mỗi path trong table:
     - Resolve về absolute (curator đã được yêu cầu output absolute, nhưng vẫn verify).
     - Check path có prefix `{effective_wiki_root}` không.
     - Check path thuộc `{effective_wiki_root}/workspaces/{workspace}/` HOẶC `{effective_wiki_root}/agents/` (chỉ khi `## Scope` của change_summary có `engine-level`).
   - Nếu phát hiện vi phạm:
     ```
     ⚠ SANDBOX VIOLATION
     Curator đã ghi vào path ngoài scope cho phép:
       - {path} (expected under: {effective_wiki_root}/workspaces/{workspace}/ hoặc engine)
     Đây có thể là bug curator hoặc prompt injection. KHÔNG commit. Báo user kiểm tra ngay.
     ```
     Dừng pipeline, KHÔNG tự rollback (đó là quyết định user).
2. Đọc lại các file curator vừa created/edited để xác nhận nội dung hợp lý (ít nhất file `knowledge-map.md` và `patterns-index.md` của workspace).
3. Confirm với user:
   - Workspace nào đã được cập nhật?
   - Đã cập nhật/tạo file nào?
   - Knowledge-map và patterns-index đã sync chưa?
   - Có gap nào curator báo nhưng chưa giải quyết không?
4. Nhắc user review trước khi commit. KHÔNG tự `git add` hay commit wiki — đó là quyết định của user.

---

## Quy tắc cứng

- KHÔNG ghi/sửa file wiki trực tiếp trong main agent — luôn delegate qua `contextd-curator`. Lý do: curator có template lookup + index update bắt buộc + self-check path trước mỗi Edit/Write. Lưu ý: enforcement path sandbox là **soft (prompt-based)** ở phía curator + **post-hoc verification** ở Bước 4 main agent — không có tool sandbox theo path. Đây là defense-in-depth, không phải single layer.
- KHÔNG copy pattern từ workspace khác. Mỗi workspace là sandbox độc lập — nếu cần pattern tương tự, brief curator tạo mới trong workspace hiện tại.
- KHÔNG xóa file wiki. Nếu cần deprecate → brief curator đánh dấu `> Deprecated:` ở đầu file.
- KHÔNG tự `git add` / `git commit` wiki — chỉ báo user file đã đổi để user tự quyết.
- Nếu curator skip tạo index entry → bắt buộc re-invoke với prompt explicit "MUST update patterns-index.md" thay vì tự sửa.
