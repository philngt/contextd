#!/usr/bin/env bash
# Usage: bash scripts/build-binary.sh [VERSION]
# Builds a standalone contextd executable via PyInstaller.
# Output: dist/contextd (Linux/macOS) or dist/contextd.exe (Windows)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYINSTALLER_VERSION="${PYINSTALLER_VERSION:-6.11.0}"

cd "$REPO_ROOT"

PROJECT_VERSION="$(python3 scripts/cli.py --version)"
PROJECT_VERSION="${PROJECT_VERSION#contextd }"
VERSION="${1:-${PROJECT_VERSION}}"
if [[ "$VERSION" != "$PROJECT_VERSION" ]]; then
    echo "ERROR: version must match pyproject.toml (${PROJECT_VERSION})" >&2
    exit 1
fi

# Ensure PyInstaller is available
if ! python3 -c 'import PyInstaller' >/dev/null 2>&1; then
    echo "Installing PyInstaller ${PYINSTALLER_VERSION}..."
    python3 -m pip install "pyinstaller==${PYINSTALLER_VERSION}"
fi

# PyInstaller consumes the same canonical package/resources as wheel installs.
python3 -m pip install --no-deps .
echo "Building contextd binary (version ${VERSION})..."
python3 -m PyInstaller --clean contextd.spec

if [ -f "dist/contextd.exe" ]; then
    echo "Binary built at: dist/contextd.exe"
else
    echo "Binary built at: dist/contextd"
fi
