# Q&A Answers — Batch 3

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Batch**: 3 | **Priority**: P0 | **Asked at**: 2026-05-08T00:00:00+07:00 | **Count**: 4

---

## q-009 — Contract C-001 evid-id-format
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: Có, thêm vào `{ws}/platform/contracts/evid-id-format.md` với src list hiện tại {paste, api, mcp, code, engine, platform}. Future src additions update contract version.
- **Cited**: `(a04-contract-proposals.md#C-001)`, `(agents/pipeline/code-snapshot-conventions.md:L40-L62)`, `(templates/evidence-source.yaml:L5)`

## q-010 — Contract C-002 evidence-file-layout
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: Có, thêm vào `{ws}/platform/contracts/evidence-file-layout.md`. Invariant: sources/{id}/{required, conditional} + analysis/ + qa/ + _index.md. Reference từ C-005 (state machine — _index.md as SoT).
- **Cited**: `(a04-contract-proposals.md#C-002)`, `(agents/pipeline/code-snapshot-conventions.md:L25-L34)`

## q-011 — Contract C-003 raw-md-section-structure
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●●) | **Confidence**: high
- **Answer**: 1 contract đa-variant tại `{ws}/platform/contracts/raw-md-section-structure.md`. Variant table inline (code | agentic-engine | bundle). Easy to extend khi thêm variant mới.
- **Cited**: `(a04-contract-proposals.md#C-003)`, `(agents/pipeline/code-snapshot-conventions.md:L67-L133, L385-L402)`

## q-012 — Contract C-004 source-yaml-required-fields
- **Status**: answered | **By**: self | **Via**: code-analyst-recommend (●●○) | **Confidence**: medium
- **Answer**: KEEP unified tại `{ws}/platform/contracts/source-yaml-schema.md`. Conditional fields rõ trong YAML structure. Revisit tách nếu conditional grow phức tạp.
- **Cited**: `(a04-contract-proposals.md#C-004)`, `(templates/evidence-source.yaml:L1-L54)`

---

## Mini Contradiction Hunter
- C-002 invariant cite C-005 (state machine) — pair with C-005 already accepted (q-005). Compatible.
- C-003 đa-variant approach align với D-001 (variant introduction). Compatible.
- No conflicts.
