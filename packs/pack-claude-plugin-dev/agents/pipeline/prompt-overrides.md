# pack-claude-plugin-dev — Prompt Overrides

## Self-Check append

```
### Claude Code Plugin (pack-claude-plugin-dev)
- Plugin-root layout uses `.claude-plugin/plugin.json` plus `commands/`, `agents/`, `skills/`, `hooks/`, `.mcp.json` as needed
- Manifest has required name; distribution metadata follows marketplace policy
- Every slash command has concise, specific description frontmatter
- argument-hint set when command takes args; allowed-tools restricts to minimum
- Every subagent has explicit tools: list (no wildcard / no missing field)
- Subagent model override is compatible with pinned host and backed by eval; otherwise inherit/default
- Every skill description states what it does + when to use/skip, without magic length rules
- No hardcoded API key / token anywhere (sk-, ghp_, AKIA, AIzaSy, xoxb-)
- Hook script idempotent, within configured timeout, and follows event-specific exit/JSON semantics
- MCP/hook paths use `${CLAUDE_PLUGIN_ROOT}`; credentials come from environment/secret manager
- README install instructions + min Claude Code version
- CHANGELOG entry for each version with breaking changes flagged
```

## Common Pitfalls (Top 10)

Mỗi task PHẢI rà soát anti-patterns trong [`../common-pitfalls.md`](../common-pitfalls.md):

```md
### Common Pitfalls — check trước khi commit
- Không vi phạm bất kỳ P01..P10 trong common-pitfalls.md (rule/why/detect/severity)
- Pitfall regex-detectable: confirm Layer-1 validator PASS
- Pitfall design-only: tick từng item ở Layer-2 self-check
```
