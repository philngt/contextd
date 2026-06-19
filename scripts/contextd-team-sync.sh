#!/usr/bin/env bash
#
# contextd-team-sync.sh
#
# Pull/push workspace knowledge from/to the team knowledge repo.
# This script resolves knowledge_root from ~/.contextd/config.json or legacy globals and operates
# on that directory (which should be a git repository).
#
# Usage:
#   bash scripts/contextd-team-sync.sh pull    # update local knowledge from team
#   bash scripts/contextd-team-sync.sh push    # push local wiki changes to team repo
#   bash scripts/contextd-team-sync.sh status  # show workspace change status
#
# Environment:
#   KNOWLEDGE_ROOT Override auto-resolved knowledge_root (useful in CI).
#   WIKI_ROOT      Legacy override alias.

set -euo pipefail

# --- resolve knowledge_root ---

if [[ -n "${KNOWLEDGE_ROOT:-}" ]]; then
  KNOWLEDGE_ROOT_ABS="$KNOWLEDGE_ROOT"
elif [[ -n "${WIKI_ROOT:-}" ]]; then
  KNOWLEDGE_ROOT_ABS="$WIKI_ROOT"
else
  GLOBAL_CONFIG=""
  if [[ -f "${HOME}/.contextd/config.json" ]]; then
    GLOBAL_CONFIG="${HOME}/.contextd/config.json"
  elif [[ -f "${HOME}/.claude/wiki-global.json" ]]; then
    GLOBAL_CONFIG="${HOME}/.claude/wiki-global.json"
  elif [[ -f "${HOME}/.Codex/wiki-global.json" ]]; then
    GLOBAL_CONFIG="${HOME}/.Codex/wiki-global.json"
  fi
  if [[ -z "$GLOBAL_CONFIG" ]]; then
    echo "✗ No global contextd config found." >&2
    echo "  Expected ~/.contextd/config.json or legacy ~/.claude/wiki-global.json." >&2
    exit 1
  fi
  KNOWLEDGE_ROOT_RAW=$(grep -oE '"knowledge_root"[[:space:]]*:[[:space:]]*"[^"]*"' "$GLOBAL_CONFIG" | sed -E 's/.*"([^"]*)"$/\1/' || true)
  if [[ -z "${KNOWLEDGE_ROOT_RAW:-}" || "$KNOWLEDGE_ROOT_RAW" == "null" ]]; then
    KNOWLEDGE_ROOT_RAW=$(grep -oE '"wiki_root"[[:space:]]*:[[:space:]]*"[^"]*"' "$GLOBAL_CONFIG" | sed -E 's/.*"([^"]*)"$/\1/' || true)
  fi
  if [[ -z "${KNOWLEDGE_ROOT_RAW:-}" || "$KNOWLEDGE_ROOT_RAW" == "null" ]]; then
    echo "✗ knowledge_root not set in $GLOBAL_CONFIG" >&2
    exit 1
  fi
  # Expand ~
  KNOWLEDGE_ROOT_ABS="${KNOWLEDGE_ROOT_RAW/#\~/$HOME}"
fi

if [[ ! -d "$KNOWLEDGE_ROOT_ABS" ]]; then
  echo "✗ knowledge_root directory does not exist: $KNOWLEDGE_ROOT_ABS" >&2
  exit 1
fi

# --- validate git repo ---

if [[ ! -d "$KNOWLEDGE_ROOT_ABS/.git" ]]; then
  echo "✗ knowledge_root is not a git repository: $KNOWLEDGE_ROOT_ABS" >&2
  echo "" >&2
  echo "  To use team sync, knowledge_root must point to a git repo" >&2
  echo "  (typically your team's knowledge repo)." >&2
  echo "" >&2
  echo "  Quick fix:" >&2
  echo "    1. Clone your team knowledge repo:" >&2
  echo "       git clone <team-repo-url> ~/company-wiki" >&2
  echo "    2. Update ~/.contextd/config.json:" >&2
  echo '       { "workspace": "default", "knowledge_root": "/Users/you/company-wiki" }' >&2
  exit 1
fi

# --- helpers ---

git_cmd() {
  git -C "$KNOWLEDGE_ROOT_ABS" "$@"
}

# --- dispatch ---

COMMAND="${1:-}"

case "$COMMAND" in
  pull)
    echo "Pulling latest knowledge into: $KNOWLEDGE_ROOT_ABS"
    if git_cmd pull --ff-only 2>/dev/null; then
      echo "  Done."
    else
      echo "  Pull failed. You may have local changes." >&2
      echo "  Resolve manually: cd $KNOWLEDGE_ROOT_ABS && git status" >&2
      exit 1
    fi
    ;;

  push)
    # Check if there are any changes in workspaces/
    if git_cmd diff --quiet --cached -- workspaces/ 2>/dev/null && \
       git_cmd diff --quiet -- workspaces/ 2>/dev/null; then
      echo "No changes in workspaces/ to push."
      exit 0
    fi

    # Prompt for commit message if stdin is a TTY
    DEFAULT_MSG="Update workspace knowledge ($(date +%Y-%m-%d))"
    if [[ -t 0 ]]; then
      read -r -p "Commit message [$DEFAULT_MSG]: " MSG
      MSG="${MSG:-$DEFAULT_MSG}"
    else
      MSG="$DEFAULT_MSG"
    fi

    echo "Pushing workspace changes from: $KNOWLEDGE_ROOT_ABS"
    git_cmd add workspaces/
    if git_cmd diff --quiet --cached -- workspaces/; then
      echo "  No changes to commit."
      exit 0
    fi
    git_cmd commit -m "$MSG"
    git_cmd push
    echo "  Done."
    ;;

  status)
    echo "Knowledge repo: $KNOWLEDGE_ROOT_ABS"
    echo "Branch: $(git_cmd rev-parse --abbrev-ref HEAD)"
    echo ""
    CHANGES=$(git_cmd status --short workspaces/ || true)
    if [[ -z "$CHANGES" ]]; then
      echo "  workspaces/ is clean (no uncommitted changes)."
    else
      echo "  Uncommitted changes in workspaces/:"
      echo "$CHANGES" | sed 's/^/    /'
    fi
    ;;

  *)
    echo "Usage: bash $(basename "$0") {pull|push|status}" >&2
    exit 1
    ;;
esac
