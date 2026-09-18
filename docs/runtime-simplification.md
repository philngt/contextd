# Runtime/engine simplification

## Commit 1: correctness and export boundaries

The initial runtime-boundary work is preserved as one commit. See
[runtime-boundaries.md](runtime-boundaries.md) for identity migration.

## Commit 2: normalized inputs

`contextd_resolver.resolve_request` owns effective workspace, knowledge root,
pack precedence, path validation and canonical state for task CLI, explain,
MCP and runtime exports. MCP only translates defaults and errors. Explicitly
passing the same workspace name selects workspace pack defaults in every
adapter; omitting it retains project-config replace semantics.

`pack_loader.load_manifest` / `parse_manifest_text` are the public manifest
boundary, including component keywords. The legacy private parser remains an
adapter; the documented YAML subset is not expanded into full YAML. OKF
frontmatter remains a distinct format. Structured metadata is parsed without
prose redaction; exported prose remains redacted.

Legacy configs and v2 packs are accepted at the boundary. No new dependencies,
daemon, cache, plugin registry or runtime manager are introduced.
