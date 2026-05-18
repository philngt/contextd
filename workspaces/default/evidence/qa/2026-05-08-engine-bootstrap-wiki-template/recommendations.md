# QA Recommendations — 2026-05-08-engine-bootstrap-wiki-template

> Auto-generated bởi C8 (QA Recommender) cho `/evidence-qa` với `source_type=code`, `code_variant=agentic-engine`.
> READ-ONLY trong QA session.

**Evidence ID**: `2026-05-08-engine-bootstrap-wiki-template`
**Generated**: 2026-05-08T00:00:00+07:00
**Source snapshot**: raw.md@unmanaged-2064d55
**Scope**: P0 + P1 questions only (19 câu).

> P2/P3 (5 câu — q-020..q-024) không có gợi ý — user trả lời trực tiếp.
> Workspace `wiki` empty baseline → mọi pattern/contract proposals là `[NEW]` (no EXTENDS/CONFLICT comparison).

---

## q-001 — Pattern P-001 workspace-resolve-step0  [P0]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: 15/15 commands ngoại trừ index README đều có Bước 0 với cấu trúc identical. Coverage near-universal → engine-level invariant rõ ràng. Không có existing pattern để extends (workspace empty).

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-001)` — 15 occurrences listed
- `(.claude/commands/code-analyze.md:L26-L36)` — canonical example
- `(agents/system-prompt.md)` — wiki_root resolution rule referenced

**Đề xuất câu trả lời**:
> Có, thêm vào `{ws}/platform/patterns/workspace-resolve-step0.md`. Pattern là engine-level invariant — apply cho mọi command future. Workspace override KHÔNG apply (engine invariant). Use canonical structure trong a03#P-001 (5 steps: find wiki.json → resolve wiki_root → STOP if empty → set {ws} → validate workspace.md).

---

## q-002 — Pattern P-002 askuser-confirm-preview  [P0]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: VỪA ●●○

**Lý do phân tích**: 4 commands explicit follow (code-analyze, evidence-ingest, contextd-setup, new-workspace) — coverage moderate. Có thể nhiều commands khác cũng follow nhưng a03 chỉ enumerate 4. Pattern là UX best practice cho irreversible ops.

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-002)` — 4 occurrences
- `(.claude/commands/code-analyze.md:L106-L182)` — canonical preview block

**Đề xuất câu trả lời**:
> Có, thêm vào `{ws}/platform/patterns/askuser-confirm-preview.md`. Apply: mọi command có **side effects filesystem** (tạo evidence, edit wiki, scaffold workspace). Canonical: preview block + AskUserQuestion 3 options (primary action / edit-detail / cancel). Cancel BẮT BUỘC.

---

## q-003 — Pattern P-003 secrets-blocklist-gate  [P0]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Security-critical pattern. Tuy chỉ 1 explicit implementation hiện tại (code-analyze Bước 4.3) nhưng pattern doc cần để áp dụng future. 5 tầng cấu trúc rõ ràng (hard blocklist + AskUser gate + redaction + guard log + workspace override).

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-003)`
- `(agents/pipeline/code-snapshot-conventions.md:L156-L251)` — full spec
- `(.claude/commands/code-analyze.md:L207-L229)` — Bước 4.3 implementation

**Đề xuất câu trả lời**:
> Có, thêm vào `{ws}/platform/patterns/secrets-blocklist-gate.md`. Security-critical pattern — apply cho mọi command đọc file content nhạy cảm (configs, credentials, ingestion từ external sources có sensitive data). 5 tầng theo a03#P-003.

---

## q-004 — Pattern P-004 redaction-post-pass  [P0]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Companion với P-003. 4 patterns scan rõ (password, token/secret/api-key/jwt-key, email, URL-with-creds) + STOP-on-secret behavior. Universal applicable.

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-004)`
- `(.claude/commands/code-analyze.md:L274-L282)` — Bước 4.10 implementation
- `(agents/pipeline/code-snapshot-conventions.md:L218-L238)` — Section 6.2

**Đề xuất câu trả lời**:
> Có, thêm vào `{ws}/platform/patterns/redaction-post-pass.md`. Companion với P-003 (`secrets-blocklist-gate.md`). Apply cho mọi output có khả năng chứa secrets (snapshots, logs, qa exports, reports). STOP-on-secret = irreversible: KHÔNG ghi file output nếu còn match.

---

## q-005 — P-005/C-005 evidence-state-machine: pattern, contract, hay PAIR?  [P0]

