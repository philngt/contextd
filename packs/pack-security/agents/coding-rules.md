# pack-security — Coding Rules

Idioms cho security review/design/control. Less strict than constraints — đây là convention.

## Control Framing

- Mô tả control theo **risk lifecycle**: prevention → detection → response.
- Mỗi control: stated control + assumption + failure mode + verification step.
- Reference framework khi áp dụng (NIST 800-53 family, OWASP ASVS level, CIS benchmark).

## Threat Model Format

- STRIDE (Spoofing/Tampering/Repudiation/Info-disclosure/DoS/Elevation) hoặc LINDDUN (privacy) — pick 1, dùng nhất quán per workspace.
- Mỗi threat: actor + entry point + target asset + impact + likelihood + mitigation.
- Data flow diagram: trust boundary đánh dấu rõ; flow băng qua boundary có ô validate.

## Authz Code Idioms

- Policy-based > role-based > attribute-based — tránh inline `if role == "admin"`.
- Default-deny — explicit allow per resource × action.
- Decision log: mỗi authz check có structured log (actor, resource, action, decision, reason).

## Secret Handling Idioms

- Naming convention: `*_SECRET`, `*_KEY`, `*_TOKEN` — pre-commit hook block literal value gán cho biến này.
- Loader pattern: 1 chỗ duy nhất đọc secret từ vault → typed config object; downstream nhận config, KHÔNG đọc trực tiếp.
- Test: mock secret loader, KHÔNG ship real secret vào test fixture (kể cả "looks fake").

## Crypto Idioms

- Wrap crypto primitive trong domain function (`hashPassword(plain)`, `encryptAtRest(blob)`) — caller KHÔNG chọn algorithm.
- Migration path: dual-write window khi xoay algorithm; deprecation log; backfill plan.
- KMS-backed key cho encryption-at-rest; KHÔNG self-managed key file trong repo.

## Logging Idioms

- Structured log (JSON) với schema: timestamp, severity, request_id, actor_id (hash), event_type, ...
- Redact decorator/middleware tự apply theo field name pattern (`password|token|secret|ssn|cc_number|email` mask hoặc hash).
- Trace ID propagate qua mọi service boundary (W3C trace context).

## Remediation Writing

- Remediation note **rõ owner + verification step** + ETA + risk-if-deferred.
- Severity rating dùng CVSS v4.0 vector/score hoặc workspace-approved current framework; priority thêm local threat/environment/business context.
- False positive ghi nhận có evidence + reviewer; không silent dismiss.

## Review Checklist Pattern

- Per-PR security checklist: input validation, authz, secret handling, log redaction, crypto choice, error message shape.
- Threat-model delta: feature mới refresh threat model section nào.
- Backout plan: bật/tắt control như thế nào nếu break production.

---

# Pentest Workflow

## Finding Format

- Format nhất quán: **Context → Reproduction/Evidence → Impact → Risk Rating → Remediation → Verification Step**.
- Ngôn ngữ trung lập, factual; KHÔNG suy đoán khi evidence chưa đủ.
- Tách rõ **observation** (quan sát) vs **conclusion** (suy luận) — giảm false positive.
- Mỗi finding có unique ID (vd `PT-2026-018`) để track xuyên engagement.

## Evidence Handling

- Screenshot redact PII (tên thật, email, CMND, account number) trước khi đưa vào report.
- Request/response sample: mask token, session ID, internal IP — chỉ giữ phần demonstrating vulnerability.
- Artifact lưu vào secure storage với access log; KHÔNG commit raw dump vào repo report.
- Reproduction step PHẢI deterministic: command exact, payload exact, expected output exact.

## Risk Rating

- Với CVSS v4.0, publish vector + score và phân biệt Base, Threat, Environmental, Supplemental context; KHÔNG ad-hoc "high/medium/low".
- Mỗi finding ghi các metric đã chọn và evidence/rationale để reviewer tái lập vector.
- Business impact thêm vào (data loss / availability / compliance / reputational).
- Severity ≠ priority; priority do client quyết theo business context.

## Reproduction Step

- Step-by-step numbered; mỗi step 1 hành động.
- Prerequisite section: account level, network position, tool version.
- Expected vs Actual: rõ ràng "what should happen" vs "what did happen".
- Failure mode: nếu step không lặp lại, document attempt count + variability.

## Remediation Writing (pentest report)

- **Owner + ETA + verification step** bắt buộc cho mỗi finding.
- Remediation đề xuất 2 tier: short-term (mitigation) + long-term (fix).
- Reference: OWASP cheat sheet, CWE ID, vendor advisory, framework doc.
- Retest cycle bám remediation due date/risk policy; document owner, trigger và evidence cần để close.

## Scope Discipline

- Pre-flight check: asset ownership verify, RoE acknowledge, test window confirm.
- Tag mỗi finding với scope item (asset ID, URL, endpoint) — out-of-scope finding flag riêng.
- Network position evidence (source IP, VPN tunnel ID) trong log để chứng minh tuân thủ.

## Report Structure

- Executive summary: 1 page, business-readable, key findings count by severity.
- Methodology: tools used, time spent, coverage matrix (in-scope items × technique).
- Findings: sorted by severity, then by attack chain logic.
- Appendix: tool output, payload list, false-positive disposition log.

## Communication Tone

- Professional, vendor-neutral; không bash framework/team.
- Constructive: mọi finding kèm path forward.
- Acknowledge limitation: time-boxed, scope-limited, không "exhaustive".
