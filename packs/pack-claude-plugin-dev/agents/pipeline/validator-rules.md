# pack-claude-plugin-dev — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-claude-plugin-dev-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-claude-plugin-dev-missing-plugin-manifest`      | error | Repo has `.claude/commands/` or `.claude/agents/` or `.claude/skills/` but no `.claude-plugin/plugin.json`. (File-level: only fires when scanning project markers.) |
| `pack-claude-plugin-dev-command-missing-description`  | error | `.md` file in `.claude/commands/` without `description:` field in YAML frontmatter. |
| `pack-claude-plugin-dev-agent-missing-tools`          | warn  | `.md` file in `.claude/agents/` without explicit `tools:` field — subagent inherits all tools (security/scope risk). |
| `pack-claude-plugin-dev-skill-description-too-vague`  | warn  | `SKILL.md` with `description` < 50 chars or missing trigger phrase (TRIGGER, "Use when", "use this when"). |
| `pack-claude-plugin-dev-secret-literal`               | error | Hardcoded secret pattern in any plugin file: `sk-...`, `ghp_...`, `AKIA...`, `xoxb-...`, `AIzaSy...`, OpenAI/Anthropic key prefixes. |
| `pack-claude-plugin-dev-hook-no-error-handling`       | warn  | Hook script (shell/python referenced from `settings.json#hooks`) without `set -e` / try-except / exit-code handling. |

## Layer-2 self-check

```md
### Claude Code Plugin (pack-claude-plugin-dev)
- Plugin manifest (.claude-plugin/plugin.json) exists with name/version/description/author
- Plugin name kebab-case; version semver
- Every slash command has description: in frontmatter (single sentence, action verb)
- Every subagent has explicit tools: list (no wildcard, no missing field)
- Every skill has description >= 50 chars with TRIGGER when: phrase
- No hardcoded API keys or tokens anywhere in plugin files
- Hook scripts: idempotent, fast (<2s), errors logged to stderr, exit 0 on non-critical failure
- MCP server config uses env vars for credentials (no hardcoded)
- README has install instructions + min Claude Code version
- CHANGELOG.md updated for each version
```

## Limitations

- `missing-plugin-manifest`: file-level scan can't see project structure unless run on plugin.json directly or special triggered file. The rule fires when scanning any `.claude/commands/*.md` if sibling `.claude-plugin/plugin.json` is absent.
- `secret-literal`: regex-only — base64-encoded or split-string secrets may bypass.
- `hook-no-error-handling`: only flags `.sh` and `.py` files referenced by hooks block; opaque binaries not checked.
