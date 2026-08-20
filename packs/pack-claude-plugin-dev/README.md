# pack-claude-plugin-dev

Build Claude Code plugins theo chuẩn Anthropic. Bao gồm: plugin manifest, slash commands, subagents, skills, hooks, MCP servers.

## Khi nào bật

- Repo có `.claude-plugin/plugin.json` (plugin marketplace entry)
- Repo build slash commands trong plugin-root `commands/*.md`
- Repo build subagents trong plugin-root `agents/*.md`
- Repo build skills trong plugin-root `skills/*/SKILL.md`
- Repo configure MCP server trong `.mcp.json`
- Repo configure hooks trong plugin-root `hooks/hooks.json`

## Components

- `plugin`: `.claude-plugin/plugin.json`, marketplace metadata
- `command`: slash command files với frontmatter
- `subagent`: agent definition files với role/tools
- `skill`: skill files với SKILL.md
- `hook`: `hooks/hooks.json` + bundled hook scripts
- `plugin-mcp`: MCP server entries trong `.mcp.json`

> Khác với `pack-agentic` (build agent loop bằng code): pack này tập trung vào **plugin packaging** theo schema Anthropic.

## Constraints highlights

- Plugin manifest có `name`, `version`, `description` đầy đủ
- Slash command có `description:` frontmatter rõ ràng (single sentence, action-oriented)
- Subagent khai báo `tools:` explicit (KHÔNG để rỗng = inherit tất cả)
- Skill có `description` nêu rõ capability + when-to-use/skip
- Hook script idempotent, có timeout, không block user
- MCP server config có error handling khi không reachable
- Không hardcode API key / secret trong plugin files
- Plugin tên kebab-case, version semver

## Validator rules

| Rule | Severity |
|------|----------|
| `pack-claude-plugin-dev-missing-plugin-manifest` | error |
| `pack-claude-plugin-dev-command-missing-description` | error |
| `pack-claude-plugin-dev-agent-missing-tools` | warn |
| `pack-claude-plugin-dev-skill-description-too-vague` | warn |
| `pack-claude-plugin-dev-secret-literal` | error |
| `pack-claude-plugin-dev-hook-no-error-handling` | warn |

## Bật pack

```md
## Packs

- pack-claude-plugin-dev
```

## When not to enable

- Chỉ cấu hình `.claude/` cho một repository, không đóng gói plugin để phân phối.
- Xây MCP server độc lập hoặc agent runtime không gắn với Claude Code plugin; dùng `pack-agentic`.

## Retrieval behavior

Routing phân biệt manifest, command, agent, skill, hook và plugin MCP. Layout plugin canonical đặt component directories (`commands/`, `agents/`, `skills/`, `hooks/`) ở plugin root; `.claude/` là project-local configuration và không phải package layout.

## Verification

```bash
contextd pack-validate --pack pack-claude-plugin-dev --format text
contextd context "Review Claude Code plugin hook packaging" --preview --format json
python scripts/validate.py --file <plugin-fixture> --workspace <workspace-with-pack>
```

Standards baseline được review ngày `2026-08-20`: [Anthropic plugin structure](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/plugin-structure/SKILL.md) và [manifest reference](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/plugin-structure/references/manifest-reference.md). Pin minimum Claude Code version và revalidate khi host schema thay đổi.

Thường kết hợp với `pack-agentic` (nếu plugin có MCP server với tool implementations).
