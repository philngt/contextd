# pack-product — Top 10 Common Pitfalls

Anti-pattern lặp lại với product brief / OKR / roadmap / PRD. Additive trên [constraints.md](constraints.md).

## P01 — Brief thiếu Problem / Metric / Acceptance
- **NG**: brief chỉ mô tả feature, không nêu vấn đề + cách đo thành công.
- **OK**: Problem statement → Metric (baseline + target) → Acceptance criteria.
- **Why**: build xong không biết thành/bại.
- **Detect**: Layer-1 `pack-product-brief-missing-problem`, `pack-product-brief-missing-metric`, and `pack-product-brief-missing-acceptance`.
- **Severity**: error

## P02 — OKR Key Result không measurable
- **NG**: KR "improve UX", "make faster".
- **OK**: "p95 page load < 2s by Q3"; "NPS từ 30 → 45".
- **Why**: KR không đo = OKR vô nghĩa.
- **Detect**: Layer-1 `pack-product-okr-missing-number`; deadline/unit semantics cần Layer-2 review.
- **Severity**: error

## P03 — Jargon kỹ thuật trong product doc
- **NG**: "use Redis pub/sub for event fanout".
- **OK**: nói nhu cầu user; implementation để eng chốt.
- **Why**: lock decision sai layer; stakeholder không hiểu.
- **Detect**: Layer-1 `pack-product-jargon-leak` + Layer-2 context review.
- **Severity**: warn

## P04 — Brief dictate implementation
- **NG**: "build a REST API with Postgres".
- **OK**: "expose data X để mobile sync offline" — let eng chose stack.
- **Why**: PM lockin tech mà không có context engineering.
- **Detect**: Layer-1 `pack-product-brief-dictates-impl` + Layer-2 constraint-vs-solution review.
- **Severity**: error

## P05 — Roadmap dùng date mơ hồ
- **NG**: "soon", "Q2-ish", "TBD".
- **OK**: target month (commit) + confidence level.
- **Why**: stakeholder không plan được; trust break.
- **Detect**: Layer-1 `pack-product-roadmap-vague-date`.
- **Severity**: warn

## P06 — Persona generic ("user")
- **NG**: "user wants to ...".
- **OK**: evidence-backed role/context/JTBD; chỉ tạo số persona cần để giải thích materially different needs.
- **Why**: thiết kế cho ai cũng = không cho ai.
- **Detect**: Layer-2 — brief có persona section.
- **Severity**: warn

## P07 — Missing success metric baseline
- **NG**: target "increase signup", không nêu hiện tại bao nhiêu.
- **OK**: baseline (giá trị + thời điểm đo + dimension) → target.
- **Why**: không đo delta, claim arbitrary.
- **Detect**: Layer-2 — metric có cả baseline + target.
- **Severity**: error

## P08 — Thiếu non-goals
- **NG**: brief chỉ liệt kê What.
- **OK**: section "Non-goals/Out of scope" nêu các boundary dễ bị hiểu nhầm hoặc gây scope creep.
- **Why**: scope creep; stakeholder mở rộng silent.
- **Detect**: Layer-2 — scope-boundary review.
- **Severity**: warn

## P09 — Thiếu stakeholder list / RACI
- **NG**: không nêu ai approve, ai informed.
- **OK**: RACI hoặc DRI + reviewer + informed list.
- **Why**: launch chậm vì 1 stakeholder veto cuối.
- **Detect**: Layer-2 — brief có RACI/DRI.
- **Severity**: warn

## P10 — Scope creep không revisit
- **NG**: brief original 3 feature, ship 8 mà không update doc.
- **OK**: change log; revisit metric; cắt scope nếu cần.
- **Why**: history mất, retrospective vô ích.
- **Detect**: Layer-2 — brief có change log.
- **Severity**: info

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 PMA | `pack-product-brief-missing-problem`, `pack-product-brief-missing-metric`, `pack-product-brief-missing-acceptance` | ✓ |
| P02 KR | `pack-product-okr-missing-number` | ✓ |
| P03 jargon | `pack-product-jargon-leak` | ✓ |
| P04 dictate | `pack-product-brief-dictates-impl` | ✓ |
| P05 date | `pack-product-roadmap-vague-date` | ✓ |
| P06 persona | — | ✓ |
| P07 baseline | — | ✓ |
| P08 non-goals | — | ✓ |
| P09 RACI | — | ✓ |
| P10 change-log | — | ✓ |
