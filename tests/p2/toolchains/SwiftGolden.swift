import Foundation

@main
struct Golden {
    static func main() throws {
        let model = ModelArtifactRef(
            model_id: "example.function-model",
            revision: "v1",
            sha256: String(repeating: "c", count: 64),
            format: .litertlm,
            quantization: "int4",
            tokenizer_sha256: String(repeating: "d", count: 64),
            license_plane: .modelWeights,
            terms_state: .humanAdmitRequired
        )
        let request = InferenceRequest(
            schema: "ai-edge-tlm/inference-request/v1",
            request_id: "req-001",
            trace_id: "trace-001",
            task_id: "calendar-create",
            task_kind: .functionCalling,
            messages: [Message(role: .user, content: "Create an event tomorrow at 9 AM.")],
            capability_profile: CapabilityProfile(
                platform: .android,
                os_version: "16",
                device_model: "example-device",
                available_memory_mb: 4096,
                supports_system_model: true,
                supported_backends: [.cpu, .gpu],
                supported_modalities: [.text],
                max_active_sessions: 2
            ),
            resource_budget: ResourceBudget(
                max_input_tokens: 1024,
                max_output_tokens: 256,
                timeout_ms: 5000,
                max_memory_mb: 512,
                allow_network: false
            ),
            preferred_provider_ids: ["android.litert"],
            model_ref: model
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let data = try encoder.encode(request)
        FileHandle.standardOutput.write(data)
    }
}
