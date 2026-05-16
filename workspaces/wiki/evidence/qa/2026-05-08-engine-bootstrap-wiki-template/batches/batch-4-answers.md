# Q&A Answers — Batch 4

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Batch**: 4 | **Priority**: P0 | **Asked at**: 2026-05-08T00:00:00+07:00 | **Count**: 2

---

## q-013 — Contract C-007 slash-command-naming
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●○) | **Confidence**: medium
- **Answer**: Document BOTH conventions tại `{ws}/platform/contracts/slash-command-naming.md`. RULE: kebab-case + lowercase + hyphens (universal). RECOMMENDATION (non-binding): "subject-verb" cho commands mới (consistency với evidence-* và wiki-* groups). Không break 5 existing commands.
- **Cited**: `(a04-contract-proposals.md#C-007)`, `(.claude/commands/README.md:L16-L20)`, `(08-knowledge-gaps.md#G-010)`

## q-014 — Contract C-008 sub-agent-frontmatter-schema
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●○) | **Confidence**: medium
- **Answer**: Required fields: name, description, tools, model. Convention (non-binding): description chứa "DÙNG KHI" + "KHÔNG DÙNG". File: `{ws}/platform/contracts/sub-agent-frontmatter-schema.md`. Defer C-008a (tools allowlist principle) per G-009 (sample size concern).
- **Cited**: `(a04-contract-proposals.md#C-008)`, 5 sub-agent files

---

## Mini Contradiction Hunter
- C-007 "kebab-case + lowercase" universal rule consistent với 19/19 commands. No conflict.
- C-008 "DÙNG KHI/KHÔNG DÙNG" as convention không break sample (5/5 follow).
- No conflicts.

---

## P0 batch summary

After Batch 4: **all 14 P0 questions answered**. Outcomes:
- 13 accepted gợi ý từ recommendations.md (via=code-analyst-recommend)
- 1 user-override (q-007: P-007 not flagship)
- 0 deferred to expert
- 0 skipped
