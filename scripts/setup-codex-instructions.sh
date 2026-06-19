#!/usr/bin/env bash
# DEPRECATED: Use setup-codex-skills.sh instead for full Codex skill installation.
# This script only generates .codex/instructions.md (project-level instructions).
#
# Usage: bash scripts/setup-codex-instructions.sh [TARGET_PROJECT_DIR]
# Copies .codex/instructions.md into a target project for Codex CLI consumption.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="${1:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# Generate instructions
python3 -m scripts.cli export --runtime codex-instructions --workspace default --output "$TARGET_DIR" --include-engine

echo ""
echo "✅ Copied contextd instructions to: $TARGET_DIR/.codex/instructions.md"
echo ""
echo "Next steps to test with Codex:"
echo "  1. Install Codex CLI: npm install -g @openai/codex"
echo "  2. cd $TARGET_DIR"
echo "  3. codex 'What are the workspace isolation rules here?'"
echo ""
echo "Or paste the file content into Codex Chat/Web app."
