# Pattern: citation-rule

> PAIR pattern của contract `../contracts/citation-format.md`. Pattern describes implementation skeleton (path format + variants); contract describes invariants + validator behavior.

## Context

Mọi analysis output / snapshot / report PHẢI cite source để claim → traceable. Citation format consistent across pipeline → analysis tools, validators, downstream commands có thể parse + validate.

Pattern reused trong mọi raw.md, analysis files (cXX, aXX, NN), QA recommendations, manifests.

## Flow

```
Author writes claim
  ↓
Append citation theo format
  ↓ {path}:L<start>[-L<end>]    ← code reference
  ↓ raw.md#section-N            ← snapshot section
  ↓ {ws}/path/file.md#section   ← wiki reference
  ↓ {repo}/path:L..-L..         ← bundle mode
  ↓
Validator scan
  ↓ no citation → mark [NO-CITE] + warn
  ↓ path absolute / cwd-relative → reject
  ↓ path outside scope → reject
  ↓ path cross-workspace → reject
```

1. **Author** (analysis prompt / snapshot builder) appends citation immediately after claim.
2. **Format selection** dựa vào type:
   - Code reference: `({path}:L<start>-L<end>)` relative tới repo root.
   - Snapshot section: `(raw.md#section-N)`.
   - Snapshot line range: `(raw.md#L<start>-L<end>)`.
   - Wiki reference: `({ws}/path/to/file.md#section)`.
   - Bundle (multi-repo): `({repo-name}/{path}:L..-L..)`.
3. **Validator** (theo `validator-rules.md`) scan output:
   - Claim không có citation → re-prompt 1 lần với reminder "missing citations".
   - Persistent miss → mark `[NO-CITE]` + warn user.
4. **Path safety check**:
   - Reject absolute paths (vd `/Users/...`, `D:/...`).
   - Reject cwd-relative paths (vd `./foo`).
   - Reject paths outside `code_scope` của source.yaml.
   - Reject paths workspace khác `workspace_at_ingest`.

On failure: validator reject → analysis output rejected, re-prompt.

## Default Config

```yaml
# Citation format definitions
formats:
  code_ref: "({path}:L<start>[-L<end>])"
  snapshot_section: "(raw.md#section-N)"
  snapshot_line: "(raw.md#L<start>-L<end>)"
  wiki_ref: "({ws}/path/to/file.md#section)"
  bundle_ref: "({repo-name}/{path}:L<start>-L<end>)"

# Path rules
path_relative_to: "repo_root"                # NOT absolute, NOT cwd-relative
line_range_format: "L<start>[-L<end>]"

# Validator behavior
re_prompt_on_missing: true
re_prompt_max_attempts: 1                    # 1 retry, then mark [NO-CITE]
mark_no_cite: "[NO-CITE]"
warn_on_no_cite: true
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| Claim không có citation | Re-prompt 1 lần với reminder; vẫn thiếu → `[NO-CITE]` + warn |
| Path absolute | Reject, hint convert to repo-relative |
| Path cwd-relative | Reject |
| Path outside `code_scope` | Reject |
| Path workspace khác | Reject với cross-workspace violation message |
| Bundle mode missing repo prefix | Reject, hint add `{repo-name}/` prefix |

## Implementation Rules

- PATH RELATIVE TO REPO ROOT — KHÔNG absolute, KHÔNG cwd-relative.
- Single line: `L42`. Range: `L42-L58`. Hyphen separator.
- Anchor `#section-N` cho raw.md sections; `#heading-slug` cho markdown sub-section.
- Mỗi claim PHẢI có citation. KHÔNG cho phép unsupported assertion.
- Bundle mode: prefix `{repo-name}/` để disambiguate.

## Override Points

- Workspace có thể add citation format variants (vd cho file types khác như `.proto`, `.sql`).
- KHÔNG override: path safety rules (relative-to-repo-root, no absolute).

## Anti-patterns

- ❌ Vague citation: `(file:42)` (no path), `(line 42)` (no path).
- ❌ Absolute path: `(/Users/me/repo/foo.java:42)`.
- ❌ Cwd-relative: `(./foo.java:42)`.
- ❌ Multi-claim single citation: "X, Y, Z (file.md)" → mỗi claim PHẢI có citation riêng.
- ❌ Cite path không tồn tại tại snapshot time (path đã rename/move sau ingest).

## Used By

- All analysis prompts (cXX, aXX, NN-) — `agents/pipeline/code-analysis-prompts.md`, `agents/pipeline/critical-analysis-prompts.md`.
- All snapshot templates — `templates/code-snapshot.md`, `templates/agentic-engine-snapshot.md`.
- QA recommendations — `templates/evidence-qa-recommendations.md`.
- Validator — `agents/pipeline/validator-rules.md` (V-04 cite consistency).

## Related

- Contract: `../contracts/citation-format.md` (PAIR — invariant rules + validator)
- Engine spec: `agents/pipeline/code-snapshot-conventions.md` Section 5
- Source: q-006, evidence `2026-05-08-engine-bootstrap-wiki-template`
