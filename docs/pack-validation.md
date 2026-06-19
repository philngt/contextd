# Pack Validation

Pack validation checks whether packs expose a stable API to the context engine.

## What Is Validated

`contextd pack-validate` checks:

- `packs/{pack}/pack.yaml` exists and declares `name`, `version`, and `components`
- `pack.yaml#name` matches the directory name
- component names are unique
- `keywords` only reference declared components
- declared files are relative and exist when listed
- `conflicts_with` references known packs
- `agents/pipeline/retrieval-map.md` rows match declared components
- retrieval-map paths are safe: no absolute paths, parent traversal, cross-workspace reads, or cross-pack reads

The retrieval map is Markdown for humans, but validation treats each table row as a normalized `{component, docs[]}` record. The companion schema `templates/retrieval-map.schema.json` documents that normalized shape.

## CLI

```bash
contextd pack-validate --all --format json
contextd pack-validate --pack pack-product --format text
```

Exit codes:

- `0`: no issues
- `1`: one or more errors
- `2`: warnings only

`contextd doctor` includes the active-pack validation summary so users can catch broken pack APIs before generating task context.

## Authoring Guidance

Keep retrieval-map entries relative to the active workspace unless the entry intentionally starts with `packs/{active-pack}/` or `templates/`. Missing required pack docs should fail validation or become explicit context gaps, never implicit guesses.
