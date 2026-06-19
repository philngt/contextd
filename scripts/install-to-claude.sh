#!/usr/bin/env bash
#
# install-to-claude.sh
#
# Sync wiki-template's slash commands + subagents vào ~/.claude/ và setup
# ~/.claude/wiki-global.json với wiki_root trỏ về repo này.
#
# Idempotent: re-run mỗi khi pull wiki-template mới để cập nhật.
# Không động vào commands/agents user tự tạo (chỉ sync file đến từ wiki-template).
#
# Usage:
#   bash scripts/install-to-claude.sh [WIKI_ROOT] [--knowledge-repo PATH] [--dry-run] [--force]
#
#   WIKI_ROOT        Đường dẫn tuyệt đối đến wiki-template repo (default: parent
#                    của script này, tức là repo root khi chạy từ scripts/).
#   --knowledge-repo PATH   Path đến team knowledge repo (chứa workspaces/).
#                    Nếu được cung cấp, wiki_root trong wiki-global.json sẽ
#                    trỏ về KNOWLEDGE_REPO thay vì ENGINE_REPO.
#   --dry-run      In ra những gì sẽ làm, KHÔNG copy/ghi file.
#   --force          Skip confirmation khi overwrite ~/.claude/wiki-global.json.

set -euo pipefail

DRY_RUN=0
FORCE=0
WIKI_ROOT=""
KNOWLEDGE_REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ; shift ;;
    --force)   FORCE=1 ; shift ;;
    --knowledge-repo) KNOWLEDGE_REPO="$2"; shift 2 ;;
    -h|--help)
      sed -n '3,22p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      if [[ -z "$WIKI_ROOT" ]]; then
        WIKI_ROOT="$1"; shift
      else
        echo "Unknown arg: $1" >&2
        exit 2
      fi
      ;;
  esac
done

