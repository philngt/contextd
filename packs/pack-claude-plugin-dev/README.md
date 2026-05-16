# pack-claude-plugin-dev

Build Claude Code plugins theo chuẩn Anthropic. Bao gồm: plugin manifest, slash commands, subagents, skills, hooks, MCP servers.

## Khi nào bật

- Repo có `.claude-plugin/plugin.json` (plugin marketplace entry)
- Repo build slash commands trong `.claude/commands/*.md`
- Repo build subagents trong `.claude/agents/*.md`
- Repo build skills trong `.claude/skills/*/SKILL.md`
- Repo configure MCP server trong `.mcp.json`
- Repo configure hooks trong `settings.json#hooks`

## Components

- `plugin`: `.claude-plugin/plugin.json`, marketplace metadata
- `command`: slash command files với frontmatter
- `subagent`: agent definition files với role/tools
- `skill`: skill files với SKILL.md
- `hook`: hook scripts + settings.json hooks block
- `plugin-mcp`: MCP server entries trong `.mcp.json`

> Khác với `pack-agentic` (build agent loop bằng code): pack này tập trung vào **plugin packaging** theo schema Anthropic.

## Constraints highlights

- Plugin manifest có `name`, `version`, `description` đầy đủ
- Slash command có `description:` frontmatter rõ ràng (single sentence, action-oriented)
- Subagent khai báo `tools:` explicit (KHÔNG để rỗng = inherit tất cả)
- Skill có `description` đủ context để auto-invoke; tag `TRIGGER when:` rõ
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

Thường kết hợp với `pack-agentic` (nếu plugin có MCP server với tool implementations).
