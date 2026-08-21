#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/ai-edge-p3a-${$}.jar"
mapfile -t CONTRACTS < <(find "$ROOT/bindings/kotlin/src/main/kotlin" -name '*.kt' -type f | sort)
mapfile -t ADAPTER < <(find "$ROOT/adapters/android/system-genai/src/main/kotlin" -name '*.kt' -type f | sort)
kotlinc "${CONTRACTS[@]}" "${ADAPTER[@]}" "$ROOT/tests/p3a/AndroidSystemAdapterTest.kt" -include-runtime -d "$OUT"
java -jar "$OUT"
rm -f "$OUT"
