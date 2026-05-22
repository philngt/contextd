# pack-ui-ux — Retrieval Map

Component → wiki doc mapping for this pack.

| Component | Docs to retrieve (relative `{ws}/`) |
|---|---|
| `design-system` | `platform/design/design-system.md`, `platform/design/tokens.md` |
| `accessibility` | `platform/design/a11y.md` |
| `user-flows` | `domains/{domain}/flows/*.md` |
| `ux-writing` | `platform/design/ux-writing.md` |

Components must match `pack.yaml#components`.

## Notes

- `{domain}` = domain liên quan đến task hiện tại (infer từ task description hoặc file context).
- Nếu `platform/design/` chưa có → STOP, thông báo user: "Workspace chưa có design docs — tạo `platform/design/design-system.md` để bắt đầu."
- Flows scoped per domain — chỉ đọc domain liên quan, không load tất cả flows của workspace.
