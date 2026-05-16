# ADR-002: Keep code-analysis-prompts.md Monolithic (do NOT split)

## Scope

Workspace-wide (`{ws}/decisions/`) — engine-level decision.

## Status

ACCEPTED — implemented session 2026-05-08.

## Context

Sau ADR-001 introducing variant=agentic-engine, file `agents/pipeline/code-analysis-prompts.md` chứa:

- CORE-CODE: C1–C4 (~470 lines)
- ON-DEMAND code: C5–C8 (~140 lines)
- CORE-AGENTIC: A1–A4 (~280 lines)
- ON-DEMAND agentic: A5–A7 (~80 lines)
- Shared: CORE 4 (questions) + CORE 8 (gaps) (~100 lines combined)
- Variant dispatch table + bundle notes + cite consistency check (~50 lines)

Total ~920 lines. Concern raised trong evidence raw.md Section 10: file phình to.

## Decision

KEEP monolithic trong `agents/pipeline/code-analysis-prompts.md`. KHÔNG split.

Single file chứa:
- Header dispatch table (variant routing).
- CORE-CODE section (C1..C4 + C8 QA Recommender).
- CORE-AGENTIC section (A1..A4).
- Shared sections (CORE 4 questions, CORE 8 gaps) — located between CORE-CODE và CORE-AGENTIC để dễ tham chiếu.
- ON-DEMAND sections (C5..C7, A5..A7).
- Bundle mode notes (apply across variants).
- Cite consistency check (validator).

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Split: `code-analysis-prompts.md` (CORE-CODE) + `agentic-analysis-prompts.md` (CORE-AGENTIC) | Shared sections (CORE 4, CORE 8) phải duplicate hoặc cross-reference complex. Variant dispatch table phải maintain ở 2 nơi. |
| Split: per-prompt file (c01.md, c02.md, ..., a01.md, ...) | Over-fragmentation; navigation harder; cross-reference từng prompt dài lê thê. |
| Move shared sections (CORE 4, CORE 8) ra file riêng | Shared sections strongly coupled với variant overrides — split cũng tạo cross-reference complex. |

## Trade-offs

**Benefits:**

- Shared CORE 4 / CORE 8 / variant dispatch table maintained once (DRY).
- Easier to find prompts when looking for variant + prompt combination (1 file scan).
- Cross-reference giữa CORE-CODE và CORE-AGENTIC prompts trivial (anchor links trong cùng file).

**Costs:**

- 920 lines reading scroll trên devices nhỏ.
- Khi thêm variant thứ 3 (vd `infra`), file có thể vượt 1500 lines → revisit decision.

## Trigger to Revisit

ADR này KHÔNG vĩnh viễn. Revisit khi BẤT KỲ điều kiện sau:

1. **File > 1500 lines** — overhead navigation rõ rệt.
2. **Variant thứ 3 introduced** (vd `infra`, `data-pipeline`) — split tự nhiên hơn ở boundary đó.
3. **User feedback** — multiple users báo navigation slow / hard to find prompts.

Khi revisit, cân nhắc lại split vs alternatives. Mỗi revisit ghi ADR mới (vd ADR-XXX-split-code-analysis-prompts.md), KHÔNG amend ADR-002.

## Impact

- Mainline pipeline development tiếp tục với 1 file.
- Engine maintainers reference 1 location cho mọi variant prompt.
- Cross-variant patches dễ hơn (vd update CORE 4 schema applies cho cả code + agentic-engine variants trong 1 edit).

## Why Not Project-Level

Engine-wide artifact — `agents/pipeline/code-analysis-prompts.md` là engine spec doc, áp dụng mọi workspace. Workspace-level (`{ws}/decisions/`) is correct scope.

## Related

- ADR: `001-introduce-agentic-engine-variant.md` (introduces variant adding lines)
- Engine source: `agents/pipeline/code-analysis-prompts.md`
- Source: q-018, evidence `2026-05-08-engine-bootstrap-wiki-template`
