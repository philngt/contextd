# Contract: slash-command-naming

## Rule

Slash commands trong `.claude/commands/` PHẢI follow universal naming:

```
/{kebab-case-lowercase}
```

- Filename `.claude/commands/{kebab-case}.md`
- Invocation `/{kebab-case}` (no positional/kwargs trong name itself)
- Multi-word: hyphen separator (`/contextd-setup`, `/evidence-ingest`)

### Recommendation (non-binding)

Cho commands MỚI: prefer "subject-verb" convention cho admin/noun commands (consistency với `evidence-*`, `contextd-*` admin groups). "Verb-subject" pattern acceptable cho action verbs against a subject (`/use-contextd`, `/update-contextd`, `/rebase-contextd`, `/list-workspaces`, `/switch-workspace`, `/new-workspace`) — backward-compat.

| Convention | Example | Group |
|------------|---------|-------|
| subject-verb (PREFERRED for admin/noun) | `/contextd-setup`, `/contextd-detect`, `/evidence-ingest`, `/code-analyze` | contextd-*, evidence-*, code-* |
| verb-subject (acceptable, action verbs) | `/use-contextd`, `/update-contextd`, `/rebase-contextd`, `/list-workspaces`, `/switch-workspace`, `/new-workspace` | wiki actions, workspace ops |

## Observed evidence

19/19 commands conform RULE:
- Workspace ops: `/contextd-setup`, `/contextd-detect`, `/switch-workspace`, `/new-workspace`, `/list-workspaces` `(.claude/commands/README.md:L16-L20)`
- Wiki usage (verb-subject): `/use-contextd`, `/update-contextd`, `/rebase-contextd` `(.claude/commands/README.md:L28-L30)`
- Codebase: `/code-analyze` `(.claude/commands/README.md:L38)`
- Reporting: `/contextd-report` `(.claude/commands/README.md:L48)`
- Observability: `/contextd-trace`, `/contextd-eval`, `/contextd-viz` `(.claude/commands/contextd-viz.md:L1)`
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
