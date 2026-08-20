# pack-operator-steering — Working Rules

> Manifest-v2 compatibility adapter. Canonical v3 guidance lives in
> [`../knowledge.md`](../knowledge.md).

Working rules cho operator-facing audit, drift, remediation, decision, handoff, and mental-model artifacts. Less strict than constraints; use these as conventions.

## Finding Shape

- Lead with findings before narrative.
- Each finding names severity, category, gap/mismatch type, evidence, missing evidence, confidence, root cause, downstream risk, proposed patch, owner, acceptance criteria, and verification method.
- Use `ready`, `needs-evidence`, `needs-decision`, `needs-research`, or `blocked` as the status vocabulary.
- When evidence is missing, ask for the smallest evidence source that can change the conclusion.

## Context Audit

- Build a context map before judging output: task frame, project memory, repo evidence, domain context, decision context, quality context, and handoff context.
- Separate active evidence from stale conversation carryover.
- Name the authority source when prompt, docs, decisions, and code disagree.
- Prefer a durable context patch over repeating the same clarification in chat.

## Drift Check

- Compare current work against accepted decisions, non-goals, assumptions, risks, implementation state, tests, and artifacts.
- Classify drift as goal, scope, quality, architecture, process, domain, context, skill, or operator drift.
- Give a continue/stop recommendation; stop when the next action would deepen a known conflict.
- Record any decision that must be added or superseded.

## Remediation Planning

- Separate quick patch, structural fix, context patch, and process guardrail.
- Every remediation item has owner, acceptance criteria, verification method, and residual risk.
- If root cause is not proven, switch to evidence intake instead of writing a final plan.
- Include monitoring or regression signal when the same failure can recur.

## Handoff And Mental Model

- Handoff briefs say what is proven, what is assumed, what changed, what remains risky, and the exact next action.
- Workflow mental models name stages, decisions per stage, artifacts, quality gates, failure modes, diagnosis cues, and remediation paths.
- For unfamiliar domains, label missing expert knowledge as `needs-research` instead of creating production claims.

## Operator Wayfinding

- Trigger narrowly when the operator explicitly reports being lost, unable to name the next step, unsure whether to stop, or notices that AI has absorbed direction-setting. Do not interrupt a routine bounded task merely because the pack is active.
- Start with orientation: desired outcome, current stage, accepted decisions, completed evidence, active risks, and the last point where direction was still clear.
- Classify the primary block before prescribing action: `task-frame`, `knowledge`, `evidence`, `decision`, `mental-model`, `execution`, `drift`, or `diminishing-return` gap.
- For the current decision, separate `must-understand` (goal/trade-off/risk/stop signal), `safe-to-delegate` (reversible implementation detail with verification), and `needs-evidence-or-expert` (knowledge the AI must not invent).
- Teach only the smallest decision-ready mental model: why the choice matters, options, failure signals, and one authoritative source or artifact. Confirm understanding through the operator's decision/rationale, not a generic quiz.
- Model unresolved material choices as a dependency tree. The current frontier contains only decisions whose prerequisites are settled.
- Ask one material frontier question per turn by default. Batch only independent, low-cognitive-load decisions when the operator requests it.
- Each question includes a recommended answer, why it is recommended now, alternatives/trade-offs, and consequence if wrong. Always allow `accept`, `revise`, `defer/need evidence`, and `stop`.
- End each round with a compact checkpoint: what became clear, what remains open, one recommended next action, what not to do yet, and the stop/revisit condition.

## Continue, Pause, Pivot, Or Stop

- `continue`: objective and current stage still hold; the operator has decision-ready understanding, and one bounded next action plus expected evidence are clear.
- `pause`: a material decision, evidence source, expert review, recovery need, or external dependency must resolve first.
- `pivot`: objective remains valuable but evidence invalidates the current approach; record the changed assumption/decision.
- `stop`: objective no longer justifies cost/risk, conflicts with a controlling constraint, or no defined evidence could change the conclusion. Record consequences and revisit trigger when relevant.
