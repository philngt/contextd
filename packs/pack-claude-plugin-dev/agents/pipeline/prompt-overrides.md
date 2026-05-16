# pack-claude-plugin-dev — Prompt Overrides

## Self-Check append

```
### Claude Code Plugin (pack-claude-plugin-dev)
- Plugin manifest exists with name (kebab-case), version (semver), description (>=20 chars), author
- Every slash command has description: frontmatter (single action-verb sentence)
- argument-hint set when command takes args; allowed-tools restricts to minimum
- Every subagent has explicit tools: list (no wildcard / no missing field)
- Subagent model: chosen per task complexity (haiku/sonnet/opus)
- Every skill description >= 50 chars with TRIGGER when: phrase for auto-invoke
- No hardcoded API key / token anywhere (sk-, ghp_, AKIA, AIzaSy, xoxb-)
- Hook script idempotent, <2s, errors to stderr, exit 0 on non-critical fail
- MCP server config uses env vars for credentials
- README install instructions + min Claude Code version
- CHANGELOG entry for each version with breaking changes flagged
```