# Resolve ENGINE_ROOT (where commands/agents come from)
if [[ -z "$WIKI_ROOT" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  WIKI_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

# Resolve WIKI_ROOT for config (engine repo or knowledge repo)
WIKI_ROOT_CONFIG="${KNOWLEDGE_REPO:-$WIKI_ROOT}"

# Validate WIKI_ROOT
if [[ ! -d "$WIKI_ROOT" ]]; then
  echo "✗ WIKI_ROOT không tồn tại: $WIKI_ROOT" >&2
  exit 1
fi
if [[ ! -d "$WIKI_ROOT/.claude/commands" ]] || [[ ! -d "$WIKI_ROOT/agents" ]]; then
  echo "✗ $WIKI_ROOT không phải wiki-template repo (thiếu .claude/commands/ hoặc agents/)." >&2
  exit 1
fi

GLOBAL_CLAUDE="${HOME}/.claude"
GLOBAL_CONTEXTD="${HOME}/.contextd"
GLOBAL_COMMANDS="$GLOBAL_CLAUDE/commands"
GLOBAL_AGENTS="$GLOBAL_CLAUDE/agents"
GLOBAL_CONFIG="$GLOBAL_CLAUDE/wiki-global.json"
GLOBAL_CONTEXTD_CONFIG="$GLOBAL_CONTEXTD/config.json"

echo "Engine repo: $WIKI_ROOT"
if [[ -n "$KNOWLEDGE_REPO" ]]; then
  echo "Knowledge repo: $KNOWLEDGE_REPO"
fi
echo "Global dir:     $GLOBAL_CLAUDE"
[[ $DRY_RUN -eq 1 ]] && echo "Mode:       DRY RUN (no changes)"
echo ""

# --- helpers ---

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "  would: $*"
  else
    "$@"
  fi
}

# Sync 1 file. Prints status: NEW / UPDATED / UNCHANGED.
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

# --- 1. sync slash commands ---

echo "── Slash commands → $GLOBAL_COMMANDS"
[[ $DRY_RUN -eq 0 ]] && mkdir -p "$GLOBAL_COMMANDS"

shopt -s nullglob
for src in "$WIKI_ROOT/.claude/commands"/*.md; do
  name="$(basename "$src")"
  sync_file "$src" "$GLOBAL_COMMANDS/$name" "$name"
done
shopt -u nullglob
echo ""

# --- 1c. also sync contextd-team-sync command if it exists in knowledge repo ---
if [[ -n "$KNOWLEDGE_REPO" && -d "$KNOWLEDGE_REPO/.claude/commands" ]]; then
  shopt -s nullglob
  for src in "$KNOWLEDGE_REPO/.claude/commands"/*.md; do
    name="$(basename "$src")"
    # Only sync commands that don't exist in engine repo (team-specific overrides)
    if [[ ! -f "$WIKI_ROOT/.claude/commands/$name" ]]; then
      sync_file "$src" "$GLOBAL_COMMANDS/$name" "$name (from knowledge repo)"
    fi
  done
  shopt -u nullglob
  echo ""
fi

# --- 1b. migrate legacy wiki-*.md commands (pre-contextd rename) ---

# Map of legacy_name -> new_name. Most are `wiki-X` -> `contextd-X`,
# but the verbs use-wiki/update-wiki/rebase-wiki collapse the suffix.
declare -A LEGACY_MAP=(
  [wiki-backup]=contextd-backup
  [wiki-detect]=contextd-detect
  [wiki-eval]=contextd-eval
  [wiki-explain]=contextd-explain
  [wiki-report]=contextd-report
  [wiki-restore]=contextd-restore
  [wiki-setup]=contextd-setup
  [wiki-trace]=contextd-trace
  [wiki-upgrade]=contextd-upgrade
  [wiki-version]=contextd-version
  [wiki-viz]=contextd-viz
  [use-wiki]=use-contextd
  [update-wiki]=update-contextd
  [rebase-wiki]=rebase-contextd
)
LEGACY_FOUND=0
for legacy in "${!LEGACY_MAP[@]}"; do
  legacy_path="$GLOBAL_COMMANDS/${legacy}.md"
  if [[ -f "$legacy_path" ]]; then
    LEGACY_FOUND=1
    echo "  [REMOVED]   ${legacy}.md  (renamed → ${LEGACY_MAP[$legacy]}.md)"
    run rm -f "$legacy_path"
  fi
done
if [[ $LEGACY_FOUND -eq 1 ]]; then
  echo ""
  echo "  ⚠ Migration notice:"
  echo "    Slash commands /wiki-*, /use-wiki, /update-wiki, /rebase-wiki đã đổi tên thành /contextd-*."
  echo "    Workspace mẫu 'wiki' đã đổi tên thành 'default'."
  echo "    Nếu codebase nào có .claude/wiki.json với \"workspace\": \"wiki\","
  echo "    cập nhật thành \"workspace\": \"default\" (hoặc chạy lại /switch-workspace)."
  echo ""
fi

# --- 2. sync subagents ---

echo "── Subagents → $GLOBAL_AGENTS"
[[ $DRY_RUN -eq 0 ]] && mkdir -p "$GLOBAL_AGENTS"

shopt -s nullglob
for src in "$WIKI_ROOT/.claude/agents"/*.md; do
  name="$(basename "$src")"
  sync_file "$src" "$GLOBAL_AGENTS/$name" "$name"
done
shopt -u nullglob
echo ""

# --- 2b. migrate legacy wiki-* subagents (pre-contextd rename) ---

LEGACY_AGENTS=(
  wiki-planner wiki-context-selector wiki-plan-reviewer wiki-curator wiki-reviewer
)
for legacy in "${LEGACY_AGENTS[@]}"; do
  legacy_path="$GLOBAL_AGENTS/${legacy}.md"
  if [[ -f "$legacy_path" ]]; then
    new_name="contextd-${legacy#wiki-}"
    echo "  [REMOVED]   ${legacy}.md  (renamed → ${new_name}.md)"
    run rm -f "$legacy_path"
  fi
done

# --- 2c. remove deprecated subagents (merged into other agents) ---
# contextd-plan-reviewer was merged into contextd-context-selector (pipeline 5→4 stages).
DEPRECATED_AGENTS=(
  contextd-plan-reviewer
)
for agent in "${DEPRECATED_AGENTS[@]}"; do
  dep_path="$GLOBAL_AGENTS/${agent}.md"
  if [[ -f "$dep_path" ]]; then
    echo "  [REMOVED]   ${agent}.md  (deprecated — merged into contextd-context-selector)"
    run rm -f "$dep_path"
  fi
done
echo ""

# --- 3. wiki-global.json ---

echo "── Global config → $GLOBAL_CONFIG"
echo "── Canonical config → $GLOBAL_CONTEXTD_CONFIG"

# Convert WIKI_ROOT_CONFIG to forward-slash form (works trên cả Windows + Unix)
WIKI_ROOT_FWD="${WIKI_ROOT_CONFIG//\\//}"

if [[ -n "$KNOWLEDGE_REPO" ]]; then
  NEW_CONTEXTD_CONFIG=$(cat <<EOF
{
  "_comment": "Generated by contextd/scripts/install-to-claude.sh. knowledge_root points to the team knowledge repo. Legacy wiki_root config is still written for Claude Code adapters.",
  "knowledge_root": "$WIKI_ROOT_FWD",
  "default_workspace": null
}
EOF
)
  NEW_CONFIG=$(cat <<EOF
{
  "_comment": "Generated by wiki-template/scripts/install-to-claude.sh. wiki_root trỏ về team knowledge repo (chứa workspaces/). Engine repo (philngt/contextd) chỉ dùng để cài commands/agents. Edit default_workspace nếu muốn fallback cho codebase chưa có .claude/wiki.json.",
  "wiki_root": "$WIKI_ROOT_FWD",
  "default_workspace": null
}
EOF
)
else
  NEW_CONTEXTD_CONFIG=$(cat <<EOF
{
  "_comment": "Generated by contextd/scripts/install-to-claude.sh. knowledge_root points to the contextd engine repo for the default seed workspace. Legacy wiki_root config is still written for Claude Code adapters.",
  "knowledge_root": "$WIKI_ROOT_FWD",
  "default_workspace": null
}
EOF
)
  NEW_CONFIG=$(cat <<EOF
{
  "_comment": "Generated by wiki-template/scripts/install-to-claude.sh. wiki_root trỏ về wiki-template repo. Edit default_workspace nếu muốn fallback cho codebase chưa có .claude/wiki.json.",
  "wiki_root": "$WIKI_ROOT_FWD",
  "default_workspace": null
}
EOF
)
fi

if [[ ! -f "$GLOBAL_CONTEXTD_CONFIG" ]]; then
  echo "  [NEW] $GLOBAL_CONTEXTD_CONFIG"
  if [[ $DRY_RUN -eq 0 ]]; then
    mkdir -p "$GLOBAL_CONTEXTD"
    echo "$NEW_CONTEXTD_CONFIG" > "$GLOBAL_CONTEXTD_CONFIG"
  fi
else
  CURRENT_KNOWLEDGE_ROOT=$(grep -oE '"knowledge_root"[[:space:]]*:[[:space:]]*"[^"]*"' "$GLOBAL_CONTEXTD_CONFIG" | sed -E 's/.*"([^"]*)"$/\1/' || true)
  if [[ "$CURRENT_KNOWLEDGE_ROOT" == "$WIKI_ROOT_FWD" ]]; then
    echo "  [UNCHANGED] knowledge_root đã đúng ($WIKI_ROOT_FWD)"
  elif [[ $FORCE -eq 1 ]]; then
    echo "  [FORCED]    overwrite $GLOBAL_CONTEXTD_CONFIG (--force)"
    [[ $DRY_RUN -eq 0 ]] && echo "$NEW_CONTEXTD_CONFIG" > "$GLOBAL_CONTEXTD_CONFIG"
  else
    echo "  [CONFLICT] knowledge_root hiện tại: ${CURRENT_KNOWLEDGE_ROOT:-<empty>}"
    echo "             knowledge_root mới     : $WIKI_ROOT_FWD"
    echo "    Hoặc edit thủ công:            $GLOBAL_CONTEXTD_CONFIG"
  fi
fi

if [[ ! -f "$GLOBAL_CONFIG" ]]; then
  echo "  [NEW] $GLOBAL_CONFIG"
  if [[ $DRY_RUN -eq 0 ]]; then
    echo "$NEW_CONFIG" > "$GLOBAL_CONFIG"
  fi
else
  # File tồn tại — chỉ overwrite nếu wiki_root khác hoặc --force.
  CURRENT_ROOT=$(grep -oE '"wiki_root"[[:space:]]*:[[:space:]]*"[^"]*"' "$GLOBAL_CONFIG" | sed -E 's/.*"([^"]*)"$/\1/' || true)

  if [[ "$CURRENT_ROOT" == "$WIKI_ROOT_FWD" ]]; then
    echo "  [UNCHANGED] wiki_root đã đúng ($WIKI_ROOT_FWD)"
  else
    echo "  [CONFLICT] wiki_root hiện tại: ${CURRENT_ROOT:-<empty>}"
    echo "             wiki_root mới     : $WIKI_ROOT_FWD"
    if [[ $FORCE -eq 1 ]]; then
      echo "  [FORCED]    overwrite (--force)"
      [[ $DRY_RUN -eq 0 ]] && echo "$NEW_CONFIG" > "$GLOBAL_CONFIG"
    else
      echo ""
      echo "  ⚠ Không tự overwrite (sẽ mất default_workspace user đã set)."
      if [[ -n "$KNOWLEDGE_REPO" ]]; then
        echo "    Để overwrite hoàn toàn:        bash $0 $WIKI_ROOT --knowledge-repo $KNOWLEDGE_REPO --force"
      else
        echo "    Để overwrite hoàn toàn:        bash $0 $WIKI_ROOT --force"
      fi
      echo "    Hoặc edit thủ công:            $GLOBAL_CONFIG"
    fi
  fi
fi
echo ""

# --- summary ---

echo "✓ Done."
echo ""
if [[ -n "$KNOWLEDGE_REPO" ]]; then
  echo "Team sync enabled. knowledge_root → $WIKI_ROOT_FWD"
  echo ""
  echo "Test thử:"
  echo "  cd /path/to/your/codebase"
  echo "  /contextd-setup              # tạo .claude/wiki.json cho codebase đó"
  echo "  contextd migrate-config      # tạo .contextd/config.json canonical"
  echo "  /contextd-team-sync pull     # lấy knowledge mới nhất từ team"
  echo "  /use-contextd \"...task...\"   # dùng pipeline với context từ workspace active"
  echo ""
  echo "Sau khi update wiki:"
  echo "  /contextd-team-sync push     # đẩy thay đổi lên team repo"
else
  echo "Test thử:"
  echo "  cd /path/to/your/codebase"
  echo "  /contextd-setup           # tạo .claude/wiki.json cho codebase đó"
  echo "  contextd migrate-config   # tạo .contextd/config.json canonical"
  echo "  /list-workspaces      # xem có workspace nào trong wiki-template"
  echo "  /use-contextd \"...task...\"  # dùng pipeline với context từ workspace active"
fi
