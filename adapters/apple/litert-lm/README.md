# Apple LiteRT-LM embedded adapter

The first slice keeps the upstream Swift API behind an explicit `PREVIEW` boundary. It uses a fake runtime on Swift/Linux to verify P4 artifact admission, CPU/GPU backend observation, streaming, cancellation, memory-pressure failure, and tool-proposal-only behavior.

Upstream `v0.14.0` is recorded with a release-integrity warning. The public package currently exposes iOS/macOS binary targets, but public reports describe tag/binary replacement and an Xcode 26.6 Swift wrapper mismatch. This repository therefore does not promote the Swift path to `STABLE` without a later exact Xcode/binary/device receipt.
