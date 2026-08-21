# Technology-selection closure

## Default technical route

| Component | Role | Current decision | Commercial boundary |
|---|---|---|---|
| LiteRT-LM | Embedded LLM runtime | Pin a stable release; Kotlin/C++ are preferred stable surfaces | Apache-2.0 code; model terms separate |
| LiteRT | Runtime/delegates | Admit per platform, model and actual delegate | Apache-2.0 code; transitive/vendor terms require review |
| litert-torch | Export/conversion | Pin toolchain and require conversion parity | Apache-2.0 code; output model terms separate |
| AI Edge Gallery | App/skill reference | Reuse patterns and adapters, not wholesale product coupling | Apache-2.0 code; remote skills have independent provenance |
| MediaPipe | Compatibility lane | Keep where the exact existing/non-LLM API requires it | Apache-2.0 code |
| FunctionGemma | Optional specialized TLM | Evaluate only after Gemma terms admission and task-specific SFT | Human terms acceptance required |
| FastVLM released weights | Research comparison | **Not a commercial default** | Official model license is research-only |
| ML Kit GenAI / AICore | Android system provider | Probe exact device, feature, model version, quota and foreground state | SDK/service/store terms review |
| Apple Foundation Models | Apple system provider | Probe exact OS/device/model capability and version prompts | Apple developer/store terms review |

## Hard corrections

- Do not represent FastVLM weights as an unrestricted commercial option.
- Do not infer iOS ANE/NPU execution from a generic cross-platform acceleration statement.
- Do not treat Swift LiteRT-LM as stable while the pinned README labels it Early Preview.
- Do not claim every MediaPipe `.task` LLM flow has already migrated.
- Do not copy talk benchmark values into local benchmark fields.
- Do not treat Apache-2.0 runtime code as permission to use model weights or services.
