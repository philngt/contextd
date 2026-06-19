# Quickstart — Go Live in 5 Minutes

**Build system for AI coding-agent context.**

contextd compiles workspace knowledge, packs, contracts, and policies into deterministic context artifacts for Claude, Codex, Cursor, and MCP.

For developers who just cloned `contextd`. This gets you from `git clone` to your first deterministic `contextd context` or `/use-contextd` run.

> Read this right after cloning the repo. Goal: a working contextd setup for one codebase in about 5 minutes.

---

## Pre-flight (1 minute)

You need:
- Python >= 3.10 for the contextd CLI.
- Optional: [Claude Code CLI](https://claude.com/claude-code) or an installed IDE extension for slash-command adapters.
- Python >= 3.10 for lint, trace, release, and runtime scripts.
- Bash shell (Windows: Git Bash or WSL).

```bash
git clone https://github.com/philngt/contextd.git ~/contextd   # or any path you prefer
cd ~/contextd
```

---

## Step 1 — Install the CLI and optional Claude adapter

```bash
pip install -e .
bash scripts/install-to-claude.sh
```

If you keep workspaces in a separate team repo, pass it explicitly:

```bash
bash scripts/install-to-claude.sh --knowledge-root ~/company-wiki --default-workspace shared
```

This script:
- Syncs slash commands + subagents to `~/.claude/{commands,agents}/`.
- Creates canonical `~/.contextd/config.json` with `knowledge_root` pointing to this repo.
- The CLI reads canonical `.contextd/config.json` first, then legacy adapters.
- Is idempotent — run again after `git pull` to update.

> Verify: `contextd resolve` and confirm `knowledge_root` is correct. Then run `contextd doctor` to catch config, pack, adapter, or safety drift before the first task.

### Migration

During the migration window the installer may also write legacy `~/.claude/wiki-global.json` with `wiki_root` for Claude Code adapters. Treat it as compatibility data; canonical project and global config live under `.contextd/config.json`.

---

## Step 2 — Enter your project codebase and pick a workspace

```bash
cd /path/to/your-project   # the codebase you are about to work on
```

List available workspaces:

```text
/list-workspaces
```

Switch this codebase to the workspace you want:

```text
/switch-workspace {name}
```

> Migration note: if an older slash-command adapter creates legacy config, run `contextd migrate-config` to create canonical `<your-project>/.contextd/config.json`.

---

## Step 3 — No matching workspace yet? Create one

```text
/new-workspace {your-workspace-name}
```

The flow asks for company, role, stack, and packs. It scaffolds `workspaces/{name}/` with full folder structure and stub READMEs for empty folders.

Then run:

```text
/switch-workspace {your-workspace-name}
```

---

## Step 4 — (Optional) Bootstrap contextd from an existing codebase

If the codebase already exists and you want to extract patterns/contracts/services automatically:

```text
/code-analyze
```

It snapshots codebase metadata (without copying source), sends it through the evidence pipeline, and proposes patterns/contracts/services/ADRs for the workspace. Review via `/evidence-qa`, then apply.

> Great for legacy onboarding. Skip this if you want to build workspace knowledge manually.

---

## Step 5 — Run your first task

Runtime-neutral CLI:

```bash
contextd resolve --format json
contextd doctor --format text
contextd pack-validate --all --format text
contextd context "Add a Kafka consumer for surgery file processed events" --format json
contextd explain "Add a Kafka consumer for surgery file processed events" --format text
contextd policy-check "Add a Kafka consumer for surgery file processed events" --format text
```

Claude Code adapter:

```text
/use-contextd "Add a Kafka consumer for surgery file processed events"
```

The context pipeline:
1. Planner — parse intent, verify required patterns/contracts exist.
2. Context builder — retrieve deterministic docs, write `.contextd/context/current-task.json`.
3. Markdown renderer — produce `.contextd/context/current-task.md` for humans/adapters.
4. Builder/reviewer — agent uses the context and validator rules.

> Output: generated code + `current-task.json`/`current-task.md` showing which knowledge was applied.
> Debug selection: `contextd explain` shows selected docs, dropped docs, gaps, warnings, source hashes, and budget estimates.

For team rollout or pack changes, run the full quality loop:

```bash
contextd doctor --format json
contextd pack-validate --all --format json
contextd policy-check "debug context quality" --format json
contextd eval --golden --workspace default --format json
```

---

## Step 6 — Find patterns directly when you already know what you need

Instead of running the full pipeline:

```text
/find kafka consumer
/find idempotency
```

Returns advisory candidates + snippets. Deterministic task context and contracts still win.

CLI equivalents:

```bash
contextd find "kafka consumer" --format json
contextd contract-path citation-format
```

## Optional MCP Setup

Generate a local stdio MCP snippet for your client:

```bash
contextd mcp-config --client codex --knowledge-root ~/contextd --workspace default
contextd mcp-config --client all --knowledge-root ~/company-wiki --workspace shared
```

See [docs/mcp.md](docs/mcp.md) for the tool list, client snippets, and security notes.

---

## Step 7 — After code is merged

Sync wiki with your code changes:

```text
/update-contextd                 # incremental sync (git diff → wiki edits)
/rebase-contextd                 # periodic verification: wiki vs codebase
```

---

## Team Setup (Optional)

If your team wants to share workspaces via git, see [docs/team-sync.md](docs/team-sync.md).

Quick start for teams:

```bash
# 1. Team lead creates a private knowledge repo from template
cp -r templates/team-knowledge-repo ~/company-wiki
cd ~/company-wiki && git init && git add . && git commit -m "init"

# 2. Each developer clones the knowledge repo and installs with --knowledge-root
git clone <team-repo-url> ~/company-wiki
cd ~/contextd
bash scripts/install-to-claude.sh --knowledge-root ~/company-wiki

# 3. Daily workflow
/contextd-team-sync pull        # before working
# ... do work, update wiki ...
/contextd-team-sync push        # share changes
```

---

## Explore Further

- **Mental model**: [README.md](README.md) — engine vs workspaces vs packs.
- **All commands + when to use**: [.claude/commands/README.md](.claude/commands/README.md).
- **Pack catalog** (stack-specific bundles): [packs/README.md](packs/README.md).
- **Cross-cutting principles** (rules spanning multiple packs): [agents/cross-cutting-principles.md](agents/cross-cutting-principles.md).
- **Pipeline debugging/observability**: [agents/pipeline/observability.md](agents/pipeline/observability.md) — `/contextd-trace`, `/contextd-viz`, `/contextd-eval`.
- **Governance loop**: [docs/governance.md](docs/governance.md), [docs/pack-validation.md](docs/pack-validation.md), [docs/evaluation.md](docs/evaluation.md).

## If You Get Stuck

| Symptom | Fix |
|---|---|
| `/use-contextd` returns "no workspace" | Run `/switch-workspace` or `/contextd-setup`. |
| Slash commands do not appear | Re-run `bash scripts/install-to-claude.sh`. |
| Pattern not found | Run `/find <keyword>` to confirm; workspace may not have that pattern yet. |
| Wiki references files renamed in code | Run `/rebase-contextd` to resync. |
| Legacy codebase onboarding with empty wiki | Run `/code-analyze` to bootstrap. |
| Need to ingest an external changelog/incident report | Run `/evidence-ingest --source paste --label "{topic}"`. |
| Team wants to share workspaces | See [docs/team-sync.md](docs/team-sync.md) and `/contextd-team-sync`. |
