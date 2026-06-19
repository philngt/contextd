# /contextd-team-sync — Team Workspace Sync

Đồng bộ workspace knowledge với team repo (git pull/push/status).

> **Yêu cầu:** `knowledge_root` trong `~/.contextd/config.json` phải trỏ về một **git repository** (thường là team knowledge repo).

---

## Bước 1 — Resolve knowledge_root

Dùng resolver canonical của contextd:

1. Đọc `~/.contextd/config.json` → lấy `knowledge_root`.
2. Expand `~` thành `$HOME`.
3. Kiểm tra `knowledge_root` tồn tại và là git repo (`.git/`).

Nếu không phải git repo → STOP:
```
✗ knowledge_root ({knowledge_root}) không phải git repo.
  Để dùng team sync, knowledge_root phải trỏ về một git repo
  (thường là team knowledge repo).

  Cách sửa:
  1. Clone team knowledge repo:
     git clone <team-repo-url> ~/company-wiki
  2. Sửa ~/.contextd/config.json:
     { "workspace": "default", "knowledge_root": "/Users/you/company-wiki" }
  3. Chạy lại /contextd-team-sync
```

---

## Bước 2 — Dispatch theo subcommand

User input: `/contextd-team-sync {pull|push|status}`

### `pull` — Lấy knowledge mới nhất từ team

1. `cd knowledge_root && git pull --ff-only`
2. Nếu success → in: `✅ Đã pull knowledge mới nhất từ team.`
3. Nếu có local changes chưa commit → `git pull --ff-only` sẽ fail.
   - In lỗi.
   - Hướng dẫn user resolve manually hoặc chạy `push` trước.

Sau pull thành công, suggest:
```
Gợi ý tiếp theo:
  /rebase-contextd      → verify knowledge không drift với codebase
  /use-contextd "..."   → bắt đầu task với knowledge mới nhất
```

### `push` — Đẩy thay đổi wiki lên team repo

1. Kiểm tra `git status --short workspaces/`:
   - Nếu clean → in: `ℹ️ workspaces/ không có thay đổi — không cần push.`
   - Nếu có changes → tiếp tục.
2. `git add workspaces/` (`.gitignore` trong knowledge repo đã loại trừ `evidence/`, `.observations/`, `eval/results/`).
3. Kiểm tra lại staged changes:
   - Nếu không có gì staged → in: `ℹ️ Không có thay đổi nào trong workspaces/ sau khi apply .gitignore.`
4. Tạo commit message:
   - Nếu user cung cấp message: dùng message đó.
   - Nếu không: `Update workspace knowledge (YYYY-MM-DD)`.
5. `git commit -m "{msg}" && git push`
6. In: `✅ Đã push workspace changes lên team repo.`

### `status` — Xem trạng thái workspace

1. `cd knowledge_root && git status --short workspaces/`
2. Hiển thị output (hoặc "clean" nếu rỗng).
3. Hiển thị branch hiện tại.

---

## Edge Cases

- **knowledge_root không tồn tại:** STOP, hướng dẫn `contextd migrate-config` hoặc `/contextd-setup`.
- **knowledge_root là git repo nhưng chưa có remote:** STOP, hướng dẫn `git remote add origin <url>`.
- **Merge conflict khi pull:** In lỗi chi tiết, hướng dẫn resolve manual (`cd knowledge_root && git status`). Không tự resolve.
- **Push thất bại do network:** In lỗi, suggest thử lại.

## Compatibility

Nếu `~/.contextd/config.json` thiếu, resolver migration có thể fallback legacy `~/.claude/wiki-global.json#wiki_root` hoặc `~/.Codex/wiki-global.json#wiki_root`. Khi fallback xảy ra, command phải khuyến nghị `contextd migrate-config` hoặc `/contextd-setup`.
