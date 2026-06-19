# Governance

contextd governance is local policy-as-code over deterministic task context. It does not call an agent, vector DB, or remote control plane.

## Policy Files

Policy files are optional:

- Workspace policy: `workspaces/{workspace}/policy/context-policy.json`
- Pack policy: `packs/{pack}/policy/context-policy.json`

If no policy exists, `governance_report.status` is `ok` with zero rules evaluated.

## Rule Shape

```json
{
  "rules": [
    {
      "id": "require-contracts-for-engineering",
      "severity": "error",
      "when": {
        "workstream": "engineering"
      },
      "require": {
        "categories": ["contract"]
      },
      "message": "Engineering tasks must include at least one contract."
    }
  ]
}
```

Supported checks:

- `require.categories`, `require.contracts`, `require.docs` or `require.path_globs`
- `deny.categories`, `deny.docs` or `deny.path_globs`
- `deny.max_selected_docs`
- `deny.max_estimated_tokens`

## CLI

```bash
contextd policy-check "debug context quality" --format json
```

`policy-check` builds the normal task context without materializing it, then reports the `governance_report`. Exit codes follow the same convention as `doctor`: `0` clean, `1` error, `2` warning only.

## Runtime Artifact

`contextd context ... --format json` includes optional `governance_report`. Existing consumers can ignore the field.

Governance evaluates the selected context; it does not select new documents and never overrides deterministic contracts, patterns, or pack retrieval.
