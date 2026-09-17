# Domain cognition packs

A domain decision lens helps an agent connect evidence to a possible mechanism,
compare strategies, recognize exceptions, and verify an outcome. It is advisory
source material for the existing context build system, not a new reasoning
engine, an intelligence score, or proof of expert performance.

## Ownership and delivery

The canonical source depends on the manifest version:

| Profile | Guidance source | Runtime behavior |
|---|---|---|
| v3 | `knowledge.md` and `pack.yaml#retrieval` | Global Principles plus matched component sections |
| v2 compatibility | Existing `agents/` files and retrieval map | Existing full static guidance; no component slicing of those files |

`pack-ui-ux` is the migration pilot; `pack-operator-steering` already uses v3.
The other thirteen packs retain v2 and receive a bounded Domain Decision Lens
in their existing runtime-loaded `agents/coding-rules.md`. This is deliberate
staging, not a claim that every pack has been migrated. Enabled v2 packs still
cost static tokens even when none of their component keywords matches.

Do not duplicate this guidance in an independent eleven-directory hierarchy,
a second graph, or host-specific prompts. Domain facts stay workspace-scoped.
Agent hosts and C2O may consume built artifacts, but orchestration, permission
enforcement, and automatic knowledge promotion are not introduced here.

## Six questions for a useful lens

| Label | Authoring question |
|---|---|
| Observe | Which entities, states, actors, contracts, and evidence must be inspected? |
| Mechanism | What interaction could explain the observation? What would disconfirm it? |
| Choose | Which approaches fit which conditions, including reuse or no change? |
| Exception | When does the usual heuristic fail without relaxing a hard constraint? |
| Verify | What observable evidence establishes the outcome, and what remains untested? |
| Stop | What permission, evidence, budget, or owner decision is required before proceeding? |

Keep a cross-component lens short (target at most 650 estimated tokens), and
avoid generic advice repeated in every section. In v3 put observations and
mechanisms under Mental Model, choices and exceptions under Standards, concrete
symptoms under Failure Signals, and verification/stopping under Evidence And
Stop Conditions. Only genuinely cross-component requirements belong in Global
Principles: those tokens load even for a neighboring task.

The vocabulary discussed during design maps to existing sections rather than
new runtime stages:

| Authoring lens | Existing home |
|---|---|
| Primitives, knowledge, mechanisms, mental models | Mental Model and relevant workspace references |
| Principles, patterns, strategies | Standards, with applicability and alternative choices |
| Skills and procedures | Working conventions and verification methods |
| Judgment and exceptions | Conditional choices, counterexamples, and stop conditions |
| Mindset and wisdom | Evidence discipline, scope, decision ownership, and when not to act |

These categories overlap. They are neither a standardized cognitive hierarchy
nor a promise that a plugin supplies human experience or judgment.

## Example: design hierarchy

Observation: a target task is difficult to locate among competing controls.
Mechanism hypothesis: similar prominence or ambiguous grouping may obscure the
intended action. Options include regrouping, changing emphasis, or deferring
secondary controls. An expert comparison tool can legitimately need several
peer actions; blindly imposing one primary action can harm its task.

Verification needs actual task observations and relevant accessibility checks,
not merely a cleaner screenshot. This is a hypothesis to test, not a universal
claim about scan order or a fixed number of controls.

## Rules, provenance, and compatibility

A heuristic never overrides an inherited strict constraint. Preserve stable
constraint IDs, executable validator IDs/severities, scope boundaries, component
names, and retrieval routes when migrating. Keep v0.x legacy filenames as marked
adapters, with canonical rule and retrieval parity checked by `pack-validate`.
Do not create an exception by deleting inconvenient legacy requirements.

The UI migration preserves its inherited design baseline. The static checks can
find selected literals or missing documentation markers; they do not measure
contrast, execute a screen reader, or certify WCAG conformance. The A11y example
uses `> A11y: ...`, matching the existing validator's actual marker.

Content-only packs receive patch versions. The UI v3 migration receives a minor
version. Existing `reviewed_on` dates are retained: this change is not a renewed
review of every external framework or standard. New factual guidance needs a
source and applicable version; proposed local lessons need review, scope, and
reconsideration conditions before becoming shared guidance.

## Evaluation: distinguish plumbing from usefulness

Run these deterministic gates from a source checkout:

```bash
python scripts/cli.py pack-validate --all --format text
python scripts/test_pack_cognition.py
python scripts/test_contextd_runtime.py
```

The cognition tests cover all first-party packs, actual component routing,
positive and neighboring-negative tasks, runtime delivery, UI component slicing,
static token accounting, repeated-build identity, validator fixtures, and
preserved compatibility boundaries. The baseline fixture records the previous
UI static-pack cost and hashes of unchanged manifest fields and validator code from commit
`303bb1a6a3860a6cea5e8673360e0afb106278f3`; it is a regression reference, not
another editable knowledge source. Do not update it just to silence a failure:
explain an intentional contract change and review it separately.

The scenario fixture also contains manual quality-review cases. The automated
suite verifies their presence and routing, **not** that a model reasons correctly.
For an agent trial, hold model/version, tools, task inputs, permissions, and time
budget fixed. Compare a baseline run with a pack-enabled run on held-out tasks;
retain outputs and evaluator observations, including failed and uncertain cases.
Score causal diagnosis, context-fit of the selected strategy, observed outcome,
missed constraints, unjustified action, and intervention/rework separately.
Blind artifact review where feasible; repeat stochastic runs and report sample
counts and uncertainty. Do not equate a longer explanation with a better result.

This PR ships no live model benchmark and makes no measured capability claim.
Structural gates cannot establish the truth of domain hypotheses or usability.

## Creating or migrating another pack

Start with `python scripts/scaffold-pack.py pack-{your-name}` and fill the
existing [knowledge template](../templates/pack-knowledge.md). Inventory the old
rules and routes before migration; add task-specific counterexamples, safe
non-trigger fixtures, and a static-budget assertion. Migrate one reviewed pack
at a time rather than automatically summarizing away legacy obligations.

See [pack validation](pack-validation.md) for required headings, ID parity,
routing safety, and the compatibility profile.
