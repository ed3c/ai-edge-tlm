from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from contracts.generator.generate import ROOT


def test_kotlin_sources_compile_when_toolchain_is_available(tmp_path: Path) -> None:
    compiler = shutil.which("kotlinc")
    if compiler is None:
        pytest.skip("kotlinc not installed on this evidence host")
    sources = sorted((ROOT / "bindings/kotlin/src/main/kotlin").rglob("*.kt"))
    subprocess.run([compiler, *map(str, sources), "-d", str(tmp_path / "contracts.jar")], check=True)


def test_swift_package_builds_when_toolchain_is_available() -> None:
    compiler = shutil.which("swift")
    if compiler is None:
        pytest.skip("Swift not installed on this evidence host")
    subprocess.run([compiler, "build", "--package-path", str(ROOT / "bindings/swift")], check=True)


def test_cross_language_golden_when_both_toolchains_are_available() -> None:
    if shutil.which("kotlinc") is None or shutil.which("swiftc") is None:
        pytest.skip("Kotlin and Swift toolchains are both required")
    subprocess.run([str(ROOT / "tests/p2/run_toolchain_golden.sh")], check=True)
