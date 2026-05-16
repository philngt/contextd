# Verified Facts — 2026-05-08-engine-bootstrap-wiki-template

> Source evidence: `2026-05-08-engine-bootstrap-wiki-template` (variant=agentic-engine)
> Workspace: `wiki`
> Generated: 2026-05-08T00:00:00+07:00
> Compiled from batches 1–6 (19 P0/P1 answered, 5 P2/P3 deferred)
>
> **Authoritative input cho `/evidence-apply`** — mỗi fact có Affects path → router quyết định create/edit.

---

## Block: Platform Patterns

### F-001 — Pattern workspace-resolve-step0
- **Confidence**: high
- **Source**: q-001 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/workspace-resolve-step0.md` (create)
- **Statement**: Engine-level invariant pattern. 5-step structure: find `.claude/wiki.json` → resolve `wiki_root` → STOP if `.workspace` empty → set `{ws}` → validate `workspace.md`.
- **Apply**: Use a03#P-001 canonical structure. Workspace override KHÔNG apply.
- **Index**: Add row vào `{ws}/patterns-index.md` Platform Patterns table.

### F-002 — Pattern askuser-confirm-preview
- **Confidence**: medium
- **Source**: q-002 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/askuser-confirm-preview.md` (create)
- **Statement**: UX pattern cho irreversible filesystem ops. Preview block + AskUserQuestion 3 options (primary action / edit-detail / cancel). Cancel BẮT BUỘC.
- **Apply**: Use a03#P-002 canonical. Apply cho commands có side effects (tạo evidence, edit wiki, scaffold workspace).
- **Index**: Add row vào `{ws}/patterns-index.md`.

### F-003 — Pattern secrets-blocklist-gate
- **Confidence**: high
- **Source**: q-003 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/secrets-blocklist-gate.md` (create)
- **Statement**: Security-critical 5-tier guard. Tier 1 hard blocklist (NEVER READ) + Tier 2 AskUser confirm + Tier 3 redaction + Tier 4 guard log + Tier 5 workspace override (add only).
- **Apply**: Use a03#P-003 + cite `agents/pipeline/code-snapshot-conventions.md:L156-L251`.
- **Index**: Add row.

### F-004 — Pattern redaction-post-pass
- **Confidence**: high
- **Source**: q-004 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/redaction-post-pass.md` (create)
- **Statement**: Companion với F-003. Post-build scan cho password/token/api-key/secret/jwt-key/email/URL-with-creds patterns. STOP-on-secret = irreversible.
- **Apply**: Use a03#P-004 canonical.
- **Index**: Add row.

### F-005 — Pattern evidence-state-machine (PAIR with F-010 contract)
- **Confidence**: high
- **Source**: q-005 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/evidence-state-machine.md` (create)
- **Statement**: Implementation skeleton: 7-state DAG (ingested → analyzed → qa_in_progress ⇄ qa_awaiting_external → qa_done → applied → archived). Storage: `{ws}/evidence/_index.md` Active table.
- **Apply**: Pattern cite contract F-010. Cross-reference 2 chiều.
- **Index**: Add row.

### F-006 — Pattern citation-rule (PAIR with F-011 contract)
- **Confidence**: high
- **Source**: q-006 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/citation-rule.md` (create)
- **Statement**: Implementation skeleton cho citation. Format: `({path}:L<start>[-L<end>])` relative to repo root. Bundle prefix variant: `({repo-name}/{path}:L..-L..)`. Anchor: `(raw.md#section-N)`.
- **Apply**: Pattern cite contract F-011.
- **Index**: Add row.

