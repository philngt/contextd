# Quickstart — Go Live in 5 Minutes

For developers who just cloned `wiki-template`. This gets you from `git clone` to your first `/use-wiki` run.

> Read this right after cloning the repo. Goal: a working wiki setup for one codebase in about 5 minutes.

---

## Pre-flight (1 minute)

You need:
- [Claude Code CLI](https://claude.com/claude-code) or an installed IDE extension.
- Python ≥ 3.9 (for lint/trace scripts; optional for basic wiki usage).
- Bash shell (Windows: Git Bash or WSL).

```bash
git clone <wiki-template-repo> ~/wiki   # or any path you prefer
cd ~/wiki
```

---

## Step 1 — Install once into `~/.claude/`

```bash
bash scripts/install-to-claude.sh
```

This script:
- Syncs slash commands + subagents to `~/.claude/{commands,agents}/`.
- Creates `~/.claude/wiki-global.json` with `wiki_root` pointing to this repo.
- Is idempotent — run again after `git pull` to update.

> Verify: `cat ~/.claude/wiki-global.json` and confirm `"wiki_root"` is correct.

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

> This creates `<your-project>/.claude/wiki.json` with `"workspace": "{name}"`, which is how the wiki maps this codebase.

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

## Step 4 — (Optional) Bootstrap wiki from an existing codebase

If the codebase already exists and you want to extract patterns/contracts/services automatically:

```text
/code-analyze
```

It snapshots codebase metadata (without copying source), sends it through the evidence pipeline, and proposes patterns/contracts/services/ADRs for the workspace. Review via `/evidence-qa`, then apply.

> Great for legacy onboarding. Skip this if you want to build wiki docs manually.

---

## Step 5 — Run your first task with `/use-wiki`

```text
/use-wiki "Add a Kafka consumer for surgery file processed events"
```

The pipeline runs 5 stages:
1. Planner — parse intent, verify required patterns/contracts exist.
2. Context selector — retrieve relevant docs, write `.claude/context/current-task.md`.
3. Plan reviewer — blocks if patterns are missing or conflicting.
4. Builder — main agent writes code from the prompt template.
5. Reviewer (optional) — checks violations/hallucinations.

> Output: generated code + `current-task.md` showing which knowledge was applied.

---

## Step 6 — Find patterns directly when you already know what you need

Instead of running the full pipeline:

```text
/find kafka consumer
/find idempotency
```

Returns top candidates + snippets. Faster than `/use-wiki` for lookup-only tasks.

---

## Step 7 — After code is merged

Sync wiki with your code changes:

```text
/update-wiki                 # incremental sync (git diff → wiki edits)
/rebase-wiki                 # periodic verification: wiki vs codebase
```

---

## Explore Further

- **Mental model**: [README.md](README.md) — engine vs workspaces vs packs.
- **All commands + when to use**: [.claude/commands/README.md](.claude/commands/README.md).
- **Pack catalog** (stack-specific bundles): [packs/README.md](packs/README.md).
- **Cross-cutting principles** (rules spanning multiple packs): [agents/cross-cutting-principles.md](agents/cross-cutting-principles.md).
- **Pipeline debugging/observability**: [agents/pipeline/observability.md](agents/pipeline/observability.md) — `/wiki-trace`, `/wiki-viz`, `/wiki-eval`.

## If You Get Stuck

| Symptom | Fix |
|---|---|
| `/use-wiki` returns "no workspace" | Run `/switch-workspace` or `/wiki-setup`. |
| Slash commands do not appear | Re-run `bash scripts/install-to-claude.sh`. |
| Pattern not found | Run `/find <keyword>` to confirm; workspace may not have that pattern yet. |
| Wiki references files renamed in code | Run `/rebase-wiki` to resync. |
| Legacy codebase onboarding with empty wiki | Run `/code-analyze` to bootstrap. |
| Need to ingest an external changelog/incident report | Run `/evidence-ingest --source paste --label "{topic}"`. |
