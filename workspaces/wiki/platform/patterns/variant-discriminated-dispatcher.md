# Pattern: variant-discriminated-dispatcher

> **Version: v1 — single instance pattern.** Pattern shape may evolve khi variant thứ 3 được introduce.
> Sample size hiện tại: 1 instance (variant=agentic-engine introduced 2026-05-08). Pattern documented sớm để variant tương lai (vd `infra`, `data-pipeline`) follow consistent skeleton.

## Context

Khi 1 command/pipeline phục vụ nhiều "variants" của input (vd codebase Java/Spring vs markdown engine; service vs infra repo), KHÔNG fork command thành 2 commands riêng — discriminate qua field `variant` và dispatch internally.

Lợi ích: shared infrastructure (state machine, file layout, validation), variant-specific schemas chỉ ở Section 4–8 của output.

Hiện tại: chỉ áp dụng cho `/code-analyze` + `/evidence-analyze` với `code_variant ∈ {code, agentic-engine}`.

## Flow

```
Input arrives
  ↓
Step 1: Detect variant (from explicit flag OR auto-detect markers)
  ↓
Step 2: Validate gate per variant
  ↓ pass
Step 3: Resolve scope default per variant
  ↓
Step 4: Build output theo template per variant
  ↓
Step 5: Write source.yaml#code_variant field
  ↓
Step 6: Downstream commands dispatch on source.yaml#code_variant
  ↓
Variant-specific CORE prompts run
```

1. **Detect variant**:
   - Explicit flag (`--variant {value}`) → use as-is.
   - Else: count markers per-variant in repo. Highest wins. Tied → AskUserQuestion.
2. **Validate gate per variant**:
   - `variant=code`: require `.git/` OR build file (pom/package/gradle/cargo/go.mod).
   - `variant=agentic-engine`: require ≥ 1 agentic marker (agents/, .claude/commands/, etc.).
3. **Default scope per variant**: heuristic globs khác nhau (vd code: `src/**`; agentic-engine: `agents/**/*.md`).
4. **Output template per variant**: `templates/{variant}-snapshot.md`.
5. **Source.yaml**: write `code_variant: {value}` field. Default omitted = `code` (backward-compat).
6. **Downstream dispatch**: `/evidence-analyze` reads `source.yaml#code_variant` → routes tới CORE-CODE (cXX) hoặc CORE-AGENTIC (aXX). Cross-variant prompts rejected.

On failure: variant detection ambiguous → AskUserQuestion. Validation gate fail → STOP với hint specific.

## Default Config

```yaml
# Variant registry
variants:
  code:
    is_default: true
    validation_gate:
      required_any: [".git/", "pom.xml", "package.json", "build.gradle", "Cargo.toml", "go.mod"]
    scope_default:
      - "src/**"
      - "pom.xml"
      - "package.json"
      - "build.gradle"
      - "Cargo.toml"
      - "go.mod"
      - "application.*"
      - "Dockerfile"
      - "*.yaml"
    snapshot_template: "templates/code-snapshot.md"
    evid_id_prefix: "code"
    origin_format: "code:{slug}@{sha7}"
    core_prompts: ["c01", "c02", "c03", "c04", "04", "08"]
    on_demand_prompts: ["c05", "c06", "c07"]

  agentic-engine:
    is_default: false
    validation_gate:
      required_any_count: 2
      markers:
        - "agents/**/*.md"
        - ".claude/commands/**/*.md"
        - ".claude/agents/**/*.md"
        - "templates/"
        - "mcp.json"
        - ".mcp.json"
    scope_default:
      - "agents/**/*.md"
      - ".claude/commands/**/*.md"
      - ".claude/agents/**/*.md"
      - "templates/**"
      - "mcp.json"
      - ".mcp.json"
      - "README.md"
      - "CLAUDE.md"
    snapshot_template: "templates/agentic-engine-snapshot.md"
    evid_id_prefix: "engine"
    origin_format: "engine:{slug}@{sha7}"
    core_prompts: ["a01", "a02", "a03", "a04", "04", "08"]
    on_demand_prompts: ["a05", "a06", "a07"]

# Tie-break
ambiguous_when_both_markers: ask_user_question

# Cross-variant prompts
reject_cross_variant_prompts: true       # vd --prompt c05 với agentic-engine evidence → reject
```

## Failure Strategy

| Scenario | Action |
|----------|--------|
| `--variant {invalid}` | STOP, list valid variants |
| Auto-detect ambiguous (both code + agentic markers ≥ threshold) | AskUserQuestion choose |
| `variant=code` + neither `.git/` nor build file | STOP, hint `--variant agentic-engine` hoặc add markers |
| `variant=agentic-engine` + zero agentic markers | STOP với reason |
| Cross-variant prompt (vd `c05` cho agentic-engine) | Reject in `/evidence-analyze` Bước 2 validation |
| Source.yaml missing `code_variant` field for non-default variant | V-02 reject downstream |

## Implementation Rules

- `code_variant` default omitted → treat as `code` (backward-compat — old evidence không có field).
- variant=agentic-engine softens validation gate (no `.git/`/build-file required).
- evid-id prefix differs per variant (`code` vs `engine` vs `platform` for bundle).
- Origin format differs (`code:{slug}@{sha}` vs `engine:{slug}@{sha}`).
- CORE prompt sets disjoint per variant (C-prefix vs A-prefix). Shared: CORE 4 (questions), CORE 8 (gaps).

## Override Points

- Workspace có thể add variant entries qua workspace-level config (future capability — chưa implement).
- Workspace có thể extend scope defaults per variant (vd add `*.go` cho Go subset).
- KHÔNG override: variant registry semantics, dispatch logic.

## Anti-patterns

- ❌ Fork command thành `/code-analyze` + `/engine-analyze` — defeat shared infrastructure.
- ❌ Use `source_type=engine` (parallel với code/paste/api/mcp) — explode source_type space khi thêm variants.
- ❌ Miss `code_variant` field trong source.yaml → downstream dispatch sai (rơi vào CORE-CODE thay vì CORE-AGENTIC).
- ❌ Allow cross-variant prompts (`--prompt c05` cho agentic-engine) — schema mismatch.
- ❌ Auto-detect default to most-common variant when ambiguous — phải AskUserQuestion.

## Used By

- `/code-analyze` Bước 1.4 (`.claude/commands/code-analyze.md:L43-L70`) — variant detection.
- `/code-analyze` Bước 4 (`L194-L297`) — variant-specific build.
- `/code-analyze` Bước 7 (`L412-L420`) — downstream dispatch.
- `/evidence-analyze` Bước 2 — sub-branch theo `code_variant`.
- Engine specs:
  - `agents/pipeline/code-snapshot-conventions.md` Section 12 — agentic-engine variant detection + structure.
  - `agents/pipeline/code-analysis-prompts.md` — variant dispatch table + CORE-CODE/CORE-AGENTIC prompts.

## Related

- Contract: `../contracts/raw-md-section-structure.md` (variant-specific Section 4–8 schemas)
- Contract: `../contracts/source-yaml-schema.md` (`code_variant` field definition)
- ADR: `../../decisions/001-introduce-agentic-engine-variant.md` (introduction reasoning + alternatives)
- Source: q-008, evidence `2026-05-08-engine-bootstrap-wiki-template`

> **Confidence note (re-iterated)**: Pattern shape v1 dựa trên 1 instance. Khi thêm variant thứ 3, pattern có thể cần adjust (vd thêm validation cho variant ID format, registry centralization, etc.). Treat v1 as starting point, not final spec.
