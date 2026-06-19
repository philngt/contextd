#!/usr/bin/env bash
#
# install-to-claude.sh
#
# Install contextd's Claude adapter files and write canonical global config.
#
# Usage:
#   bash scripts/install-to-claude.sh [ENGINE_ROOT] [options]
#
# Options:
#   --engine-root PATH          Path to the contextd engine repo.
#   --knowledge-root PATH       Canonical root containing workspaces/.
#   --knowledge-repo PATH       Compatibility alias for --knowledge-root.
#   --default-workspace NAME    Write default_workspace in ~/.contextd/config.json.
#   --print-mcp-config CLIENT   Print MCP snippet for claude|cursor|codex|all and exit.
#   --dry-run                   Print actions without copying or writing files.
#   --force                     Overwrite existing global configs when roots differ.

set -euo pipefail

DRY_RUN=0
FORCE=0
ENGINE_ROOT=""
KNOWLEDGE_ROOT=""
KNOWLEDGE_REPO_ALIAS_USED=0
DEFAULT_WORKSPACE=""
PRINT_MCP_CONFIG=""

usage() {
  sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --engine-root) ENGINE_ROOT="$2"; shift 2 ;;
    --knowledge-root) KNOWLEDGE_ROOT="$2"; shift 2 ;;
    --knowledge-repo)
      KNOWLEDGE_ROOT="$2"
      KNOWLEDGE_REPO_ALIAS_USED=1
      shift 2
      ;;
    --default-workspace) DEFAULT_WORKSPACE="$2"; shift 2 ;;
    --print-mcp-config) PRINT_MCP_CONFIG="$2"; shift 2 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$ENGINE_ROOT" ]]; then
        ENGINE_ROOT="$1"
        shift
      else
        echo "Unknown arg: $1" >&2
        exit 2
      fi
      ;;
  esac
done

expand_path() {
  local path="$1"
  case "$path" in
    "~") path="$HOME" ;;
    "~/"*) path="$HOME/${path#~/}" ;;
  esac
  printf "%s" "$path"
}

abs_dir() {
  local path
  path="$(expand_path "$1")"
  if [[ ! -d "$path" ]]; then
    printf "%s" "$path"
    return 0
  fi
  (cd "$path" && pwd)
}

json_string_or_null() {
  local value="$1"
  if [[ -z "$value" ]]; then
    printf "null"
  else
    printf '"%s"' "${value//\"/\\\"}"
  fi
}

read_json_string_key() {
  local file="$1"
  local key="$2"
  if [[ ! -f "$file" ]]; then
    return 0
  fi
  grep -oE "\"${key}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$file" \
    | sed -E 's/.*"([^"]*)"$/\1/' \
    | head -n 1 || true
}

