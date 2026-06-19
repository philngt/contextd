# Runbook: Team Sync Knowledge Root Failure

## Symptom

`/contextd-team-sync pull|push|status` cannot find the team knowledge repo, reports `knowledge_root is not a git repo`, uses the wrong remote, or fails on pull/push conflicts.

## Likely Causes

1. `~/.contextd/config.json#knowledge_root` points to the engine repo instead of the team knowledge repo.
2. `knowledge_root` is not a git repository or has no remote.
3. Local changes block `git pull --ff-only`.
4. Legacy global fallback is being used and hides the canonical config mistake.

## Diagnosis Steps

```bash
# Resolve global/project config and inspect warnings.
python3 -m scripts.cli resolve --format json

# Check git state of the configured knowledge root.
python3 - <<'PY'
import json, pathlib, subprocess
data = json.loads(subprocess.check_output(["python3", "-m", "scripts.cli", "resolve", "--format", "json"]))
root = pathlib.Path(data["knowledge_root"]).expanduser()
print(root)
subprocess.run(["git", "-C", str(root), "status", "--short"], check=False)
subprocess.run(["git", "-C", str(root), "remote", "-v"], check=False)
PY

# If using the shell helper, check status.
bash scripts/contextd-team-sync.sh status
```

Key signals to look for:
- `knowledge_root` should be the team knowledge repo when team sync is expected.
- `git remote -v` should show the team remote, not the engine-only remote.
- `git status --short` must be clean before fast-forward pull unless the user intends to commit/push.

## Fix

| Cause | Fix |
|-------|-----|
| `knowledge_root` points to engine repo | Edit `~/.contextd/config.json` to the team knowledge repo path. |
| Not a git repo | Clone the team repo, then update `knowledge_root`. |
| Wrong remote | Run `git -C <knowledge_root> remote set-url origin <team-repo-url>`. |
| Pull conflict | Commit/stash local changes or push them before pulling. |
| Legacy fallback confusion | Create/fix `~/.contextd/config.json` and treat legacy globals as migration adapters only. |

## Verification

```bash
python3 -m scripts.cli resolve --format json
bash scripts/contextd-team-sync.sh status
```

The status command should show the expected repo, branch, remote, and workspace changes.

## Escalation

Escalate to the knowledge repo owner if the remote URL is unknown, permissions fail, or two teammates made conflicting edits to the same workspace docs.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Team sync docs](../../../docs/team-sync.md)
- [Config resolution failure](./config-resolution-failure.md)
- [Workspace switch mismatch](./workspace-switch-mismatch.md)
