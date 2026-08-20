# Contributing

Thanks for your interest in contributing.

## Before You Start

- Read [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md)
- Ensure your local Claude Code setup works

## Development Workflow

1. Create a feature branch from `main`
2. Make focused changes with clear commit messages
3. Install the editable package and test dependencies:
   `python3 -m pip install -e ".[test]"`
4. Run the local release gates:

   ```bash
   python3 -m compileall -q scripts
   python3 scripts/test_lint_wiki.py
   python3 scripts/test_atomic_write.py
   python3 scripts/test_detect_repetition.py
   python3 scripts/test_contextd_runtime.py
   python3 scripts/test_artifact_schemas.py
   python3 scripts/lint-wiki.py --all-workspaces --wiki-root . --strict
   python3 scripts/check-patterns-index.py
   ```

5. Verify any additional commands, docs links, or workflows affected by the
   change.
6. Open a pull request with context and test notes

## Pull Request Guidelines

- Keep PR scope small and focused
- Explain the problem and why the change is needed
- Reference related issues when applicable
- Update docs when behavior or workflow changes

## Wiki-Specific Expectations

- Preserve workspace isolation rules
- Avoid cross-workspace knowledge mixing
- Prefer updating existing docs/patterns over introducing duplicates

## Code of Conduct

Be respectful and constructive in all interactions.
