# pack-security — Prompt Overrides

Section bổ sung vào `agents/pipeline/prompt-template.md` self-check khi pack active.
Pack này gộp pentest workflow — self-check chia thành Security Engineering + Pentest blocks.

## Self-Check Constraints (append vào `Constraints to check` của prompt-template)

```
### Threat Model & AuthN-Z (pack-security)
- Feature mới có abuse case + mitigation (tối thiểu 3 case)
- Trust boundary vẽ rõ, input validate ở mỗi boundary (defense in depth)
- Authz check ở middleware/policy engine, không inline if-role
- JWT verify signature + iss + aud + exp; không alg=none / verify=False
- Password hash bằng bcrypt/argon2/scrypt; không MD5/SHA-1/SHA-256 plain

### Secret & Crypto (pack-security)
- Không secret literal trong config/example/test fixture
- Secret từ secret manager (Vault/AWS SM/sealed-secret)
- Không MD5/SHA-1/DES/RC4/ECB cho auth/integrity
- Random dùng crypto-secure source (secrets/crypto.randomBytes)
- TLS ≥ 1.2 (prefer 1.3); cipher suite từ allow-list current

### Logging & Data Handling (pack-security)
- Logging guidance có redaction per-field (PII, auth, payment)
- Không log raw request body chứa secret/PII
- Audit log có integrity protection (append-only/signed)
- Data classification documented per field

### Pentest Workflow (pack-security)
- Engagement có RoE ký bởi asset owner
- Finding có evidence reproducible + risk rating (CVSS 3.1)
- Finding có owner + ETA + verification step (retest)
- Out-of-scope tag rõ; PII victim redact trong report
```

## Layer-2 LLM self-check (append vào validator-rules Layer 2)

```md
### Security Engineering
- Threat model có abuse case, không chỉ happy path
- Authz centralized (middleware), không inline scattered
- Secret từ vault, rotation cadence ≤ 90 days
- Crypto: SHA-256+ / bcrypt / argon2 / AES-GCM
- Logging có redactor + structured schema
- IR runbook tồn tại trong {ws}/runbooks/

### Pentest
- Finding format: Context → Repro → Impact → CVSS → Remediation → Verify
- Evidence redacted PII, không raw dump vào repo
- Risk rating dùng CVSS 3.1, không "high/medium" mơ hồ
- Remediation 2-tier (short/long-term) + retest schedule
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
