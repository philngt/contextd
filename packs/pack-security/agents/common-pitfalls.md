# pack-security — Top 10 Common Pitfalls

Anti-pattern lặp lại với security review / threat model / authn-authz. Additive trên [constraints.md](constraints.md).

## P01 — Secret hardcoded trong config / example
- **NG**: `api_key: "sk-real-prod-..."` trong README/config.
- **OK**: placeholder `${API_KEY}`; doc setup env.
- **Why**: leak qua git history vĩnh viễn.
- **Detect**: Layer-1 `pack-security-secrets-in-config` + dedicated secret scanner.
- **Severity**: error

## P02 — Logging guidance thiếu redaction
- **NG**: doc bảo log `request_body` đầy đủ.
- **OK**: kèm redaction rule per field (PII, auth header, payment).
- **Why**: log = data store; chứa PII = compliance fail.
- **Detect**: Layer-2 — logging doc có redact section.
- **Severity**: error

## P03 — Threat model thiếu abuse case
- **NG**: design doc liệt kê happy path, không xét attacker.
- **OK**: cover credible abuse cases derived từ asset, actor, trust boundary và local risk; mỗi case có mitigation/verification.
- **Why**: phát hiện trust-boundary/control gap muộn thường kéo theo redesign, migration và retest rộng hơn.
- **Detect**: Layer-2 — design doc có "Threat / Abuse Cases" section.
- **Severity**: error

## P04 — Authz inline thay vì middleware
- **NG**: `if user.role == "admin"` rải khắp handler.
- **OK**: middleware/decorator/policy engine (OPA/Cedar).
- **Why**: 1 chỗ quên check = bypass; audit khó.
- **Detect**: Layer-2 — review handler có centralized policy.
- **Severity**: error

## P05 — Không có key rotation policy
- **NG**: API key cấp một lần, không hết hạn.
- **OK**: short-lived/dynamic credential khi có thể; otherwise risk-based automated rotation, expiry metadata, alert và immediate revocation path.
- **Why**: leak key sống mãi.
- **Detect**: Layer-2 — security doc có rotation section.
- **Severity**: warn

## P06 — Trust user input ở internal layer
- **NG**: validate ở edge nhưng internal service trust caller.
- **OK**: validate ở mỗi trust boundary; defense in depth.
- **Why**: SSRF, internal lateral attack.
- **Detect**: Layer-2 — service contract có input schema.
- **Severity**: error

## P07 — JWT không verify signature
- **NG**: `jwt.decode(token, verify=False)`.
- **OK**: verify signature + issuer + audience + exp.
- **Why**: forge token trivial.
- **Detect**: Layer-1 `pack-security-jwt-no-verify`.
- **Severity**: error

## P08 — Missing HTTPS-only / HSTS
- **NG**: server listen 80, không redirect; cookie không `Secure`.
- **OK**: HTTPS-only, HSTS header, `Secure; HttpOnly; SameSite` cookie.
- **Why**: MITM, session hijack.
- **Detect**: Layer-2 — config có TLS + cookie flags.
- **Severity**: error

## P09 — Weak crypto (MD5 / SHA1 / DES)
- **NG**: `hashlib.md5(pw)`, `MessageDigest.getInstance("SHA-1")` cho auth.
- **OK**: bcrypt/argon2/scrypt cho password; SHA-256+ cho integrity.
- **Why**: collision/rainbow trivial.
- **Detect**: Layer-1 `pack-security-weak-crypto` (known weak primitive heuristic).
- **Severity**: error

## P10 — Không có incident-response runbook
- **NG**: breach xảy ra mới ngồi nghĩ làm gì.
- **OK**: runbook: detect → contain → eradicate → recover → postmortem; key contacts.
- **Why**: MTTR cao, leak phình to.
- **Detect**: Layer-2 — `{ws}/runbooks/` có incident-response doc.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 secret | `pack-security-secrets-in-config` | ✓ |
| P02 redact | — | ✓ |
| P03 abuse | — | ✓ |
| P04 inline-authz | — | ✓ |
| P05 rotation | — | ✓ |
| P06 trust-internal | — | ✓ |
| P07 jwt-verify | `pack-security-jwt-no-verify` | ✓ |
| P08 https | — | ✓ |
| P09 weak-crypto | `pack-security-weak-crypto` | ✓ |
| P10 IR runbook | — | ✓ |

