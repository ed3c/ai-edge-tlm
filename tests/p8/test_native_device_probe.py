from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from apps.convergence.native_device_probe import NativeProbeError, probe_native_resources, validate_native_build_receipt

COMMIT = "0" * 40


def test_probe_fails_closed_when_android_and_apple_resources_are_missing():
    receipt = probe_native_resources(
        app_commit=COMMIT,
        environ={},
        which=lambda _: None,
        system="Linux",
        machine="x86_64",
    )
    assert receipt.android.state == "BLOCKED_RESOURCE"
    assert "ANDROID_SDK_HOME_MISSING" in receipt.android.blockers
    assert "ANDROID_DEVICE_MISSING" in receipt.android.blockers
    assert receipt.apple.state == "BLOCKED_RESOURCE"
    assert "MACOS_HOST_REQUIRED" in receipt.apple.blockers
    assert "APPLE_DEVICE_MISSING" in receipt.apple.blockers


def test_probe_only_calls_device_commands_when_tools_exist():
    paths = {"java": "/j/java", "gradle": "/g/gradle", "sdkmanager": "/s/sdkmanager", "adb": "/a/adb", "xcodebuild": "/x/xcodebuild", "xcrun": "/x/xcrun"}
    def which(name: str): return paths.get(name)
    def runner(argv, **kwargs):
        if argv[0].endswith("adb"):
            return subprocess.CompletedProcess(argv, 0, "List of devices attached\nABC123\tdevice product:p model:m\n", "")
        if argv[:3] == ["/x/xcrun", "xctrace", "list"]:
            return subprocess.CompletedProcess(argv, 0, "== Devices ==\niPhone (17.0) (UDID)\n", "")
        return subprocess.CompletedProcess(argv, 0, "", "")
    receipt = probe_native_resources(
        app_commit=COMMIT,
        environ={"ANDROID_HOME": "/sdk"},
        which=which,
        runner=runner,
        system="Darwin",
        machine="arm64",
    )
    assert receipt.android.state == "READY"
    assert receipt.android.observed_devices == ("ABC123",)
    assert receipt.apple.state == "READY"
    assert receipt.apple.observed_devices == ("iPhone (17.0) (UDID)",)


def test_invalid_exact_commit_rejected():
    with pytest.raises(NativeProbeError):
        probe_native_resources(app_commit="main", environ={}, which=lambda _: None)


def test_native_build_receipt_requires_exact_subject_toolchain_and_artifact_digest():
    good = {
        "schema": "ai-edge-tlm/p8-native-build-receipt/v1",
        "app_commit": COMMIT,
        "lane": "ANDROID_GRADLE",
        "state": "PASS",
        "toolchain": {"host_os": "Linux", "tool": "gradle", "version": "9.5.0"},
        "command": ["./gradlew", ":app:assembleDebug"],
        "artifact": {"path": "app-debug.apk", "sha256": "a" * 64},
    }
    validate_native_build_receipt(good, expected_commit=COMMIT, expected_lane="ANDROID_GRADLE")
    bad = dict(good); bad["app_commit"] = "1" * 40
    with pytest.raises(NativeProbeError):
        validate_native_build_receipt(bad, expected_commit=COMMIT, expected_lane="ANDROID_GRADLE")


def test_device_handoff_files_do_not_claim_native_pass():
    root = Path(__file__).resolve().parents[2]
    text = (root / "apps/convergence/handoff/README.md").read_text(encoding="utf-8")
    assert "BLOCKED_RESOURCE" in text
    assert "never inferred as PASS" in text
