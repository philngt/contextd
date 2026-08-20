# pack-claude-plugin-dev — Validator Rules

Layer-1 rule. Implement: [`scripts/rules.py`](../../scripts/rules.py). Prefix `pack-claude-plugin-dev-`.

| Rule ID | Severity | Check |
|---------|----------|-------|
| `pack-claude-plugin-dev-missing-plugin-manifest`      | error | Plugin-root `commands/`, `agents/`, `skills/`, or `hooks/` exists but `.claude-plugin/plugin.json` does not. Project-local `.claude/*` is ignored. |
| `pack-claude-plugin-dev-command-missing-description`  | error | `.md` file in plugin-root `commands/` without `description:` field in YAML frontmatter. |
| `pack-claude-plugin-dev-agent-missing-tools`          | warn  | `.md` file in plugin-root `agents/` without explicit `tools:` field — subagent inherits all tools (security/scope risk). |
| `pack-claude-plugin-dev-skill-description-too-vague`  | warn  | Plugin `SKILL.md` missing description or a clear when-to-use condition. |
| `pack-claude-plugin-dev-secret-literal`               | error | Hardcoded secret pattern in any plugin file: `sk-...`, `ghp_...`, `AKIA...`, `xoxb-...`, `AIzaSy...`, OpenAI/Anthropic key prefixes. |
| `pack-claude-plugin-dev-hook-no-error-handling`       | warn  | Shell/Python file under plugin-root `hooks/` without visible error/exit handling. |

## Layer-2 self-check

```md
### Claude Code Plugin (pack-claude-plugin-dev)
- Plugin-root layout is used; project-local `.claude/*` is not packaged as components
- Plugin manifest exists with required name and distribution metadata required by target marketplace
- Plugin name kebab-case; version semver
- Every slash command has description: in frontmatter (single sentence, action verb)
- Every subagent has explicit tools: list (no wildcard, no missing field)
- Every skill description states capability + when to use/skip
- No hardcoded API keys or tokens anywhere in plugin files
- Hook scripts respect configured timeout and event-specific exit/JSON semantics
- MCP server config uses `${CLAUDE_PLUGIN_ROOT}` for bundled paths and env vars for credentials
- README has install instructions + min Claude Code version
- CHANGELOG.md updated for each version
```

## Limitations

- `missing-plugin-manifest`: file-level heuristic infers root from default component directories; custom manifest paths still need schema/host validation.
- `secret-literal`: regex-only — base64-encoded or split-string secrets may bypass.
- `hook-no-error-handling`: only flags `.sh` and `.py` files under `hooks/`; it does not parse `hooks.json` references or opaque binaries.
