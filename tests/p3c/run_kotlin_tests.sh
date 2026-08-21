#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/p3c-tests.jar"
kotlinc "$ROOT"/bindings/kotlin/src/main/kotlin/io/ed3c/aiedge/contracts/v1/*.kt "$ROOT"/adapters/android/litert-lm/src/main/kotlin/io/ed3c/aiedge/adapters/android/litertlm/AndroidLiteRtLmAdapter.kt "$ROOT"/tests/p3c/AndroidLiteRtLmAdapterTest.kt -include-runtime -d "$OUT"
java -jar "$OUT"
