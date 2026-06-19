#!/usr/bin/env bash
#
# package-release.sh
#
# Package contextd source zip để distribute cho user không có Git.
# Output (both names emitted in parallel for migration window):
#   - release/contextd-{version}.zip       + release/contextd-latest.zip     (canonical)
#   - release/wiki-template-{version}.zip  + release/wiki-template-latest.zip (legacy alias)
#
# EXCLUDE:
#   - .git/, .github/, .gitattributes
#   - workspaces/* TRỪ workspaces/default/ và workspaces/README.md
#   - .claude/runs/, .claude/context/, .claude/settings.local.json
#   - evidence/ trong mọi workspace
#   - .observations/prompts.jsonl, *.lock
#   - __pycache__/, *.pyc, node_modules/, .DS_Store, Thumbs.db
#   - release/ (folder output này)
#
# INCLUDE:
#   - agents/, packs/, templates/, scripts/, .claude/commands/, .claude/agents/, .claude/settings.json
#   - workspaces/default/, workspaces/README.md
#   - README.md, QUICKSTART.md, CLAUDE.md, install.html, onboarding.html, .gitignore
#
# Usage:
#   bash scripts/package-release.sh                    # auto version từ git/timestamp
#   bash scripts/package-release.sh 1.2.0              # version manual
#   bash scripts/package-release.sh --dry-run          # in cây file sẽ pack, KHÔNG zip

set -euo pipefail

# ---------- resolve repo root ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# ---------- args ----------
DRY_RUN=0
VERSION=""
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --help|-h)
            sed -n '3,30p' "$0"  # print header doc
            exit 0
            ;;
        *) VERSION="$arg" ;;
    esac
done

# ---------- determine version ----------
if [[ -z "$VERSION" ]]; then
    if git rev-parse --git-dir > /dev/null 2>&1 && git rev-parse HEAD > /dev/null 2>&1; then
        # Try git tag, fallback to short commit + date
        COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
        if TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
            VERSION="${TAG}+${COMMIT}"
        else
            VERSION="0.0.0+${COMMIT}"
        fi
    else
        VERSION="0.0.0+$(date +%Y%m%d-%H%M%S)"
    fi
fi

echo "📦 Packaging contextd v${VERSION}"

# ---------- check zip available (skip for dry-run) ----------
if [[ $DRY_RUN -eq 0 ]] && ! command -v zip > /dev/null 2>&1; then
    echo "❌ ERROR: 'zip' command not found. Install:"
    echo "   - Linux:   apt install zip / yum install zip"
    echo "   - macOS:   brew install zip (usually pre-installed)"
    echo "   - Windows: use Git Bash (zip included) or install via choco/scoop"
    exit 1
fi

# ---------- prepare output ----------
RELEASE_DIR="$REPO_ROOT/release"
mkdir -p "$RELEASE_DIR"

OUT_NAME="contextd-${VERSION}.zip"
OUT_PATH="$RELEASE_DIR/$OUT_NAME"
LATEST_PATH="$RELEASE_DIR/contextd-latest.zip"
# Legacy aliases (same content) for migration window
LEGACY_OUT_PATH="$RELEASE_DIR/wiki-template-${VERSION}.zip"
LEGACY_LATEST_PATH="$RELEASE_DIR/wiki-template-latest.zip"

# ---------- staging area ----------
STAGE_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t wiki-pkg)"
STAGE_ROOT="$STAGE_DIR/wiki-template"  # Legacy zip root kept for v0.x compatibility.
mkdir -p "$STAGE_ROOT"

cleanup() {
    rm -rf "$STAGE_DIR"
}
trap cleanup EXIT

echo "📂 Staging at: $STAGE_DIR"

# ---------- copy with rsync (if available) or fallback ----------
EXCLUDES=(
    --exclude=".git/"
    --exclude=".github/"
    --exclude=".gitattributes"
    --exclude="release/"
    --exclude=".claude/runs/"
    --exclude=".claude/context/"
    --exclude=".claude/settings.local.json"
    --exclude="__pycache__/"
    --exclude="*.pyc"
    --exclude="node_modules/"
    --exclude=".DS_Store"
    --exclude="Thumbs.db"
    --exclude="*.swp"
    --exclude="*.swo"
    --exclude=".idea/"
    --exclude=".vscode/"
    --exclude="evidence/"
    --exclude=".observations/prompts.jsonl"
    --exclude=".observations/*.lock"
    --exclude="eval/results/"
)

