#!/usr/bin/env bash
#
# setup-team-knowledge.sh
#
# One-liner onboarding script for new team members.
# Clones the team knowledge repo and runs install-to-claude.sh from the engine repo
# with --knowledge-repo pointing to the cloned knowledge repo.
#
# Usage:
#   bash setup-team-knowledge.sh \
#       --engine-repo ~/contextd \
#       --knowledge-repo git@github.com:company/company-wiki.git \
#       --local-path ~/company-wiki
#
#   --engine-repo PATH|URL    Path to local engine repo (philngt/contextd clone)
#                             or git URL to clone it.
#   --knowledge-repo URL      Git URL of the team knowledge repo.
#   --local-path PATH         Where to clone the knowledge repo locally.
#                             Defaults to ~/company-wiki.

set -euo pipefail

ENGINE_REPO=""
KNOWLEDGE_REPO=""
LOCAL_PATH=""

for arg in "$@"; do
  case "$arg" in
    --engine-repo)    shift; ENGINE_REPO="$1"; shift ;;
    --knowledge-repo) shift; KNOWLEDGE_REPO="$1"; shift ;;
    --local-path)     shift; LOCAL_PATH="$1"; shift ;;
    -h|--help)
      sed -n '3,18p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
  esac
done

# Validate required args
if [[ -z "$ENGINE_REPO" || -z "$KNOWLEDGE_REPO" || -z "$LOCAL_PATH" ]]; then
  echo "Usage: bash $0 --engine-repo <path|url> --knowledge-repo <url> --local-path <path>" >&2
  echo "" >&2
  echo "Example:" >&2
  echo "  bash $0 \\" >&2
  echo "    --engine-repo ~/contextd \\" >&2
  echo "    --knowledge-repo git@github.com:company/company-wiki.git \\" >&2
  echo "    --local-path ~/company-wiki" >&2
  exit 1
fi

# Resolve or clone engine repo
if [[ -d "$ENGINE_REPO/.git" ]]; then
  ENGINE_ROOT="$ENGINE_REPO"
  echo "Using existing engine repo: $ENGINE_ROOT"
elif [[ "$ENGINE_REPO" == git@* || "$ENGINE_REPO" == https://* ]]; then
  ENGINE_ROOT="$(dirname "$LOCAL_PATH")/contextd-engine"
  echo "Cloning engine repo → $ENGINE_ROOT"
  git clone "$ENGINE_REPO" "$ENGINE_ROOT"
else
  echo "Engine repo not found: $ENGINE_REPO" >&2
  exit 1
fi

# Clone knowledge repo
echo ""
echo "Cloning knowledge repo → $LOCAL_PATH"
if [[ -d "$LOCAL_PATH/.git" ]]; then
  echo "  (already exists — pulling latest)"
  git -C "$LOCAL_PATH" pull
else
  git clone "$KNOWLEDGE_REPO" "$LOCAL_PATH"
fi

# Run install-to-claude.sh with --knowledge-repo
echo ""
echo "Installing contextd engine with knowledge repo: $LOCAL_PATH"
bash "$ENGINE_ROOT/scripts/install-to-claude.sh" --knowledge-repo "$LOCAL_PATH"

# Verify
echo ""
echo "Verifying contextd config..."
GLOBAL_CONFIG="${HOME}/.contextd/config.json"
if [[ -f "$GLOBAL_CONFIG" ]]; then
  CURRENT_ROOT=$(grep -oE '"knowledge_root"[[:space:]]*:[[:space:]]*"[^"]*"' "$GLOBAL_CONFIG" | sed -E 's/.*"([^"]*)"$/\1/' || true)
  if [[ "$CURRENT_ROOT" == "$LOCAL_PATH" ]]; then
    echo "  OK — knowledge_root points to: $CURRENT_ROOT"
  else
    echo "  WARN — knowledge_root is: ${CURRENT_ROOT:-<empty>}"
    echo "         Expected: $LOCAL_PATH"
  fi
else
  echo "  WARN — contextd config not found at $GLOBAL_CONFIG"
fi

echo ""
echo "Done."
echo ""
echo "Next steps:"
echo "  cd /path/to/your-project"
echo "  /contextd-setup"
echo "  /use-contextd \"your task here\""
