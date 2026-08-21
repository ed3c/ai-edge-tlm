#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

expected=$(python - <<'PY' "$root/contracts/examples/inference-request.json"
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    print(json.dumps(json.load(f), ensure_ascii=False, sort_keys=True, separators=(',', ':')), end='')
PY
)

mapfile -t kotlin_sources < <(find "$root/bindings/kotlin/src/main/kotlin" -name '*.kt' -print | sort)
kotlinc "${kotlin_sources[@]}" "$root/tests/p2/toolchains/KotlinGolden.kt" -include-runtime -d "$tmp/kotlin-golden.jar"
kotlin_output=$(java -jar "$tmp/kotlin-golden.jar")
[[ "$kotlin_output" == "$expected" ]] || { echo "Kotlin golden mismatch" >&2; diff -u <(printf '%s\n' "$expected") <(printf '%s\n' "$kotlin_output") || true; exit 1; }

mapfile -t swift_sources < <(find "$root/bindings/swift/Sources/AIEdgeContracts" -name '*.swift' -print | sort)
swiftc "${swift_sources[@]}" "$root/tests/p2/toolchains/SwiftGolden.swift" -o "$tmp/swift-golden"
swift_output=$("$tmp/swift-golden")
[[ "$swift_output" == "$expected" ]] || { echo "Swift golden mismatch" >&2; diff -u <(printf '%s\n' "$expected") <(printf '%s\n' "$swift_output") || true; exit 1; }

[[ "$kotlin_output" == "$swift_output" ]] || { echo "cross-language mismatch" >&2; exit 1; }
echo "PASS: Kotlin and Swift emit the same canonical inference-request wire value"
