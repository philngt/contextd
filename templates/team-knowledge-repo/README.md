# Team Knowledge Repo

This is your team's private knowledge repository for [contextd](https://github.com/philngt/contextd).

It contains only `workspaces/` (and optionally packs/contracts local to your team). The engine (slash commands, subagents, templates) lives in a separate upstream repo and is installed via `scripts/install-to-claude.sh`.

## Structure

```
.
├── .gitignore
├── README.md
└── workspaces/
    ├── default/          # optional — copied from upstream
    ├── shared/           # company-wide contracts, patterns
    ├── project-a/        # knowledge for repo/codebase A
    └── project-b/        # knowledge for repo/codebase B
```

## Quick Start (per developer)

1. **Clone this repo**
   ```bash
   git clone <your-team-repo-url> ~/company-wiki
   ```

2. **Install the engine** (once per machine, from upstream)
   ```bash
   git clone https://github.com/philngt/contextd.git ~/contextd
   cd ~/contextd
   bash scripts/install-to-claude.sh --knowledge-repo ~/company-wiki
   ```

3. **Verify**
   ```bash
   contextd resolve
   # Should show knowledge_root pointing to this repo
   ```

4. **Start using**
   ```bash
   cd /path/to/your-project
   /contextd-setup
   /use-contextd "your task here"
   ```

## Daily Workflow

- **Before working**: `/contextd-team-sync pull` (pull latest knowledge from team)
- **After updating wiki** (e.g. `/update-contextd`): `/contextd-team-sync push` (share your changes)
- **Check status**: `/contextd-team-sync status`

## Updating the Engine

The engine (`~/contextd`) can be updated independently without touching this repo:

```bash
cd ~/contextd && git pull
bash scripts/install-to-claude.sh --knowledge-repo ~/company-wiki
```

This updates slash commands and subagents in `~/.claude/` while keeping canonical `knowledge_root` pointed at your team knowledge repo. Legacy `wiki_root` is still written for Claude Code adapters.

## What NOT to Commit

- `evidence/` — large, ingestable data. Use `.gitignore` to exclude.
- `.observations/prompts.jsonl` — may contain sensitive prompts.
- `eval/results/` — per-machine evaluation data.
- `.claude/` — runtime context (regenerated per task).

These are already excluded by the provided `.gitignore`.
