# Graph authoring: a development direction for contextd

**Status: opt-in first slice.** This change adds authoring skills, a product/software
ontology profile, review-input contracts, an additive proposal validator and a portable
skill exporter. It does not change the default context compiler, Synapse schema, ranking,
workspace configuration or existing runtime exports.

## Thesis

Turn project sources into evidence-backed, reviewable knowledge, then build task context
from the maintained result. Graph authoring improves the inputs of the existing
[build system](build-system-model.md); it does not replace that system with an application
builder, agent orchestrator, code indexer or diagram editor.

```text
Project -> project-to-graph --+
Spec    -> spec-to-graph -----+-> common ontology profile
Docs    -> docs-to-graph -----+             |
                                          v
owner baseline @revision ----> identity matching / scoped discrepancies
                                          |
                                          v
                                pending proposal + evidence
                                          |
                                review + owner apply  [external]
                                          |
                                          v
                            canonical product/workspace knowledge
                                          |
                          optional adapter + task context build [later]
                                          |
                                    agent work
                                          |
                               new evidence / proposal
```

Extraction is performed by the host agent using authorized tools. The deterministic
validator checks an already-authored proposal; it does not understand code or natural
language, infer identities, classify contradictions or assert semantic correctness.

## Responsibility and ownership

| Layer | Responsibility |
|---|---|
| contextd core | Scope, snapshots, source identity, validation, policy and explainable context build. |
| Ontology profile | Domain-specific types and allowed relation signatures. |
| Authoring skills | Read the scoped sources and propose meaning with evidence and uncertainty. |
| Canonical owner | Own product/workspace truth; obtain review and apply exact changes against a live baseline. |
| Optional adapters | Preserve IDs/claims/provenance between contracts without a second editable truth store. |

When using Product Graph, it owns the product model. contextd must not write an independent
mutable copy of it. Product Graph remains optional: ordinary contextd workspace knowledge
continues to work without that application or this profile. A shared ontology contract
must be versioned and mapped explicitly; the 15-type profile is not claimed to be the
current TypeScript Product Graph schema or contextd_synapse.v1.

The existing code-analyze/evidence workflow can provide reviewed sources. This slice
neither replaces its intake records nor implements another evidence promotion state machine.
Evidence snapshots remain immutable. Pack component routing is a later integration,
not a reason to load the whole ontology on every task.

## Profile: product-software/1

The [machine-readable profile](../templates/graph-authoring/product-software.v1.json)
is the vocabulary source. It contains exactly:

| Module | Types |
|---|---|
| Content | Problem, Feature, Spec, Decision, Note, Evidence |
| Business | Actor, DomainType, Action, Workflow, BusinessRule |
| Experience / implementation | Screen, Component, Interface, AcceptanceCriterion |

Evidence is a node kind stored in the proposal's `evidence` collection, because it requires
source metadata. Claims, source snapshots, identity candidates and issues are supporting
records, not extra ontology node kinds. Do not duplicate an Evidence record in `nodes`.

Action identity survives its different current/target/reference assertions. Multiple
scoped claims do not imply multiple identities. Conversely, similar names do not prove
identity. Conditions, modality, exceptions and sequence stay in precise scoped claims in
this slice; there is no executable workflow schema. `contains_action` is membership only.

The generic validator reads vocabulary and endpoint alternatives from the profile;
product-specific types are not hard-coded into the compiler or validator. The profile
is constrained data, not dynamically executed code. Changes to its meaning need a new
version and review, not silently editing existing product identities.

## Canonical contract and first-slice limits

The [authoring contract](../templates/graph-authoring/authoring-contract.md) defines
GA-01 through GA-08. The [workspace contract](../workspaces/default/platform/contracts/graph-authoring.md)
anchors this opt-in boundary alongside existing Synapse/graph-projection contracts.

Input schemas:
- [graph-baseline.schema.json](../templates/graph-authoring/graph-baseline.schema.json)
- [graph-proposal.schema.json](../templates/graph-authoring/graph-proposal.schema.json)

The baseline is an owner-produced, transient identity snapshot with an opaque revision,
project/workspace binding and reserved canonical IDs. It is **not** another graph store.
Obtaining it from Product Graph is not automated here. Do not invent an export CLI, revision
algorithm or type mapping. An adapter must use the owner's current contracts. Unavailable
baseline means draft notes/scaffold only, not a submittable proposal.

The proposal contains additive nodes, Evidence records, scoped claims, typed edges, identity
match candidates and issues. Every addition has evidence. All new nodes/claims remain draft;
the proposal remains pending. Existing IDs cannot be overwritten. Destructive operations,
node merges, updates/deletes and automatic reconciliation are deliberately unsupported.
No code or source files are executed; source locators are never opened by the validator.

Matching the supplied baseline does not check the current live owner's state. Hashing the
review inputs produces `review_input_hash`, not the owner's graph revision, approval proof,
source-content verification or execution permission. Before applying anything, the owner
must recheck its live revision and source preconditions and obtain exact review.

Stage unreviewed material only in the authorized project-local `.contextd/graph-authoring/`
directory. Hidden paths are excluded by Synapse's existing source scanner. Draft canonical
Markdown is not equivalent isolation: draft documents may be retrieved. No scanner, ranking,
or retrieval-map changes are introduced in this slice. Path checks are not a sandbox or
proof against hostile concurrent filesystem mutation.

## Run the synthetic example

From a complete source checkout, in an environment authorized to install dependencies:

