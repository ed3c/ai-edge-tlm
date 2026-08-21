#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
mapfile -t files < <(find "$root/bindings/kotlin/src/main/kotlin" -name '*.kt' -print | sort)
kotlinc "${files[@]}" -d "${TMPDIR:-/tmp}/ai-edge-contracts-kotlin.jar"
