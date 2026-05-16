# pack-security — Validator Rules

Layer-1 rule. Prefix `pack-security-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-security-missing-threat-model` | error | Security/design doc thiếu threat assumptions hoặc abuse cases |
| `pack-security-secrets-in-config` | error | Có dấu hiệu secret hardcoded trong config/examples |
| `pack-security-missing-authz-boundary` | warn | Luồng/endpoint nhạy cảm thiếu authz boundary |
| `pack-security-no-logging-redaction` | warn | Logging/security note thiếu redaction guidance |

## Layer-2 self-check

```md
### Security Engineering (pack-security)
- Security/design doc có threat assumptions hoặc abuse cases
- Không hardcode secret trong config/examples
- Luồng/endpoint nhạy cảm có authz boundary
- Logging guidance có redaction/masking cho dữ liệu nhạy cảm
```

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
