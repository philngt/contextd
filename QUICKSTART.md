# Quickstart — See Value in 5 Minutes

**Build system for AI coding-agent context.**

contextd compiles workspace knowledge, packs, contracts, and policies into deterministic context artifacts for Claude, Codex, Cursor, and MCP.

This path gets you to a working contextd setup with a release binary first. You only need a source checkout if you want to edit contextd itself, use the bundled default demo workspace, or install Claude slash-command adapters from this repo.

---

## Pre-flight

You need:

- macOS/Linux: `curl` or `wget`, plus `bash`.
- Windows: PowerShell.
- Git if you want to clone the demo knowledge root or a team knowledge repo.
- Python >= 3.10 only for source/developer installs.

---

## Step 1 — Install the CLI

macOS / Linux:

```bash
curl -fsSL https://github.com/philngt/contextd/releases/latest/download/install.sh | sh
contextd --version
```

Windows PowerShell:

```powershell
iwr https://github.com/philngt/contextd/releases/latest/download/install.ps1 -UseBasicParsing | iex
contextd --version
```

The release installer installs the `contextd` binary only. It does not mutate your agent client configs or create a team knowledge repo.

---

## Step 2 — Try the Default Demo Knowledge Root

Clone this repo as a sample `knowledge_root`, then run from the repo root:

```bash
git clone https://github.com/philngt/contextd.git ~/contextd
cd ~/contextd
contextd resolve --format json
contextd doctor --format text
```

Expected signal:

- `resolve` shows workspace `default` and canonical `.contextd/config.json`.
- `doctor` reports config, packs, adapter drift, and safety status before an agent works.

---

## Step 3 — Build One Context Artifact

Run the demo task against the bundled default workspace:

```bash
contextd context "prepare agent context for product requirements" --format json --no-materialize
contextd explain "prepare agent context for product requirements" --format text
contextd eval --golden --workspace default --format text
```

What to look for:

- `context` emits `artifact_type=contextd_task_context.v1`.
- `explain` shows selected docs, dropped docs, gaps, warnings, source hashes, and a lightweight budget estimate.
- `eval --golden` proves the bundled golden tasks still select the expected context.

This is the first aha moment: team knowledge becomes an auditable agent input, not a hidden prompt blob.

---

## Step 4 — Use contextd In Your Codebase

Inside the codebase where your agent will work, create or migrate the project config so contextd knows which workspace to use.

If the project already has legacy config:

```bash
contextd migrate-config --dry-run
contextd migrate-config
```

For a new project, create `<project>/.contextd/config.json` with:

```json
{
  "workspace": "default",
  "knowledge_root": "/absolute/path/to/contextd-or-team-knowledge-root",
  "packs": null
}
```

Then verify:

```bash
contextd resolve --format json
contextd doctor --format text
contextd context "your real task" --format json
contextd explain "your real task" --format text
```

`current-task.json` is the canonical artifact. `current-task.md` is only the human-readable render.

---

## Step 5 — Connect Agents

MCP stdio snippet generation:

```bash
contextd mcp-config --client codex --knowledge-root ~/contextd --workspace default
contextd mcp-config --client all --knowledge-root ~/company-wiki --workspace shared
```

Codex skill/plugin export:

```bash
contextd export --runtime codex-plugin --install
```

Claude Code adapters from a source checkout:

```bash
cd ~/contextd
bash scripts/install-to-claude.sh --knowledge-root ~/contextd --default-workspace default
```

Cursor/plain exports:

```bash
contextd export --runtime cursor --workspace default --output ./
contextd export --runtime plain --workspace default --output ./
```

See [docs/mcp.md](docs/mcp.md) and [README.md](README.md) for the full adapter matrix.

---

## Step 6 — Source/Developer Install

Use this only when editing contextd or running scripts from a checkout:

```bash
git clone https://github.com/philngt/contextd.git ~/contextd
cd ~/contextd
pip install -e .
python3 scripts/test_contextd_runtime.py
```

The source checkout also contains the default workspace, templates, packs, docs, and Claude adapter installer scripts.

---

## Step 7 — Team Knowledge Repo

If your team wants workspaces separate from the engine repo:

```bash
# Team lead creates a private knowledge repo from the template.
cp -r templates/team-knowledge-repo ~/company-wiki
cd ~/company-wiki
git init
git add .
git commit -m "init contextd knowledge root"

# Each developer clones it and points contextd at that knowledge_root.
git clone YOUR_TEAM_KNOWLEDGE_REPO_URL ~/company-wiki
contextd mcp-config --client all --knowledge-root ~/company-wiki --workspace shared
```

Daily team flow:

```text
/contextd-team-sync pull
# work, update knowledge, evaluate
/contextd-team-sync push
```

---

## Explore Further

- **Mental model**: [README.md](README.md).
- **Build-system deep dive**: [docs/build-system-model.md](docs/build-system-model.md).
- **Positioning**: [docs/comparison.md](docs/comparison.md).
- **Measuring effectiveness**: [docs/effectiveness.md](docs/effectiveness.md).
- **Context quality**: [docs/context-quality.md](docs/context-quality.md).
- **Governance loop**: [docs/governance.md](docs/governance.md), [docs/pack-validation.md](docs/pack-validation.md), [docs/evaluation.md](docs/evaluation.md).
- **Pack catalog**: [packs/README.md](packs/README.md).

## If You Get Stuck

| Symptom | Fix |
|---|---|
| `contextd resolve` cannot find a workspace | Create `.contextd/config.json`, run `contextd migrate-config`, or use `/switch-workspace` from Claude adapters. |
| `knowledge_root` points to the wrong repo | Run `contextd resolve --format json` and update `.contextd/config.json#knowledge_root`. |
| Slash commands do not appear | Re-run `bash scripts/install-to-claude.sh` from a source checkout, then restart Claude Code. |
| Pattern not found | Run `contextd find "keyword" --format json`; deterministic `contextd context` still wins over advisory search. |
| Wrong docs selected | Run `contextd explain "task" --format json` and inspect selected docs, dropped docs, gaps, and source hashes. |
| Team wants shared knowledge | See [docs/team-sync.md](docs/team-sync.md) and `/contextd-team-sync`. |
