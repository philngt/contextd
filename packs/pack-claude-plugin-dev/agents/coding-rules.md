# pack-claude-plugin-dev — Coding Rules

## Plugin Project Layout

```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json           # manifest
│   └── marketplace.json      # optional: marketplace listing
├── commands/                 # slash commands
├── agents/                   # subagents
├── skills/                   # skills (each in own dir)
├── hooks/
│   ├── hooks.json            # plugin hook configuration
│   └── scripts/              # optional hook scripts
├── .mcp.json                 # MCP servers (optional)
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Frontmatter Convention

### Slash command

```md
---
description: Concise sentence describing behavior and usage
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
model: inherit
---

# Agent system prompt

(Detailed role + behavior + output format)
```

### Skill

```md
---
name: my-skill
description: |
  What this skill does. Use when <specific condition>.
  Do not use for <neighboring concern>.
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

- Configure events in `hooks/hooks.json`; resolve bundled scripts/assets with `${CLAUDE_PLUGIN_ROOT}` so installed paths remain portable.
- Read the documented event payload from stdin and emit only the response shape allowed by that event.
- Treat exit codes/JSON control fields as an event-specific protocol contract; test allow, block, timeout, malformed input, and non-critical failure paths.
- Log diagnostics to stderr when stdout is reserved for protocol output; keep work within the configured hook timeout.

## MCP Server Coding

- stdio MCP server: read JSON-RPC từ stdin, write to stdout. Stderr cho logs.
- Tool schema explicit (name, description, inputSchema) — không generate runtime.
- Capability declaration đầy đủ ở `initialize` response.
- Graceful shutdown on `SIGTERM`/stdin close.

## Testing Plugin

- Test through the supported Claude Code plugin install/dev workflow; do not rely on copying files into an undocumented cache path.
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

## Domain Decision Lens

Use within this pack's scope; existing constraints remain authoritative.

- **Observe:** Inspect the pinned host version, plugin root, discovery metadata, invocation path, permissions, and event/transport contract. Distinguish packaging, discovery, invocation, and execution failures.
- **Mechanism:** A valid manifest does not ensure discovery or correct invocation. A discovered instruction does not grant tool authority; event handlers additionally depend on their input/output protocol.
- **Choose:** Use a skill/command for reusable guidance, a tool for an external capability, and a hook only for a documented lifecycle event. Select the smallest surface that owns the requirement.
- **Exception:** Do not add MCP or a hook just to ship prose. Host-specific paths and control fields are not portable assumptions for other agents; keep domain guidance separate from its adapter.
- **Verify:** Exercise supported installation on the pinned host, then valid/invalid arguments, relocated plugin paths, denied capabilities, malformed event input, and timeouts. Record actual host output.
- **Stop:** Pause publication when protocol compatibility or requested permissions cannot be verified. Treat install success as packaging evidence, not proof of correct or safe runtime behavior.
