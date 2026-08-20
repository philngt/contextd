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

`knowledge_root` is the canonical root field.

### Compatibility

Legacy `wiki_root` in `.claude/wiki.json`, `.Codex/wiki.json`, and legacy global configs is accepted only as a migration adapter.

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

Pack rules are active only when the codebase resolves that pack. Do not copy a
summary list into this reference: it becomes stale and can accidentally loosen
the canonical rules. Resolve and read, in order:

1. `packs/{name}/pack.yaml` for scope, audiences, task types and components.
2. For manifest v3, `knowledge.md#Global Principles` plus matched component
   sections; for v2, the declared `agents/` compatibility rule files.
3. For manifest v3, selected `pack.yaml#retrieval` rows; for v2, selected rows
   in `agents/pipeline/retrieval-map.md`.
4. `scripts/rules.py` and the version-appropriate canonical knowledge catalog
   for documented/executable Layer-1 parity.

The canonical catalog, maturity model and selection guide are in
[`packs/README.md`](../packs/README.md). Validate them with
`contextd pack-validate --all --format text`; use `contextd explain` to verify
that a task loads only the intended pack components.

## Maintaining the Wiki

When code changes, update the wiki of the **active workspace**. Keep both in sync.

| Change | Update |
|--------|--------|
| New reusable pattern | `{ws}/platform/patterns/` + `{ws}/patterns-index.md` |
| New MQTT type (pack-event-driven on) | `{ws}/platform/contracts/mqtt-topic-contract.md` |
| New project service | `{ws}/projects/{project}/services/` + `knowledge-map.md` |
| Architecture decision | `{ws}/decisions/` (workspace) or `{ws}/projects/{p}/decisions/` (project) |
| Repeated agent mistake (workspace-local) | `{ws}/agents/constraints.md` + `{ws}/agents/pipeline/validator-rules.md` (prefix `ws-`) |
| Repeated agent mistake (stack-wide) | v3 `packs/{name}/knowledge.md` + `scripts/rules.py` when deterministic (v2 constraints/validator compatibility files), prefix `pack-{name}-` |
| Repeated agent mistake (engine-wide) | `agents/constraints.md` + `agents/pipeline/validator-rules.md` |
| Onboard new stack | `python scripts/scaffold-pack.py pack-{name}` → v3 manifest + canonical knowledge |
| Production incident | `{ws}/runbooks/` |
| Raw evidence (MCP/API/paste) | `{ws}/evidence/` via `/evidence-{ingest,analyze,qa,apply}`. Solo-builder workspaces auto-use [domain-analysis-prompts.md](../packs/pack-solo-builder/agents/pipeline/domain-analysis-prompts.md) + [qa-batch-non-tech.md](../packs/pack-solo-builder/agents/pipeline/qa-batch-non-tech.md) |
| Onboard codebase / refresh platform from code | `/code-analyze` → evidence pipeline (`source_type=code`) → CORE-CODE prompts → `/evidence-qa` → `/evidence-apply` |

Use templates in [templates/](../templates/).

## OKF (Open Knowledge Format)

Concept files trong workspace theo [OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md): YAML frontmatter bắt buộc `type`, khuyến nghị `title`/`description`. Mục đích: metadata đồng nhất để agent/tool parse, provenance (ai tạo, verified bởi ai) traceable, diffable trong version control.

**Type set hiện tại** (lint warning nếu type ngoài set): `Contract`, `Pattern`, `Decision`, `Evidence`, `Runbook`, `Report`, `Tool`, `Service`, `Domain`, `Reference`, `Recipe`, `Brief`, `Requirement`, `Design`.

**Field mapping contextd → OKF:**

| contextd | OKF |
|----------|-----|
| `{ws}/platform/contracts/*.md` | `type: Contract` |
| `{ws}/platform/patterns/*.md` | `type: Pattern` |
| `{ws}/decisions/*.md` | `type: Decision`, `status: stable` khi ACCEPTED (OKF status = lifecycle; ADR Status trong body giữ nguyên) |
| `{ws}/runbooks/*.md` | `type: Runbook` |
| `{ws}/evidence/qa/*/...` | `type: Evidence` + `generated: { by, at }` |
| `agents/*.md` (engine rules) | `type: Reference` (khi áp dụng) |
| `patterns-index.md`, `README.md`, `INDEX.md`, `_index.md` | index role — KHÔNG cần frontmatter (OKF reserve `index.md`/`log.md`; project giữ tên riêng) |

**Quy tắc:**

