# Team Workspace Sync Guide

## Mental Model

`contextd` is designed around a clean separation:

| Layer | Lives In | Managed By | Update Frequency |
|-------|----------|------------|------------------|
| **Engine** | `philngt/contextd` (upstream) | Upstream maintainer | When new releases drop |
| **Knowledge** | Your team's private repo | Your team | Daily, as you work |

- **Engine** = CLI, slash-command adapters, subagents, templates, packs, system prompts. You install it once and re-run when upstream updates.
- **Knowledge** = `workspaces/` (contracts, patterns, domains, project docs). You create a private git repo for your team and commit workspaces there.

This keeps your team knowledge private and version-controlled while making engine updates trivial.

---

## Setup for Team Lead

### 1. Create the team knowledge repo

You can start from the provided template:

```bash
git clone https://github.com/philngt/contextd.git ~/contextd
cd ~/contextd

# Copy the template to your new repo
cp -r templates/team-knowledge-repo ~/my-company-wiki
cd ~/my-company-wiki
git init
git add .
git commit -m "Initial team knowledge repo"

# Push to your private GitHub/GitLab
git remote add origin git@github.com:your-org/company-wiki.git
git push -u origin main
```

Or create the repo manually:

```bash
mkdir company-wiki && cd company-wiki
git init

# Create .gitignore (see templates/team-knowledge-repo/.gitignore)
cat > .gitignore <<'EOF'
evidence/
.observations/prompts.jsonl
.observations/*.lock
eval/results/*
!eval/results/.gitkeep
.claude/
.DS_Store
Thumbs.db
__pycache__/
*.pyc
node_modules/
EOF

mkdir -p workspaces
touch workspaces/.gitkeep

git add .
git commit -m "Initial team knowledge repo"
```

### 2. Scaffold workspaces

```bash
cd ~/contextd
bash scripts/install-to-claude.sh --knowledge-repo ~/my-company-wiki

# In Claude Code:
# /new-workspace shared
# /new-workspace project-a
```

### 3. Commit initial workspaces

```bash
cd ~/my-company-wiki
git add workspaces/
git commit -m "Add shared and project-a workspaces"
git push
```

---

## Setup for Each Developer

### Option A: Manual

```bash
# 1. Clone the team knowledge repo
git clone git@github.com:your-org/company-wiki.git ~/company-wiki

# 2. Clone the engine repo
git clone https://github.com/philngt/contextd.git ~/contextd
cd ~/contextd

# 3. Install with knowledge repo pointing to your team repo
bash scripts/install-to-claude.sh --knowledge-repo ~/company-wiki

# 4. Verify
contextd resolve
# Should show knowledge_root pointing to ~/company-wiki
```

### Option B: One-liner (recommended)

```bash
bash ~/contextd/scripts/setup-team-knowledge.sh \
    --engine-repo ~/contextd \
    --knowledge-repo git@github.com:your-org/company-wiki.git \
    --local-path ~/company-wiki
```

### Option C: From existing engine

If the developer already has `philngt/contextd` cloned:

```bash
cd ~/contextd
git pull
bash scripts/install-to-claude.sh --knowledge-repo ~/company-wiki
```

---

## Daily Workflow

### Before starting work

Pull latest knowledge so you're working with the team's most current contracts and patterns:

```text
/contextd-team-sync pull
```

Or from bash:

```bash
bash ~/contextd/scripts/contextd-team-sync.sh pull
```

### Working on a task

```text
/use-contextd "Add Kafka consumer for surgery events"
```

### After code is merged — update wiki

```text
/update-contextd
/contextd-team-sync push
```

### Check status

```text
/contextd-team-sync status
```

---

## Updating the Engine (Upstream)

When `philngt/contextd` releases updates:

```bash
cd ~/contextd
git pull
bash scripts/install-to-claude.sh --knowledge-repo ~/company-wiki
```

This updates:
- `~/.claude/commands/` (Claude Code slash-command adapter)
- `~/.claude/agents/` (Claude Code subagent adapter)
- Keeps canonical `knowledge_root` pointed at `~/company-wiki` when `.contextd/config.json` is present

Your team knowledge repo is untouched.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/contextd-team-sync` says "knowledge_root is not a git repo" | `knowledge_root` points to engine repo or missing | Edit `.contextd/config.json` or legacy `~/.claude/wiki-global.json` |
| `git pull` fails with merge conflict | Local uncommitted changes | `cd ~/company-wiki && git stash && git pull && git stash pop` or commit first |
| Pushed files include `evidence/` | Missing `.gitignore` in knowledge repo | Add template `.gitignore` from `templates/team-knowledge-repo/.gitignore` |
| Workspace not found after pull | New workspace created by teammate | Run `/list-workspaces` then `/switch-workspace {name}` |
| Slash commands outdated | Engine not updated | Re-run `install-to-claude.sh --knowledge-repo ~/company-wiki` |

---

## Advanced: Multiple Knowledge Repos

If you work across multiple organizations (e.g., full-time job + freelance), you can have multiple knowledge repos:

```bash
# Repo 1: company
git clone git@github.com:company/company-wiki.git ~/company-wiki
# Repo 2: freelance client
git clone git@github.com:client/client-wiki.git ~/client-wiki
```

Switch by editing `.contextd/config.json` in each codebase:

```json
{
  "project": "my-project",
  "workspace": "project-a",
  "knowledge_root": "~/company-wiki"
}
```

Legacy `.claude/wiki.json` may keep using `wiki_root`; contextd treats it as an adapter alias.
