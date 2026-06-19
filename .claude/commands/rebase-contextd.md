# /rebase-contextd — Rebase Wiki Against Code

Chạy skill này định kỳ hoặc khi nghi ngờ wiki **của workspace active** đã lỗi thời so với codebase thực tế.
Mục tiêu: tìm và vá mọi chỗ wiki nói một kiểu, code chạy một kiểu.

## Bước 0 — Xác định active workspace

Theo [workspace-resolution.md Profile A](../../agents/pipeline/workspace-resolution.md#profile-a--active-workspace-required). Set: `config_dir`, `workspace`, `effective_knowledge_root`, `{ws}`. Toàn bộ rebase chỉ scope trong `{ws}/`.

Sau đó: Confirm với user "Sẽ rebase wiki của workspace `{workspace}` (codebase: `<cwd>`). Đúng chưa?" (AskUserQuestion Yes/No nếu chưa chắc).

## Bước 0.5 — Evidence-driven mode (optional)

Nếu được invoke với `--evidence <evid-id>` HOẶC `{ws}/evidence/_index.md` có entry state=`qa_done` chưa applied:
- Ưu tiên đọc `{ws}/evidence/{id}/qa/verified-facts.md` + `analysis/{id}/02-contradiction.md` + `analysis/{id}/08-knowledge-gaps.md` làm **source-of-truth**.
- **Conflict resolution rule** khác mặc định:
  - Nếu code thực tế ≠ verified-facts → **verified-facts thắng** (evidence là truth, code có thể chưa kịp deploy).
  - Nếu wiki hiện tại ≠ verified-facts → wiki update theo facts.
  - Nếu code thực tế ≠ wiki HIỆN TẠI và KHÔNG có fact cover → fall back behavior cũ (sửa wiki theo code).
- Authority order: **Contracts > Verified facts > Code thực tế > Wiki hiện tại**.

Prefer wrap qua `/evidence-apply --id {id} --mode rebase` để có manifest audit trail (tự ghi `applied/{id}/manifest.yaml`).

Nếu KHÔNG có flag và KHÔNG có evidence pending → tiếp tục flow cũ scan code vs wiki.

Reference: [agents/pipeline/evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md), [evidence-apply.md](evidence-apply.md).

## Bước 1 — Lập danh sách cần kiểm tra

Tạo checklist gồm tất cả service doc trong workspace:

```
{ws}/projects/
  {project}/
    knowledge-map.md
    services/
      {service}.md  ← từng file này cần verify
    decisions/
      *.md
```

Và tất cả platform patterns + contracts của workspace:

```
{ws}/platform/patterns/*.md
{ws}/platform/contracts/*.md
```

## Bước 2 — Verify từng service doc

Với mỗi `{ws}/projects/{project}/services/{service}.md`, kiểm tra:

### 2a. Config Overrides còn đúng không?

Đọc bảng `Config Overrides` trong service doc.
So sánh từng giá trị với config thực tế trong code (application.yml, properties, env vars).

| Trạng thái | Hành động |
|-----------|-----------|
| Giá trị trong wiki = code | ✅ giữ nguyên |
| Giá trị trong wiki ≠ code | ❌ cập nhật wiki theo code |
| Config trong code không có trong wiki | ❌ thêm vào bảng |
| Config trong wiki không còn trong code | ❌ xóa khỏi bảng |

### 2b. Flow còn phản ánh đúng không?

Đọc section `Flow` trong service doc.
Đọc implementation thực tế trong code.
Nếu flow thay đổi (thêm bước, bỏ bước, đổi thứ tự) → cập nhật.

### 2c. Pattern reference còn đúng không?

Kiểm tra dòng `Áp dụng platform pattern: → {path}`.
Xác nhận code thực sự đang dùng pattern đó (path trỏ vào `{ws}/platform/patterns/...`), không phải implementation tự viết.

Nếu code đã tự viết khác pattern → một trong hai:
- Code sai → fix code theo pattern
- Pattern cần update → cập nhật pattern và ghi ADR lý do trong `{ws}/decisions/`

### 2d. Failure handling còn đầy đủ không?

So sánh bảng `Failure Handling` với code thực tế.
Tìm các error case trong code không có trong wiki và ngược lại.

## Bước 3 — Verify platform patterns

Với mỗi `{ws}/platform/patterns/{pattern}.md`:

### 3a. Default Config còn là default không?

Đọc `Default Config` trong pattern.
Kiểm tra các service trong workspace đang dùng pattern này — có service nào dùng giá trị khác mà không ghi vào Override không?

### 3b. Bảng "Used By" còn đầy đủ không?

Tìm trong codebase (chỉ codebase liên quan workspace này) tất cả nơi pattern này được áp dụng.
So sánh với danh sách `## Used By` trong file pattern.
Thêm service còn thiếu, xóa service đã không còn dùng.

## Bước 4 — Verify contracts

Với mỗi `{ws}/platform/contracts/{contract}.md`:

### 4a. Registered Types còn đúng không?

Tìm tất cả handler đang được register trong code.
So sánh với bảng `Registered Types` trong contract.
Thêm type mới, đánh dấu hoặc xóa type đã bị xóa.

### 4b. Format còn đúng không?

Kiểm tra format topic/schema trong contract với format thực tế trong code.

## Bước 5 — Verify knowledge-map.md

Với mỗi `{ws}/projects/{project}/knowledge-map.md`:

- Các link có còn trỏ đúng file không? (file đã bị rename hoặc move chưa?)
- Các link `../../platform/...`, `../../domains/...`, `../../runbooks/...`, `../../decisions/...` có resolve về đúng workspace không? (KHÔNG được trỏ ra ngoài `{ws}/`)
- Có service doc mới chưa được thêm vào map không?
- Có ADR mới chưa được thêm không?

## Bước 6 — Verify patterns-index.md

So sánh danh sách trong `{ws}/patterns-index.md` với tất cả file thực tế trong `{ws}/platform/patterns/` và `{ws}/platform/contracts/`.
Thêm pattern/contract mới, xóa pattern/contract đã bị remove.

## Bước 7 — Verify workspace.md

Đọc `{ws}/workspace.md`:

- `Tech Stack` còn khớp với codebase không?
- `Override Notes` có liệt kê đầy đủ file `{ws}/agents/...` đang tồn tại không? (nếu có file override mà workspace.md không nhắc → thêm; nếu workspace.md nhắc file đã xóa → bỏ)

## Bước 8 — Báo cáo kết quả

Tạo báo cáo theo format:

```
## Rebase Wiki Report — workspace `{active}` — {ngày}

### Đã cập nhật
- {file}: {mô tả thay đổi}

### Gap phát hiện (chưa có đủ thông tin để fix)
- {file}: {mô tả gap} — cần: {thông tin gì}

### Không thay đổi
- {số lượng} file đã verify, còn đúng

### Link cross-workspace bị phát hiện (vi phạm)
- {file}: link trỏ ra ngoài {ws}/ — phải fix
```

## Khi nào nên chạy

- Sau mỗi sprint hoặc release của workspace
- Khi AI agent tạo ra code sai lặp lại trong workspace này (wiki có thể đã lỗi thời)
- Khi onboard project mới vào workspace (verify wiki phản ánh đúng codebase)
- Trước khi dùng `/use-contextd` cho task lớn
- Sau khi `/switch-workspace` về workspace lâu không động đến