---

# Pentest Workflow — Top 10 Pitfalls

## PT01 — Thiếu authorization document (Rules of Engagement)
- **NG**: bắt đầu test mà không có RoE/SOW ký bởi target owner.
- **OK**: RoE: scope, time window, contact, allowed techniques, escalation path.
- **Why**: có thể gây thiệt hại, vi phạm hợp đồng hoặc pháp luật áp dụng; legal owner phải xác nhận jurisdiction.
- **Detect**: Layer-2 authorization/RoE gate; static scope rule không chứng minh legal authorization.
- **Severity**: error

## PT02 — Lưu raw credential thực vào repo
- **NG**: commit `dump.txt` chứa hash + plaintext password phục hồi được.
- **OK**: redact victim PII/credential trong artifact; secure storage chỉ recover được khi cần.
- **Why**: pentester thành nguồn breach thứ 2.
- **Detect**: Layer-1 — git scan (gitleaks) trong evidence folder.
- **Severity**: error

## PT03 — Không redact victim PII trong report
- **NG**: screenshot có tên thật, email, CMND trong báo cáo gửi client.
- **OK**: redact field-by-field; hash hoặc placeholder.
- **Why**: report leak → second breach; lawsuit.
- **Detect**: Layer-2 — report review checklist.
- **Severity**: error

## PT04 — Exploit live system khi chưa approve
- **NG**: chạy `sqlmap --dump` lên prod DB chứa data thật.
- **OK**: PoC tối thiểu (1 row, 1 path); destructive test → staging.
- **Why**: data corruption, outage, criminal liability.
- **Detect**: Layer-2 — test log có target env tag.
- **Severity**: error

## PT05 — Không record test window
- **NG**: không log start/end time → alert SOC trigger nhầm prod incident.
- **OK**: test window doc; ping SOC trước/sau; log mọi action với timestamp.
- **Why**: confusion với incident thật, response cost.
- **Detect**: Layer-2 — engagement log có timestamp.
- **Severity**: error

## PT06 — Miss out-of-scope check
- **NG**: scan subdomain rồi attack server thuộc tenant khác.
- **OK**: verify ownership từng asset trước action; halt khi unsure.
- **Why**: hack nhầm bên thứ 3 = liability.
- **Detect**: Layer-2 — asset list verified before scan.
- **Severity**: error

## PT07 — Copy-paste payload không hiểu
- **NG**: chạy exploit script từ GitHub không đọc, embed backdoor.
- **OK**: review code, run in isolated VM, hash-verify source.
- **Why**: backdoor lan vào tester machine, client env.
- **Detect**: Layer-2 — tool provenance doc.
- **Severity**: error

## PT08 — Không document false positive
- **NG**: scanner báo 50 critical, report copy thẳng.
- **OK**: triage; mark FP với evidence; chỉ ship verified finding.
- **Why**: noise report mất uy tín, client ignore real issue.
- **Detect**: Layer-2 — finding có verify status.
- **Severity**: warn

## PT09 — Missing remediation owner / SLA
- **NG**: report "vulnerability X exists", không nói ai fix, bao giờ.
- **OK**: mỗi finding có severity/vector, owner, due date theo risk policy và retest trigger.
- **Why**: finding lưu vĩnh viễn không fix.
- **Detect**: Layer-2 — finding schema có `owner, sla` field.
- **Severity**: warn

## PT10 — Không có retest / regression schedule
- **NG**: 1 lần pentest, không follow-up sau khi client claim fix.
- **OK**: retest theo remediation due date/risk policy; compare evidence và control delta.
- **Why**: "fix" không thực sự fix; regression slip in.
- **Detect**: Layer-2 — engagement plan có retest milestone.
- **Severity**: warn

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| PT01 RoE | — | ✓ |
| PT02 cred-storage | — (gitleaks) | ✓ |
| PT03 PII | — | ✓ |
| PT04 live | — | ✓ |
| PT05 window | — | ✓ |
| PT06 scope | — | ✓ |
| PT07 payload | — | ✓ |
| PT08 FP | — | ✓ |
| PT09 owner | — | ✓ |
| PT10 retest | — | ✓ |
