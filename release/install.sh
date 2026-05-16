#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${WIKI_RELEASE_URL:-}" ]]; then
  echo "ERROR: Missing WIKI_RELEASE_URL env var." >&2
  echo "Example: WIKI_RELEASE_URL='https://.../wiki-template-latest.zip' bash <(curl -fsSL https://.../install.sh)" >&2
  exit 1
fi

if command -v curl >/dev/null 2>&1; then
  DOWNLOADER="curl -fL --retry 3 --connect-timeout 15"
elif command -v wget >/dev/null 2>&1; then
  DOWNLOADER="wget -O"
else
  echo "ERROR: Need curl or wget." >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "ERROR: Missing unzip command." >&2
  exit 1
fi

TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t wiki-install)"
ZIP_PATH="$TMP_DIR/wiki-template.zip"
EXTRACT_DIR="$TMP_DIR/extract"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$EXTRACT_DIR"

echo "Downloading: $WIKI_RELEASE_URL"
if [[ "$DOWNLOADER" == curl* ]]; then
  curl -fL --retry 3 --connect-timeout 15 "$WIKI_RELEASE_URL" -o "$ZIP_PATH"
else
  wget -O "$ZIP_PATH" "$WIKI_RELEASE_URL"
fi

echo "Extracting package..."
unzip -q "$ZIP_PATH" -d "$EXTRACT_DIR"

REPO_ROOT="$EXTRACT_DIR/wiki-template"
if [[ ! -f "$REPO_ROOT/scripts/install-to-claude.sh" ]]; then
  echo "ERROR: Invalid artifact structure. Expected wiki-template/scripts/install-to-claude.sh" >&2
  exit 1
fi

echo "Running installer..."
(
  cd "$REPO_ROOT"
  bash scripts/install-to-claude.sh
)

echo "Done. Verify: cat ~/.claude/wiki-global.json"
