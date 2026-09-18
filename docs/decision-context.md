# Decision-first context

contextd supplies the context a capable agent needs to **choose well in this
situation**, rather than reteaching a whole discipline or requiring a packaged
skill before every action. This is an author-controlled projection of existing
v3 packs, not an agent runtime, model training, or a claim of general intelligence.

## What always travels, and what can be deferred

For an explicitly profiled pack, the selected component's **Strategy, Judgment,
Standards, Failure Signals, and Evidence And Stop Conditions** travel together
with a compact Mental Model and the pack's Global Principles. Local facts,
controlling definitions, permissions, required procedures, and workspace/engine
constraints are not classified away. Workspace retrieval and priority are
unchanged; existing gaps and governance violations remain visible.

Generic foundations (primitives, definitions, mechanisms, principles, mental
models) are optional supplementary material. A strategy can retain a short causal
rationale without loading a tutorial. Patterns are possible approaches, not
automatic choices. Procedural skill documents are optional assistance, not a
required dependency of a strategy. Agents may execute with their existing
capabilities and available tools, subject to actual permission and verification.

The compiler does not know what a model has learned. Opt-in is an author/owner
assumption to validate against target models and tasks, **not** the model saying
“I already know this.” A host can request a foundation for a novel concept,
version-specific behavior, conflicting evidence, or a demonstrated knowledge
gap; it can request a procedure when an unfamiliar tool or fragile operation
needs it. Required material belongs in core, regardless of its cognitive label.

## Opt-in pack contract

Add `context_profile: decision-first` to a **manifest v3** pack. The canonical
source is still `knowledge.md`; `pack.yaml#retrieval` still owns component routes.
Existing v1/v2 packs and unprofiled v3 packs keep their previous loading behavior
and default artifact identities. No eleven-folder layout, model profile database,
second graph, or dependency on C2O is introduced.

Each profiled component has these unique level-three headings:

```markdown
## Component: your-component
### Mental Model
Observed state, boundaries and the minimum rationale for this task family.
### Standards
Controlling requirements, including required knowledge or exact procedures.
### Strategy
Conditional alternatives, objectives, costs and the option not to change.
### Judgment
Contrasting situations, exceptions, contrary evidence and revisit conditions.
### Failure Signals
Observable errors and misleading “success” signals.
### Evidence And Stop Conditions
Outcome evidence, unresolved authority and stopping conditions.
### Foundation: your-concept
Optional definitions or deeper explanation.
### Procedure: your-recipe
Optional suggested execution sequence; not a mandatory prerequisite.
```

Foundation/Procedure headings are optional, repeatable under distinct slug IDs,
and **only allowed inside components**. All other component sections, the
preface, and Global Principles are retained. Do not hide requirements in optional
blocks. Validation rejects duplicate/unknown components, empty core/support
sections, malformed support IDs, optional Global Principles blocks, uppercase
MUST/SHALL/PHẢI obligations in optional blocks, and stable rule IDs defined only
in optional support. Fenced examples are not headings. These mechanical checks
cannot prove semantic safety; review conditional guidance and all moved rules.

An exact support reference is `pack-name/component/section-id`. It is a local
identifier, never a path, URL, executable instruction, or permission grant.
Foundation and procedure IDs are unique within their component. A request must
match its kind, an enabled profiled pack and a component already routed by the
task. Unknown, inactive, mistyped or out-of-task requests fail before writing;
use `contextd explain` to inspect the available IDs and refine the task when its
component was not selected. No hidden semantic routing or confidence heuristic.

`pack-ui-ux` 0.4.0 is the shipped pilot. The other fourteen packs are unprofiled;
operator steering retains ordinary v3, and thirteen packs retain v2 full static
loading. The scaffold template opts new v3 packs into this profile after authors
complete their placeholder guidance.

## CLI

Enable `pack-ui-ux` in the active workspace or the project's existing pack override
before these examples. A per-project `packs` array replaces workspace defaults;
preserve other required packs rather than blindly replacing the array.

```bash
# Core strategy/judgment and required constraints; no optional support bodies.
contextd context "Review keyboard navigation" --preview --format json

# See loaded/deferred support IDs and reasons without opening every file.
contextd explain "Review keyboard navigation" --text

# Request unfamiliar foundation; no procedure is implied.
contextd context "Review keyboard navigation" --preview --foundation pack-ui-ux/accessibility/semantics-basics

# Request a documentation recipe; no foundation is implied.
contextd context "Review keyboard navigation" --preview --procedure pack-ui-ux/accessibility/document-accessibility

# Full support for the selected components only, not the entire pack corpus.
contextd context "Review keyboard navigation" --preview --context-detail full
```

`--foundation` and `--procedure` are repeatable and normalized to sorted unique
IDs. `context`, `task-context`, and `explain` accept the same options, including
the direct command-module entry points. Without `--preview`, `context` retains
its existing materialization behavior.

## Python and MCP

The public snapshot/artifact/explanation builders accept an optional keyword-only
`support_request` object:

```python
request = {
    "detail": "decision-first",  # or "full"
    "foundations": ["pack-ui-ux/accessibility/semantics-basics"],
    "procedures": [],
}
# task_context_engine.build_context_snapshot(..., support_request=request)
```

The existing MCP `contextd.context` tool accepts `context_detail`, `foundations`
and `procedures` in addition to its existing task/workspace/cwd/materialize fields.
It delegates to the same compiler. No new MCP tool, model call or execution step
is needed. General library `find`, `bundle`, or resource-read operations remain
explicit discovery/export surfaces; they are not decision-filtered task builds.

## Artifacts, provenance and budget

The additive `decision_context` report records the normalized request, profiled
and unprofiled packs, loaded/deferred references with reasons, and character-based
source-content token estimates. Deferred support contributes metadata, not its
body. The JSON artifact, task Markdown, explanation and compiled pack expose the
same decision selection. An explicit self-route to canonical pack knowledge
cannot reintroduce an unsliced copy through referenced documents.

`source_hashes` still hash full original bytes, so an edit to a deferred section
invalidates the source identity. Decision-profile pack identities additionally
bind the request and projected content/sections. Decision-first, full, and
specific support requests cannot overwrite each other's materialized pack paths
merely because they read the same source files. Materialization verifies this
identity before any writes and reuses the built snapshot without rereading
workspace sources. Profiled knowledge cannot resolve outside its pack boundary.

Budget fields retain their existing source-content accounting semantics and are
recomputed after projection. They exclude JSON/report/wrapper overhead and are
not model-tokenizer measurements or hard token caps. Required content is not
silently trimmed to fit a target. Existing policy checks are run on the final
artifact; this change does not expand the semantics of a policy's legacy
`max_estimated_tokens` check (selected referenced content only).

## Evaluation and limits

Run `python scripts/test_decision_context.py`, the existing pack/runtime/schema
suites, and `contextd pack-validate --all`. Tests cover selective delivery, hard
core preservation, independent support requests, CLI/MCP parity, scope/path
rejection, safe fallbacks, identity, materialization, and fenced examples.

For a separate agent trial, compare the same model/tools/task data with (A)
constraints and task facts, (B) added foundations, (C) added strategy/judgment,
and (D) C plus on-demand support. Retain failed/uncertain outputs, total context
including follow-up requests, interventions, and actual outcomes. Evaluate
situational decisions and constraint violations, not prose sophistication.
This change ships **no live model benchmark** and claims no measured improvement
in intelligence, design quality or execution reliability.

Authoring reference: [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
(accessed 2026-09-18), on avoiding redundant teaching, choosing appropriate
procedural specificity, and testing target models. This supports the authoring
approach, not a benchmark result for contextd.
