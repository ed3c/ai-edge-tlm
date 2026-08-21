package io.ed3c.aiedge.contracts.v1

data class ErrorDetail(
    val code: ErrorCode,
    val message: String,
    val retryable: Boolean,
    val provider_id: String? = null,
    val details: Map<String, JsonValue>? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["code"] = code.wireValue
        out["message"] = message
        out["retryable"] = retryable
        provider_id?.let { value -> out["provider_id"] = value }
        details?.let { value -> out["details"] = value.mapValues { it.value.toWireValue() } }
        return out
    }
}

data class InferenceEvent(
    val schema: String,
    val request_id: String,
    val sequence: Long,
    val type: InferenceEventType,
    val text_delta: String? = null,
    val tool_proposal: ToolProposal? = null,
    val tool_result: ToolResult? = null,
    val error: ErrorDetail? = null,
    val finish_reason: String? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["schema"] = schema
        out["request_id"] = request_id
        out["sequence"] = sequence
        out["type"] = type.wireValue
        text_delta?.let { value -> out["text_delta"] = value }
        tool_proposal?.let { value -> out["tool_proposal"] = value.toWireValue() }
        tool_result?.let { value -> out["tool_result"] = value.toWireValue() }
        error?.let { value -> out["error"] = value.toWireValue() }
        finish_reason?.let { value -> out["finish_reason"] = value }
        return out
    }
}

data class InferenceRequest(
    val schema: String,
    val request_id: String,
    val trace_id: String,
    val task_id: String,
    val task_kind: TaskKind,
    val messages: List<Message>,
    val capability_profile: CapabilityProfile,
    val resource_budget: ResourceBudget,
    val preferred_provider_ids: List<String>? = null,
    val model_ref: ModelArtifactRef? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["schema"] = schema
        out["request_id"] = request_id
        out["trace_id"] = trace_id
        out["task_id"] = task_id
        out["task_kind"] = task_kind.wireValue
        out["messages"] = messages.map { item -> item.toWireValue() }
        out["capability_profile"] = capability_profile.toWireValue()
        out["resource_budget"] = resource_budget.toWireValue()
        preferred_provider_ids?.let { value -> out["preferred_provider_ids"] = value.map { item -> item } }
        model_ref?.let { value -> out["model_ref"] = value.toWireValue() }
        return out
    }
}

data class ToolResult(
    val proposal_id: String,
    val state: ResultState,
    val output: JsonValue? = null,
    val error: ErrorDetail? = null,
    val receipt_subject: SubjectRef? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["proposal_id"] = proposal_id
        out["state"] = state.wireValue
        output?.let { value -> out["output"] = value.toWireValue() }
        error?.let { value -> out["error"] = value.toWireValue() }
        receipt_subject?.let { value -> out["receipt_subject"] = value.toWireValue() }
        return out
    }
}