### F-007 — Pattern multi-stage-subagent-pipeline (NOT flagship — user override)
- **Confidence**: high
- **Source**: q-007 (self, user-override) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/multi-stage-subagent-pipeline.md` (create)
- **Statement**: 5-stage `/use-wiki` flow: Stage 0 (workspace resolve) → Stage 1 (planner) → Stage 2 (context-selector) → Stage 2.5 (plan-reviewer gate) → Stage 3 (Builder) → Stage 4 (reviewer optional).
- **Apply**: Use a03#P-007 canonical structure. **DO NOT** mark as flagship in `{ws}/patterns-index.md`. **DO NOT** cross-reference từ `{ws}/workspace.md`. Pattern listed normally trong patterns-index (alphabetical hoặc grouping bình thường).
- **Index**: Add row (normal position, không top).

### F-008 — Pattern variant-discriminated-dispatcher (v1, single-instance)
- **Confidence**: medium
- **Source**: q-008 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/patterns/variant-discriminated-dispatcher.md` (create)
- **Statement**: 6-step canonical: detect → validation gate per variant → scope default per variant → output template per variant → source.yaml field → downstream dispatch by variant. Version v1 — single instance (variant=agentic-engine).
- **Apply**: Use a03#P-008. **Note inline**: "single instance — pattern shape may evolve khi variant thứ 3 được introduce".
- **Index**: Add row với version note.

---

## Block: Platform Contracts

### F-009 — Contract evid-id-format
- **Confidence**: high
- **Source**: q-009 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/evid-id-format.md` (create)
- **Statement**: `{YYYY-MM-DD}-{src}-{slug}[-{n}]` với `src ∈ {paste, api, mcp, code, engine, platform}`. `slug` kebab-case ≤ 30 chars. Future src additions update contract version.
- **Apply**: Use a04#C-001. Reference từ F-010 contract (state machine).

### F-010 — Contract evidence-state-machine-transitions (PAIR with F-005 pattern)
- **Confidence**: high
- **Source**: q-005 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/evidence-state-machine-transitions.md` (create)
- **Statement**: Invariant rules — transition ownership (chỉ owning command được transition tương ứng), no-skip DAG, `_index.md` as SoT, I-2 workspace lock invariant. Ownership table:
  - `(none) → ingested`: `/evidence-ingest`, `/code-analyze`, `/obsidian-ingest`
  - `ingested → analyzed`: `/evidence-analyze` (CORE set complete)
  - `analyzed → qa_in_progress`: `/evidence-qa`
  - `qa_in_progress ⇄ qa_awaiting_external`: `/evidence-qa`
  - `qa_in_progress → qa_done`: `/evidence-qa` (verified-facts.md complete)
  - `qa_done → applied`: `/evidence-apply`
  - `applied → archived`: manual
- **Apply**: Pattern F-005 cite contract; contract cite pattern. Cross-reference 2 chiều.

### F-011 — Contract citation-format (PAIR with F-006 pattern)
- **Confidence**: high
- **Source**: q-006 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/citation-format.md` (create)
- **Statement**: Validator behavior — reject paths absolute, reject paths cross-workspace (outside `workspace_at_ingest`), reject paths outside `code_scope`. Re-prompt 1 lần với reminder; persistent miss → mark `[NO-CITE]` + warn.
- **Apply**: Use a04#C-006. Cross-ref pattern F-006.

### F-012 — Contract evidence-file-layout
- **Confidence**: high
- **Source**: q-010 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/evidence-file-layout.md` (create)
- **Statement**: Layout invariant per evid-id: `sources/{id}/{source.yaml REQUIRED, raw.{ext} REQUIRED, raw.normalized.md? CONDITIONAL when raw>50KB}` + `analysis/{id}/{NN|cNN|aNN}-*.md` + `qa/{id}/{recommendations.md, batches/, todo.json, verified-facts.md, pending-external.md?}` + `_index.md` (single source of truth cho state).
- **Apply**: Use a04#C-002. Cross-ref F-010 (`_index.md` as SoT).