**Kết luận**: NÊN THÊM (PAIR approach)
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Per a06 D-004 (pattern–contract pairing convention), state machine có cả implementation skeleton (pattern) VÀ invariant rule (contract). PAIR matches convention: pattern describes "states + transitions + storage" cho implementer; contract describes "invariants + ownership + transition rules" cho validator/reviewer.

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-005)` — pattern with 8 occurrences
- `(a04-contract-proposals.md#C-005)` — contract with transition ownership table
- `(a06-decision-drafts.md#D-004)` — pairing convention rationale

**Đề xuất câu trả lời**:
> PAIR. Tạo cả 2 docs với cross-reference:
> - `{ws}/platform/patterns/evidence-state-machine.md` — implementation skeleton (states, transitions, storage location).
> - `{ws}/platform/contracts/evidence-state-machine-transitions.md` — invariant rules (transition ownership, no-skip, _index.md as SoT, I-2 lock).
> Pattern doc cite contract; contract doc cite pattern.

---

## q-006 — P-006/C-006 citation-rule + citation-format: PAIR?  [P0]

**Kết luận**: NÊN THÊM (PAIR approach)
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Same logic q-005. Pattern describes implementation skeleton (path format + bundle prefix); contract describes invariant rules (validator rejects). Engine-wide universal rule.

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-006)`
- `(a04-contract-proposals.md#C-006)`
- `(a06-decision-drafts.md#D-004)` — pairing convention

**Đề xuất câu trả lời**:
> PAIR. Tạo:
> - `{ws}/platform/patterns/citation-rule.md` — implementation skeleton (path format, bundle prefix variant).
> - `{ws}/platform/contracts/citation-format.md` — invariant + validator behavior (reject paths absolute / cross-workspace / outside scope).
> Cross-reference 2 chiều.

---

## q-007 — Pattern P-007 multi-stage-subagent-pipeline làm FLAGSHIP top patterns-index?  [P0]

**Kết luận**: NÊN THÊM (top of patterns-index)
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: P-007 là 5-stage `/contextd-use` flow — flagship của engine identity. Coverage: 1 implementation chính + nhiều spec docs reference (multi-agent-pipeline.md, PIPELINE-VISUAL.md). Đặt làm pattern đầu tiên trong patterns-index làm bài giới thiệu engine.

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-007)`
- `(agents/pipeline/README.md:L27-L46)` — 5-stage diagram
- `(.claude/commands/contextd-use.md:L1)` — implementation

**Đề xuất câu trả lời**:
> Có, thêm với vị trí top trong `{ws}/patterns-index.md`. Pattern doc tại `{ws}/platform/patterns/multi-stage-subagent-pipeline.md`. Cross-reference từ `{ws}/workspace.md` (workspace overview). Đây là flagship — mọi command wiki-aware nên follow.

---

## q-008 — Pattern P-008 variant-discriminated-dispatcher: add NOW (sample=1) hay defer?  [P0]

**Kết luận**: NÊN THÊM (with confidence note)
**Độ tin cậy**: VỪA ●●○

**Lý do phân tích**: Sample size = 1 instance hoàn chỉnh (variant=agentic-engine vừa được introduce). Confidence thấp về exact pattern shape. NHƯNG: documenting sớm tốt hơn vì variant tiếp theo (vd `infra`, `data-pipeline`) sẽ follow consistent skeleton thay vì reinvent.

**Trích dẫn chính**:
- `(a03-pattern-proposals.md#P-008)`
- `(.claude/commands/code-analyze.md:L43-L70)` — Bước 1.4 detect implementation
- `(a06-decision-drafts.md#D-001)` — variant introduction context

**Đề xuất câu trả lời**:
> Có, thêm với note "single instance — pattern shape may evolve khi variant thứ 3 được introduce". File: `{ws}/platform/patterns/variant-discriminated-dispatcher.md`. Document 6 bước canonical (detect → validation gate → scope default → output template → source.yaml field → downstream dispatch). Version: v1; revisit khi có variant thứ 3.

---

## q-009 — Contract C-001 evid-id-format: src list đầy đủ?  [P0]

**Kết luận**: NÊN THÊM (current src list)
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: 5/5 ingestion entry-points follow format `{date}-{src}-{slug}`. src list hiện tại {paste, api, mcp, code, engine, platform} cover toàn bộ source_type + variant + bundle mode. Future src additions (vd `ticket` cho Jira) sẽ update contract version.

**Trích dẫn chính**:
- `(a04-contract-proposals.md#C-001)`
- `(agents/pipeline/code-snapshot-conventions.md:L40-L62)` — formal definition
- `(templates/evidence-source.yaml:L5)` — schema

**Đề xuất câu trả lời**:
> Có, thêm vào `{ws}/platform/contracts/evid-id-format.md` với src list hiện tại. Future src additions phải update contract (semantic versioning) và trace lý do trong ADR.

---

## q-010 — Contract C-002 evidence-file-layout: invariant đúng?  [P0]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Universal layout used across all evidence (this evidence + template + spec docs match). Coverage 4/4. Counter-examples không có.

**Trích dẫn chính**:
- `(a04-contract-proposals.md#C-002)`
- `(agents/pipeline/code-snapshot-conventions.md:L25-L34)` — layout spec
- `(workspaces/default/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md:L1)` — this evidence follows

**Đề xuất câu trả lời**:
> Có, thêm vào `{ws}/platform/contracts/evidence-file-layout.md`. Chứa: sources/{id}/{required, conditional} + analysis/ + qa/ + _index.md. Reference từ C-005 (state machine — _index.md as SoT).

---

## q-011 — Contract C-003 raw-md-section-structure: 1 đa-variant hay 3 contracts riêng?  [P0]

**Kết luận**: 1 contract đa-variant (chosen)
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Cùng concept (raw.md có N sections theo schema), variant table dễ extend. Tách 3 contracts → maintenance overhead khi variant thứ 3 thêm vào.

**Trích dẫn chính**:
- `(a04-contract-proposals.md#C-003)`
- `(agents/pipeline/code-snapshot-conventions.md:L67-L133)` — code variant
- `(agents/pipeline/code-snapshot-conventions.md:L385-L402)` — agentic-engine variant

**Đề xuất câu trả lời**:
> 1 contract đa-variant tại `{ws}/platform/contracts/raw-md-section-structure.md`. Variant table inline (code | agentic-engine | bundle). Easy to extend khi thêm variant mới.

---

## q-012 — Contract C-004 source-yaml: tách C-004a (code-specific)?  [P0]

**Kết luận**: KEEP unified
**Độ tin cậy**: VỪA ●●○

**Lý do phân tích**: 11 always-required fields + conditional sections cho code/bundle. Conditional sections rõ ràng trong YAML structure. Tách C-004a → 2 contracts maintain song song với cross-reference complex.

**Trích dẫn chính**:
- `(a04-contract-proposals.md#C-004)`
- `(templates/evidence-source.yaml:L1-L54)` — schema with conditional sections

**Đề xuất câu trả lời**:
> KEEP unified tại `{ws}/platform/contracts/source-yaml-schema.md`. Conditional fields rõ trong YAML structure. Revisit tách nếu conditional grow phức tạp (vd thêm 5+ variant-specific fields).

---

## q-013 — Contract C-007 slash-command-naming: enforce consistency hay accept mix?  [P0]

**Kết luận**: Document BOTH conventions, suggest "subject-verb" cho future
**Độ tin cậy**: VỪA ●●○

**Lý do phân tích**: Hiện tại 19/19 commands follow kebab-case + lowercase. Mix verb-subject vs subject-verb là minor stylistic — cả 2 đều readable. Enforcing breaking change cho 5 existing commands không cần thiết. Suggesting "subject-verb" cho commands mới (vì more searchable theo subject prefix).

**Trích dẫn chính**:
- `(a04-contract-proposals.md#C-007)`
- `(.claude/commands/README.md:L16-L20)` — workspace ops mix
- `(08-knowledge-gaps.md#G-010)` — inconsistency note

**Đề xuất câu trả lời**:
> Document BOTH conventions as valid trong `{ws}/platform/contracts/slash-command-naming.md`. RULE: kebab-case + lowercase + hyphens (universal). RECOMMENDATION (non-binding): "subject-verb" cho commands mới (consistency với evidence-* và wiki-* groups). Không break existing commands.

---

## q-014 — Contract C-008: 'DÙNG KHI/KHÔNG DÙNG' description = required hay convention?  [P0]

**Kết luận**: Convention (recommended), KHÔNG required
**Độ tin cậy**: VỪA ●●○

**Lý do phân tích**: Sample 5/5 sub-agents follow nhưng có thể là coincidence (small sample). Some future agents có thể có scope đơn giản, single sentence description đủ. "DÙNG KHI/KHÔNG DÙNG" pattern là good practice nhưng không phải hard invariant.

**Trích dẫn chính**:
- `(a04-contract-proposals.md#C-008)`
- 5 sub-agent files với "DÙNG KHI/KHÔNG DÙNG" pattern

**Đề xuất câu trả lời**:
> Convention (recommended). Required fields: name, description, tools, model. Convention (non-binding): description chứa "DÙNG KHI" (positive trigger) + "KHÔNG DÙNG" (negative trigger / scope constraint). File: `{ws}/platform/contracts/sub-agent-frontmatter-schema.md`. Defer C-008a (tools allowlist principle) per G-009 (sample size concern).

---

## q-015 — Doc grouping strategy  [P1]

**Kết luận**: Option B (group by category, 6 docs) — match a05 default
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: 24 entries (19 commands + 5 sub-agents) → 1-doc-per-entry tốn quá nhiều file (24+) cho navigation. 1 mega-doc → quá lớn (>2000 lines). Per-category 6 docs (workspace-ops, wiki-usage, codebase-analysis, reporting, observability, evidence-pipeline) + 1 agents doc balance giữa detail và navigation. a05 đã draft theo schema này.

**Trích dẫn chính**:
- `(a05-doc-drafts.md#DRAFT-G1..G6)` — 6 group drafts ready
- `(08-knowledge-gaps.md#G-003)` — context

**Đề xuất câu trả lời**:
> Option B — 6 group docs theo category + 1 agents doc tại `{ws}/projects/engine/services/`. a05 đã draft sẵn 7 files. Apply ngay từ a05.

---

## q-016 — Doc location: projects/engine/ vs engine/?  [P1]

**Kết luận**: `{ws}/projects/engine/`
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: Workspace structure consistent (`projects/{name}/`). Tạo namespace mới `{ws}/engine/` introduce special case → break workspace model invariant. Treat engine như 1 project có ưu điểm uniform UX.

**Trích dẫn chính**:
- `(CLAUDE.md:L77-L80)` — workspace structure invariant
- `(a05-doc-drafts.md)` — proposed paths use `{ws}/projects/engine/services/`
- `(a06-decision-drafts.md#D-003)` — self-referential workspace rationale

**Đề xuất câu trả lời**:
> `{ws}/projects/engine/services/{group-name}.md`. Treat engine như 1 project. Reuse workspace structure (no special namespace). Decision documented trong D-003 ADR.

---

## q-017 — ADR variant=agentic-engine: a06 đã draft (D-001). Confirm apply?  [P1]

**Kết luận**: NÊN THÊM
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: a06 D-001 đã có draft đầy đủ (alternatives, trade-offs, citation 5 surfaces). Apply trực tiếp tạo `{ws}/decisions/001-introduce-agentic-engine-variant.md`.

**Trích dẫn chính**:
- `(a06-decision-drafts.md#D-001)`
- `(08-knowledge-gaps.md#G-004)`

**Đề xuất câu trả lời**:
> Có, apply D-001 thành ADR `{ws}/decisions/001-introduce-agentic-engine-variant.md` từ a06 draft. Use template `templates/adr.md`. Status field = "ACCEPTED" (vì decision đã thực thi trong session 2026-05-08).

---

## q-018 — Split or keep code-analysis-prompts.md? a06 D-002 chose KEEP.  [P1]

**Kết luận**: KEEP (per D-002)
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: a06 D-002 đã reasoning đầy đủ với revisit triggers (>1500 lines / variant #3 / user feedback). 920 lines hiện tại manageable. Apply ADR trực tiếp.

**Trích dẫn chính**:
- `(a06-decision-drafts.md#D-002)`

**Đề xuất câu trả lời**:
> KEEP per D-002. Apply ADR `{ws}/decisions/002-keep-code-analysis-prompts-monolithic.md`. Revisit triggers documented inline.

---

## q-019 — /contextd-viz orphan README fix: cùng phiên hay tách?  [P1]

**Kết luận**: Tách phiên
**Độ tin cậy**: CAO ●●●

**Lý do phân tích**: G-006 không block evidence-apply (file path khác workspace). Trộn doc fix với evidence-apply tăng complexity. Tách: chạy `/contextd-update` riêng sau khi evidence-apply done.

**Trích dẫn chính**:
- `(a06-decision-drafts.md#D-005)`
- `(08-knowledge-gaps.md#G-006)`

**Đề xuất câu trả lời**:
> Tách phiên. Apply evidence này trước. Sau đó chạy `/contextd-update --scope .claude/commands/README.md` để add row cho `/contextd-viz` Section "Pipeline observability". KHÔNG tạo ADR (bug fix only).

---

## Summary

| Question | Confidence | Default | Notes |
|----------|------------|---------|-------|
| q-001..q-004 | ●●● / ●●○ / ●●● / ●●● | All NÊN THÊM | Patterns P-001..P-004 |
| q-005, q-006 | ●●● / ●●● | PAIR | State machine + citation pairs |
| q-007 | ●●● | NÊN THÊM (FLAGSHIP top) | P-007 |
| q-008 | ●●○ | NÊN THÊM (with note) | P-008 sample=1 |
| q-009..q-014 | ●●● x4 + ●●○ x2 | All NÊN THÊM | Contracts C-001..C-004, C-007, C-008 |
| q-015..q-018 | ●●● x4 | Per a05/a06 defaults | Strategy + 2 ADRs |
| q-019 | ●●● | Tách phiên | Bug fix only |

**Total recommendations**: 19 (P0=14 + P1=5).
**Distribution**: CAO ●●● = 14 câu, VỪA ●●○ = 5 câu, THẤP ●○○ = 0 câu.

> ⚠ THẤP confidence = 0 — bootstrap workflow với workspace empty cho phép confident defaults. Không cần warning per-question.
