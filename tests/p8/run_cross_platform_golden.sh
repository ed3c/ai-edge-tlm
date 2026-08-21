#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mapfile -t KOTLIN_CONTRACTS < <(find "$ROOT/bindings/kotlin/src/main/kotlin" -name '*.kt' -print | sort)
kotlinc "${KOTLIN_CONTRACTS[@]}" "$ROOT/apps/android-reference/src/main/kotlin/io/ed3c/aiedge/reference/ReferenceHost.kt" "$ROOT/tests/p8/AndroidGoldenMain.kt" -include-runtime -d "$TMP/android.jar"
ANDROID="$(java -jar "$TMP/android.jar")"
IOS="$(swift run --package-path "$ROOT/apps/ios-reference" ios-reference-golden 2>/dev/null | tail -n 1)"
EXPECTED="$(python - <<PY
import json
from pathlib import Path
p=Path('$ROOT/apps/convergence/golden/reference-scenario.json')
print(json.dumps(json.loads(p.read_text()),sort_keys=True,separators=(',',':')))
PY
)"
[[ "$ANDROID" == "$EXPECTED" ]]
[[ "$IOS" == "$EXPECTED" ]]
printf '%s\n' "$EXPECTED"
