# pack-operator-steering — Canonical Knowledge

Manifest v3 source-of-truth for operator steering. Runtime loads Global
Principles plus only the component sections matched by the current task. Legacy
files under `agents/` remain compatibility adapters during the v2→v3 migration;
they must not define weaker or competing rules.

## Global Principles

1. **Evidence before judgment.** Separate inspected facts, missing evidence,
   assumptions, inference, confidence, and judgment. Unknown root cause uses
   `needs-evidence`; missing domain expertise uses `needs-research`.
2. **Human direction ownership.** The agent should discover facts and recommend
   a path, while material goal, scope, risk, and stop decisions remain explicit
   operator decisions.
3. **Smallest decision-ready context.** Load and explain only what changes the
   current decision. More documents or another memory store do not equal better
   context.
4. **Durable state has one owner.** Persist accepted decisions, evidence state,
   and handoff state in the active workspace/context artifact or an owner-chosen
   report path; never create an implicit parallel source of truth.
5. **Every recommendation is verifiable.** Name owner, expected evidence,
   acceptance criteria, verification method, residual risk, and stop/revisit
   condition when those fields govern the decision.

### Global Standards

- `pack-operator-steering-evidence-assumptions` — global strict-only standard
  group for evidence and assumption handling.
- `pack-operator-steering-evidence-before-judgment` — findings MUST distinguish
  facts/evidence, missing evidence, assumptions, inference, confidence, and
  judgment.
- `pack-operator-steering-no-assumption-as-fact` — assumptions MUST be labeled
  with confidence and impact if wrong; they MUST NOT become facts or accepted
  decisions implicitly.
- `pack-operator-steering-gap-status-required` — insufficient evidence or
  expertise MUST use `needs-evidence`, `needs-decision`, `needs-research`, or
  `blocked`; it MUST NOT produce a confident final claim.
- `pack-operator-steering-no-double-source-of-truth` — durable steering state
  MUST remain in the active workspace/context artifact or an explicitly chosen
  report path.

### Shared Status Vocabulary

Use `ready`, `needs-evidence`, `needs-decision`, `needs-research`, or `blocked`.
Request only the smallest missing artifact or owner decision that can change the
conclusion.

## Component: context-audit

### Mental Model

A context audit asks whether the agent has the right controlling knowledge, not
whether it has many documents. Map task frame, project memory, repo evidence,
domain context, accepted decisions, quality evidence, handoff state, authority,
freshness, relevance, and contradictions before judging readiness.

### Standards

- `pack-operator-steering-report-missing-evidence` — an operator audit artifact
  MUST contain an Evidence/Bằng chứng section before its judgment.
- Findings SHOULD lead with severity, gap type, evidence, missing evidence,
  confidence, root cause status, downstream risk, proposed patch, owner,
  acceptance criteria, and verification method.
- When prompt, code, contract, decision, and runtime disagree, the audit MUST
  name the controlling authority and the contradiction.
- Repeated clarification SHOULD become a durable context patch rather than
  remaining only in conversation history.

### Failure Signals

- Judgment appears before inspected evidence.
- Stale conversation carryover is treated as current authority.
- A long document list is presented without controlling facts or relevance.
- Skill/runtime mismatch is invisible even though output quality depends on it.
- Another memory store is proposed instead of repairing the current source.

### Evidence And Stop Conditions

Evidence includes current context artifacts, source hashes, contracts, project
maps, accepted decisions, runtime output, tests, and explicit owner statements.
Stop the audit conclusion at `needs-evidence` when authority, freshness, or a
load-bearing contradiction cannot be resolved.

## Component: drift-check

### Mental Model

Drift is a mismatch between accepted direction and current work. Compare goals,
scope, quality bar, architecture, process, domain rules, context, skill fit, and
operator ownership against decisions, non-goals, assumptions, risks, code,
tests, and produced artifacts.

### Standards

- `pack-operator-steering-stop-on-deepening-drift` — when the next action would
  deepen a proven conflict with a decision or constraint, the output MUST
  recommend stop or `needs-decision` before implementation.
- Every drift finding MUST name mismatch type, controlling evidence, current
  evidence, impact, confidence, and the decision or patch required.
