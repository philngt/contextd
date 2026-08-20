# Pack Validation

`contextd pack-validate` verifies both the runtime API of a pack and its
versioned authoring-quality contract.

## Compatibility profiles

- Legacy manifests without `manifest_version` (or with version `1`) remain
  loadable and receive an informational migration notice.
- `manifest_version: 2` retains the seven-file compatibility contract.
- `manifest_version: 3` is required for newly scaffolded packs and enables one
  canonical knowledge file plus manifest-owned retrieval.
- Unknown manifest versions are errors. This prevents a newer contract from
  being silently interpreted as an older one.

The v2/v3 authoring schema is
[`templates/pack.schema.json`](../templates/pack.schema.json). Runtime
validation remains implemented in `scripts/lib/pack_validation.py` so the CLI
does not require a JSON Schema dependency.

## Checks for every pack

- `pack.yaml` exists, parses, and its `name` matches `pack-{slug}` directory.
- Version/description/components exist; components are unique.
- `keywords` only reference declared components.
- Declared file paths are relative, traversal-safe, and present.
- `conflicts_with` references known packs.
- Retrieval rows only use declared components.
- Retrieval paths cannot be absolute, traverse parents, cross workspaces, or
  read another pack.
- A documented validator catalog requires a declared executable rule script.
- Component slugs and exact routing keywords are unique across the pack catalog;
  collisions fail fast instead of making context selection order-dependent.

## Additional manifest v2 checks

- Semver version; valid status/category; ISO review date.
- At least one supported audience and task type.
- Non-empty include/exclude scope boundaries without overlap.
- Component slugs are normalized.
- Every component has at least three unique routing signals.
- The same keyword cannot own multiple components in one pack, which would make
  routing ambiguous and add unnecessary context.
- All seven standard pack files are declared.
- README documents activation, exclusion boundary, retrieval behavior, and
  verification.
- Constraints expose stable `pack-{name}-...` group IDs.
- Common pitfalls contain at least five numbered entries.
- Every documented Layer-1 rule ID is implemented and every implemented ID is
  documented.

## Additional manifest v3 checks

- Every component has a non-empty canonical `pack.yaml#retrieval` row.
- `files.knowledge` and `files.validator_script` are declared and readable.
- `knowledge.md` contains `## Global Principles`.
- Every component has one exact `## Component: {slug}` section with
  `### Mental Model`, `### Standards`, `### Failure Signals`, and
  `### Evidence And Stop Conditions`.
- Standards expose stable `pack-{name}-...` IDs and every implemented validator
  ID is documented there.
- If a legacy `agents/pipeline/retrieval-map.md` adapter remains, it must exactly
  match canonical manifest retrieval. Drift is an error.
- A legacy `agents/**/*.md` adapter may not define a stable pack rule ID absent
  from canonical knowledge.

These checks deliberately do not claim that a technology recommendation is
current. Provider/framework packs must also carry an official baseline link,
review date, and workspace-pinned compatibility contract.

## CLI and exit codes

```bash
contextd pack-validate --all --format json
contextd pack-validate --pack pack-product --format text
```

- `0`: no errors or warnings (informational migration notices are allowed).
- `1`: one or more errors.
- `2`: warnings only.

`contextd doctor` includes validation for the effective packs of the current
codebase. CI should validate all first-party packs:

```bash
contextd pack-validate --all --format text
```

## Validate usefulness, not only shape

A zero-issue report proves the pack contract is internally consistent. It does
not prove good retrieval or domain correctness. Before release, also test:

1. Representative positive tasks select the intended component/docs.
2. Neighboring negative tasks do not select the pack.
3. `contextd explain` shows no irrelevant high-cost candidates.
4. The budget report includes static pack guidance and remains below the target
   total for representative multi-pack tasks.
5. Layer-1 fixtures fire every documented executable rule and include safe
   non-trigger cases.
6. Layer-2 guidance cites current official sources where behavior can change.

```bash
contextd context "{positive task}" --preview --format json
contextd explain "{positive task}" --format text
contextd context "{negative neighboring task}" --preview --format json
python scripts/validate.py --file <fixture> --workspace <workspace-with-pack>
```

Keep retrieval entries relative to the active workspace unless they
intentionally start with `packs/{active-pack}/` or `templates/`. Missing
workspace knowledge should become an explicit context gap, never an implicit
guess or a cross-workspace lookup.
