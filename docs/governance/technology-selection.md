# Technology selection and commercial-use boundary

The admission target is permissive source code or platform APIs that do not force this repository or consuming apps to publish proprietary application source. Model, dataset, service, and store terms remain separate.

| Technology | Role | License/terms class | Decision |
|---|---|---|---|
| `google-ai-edge/LiteRT-LM` | primary embedded LLM runtime | Apache-2.0 source | ADOPT, exact pin |
| `google-ai-edge/LiteRT` | accelerator/runtime substrate | Apache-2.0 source | ADOPT transitively/as needed |
| `google-ai-edge/litert-torch` | model conversion | Apache-2.0 source; Generative API maturity-gated | ADOPT as build tool, pin nightly/stable explicitly |
| `google-ai-edge/gallery` | reference implementation and skill contract | Apache-2.0 source | REFERENCE; port patterns, do not fork product wholesale |
| FunctionGemma/Gemma weights | specialized TLM/SLM | Gemma terms; responsible commercial use; access acceptance | OPTIONAL/RECOMMENDED for suitable tasks; manifest-only |
| Android ML Kit GenAI/AICore | system SLM | Android/Google API and additional terms | ADAPTER; product/legal review |
| Apple Foundation Models | system SLM | Apple SDK/program terms | ADAPTER; supported-device gate |
| Apple FastVLM | optional VLM | custom code and model licenses | REVIEW_REQUIRED; not default |
| ONNX Runtime | optional fallback | MIT | OPTIONAL |
| ExecuTorch | optional fallback | BSD-3-Clause | OPTIONAL |
| llama.cpp | optional diagnostic/reference runtime | MIT | OPTIONAL; no format drift into core contracts |
| coremltools | Apple conversion tooling for non-LiteRT paths | BSD-3-Clause | OPTIONAL; separate provider path |

## Rules

1. Pin repository revision and direct license digest.
2. Generate or ingest SBOM before release.
3. Record NOTICE and attribution obligations.
4. Keep model weights outside this repository unless their redistribution rights are explicitly admitted.
5. Do not describe "commercially usable" as "zero legal risk."
6. Copyleft dependencies require a separate architecture and distribution review; they are not admitted by default.
