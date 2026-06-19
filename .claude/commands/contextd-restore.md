# /contextd-restore — Restore Workspace From Backup

Khôi phục contextd config và Claude adapter artifacts từ backup gần nhất hoặc backup do user chỉ định.

## CHECKPOINT 0 — Chọn backup source

Ưu tiên:
1. Nếu user cung cấp đường dẫn backup thì dùng đường dẫn đó.
2. Nếu không, tự chọn file mới nhất trong `~/.claude/backups/`.

Hỗ trợ format:
- `.tgz` (macOS/Linux)
- `.zip` (Windows PowerShell)

Nếu không tìm thấy file phù hợp thì dừng và báo rõ.

## CHECKPOINT 1 — Cảnh báo ghi đè

In cảnh báo:

```text
⚠️ Restore sẽ ghi đè dữ liệu hiện tại trong ~/.contextd và ~/.claude (commands/agents/config).
Nên backup trạng thái hiện tại trước khi restore.
```

Gợi ý user chạy `/contextd-backup` trước.

## CHECKPOINT 2 — Xác nhận thực thi

Hỏi user xác nhận restore từ `{backup_path}`. Chỉ chạy khi user đồng ý.

## CHECKPOINT 3 — Khôi phục theo OS

- macOS/Linux: giải nén `.tgz` về home config paths trong archive
- Windows PowerShell: giải nén `.zip` về home config paths trong archive

## CHECKPOINT 4 — Verify sau restore

Bắt buộc verify ít nhất một trong các path tồn tại sau restore:
- `~/.contextd/config.json`
- `~/.claude/commands/`
- `~/.claude/agents/`

Nếu verify fail: báo lỗi, không báo thành công.

## CHECKPOINT 5 — Kết quả

```text
Restore complete
- Source: {backup_path}
- Next step: /contextd-version
- Gợi ý: /exit rồi mở lại Claude Code session
```

## Compatibility

Legacy `~/.claude/wiki-global.json` may exist in older backups. Restore it only as a migration adapter; canonical config is `~/.contextd/config.json`.
