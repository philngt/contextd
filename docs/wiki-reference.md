# Wiki Reference

Detailed reference for `contextd`. CLAUDE.md links here for material that doesn't need to be in the agent's hot-path instructions.

## Knowledge Structure

```
agents/                              ← ENGINE (stack-agnostic, every workspace)
  system-prompt.md, coding-rules.md, constraints.md
  pipeline/                          ← intent → retrieval → filter → validate
templates/                           ← ENGINE — skeletons (workspace.md, service.md, pack.yaml, ...)
.claude/commands/                    ← ENGINE — slash commands

packs/                               ← PACKS (stack-specific, opt-in per workspace)
  pack-event-driven/                 ← Kafka/MQTT/DLQ
  pack-web-api/                      ← REST/GraphQL/gRPC
  pack-frontend-react/               ← React/Next.js
  pack-ai-app/                       ← LLM apps
  pack-agentic/                      ← agent loops, tool use, MCP
  pack-claude-plugin-dev/            ← build Claude Code plugins
  pack-security/                     ← AppSec + pentest combined
  pack-qc/                           ← QA + performance optimization
  pack-product/                      ← briefs/OKR/roadmap
  pack-solo-builder/                 ← non-tech expert workflow
  ... (see packs/README.md)

workspaces/
  {ws}/                              ← resolved from <cwd>/.contextd/config.json.workspace
    workspace.md                     ← metadata + ## Packs opt-in
    patterns-index.md                ← per-workspace pattern lookup
    platform/
      contracts/                     ← topic formats, API schemas — highest priority
      patterns/                      ← canonical implementations to reuse
      architecture/                  ← system topology
      infrastructure/
    domains/{domain}/                ← business rules, state machines
    projects/{project}/              ← per-service docs, local overrides, ADRs
    runbooks/                        ← incident handling
    decisions/                       ← workspace ADRs
    agents/                          ← OPTIONAL — workspace overrides
```

`knowledge_root` is the canonical root field. Legacy `wiki_root` in `.claude/wiki.json`, `.Codex/wiki.json`, and legacy global configs is accepted only as a migration adapter.

## Output Format

```
## Understanding
{Restate the task — include workspace name}

## Knowledge Mapping
{Which contracts, patterns, domain docs in {ws}/ are applied}

## Design
{Flow description before any code}

## Implementation
{Code}

## Edge Cases
{Failure scenarios handled}

## Assumptions
{Anything not in {ws}/ that was assumed — NEVER taken from another workspace}
```

## Pack-specific Hard Constraints

Active only when the workspace enables that pack:

- **pack-event-driven**: never bypass retry/DLQ, commit Kafka offset before processing, inline MQTT topic, hardcode topic
- **pack-web-api**: never leak stack trace, miss input validation, expose mutating endpoint without idempotency
- **pack-frontend-react**: no direct state mutation, no missing alt/key, no effect without cleanup
- **pack-ai-app**: never log raw prompt, hardcode model ID, omit max_tokens, skip prompt cache
- **pack-agentic**: no unbounded agent loop, no tool without timeout, no destructive tool without confirm
- **pack-claude-plugin-dev**: never miss plugin.json manifest, slash command without description, subagent without explicit tools, hardcoded API secret
- **pack-product**: brief must include Problem/Metric/Acceptance, KR must be measurable, no tech jargon, no implementation dictation, no vague roadmap dates
- **pack-solo-builder**: tool spec must include Problem/System Map/Tech Stack/Acceptance/Setup, recommend only tech in `recipes/`, plain language with 1-line jargon explain, 1-tool-1-purpose, concrete acceptance
- **pack-security**: never recommend technique without authorization context, leak credentials in logs, skip threat model on auth/crypto changes
- **pack-qc**: no untested critical path, no perf regression without budget, no flaky test merged

## Maintaining the Wiki

When code changes, update the wiki of the **active workspace**. Keep both in sync.

