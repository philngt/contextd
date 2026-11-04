# Measuring contextd Effectiveness

contextd should be evaluated by whether it makes agent inputs more reliable, not by broad claims about model quality. The runtime already emits enough data to measure the first useful signals.

## What contextd Can Prove Today

| Signal | How to observe it | Why it matters |
|---|---|---|
| Deterministic selection | Run `contextd explain "task" --format json` and compare selected docs plus `source_hashes`. | Same source knowledge and task should produce the same build inputs. |
| Governance coverage | Run `contextd policy-check "task" --format json` and inspect required docs, contracts, categories, gaps, and violations. | Required context is selected or reported as missing before the agent works. |
| Agent efficiency proxy | Inspect `budget_report`, selected doc count, dropped docs, and estimated tokens. | The artifact stays focused instead of dumping an entire wiki into the agent. |
| Honest retrieval misses | Inspect `coverage`, scoped gaps, and the no-knowledge golden task. | Zero task-specific support remains visible in the compiled agent pack. |

## Minimal Demo Scorecard

Use this for a new user or team rollout:

```bash
contextd resolve --format json
contextd doctor --format json
contextd context "prepare agent context for product requirements" --format json --no-materialize
contextd explain "prepare agent context for product requirements" --format json
contextd eval --golden --workspace default --format json
```

Good first-run signals:

- `resolve` reports the expected workspace and `knowledge_root`.
- `doctor` returns `ok` before an agent session starts.
- `context` emits `artifact_type=contextd_task_context.v1`.
- `explain.summary.referenced_doc_count` is small enough to inspect.
- Gaps are actionable; a zero gap count does not establish complete task coverage.
- `artifact.coverage.status` distinguishes literal matches, declared routes,
  checked evidence routes, no match, and an unassessed query. `complete` stays false.
- `explain.summary.budget_report` shows selected, considered, dropped, and estimated token counts.
- `artifact.source_hashes` names the exact source docs behind the build.
- `eval --golden` passes for the bundled demo tasks.

## Negative Tasks and External Projects

The default golden set includes `add idempotency to kafka consumer`. The seed
workspace has no task-specific support on the configured implementation routes:
the expected result is zero referenced documents and a `knowledge-coverage` gap,
while general static guidance remains available. A positive category score must
never satisfy this fixture. The assertion is scoped to the retrieval routes;
it does not prove absence from every possible source in a workspace.

The [external-project example](../examples/external-project/README.md) runs the
same task from a separate payment project and knowledge root, then supplies an
OES graph to route it to an exact source excerpt. This checks both an honest
retrieval miss and useful evidence-backed selection without using contextd's
own project documentation as the task domain.

Graph validation checks graph conformance and exact source text. It does not
prove that the excerpt entails the assertion. Keyword matches remain a limited
fallback when no explicit route is available; aliases, ambiguity and incomplete
graphs can still affect retrieval. Unmatched literal terms are diagnostic data,
not automatic missing-knowledge claims.

Effective query terms exclude generic actions and software roles: an “OES
consumer” contract must not be selected for a Kafka task solely because both
contain `consumer`. A narrower topical match such as `kafka` may still provide
partial support. This is a deterministic eligibility guard, not a semantic
relevance model; meaningful aliases and ambiguous domain terms still need
authored routes or evidence.

A governance report of `ok` means the configured policy checks passed. Inspect
`coverage` and `gaps` independently: policy compliance alone does not establish
that task-specific knowledge was found.

## What Not To Claim Yet

Do not claim contextd reduces tokens by a fixed percentage, improves model answer quality by a fixed percentage, or beats a code graph/vector search system unless a reproducible benchmark exists.

Recommended wording:

- "contextd reports selected docs, dropped docs, gaps, source hashes, and budget estimates."
- "contextd makes context selection auditable before the agent works."
- "contextd helps teams test context selection with golden tasks."

Avoid wording such as:

- "contextd guarantees better answers."
- "contextd replaces code intelligence."
- "contextd is a memory database."
- "contextd reduces tokens by N percent."

## Team Rollout Metrics

For real teams, track 5 to 10 recurring tasks and record:

- expected docs selected vs actual docs selected
- required contracts present or reported as gaps
- wrong-workspace incidents
- policy violations caught before agent output
- number of corrective prompts caused by missing context
- context artifact size and estimated selected tokens

These metrics keep the product thesis grounded: contextd is useful when it turns maintained team knowledge into reliable agent inputs.
