# Automation Skeletons

Templates for `/suggest-automation` Bước 4. Loaded **only** when the user picks the matching artifact kind — keeps the slash command body small.

## A. Slash command

```markdown
# {Title}

{One-paragraph mô tả ý đồ, suy ra từ cluster theme + prompt_preview}.

## Argument syntax

```
/{name} [...]
```

## Bước 1 — ...

## Bước 2 — ...

## Self-check

- [ ] ...
```

## B. Subagent

```markdown
---
name: {name}
description: {1-liner — ai cũng tự biết khi nào nên gọi}
tools: Read, Glob, Grep   # whitelist tối thiểu, mở rộng khi rõ nhu cầu
model: sonnet
---

# Role

{Mô tả vai}.

# Process

1. ...
```

## C. Skill

User-global: `~/.claude/skills/<name>/SKILL.md`.
Pack-scoped: `packs/<pack>/skills/<name>/SKILL.md`.

Format theo [Claude Code skills](https://docs.anthropic.com/claude/docs/skills):

```markdown
---
name: {name}
description: {when Claude should auto-invoke this skill}
---

# {Title}

{Body — instructions Claude executes when skill is triggered}.
```

## D. Pack

Don't hand-roll. Run:

```
python scripts/scaffold-pack.py --name <pack-name>
```

Then fill:
- `pack.yaml#keywords` — components detector dùng để map task → pack.
- `agents/constraints.md` — hard rules of the stack.
- `agents/coding-rules.md` — style conventions.
- `agents/pipeline/validator-rules.md` — self-check items (prefix `pack-<name>-`).

## E. Refine existing

Đọc artifact đang cover (`covered_by` từ detector log, hoặc tự `Grep` cluster tokens trong `.claude/commands/` + `.claude/agents/`). Đề xuất:
- Mở rộng `description` để keyword match tốt hơn.
- Bổ sung trigger phrase trong body.
- Tách thành 2 artifact nếu artifact đang cover quá nhiều intent.

## Lifecycle front-matter (Phase B — placeholder)

```yaml
---
name: {name}
description: {one-line}
created_from_cluster: {cluster_id}
created_at: {YYYY-MM-DD}
status: active                              # active | deprecated | retired
review_after: {YYYY-MM-DD + 6 months}
related_patterns: []
related_contracts: []
---
```
