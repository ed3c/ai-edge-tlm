import io.ed3c.aiedge.contracts.v1.*

fun main() {
    val model = ModelArtifactRef(
        model_id = "example.function-model",
        revision = "v1",
        sha256 = "c".repeat(64),
        format = ArtifactFormat.LITERTLM,
        quantization = "int4",
        tokenizer_sha256 = "d".repeat(64),
        license_plane = LicensePlane.MODEL_WEIGHTS,
        terms_state = TermsState.HUMAN_ADMIT_REQUIRED,
    )
    val request = InferenceRequest(
        schema = "ai-edge-tlm/inference-request/v1",
        request_id = "req-001",
        trace_id = "trace-001",
        task_id = "calendar-create",
        task_kind = TaskKind.FUNCTION_CALLING,
        messages = listOf(Message(role = MessageRole.USER, content = "Create an event tomorrow at 9 AM.")),
        capability_profile = CapabilityProfile(
            platform = PlatformKind.ANDROID,
            os_version = "16",
            device_model = "example-device",
            available_memory_mb = 4096,
            supports_system_model = true,
            supported_backends = listOf(BackendKind.CPU, BackendKind.GPU),
            supported_modalities = listOf(Modality.TEXT),
            max_active_sessions = 2,
        ),
        resource_budget = ResourceBudget(
            max_input_tokens = 1024,
            max_output_tokens = 256,
            timeout_ms = 5000,
            max_memory_mb = 512,
            allow_network = false,
        ),
        preferred_provider_ids = listOf("android.litert"),
        model_ref = model,
    )
    print(CanonicalJson.encode(request))
}