| Change | Update |
|--------|--------|
| New reusable pattern | `{ws}/platform/patterns/` + `{ws}/patterns-index.md` |
| New MQTT type (pack-event-driven on) | `{ws}/platform/contracts/mqtt-topic-contract.md` |
| New project service | `{ws}/projects/{project}/services/` + `knowledge-map.md` |
| Architecture decision | `{ws}/decisions/` (workspace) or `{ws}/projects/{p}/decisions/` (project) |
| Repeated agent mistake (workspace-local) | `{ws}/agents/constraints.md` + `{ws}/agents/pipeline/validator-rules.md` (prefix `ws-`) |
| Repeated agent mistake (stack-wide) | `packs/{name}/agents/constraints.md` + validator-rules (prefix `pack-{name}-`) |
| Repeated agent mistake (engine-wide) | `agents/constraints.md` + `agents/pipeline/validator-rules.md` |
| Onboard new stack | New `packs/{name}/` from `templates/pack.yaml` |
| Production incident | `{ws}/runbooks/` |
| Raw evidence (MCP/API/paste) | `{ws}/evidence/` via `/evidence-{ingest,analyze,qa,apply}`. Solo-builder workspaces auto-use [domain-analysis-prompts.md](../packs/pack-solo-builder/agents/pipeline/domain-analysis-prompts.md) + [qa-batch-non-tech.md](../packs/pack-solo-builder/agents/pipeline/qa-batch-non-tech.md) |
| Onboard codebase / refresh platform from code | `/code-analyze` → evidence pipeline (`source_type=code`) → CORE-CODE prompts → `/evidence-qa` → `/evidence-apply` |

Use templates in [templates/](../templates/).

## Detailed References

| Topic | File |
|-------|------|
| Workspaces — mechanism | [workspaces/README.md](../workspaces/README.md) |
| Packs — catalog + mechanism | [packs/README.md](../packs/README.md) |
| Coding rules (engine) | [agents/coding-rules.md](../agents/coding-rules.md) (+ `packs/{name}/agents/coding-rules.md`) |
| Per-workspace pattern lookup | `{ws}/patterns-index.md` |
| Engine constraints | [agents/constraints.md](../agents/constraints.md) (+ workspace override) |
| Prompt pipeline design | [agents/pipeline/README.md](../agents/pipeline/README.md) |
| Context retrieval rules | [agents/pipeline/task-to-docs-map.md](../agents/pipeline/task-to-docs-map.md) |
| Prompt template | [agents/pipeline/prompt-template.md](../agents/pipeline/prompt-template.md) |
| Validator rules | [agents/pipeline/validator-rules.md](../agents/pipeline/validator-rules.md) (+ workspace override) |
| Multi-agent pipeline | [agents/pipeline/multi-agent-pipeline.md](../agents/pipeline/multi-agent-pipeline.md) |
| Pipeline visual | [agents/pipeline/PIPELINE-VISUAL.md](../agents/pipeline/PIPELINE-VISUAL.md) |
| Pipeline observability | [agents/pipeline/observability.md](../agents/pipeline/observability.md), [.claude/commands/contextd-eval.md](../.claude/commands/contextd-eval.md), [contextd-trace.md](../.claude/commands/contextd-trace.md), [contextd-viz.md](../.claude/commands/contextd-viz.md), `scripts/render_trace.py`, `{ws}/eval/golden-tasks/` |
| Repetition detector | [agents/pipeline/repetition-detection.md](../agents/pipeline/repetition-detection.md), `scripts/detect_repetition.py`, [.claude/commands/suggest-automation.md](../.claude/commands/suggest-automation.md), [observations-clear.md](../.claude/commands/observations-clear.md) |
| Evidence ingestion | [agents/pipeline/critical-analysis-prompts.md](../agents/pipeline/critical-analysis-prompts.md), [qa-batching.md](../agents/pipeline/qa-batching.md), [evidence-lifecycle.md](../agents/pipeline/evidence-lifecycle.md) |
| Code analysis | [agents/pipeline/code-snapshot-conventions.md](../agents/pipeline/code-snapshot-conventions.md), [code-analysis-prompts.md](../agents/pipeline/code-analysis-prompts.md), [.claude/commands/code-analyze.md](../.claude/commands/code-analyze.md) |
| Raw storage conventions | [agents/pipeline/raw-storage-conventions.md](../agents/pipeline/raw-storage-conventions.md) |
