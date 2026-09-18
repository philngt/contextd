# Runtime boundary simplification (phase 1)

Context compilation remains deterministic and file-backed. This change does
not change task classification, ranking, document quotas or Synapse traversal.

## One compiled source view

`lib/context_payload.py::compiled_sources` is the ordered, static-first,
path-deduplicated view used by pack identity, total-budget accounting and pack
Markdown output. It is a pure function, not a new engine or plugin framework.

Pack identity version 2 binds workspace, enabled packs, source hashes, selected
sections, selected content **in output order**, and the decision report. It
applies to both profiled and unprofiled packs. Different projections of an
unchanged source file can no longer reuse a key just because raw hashes match.

Newly built `contextPack` objects include `identity_version: 2` and `packs`.
Existing outer artifact fields and CLI command names remain unchanged. Pack
keys rotate once after upgrade. Rebuild older artifacts before materializing;
old files remain readable but are not silently republished with obsolete keys.

From the configured project directory, rebuild with the original task and any
original workspace/support flags, for example:

```bash
contextd context "implement demo feature"
```

Read the newly emitted `contextPack.compiledRef` rather than constructing an
old pack path from a cached key. Rebuild through the compiler; do not edit old
hashes or add identity metadata by hand.

## Validation before writes

Materialization checks pack identity and the supplied Synapse snapshot, then
prepares all rendered outputs, including Synapse JSON, before creating
directories or writing any file. Mutating a compiled payload after build is
rejected before writes. Serialization or rendering failures leave existing
artifacts untouched; filesystem failures during publication are a different case.

An optional mismatched Synapse snapshot retains the documented `drifted`
behavior: no new `synapse.json` is written, its reference is cleared, and valid
task artifacts can still be materialized. This is deliberately not a global
transaction. Per-file atomic writes do not guarantee multi-file atomicity or
serialize concurrent writers. Generation directories/current-pointer changes
are outside this PR.

## Runtime adapters versus workspace bundles

The legacy `codex-instructions` export is now a small compiler bootstrap. It
no longer implements its own first-five-documents/800-character selection.
The compatibility output path is not a promise of client auto-discovery.

`plain` remains an explicit whole-workspace bundle with its historical source
inventory. Its workspace, engine and pack reads use the shared boundary and
redaction helper. A v3 pack loads canonical manifest/knowledge rather than
legacy rule files; a v2 pack keeps its compatibility prose. Invalid workspace
overrides, outside-root symlinks, and unsafe pack paths are refused/omitted.
Non-regular sources are rejected before reading, and workspace bundle reads
accept both absolute and relative knowledge roots. The helper is not an OS
sandbox against concurrently hostile filesystem edits.

## Deferred work

Shared CLI/MCP resolved requests, complete all-input snapshots, parser
consolidation, pack-owned workstream policy, total-context budget enforcement
and a separate compiler/output module split remain follow-up changes. No
daemon, persistent cache, runtime manager or workflow orchestrator is added.

## Regression checks

Run `python scripts/test_runtime_boundaries.py` (30 focused regressions), the
existing runtime and decision-context suites, artifact-schema validation, and
the normal CI checks. Existing tests are retained without weakened assertions.