- A drift report MUST conclude with `continue`, `pause`, `pivot`, or `stop` and
  state why that disposition follows from evidence.
- A changed durable direction MUST create or supersede a decision record.

### Failure Signals

- Work continues because implementation is possible, despite a known conflict.
- A new preference silently replaces an accepted decision.
- Scope or quality drift is described as an isolated coding defect.
- The report recommends stopping without naming the controlling evidence.

### Evidence And Stop Conditions

Use accepted decisions, non-goals, assumption ledgers, current diffs, tests,
quality artifacts, and runtime evidence. Pause when the mismatch is visible but
the owner decision or authoritative baseline is unresolved; stop when a
controlling constraint is violated or continued work only increases sunk cost.

## Component: remediation-planning

### Mental Model

Remediation closes a proven root cause through a bounded change and observable
verification. Separate symptom patch, structural fix, context patch, and process
guardrail; do not disguise evidence collection as a final remediation plan.

### Standards

- `pack-operator-steering-remediation` — strict-only remediation standard group.
- `pack-operator-steering-root-cause-before-remediation` — a remediation MUST
  name the proven root cause or explicitly state that root cause remains
  `needs-evidence`.
- `pack-operator-steering-acceptance-verification-required` — every remediation
  item MUST name owner, acceptance criteria, verification method, and residual
  risk.
- `pack-operator-steering-remediation-missing-verification` — remediation
  artifacts missing acceptance criteria or verification method fail Layer 1.
- Recurring failures MUST include a monitoring or regression signal.

### Failure Signals

- Verbs such as fix, improve, or update have no acceptance evidence.
- The plan treats a suspected root cause as proven.
- All remediation is collapsed into one large rewrite.
- No owner, residual risk, rollback, or recurrence signal exists.

### Evidence And Stop Conditions

Evidence includes reproduction, trace/log output, failing and passing fixtures,
source-to-symptom linkage, and before/after verification. Switch to evidence
intake when root cause is not proven. Stop remediation expansion when acceptance
criteria are met and residual risk is recorded; do not continue polishing by
default.

## Component: decision-ledger

### Mental Model

A durable decision preserves why direction changed so later sessions do not
re-litigate or silently reverse it. It records the owner choice and its evidence,
not every reversible implementation detail.

### Standards

- `pack-operator-steering-decision-handoff` — strict-only group for durable
  decisions and transfer state.
- `pack-operator-steering-decision-ledger-required` — a durable decision MUST
  include status, context, decision, consequences, owner, and revisit trigger.
- `pack-operator-steering-decision-missing-ledger-fields` — decision/ADR
  artifacts missing status, owner, or revisit trigger receive a Layer-1 warning.
- Superseding a decision MUST link the previous decision and identify the
  changed evidence or assumption.

### Failure Signals

- A material direction changes only in chat.
- The record states what was selected but not why or when to revisit it.
- An implementation detail is elevated into a permanent architecture decision.
- A previous decision disappears rather than being superseded.

### Evidence And Stop Conditions

Use accepted owner statements, evaluated options, trade-offs, controlling
constraints, and resulting evidence. Defer the decision when a prerequisite
fact is missing. Stop recording when the choice is reversible, local, and fully
bounded by an existing standard.

## Component: handoff-quality

### Mental Model

A handoff transfers verified state and control boundaries so the next operator
or agent can continue without re-guessing. It is a state checkpoint, not a
conversation summary.

### Standards

- `pack-operator-steering-handoff-state-required` — a handoff MUST state current
  state, proven and unproven items, risks, exact next action, and stop condition.
- `pack-operator-steering-handoff-missing-next-action` — handoff/session briefs
  missing next action or stop condition receive a Layer-1 warning.
- The handoff MUST distinguish completed work, uncommitted work, external state,
  assumptions, and owner decisions.
- References MUST point to the active workspace/context source rather than copy
  a competing durable state store.

### Failure Signals

- “Continue from here” appears without an exact action or expected evidence.
- Uncertainty, failing tests, dirty state, or unresolved decisions are hidden.
- The next agent must reconstruct authority from conversation history.
- The brief duplicates mutable state instead of linking its owner artifact.

### Evidence And Stop Conditions

Use repository status, test output, context/synapse hashes, accepted decisions,
artifact paths, risks, and pending external dependencies. Stop transfer and mark
`blocked` when the next actor cannot safely identify authority or reproduce the
current state.

