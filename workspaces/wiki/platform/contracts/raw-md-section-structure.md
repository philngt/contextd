# Contract: raw-md-section-structure

## Rule

`raw.md` PHẢI có 10 sections theo thứ tự, mỗi section có anchor `#section-N`. Skip section trống bằng `_(none detected)_` — KHÔNG xóa heading. Section structure khác theo variant.

### Variant: `code` (classic runtime codebase)

| # | Heading | Content |
|---|---------|---------|
| 1 | Project metadata | name, version, build tool, language, top dirs, README excerpt |
| 2 | Dependencies | parsed table từ pom.xml / package.json / build.gradle / Cargo.toml / go.mod |
| 3 | Configs | gated by `--allow-configs` (xem pattern secrets-blocklist-gate) |
| 4 | REST endpoints | `@RestController` / `@*Mapping` / `app.get(` / route DSL |
| 5 | Message consumers | `@KafkaListener`, MQTT subscribers, RabbitMQ, SQS handlers |
| 6 | Services & components | `@Service` / `@Component` / `@Repository` |
| 7 | DB schema | entities, repositories, migrations |
| 8 | Public APIs | class signatures cho package-public API |
| 9 | Git summary | last 50 commits, top contributors, notable commits |
| 10 | Notes | observations surprising kèm citation |

### Variant: `agentic-engine` (markdown-heavy: slash commands, sub-agents, prompt templates)

| # | Heading | Content |
|---|---------|---------|
| 1 | Engine metadata | engine name, purpose excerpt, top dirs, Claude Code version target |
| 2 | Dependencies | MCP servers, runtime/script-tool deps, external integrations |
| 3 | Configs | gated by `--allow-configs` (settings.json, wiki.json) |
| 4 | Slash commands | table của `.claude/commands/*.md` |
| 5 | Sub-agents & system prompts | `.claude/agents/*.md` + `agents/**/*.md` |
| 6 | Pipeline stages / Modules | `agents/pipeline/*` hoặc functional modules |
| 7 | Templates | `templates/*` skeletons |
| 8 | Hooks & settings | từ `settings.json` (gated) |
| 9 | Git summary | same as code variant — fallback `unmanaged` nếu no git |
| 10 | Notes | observations |

### Variant: `bundle` (multi-repo)

```
Section 0: Bundle Overview                ← REQUIRED dù chỉ 1 repo
Repo: {name-1} [{role}]
  Section 1..9 với heading suffix [{repo-name-1}]
Repo: {name-2}
  Section 1..9 với heading suffix [{repo-name-2}]
Docs (optional)                            ← key excerpts từ tài liệu đi kèm
Section 10: Notes                          ← tổng hợp cuối file
```

## Invariants

- 10 sections (code/agentic-engine) hoặc Section 0 + N×Sections (bundle) — KHÔNG được skip heading.
- Section number stable across variants (Section 9 luôn là Git summary, Section 10 luôn là Notes).
- Heading anchor `#section-N` reliable cho citations.
- Variant table EXTENSIBLE — thêm variant mới (vd `infra`) update contract version, NOT break existing.

## Observed evidence

- ✅ Code variant: `(agents/pipeline/code-snapshot-conventions.md:L67-L86)` + template `(templates/code-snapshot.md:L1)`
- ✅ Agentic-engine: `(agents/pipeline/code-snapshot-conventions.md:L385-L402)` + template `(templates/agentic-engine-snapshot.md:L1)`
- ✅ Bundle: `(agents/pipeline/code-snapshot-conventions.md:L88-L133)`
- ✅ This evidence raw.md follows agentic-engine schema: `(workspaces/wiki/evidence/sources/2026-05-08-engine-bootstrap-wiki-template/raw.md:L1)` 10 sections present

## Counter-examples

_(none detected — both templates strictly follow the schema)_

## Validator behavior

- Missing required section heading → analyzer reject + re-prompt.
- Section out of order → reject (heading anchor stable invariant).

## Related

- Contract: `evidence-file-layout.md` (raw.md location)
- Pattern: `../patterns/variant-discriminated-dispatcher.md` (variant detection logic)
- Templates: `templates/code-snapshot.md`, `templates/agentic-engine-snapshot.md`
- Source: q-011, evidence `2026-05-08-engine-bootstrap-wiki-template`
