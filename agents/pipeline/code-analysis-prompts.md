# Code Analysis Prompts — Evidence Pipeline (source_type=code)

**Orchestrator**. Dispatch tới 1 trong 2 variant theo `source.yaml#code_variant`. Mỗi variant định nghĩa CORE prompts riêng + ON-DEMAND prompts riêng.

> Sibling: [critical-analysis-prompts.md](critical-analysis-prompts.md) (cho non-code text sources such as paste, api, mcp, document, interview, ticket, analytics, regulation, design, incident).

---

## Variant dispatch

| `source.yaml#code_variant` | Pipeline | Reference |
|---|---|---|
| `code` (default, vắng mặt) | CORE-CODE: C1, C2, C3, C4, 4, 8 + ON-DEMAND C5, C6, C7, C8 | [code-analysis-prompts-code.md](code-analysis-prompts-code.md) |
| `agentic-engine` | CORE-AGENTIC: A1, A2, A3, A4, 4, 8 + ON-DEMAND A5, A6, A7 | [code-analysis-prompts-agentic.md](code-analysis-prompts-agentic.md) |

`CORE 4` (`04-questions.md`) và `CORE 8` (`08-knowledge-gaps.md`) DÙNG CHUNG filename ở mọi variant — chỉ override prompt template theo variant. Filename ổn định để `/evidence-qa` và `/evidence-apply` không phân nhánh.

**Bundle mode** (`source.yaml#code_repos` non-empty): raw.md có Section 0 + per-repo sections với prefix `[{repo-name}]`. Per-repo có thể mix variants (`code_repos[].variant`). Bundle dispatcher chạy **union** prompts dựa trên variants có mặt.

---

## Conventions (shared cho mọi variant)

Mỗi prompt có:
- **Inputs**: file đọc trước khi run (raw.md, source.yaml, wiki context).
- **Output file**: path tương đối `analysis/{evid-id}/`.
- **Output schema**: structure markdown bắt buộc.
- **Cite rule**: mọi claim cite một trong:
  - `(raw.md#section-N)` — về snapshot section
  - `(raw.md#L<start>-L<end>)` — về dòng raw cụ thể
  - `({path}:L..-L..)` — về code thật trong repo (path relative tới repo root)
  - `({ws}/path/to/file.md#section)` — về wiki

### Khi nào dùng `raw.normalized.md`

Nếu raw.md > 50KB và đã có `raw.normalized.md` → input nói `raw.normalized.md (full)` thay vì `raw.md`. Cite format đổi thành `(raw.normalized.md#section-N)`.

Theo Section 7 của [code-snapshot-conventions.md](code-snapshot-conventions.md).

---

## Cite consistency check (shared)

Validator (`validator-rules.md`) sẽ reject nếu:
- File cXX/aXX có claim không kèm citation `(raw.md#...)` hoặc `({path}:L..)`.
- File cXX/aXX cite path ngoài `code_scope` của source.yaml (bundle mode: ngoài tất cả `code_repos[].scope`).
- File cXX/aXX cite `{ws}/...` trỏ về workspace khác workspace_at_ingest.