## Component: workflow-mental-model

### Mental Model

A workflow mental model explains where work is, what decision belongs there,
which artifact proves completion, and how failure is diagnosed. It should expose
stages, transitions, quality gates, failure modes, diagnosis cues, and
remediation paths without pretending to supply missing domain expertise.

### Standards

- Every model MUST name stages, allowed transitions, owner decisions, artifacts,
  gates, failure modes, diagnosis cues, and recovery paths relevant to the task.
- The current stage and earliest unresolved gate MUST be explicit.
- Unknown domain rules MUST be labeled `needs-research`; a generic pack MUST NOT
  invent production claims.
- The model SHOULD separate what the operator must understand from reversible
  implementation detail that can be delegated and verified.

### Failure Signals

- Quality is judged without a stage or gate model.
- The model is a generic lifecycle unrelated to current artifacts.
- Missing expertise is hidden behind confident workflow prose.
- Every possible stage is loaded even though only one decision is active.

### Evidence And Stop Conditions

Use domain workflows, project maps, contracts, runbooks, decisions, and current
artifacts. Stop expansion when the operator can locate the current stage,
identify the active gate, and explain the next evidence or decision. Route to
domain research when a stage depends on unsupported expertise.

## Component: operator-wayfinding

### Mental Model

Wayfinding restores orientation and decision ownership when long-running work
has become directionless. The flow is:

```text
orient → inspect facts → classify gap → expose decision frontier
       → recover decision-ready knowledge → recommend one bounded next step
       → continue | pause | pivot | stop
```

The primary gap is one of `task-frame`, `knowledge`, `evidence`, `decision`,
`mental-model`, `execution`, `drift`, or `diminishing-return`. The current
decision frontier contains only material choices whose prerequisites are
settled.

### Standards

- `pack-operator-steering-wayfinding-agency` — strict-only wayfinding and human
  agency standard group.
- `pack-operator-steering-discover-facts-before-asking` — the agent MUST inspect
  discoverable repo/runtime/context facts before asking; questions are reserved
  for owner intent, value, risk tolerance, or material decisions.
- `pack-operator-steering-decision-frontier-required` — material decisions MUST
  be dependency-ordered; downstream choices MUST NOT be asked or silently made
  while prerequisites remain open.
- `pack-operator-steering-decision-ready-knowledge` — current knowledge MUST be
  split into `must-understand`, `safe-to-delegate`, and
  `needs-evidence-or-expert`.
- `pack-operator-steering-recommendation-preserves-agency` — each material
  question MUST include recommendation, rationale, trade-off, impact if wrong,
  and allow `accept`, `revise`, `defer/need-evidence`, or `stop`.
- `pack-operator-steering-wayfinding-stop-gate` — every checkpoint MUST conclude
  `continue`, `pause`, `pivot`, or `stop`, with one bounded next action or a
  revisit trigger. Remaining possible work is not evidence to continue.
- `pack-operator-steering-no-material-action-before-alignment` — during an
  explicit wayfinding session, the agent MUST NOT implement a material path
  until the operator confirms sufficient shared understanding or exits the
  session.
- `pack-operator-steering-wayfinding-missing-control-fields` — a checkpoint
  missing orientation, primary gap, knowledge recovery, decision frontier,
  recommendation, operator decision, or stop gate fails Layer 1.

### Failure Signals

- The agent asks the user for facts already present in the repository.
- A long tutorial replaces the minimum knowledge needed for the current choice.
- “AI tự quyết” becomes blanket approval for scope, architecture, or risk.
- Multiple dependent material questions are batched together.
- The plan defaults to continue because more tasks exist.
- Implementation starts before shared understanding is confirmed.

### Evidence And Stop Conditions

Inspect the current context artifact, project map, decisions, evidence, runbooks,
tests, and repository state. `continue` requires a valid objective, sufficient
decision-ready understanding, one bounded action, and expected evidence.
`pause` waits for evidence, expertise, recovery, or an owner decision. `pivot`
records the invalidated assumption and new direction. `stop` applies when value
no longer justifies cost/risk, a controlling constraint conflicts, or no defined
evidence would change the conclusion.