if [[ -z "$ENGINE_ROOT" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ENGINE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  ENGINE_ROOT="$(abs_dir "$ENGINE_ROOT")"
fi

if [[ ! -d "$ENGINE_ROOT" ]]; then
  echo "Error: ENGINE_ROOT does not exist: $ENGINE_ROOT" >&2
  exit 1
fi
if [[ ! -d "$ENGINE_ROOT/.claude/commands" ]] || [[ ! -d "$ENGINE_ROOT/agents" ]]; then
  echo "Error: $ENGINE_ROOT is not a contextd engine repo (missing .claude/commands or agents)." >&2
  exit 1
fi

GLOBAL_CLAUDE="${HOME}/.claude"
GLOBAL_CONTEXTD="${HOME}/.contextd"
GLOBAL_COMMANDS="$GLOBAL_CLAUDE/commands"
GLOBAL_AGENTS="$GLOBAL_CLAUDE/agents"
GLOBAL_CONFIG="$GLOBAL_CLAUDE/wiki-global.json"
GLOBAL_CONTEXTD_CONFIG="$GLOBAL_CONTEXTD/config.json"
CURRENT_KNOWLEDGE_ROOT="$(read_json_string_key "$GLOBAL_CONTEXTD_CONFIG" "knowledge_root")"

if [[ $KNOWLEDGE_REPO_ALIAS_USED -eq 1 ]]; then
  echo "Warning: --knowledge-repo is a compatibility alias. Use --knowledge-root for canonical installs." >&2
fi

if [[ -z "$KNOWLEDGE_ROOT" ]]; then
  if [[ -t 0 ]]; then
    echo "Select workspace/knowledge root (canonical knowledge_root):"
    if [[ -n "$CURRENT_KNOWLEDGE_ROOT" ]]; then
      echo "  1) Current config root: $CURRENT_KNOWLEDGE_ROOT"
      echo "  2) Engine repo root:    $ENGINE_ROOT"
      echo "  3) Custom path"
      printf "Choice [1]: "
      read -r choice
      choice="${choice:-1}"
      case "$choice" in
        1) KNOWLEDGE_ROOT="$CURRENT_KNOWLEDGE_ROOT" ;;
        2) KNOWLEDGE_ROOT="$ENGINE_ROOT" ;;
        3)
          printf "Custom knowledge_root: "
          read -r KNOWLEDGE_ROOT
          ;;
        *)
          echo "Invalid choice: $choice" >&2
          exit 2
          ;;
      esac
    else
      echo "  1) Engine repo root: $ENGINE_ROOT"
      echo "  2) Custom path"
      printf "Choice [1]: "
      read -r choice
      choice="${choice:-1}"
      case "$choice" in
        1) KNOWLEDGE_ROOT="$ENGINE_ROOT" ;;
        2)
          printf "Custom knowledge_root: "
          read -r KNOWLEDGE_ROOT
          ;;
        *)
          echo "Invalid choice: $choice" >&2
          exit 2
          ;;
      esac
    fi
  else
    KNOWLEDGE_ROOT="$ENGINE_ROOT"
  fi
fi

KNOWLEDGE_ROOT="$(abs_dir "$KNOWLEDGE_ROOT")"

if [[ ! -d "$KNOWLEDGE_ROOT" ]]; then
  echo "Error: knowledge_root does not exist: $KNOWLEDGE_ROOT" >&2
  exit 1
fi
if [[ ! -d "$KNOWLEDGE_ROOT/workspaces" ]]; then
  echo "Error: knowledge_root must contain workspaces/: $KNOWLEDGE_ROOT" >&2
  exit 1
fi
if ! git -C "$KNOWLEDGE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Warning: knowledge_root is not a git repo: $KNOWLEDGE_ROOT" >&2
fi

if [[ -n "$PRINT_MCP_CONFIG" ]]; then
  MCP_ARGS=(mcp-config --client "$PRINT_MCP_CONFIG" --knowledge-root "$KNOWLEDGE_ROOT")
  if [[ -n "$DEFAULT_WORKSPACE" ]]; then
    MCP_ARGS+=(--workspace "$DEFAULT_WORKSPACE")
  fi
  python3 "$ENGINE_ROOT/scripts/cli.py" "${MCP_ARGS[@]}"
  exit $?
fi

echo "Engine root:    $ENGINE_ROOT"
echo "Knowledge root: $KNOWLEDGE_ROOT"
if [[ -n "$DEFAULT_WORKSPACE" ]]; then
  echo "Default workspace: $DEFAULT_WORKSPACE"
fi
echo "Global dir:     $GLOBAL_CLAUDE"
[[ $DRY_RUN -eq 1 ]] && echo "Mode:           DRY RUN (no changes)"
echo ""

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  would: $*"
  else
    "$@"
  fi
}

write_content() {
  local path="$1"
  local content="$2"
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  would write: $path"
  else
    mkdir -p "$(dirname "$path")"
    printf "%s\n" "$content" > "$path"
  fi
}

sync_file() {
  local src="$1"
  local dst="$2"
  local label="$3"

  if [[ ! -f "$dst" ]]; then
    echo "  [NEW]       $label"
    run mkdir -p "$(dirname "$dst")"
    run cp "$src" "$dst"
  elif ! cmp -s "$src" "$dst"; then
    echo "  [UPDATED]   $label"
    run cp "$src" "$dst"
  else
    echo "  [UNCHANGED] $label"
  fi
}

echo "-- Slash commands -> $GLOBAL_COMMANDS"
[[ $DRY_RUN -eq 0 ]] && mkdir -p "$GLOBAL_COMMANDS"

