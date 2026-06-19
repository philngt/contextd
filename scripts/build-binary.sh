#!/usr/bin/env bash
# Usage: bash scripts/build-binary.sh [VERSION]
# Builds a standalone contextd executable via PyInstaller.
# Output: dist/contextd (Linux/macOS) or dist/contextd.exe (Windows)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION="${1:-0.0.0-dev}"
PYINSTALLER_VERSION="${PYINSTALLER_VERSION:-6.11.0}"

cd "$REPO_ROOT"

# Generate ephemeral version module
echo "__version__ = '${VERSION}'" > scripts/_version.py
cleanup_version() {
    rm -f scripts/_version.py
}
trap cleanup_version EXIT

# Ensure PyInstaller is available
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "Installing PyInstaller ${PYINSTALLER_VERSION}..."
    pip install "pyinstaller==${PYINSTALLER_VERSION}"
fi

echo "Building contextd binary (version ${VERSION})..."
pyinstaller --clean contextd.spec

if [ -f "dist/contextd.exe" ]; then
    echo "Binary built at: dist/contextd.exe"
else
    echo "Binary built at: dist/contextd"
fi
