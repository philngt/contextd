# Runbook: Materialized Context Pack Stale

## Symptom

`.contextd/context/current-task.json`, `.contextd/context/current-task.md`, or `.contextd/context/packs/{packKey}.md` looks stale after contracts, patterns, workspace profile, or active packs change.

## Likely Causes

1. Runtime artifacts were not regenerated after static source changes.
2. A contract/pattern changed and `source_hashes` no longer match.
3. Pack override changed but old `packKey` is still being inspected.
4. `.contextd/context/` is ignored, so teammates do not receive local runtime artifacts.

## Diagnosis Steps

```bash
# Generate materialized artifacts.
python3 -m scripts.cli context "debug materialized pack" --format json

# Inspect current pack key and source hashes.
python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".contextd/context/current-task.json")
doc = json.loads(p.read_text())
print(doc.get("contextPack", {}))
print(json.dumps(doc.get("source_hashes", {}), indent=2))
PY

# List materialized pack files.
find .contextd/context -maxdepth 3 -type f | sort
```

Key signals to look for:
- Same static sources should produce the same `packKey`.
- Changing a referenced contract/pattern should change the relevant source hash and usually the pack key.
- Search/RAG snippets, logs, and generated task outputs must not be included in materialized packs.

## Fix

| Cause | Fix |
|-------|-----|
| Stale artifact | Regenerate with `python3 -m scripts.cli context "..." --format json`. |
| Unexpected `packKey` | Compare `workspace`, active packs, referenced contracts/patterns, and `source_hashes`. |
| Source hash mismatch | Verify the changed file is intended, then regenerate artifacts. |
| Teammate missing runtime artifacts | Do not commit `.contextd/context/`; teammates regenerate locally. |

## Verification

```bash
python3 -m scripts.cli context "debug materialized pack" --format json
python3 -m scripts.cli context "debug materialized pack" --format json --no-materialize
```

The materialized run and no-materialize run should produce equivalent JSON semantics. Only filesystem side effects should differ.

## Escalation

Escalate if volatile outputs, logs, generated files, or advisory search snippets appear in `contextPack` or `packs/{packKey}.md`.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Task context schema](../../../templates/task-context.schema.json)
- [Context artifact generation failure](./context-artifact-generation-failure.md)
- [Workspace resolution pipeline](../../../agents/pipeline/workspace-resolution.md)
