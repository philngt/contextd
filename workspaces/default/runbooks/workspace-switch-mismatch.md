# Runbook: Workspace Switch Mismatch

## Symptom

After `/switch-workspace` or manual config editing, commands still use the old workspace, packs do not match the expected workspace, or generated context references docs from the wrong scope.

## Likely Causes

1. `.contextd/config.json#workspace` was not updated in the current codebase.
2. The target workspace directory or `workspace.md` is missing.
3. Local `packs` array overrides workspace defaults with replace semantics.
4. A stale legacy adapter is being inspected instead of canonical config.

## Diagnosis Steps

```bash
# Confirm the active workspace and resolver source.
python3 -m scripts.cli resolve --format json

# Inspect canonical project config.
python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".contextd/config.json")
print(p.resolve())
print(json.dumps(json.loads(p.read_text()), indent=2))
PY

# Check target workspace profile and default packs.
rg -n "^#|^## Packs|^- " workspaces/*/workspace.md
```

Key signals to look for:
- `config_source` should point at `.contextd/config.json` when it exists.
- `packs: []` or a non-null array in project config replaces workspace defaults.
- `workspaces/{name}/workspace.md` missing means the switch target is invalid.

## Fix

| Cause | Fix |
|-------|-----|
| Wrong `workspace` field | Run `/switch-workspace {name}` or edit `.contextd/config.json#workspace`. |
| Missing workspace directory | Run `/new-workspace {name}` or restore the workspace from the knowledge repo. |
| Pack override mismatch | Set project config `packs` to `null` to follow workspace defaults, or set the exact desired array. |
| Stale legacy adapter | Ignore or migrate the legacy file; canonical `.contextd/config.json` must be updated first. |

## Verification

```bash
python3 -m scripts.cli resolve --format json
python3 -m scripts.cli context "debug workspace switch" --format json --no-materialize
```

The JSON artifact should show the expected `workspace`, `contextPack.active_packs`, and `referenced_docs` scoped to that workspace plus engine/active-pack baseline docs.

## Escalation

Escalate when canonical config is correct but `referenced_docs` includes another workspace. Include the generated context JSON and the `workspace.md` for both workspaces.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Config resolution failure](./config-resolution-failure.md)
- [Workspace resolve step 0](../platform/patterns/workspace-resolve-step0.md)
- [Workspace resolution pipeline](../../../agents/pipeline/workspace-resolution.md)
