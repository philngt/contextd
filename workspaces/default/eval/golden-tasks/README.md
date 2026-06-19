# Golden Tasks

Golden tasks define expected context selection behavior for this workspace.

Use them when changing:

- pack keywords
- pack retrieval maps
- workspace contracts, patterns, runbooks, or evidence summaries
- context budgeting and category priority
- policy-as-code rules

Run:

```bash
contextd eval --golden --workspace default --format json
```

Store generated reports in `.contextd/runs/` or another ignored runtime path.
