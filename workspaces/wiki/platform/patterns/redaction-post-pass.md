# Pattern: redaction-post-pass

## Context

Companion pattern với `secrets-blocklist-gate.md`. Post-build scan để catch secrets có thể leak qua các kênh không được anticipate (vd commit messages, docstrings, comments).

Apply cho mọi output có khả năng chứa secrets: snapshots, logs, qa exports, reports, analysis files.

## Flow

```
Output file built (raw.md, log, report, etc.)
  ↓
Scan với regex patterns
  ↓ no match
  ↓
Replace matches → REDACTED placeholders
  ↓
Re-scan post-replace
  ↓ still match → STOP error
  ↓ clean
Write file
```

1. **Build output** — file vừa được build (snapshot, analysis, report).
2. **Scan toàn file** với 4 regex patterns (xem Default Config).
3. **Replace** matches bằng `<REDACTED-{TYPE}>` placeholder.
4. **Re-scan post-replace** — nếu VẪN còn match (edge case không bắt được lần đầu) → STOP với error `SECRET DETECTED IN SNAPSHOT — fix manually before continue`.
5. **Write** file chỉ khi scan clean.

On failure: STOP-on-secret = irreversible. KHÔNG ghi file output nếu còn match. User phải manual edit input source rồi rerun.

## Default Config

```yaml
# Regex patterns (order matters — most specific first)
patterns:
  - regex: 'password\s*[:=]\s*[^<\s]+'
    replacement: '<REDACTED-SECRET>'
  - regex: '(token|api[-_]?key|secret|jwt[-_]?key)\s*[:=]\s*[^<\s]+'
    replacement: '<REDACTED-SECRET>'
  - regex: '[\w.+-]+@[\w-]+\.[\w.-]+'
    replacement: '<REDACTED-EMAIL>'
    except_section: "section-1"             # README excerpt cho phép email (intentional)
  - regex: 'https?://\w+:\w+@'
    replacement: '<REDACTED-URL>'

# Behavior
stop_on_residual_match: true               # post-replace scan thấy match → STOP
write_only_when_clean: true                # KHÔNG ghi file nếu scan dirty
audit_log_residual_matches: true           # log path + line number cho debug
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| Regex match found (first pass) | Replace với `<REDACTED-{TYPE}>` |
| Match still found after replace | STOP với `SECRET DETECTED IN SNAPSHOT — fix manually before continue` |
| File too large to scan inline | Stream-scan, abort on first residual match |
| Email trong Section 1 README excerpt | Allow (except_section rule) |

## Implementation Rules

- Scan PHẢI chạy SAU khi build (KHÔNG in-place during build — patterns có thể đan xen).
- STOP-on-secret = irreversible: KHÔNG ghi file output nếu residual match. Tốt hơn no-output than leak-output.
- Pattern coverage minimum: password, token/api-key/secret/jwt-key, email, URL-with-creds.
- `except_section` rule chỉ apply cho email trong README excerpt — KHÔNG bypass cho other types.

## Override Points

- Workspace có thể ADD regex patterns (vd custom secret format `MYCO_KEY_*`).
- Workspace có thể ADD `except_section` rules (vd allow internal hostname trong specific section).
- KHÔNG override: STOP-on-secret behavior, write_only_when_clean.

## Anti-patterns

- ❌ Run redaction trong-line during build — patterns đan xen, miss cross-line secrets.
- ❌ Continue write file even if residual match (vd "warn but write") — defeat security.
- ❌ Skip post-replace re-scan — first pass có thể miss complex patterns.
- ❌ Whitelist file extensions (vd skip `.md` because "docs are safe") — secrets lẫn vào docstrings/comments.

## Used By

- `/code-analyze` Bước 4.10 `(.claude/commands/code-analyze.md:L274-L282)` — implementation
- Engine spec: `agents/pipeline/code-snapshot-conventions.md:L218-L238` — Section 6.2 redaction rules

## Related

- Pattern: `secrets-blocklist-gate.md` (companion — pre-read gate)
- Source: q-004, evidence `2026-05-08-engine-bootstrap-wiki-template`
