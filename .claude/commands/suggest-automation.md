# Suggest Automation

Chuyển một **pattern lặp** (đã được `scripts/detect_repetition.py` phát hiện) thành **skill / slash command / subagent / pack** — hoặc refine artifact đang có nhưng miss-fire.

> Detector chạy ngầm qua UserPromptSubmit hook và inject 1 dòng hint `[rep] '<id>' xN -> /suggest-automation <id>` khi đủ ngưỡng. Khi user thấy hint hoặc tự nhận ra hành vi lặp, chạy command này để promote.

## Argument syntax

```
/suggest-automation [{cluster_id}]
```

Không pass `{cluster_id}` → list top clusters từ `{ws}/.observations/clusters.json`.

## Bước 0 — Resolve workspace

Theo [agents/pipeline/workspace-resolution.md](../../agents/pipeline/workspace-resolution.md) Profile B. Set `{ws} = {effective_knowledge_root}/workspaces/{workspace}/`. STOP nếu thiếu.

## Bước 1 — Load clusters

Đọc `{ws}/.observations/clusters.json`. Nếu thiếu:

```
✗ Chưa có observation. Detector cần ≥ 3 prompt tương tự trong 14 ngày.
  Hook đã bật chưa? Xem .claude/settings.json -> hooks.UserPromptSubmit.
```

Lọc: `count ≥ REP_MIN_COUNT`, `id NOT IN suppressions.dismissed`. Sort theo `count` desc.

## Bước 2 — Pick cluster

- Có `{cluster_id}`: tìm trong list, không thấy → STOP.
- Không có: show top 5 (id, count, theme, first/last seen, 1 prompt_preview tiêu biểu từ `prompts.jsonl`). Dùng `AskUserQuestion` để chọn.

## Bước 3 — Chọn loại artifact

Dùng `AskUserQuestion` (single-select):

| Loại | Khi dùng | Ghi vào |
|------|----------|---------|
| **Slash command** | Workflow gồm bước rõ ràng, ít suy luận | `{ws}/.claude/commands/<name>.md` hoặc `<knowledge_root>/.claude/commands/<name>.md` |
| **Subagent** | Cần phân tích/tổng hợp riêng, model + tool whitelist riêng | `{ws}/agents/<name>.md` hoặc `.claude/agents/<name>.md` |
| **Skill** | Khả năng tái sử dụng — Claude auto-invoke khi keyword match | `~/.claude/skills/<name>/` hoặc `packs/<pack>/skills/<name>/` |
| **Pack** | Cả stack mới (Kafka, Mobile, ML...) | `packs/<pack-name>/` qua `scripts/scaffold-pack.py` |
| **Refine existing** | Cluster đã có artifact match nhưng vẫn lặp | Sửa file artifact hiện có |

## Bước 4 — Sinh skeleton

Mở **chỉ section tương ứng** trong [agents/pipeline/automation-skeletons.md](../../agents/pipeline/automation-skeletons.md) (A=command, B=subagent, C=skill, D=pack, E=refine). Lifecycle front-matter cũng ở đó (mục cuối).

> Đừng load file skeletons trừ khi user đã chốt loại artifact ở Bước 3 — file ~80 dòng, không cần khi command chỉ chạy đến Bước 2.

## Bước 5 — Trình diff cho user

KHÔNG ghi ngay. Show preview:

```
Sẽ tạo: {path} ({N} dòng)
---
{nội dung}
---
Confirm? [y/N]
```

Đợi xác nhận. User chỉnh → sửa, show diff lại.

## Bước 6 — Suppress cluster

Sau khi user accept + file đã ghi:

1. Đọc `{ws}/.observations/suppressions.json` (tạo nếu thiếu): `{"dismissed":[],"resolved":[]}`.
2. Append `resolved`: `{"cluster_id":"...","artifact":"<path>","ts":"..."}`.
3. Append `cluster_id` vào `dismissed`.
4. Atomic write qua `atomic_write_json`.

## Bước 7 — Báo cáo

```
✓ Promoted cluster '{id}' -> {path}
  Detector sẽ ngừng nhắc cluster này.
  Reload Claude Code session để artifact mới có hiệu lực.
```

## Self-check

- [ ] Chỉ ghi trong `{ws}/`, `<knowledge_root>/.claude/`, hoặc `packs/{pack}/`. KHÔNG ghi workspace khác.
- [ ] Front-matter có đủ field bắt buộc (xem skeletons.md mục cuối).
- [ ] Đã thêm cluster vào suppressions.
- [ ] Không hardcode path — dùng `{ws}` placeholder hoặc relative.
