# Validator Rules — Engine (Universal)

## Purpose

Catch violations in agent output before it reaches a human or gets committed. Two layers: fast rule-based checks, then a prompt-based self-check for deeper issues.

## Resolution Order

```
engine rules      (this file + scripts/validate.py — immutable, no prefix)
  → pack rules    (per workspace.md `## Packs` — prefix `pack-{name}-`)
    → workspace rules (workspaces/{ws}/agents/pipeline/validator-rules.md — prefix `ws-`)
```

All three are **additive**. Loader fail-fast on naming collision (engine rule reused in pack/workspace, or pack rule reused in workspace).

## Layer 1 — Rule-Based Checks

Run these as code or regex against the generated output. Fast, deterministic, zero LLM cost.

> **Source of truth: [`scripts/validate.py`](../../scripts/validate.py)** (engine rules) + each active pack's `scripts/rules.py` (loaded via [`scripts/pack_loader.py`](../../scripts/pack_loader.py)).

### How to run

```bash
python scripts/validate.py --file <path-to-code-file> [--workspace <name>] [--wiki-root <path>] [--pretty]
```

* Workspace + `knowledge_root` are auto-resolved from `<cwd-walk-up>/.contextd/config.json` per [system-prompt.md Resolution Rule](../system-prompt.md). Legacy `.claude/wiki.json` / `.Codex/wiki.json` and `wiki_root` remain accepted as adapters.
* Validator reads `## Packs` section from `workspaces/{ws}/workspace.md` and dynamically loads each pack's rule module.
* Output: JSON `{violations: [...], summary: {errors, warnings}, context: {..., active_packs: [...]}}` on stdout.
* Exit code: `0` if no errors (warnings allowed), `1` if any errors, `2` for bad invocation.

### Engine rule list

| Rule ID | Severity | Check |
|---------|----------|-------|
| `domain-unknown-state`         | error | UPPER_CASE_SNAKE string literal that looks state-like (has `_` or ends in `ED`/`ING`/`AL`/`ANT`/`OUS`) and is not in `{ws}/domains/{domain}/workflow.md`. |
| `no-hardcoded-config`          | warn  | Numeric literal assigned to a config-like identifier (`batchSize`, `timeoutMs`, `concurrency`, `retries`, `backoffMs`, ...). |
| `constructor-injection`        | error | `@Autowired` annotation immediately followed by a field declaration (next non-blank line ends with `;` and has no `(`). |
| `report-html-self-contained`  | error | Output of `/contextd-report` (HTML files under `{ws}/reports/*.html`) MUST NOT reference external resources. Block if file matches `<script\s+src="https?:` / `<link\s+[^>]*href="https?:` / `<link\s+[^>]*href="//` / `<img\s+src="https?:` / `@import\s+url\(['"]?https?:` / `<iframe`. Skeleton placeholders (`{{...}}`) must all be replaced — `{{` in output also fails. |
| `report-citation-required`    | error | Each `<section class="report-section">` in a `/contextd-report` HTML output must contain at least one `<a class="cite"` OR one `<p class="nodata">`. A section with neither indicates fabricated content lacking source attribution. |
| `report-no-cross-workspace`   | error | A `/contextd-report` HTML output must not reference workspaces other than the one named in the report header `<title>`. Check: parse `<title>Technical Report — {WS} —` then grep for any other workspace name from `workspaces/*/` directories. Hits = violation. |

### Pack rules

Each pack contributes additional rules with prefix `pack-{name}-`. Examples:

- [`pack-event-driven`](../../packs/pack-event-driven/agents/pipeline/validator-rules.md) → `pack-event-driven-kafka-no-hardcoded-topic`, `pack-event-driven-kafka-dlq-required`, `pack-event-driven-mqtt-no-inline-topic`, ...

Pack rules only run if the workspace opts into the pack (via `## Packs` section in `workspace.md`).

### How to add a new rule

| New rule applies to | Where to add |
|---------------------|--------------|
| Every workspace, every stack | `scripts/validate.py` `ALL_RULES` + table above (engine) |
| One stack/concern (Kafka, REST, React, ...) | `packs/{pack-name}/scripts/rules.py` + pack's validator-rules.md (prefix `pack-{name}-`) |
| One workspace only | `workspaces/{ws}/agents/pipeline/validator-rules.md` (prefix `ws-`) |

For all three: add a fixture line in `scripts/test-fixtures/` that triggers the rule, and verify the script catches it.

### Heuristic limitations (Layer 1, by design)

* No real parser — comment / string-aware brace tracking is naive.
* `domain-unknown-state` depends on a parseable workflow.md and a single domain (or `wiki.json#domain` set explicitly).
* Workspace `ws-` rule loader is a stub: the script reports the presence of `{ws}/agents/pipeline/validator-rules.md` in `context.workspace_rules_file` but does not yet execute additive rules. (TODO marked in `scripts/validate.py`.)
* Layer 1 catches the common drift; Layer 2 (below) covers the rest.

## Layer 2 — Prompt-Based Self-Check

Run this as a second LLM call on the agent's output. Use a small/fast model — it's a verification pass, not a generation pass.

```md
# SELF-CHECK TASK

Review the solution below against the engine constraint catalog + active pack constraints + workspace overrides.
For each violation found, describe: rule ID, what it is, where it occurs, and how to fix.
If no violations found, respond with: "PASS"

## Constraint sources (load by ID, do not restate)

- Engine baseline: [agents/constraints.md](../constraints.md) — every `engine-*` rule applies.
- Workspace `{ws}` domain pin-down (substitute concrete state list):
  - `engine-no-new-workflow-state` → allowed states: {list from `{ws}/domains/{domain}/workflow.md`}
  - `engine-no-unlisted-transition` → allowed transitions: {list from `{ws}/domains/{domain}/workflow.md`}
- Coding conventions: [coding-rules.md](../coding-rules.md) (constructor injection, idempotent handlers, etc.)
- Active packs (append): for each pack in `workspace.md ## Packs`, load `packs/{name}/agents/constraints.md` and `packs/{name}/agents/pipeline/prompt-overrides.md`.
- Workspace overrides: `workspaces/{ws}/agents/constraints.md` (`ws-*` rules).

## Solution to Review

{{agent_output}}
```

The self-check prompt loads rule definitions by ID from the files above. Do not duplicate rule prose here — single source of truth is [agents/constraints.md](../constraints.md). Pack self-check sections come from each pack's `agents/pipeline/prompt-overrides.md` (e.g. `pack-event-driven` adds Kafka/MQTT checks: offset commit, DLQ, topic format, registered types).

## Escalation

If Layer 1 finds a violation → block output, return violation report to user.

If Layer 2 finds a violation → append the self-check result to the agent output as a `## Violations Found` section. Do not silently fix.

## When to Update These Rules

- Engine: add a check here when a new universal constraint is added to [`agents/constraints.md`](../constraints.md).
- Pack: add a rule when an agent generates the same stack-specific bug twice in projects using that stack.
- Workspace: add a rule when only one workspace needs the check (use `ws-` prefix).
- KHÔNG override engine rule trong workspace — mở PR vào engine file thay vào.

## Related

- [Engine constraints](../constraints.md)
- [Prompt template](prompt-template.md)
- [Pack system](../../packs/README.md)
