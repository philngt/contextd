# Observations Clear

Maintenance cho file state của repetition detector trong workspace active. Xem [agents/pipeline/repetition-detection.md](../../agents/pipeline/repetition-detection.md).

## Argument syntax

```
/observations-clear [--list | --dismiss {cluster_id} | --reset]
```

Mặc định (không flag) = `--list`.

## Bước 0 — Resolve workspace

Theo [agents/pipeline/workspace-resolution.md](../../agents/pipeline/workspace-resolution.md) Profile B. Set `obs_dir = {ws}/.observations/`.

## Mode A — `--list`

1. Đọc `{obs_dir}/clusters.json`. Đếm tổng cluster, tổng observation từ `prompts.jsonl` (line count).
2. Lọc cluster `count ≥ REP_MIN_COUNT` (default 3).
3. Hiển thị table sort theo `count` giảm dần:

```
ID                          | Count | First seen | Last seen  | Hinted | Theme
--------------------------- | ----- | ---------- | ---------- | ------ | -----
rebase-wiki-merge-a1b2c3    |     7 | 2026-04-10 | 2026-05-14 | yes    | rebase wiki merge
deploy-staging-x9y8z7       |     4 | 2026-04-22 | 2026-05-12 | no     | deploy staging k8s
...
```

4. Show danh sách `dismissed` từ `suppressions.json` riêng (cluster user đã chủ động ẩn).

## Mode B — `--dismiss {cluster_id}`

1. Verify `{cluster_id}` tồn tại trong `clusters.json`. Không có → STOP với lỗi rõ.
2. Đọc `{obs_dir}/suppressions.json` (tạo nếu chưa có): `{"dismissed": [], "resolved": []}`.
3. Append `{cluster_id}` vào `dismissed` (skip nếu đã có).
4. Atomic write qua `scripts/lib/atomic_write.py#atomic_write_json` — gọi inline Python một dòng nếu cần.
5. Báo:
   ```
   ✓ Cluster '{id}' đã ẩn. Detector sẽ không nhắc lại.
     Khôi phục bằng cách xoá id khỏi {obs_dir}/suppressions.json#dismissed.
   ```

## Mode C — `--reset`

XOÁ history (cluster + raw prompt log) nhưng **giữ suppressions** — user vẫn không bị nhắc lại pattern đã chủ động bỏ qua.

1. Hỏi user xác nhận (AskUserQuestion, Yes/No): "Xoá toàn bộ observation history của workspace `{workspace}`?".
2. Nếu Yes: unlink `{obs_dir}/clusters.json` và `{obs_dir}/prompts.jsonl`.
3. Báo:
   ```
   ✓ Đã reset observation history. Detector bắt đầu thu thập lại.
     Suppressions giữ nguyên ({n} cluster đã ẩn).
   ```

## Self-check

- [ ] Chỉ thao tác trong `{ws}/.observations/` của workspace active.
- [ ] Atomic write cho mọi JSON file (qua `atomic_write_json`).
- [ ] Không xoá `suppressions.json` trong mode `--reset`.
