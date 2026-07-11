# Pack Validation

Pack validation checks whether packs expose a stable API to the context engine.

## What Is Validated

`contextd pack-validate` checks:

- `packs/{pack}/pack.yaml` exists and declares `name`, `version`, and `components`
- `pack.yaml#name` matches the directory name
- pack identifiers are safe single path segments before any `packs/{pack}` path is built
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

## Path and Symlink Model

Pack paths have both a logical spelling and a canonical filesystem target:

1. Validate the pack identifier as a single safe path segment.
2. Require both `packs/` and `packs/{pack}` to be real non-aliased directories under the canonical knowledge root.
3. Resolve every declared file, retrieval-map target, glob result, and symlink before reading it.
4. Reject anything whose canonical target leaves the active pack root (or the explicitly allowed active workspace/templates root).
5. Record accepted files as normalized, knowledge-root-relative POSIX provenance.

The configured `knowledge_root` may itself be a symlink alias. That alias names the trust root; it does not permit `packs/`, a named pack root, or a declared executable file to be a symlink/junction alias. Invalid or missing active packs invalidate the effective state rather than being silently dropped or reinterpreted as paths. The active-pack result is shared by CLI and MCP adapters.

## Authoring Guidance

Keep retrieval-map entries relative to the active workspace unless the entry intentionally starts with `packs/{active-pack}/` or `templates/`. Do not use absolute paths, URI/drive prefixes, backslashes, `.`/`..` segments, direct `workspaces/{other}/...` references, or another pack's root. Missing required pack docs should fail validation or become explicit context gaps, never implicit guesses.
