# pack-claude-plugin-dev — Coding Rules

## Plugin Project Layout

```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json           # manifest
│   └── marketplace.json      # optional: marketplace listing
├── .claude/
│   ├── commands/             # slash commands
│   ├── agents/               # subagents
│   ├── skills/               # skills (each in own dir)
│   ├── settings.json         # plugin-specific settings
│   └── hooks/                # hook scripts (optional)
├── .mcp.json                 # MCP servers (optional)
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Frontmatter Convention

### Slash command

```md
---
description: One sentence, action verb first, < 100 chars
argument-hint: <required-arg> [optional-arg]
allowed-tools: Read, Grep, Bash(git status:*)
---

# Command title

(Natural language prompt to Claude — what to do with the user's input.)
```

### Subagent

```md
---
name: my-agent
description: Specialized agent for X. Use when Y. Don't use for Z.
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Agent system prompt

(Detailed role + behavior + output format)
```

### Skill

```md
---
name: my-skill
description: |
  Multi-line description with TRIGGER when:, examples, and SKIP conditions.
  TRIGGER when: user mentions <pattern> OR file matches <glob>.
  SKIP: tests, examples.
---

# Skill body

(Detailed instructions when skill is invoked)
```

## Tool Allowlist Best Practices

- **Default deny** — chỉ allow tool subagent thật sự cần.
- **Restrict Bash** với glob: `Bash(npm:*)`, `Bash(git status:*, git log:*)`.
- **No `*` for subagent tools** — explicit list.
- **MCP tools** include theo prefix: `mcp__<server>__*` (cẩn thận với wildcard).

## Hook Design

- Read input từ stdin (Claude Code pipe JSON to hook stdin).
- Write structured response to stdout (JSON nếu cần block/allow).
- Exit code `0` = pass through; non-zero = block (chỉ dùng khi thật sự cần).
- Log errors to stderr, không stdout (stdout reserved cho protocol response).
- Timeout 2s default — long-running hooks degrade UX.

## MCP Server Coding

- stdio MCP server: read JSON-RPC từ stdin, write to stdout. Stderr cho logs.
- Tool schema explicit (name, description, inputSchema) — không generate runtime.
- Capability declaration đầy đủ ở `initialize` response.
- Graceful shutdown on `SIGTERM`/stdin close.

## Testing Plugin

- Manual test: install vào local Claude Code (`~/.claude/plugins/{name}`) hoặc dev mode.
- Validate plugin.json schema trước khi publish.
- Test mỗi slash command với edge cases (no args, invalid args).
- Test subagent với multiple delegation paths.
- Test hooks với mock JSON input.

## Versioning

- Semver: breaking change → MAJOR; new feature → MINOR; bug fix → PATCH.
- Document breaking changes in CHANGELOG.md.
- Tag releases trong git: `v1.0.0`.

## Publishing

- Marketplace: ship marketplace.json với plugin metadata + screenshot.
- Self-host: README có install command (vd `claude plugin install <repo-url>`).
- README có "Compatibility" section (min Claude Code version, OS support).
