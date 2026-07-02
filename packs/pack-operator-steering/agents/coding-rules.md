# pack-operator-steering — Working Rules

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