### F-013 — Contract raw-md-section-structure (1 đa-variant)
- **Confidence**: high
- **Source**: q-011 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/raw-md-section-structure.md` (create)
- **Statement**: 1 contract đa-variant với variant table inline:
  - variant=code: 10 sections (Project metadata / Dependencies / Configs / REST endpoints / Message consumers / Services / DB schema / Public APIs / Git summary / Notes)
  - variant=agentic-engine: 10 sections (Engine metadata / Dependencies / Configs / Slash commands / Sub-agents / Pipeline / Templates / Hooks / Git summary / Notes)
  - bundle mode: Section 0 + per-repo Sections 1–9 với heading suffix `[{repo-name}]` + Docs section
- **Apply**: Use a04#C-003. Variant table extensible cho future variants.

### F-014 — Contract source-yaml-required-fields (KEEP unified)
- **Confidence**: medium
- **Source**: q-012 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/source-yaml-schema.md` (create)
- **Statement**: KEEP unified contract. Always-required: evid_id, source_type, origin, label, fetched_at, fetched_by, sha256, raw_filename, raw_size_bytes, normalized, workspace_at_ingest. Conditional (source_type=code): code_variant, git_sha, git_branch, code_scope, code_repo_path. Conditional (bundle): code_repos[], include_docs[].
- **Apply**: Use a04#C-004. Revisit tách C-004a nếu conditional grow phức tạp (5+ variant-specific fields).

