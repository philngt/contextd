# Service: codebase-analysis

## Purpose

Snapshot metadata codebase (variant=code or agentic-engine) → ingest vào evidence pipeline với `source_type=code` → auto-trigger CORE analysis prompts → sinh proposals patterns/contracts/services/ADRs cho workspace.

## Input

`/code-analyze` slash command với args:

```
--ref {repo-path}         # default: cwd's parent of .claude/wiki.json
--scope {globs}           # comma-separated; default per variant
--bundle {dir}            # multi-repo mode (mutex với --ref)
--label {≤ 30 char}       # human-readable
--variant {code|agentic-engine}   # default: auto-detect
--skip-analyze            # ingest only, no analyze
--allow-configs           # opt-in cho Section 3 configs
--with-drafts             # add ON-DEMAND prompts (cXX/aXX 5-7)
```

## Output

```
{ws}/evidence/sources/{evid-id}/
  ├── source.yaml              # source_type=code, code_variant={variant}
  ├── raw.md                   # 10-section metadata snapshot
  └── raw.normalized.md        # auto if raw.md > 50KB
{ws}/evidence/_index.md        # row appended state=ingested
```

Auto-trigger `/evidence-analyze` (unless `--skip-analyze`) → analysis files dispatched theo variant.

## Flow

Applies platform patterns (5):
- → [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md) (Bước 0)
- → [../../platform/patterns/variant-discriminated-dispatcher.md](../../platform/patterns/variant-discriminated-dispatcher.md) (Bước 1.4 detect + dispatch)
- → [../../platform/patterns/askuser-confirm-preview.md](../../platform/patterns/askuser-confirm-preview.md) (Bước 3 preview)
- → [../../platform/patterns/secrets-blocklist-gate.md](../../platform/patterns/secrets-blocklist-gate.md) (Bước 4.3 config guard)
- → [../../platform/patterns/redaction-post-pass.md](../../platform/patterns/redaction-post-pass.md) (Bước 4.10 secret scan)

```
0. Workspace check
  ↓
1. Resolve repo + variant + scope
  ↓ variant detect (P-008)
2. Detect project name + label + evid-id (per contract evid-id-format)
  ↓
3. Confirm preview (P-002 askuser-confirm)
  ↓ user approves
4. Build snapshot (10 sections per variant template)
  ↓ Section 3 config guard (P-003 secrets-blocklist-gate)
  ↓ Section 4-8 variant-specific extraction
  ↓ 4.10 redaction post-pass (P-004)
5. Compute size + sha256 + write source.yaml
  ↓
6. Update _index.md (state=ingested)
  ↓
7. Trigger /evidence-analyze (variant-specific CORE set)
  ↓
8. Confirm
```

## Config

```yaml
size_threshold:
  single_repo_warn: 50_KB        # auto-create raw.normalized.md
  single_repo_stop: 200_KB       # STOP, hint narrow scope
  bundle_warn: 50_KB
  bundle_stop: 300_KB

variant_detect:
  code_markers_required: 1
  agentic_markers_required: 2
  ambiguous_resolution: ask_user_question

dedup_check: sha256_match → reuse_existing_evid_id
```

## Config Overrides

| Parameter | Platform Default | This Service | Reason |
|-----------|-----------------|--------------|--------|
| _(none — engine-level)_ | | | |

## Failure Handling

| Scenario | Action |
|----------|--------|
| Repo not recognized (no markers) | STOP, hint `--variant` flag |
| Working tree dirty (variant=code) | AskUserQuestion (Continue/Abort) |
| Duplicate sha256 | STOP, reuse existing evid-id |
| `raw.md > 200KB` (single-repo) | STOP, hint narrow `--scope` |
| `raw.md > 300KB` (bundle) | STOP, hint reduce repos hoặc scope |
| Secret detected post-redaction | STOP với `SECRET DETECTED IN SNAPSHOT` |
| `--allow-configs` not set + `settings.json` in scope | Skip configs với note (P-003 Tier 2 default) |
| Bundle + per-repo dirty | Warn per-repo, NOT block bundle |

## Notes

- Single-repo + bundle + agentic-engine = 3 input modes. Bundle dùng `templates/bundle.yaml` staging.
- `/code-analyze` luôn auto-trigger `/evidence-analyze` (full pipeline) trừ khi `--skip-analyze`.
- `--with-drafts` = convenience flag chạy ON-DEMAND prompts c05/c06/c07 (variant=code) hoặc a05/a06/a07 (variant=agentic-engine) sau CORE.

## Related

- Pattern: [../../platform/patterns/workspace-resolve-step0.md](../../platform/patterns/workspace-resolve-step0.md)
- Pattern: [../../platform/patterns/variant-discriminated-dispatcher.md](../../platform/patterns/variant-discriminated-dispatcher.md)
- Pattern: [../../platform/patterns/askuser-confirm-preview.md](../../platform/patterns/askuser-confirm-preview.md)
- Pattern: [../../platform/patterns/secrets-blocklist-gate.md](../../platform/patterns/secrets-blocklist-gate.md)
- Pattern: [../../platform/patterns/redaction-post-pass.md](../../platform/patterns/redaction-post-pass.md)
- Contract: [../../platform/contracts/evid-id-format.md](../../platform/contracts/evid-id-format.md)
- Contract: [../../platform/contracts/raw-md-section-structure.md](../../platform/contracts/raw-md-section-structure.md)
- Contract: [../../platform/contracts/source-yaml-schema.md](../../platform/contracts/source-yaml-schema.md)
- Service: [evidence-pipeline.md](evidence-pipeline.md) (downstream)
- Engine source: `.claude/commands/code-analyze.md`
- Engine spec: `agents/pipeline/code-snapshot-conventions.md`, `agents/pipeline/code-analysis-prompts.md`
- ADR: [../../decisions/001-introduce-agentic-engine-variant.md](../../decisions/001-introduce-agentic-engine-variant.md)
- Source: F-017c, evidence `2026-05-08-engine-bootstrap-wiki-template`
