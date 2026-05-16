# ADR-003: Self-Referential Engine Workspace

## Scope

Workspace-wide (`{ws}/decisions/`) — defines workspace `wiki` boundary + role.

## Status

ACCEPTED — implemented session 2026-05-08 via evidence `2026-05-08-engine-bootstrap-wiki-template`.

## Context

`wiki-template` repo (the engine itself) đang dùng workspace `wiki` để document chính nó (engine documenting engine). Đây là pattern bất thường vì:

- Mọi workspace khác là **application workspace** (vd `example-surgery`) — chứa knowledge về business domain, services, contracts cho 1 app.
- Workspace `wiki` chứa knowledge về **engine internals** — patterns, contracts, decisions của engine code.

Câu hỏi: Đây có phải special case (gây confusion) hay first-class workspace category?

## Decision

Workspace `wiki` là **first-class self-referential workspace**, KHÔNG phải special case. Hợp lệ vì:

- Engine maintainers cần knowledge sandbox riêng để document patterns engine.
- Workspace structure (`platform/`, `projects/`, `decisions/`, ...) áp dụng đầy đủ — engine commands/agents treat như "services" trong project `engine`.
- Không cross-pollution với application workspaces (mỗi workspace là sandbox độc lập theo CLAUDE.md hard constraint).

### Boundary rule (key clarification)

| Layer | Định nghĩa | Audience | File location |
|-------|-----------|----------|---------------|
| **Engine spec docs** | Describe HOW engine works internally | Engine maintainer | `agents/pipeline/*.md`, `agents/coding-rules.md`, etc. (in engine repo, NOT in `{ws}/`) |
| **Platform patterns (workspace `wiki`)** | Describe WHAT to apply (action-oriented) | Engine USER (developer building on engine) | `{ws}/platform/patterns/*.md` |

Khi engine spec change → engine spec doc updated. Khi user-facing pattern reusable → platform pattern doc updated. Drift between 2 layers OK trong short term, but `/wiki-eval` should detect mismatches.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Don't document engine at all (just spec docs) | Engine users cần actionable patterns, không chỉ architecture spec. |
| Special namespace `engine/` outside workspaces | Breaks workspace model invariant. Special case proliferation. |
| Document engine trong template workspace (`templates/workspace.md`) | Templates là skeletons, không phải knowledge store. |
| Separate "meta" workspace category | Adds complexity; uniform workspace model preferable. |

## Trade-offs

**Benefits:**

- Workspace model uniform — user mental model simple ("there are workspaces, one of them happens to be about the engine").
- Engine evolution traceable via workspace ADRs (`{ws}/decisions/`).
- Engine onboarding consistent với application onboarding (same `/wiki-setup` flow with `--variant agentic-engine`).
- Sandboxed from application workspaces (no cross-pollution).

**Costs:**

- Risk of drift between engine spec docs (`agents/pipeline/*`) và workspace platform patterns (`{ws}/platform/patterns/*`). Mitigation: `/wiki-eval` cross-check + boundary rule explicit.
- User onboarding confusion ("which is source of truth?"). Mitigation: rule "spec docs describe HOW; patterns describe WHAT to apply".

## Impact

- Workspace `wiki` populated với 8 patterns + 8 contracts + 7 services + 4 ADRs (this evidence).
- Future engine spec changes phải coordinate update với workspace `wiki` artifacts (manual sync via `/update-wiki` hoặc `/rebase-wiki`).
- Application workspaces (`example-surgery`, etc.) vẫn isolated — KHÔNG copy patterns từ `wiki` workspace sang automatically.

## Why Not Project-Level

Decision affects toàn workspace `wiki` (define purpose of workspace itself), không thuộc 1 project nội bộ. Workspace-level (`{ws}/decisions/`) is correct scope.

## Related

- Pattern: `../platform/patterns/multi-stage-subagent-pipeline.md` (engine flow pattern, audience = user)
- Engine spec: `agents/pipeline/multi-agent-pipeline.md` (engine flow architecture, audience = engine maintainer) — example of HOW vs WHAT divide.
- Workspace doc: `../workspace.md` (workspace `wiki` purpose statement)
- Source: q-016 + raw.md note 5, evidence `2026-05-08-engine-bootstrap-wiki-template`
