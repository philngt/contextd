# pack-solo-builder — Top 10 Common Pitfalls

Anti-pattern lặp lại khi non-tech expert build tool cá nhân/ngành. Additive trên [constraints.md](constraints.md).

## P01 — Tool đa mục đích (vi phạm 1-tool-1-purpose)
- **NG**: 1 tool vừa parse PDF, vừa gửi email, vừa render dashboard.
- **OK**: chia 3 tool nhỏ; ghép qua pipeline đơn giản.
- **Why**: khó debug, khó reuse, khó rollback.
- **Detect**: Layer-1 `pack-solo-builder-multi-purpose-tool` (heuristic).
- **Severity**: error

## P02 — Acceptance criteria vague ("hoạt động tốt")
- **NG**: "tool chạy ổn", "kết quả đúng".
- **OK**: đủ criterion testable để chứng minh core purpose, failure handling và target environment; không quota số lượng cố định.
- **Why**: không biết khi nào done.
- **Detect**: Layer-1 `pack-solo-builder-vague-acceptance` plus `pack-solo-builder-spec-missing-acceptance`.
- **Severity**: error

## P03 — Recommend tech ngoài recipes/
- **NG**: spec gợi ý "dùng MongoDB sharding cluster" trong khi recipes/ chỉ có SQLite.
- **OK**: chỉ chọn tech có recipe; nếu cần mới → đề xuất recipe mới trước.
- **Why**: non-tech user không setup được; tool break.
- **Detect**: Layer-2 — tech stack có recipe link.
- **Severity**: error

## P04 — Jargon không kèm 1-line explain
- **NG**: "dùng cron schedule" không giải thích.
- **OK**: "cron schedule (lịch chạy tự động theo giờ Linux)".
- **Why**: user không biết jargon → lạc.
- **Detect**: Layer-1 — md có jargon từ glossary mà thiếu inline-explain (heuristic).
- **Severity**: warn

## P05 — Sinh code khi spec chưa specced
- **NG**: user mới hỏi "làm tool X", agent code ngay.
- **OK**: chốt Problem/System Map/Tech Stack/Acceptance/Setup trước.
- **Why**: code sai scope = vứt; user mất tiền compute.
- **Detect**: Layer-2 — spec có các section bắt buộc + setup và unresolved questions đã được xử lý trước implement.
- **Severity**: error

## P06 — Thiếu Setup section
- **NG**: tool spec không nói install gì, env var gì.
- **OK**: nêu runtime/dependency version đã test, install từ lock/requirements file và cách cấu hình secret ngoài repo.
- **Why**: user clone về không chạy được.
- **Detect**: Layer-1 `pack-solo-builder-spec-missing-setup`.
- **Severity**: error

## P07 — Không có System Map
- **NG**: chỉ mô tả tool isolated, không nói nó nằm trong workflow nào.
- **OK**: diagram/bullet input → process → output → downstream.
- **Why**: tool cô lập = không integrate được; user quên đặt vào đâu.
- **Detect**: Layer-1 `pack-solo-builder-spec-missing-system-map`.
- **Severity**: warn

## P08 — Tech stack không justify
- **NG**: "dùng FastAPI" không nói tại sao.
- **OK**: 1-2 dòng justify ("nhẹ, auto-doc, có recipe FastAPI-minimal").
- **Why**: lựa chọn arbitrary, không learnable.
- **Detect**: Layer-2 — tech stack có rationale.
- **Severity**: warn

## P09 — Không rollback khi tool break
- **NG**: deploy tool → ghi đè data → không restore được.
- **OK**: backup trước action destructive; dry-run mode; undo doc.
- **Why**: data loss, user mất tin tưởng tool.
- **Detect**: Layer-2 — destructive action có backup step.
- **Severity**: error

## P10 — Treat recipe hoặc domain formula như nguồn đã được verify
- **NG**: copy công thức/liều/quy định từ prompt hoặc recipe rồi dùng cho quyết định thật.
- **OK**: cite source/version/jurisdiction, chốt units/assumptions, qualified review, golden fixtures và human checkpoint theo risk.
- **Why**: recipe có thể outdated hoặc thiếu context chuyên môn; lỗi có thể gây harm thay vì chỉ gây bug.
- **Detect**: Layer-2 — evidence + review + verification contract tồn tại; unresolved gap giữ spec `draft`.
- **Severity**: error

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 multi-purpose | `pack-solo-builder-multi-purpose-tool` | ✓ |
| P02 acceptance | `pack-solo-builder-vague-acceptance`, `pack-solo-builder-spec-missing-acceptance` | ✓ |
| P03 recipes | `pack-solo-builder-recipe-not-in-library` | ✓ |
| P04 jargon | `pack-solo-builder-jargon-without-explain` | ✓ |
| P05 code-first | — | ✓ |
| P06 setup | `pack-solo-builder-spec-missing-setup` | ✓ |
| P07 sysmap | `pack-solo-builder-spec-missing-system-map` | ✓ |
| P08 stack | — | ✓ |
| P09 rollback | — | ✓ |
| P10 domain safety | — | ✓ |
