# pack-ba — Top 10 Common Pitfalls

Anti-pattern lặp lại với business analysis / requirement / user story. Additive trên [constraints.md](constraints.md).

## P01 — Requirement không testable
- **NG**: "system shall be fast / user-friendly".
- **OK**: "p95 page load meets workspace SLO X under workload Y"; "target flow completion improves from measured baseline A to B".
- **Why**: không verify được = không nghiệm thu được.
- **Detect**: Layer-1 `pack-ba-acceptance-vague-language` + Layer-2 requirement review.
- **Severity**: error

## P02 — Missing acceptance criteria (Gherkin)
- **NG**: user story chỉ "As X I want Y".
- **OK**: kèm acceptance rules/scenarios cho relevant success, edge và failure states; Gherkin dùng khi team/tooling hưởng lợi.
- **Why**: dev đoán requirement → rework.
- **Detect**: Layer-2 — story/requirement thiếu acceptance section hoặc testable rule.
- **Severity**: error

## P03 — Conflate Problem và Solution
- **NG**: requirement viết "build a dropdown to filter".
- **OK**: "user cần filter trên list X theo Y" — solution để design quyết.
- **Why**: lockin solution sớm, miss better option.
- **Detect**: Layer-2 — requirement focus vào outcome.
- **Severity**: error

## P04 — Không trace user role / persona
- **NG**: "user clicks", không biết là role nào.
- **OK**: rõ persona (admin, customer, support); permission tương ứng.
- **Why**: authz miss; UX rối.
- **Detect**: Layer-2 — story có role field.
- **Severity**: warn

## P05 — Thiếu non-functional requirement
- **NG**: chỉ list functional, quên performance/security/compliance.
- **OK**: NFR/risk checklist theo domain; item không áp dụng ghi `N/A` + rationale thay vì copy boilerplate.
- **Why**: build xong không pass audit / SLA.
- **Detect**: Layer-2 — NFR/risk coverage so với task/domain.
- **Severity**: error

## P06 — Magic numbers trong business rule
- **NG**: "auto-suspend after 30 days inactive" — không nói tại sao 30.
- **OK**: nêu source (policy doc/regulation/research); link.
- **Why**: rule arbitrary → khó change/justify.
- **Detect**: Layer-2 — rule có rationale link.
- **Severity**: warn

## P07 — Ambiguous "etc.", "and so on"
- **NG**: "validate email, phone, etc.".
- **OK**: enumerate hết, hoặc nêu rõ "etc = các field optional listed in section X".
- **Why**: scope mơ hồ; dev/QA hiểu khác nhau.
- **Detect**: Layer-2 — ambiguous scope wording review.
- **Severity**: warn

## P08 — Missing edge case enumeration
- **NG**: chỉ happy path.
- **OK**: explicit edge: empty, null, max, concurrent, expired, partial fail.
- **Why**: bug ở boundary phổ biến.
- **Detect**: Layer-2 — story có section Edge Cases.
- **Severity**: warn

## P09 — Không version requirement
- **NG**: doc edit in-place, không history.
- **OK**: version + change log; link ticket.
- **Why**: dispute "feature này đã spec chưa" vô tận.
- **Detect**: Layer-2 — doc có version footer.
- **Severity**: warn

## P10 — Không link source / stakeholder
- **NG**: "user wants X" không nói user nào, ticket nào.
- **OK**: source: interview ID / Linear ticket / Slack thread.
- **Why**: dispute nguồn → revisit từ đầu.
- **Detect**: Layer-2 — requirement có source link.
- **Severity**: info

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 testable | `pack-ba-acceptance-vague-language` | ✓ |
| P02 AC | — | ✓ |
| P03 problem/sol | — | ✓ |
| P04 role | `pack-ba-requirement-missing-actor-or-outcome` (partial) | ✓ |
| P05 NFR | — | ✓ |
| P06 magic | — | ✓ |
| P07 etc | — | ✓ |
| P08 edge | — | ✓ |
| P09 version | — | ✓ |
| P10 source | `pack-ba-stakeholder-missing-owner` (partial) | ✓ |
