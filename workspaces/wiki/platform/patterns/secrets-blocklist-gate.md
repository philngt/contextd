# Pattern: secrets-blocklist-gate

## Context

Security-critical pattern: mọi command đọc file content nhạy cảm (configs, credentials, ingestion external sources) PHẢI gate qua 5-tier defense. Default state = block-all; opt-in via `--allow-configs` flag.

Companion với `redaction-post-pass.md` (post-read scan). Pattern này áp dụng PRE-read; redaction-post-pass áp dụng POST-read.

## Flow

```
File scope contains config-like file
  ↓
Tier 1: Hard blocklist check
  ↓ pattern match → [HARD-BLOCKED] (NEVER read, no flag bypass)
  ↓ no match
Tier 2: --allow-configs gate
  ↓ flag NOT set → skip (record "configs not read")
  ↓ flag set
Tier 3: AskUserQuestion per-file
  ↓ user select files to include
  ↓ files not selected → [SKIPPED-BY-USER]
Tier 4: Read selected files
  ↓ inline redaction (tokens, passwords, keys, URLs-with-creds)
Tier 5: Workspace override blocklist (add only, no remove)
  ↓
Append guard log to output
```

1. **Tier 1 — Hard blocklist (NEVER READ)**: match patterns `.env`, `*-prod.yaml`, `*.key`, `*.pem`, `*secret*`, `secrets/`, etc. Khớp → ghi `[HARD-BLOCKED: {path}]`, không đọc. KHÔNG có flag bypass.
2. **Tier 2 — User confirm gate**: nếu `--allow-configs` chưa set, skip tất cả còn lại với note "Configs skipped — rerun with --allow-configs". Nếu set, tiếp Tier 3.
3. **Tier 3 — AskUserQuestion per-file group**: list các file còn lại, hỏi user chọn include/skip per-file. File không chọn → `[SKIPPED-BY-USER: {path}]`.
4. **Tier 4 — Read + inline redact**: tokens/passwords/keys → `<REDACTED-SECRET>`; emails → `<REDACTED-EMAIL>`; URLs có credentials inline → `<REDACTED-URL>`.
5. **Tier 5 — Workspace override**: workspace có thể THÊM patterns vào hard blocklist qua `{ws}/evidence/STORAGE.md`. KHÔNG được REMOVE engine entries.

On failure: secret detected post-redaction (Tier 4 escape) → STOP với error `SECRET DETECTED IN SNAPSHOT — fix manually before continue`.

## Default Config

```yaml
# Hard blocklist (NEVER bypass — Tier 1)
hard_blocklist_patterns:
  - ".env"
  - ".env.local"
  - ".env.*.local"
  - "*-prod.yaml"
  - "*-prod.yml"
  - "*-prod.properties"
  - "*-production.yaml"
  - "*-production.yml"
  - "*-production.properties"
  - "*secret*.yaml"
  - "*secret*.yml"
  - "*secret*.properties"
  - "*credential*.yaml"
  - "*credential*.properties"
  - "vault.yaml"
  - "vault.yml"
  - "vault.properties"
  - "*.key"
  - "*.pem"
  - "*.p12"
  - "*.jks"
  - "*.pfx"
  - "*.crt"
  - "*.cer"
  - "secrets/**"
  - "credentials/**"
  - ".ssh/**"
  - ".gnupg/**"
  - "*keystore*"
  - "*truststore*"

# Tier 2 default
allow_configs_flag_required: true        # opt-in only
default_when_flag_unset: skip_all_configs

# Tier 4 redaction patterns (regex)
redaction_patterns:
  - 'password\s*[:=]\s*[^<\s]+'
  - '(token|api[-_]?key|secret|jwt[-_]?key)\s*[:=]\s*[^<\s]+'
  - '[\w.+-]+@[\w-]+\.[\w.-]+'         # email (except README excerpt)
  - 'https?://\w+:\w+@'                 # URL with credentials
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| File matches hard blocklist | Block, record `[HARD-BLOCKED]`, no read |
| `--allow-configs` not set | Skip all, record "Configs skipped" |
| User chọn skip file trong Tier 3 | Record `[SKIPPED-BY-USER]` |
| Secret pattern match post-redaction | STOP với `SECRET DETECTED IN SNAPSHOT` error |
| Workspace override tries REMOVE engine entry | Reject, engine blocklist immutable |

## Implementation Rules

- Hard blocklist KHÔNG có flag bypass — user explicit cũng không thể đọc `.env` hay `*.key`.
- Workspace override CHỈ THÊM, KHÔNG thu hẹp engine blocklist.
- Default state = block-all; flag `--allow-configs` OPT-IN, không bao giờ default true.
- Guard log BẮT BUỘC append cuối Section configs (audit trail).
- Redaction inline (Tier 4) áp dụng cho file content TRƯỚC khi ghi vào snapshot.

## Override Points

- Workspace có thể add patterns vào blocklist qua `{ws}/evidence/STORAGE.md`.
- Workspace có thể add redaction regex patterns (vd custom secret format).
- KHÔNG override: default state (block-all), Tier 2 opt-in flag, hard blocklist immutability.

## Anti-patterns

- ❌ Default `--allow-configs=true` — defeats security model.
- ❌ Skip Tier 3 AskUserQuestion (auto-include all when flag set) — user phải explicit chọn per-file.
- ❌ Read file content trước khi check Tier 1 (vẫn loading bytes vào memory dù sau đó "skip").
- ❌ Workspace remove engine blocklist entries (vd `application.yaml` thoát blocklist) — workspace chỉ ADD.

## Used By

- `/code-analyze` Bước 4.3 `(.claude/commands/code-analyze.md:L207-L229)` — full implementation
- Engine spec: `agents/pipeline/code-snapshot-conventions.md:L156-L251` — Section 6

## Related

- Pattern: `redaction-post-pass.md` (companion — post-read scan)
- Pattern: `askuser-confirm-preview.md` (Tier 3 uses AskUserQuestion)
- Source: q-003, evidence `2026-05-08-engine-bootstrap-wiki-template`