if command -v rsync > /dev/null 2>&1; then
    echo "📤 Copying files (rsync)..."
    rsync -a "${EXCLUDES[@]}" \
        --exclude="workspaces/*/" \
        --include="workspaces/default/***" \
        --include="workspaces/README.md" \
        "$REPO_ROOT/" "$STAGE_ROOT/"
    # Note: workspaces/*/ exclude blocks all subdirs, but include workspaces/default/*** brings it back
else
    echo "⚠️  rsync not found — falling back to cp + manual cleanup (slower)."
    cp -r "$REPO_ROOT/." "$STAGE_ROOT/"
    # Remove unwanted
    rm -rf "$STAGE_ROOT/.git" "$STAGE_ROOT/.github" "$STAGE_ROOT/release" \
           "$STAGE_ROOT/.claude/runs" "$STAGE_ROOT/.claude/context" \
           "$STAGE_ROOT/.claude/settings.local.json" 2>/dev/null || true
    find "$STAGE_ROOT" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
    find "$STAGE_ROOT" -type d -name "node_modules" -prune -exec rm -rf {} + 2>/dev/null || true
    find "$STAGE_ROOT" -type d -name "evidence" -prune -exec rm -rf {} + 2>/dev/null || true
    find "$STAGE_ROOT" -type d -name ".idea" -prune -exec rm -rf {} + 2>/dev/null || true
    find "$STAGE_ROOT" -type d -name ".vscode" -prune -exec rm -rf {} + 2>/dev/null || true
    find "$STAGE_ROOT" -type f \( -name "*.pyc" -o -name ".DS_Store" -o -name "Thumbs.db" -o -name "*.swp" \) -delete 2>/dev/null || true
    # Workspaces: keep only default/ + README.md
    if [[ -d "$STAGE_ROOT/workspaces" ]]; then
        for d in "$STAGE_ROOT/workspaces"/*/; do
            name=$(basename "$d")
            if [[ "$name" != "default" ]]; then
                rm -rf "$d"
            fi
        done
    fi
fi

# ---------- write VERSION file ----------
cat > "$STAGE_ROOT/VERSION" <<EOF
$VERSION
$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

# ---------- size summary ----------
TOTAL_FILES=$(find "$STAGE_ROOT" -type f | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$STAGE_ROOT" 2>/dev/null | cut -f1)

echo ""
echo "📊 Staged content:"
echo "   Files: $TOTAL_FILES"
echo "   Size:  $TOTAL_SIZE (uncompressed)"
echo ""
echo "📁 Top-level entries:"
ls -la "$STAGE_ROOT" | tail -n +2 | awk '{print "   " $NF}' | grep -v "^\s*\.$\|^\s*\.\.$"
if [[ -d "$STAGE_ROOT/workspaces" ]]; then
    echo ""
    echo "📁 Included workspaces:"
    ls -la "$STAGE_ROOT/workspaces" | tail -n +2 | awk '{print "   " $NF}' | grep -v "^\s*\.$\|^\s*\.\.$"
fi

# ---------- dry run stops here ----------
if [[ $DRY_RUN -eq 1 ]]; then
    echo ""
    echo "🔍 Dry run — KHÔNG tạo zip. Files đã stage tại:"
    echo "   $STAGE_ROOT"
    echo ""
    echo "   (sẽ bị xoá khi script exit)"
    trap - EXIT  # disable cleanup so user can inspect
    echo "   trap removed — folder NOT cleaned up automatically."
    exit 0
fi

# ---------- create zip ----------
echo ""
echo "🗜️  Creating zip..."
( cd "$STAGE_DIR" && zip -rq "$OUT_PATH" "wiki-template" )

# ---------- update latest pointer + legacy aliases ----------
cp "$OUT_PATH" "$LATEST_PATH"
cp "$OUT_PATH" "$LEGACY_OUT_PATH"
cp "$OUT_PATH" "$LEGACY_LATEST_PATH"

ZIP_SIZE=$(du -h "$OUT_PATH" | cut -f1)

echo ""
echo "✅ Release packaged ($ZIP_SIZE each):"
echo "   Canonical:"
echo "     $OUT_PATH"
echo "     $LATEST_PATH"
echo "   Legacy alias (migration window):"
echo "     $LEGACY_OUT_PATH"
echo "     $LEGACY_LATEST_PATH"
echo ""
echo "📤 Distribute:"
echo "   - Upload to GitHub Releases / S3 / file server"
echo "   - Or share file trực tiếp với user"
echo ""
echo "💡 install.html section 'Download không cần Git' link tới release/contextd-latest.zip"
