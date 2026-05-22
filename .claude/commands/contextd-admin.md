# /contextd-admin — Admin & Diagnostics Index

Single entry point that explains the **engine-administration** slash commands. These commands operate **on contextd itself** (install metadata, backups, pipeline traces, evals) — not on workspace knowledge or user tasks.

Use this file when you're not sure which admin command you need. Each command is still callable directly; this is only a navigation aid.

## Quick map

| Goal | Command |
|------|---------|
| Show installed version + release tag | [`/contextd-version`](contextd-version.md) |
| Confirm contextd is installed and resolve its wiki root | [`/contextd-detect`](contextd-detect.md) |
| Upgrade to latest release | [`/contextd-upgrade`](contextd-upgrade.md) |
| Snapshot active workspace into a backup archive | [`/contextd-backup`](contextd-backup.md) |
| Restore a workspace from a backup archive | [`/contextd-restore`](contextd-restore.md) |
| Render workspace status / coverage report | [`/contextd-report`](contextd-report.md) |
| Inspect a single pipeline trace (intent → retrieval → validate) | [`/contextd-trace`](contextd-trace.md) |
| Visualize pipeline traces in an HTML viewer | [`/contextd-viz`](contextd-viz.md) |
| Run A/B eval over golden tasks | [`/contextd-eval`](contextd-eval.md) |
| Explain a concept (workspace / pack / contract / pipeline term) | [`/contextd-explain`](contextd-explain.md) |

## When to reach for these

- **Install / upgrade / detect / version**: setting up a new machine, bumping to a new release, troubleshooting "command not found".
- **Backup / restore**: before a risky rebase, or migrating a workspace between machines.
- **Report / trace / viz / eval**: debugging "why did the agent pull the wrong context" or running prompt-pipeline regression.
- **Explain**: when the user (or you) is unsure what a wiki concept means.

## Task commands live elsewhere

These are **not** admin commands — they are the commands you reach for during actual work:

- `/use-contextd` — frame a new task against the active workspace
- `/update-contextd` — sync wiki after code changes
- `/rebase-contextd` — rebuild wiki snapshot against current code
- `/contextd-setup` — first-time per-codebase setup
- `/switch-workspace`, `/list-workspaces`, `/new-workspace`
- `/code-analyze`, `/evidence-{ingest,analyze,qa,apply}`, `/obsidian-ingest`
- `/product-brief`, `/business-view`, `/tool-design`, `/tool-extend`, `/tool-list`
- `/find`, `/suggest-automation`, `/observations-clear`

See [`README.md`](README.md) for the full command index.