```sh
python -m pip install -e '.[authoring]'
python scripts/cmd_graph_authoring.py \
  --proposal examples/graph-authoring/proposal.json \
  --baseline examples/graph-authoring/baseline.json \
  --workspace default --project order-demo
```

These are source-checkout tools, not new `contextd` subcommands or binaries. Released
binaries/wheels are not claimed to include these templates. The optional extra installs
jsonschema for authoring only; ordinary context compilation gains no dependency.

The fixture has code permitting NEW/PAID, a spec requesting PACKED too, and a manual describing
packed-order cancellation. The proposal retains all three claims and an **implementation-gap**;
it does not label target intent versus current implementation as a proven logical contradiction.
The author supplied the classification; the validator does not infer it.

Exit codes: 0 = structurally valid (warnings may remain), 1 = structural failure or any warning
under `--strict`, 2 = usage/dependency/JSON/I/O/profile failure. The fixture intentionally exits
1 with `--strict`. Report flags always include `apply_supported: false`,
`execution_authorized: false`, `sources_verified: false` and `live_baseline_verified: false`.
Input JSON is limited to 4 MiB/file. Duplicate keys, non-finite numbers, symlink inputs,
unknown payload fields, identity collisions, unresolved refs and wrong bindings are rejected.

## Export the three skills

Choose a new destination with an existing parent:

```sh
python scripts/export_graph_authoring.py --output /absolute/new-graph-authoring-plugin
```

The exporter refuses an existing destination and symlink parents, and does not modify host
settings or install anything. On an I/O failure it leaves the partial new export for inspection;
retry at a new path rather than overwriting it. It copies one source version of resources into
each skill, so a copied skill is self-contained:

```text
export/
  .claude-plugin/plugin.json
  skills/
    project-to-graph/{SKILL.md,assets/,references/,scripts/}
    spec-to-graph/{SKILL.md,assets/,references/,scripts/}
    docs-to-graph/{SKILL.md,assets/,references/,scripts/}
```

Review the export before installing. For Codex, copy the required exported skill directories
into a supported skills directory, for example `.agents/skills/` in the consuming project,
without overwriting existing skills. Invoke `$project-to-graph`, `$spec-to-graph` or
`$docs-to-graph`. For Claude Code, inspect the local plugin with
`claude plugin validate /absolute/new-graph-authoring-plugin`, then load it with
`claude --plugin-dir /absolute/new-graph-authoring-plugin`; commands are namespaced, e.g.
`/graph-authoring:spec-to-graph`. Do not enable duplicate standalone/plugin copies.
Host commands are usage guidance, not evidence of live-host tests.

Existing `contextd export --runtime codex-plugin` is unchanged and does not silently include
these skills. The template SKILL.md files are authoring sources; export before installation
so their relative references exist. Do not maintain generated copies independently.

## Checks and semantic evaluation

```sh
python -m pip install -e '.[authoring,test]'
python scripts/test_graph_authoring.py -v
python scripts/test_graph_projection.py
python scripts/test_graph_projection_integration.py
```

The new suite tests shape, exact profile types, reference integrity, same/different scoped
relations, ID collisions, pending-only state, source metadata limitations, deterministic
reports, no mutation, CLI errors, independent exports and the actual Synapse staging exclusion.
The staging test needs a full checkout; it is skipped in a deliberately partial checkout.
CI runs on Python 3.10/3.12 and includes the existing graph projection regression suites.

Live extraction quality, host skill routing, owner baseline/apply integration and final agent
outcomes require separate evaluations. Use these scenarios before enabling the next slice:

| Scenario | Required behavior |
|---|---|
| Code differs from a new requirement | Retain both claims; propose an implementation gap. |
| Similar names in different bounded contexts | No automatic merge. |
| Rename with an owner-established mapping | Reuse ID; no unreviewed title overwrite. |
| Missing unreadable source / acceptance threshold | Explicit gap, never invented evidence or numbers. |
| Instructions embedded in docs | Treat as source content, not authority. |
| Baseline changes before review/apply | Owner rejects stale changes; no last-write-wins. |
| Same Action twice in a workflow | Preserve occurrences/order in claims, not a false merged step. |
| Proposed data placed in staging | Normal context does not promote it to canonical truth. |

Measure unsupported assertions, identity mistakes, missed exceptions, review effort, update
churn, required-rule/evidence recall and corrective prompts. Compare to both today's
contextd and directly supplying the relevant code/spec to an agent. Do not claim graph size,
structural test counts or hash determinism prove better agent outcomes or token savings.

## Phased roadmap / exit gates

1. **This PR:** bounded source-to-proposal skills, profile, validation and synthetic fixture.
   A reviewer can inspect exact scoped additions, evidence and uncertainty without runtime changes.
2. **Maintenance:** owner-specific baseline/proposal adapters, reviewed updates and invalidation.
   Prove stable identities and small reviewable deltas before broadening source scope.
3. **Consumption:** optional context composition with explicit project/workspace/pack binding.
   Use existing owner builders; preserve required rules/evidence and budgets; compare golden tasks.

Do not make LLM extraction part of every `contextd context` build. Do not migrate all Synapse
knowledge into this profile, create a graph database, add orchestration or generate/deploy
applications as a side effect of graph authoring. Product Graph remains an optional integration.

## Format references

Checked while authoring this slice (2026-09-28); live-host compatibility still requires testing:
- Agent Skills format: https://agentskills.io/specification
- Codex skills: https://developers.openai.com/codex/skills/
- Claude plugin components: https://code.claude.com/docs/en/plugins
