# Runbook: Context Artifact Generation Failure

## Symptom

`contextd context "..."` fails, emits blocking gaps, omits expected contracts/patterns, or returns an artifact that does not satisfy `contextd_task_context.v1`.

## Likely Causes

1. Active workspace cannot be resolved.
2. Required contract or pattern is missing from the active workspace.
3. `contract-index.json` maps an id to a missing file.
4. Context slicing fails to find a relevant section and records a gap.

## Diagnosis Steps

```bash
# Build artifact without writing runtime files.
python3 -m scripts.cli context "debug config resolution" --format json --no-materialize

# Inspect the artifact shape and gaps.
python3 - <<'PY'
import json, subprocess
raw = subprocess.check_output(["python3", "-m", "scripts.cli", "context", "debug config resolution", "--format", "json", "--no-materialize"])
doc = json.loads(raw)
print(doc["artifact_type"])
print(json.dumps(doc.get("gaps", []), indent=2))
print(json.dumps(doc.get("referenced_docs", []), indent=2))
PY

# Resolve a suspected contract id.
python3 -m scripts.cli contract-path <contract-id> --format json
```

Key signals to look for:
- `artifact_type` must be `contextd_task_context.v1`.
- Missing contract/pattern must appear in `gaps[]`; it must not be guessed.
- `referenced_docs[]` should not leave the active workspace except engine and active-pack baseline docs.

## Fix

| Cause | Fix |
|-------|-----|
| Resolver failure | Follow [config-resolution-failure.md](./config-resolution-failure.md). |
| Missing pattern/contract | Add the doc under `workspaces/{workspace}/platform/` and update `patterns-index.md` or `contract-index.json`. |
| Bad `contract-index.json` path | Correct the mapping or remove the stale id so filename-stem fallback can work. |
| Slicing gap | Add headings/sections matching the task intent or update context filter rules. |

## Verification

```bash
python3 -m scripts.cli context "debug config resolution" --format json --no-materialize
python3 -m scripts.cli contract-path <contract-id> --format json
```

`gaps[]` should be empty for the fixed reference, or contain only non-blocking gaps with explicit reasons.

## Escalation

Escalate if the artifact passes shape checks but the markdown render diverges from the JSON. Include both `.contextd/context/current-task.json` and `.contextd/context/current-task.md`.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Task context schema](../../../templates/task-context.schema.json)
- [Context filter rules](../../../agents/pipeline/context-filter.md)
- [Workspace resolve step 0](../platform/patterns/workspace-resolve-step0.md)
- [Runtime adapter drift](./runtime-adapter-drift.md)
