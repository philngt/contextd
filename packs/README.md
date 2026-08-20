# Domain Packs

Packs are opt-in context modules. Each pack adds domain-specific decision
guidance, retrieval routes, and optional deterministic validators on top of the
stack-agnostic contextd engine.

Enable the smallest set that owns the task. A pack does not automatically make
context cheaper. Manifest v3 makes its cost bounded and visible: runtime loads
compact metadata, Global Principles, and only the component sections selected by
the task. Precise components/keywords still matter; enabling every pack “just in
case” increases noise and can create conflicting mental models.

## Resolution and precedence

Effective packs resolve in this order:

1. If `<codebase>/.contextd/config.json#packs` is an array, it replaces the
   workspace default, including an empty array.
2. Otherwise contextd reads `workspaces/{ws}/workspace.md#Packs`.
3. Legacy adapters are accepted only during migration.

Rules remain additive and strict-only:

```text
engine  →  effective packs (alphabetical)  →  workspace
```

No later layer may relax an earlier constraint. `conflicts_with` is fail-fast
when incompatible packs are enabled together.

Per-codebase selection:

```json
{
  "workspace": "default",
  "knowledge_root": ".",
  "packs": ["pack-web-api", "pack-security"]
}
```

Workspace default:

```md
## Packs

- pack-web-api
- pack-security
```

See [workspace resolution](../agents/pipeline/workspace-resolution.md) for the
complete canonical/legacy fallback rules.

## Pack manifest v3 and v2 compatibility

New packs use `manifest_version: 3`. It keeps the v2 metadata contract and adds
two authoring constraints:

- `pack.yaml#retrieval` is the canonical component-to-doc mapping.
- `knowledge.md` is the canonical guidance source, organized as Global
  Principles plus component-scoped Mental Model, Standards, Failure Signals,
  and Evidence And Stop Conditions.

The runtime compiles two planes:

```text
always loaded: compact pack metadata + Global Principles
task selected: matched Component sections + matched workspace documents
```

The metadata contract shared by v2 and v3 includes:

- Semver `version`, maturity `status`, `category`, and ISO `reviewed_on`.
- Runtime `audiences` and `task_types`.
- Explicit `scope_includes` and `scope_excludes`.
- At least three specific, unique routing keywords for every component.
- Complete declarations for the files required by that manifest version.

Existing v2 packs remain fully supported while they are migrated. Their seven
prose/runtime files retain their current strict semantics. Legacy v1 manifests
remain loadable and receive an informational migration notice. New/scaffolded
packs must use v3. The schema is
[`templates/pack.schema.json`](../templates/pack.schema.json).

`reviewed_on` records an evidence review; it is not a promise that an external
framework can never change. Provider/framework-specific packs should link their
official baseline and pin the version used by each workspace.

## Required structure

Manifest v3:

```text
packs/{pack-name}/
├── pack.yaml
├── README.md
├── knowledge.md
└── scripts/
    └── rules.py
```

Manifest v2 retains `agents/constraints.md`, `coding-rules.md`,
`common-pitfalls.md`, `pipeline/validator-rules.md`, `retrieval-map.md`, and
`prompt-overrides.md`. A v3 pack may keep those files as migration adapters, but
they must not become a second or weaker source of truth.

Each pack README must explain when to enable it, when not to enable it, how
retrieval behaves, and how to verify a representative task. Standards use stable
`pack-{name}-...` IDs. Every executable validator ID must be documented in the
canonical knowledge source.

### Migrating a v2 pack

1. Inventory constraints, working rules, pitfalls, self-checks, validator IDs,
   and component routes; resolve contradictions before moving text.
2. Move durable cross-component rules to Global Principles. For each component,
   keep only its Mental Model, Standards, Failure Signals, and Evidence And Stop
   Conditions. Leave project-specific implementation detail in workspace docs.
3. Move retrieval rows into `pack.yaml#retrieval`; keep the old retrieval table
   equivalent while adapters are supported.
4. Keep v0.x legacy filenames as marked adapters; do not delete or rename them
   before the planned v1.0 migration boundary.
5. Prove positive/negative routing, validator parity, golden tasks, and the
   referenced/static/total token budget before changing the manifest to v3.

## Maturity model

| Status | Meaning |
|---|---|
| `stable` | Public scope/IDs are expected to remain compatible within a major version; runtime and representative tasks are covered. |
| `beta` | Useful and validated, but scope or heuristics may still change before v1. |
| `experimental` | Evaluation only; activation should be narrow and explicitly accepted. |
| `deprecated` | Kept for migration; do not enable in new workspaces. |

Maturity describes the pack contract, not the maturity of every external
technology mentioned by the pack.

## Current catalog

