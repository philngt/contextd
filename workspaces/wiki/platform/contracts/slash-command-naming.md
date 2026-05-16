# Contract: slash-command-naming

## Rule

Slash commands trong `.claude/commands/` PHẢI follow universal naming:

```
/{kebab-case-lowercase}
```

- Filename `.claude/commands/{kebab-case}.md`
- Invocation `/{kebab-case}` (no positional/kwargs trong name itself)
- Multi-word: hyphen separator (`/wiki-setup`, `/evidence-ingest`)

### Recommendation (non-binding)

Cho commands MỚI: prefer "subject-verb" convention (consistency với `evidence-*`, `wiki-*` groups). Existing commands "verb-subject" pattern (`/list-workspaces`, `/switch-workspace`, `/new-workspace`) KHÔNG cần break — backward-compat.

| Convention | Example | Group |
|------------|---------|-------|
| subject-verb (PREFERRED for new) | `/wiki-setup`, `/wiki-detect`, `/evidence-ingest`, `/code-analyze` | wiki-*, evidence-*, code-* |
| verb-subject (acceptable, existing) | `/list-workspaces`, `/switch-workspace`, `/new-workspace` | workspace ops |

## Observed evidence

19/19 commands conform RULE:
- Workspace ops: `/wiki-setup`, `/wiki-detect`, `/switch-workspace`, `/new-workspace`, `/list-workspaces` `(.claude/commands/README.md:L16-L20)`
- Wiki usage: `/use-wiki`, `/update-wiki`, `/rebase-wiki` `(.claude/commands/README.md:L28-L30)`
- Codebase: `/code-analyze` `(.claude/commands/README.md:L38)`
- Reporting: `/wiki-report` `(.claude/commands/README.md:L48)`
- Observability: `/wiki-trace`, `/wiki-eval`, `/wiki-viz` `(.claude/commands/wiki-viz.md:L1)`
- Evidence: `/evidence-ingest`, `/obsidian-ingest`, `/evidence-analyze`, `/evidence-qa`, `/evidence-apply` `(.claude/commands/README.md:L72-L76)`

## Counter-examples

_(none — 19/19 conform)_

## Validator behavior

- Filename không kebab-case lowercase → reject by linter.
- Convention recommendation non-binding — không reject "verb-subject" cho commands mới, chỉ warn.

## Note

`/obsidian-ingest` is convention-compliant (subject-verb pattern), even though filename starts with proper noun. Pattern: `{integration-name}-{verb}` cho integration-specific commands.

## Related

- Contract: `sub-agent-frontmatter-schema.md` (sub-agent naming uses similar kebab-case convention)
- Source: q-013, evidence `2026-05-08-engine-bootstrap-wiki-template`