### F-015 — Contract slash-command-naming
- **Confidence**: medium
- **Source**: q-013 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/slash-command-naming.md` (create)
- **Statement**: RULE (universal): kebab-case + lowercase + hyphens. RECOMMENDATION (non-binding): "subject-verb" cho commands mới (consistency với evidence-* và wiki-* groups). KHÔNG break 5 existing commands có "verb-subject" pattern.
- **Apply**: Use a04#C-007. Document BOTH conventions as valid.

### F-016 — Contract sub-agent-frontmatter-schema
- **Confidence**: medium
- **Source**: q-014 (self) — answered 2026-05-08
- **Affects**: `{ws}/platform/contracts/sub-agent-frontmatter-schema.md` (create)
- **Statement**: Required fields: `name`, `description`, `tools`, `model`. Convention (non-binding): `description` chứa "DÙNG KHI" (positive trigger) + "KHÔNG DÙNG" (negative trigger / scope constraint). Tools allowlist principle (read-only vs write-allowed) deferred (G-009 sample size concern).
- **Apply**: Use a04#C-008.

---

## Block: Service docs (engine project)

### F-017 — Doc strategy + location
- **Confidence**: high
- **Source**: q-015, q-016 (self) — answered 2026-05-08
- **Affects**: `{ws}/projects/engine/services/` (create dir + 7 docs from a05 drafts)
- **Statement**: Option B grouping — 6 group docs theo category + 1 agents doc:
  - `workspace-ops.md` (E-001..E-005)
  - `wiki-usage.md` (E-006..E-008)
  - `codebase-analysis.md` (E-009)
  - `reporting.md` (E-010)
  - `observability.md` (E-011..E-013, including `/wiki-viz`)
  - `evidence-pipeline.md` (E-014..E-018)
  - `agents.md` (A-001..A-005)
- **Apply**: Apply a05 drafts directly. `{TODO: ask expert}` markers leave as-is (convert to follow-up questions in next session if user wants refine).

---

## Block: Decisions (ADRs)

### F-018 — ADR 001 introduce variant=agentic-engine
- **Confidence**: high
- **Source**: q-017 (self) — answered 2026-05-08
- **Affects**: `{ws}/decisions/001-introduce-agentic-engine-variant.md` (create)
- **Statement**: Apply a06 D-001 draft as ADR. Status field = "ACCEPTED" (decision đã thực thi trong session 2026-05-08). Use template `templates/adr.md`.
- **Apply**: Use a06#D-001 (alternatives, trade-offs, citation 5 surfaces).

### F-019 — ADR 002 keep code-analysis-prompts.md monolithic
- **Confidence**: high
- **Source**: q-018 (self) — answered 2026-05-08
- **Affects**: `{ws}/decisions/002-keep-code-analysis-prompts-monolithic.md` (create)
- **Statement**: KEEP per D-002. Revisit triggers: file > 1500 lines / variant #3 introduced / user feedback navigation slow.
- **Apply**: Use a06#D-002.

### F-020 — ADR 003 self-referential engine workspace
- **Confidence**: high
- **Source**: a06 D-003 (auto-included từ G-016 cross-ref decision; not directly answered but implied by q-016 acceptance "treat engine như project")
- **Affects**: `{ws}/decisions/003-self-referential-engine-workspace.md` (create)
- **Statement**: Workspace `wiki` is first-class self-referential workspace (engine documents itself). Boundary rule: engine spec docs (`agents/pipeline/*`) describe HOW engine works internally; platform patterns (`{ws}/platform/patterns/*`) describe WHAT to apply. Different audiences.
- **Apply**: Use a06#D-003.

### F-021 — ADR 004 pattern-contract pairing convention
- **Confidence**: high
- **Source**: q-005, q-006 acceptance pattern (PAIR convention applied)
- **Affects**: `{ws}/decisions/004-pattern-contract-pairing-convention.md` (create)
- **Statement**: Convention — concept có cả implementation skeleton VÀ invariant rule → tạo PAIR (pattern + contract với cross-reference 2 chiều). Concept pure rule → contract only. Concept pure pattern → pattern only.
- **Apply**: Use a06#D-004.

---

## Block: Patterns Index update

### F-022 — patterns-index.md populate
- **Confidence**: high
- **Source**: derived from F-001..F-008 (all patterns)
- **Affects**: `{ws}/patterns-index.md` (edit)
- **Statement**: Replace empty placeholder rows với 8 patterns + 8 contracts. Order: alphabetical theo name. **DO NOT** flagship F-007 to top (per user override q-007). Add Domain Workflows row leave empty (no domain workflows yet for workspace `wiki`).
- **Apply**: Edit existing file at `{ws}/patterns-index.md`.

---

## Block: Action items (post-apply)

### F-023 — `/wiki-viz` README orphan fix (separate session)
- **Confidence**: high
- **Source**: q-019 (self) — answered 2026-05-08
- **Affects**: `.claude/commands/README.md` (edit, ENGINE-LEVEL — không phải workspace path)
- **Statement**: TÁCH PHIÊN. Sau evidence-apply done, run `/update-wiki --scope .claude/commands/README.md` để add row cho `/wiki-viz` Section "Pipeline observability". KHÔNG tạo ADR (bug fix only). KHÔNG include trong evidence-apply manifest này.

---

## Open / deferred

| q-id | Priority | Status | Reason | Resolution path |
|------|----------|--------|--------|-----------------|
| q-020 | P2 | deferred | Pipeline support docs README table outdated (G-007 nice) | Defer phiên riêng, run `/update-wiki` extend table |
| q-021 | P2 | deferred | Tools allowlist principle C-008a sample size concern (G-009) | Defer until sample ≥ 8 sub-agents |
| q-022 | P2 | deferred | Configs/hooks unanalyzed (G-008 nice) | Future rerun `/code-analyze --allow-configs` → new evid-id `refresh-wiki-template-{date}` |
| q-023 | P3 | deferred | Counter-arg: pattern overlap với spec docs | Stop check user choice. ADR D-003 already covers boundary rule |
| q-024 | P3 | deferred | Counter-arg: source_type=engine alternative | Stop check. ADR D-001 alternatives section addresses this |

---

## Apply order (for `/evidence-apply`)

Per a06 notes + cross-references:

1. **Contracts** (F-009..F-016) — 8 files
2. **Patterns** (F-001..F-008) — 8 files
3. **Service docs** (F-017) — 7 files (a05 drafts)
4. **patterns-index.md** (F-022) — 1 file (edit existing)
5. **ADRs** (F-018..F-021) — 4 files
6. **Action item** (F-023) — separate session, NOT in this apply manifest

**Total in apply manifest**: 27 files (8 + 8 + 7 + 1 edit + 4) + 1 deferred.

---

## Stats

| Category | Count |
|----------|-------|
| P0 answered (accept gợi ý) | 13 |
| P0 answered (user override) | 1 (q-007) |
| P1 answered (accept gợi ý) | 5 |
| P2 deferred | 3 |
| P3 deferred (stop check) | 2 |
| **Total resolved** | **24** |
| Awaiting external | 0 |
| Skipped | 0 |

| Block | Files to create | Files to edit |
|-------|-----------------|---------------|
| Platform Patterns | 8 | 0 |
| Platform Contracts | 8 | 0 |
| Service docs (projects/engine/) | 7 | 0 |
| Decisions (ADRs) | 4 | 0 |
| Patterns Index | 0 | 1 |
| **Total** | **27** | **1** |
