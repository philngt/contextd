# ADR-004: Pattern–Contract Pairing Convention

## Scope

Workspace-wide (`{ws}/decisions/`) — convention cho mọi workspace future (KHÔNG chỉ workspace `wiki`).

## Status

ACCEPTED — implemented session 2026-05-08 via evidence `2026-05-08-engine-bootstrap-wiki-template` (3 pairs introduced: P-005↔C-005, P-006↔C-006, future P-008↔C-???).

## Context

Trong `a03-pattern-proposals.md` + `a04-contract-proposals.md` của evidence này, 3 cặp pattern-contract cùng concept lộ ra:

- P-005 evidence-state-machine ↔ C-005 evidence-state-machine-transitions
- P-006 citation-rule-relative-path ↔ C-006 citation-format
- P-007/P-008 (patterns chưa có pair contract — chờ data thêm)

Câu hỏi: Khi nào 1 concept nên là pattern, khi nào contract, khi nào CẢ HAI?

Without explicit convention, future evidence sẽ generate inconsistent decisions (đôi khi PAIR, đôi khi pattern only, đôi khi contract only).

## Decision

Define convention layered information cho concepts:

| Layer | Định nghĩa | Audience | File location |
|-------|-----------|----------|---------------|
| **Pattern** | Implementation **skeleton** + canonical structure + diff vs alternatives | Người đang IMPLEMENT 1 feature follow pattern | `{ws}/platform/patterns/{name}.md` |
| **Contract** | Invariant **rule** + observed evidence + counter-examples + validator behavior | Người đang VALIDATE / REVIEW code | `{ws}/platform/contracts/{name}.md` |

### Pairing rule

Concept có cả **implementation skeleton** VÀ **invariant rule** → tạo cả 2 docs với cross-reference 2 chiều. Pattern doc cite contract; contract doc cite pattern.

### Single-document rule

- Concept chỉ là **pure rule** (vd evid-id format): contract only.
- Concept chỉ là **implementation pattern** không có hard invariant (vd "preview-block layout style"): pattern only.

### Cross-reference format (for paired docs)

Pattern doc:
```markdown
> PAIR pattern của contract `../contracts/{name}.md`. Pattern describes implementation skeleton; contract describes invariant rules.
```

Contract doc:
```markdown
> PAIR contract của pattern `../patterns/{name}.md`. Pattern describes implementation skeleton; contract describes invariant rules.
```

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| All patterns (no contracts) | Validator reject conditions cần ngôn ngữ "rule" không phải "skeleton". Confusion. |
| All contracts (no patterns) | Implementer cần "how to apply", không phải "what to validate". Half-information. |
| Merge pattern + contract trong 1 doc | Audience mixing — implementer lost trong validator details; validator lost trong implementation detail. |
| Auto-derive contract từ pattern (script) | Loss of nuance; observed-evidence + counter-examples hard to auto-generate. |

## Trade-offs

**Benefits:**

- Clear separation of concerns (HOW vs WHAT-IS-CORRECT).
- Cross-reference enforces consistency (impl skeleton phải satisfy invariant rule).
- Different audiences (implementer vs validator) có entry points riêng — better navigation.
- Future patterns/contracts decision rõ ràng (no ad-hoc judgment).

**Costs:**

- 2 docs cho cùng concept = double maintenance.
- User decision required mỗi pattern proposal: pair-or-single. → Q&A friction.
- Cross-reference drift risk khi 1 doc update mà quên update doc kia.

## Mitigations cho costs

- **Drift detection**: `/wiki-eval` có thể check pair docs có cross-reference 2 chiều.
- **Q&A friction**: C8/A8 QA Recommender có thể default suggest PAIR khi pattern có invariant rule clear.
- **Double maintenance**: chỉ apply convention cho concepts thật sự có cả 2 layers — không force-pair mọi pattern.

## Impact

- 3 pairs introduced trong evidence này (P-005↔C-005, P-006↔C-006, future P-008↔contract-future).
- Future pattern/contract proposals trong evidence pipeline phải declare pair-or-single status.
- Patterns/contracts indexed trong `{ws}/patterns-index.md` reflect pair status (cross-reference between sections).

## Why Not Project-Level

Convention applies workspace-wide, KHÔNG project-specific. Future projects trong workspace `wiki` (hoặc workspace khác) đều follow convention này. Workspace-level (`{ws}/decisions/`) is correct scope.

## Related

- Pattern: `../platform/patterns/evidence-state-machine.md` (PAIR example with C-005)
- Contract: `../platform/contracts/evidence-state-machine-transitions.md` (PAIR example with P-005)
- Pattern: `../platform/patterns/citation-rule.md` (PAIR example with C-006)
- Contract: `../platform/contracts/citation-format.md` (PAIR example with P-006)
- Source: q-005, q-006, evidence `2026-05-08-engine-bootstrap-wiki-template`
