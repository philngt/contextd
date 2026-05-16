# ADR-001: Introduce variant=agentic-engine cho /code-analyze

## Scope

Workspace-wide (`{ws}/decisions/`) — engine-level decision affecting mọi workspace consume engine.

## Status

ACCEPTED — implemented session 2026-05-08.

## Context

Trước session 2026-05-08, `/code-analyze` chỉ hỗ trợ runtime codebase (Java/Spring, Node/Express, Python/FastAPI, Go) — Section 4–8 của raw.md design cho REST endpoints / Kafka consumers / JPA entities / DB migrations.

User cố gắng chạy `/code-analyze` trên `wiki-template` repo (markdown-heavy: 19 slash commands, 5 sub-agents, 16 pipeline spec docs, 22 templates) gặp 2 vấn đề:

1. **Validation gate fail**: repo không có `.git/` cũng không có `pom.xml`/`package.json`/etc → STOP `not a recognized code repo`.
2. **Sections misfire**: nếu force-fit, Section 4 (REST endpoints) / Section 5 (Kafka consumers) / Section 7 (DB schema) sẽ trống — output cho CORE-CODE prompts (c01–c04) sẽ tạo proposals vô nghĩa (Kafka topic naming pattern cho 1 markdown engine).

Engine maintainers cần path để bootstrap wiki cho engine repos themselves.

## Decision

Introduce `code_variant: code | agentic-engine` field cho `source.yaml`.

- Default omitted = `code` (backward-compat).
- `agentic-engine` variant:
  - **Validation gate softened**: không yêu cầu `.git/`/build file; đủ ≥ 2 markers trong {`agents/**/*.md`, `.claude/commands/**/*.md`, `.claude/agents/**/*.md`, `templates/`, `mcp.json`}.
  - **Section 4–8 redefined**: Slash commands / Sub-agents / Pipeline stages / Templates / Hooks (thay vì REST/Kafka/Services/DB/Public APIs).
  - **evid-id prefix**: `engine` (thay `code`).
  - **Origin format**: `engine:{slug}@{sha}`.
  - **CORE prompts**: A1–A4 dispatched via `code_variant` (parallel với CORE-CODE C1–C4).
  - **ON-DEMAND prompts**: A5–A7 (parallel với C5–C7).
- Shared (cross-variant): CORE 4 (questions) + CORE 8 (knowledge gaps) — same filename, slight variant override prompts.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| (a) Skip /code-analyze cho engine repos | Engine maintainers không có path để bootstrap wiki cho engine. Onboarding gap. |
| (b) Force-fit variant=code, accept empty Section 4–8 | CORE-CODE prompts hallucinate (đề xuất Kafka pattern cho markdown repo). Misfire output >> empty output value. |
| (c) New `source_type=engine` parallel với code/paste/api/mcp | Source_type space explode khi thêm variant tương lai (infra, data-pipeline, ...). Variant approach scales better. |

## Trade-offs

**Benefits:**

- Variant approach extensible (vd thêm `infra`, `data-pipeline` future).
- Share state machine + file layout contracts (DRY).
- CORE 4 (questions) và CORE 8 (gaps) reused via filename across variants.
- Backward-compat (default omitted treated as `code`).

**Costs:**

- `code-analysis-prompts.md` tăng size từ ~520 lines lên ~920 lines (CORE-CODE + CORE-AGENTIC trong cùng file). → Mitigation per ADR-002.
- 2 templates `code-snapshot.md` + `agentic-engine-snapshot.md` cần maintain song song. Drift risk khi future change Section structure.
- Implementation patch trên 5 surfaces:
  - `agents/pipeline/code-snapshot-conventions.md` Section 12 — agentic-engine variant detection + structure
  - `agents/pipeline/code-analysis-prompts.md` — CORE-AGENTIC A1–A4 + ON-DEMAND A5–A7
  - `.claude/commands/code-analyze.md` — Bước 1.4 detect + Bước 4 dispatch + Bước 7 dispatch
  - `.claude/commands/evidence-analyze.md` — Bước 2 dispatch (patched session 2026-05-08)
  - `templates/agentic-engine-snapshot.md` — new template

## Impact

- Mọi workspace có thể onboard engine-style repos qua `/code-analyze --variant agentic-engine`.
- Variant pattern (per `{ws}/platform/patterns/variant-discriminated-dispatcher.md` v1) documented cho future variant additions.
- Bundle mode supports per-repo `variant` field — multi-repo bundles có thể trộn variants.
- Existing code/paste/api/mcp evidence flows unchanged (pure additive).

## Why Not Project-Level

Engine-wide invariant — affects every codebase consuming engine, not specific to 1 project. Workspace-level (`{ws}/decisions/`) is correct scope.

## Related

- Pattern: `../platform/patterns/variant-discriminated-dispatcher.md` (P-008)
- Contract: `../platform/contracts/raw-md-section-structure.md` (variant table)
- Contract: `../platform/contracts/source-yaml-schema.md` (`code_variant` field)
- Contract: `../platform/contracts/evid-id-format.md` (`engine` src prefix)
- ADR: `002-keep-code-analysis-prompts-monolithic.md` (file size mitigation)
- Source: q-017, evidence `2026-05-08-engine-bootstrap-wiki-template`
