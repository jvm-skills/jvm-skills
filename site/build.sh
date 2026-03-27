#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v kotlin &>/dev/null; then
  echo "ERROR: kotlin is required but not found in PATH." >&2
  echo "Install via: sdk install kotlin  (https://sdkman.io)" >&2
  exit 1
fi

kotlin "$SCRIPT_DIR/build.main.kts" "$@"
