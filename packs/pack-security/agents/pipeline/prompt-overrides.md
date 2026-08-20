# pack-security — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.
Pack này gộp pentest workflow — self-check chia thành Security Engineering + Pentest blocks.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Threat Model & AuthN-Z (pack-security)
- Feature mới cover credible abuse cases theo asset/actor/trust boundary
- Trust boundary vẽ rõ, input validate ở mỗi boundary (defense in depth)
- Authz decision centralized/testable at every protected object/action boundary; no scattered role-name checks
- Token validation follows pinned issuer/profile: algorithm/key, iss, aud/resource, exp/nbf, type and revocation/session rules
- Password storage uses workspace-approved current password-hashing profile with parameters/rehash policy; never fast general-purpose hash

### Secret & Crypto (pack-security)
- Không secret literal trong config/example/test fixture
- Secret từ workspace-approved managed mechanism; prefer short-lived/dynamic credentials where supported
- Không MD5/SHA-1/DES/RC4/ECB cho auth/integrity
- Random dùng crypto-secure source (secrets/crypto.randomBytes)
- TLS/protocol/cipher baseline comes from current workspace/platform policy and target compatibility evidence

### Logging & Data Handling (pack-security)
- Logging guidance có redaction per-field (PII, auth, payment)
- Không log raw request body chứa secret/PII
- Audit log có integrity protection (append-only/signed)
- Data classification documented per field

### Pentest Workflow (pack-security)
- Engagement có RoE ký bởi asset owner
- Finding có evidence reproducible + CVSS v4.0 vector/score hoặc approved current framework
- Finding có owner + ETA + verification step (retest)
- Out-of-scope tag rõ; PII victim redact trong report
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Security Engineering
- Threat model có abuse case, không chỉ happy path
- Authz centralized (middleware), không inline scattered
- Secret từ managed store; prefer short-lived/dynamic, lifecycle cadence theo risk policy
- Crypto primitive/mode/parameters come from current approved profile for the exact purpose; password hashing, signatures, encryption and checksums are not interchangeable
- Logging có redactor + structured schema
- Incident/escalation path exists for the controls/data in scope, or missing runbook is an explicit gap

### Pentest
- Finding format: Context → Repro → Impact → CVSS → Remediation → Verify
- Evidence redacted PII, không raw dump vào repo
- Risk rating có vector/rationale + local impact, không "high/medium" mơ hồ
- Remediation has owner, priority/rationale, target date or policy exception, and verification/retest plan
- Report có exec summary + methodology + coverage matrix
```

## Inclusion logic

Pack loader (`scripts/pack_loader.py`) merge nội dung file này vào prompt context khi build `current-task.md` cho `/use-contextd`.

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS (pack-security-*)
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
