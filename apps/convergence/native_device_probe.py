from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Mapping


class NativeProbeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CommandProbe:
    name: str
    path: str | None
    state: str


@dataclass(frozen=True, slots=True)
class LaneProbe:
    lane: str
    state: str
    blockers: tuple[str, ...]
    commands: tuple[CommandProbe, ...]
    environment: Mapping[str, str]
    observed_devices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NativeResourceReceipt:
    schema: str
    app_commit: str
    host_os: str
    host_arch: str
    android: LaneProbe
    apple: LaneProbe

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _which(name: str, which: Callable[[str], str | None]) -> CommandProbe:
    path = which(name)
    return CommandProbe(name=name, path=path, state="PRESENT" if path else "MISSING")


def _run(argv: list[str], runner: Callable[..., subprocess.CompletedProcess[str]]) -> subprocess.CompletedProcess[str]:
    return runner(argv, check=False, capture_output=True, text=True, timeout=20)


def _adb_devices(adb: str | None, runner: Callable[..., subprocess.CompletedProcess[str]]) -> tuple[str, ...]:
    if not adb:
        return ()
    result = _run([adb, "devices", "-l"], runner)
    if result.returncode != 0:
        return ()
    devices: list[str] = []
    for raw in result.stdout.splitlines()[1:]:
        line = raw.strip()
        if not line or "\tdevice" not in line:
            continue
        devices.append(line.split()[0])
    return tuple(sorted(devices))


def _apple_devices(xcrun: str | None, runner: Callable[..., subprocess.CompletedProcess[str]]) -> tuple[str, ...]:
    if not xcrun:
        return ()
    result = _run([xcrun, "xctrace", "list", "devices"], runner)
    if result.returncode != 0:
        return ()
    values = []
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if line and "(" in line and ")" in line and not line.startswith("=="):
            values.append(line)
    return tuple(values)


def probe_native_resources(
    *,
    app_commit: str,
    environ: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    system: str | None = None,
    machine: str | None = None,
) -> NativeResourceReceipt:
    if len(app_commit) != 40 or any(ch not in "0123456789abcdef" for ch in app_commit):
        raise NativeProbeError("exact app commit must be a lowercase SHA-40")

    env = dict(os.environ if environ is None else environ)
    host_os = system or platform.system()
    host_arch = machine or platform.machine()

    adb = _which("adb", which)
    sdkmanager = _which("sdkmanager", which)
    gradle = _which("gradle", which)
    java = _which("java", which)
    android_home = env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT") or ""
    android_blockers: list[str] = []
    if not android_home:
        android_blockers.append("ANDROID_SDK_HOME_MISSING")
    if not adb.path:
        android_blockers.append("ADB_MISSING")
    if not sdkmanager.path:
        android_blockers.append("SDKMANAGER_MISSING")
    if not gradle.path:
        android_blockers.append("GRADLE_MISSING")
    if not java.path:
        android_blockers.append("JAVA_MISSING")
    android_devices = _adb_devices(adb.path, runner)
    if not android_devices:
        android_blockers.append("ANDROID_DEVICE_MISSING")
    android_state = "READY" if not android_blockers else "BLOCKED_RESOURCE"

    xcodebuild = _which("xcodebuild", which)
    xcrun = _which("xcrun", which)
    apple_blockers: list[str] = []
    if host_os != "Darwin":
        apple_blockers.append("MACOS_HOST_REQUIRED")
    if not xcodebuild.path:
        apple_blockers.append("XCODEBUILD_MISSING")
    if not xcrun.path:
        apple_blockers.append("XCRUN_MISSING")
    apple_devices = _apple_devices(xcrun.path, runner)
    if not apple_devices:
        apple_blockers.append("APPLE_DEVICE_MISSING")
    apple_state = "READY" if not apple_blockers else "BLOCKED_RESOURCE"

    return NativeResourceReceipt(
        schema="ai-edge-tlm/p8-native-resource-receipt/v1",
        app_commit=app_commit,
        host_os=host_os,
        host_arch=host_arch,
        android=LaneProbe(
            lane="ANDROID_GRADLE_LIVE_DEVICE",
            state=android_state,
            blockers=tuple(android_blockers),
            commands=(java, gradle, sdkmanager, adb),
            environment={"ANDROID_HOME": env.get("ANDROID_HOME", ""), "ANDROID_SDK_ROOT": env.get("ANDROID_SDK_ROOT", "")},
            observed_devices=android_devices,
        ),
        apple=LaneProbe(
            lane="XCODE_IOS_LIVE_DEVICE",
            state=apple_state,
            blockers=tuple(apple_blockers),
            commands=(xcodebuild, xcrun),
            environment={},
            observed_devices=apple_devices,
        ),
    )


def validate_native_build_receipt(value: Mapping[str, object], *, expected_commit: str, expected_lane: str) -> None:
    if value.get("schema") != "ai-edge-tlm/p8-native-build-receipt/v1":
        raise NativeProbeError("wrong native build receipt schema")
    if value.get("app_commit") != expected_commit:
        raise NativeProbeError("native build receipt subject drift")
    if value.get("lane") != expected_lane:
        raise NativeProbeError("wrong evidence lane")
    if value.get("state") != "PASS":
        raise NativeProbeError("native build receipt is not PASS")
    toolchain = value.get("toolchain")
    if not isinstance(toolchain, Mapping):
        raise NativeProbeError("toolchain identity missing")
    for key in ("host_os", "tool", "version"):
        if not isinstance(toolchain.get(key), str) or not toolchain[key].strip():
            raise NativeProbeError(f"toolchain field missing: {key}")
    if not isinstance(value.get("command"), list) or not value["command"]:
        raise NativeProbeError("build command missing")
    artifact = value.get("artifact")
    if not isinstance(artifact, Mapping):
        raise NativeProbeError("build artifact identity missing")
    digest = artifact.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise NativeProbeError("build artifact digest missing")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    receipt = probe_native_resources(app_commit=args.app_commit)
    payload = json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