| Pack | Category | Status | Best for |
|---|---|---|---|
| [pack-agentic](pack-agentic/) | agent runtime | stable 1.1.0 | Bounded agent loops, tool effects, MCP, handoffs, runtime/long-term memory boundaries |
| [pack-ai-app](pack-ai-app/) | engineering | stable 1.1.0 | Provider-aware LLM calls, prompt lifecycle, RAG/embedding, evals, data/cost controls |
| [pack-claude-plugin-dev](pack-claude-plugin-dev/) | developer tooling | stable 1.1.0 | Claude Code plugin-root packaging, commands, agents, skills, hooks, and plugin MCP |
| [pack-event-driven](pack-event-driven/) | engineering | stable 1.1.0 | Kafka/MQTT/event delivery, retry/DLQ, offset and batch semantics |
| [pack-frontend-react](pack-frontend-react/) | engineering | stable 1.1.0 | Current Rules of React, Hooks/effects, JSX accessibility, pinned Next.js router boundaries |
| [pack-web-api](pack-web-api/) | engineering | stable 1.1.0 | REST/GraphQL/gRPC boundaries, validation, retry safety, errors and abuse controls |
| [pack-ba](pack-ba/) | product | beta 0.2.0 | Requirements, acceptance criteria, process maps and stakeholder decisions |
| [pack-dba](pack-dba/) | operations | beta 0.2.0 | Evidence-based schema changes, query plans, restore proof and DB operations |
| [pack-devops-iac](pack-devops-iac/) | operations | beta 0.2.0 | Terraform/OpenTofu, Kubernetes, CI/CD promotion, drift and rollback |
| [pack-operator-steering](pack-operator-steering/) | agent runtime | beta 0.4.0 | Recover direction, retain human decision ownership, audit drift/context, and decide continue/pause/pivot/stop |
| [pack-product](pack-product/) | product | beta 0.2.0 | Briefs, outcomes, roadmaps, evidence-backed personas and journeys |
| [pack-qc](pack-qc/) | quality | beta 0.3.0 | Test/defect/release evidence plus measured, guarded performance optimization |
| [pack-security](pack-security/) | security | beta 0.3.0 | Threat/control review and explicitly authorized evidence-based security validation |
| [pack-solo-builder](pack-solo-builder/) | enablement | beta 0.2.0 | Recipe-driven single-purpose tools for non-technical domain experts |
| [pack-ui-ux](pack-ui-ux/) | design | beta 0.2.0 | Design systems, WCAG 2.2, stateful user flows and UX writing |

## Selection guide

Start from the artifact or boundary being changed:

| Task signal | Start with | Add only when |
|---|---|---|
| HTTP/GraphQL/gRPC boundary | `pack-web-api` | `pack-security` for a real trust/sensitive-data concern; `pack-qc` for release/perf evidence |
| Broker consumer/producer | `pack-event-driven` | `pack-dba` for schema/restore obligations; `pack-agentic` only for an actual agent runtime |
| React/Next implementation | `pack-frontend-react` | `pack-ui-ux` when design/a11y/flow artifacts are also in scope |
| LLM/RAG application | `pack-ai-app` | `pack-agentic` for loop/tool/orchestration behavior |
| Claude Code plugin package | `pack-claude-plugin-dev` | `pack-agentic` for MCP tool runtime behavior, not packaging alone |
| Product discovery to release | `pack-product`, `pack-ba` | `pack-ui-ux`, then `pack-qc` as those artifacts enter scope |
| Infrastructure release | `pack-devops-iac` | `pack-dba` for DB changes; `pack-security` for IAM/secrets/threat controls |
| Lost direction, unclear next step, or long-running agent operation | `pack-operator-steering` | relevant domain pack for the work being steered |

Use `contextd explain` to inspect what a candidate combination actually loads:

```bash
contextd context "Review retry-safe payment endpoint" --preview --format json
contextd explain "Review retry-safe payment endpoint" --format text
```

## Create or upgrade a pack

Fast path:

```bash
python scripts/scaffold-pack.py pack-{your-name}
```

Before enabling it:

1. Complete manifest scope, audiences, task types, components, and specific keywords.
2. Give every component one manifest retrieval row scoped to the active workspace.
3. Write Global Principles and each component's Mental Model, Standards, Failure
   Signals, and Evidence And Stop Conditions in `knowledge.md`.
4. Use stable standard IDs; keep validators narrow and document every executable
   rule ID in `knowledge.md`.
5. Add representative positive/negative routing tasks, a context-budget
   assertion, and a validator fixture when executable rules exist.
6. Run the quality gates below.

```bash
contextd pack-validate --pack pack-{your-name} --format text
contextd context "{representative task}" --preview --format json
contextd explain "{representative task}" --format text
python scripts/validate.py --file <fixture> --workspace <workspace-with-pack>
```

Full validation semantics and exit codes are documented in
[`docs/pack-validation.md`](../docs/pack-validation.md).
