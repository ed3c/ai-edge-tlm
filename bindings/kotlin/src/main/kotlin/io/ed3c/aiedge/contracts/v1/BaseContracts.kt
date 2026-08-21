package io.ed3c.aiedge.contracts.v1

data class CapabilityProfile(
    val platform: PlatformKind,
    val os_version: String,
    val device_model: String,
    val available_memory_mb: Long,
    val supports_system_model: Boolean,
    val supported_backends: List<BackendKind>,
    val supported_modalities: List<Modality>,
    val max_active_sessions: Long
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["platform"] = platform.wireValue
        out["os_version"] = os_version
        out["device_model"] = device_model
        out["available_memory_mb"] = available_memory_mb
        out["supports_system_model"] = supports_system_model
        out["supported_backends"] = supported_backends.map { item -> item.wireValue }
        out["supported_modalities"] = supported_modalities.map { item -> item.wireValue }
        out["max_active_sessions"] = max_active_sessions
        return out
    }
}

data class Message(
    val role: MessageRole,
    val content: String,
    val name: String? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["role"] = role.wireValue
        out["content"] = content
        name?.let { value -> out["name"] = value }
        return out
    }
}

data class ModelArtifactRef(
    val model_id: String,
    val revision: String,
    val sha256: String,
    val format: ArtifactFormat,
    val quantization: String? = null,
    val tokenizer_sha256: String? = null,
    val license_plane: LicensePlane,
    val terms_state: TermsState
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["model_id"] = model_id
        out["revision"] = revision
        out["sha256"] = sha256
        out["format"] = format.wireValue
        quantization?.let { value -> out["quantization"] = value }
        tokenizer_sha256?.let { value -> out["tokenizer_sha256"] = value }
        out["license_plane"] = license_plane.wireValue
        out["terms_state"] = terms_state.wireValue
        return out
    }
}

data class ProviderDescriptor(
    val provider_id: String,
    val kind: ProviderKind,
    val maturity: ApiMaturity,
    val task_kinds: List<TaskKind>,
    val supported_backends: List<BackendKind>,
    val requires_network: Boolean,
    val terms_state: TermsState
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["provider_id"] = provider_id
        out["kind"] = kind.wireValue
        out["maturity"] = maturity.wireValue
        out["task_kinds"] = task_kinds.map { item -> item.wireValue }
        out["supported_backends"] = supported_backends.map { item -> item.wireValue }
        out["requires_network"] = requires_network
        out["terms_state"] = terms_state.wireValue
        return out
    }
}

data class ResourceBudget(
    val max_input_tokens: Long,
    val max_output_tokens: Long,
    val timeout_ms: Long,
    val max_memory_mb: Long,
    val allow_network: Boolean
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["max_input_tokens"] = max_input_tokens
        out["max_output_tokens"] = max_output_tokens
        out["timeout_ms"] = timeout_ms
        out["max_memory_mb"] = max_memory_mb
        out["allow_network"] = allow_network
        return out
    }
}

data class SubjectRef(
    val repository: String,
    val commit_sha: String,
    val tree_sha: String? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["repository"] = repository
        out["commit_sha"] = commit_sha
        tree_sha?.let { value -> out["tree_sha"] = value }
        return out
    }
}
