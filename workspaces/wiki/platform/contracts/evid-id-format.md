# Contract: evid-id-format

## Rule

Mọi evidence ID PHẢI follow pattern:
```
{YYYY-MM-DD}-{src}-{slug}[-{n}]
```

- `{YYYY-MM-DD}` — ngày ingest theo timezone của user (ISO date).
- `{src} ∈ {paste, api, mcp, code, engine, platform}`:
  - `paste|api|mcp` — text sources (manual paste, HTTP API fetch, MCP tool result).
  - `code` — single-repo code snapshot (variant=code).
  - `engine` — single-repo agentic-engine snapshot (variant=agentic-engine).
  - `platform` — bundle mode (multi-repo).
- `{slug}` — kebab-case, ≤ 30 ký tự, derive từ `--label` (slugify) hoặc fallback project-name.
- `{-n}` suffix khi trùng entry trong `_index.md` (n = 2, 3, ...).

## Observed evidence

- ✅ Text source: `2026-05-04-paste-PROJ-1234` (`templates/evidence-index.md:L11`)
- ✅ Single-repo code: `2026-05-04-code-surgery-service` (`agents/pipeline/code-snapshot-conventions.md:L50`)
- ✅ Bundle: `2026-05-04-platform-platform-v2` (`agents/pipeline/code-snapshot-conventions.md:L59`)
- ✅ Agentic-engine: `2026-05-08-engine-bootstrap-wiki-template` (this evidence — `workspaces/wiki/evidence/_index.md:L11`)
- ✅ Schema validation: `(templates/evidence-source.yaml:L5)`
- ✅ Definition: `(agents/pipeline/code-snapshot-conventions.md:L40-L62)`

## Counter-examples

_(none detected)_

## Validator behavior

- evid-id KHÔNG match pattern → `/evidence-ingest`/`/code-analyze` STOP với hint format.
- Trùng sha256 (cùng raw.md content) → STOP, reuse evid-id cũ.
- Trùng evid-id (cùng date + src + slug) → append `-{n}` automatic.

## Future src additions

Nếu introduce src mới (vd `--source ticket` cho Jira), update:
1. Contract này — extend `{src}` enum + bump version.
2. `templates/evidence-source.yaml` enum.
3. ADR documenting reason cho new src.
4. Slash commands acceptance.

## Related

- Pattern: `../patterns/evidence-state-machine.md` (state machine consumes evid-id)
- Contract: `evidence-file-layout.md` (layout uses evid-id as dir name)
- Contract: `source-yaml-schema.md` (source.yaml#evid_id field)
- Source: q-009, evidence `2026-05-08-engine-bootstrap-wiki-template`
