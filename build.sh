#!/usr/bin/env bash
# Build a standalone binary for the current platform.
# Run from the project root:  bash build.sh
set -e

VENV="venv/bin"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  VENV="venv/Scripts"
fi

echo "==> Cleaning previous build..."
rm -rf build dist

echo "==> Building with PyInstaller..."
"$VENV/pyinstaller" etrade-gl.spec

echo ""
echo "Done! Binary is at: dist/etrade-gl"
echo "Run it with:  ./dist/etrade-gl"
