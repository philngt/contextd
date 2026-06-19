# Contract: source-yaml-schema

## Rule

`source.yaml` PHẢI có required fields. Conditional fields cho `source_type=code` và bundle mode. Non-code evidence may add optional classification fields for first-class product, BA, QC, design, security, ops, and domain-research context.

### Always-required (mọi source_type)

```yaml
evid_id: "{C-001 evid-id-format}"
source_type: "paste|api|mcp|code|document|interview|ticket|analytics|regulation|design|incident"
origin: "{description-with-source-pointer}"
label: "{≤ 30-char human-readable}"
fetched_at: "{ISO8601 với timezone}"
fetched_by: "{email user}"
sha256: "{SHA256 của raw.{ext}}"
raw_filename: "raw.{ext}"
raw_size_bytes: {integer}
normalized: {bool}                # true nếu có raw.normalized.md
workspace_at_ingest: "{name}"     # CRITICAL — invariant I-2 lock
```

### Conditional: `source_type=code`

```yaml
code_variant: "code|agentic-engine"   # default omitted → "code"
git_sha: "{full 40-char SHA hoặc 'unmanaged-{sha256-tree}'}"
git_branch: "{branch hoặc 'unmanaged'}"
code_scope: ["{glob}", ...]
code_repo_path: "{path}"
```

### Conditional: bundle mode (single-repo các field trên = null)

```yaml
code_repos:
  - name: "{repo-name}"
    path: "{absolute-path}"
    role: "framework|shared-lib|application|sample|plugin|engine"
    variant: "code|agentic-engine"   # per-repo discriminator
    git_sha: "{full SHA hoặc unmanaged-{...}}"
    git_branch: "{branch}"
    scope: ["{glob}", ...]
include_docs:                         # optional bundle docs
  - path: "{path}"
    type: "architecture|openapi|confluence-export|readme|other"
    label: "{≤ 30-char}"
```

### Optional (informational)

```yaml
evidence_kind: "requirement|decision|metric|policy|workflow|bug|risk|research|customer_signal"
audience: "engineering|product|ba|qc|security|design|ops"
confidence: "low|medium|high"
review_by: "{ISO8601 date}"
related_files: ["{ws}/path/...", ...]
related_domains: ["{name}", ...]
related_projects: ["{name}", ...]
notes: |
  Multi-line free text.
```

## Invariants

- `workspace_at_ingest` immutable — apply phải khớp active workspace (I-2).
- `sha256` immutable — match raw.{ext} content exactly.
- `evid_id` match dir name.
- `source_type=code` mà `git_sha` null → V-02 reject.
- Non-code `source_type` values MUST NOT require code-specific fields.
- `code_variant` field default omitted → treat as `code` (backward-compat).

## Observed evidence

- ✅ Template definition: `(templates/evidence-source.yaml:L1-L54)`
- ✅ This evidence source.yaml: `(workspaces/default/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/source.yaml:L1-L40)` — has all required + code-specific fields
- ✅ Validator V-02: `(agents/pipeline/code-snapshot-conventions.md:L271-L279)`

## Counter-examples

_(none detected)_

## Validator behavior

- Missing required field → reject ingest.
- `workspace_at_ingest ≠ active` lúc apply → cross-workspace violation STOP.
- `git_sha` null khi `source_type=code` → V-02 reject.
- Invalid optional enum (`evidence_kind`, `audience`, `confidence`) → warn or reject before apply, depending on command strictness.
- `sha256` không match raw content (calculated) → I-1 violation, audit log.

## Future evolution

Khi conditional grow phức tạp (5+ variant-specific fields), revisit tách C-004a (code-specific schema) thành contract riêng. Hiện tại code-specific fields vẫn conditional; non-code classification fields are optional and backward-compatible.

## Related

- Contract: `evid-id-format.md`
- Contract: `evidence-file-layout.md`
- Contract: `evidence-state-machine-transitions.md` (workspace_at_ingest used by I-2 lock)
- Source: q-012, evidence `2026-05-08-engine-bootstrap-wiki-template`