shopt -s nullglob
for src in "$ENGINE_ROOT/.claude/commands"/*.md; do
  name="$(basename "$src")"
  sync_file "$src" "$GLOBAL_COMMANDS/$name" "$name"
done
shopt -u nullglob
echo ""

if [[ "$KNOWLEDGE_ROOT" != "$ENGINE_ROOT" && -d "$KNOWLEDGE_ROOT/.claude/commands" ]]; then
  shopt -s nullglob
  for src in "$KNOWLEDGE_ROOT/.claude/commands"/*.md; do
    name="$(basename "$src")"
    if [[ ! -f "$ENGINE_ROOT/.claude/commands/$name" ]]; then
      sync_file "$src" "$GLOBAL_COMMANDS/$name" "$name (from knowledge root)"
    fi
  done
  shopt -u nullglob
  echo ""
fi

LEGACY_PAIRS=(
  "wiki-backup:contextd-backup"
  "wiki-detect:contextd-detect"
  "wiki-eval:contextd-eval"
  "wiki-explain:contextd-explain"
  "wiki-report:contextd-report"
  "wiki-restore:contextd-restore"
  "wiki-setup:contextd-setup"
  "wiki-trace:contextd-trace"
  "wiki-upgrade:contextd-upgrade"
  "wiki-version:contextd-version"
  "wiki-viz:contextd-viz"
  "use-wiki:use-contextd"
  "update-wiki:update-contextd"
  "rebase-wiki:rebase-contextd"
)
LEGACY_FOUND=0
for pair in "${LEGACY_PAIRS[@]}"; do
  legacy="${pair%%:*}"
  new_name="${pair#*:}"
  legacy_path="$GLOBAL_COMMANDS/${legacy}.md"
  if [[ -f "$legacy_path" ]]; then
    LEGACY_FOUND=1
    echo "  [REMOVED]   ${legacy}.md (renamed -> ${new_name}.md)"
    run rm -f "$legacy_path"
  fi
done
if [[ $LEGACY_FOUND -eq 1 ]]; then
  echo ""
  echo "  Migration notice:"
  echo "    Slash commands /wiki-*, /use-wiki, /update-wiki, /rebase-wiki were renamed to /contextd-*."
  echo "    If a codebase still has legacy config, run: contextd migrate-config"
  echo ""
fi

echo "-- Subagents -> $GLOBAL_AGENTS"
[[ $DRY_RUN -eq 0 ]] && mkdir -p "$GLOBAL_AGENTS"

shopt -s nullglob
for src in "$ENGINE_ROOT/.claude/agents"/*.md; do
  name="$(basename "$src")"
  sync_file "$src" "$GLOBAL_AGENTS/$name" "$name"
done
shopt -u nullglob
echo ""

LEGACY_AGENTS=(
  wiki-planner wiki-context-selector wiki-plan-reviewer wiki-curator wiki-reviewer
)
for legacy in "${LEGACY_AGENTS[@]}"; do
  legacy_path="$GLOBAL_AGENTS/${legacy}.md"
  if [[ -f "$legacy_path" ]]; then
    new_name="contextd-${legacy#wiki-}"
    echo "  [REMOVED]   ${legacy}.md (renamed -> ${new_name}.md)"
    run rm -f "$legacy_path"
  fi
done

DEPRECATED_AGENTS=(
  contextd-plan-reviewer
)
for agent in "${DEPRECATED_AGENTS[@]}"; do
  dep_path="$GLOBAL_AGENTS/${agent}.md"
  if [[ -f "$dep_path" ]]; then
    echo "  [REMOVED]   ${agent}.md (deprecated; merged into contextd-context-selector)"
    run rm -f "$dep_path"
  fi
done
echo ""

echo "-- Global config -> $GLOBAL_CONFIG"
echo "-- Canonical config -> $GLOBAL_CONTEXTD_CONFIG"

KNOWLEDGE_ROOT_FWD="${KNOWLEDGE_ROOT//\\//}"
DEFAULT_WORKSPACE_JSON="$(json_string_or_null "$DEFAULT_WORKSPACE")"

NEW_CONTEXTD_CONFIG=$(cat <<EOF
{
  "_comment": "Generated by contextd/scripts/install-to-claude.sh. knowledge_root is canonical; legacy wiki globals are compatibility adapters.",
  "knowledge_root": "$KNOWLEDGE_ROOT_FWD",
  "default_workspace": $DEFAULT_WORKSPACE_JSON
}
EOF
)

NEW_LEGACY_CONFIG=$(cat <<EOF
{
  "_comment": "Compatibility adapter generated by contextd/scripts/install-to-claude.sh. Canonical config lives at ~/.contextd/config.json.",
  "wiki_root": "$KNOWLEDGE_ROOT_FWD",
  "default_workspace": $DEFAULT_WORKSPACE_JSON
}
EOF
)

write_contextd_config() {
  if [[ ! -f "$GLOBAL_CONTEXTD_CONFIG" ]]; then
    echo "  [NEW]       $GLOBAL_CONTEXTD_CONFIG"
    write_content "$GLOBAL_CONTEXTD_CONFIG" "$NEW_CONTEXTD_CONFIG"
    return
  fi

  local current_root
  current_root="$(read_json_string_key "$GLOBAL_CONTEXTD_CONFIG" "knowledge_root")"
  if [[ "$current_root" == "$KNOWLEDGE_ROOT_FWD" ]]; then
    if [[ -n "$DEFAULT_WORKSPACE" ]]; then
      echo "  [UPDATED]   default_workspace -> $DEFAULT_WORKSPACE"
      write_content "$GLOBAL_CONTEXTD_CONFIG" "$NEW_CONTEXTD_CONFIG"
    else
      echo "  [UNCHANGED] knowledge_root is already $KNOWLEDGE_ROOT_FWD"
    fi
  elif [[ $FORCE -eq 1 ]]; then
    echo "  [FORCED]    overwrite $GLOBAL_CONTEXTD_CONFIG"
    write_content "$GLOBAL_CONTEXTD_CONFIG" "$NEW_CONTEXTD_CONFIG"
  else
    echo "  [CONFLICT]  knowledge_root current: ${current_root:-<empty>}"
    echo "              knowledge_root new:     $KNOWLEDGE_ROOT_FWD"
    echo "              Re-run with --force to overwrite or edit $GLOBAL_CONTEXTD_CONFIG"
  fi
}

write_legacy_config() {
  if [[ ! -f "$GLOBAL_CONFIG" ]]; then
    echo "  [NEW]       $GLOBAL_CONFIG"
    write_content "$GLOBAL_CONFIG" "$NEW_LEGACY_CONFIG"
    return
  fi

  local current_root
  current_root="$(read_json_string_key "$GLOBAL_CONFIG" "wiki_root")"
  if [[ "$current_root" == "$KNOWLEDGE_ROOT_FWD" ]]; then
    if [[ -n "$DEFAULT_WORKSPACE" ]]; then
      echo "  [UPDATED]   legacy default_workspace -> $DEFAULT_WORKSPACE"
      write_content "$GLOBAL_CONFIG" "$NEW_LEGACY_CONFIG"
    else
      echo "  [UNCHANGED] legacy wiki_root is already $KNOWLEDGE_ROOT_FWD"
    fi
  elif [[ $FORCE -eq 1 ]]; then
    echo "  [FORCED]    overwrite $GLOBAL_CONFIG"
    write_content "$GLOBAL_CONFIG" "$NEW_LEGACY_CONFIG"
  else
    echo "  [CONFLICT]  legacy wiki_root current: ${current_root:-<empty>}"
    echo "              legacy wiki_root new:     $KNOWLEDGE_ROOT_FWD"
    echo "              This legacy file is only for adapter compatibility."
  fi
}

write_contextd_config
write_legacy_config
echo ""

echo "Done."
echo ""
echo "Try:"
echo "  cd /path/to/your/codebase"
echo "  /contextd-setup              # creates .contextd/config.json for that codebase"
echo "  contextd resolve             # verify workspace and knowledge_root"
echo "  contextd context \"...task...\" --format json"
echo ""
echo "MCP snippets:"
echo "  bash $0 --knowledge-root \"$KNOWLEDGE_ROOT_FWD\" --print-mcp-config codex"
