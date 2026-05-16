# pack-solo-builder — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-solo-builder-`.

Áp dụng cho file `.md` trong `{ws}/tools/` (spec files).

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-solo-builder-spec-missing-problem`     | error | Spec file thiếu section heading `Problem` / `Vấn đề` |
| `pack-solo-builder-spec-missing-system-map`  | error | Spec file thiếu section `System Map` / `Sơ đồ hệ thống` |
| `pack-solo-builder-spec-missing-stack`       | error | Spec file thiếu section `Tech Stack` / `Stack` |
| `pack-solo-builder-spec-missing-acceptance`  | error | Spec file thiếu `Acceptance Criteria` |
| `pack-solo-builder-spec-missing-setup`       | warn  | Spec file thiếu section `Setup` (per-OS) |
| `pack-solo-builder-recipe-not-in-library`    | warn  | Spec mention "Recipe used:" nhưng path không tồn tại trong `packs/pack-solo-builder/recipes/` |
| `pack-solo-builder-jargon-without-explain`   | warn  | Spec dùng jargon (venv, Docker, cron, SQLite, argparse, Streamlit, ...) trên cùng dòng KHÔNG có explanation in parentheses hoặc dòng kế |
| `pack-solo-builder-multi-purpose-tool`       | warn  | Title hoặc Problem section dùng "and" / "và" nhiều lần → có thể vi phạm "1 tool = 1 mục đích" |
| `pack-solo-builder-vague-acceptance`         | warn  | Acceptance Criteria có "hoạt động tốt", "dễ dùng", "stable", "robust" — không testable |

## Layer-2 self-check

Xem [`prompt-overrides.md`](prompt-overrides.md#self-check-append) — toàn bộ block Self-Check.

## Limitations

- Section detection dựa markdown heading (`## Section`). Spec dùng table-only hoặc HTML → false-negative.
- Jargon list giới hạn (~15 terms phổ biến nhất). Term ngành nghề (mechanical, accounting) không catch.
- Multi-purpose detection dựa keyword đếm — false-positive khi "and" dùng trong context hợp lệ.
- Vague acceptance check chỉ catch keyword phổ biến, không hiểu context (vd "performance phải tốt hơn baseline" thực ra rõ ràng).
