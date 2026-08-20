# pack-security — Constraints

Hard rules cho security engineering (threat model / authn-authz / secret / crypto / logging) **và** authorized pentest workflow. Additive trên engine constraints. Strict-only direction.

> Pack này gộp `pack-pentest` (v0.1) — phần pentest đặt ở section riêng "Pentest Workflow" bên dưới.

## Threat Model (`pack-security-threat-model`)

- **Security/design doc PHẢI có threat assumptions và credible abuse cases** cho feature chạm data nhạy cảm; coverage dựa trên asset, actor, trust boundary và risk, không quota số lượng tùy ý.
- **Trust boundary PHẢI vẽ rõ** — input từ untrusted source validate ở mỗi boundary (defense in depth).
- **Threat model PHẢI refresh khi đổi authz scope** — không reuse threat model cũ cho feature có data classification khác.

## Authentication & Authorization (`pack-security-authn-authz`)

- **Authz check precedes business logic** — middleware/decorator/policy engine (OPA/Cedar), KHÔNG inline `if user.role == ...`.
- **JWT/session token PHẢI verify signature + issuer + audience + exp** — không có `verify=False`, không `alg=none`.
- **Password storage PHẢI dùng bcrypt/argon2/scrypt** với cost factor phù hợp — KHÔNG MD5/SHA-1/SHA-256 plain.
- **Sensitive endpoint PHẢI có rate limit + audit log** — login/forgot-password/admin action.

## Secret Management (`pack-security-secrets`)

- **KHÔNG hardcode secret** trong config/example/test fixture (literal > 8 char trông như key/token).
- **Secret lifecycle policy PHẢI có** — prefer short-lived/dynamic credentials; rotation/expiry cadence dựa trên secret type, blast radius, provider capability và organization policy; compromised secret phải revoke/rotate ngay.
- **Secret PHẢI từ secret manager** (Vault/AWS SM/sealed-secret), KHÔNG env file commit vào repo.
- **Pre-commit hook PHẢI scan secret** (gitleaks/trufflehog) — block commit có secret leak.

## Crypto (`pack-security-crypto`)

- **KHÔNG dùng weak algorithm** cho auth/integrity: MD5, SHA-1, DES, RC4, ECB mode.
- **TLS profile PHẢI theo current organization-approved baseline** cho client/server và data classification; prefer TLS 1.3, chỉ giữ compatibility protocol/cipher khi policy cho phép và có kế hoạch retire. Không đóng băng minimum/cipher list trong pack.
- **Random PHẢI cryptographically secure** (`secrets`/`crypto.randomBytes`), KHÔNG `Math.random()` / `Random()`.
- **Algorithm/key parameters PHẢI theo current organization-approved cryptographic baseline** và có owner/review date; pack không đóng băng key-size policy có thể lỗi thời.

## Logging & Data Handling (`pack-security-logging-data`)

- **Logging guidance PHẢI nêu redaction cho sensitive data** — PII, auth header, payment field mask field-by-field.
- **KHÔNG log raw request body** chứa secret/PII; chỉ log metadata (length, hash, request ID).
- **Audit log PHẢI có integrity protection** (append-only, signed, hoặc immutable storage) cho compliance trail.
- **Data classification PHẢI document** — PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED với handling rule tương ứng.

## Incident Response (`pack-security-incident-response`)

- **Incident-response runbook PHẢI tồn tại** trong `{ws}/runbooks/`: detect → contain → eradicate → recover → postmortem + key contacts.
- **Notification/escalation deadline PHẢI map tới jurisdiction, contract và incident class hiện hành**; legal/privacy owner duy trì source-of-truth thay vì copy một con số luật vào pack.

---

# Pentest Workflow

Constraints áp dụng cho authorized pentest engagements (active khi workspace có ngữ cảnh testing).

## Authorization & Scope (`pack-security-authorization-scope`)

- **Mọi engagement PHẢI có Rules of Engagement (RoE) ký bởi asset owner** trước khi bắt đầu — scope, time window, contact, allowed technique, escalation path.
- **Mọi artifact PHẢI nêu rõ `in-scope` và `out-of-scope`** — không ambiguous.
- **KHÔNG test recommendation/action vượt ra ngoài ranh giới cho phép** — halt + escalate khi unsure.
- **KHÔNG attack live system khi chưa approve cụ thể cho production** — PoC tối thiểu, destructive test → staging.

## Evidence Integrity (`pack-security-evidence`)

- **Mọi finding PHẢI có evidence tối thiểu** (PoC steps hoặc tool output chứng minh reproducible).
- **Finding không có evidence KHÔNG được kết luận là confirmed vulnerability** — chỉ "potential/suspected".
- **Evidence artifact PHẢI redact PII victim** trước khi đưa vào report — screenshot, log, dump.
- **Raw credential thực KHÔNG được commit vào repo** — secure storage có access log; report dùng masked/hashed sample.

## Actionability (`pack-security-actionability`)

- **Finding PHẢI có CVSS v4.0 vector/score hoặc workspace-approved current framework**, kèm Threat/Environmental context khi có và business impact riêng; không chỉ ghi "high/medium" mơ hồ.
- **Finding PHẢI có remediation guidance + verification step** cho retest — không chỉ "fix the vulnerability".
- **Finding PHẢI có owner + remediation due date** lấy từ workspace risk policy, exploitability, exposure và compensating controls; severity không tự động đồng nghĩa với một SLA cố định.

## Operational Safety (`pack-security-operational-safety`)

- **Test window PHẢI document** (start/end timestamp) + ping SOC trước/sau — tránh confused với incident thật.
- **Destructive technique** (DoS, data wipe, ransomware sim) PHẢI có riêng approval letter + staging-only flag.
- **Tool provenance PHẢI verifiable** — exploit script từ public source phải review code + hash-verify; run trong isolated VM.
- **Exploit chain test PHẢI documented stop condition** — khi nào dừng tránh leo thang ngoài scope.

## Reporting (`pack-security-reporting`)

- **Report PHẢI có executive summary** business-readable + technical detail tách section.
- **False positive PHẢI document có evidence dispose**; không silent dismiss để giữ "clean" report.
- **Methodology section PHẢI nêu tool + version + coverage matrix** (in-scope item × technique tested).

## Knowledge Isolation (pentest) (`pack-security-knowledge-isolation`)

- **KHÔNG dùng pattern/finding từ engagement workspace khác** — data classification + RoE per-client.
- **Retest cycle PHẢI define** theo remediation due date/risk acceptance; finding không có verification evidence vẫn ở trạng thái chưa xác nhận fix.

---

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
