## Summary / Context

<!-- What changed? Keep scope focused. -->

## Problem & Why

<!-- What problem does this solve, and why is this change needed? -->

## Test Notes

- [ ] `python scripts/test_lint_wiki.py`
- [ ] `python scripts/test_atomic_write.py`
- [ ] `python scripts/test_detect_repetition.py`
- [ ] `python scripts/test_contextd_runtime.py`
- [ ] `python scripts/test_context_security.py`
- [ ] `python -m json.tool templates/contextd-config.schema.json` and `python -m json.tool templates/task-context.schema.json`
- [ ] `python scripts/lint-wiki.py --all-workspaces --wiki-root .`
- [ ] N/A (reason):

## Related Issues

<!-- Closes #... / Relates to #... -->

## Docs / Workflow Impact

- [ ] Updated docs because behavior/workflow changed
- [ ] No docs update needed (reason):

## Wiki-specific checks

- [ ] Preserved workspace isolation
- [ ] No cross-workspace knowledge mixing
- [ ] Avoided duplicate docs/patterns

## Path safety / adapter parity (when applicable)

- [ ] Workspace and pack identifiers fail closed before path construction
- [ ] Named workspace/pack roots are non-aliased; descendant symlinks stay within their named root
- [ ] Artifact provenance paths remain normalized and relative; explicitly absolute diagnostics remain absolute
- [ ] CLI and MCP produce the same scope/security decision
- [ ] Ubuntu, macOS, and Windows path/runtime CI passed
- [ ] N/A (reason):

## Project Spirit Check

- [ ] Change reinforces knowledge-first workflow (contracts/patterns before invention)
- [ ] Contributor experience stays simple and practical (no unnecessary complexity)
- [ ] Project voice and intent remain consistent across docs/workflows
- [ ] If trade-offs were made, rationale is stated clearly in this PR
