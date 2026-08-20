# Third-party notices and admission status

This file is an engineering registry, not legal advice. Pin exact revisions and re-read direct license bytes before distribution.

| Component | Role | Source/code terms | Model/service terms | Default admission |
|---|---|---|---|---|
| Google LiteRT-LM | embedded LLM runtime | Apache-2.0 | model-specific | admitted for evaluation; pin version |
| Google LiteRT | lower-level runtime | Apache-2.0 | artifact-specific | admitted for evaluation; pin version |
| Google LiteRT Torch | conversion/build tooling | Apache-2.0; Generative API maturity varies | model-specific | build-time, version-gated |
| Google AI Edge Gallery | reference app and skill format | Apache-2.0 | downloaded models have separate terms | reference-only; do not vendor wholesale |
| FunctionGemma / Gemma weights | specialized/local model | n/a | Gemma Terms and Prohibited Use Policy; access acceptance may be required | manifest-only; no redistribution by default |
| Android ML Kit GenAI / AICore | system provider | platform SDK terms | additional API/service terms may apply | adapter only; product review required |
| Apple Foundation Models | system provider | Apple SDK terms | device/OS and Apple program terms | adapter only; product review required |
| Apple FastVLM | optional VLM experiment | Apple-specific code license | separate model license | REVIEW_REQUIRED |
| ONNX Runtime | optional fallback | MIT | model-specific | OPTIONAL |
| ExecuTorch | optional fallback | BSD-3-Clause | model-specific | OPTIONAL |
| llama.cpp | optional local reference | MIT | model-specific | OPTIONAL; not primary LiteRT-LM path |

The repository must not claim that a permissive code license settles model-weight, dataset, service, patent, trademark, export-control, privacy, or store-policy obligations.
