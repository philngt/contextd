# pack-dba — Coding Rules

- Trình bày migration theo thứ tự: precheck -> change -> validation -> rollback.
- Mọi đề xuất index/query nên nêu expected trade-off (read/write/storage).
- Với incident DB, luôn nêu blast radius và recovery checkpoints.
