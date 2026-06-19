#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET_DIR="${HOME}/.agents/skills/contextd"
mkdir -p "$TARGET_DIR"

# Export skill artifacts using the CLI
python3 -m scripts.cli export --runtime codex-plugin --workspace default --output "$TARGET_DIR"

echo "✅ Installed contextd skill to: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "  1. cd <your-project>"
echo "  2. codex 'Use contextd to find the Kafka consumer pattern'"
