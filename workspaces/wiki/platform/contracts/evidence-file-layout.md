# Contract: evidence-file-layout

## Rule

Mỗi evidence set PHẢI follow file layout invariant:

```
{ws}/evidence/sources/{evid-id}/
  ├── source.yaml          # REQUIRED — schema theo contract source-yaml-schema.md
  ├── raw.{ext}            # REQUIRED — ext ∈ {md, json, html, txt}; với source_type=code: luôn .md
  └── raw.normalized.md    # CONDITIONAL — auto-tạo nếu raw.{ext} > 50KB; chunked theo Section heading
```

Sub-paths:
```
{ws}/evidence/analysis/{evid-id}/{NN-name.md|cNN-name.md|aNN-name.md}
{ws}/evidence/qa/{evid-id}/{recommendations.md, batches/, todo.json, verified-facts.md, pending-external.md?}
{ws}/evidence/applied/{evid-id}/{checkpoint.json, manifest.yaml, diff-summary.md}
{ws}/evidence/_index.md   # SINGLE SOURCE OF TRUTH cho state
```

## Invariants

- **Immutability (I-1)**: `sources/{id}/raw.*` và `source.yaml` immutable sau ingest. KHÔNG sửa raw evidence.
- **`_index.md` as SoT**: state lưu duy nhất ở Active table của `_index.md`. KHÔNG duplicate state ở source.yaml.
- **Per-evid-id isolation**: mỗi evid-id có thư mục riêng dưới `sources/`, `analysis/`, `qa/`, `applied/`.
- **Workspace isolation (I-2)**: KHÔNG có evid-id nằm ngoài `{ws}/evidence/`.

## Observed evidence

- ✅ Layout spec: `(agents/pipeline/code-snapshot-conventions.md:L25-L34)`
- ✅ Engine-level rules: `(agents/pipeline/raw-storage-conventions.md:L1)`
- ✅ Index template: `(templates/evidence-index.md:L1)`
- ✅ This evidence layout: `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md:L1)`, `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/source.yaml:L1)`

## Counter-examples

_(none detected)_

## Validator behavior

- Missing `source.yaml` hoặc `raw.{ext}` → STOP ingest.
- raw.{ext} > 50KB không có raw.normalized.md → auto-generate.
- raw.{ext} > 200KB (single-repo) hoặc > 300KB (bundle) → STOP, hint narrow scope.
- Modify raw.* sau ingest → I-1 violation, audit log + STOP.

## Related

- Contract: `evid-id-format.md` (evid-id used as dir name)
- Contract: `source-yaml-schema.md` (source.yaml schema)
- Contract: `evidence-state-machine-transitions.md` (`_index.md` as SoT)
- Engine spec: `agents/pipeline/raw-storage-conventions.md`
- Source: q-010, evidence `2026-05-08-engine-bootstrap-wiki-template`
