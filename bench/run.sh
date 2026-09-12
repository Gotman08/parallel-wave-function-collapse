#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
PYTHON=${PYTHON:-python3}
BUILD_DIR=${BUILD_DIR:-build}
OUTPUT=${1:-bench/results/local}
"$PYTHON" bench/collect.py --build "$BUILD_DIR" --output "$OUTPUT"
