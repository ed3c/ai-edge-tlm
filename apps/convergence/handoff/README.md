# P8 Native / Device Handoff

This directory defines the fail-closed transition from the P8 STATIC/LOCAL receipt to native build and physical-device evidence.

## Android

Required before `ANDROID_GRADLE=PASS`:

1. JDK compatible with the pinned Android Gradle Plugin.
2. Android SDK and `sdkmanager` available through `ANDROID_HOME` or `ANDROID_SDK_ROOT`.
3. Gradle or a repository Gradle wrapper generated from the pinned toolchain.
4. A build command that produces an APK/AAB whose SHA-256 is recorded in a native-build receipt.

`LIVE_DEVICE` additionally requires an `adb devices -l` physical device and a device receipt containing the exact app commit, OS/device, provider/runtime/model/skill identities, and **runtime-observed** backend.

## Apple

Required before `XCODE_IOS=PASS`:

1. macOS host.
2. `xcodebuild` and `xcrun` from the pinned Xcode installation.
3. A build command targeting the explicit iOS SDK/destination and a SHA-256 identity for the produced artifact.

`LIVE_DEVICE` additionally requires a physical iPhone/iPad. Swift/Linux compilation remains LOCAL semantic evidence and is never promoted to Xcode/iOS evidence.

## Fail closed

Missing SDKs, Xcode, devices, model access, signing, or terms are `BLOCKED_RESOURCE` or `HUMAN_ADMIT_REQUIRED`; they are never inferred as PASS.
