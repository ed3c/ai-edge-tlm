from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from contracts.generator.generate import ROOT

RUN_NATIVE = os.environ.get("AI_EDGE_RUN_NATIVE_TOOLCHAINS") == "1"


def require_native_toolchains() -> tuple[str, str, str]:
    if not RUN_NATIVE:
        pytest.skip("native compile is a separate LOCAL evidence lane; set AI_EDGE_RUN_NATIVE_TOOLCHAINS=1")
    kotlinc = shutil.which("kotlinc")
    swift = shutil.which("swift")
    swiftc = shutil.which("swiftc")
    if kotlinc is None or swift is None or swiftc is None:
        pytest.skip("Kotlin and Swift toolchains are not both installed on this evidence host")
    return kotlinc, swift, swiftc


def test_kotlin_sources_compile_on_explicit_native_lane(tmp_path: Path) -> None:
    kotlinc, _, _ = require_native_toolchains()
    sources = sorted((ROOT / "bindings/kotlin/src/main/kotlin").rglob("*.kt"))
    subprocess.run([kotlinc, *map(str, sources), "-d", str(tmp_path / "contracts.jar")], check=True)


def test_swift_package_builds_on_explicit_native_lane() -> None:
    _, swift, _ = require_native_toolchains()
    subprocess.run([swift, "build", "--package-path", str(ROOT / "bindings/swift")], check=True)


def test_cross_language_golden_on_explicit_native_lane() -> None:
    require_native_toolchains()
    subprocess.run([str(ROOT / "tests/p2/run_toolchain_golden.sh")], check=True)