- `status` ∈ `draft | stable | deprecated` (absent ⇒ `stable`). Tool-spec dùng lifecycle riêng (`draft|specced|building|done|shelved` — pack constraint, không đổi).
- Provenance: `generated: { by: <actor>, at: <ISO> }`, `verified: [{ by, at }]`, actor convention `human:<id>` / `process:<id>` / `<agent>/<version>`.
- Per-claim attribution: footnote `[^id]` trong body, `id` join vào `sources[].id`; `resource` bắt buộc mỗi entry, `id` optional (entry chỉ có `resource`, hoặc id không được cite trong body, đều hợp lệ).
- Consumers KHÔNG reject unknown keys/types — OKF "tolerate unknown" (lint chỉ warning).

### Synapse metadata

Concept files may add `node_id`, `freshness`, `review_by`, `lifecycle`, and a
typed `relations` list. `contextd synapse` compiles these fields into a
workspace-scoped `contextd_synapse.v1` index. Missing fields remain backward
compatible: path-derived ID, active lifecycle, and unknown freshness.

The generated graph is not canonical storage. Workspace files remain the
long-term governed knowledge source; task artifacts contain a context
projection, while session history/checkpoints remain runtime state.

**Enforcement**: `scripts/lint-wiki.py` check frontmatter parseable, `type` non-empty, type ∈ set, `status` ∈ enum, mỗi `sources[]` entry có `resource`, footnote `[^id]` khớp `sources[].id` (id không cite trong body là hợp lệ) — tất cả warning, **exit 0 mặc định** (CI-friendly; `--strict` → exit 2 nếu muốn warnings-as-errors). File ngoài concept (index/config) và `.claude/**` (harness schema riêng) không bị check.

## Detailed References

| Topic | File |
|-------|------|
| Workspaces — mechanism | [workspaces/README.md](../workspaces/README.md) |
| Packs — catalog + mechanism | [packs/README.md](../packs/README.md) |
| Coding rules (engine) | [agents/coding-rules.md](../agents/coding-rules.md) (+ v3 pack `knowledge.md`, v2 compatibility `agents/coding-rules.md`) |
| Per-workspace pattern lookup | `{ws}/patterns-index.md` |
| Engine constraints | [agents/constraints.md](../agents/constraints.md) (+ workspace override) |
| Prompt pipeline design | [agents/pipeline/README.md](../agents/pipeline/README.md) |
| Context retrieval rules | [agents/pipeline/task-to-docs-map.md](../agents/pipeline/task-to-docs-map.md) |
| Synapse context management and loading | [docs/synapse-context-management.md](synapse-context-management.md) |
| Prompt template | [agents/pipeline/prompt-template.md](../agents/pipeline/prompt-template.md) |
| Validator rules | [agents/pipeline/validator-rules.md](../agents/pipeline/validator-rules.md) (+ workspace override) |
| Multi-agent pipeline | [agents/pipeline/multi-agent-pipeline.md](../agents/pipeline/multi-agent-pipeline.md) |
| Pipeline visual | [agents/pipeline/PIPELINE-VISUAL.md](../agents/pipeline/PIPELINE-VISUAL.md) |
| Pipeline observability | [agents/pipeline/observability.md](../agents/pipeline/observability.md), [.claude/commands/contextd-eval.md](../.claude/commands/contextd-eval.md), [contextd-trace.md](../.claude/commands/contextd-trace.md), [contextd-viz.md](../.claude/commands/contextd-viz.md), `scripts/render_trace.py`, `{ws}/eval/golden-tasks/` |
| Repetition detector | [agents/pipeline/repetition-detection.md](../agents/pipeline/repetition-detection.md), `scripts/detect_repetition.py`, [.claude/commands/suggest-automation.md](../.claude/commands/suggest-automation.md), [observations-clear.md](../.claude/commands/observations-clear.md) |
| Evidence ingestion | [agents/pipeline/critical-analysis-prompts.md](../agents/pipeline/critical-analysis-prompts.md), [qa-batching.md](../agents/pipeline/qa-batching.md), [evidence-lifecycle.md](../agents/pipeline/evidence-lifecycle.md) |
| Code analysis | [agents/pipeline/code-snapshot-conventions.md](../agents/pipeline/code-snapshot-conventions.md), [code-analysis-prompts.md](../agents/pipeline/code-analysis-prompts.md), [.claude/commands/code-analyze.md](../.claude/commands/code-analyze.md) |
| Raw storage conventions | [agents/pipeline/raw-storage-conventions.md](../agents/pipeline/raw-storage-conventions.md) |
