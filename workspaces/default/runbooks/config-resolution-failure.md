# Runbook: Config Resolution Failure

## Symptom

`contextd resolve`, `contextd context`, `/use-contextd`, or any active-workspace command cannot determine the project config, workspace, or `knowledge_root`.

Common messages include:
- `missing .contextd/config.json`
- `workspace is empty`
- `knowledge_root does not exist`
- warning that canonical and legacy configs disagree

## Likely Causes

1. `<project>/.contextd/config.json` is missing after cloning or migration.
2. `workspace` is empty or points to a workspace directory that does not exist.
3. Relative `knowledge_root` was resolved from the wrong directory.
4. Canonical `.contextd/config.json` and legacy adapters disagree.

## Diagnosis Steps

```bash
# Show the resolver's effective config and warnings.
python3 -m scripts.cli resolve --format json

# Check whether a canonical project config exists.
find . -type f -path '*/.contextd/config.json'

# Preview migration from legacy adapters, if any.
python3 -m scripts.cli migrate-config --dry-run

# List available workspaces from the current knowledge root.
python3 - <<'PY'
import json, subprocess
data = json.loads(subprocess.check_output(["python3", "-m", "scripts.cli", "resolve", "--format", "json"]))
root = data.get("knowledge_root")
print(root)
PY
```

Key signals to look for:
- `warnings[]` mentions legacy disagreement: canonical `.contextd/config.json` wins.
- `workspace` is `null` or empty: active-workspace commands must stop.
- `knowledge_root` is relative but resolves outside the intended project root.

## Fix

| Cause | Fix |
|-------|-----|
| Missing canonical config | Run `python3 -m scripts.cli migrate-config`, `/contextd-setup`, or copy `templates/contextd-config.json` to `<project>/.contextd/config.json`. |
| Empty workspace | Set `workspace` to an existing directory under `workspaces/`, then rerun `contextd resolve`. |
| Bad relative `knowledge_root` | Use an absolute path, or set `knowledge_root` relative to the project root containing `.contextd/config.json`. |
| Canonical/legacy disagreement | Keep canonical `.contextd/config.json`; update or remove legacy adapters during migration. |

## Verification

Resolver and artifact generation should both succeed.

```bash
python3 -m scripts.cli resolve --format json
python3 -m scripts.cli context "debug config resolution" --format json --no-materialize
```

## Escalation

Escalate if `resolve` succeeds but `contextd context` still reads another workspace, or if a legacy adapter silently overrides canonical config. Include the `resolve --format json` output and the project `.contextd/config.json`.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Workspace resolve step 0](../platform/patterns/workspace-resolve-step0.md)
- [Workspace resolution pipeline](../../../agents/pipeline/workspace-resolution.md)
- [Contextd config schema](../../../templates/contextd-config.schema.json)
- [Workspace switch mismatch](./workspace-switch-mismatch.md)
