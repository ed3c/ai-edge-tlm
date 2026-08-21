package io.ed3c.aiedge.contracts.v1

data class SkillRef(
    val skill_id: String,
    val version: String,
    val source_uri: String,
    val source_sha256: String,
    val manifest_sha256: String,
    val trust_state: SkillTrustState,
    val required_tools: List<String>
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["skill_id"] = skill_id
        out["version"] = version
        out["source_uri"] = source_uri
        out["source_sha256"] = source_sha256
        out["manifest_sha256"] = manifest_sha256
        out["trust_state"] = trust_state.wireValue
        out["required_tools"] = required_tools.map { item -> item }
        return out
    }
}

data class ToolAdmission(
    val proposal_id: String,
    val decision: ToolDecision,
    val policy_reason: String,
    val idempotency_key: String? = null,
    val admitted_effect: ToolEffect
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["proposal_id"] = proposal_id
        out["decision"] = decision.wireValue
        out["policy_reason"] = policy_reason
        idempotency_key?.let { value -> out["idempotency_key"] = value }
        out["admitted_effect"] = admitted_effect.wireValue
        return out
    }
}

data class ToolDefinition(
    val tool_name: String,
    val description: String,
    val input_schema_uri: String,
    val effect: ToolEffect,
    val requires_confirmation: Boolean,
    val idempotency_required: Boolean
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["tool_name"] = tool_name
        out["description"] = description
        out["input_schema_uri"] = input_schema_uri
        out["effect"] = effect.wireValue
        out["requires_confirmation"] = requires_confirmation
        out["idempotency_required"] = idempotency_required
        return out
    }
}

data class ToolProposal(
    val proposal_id: String,
    val tool_name: String,
    val arguments: Map<String, JsonValue>,
    val model_output_digest: String
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["proposal_id"] = proposal_id
        out["tool_name"] = tool_name
        out["arguments"] = arguments.mapValues { it.value.toWireValue() }
        out["model_output_digest"] = model_output_digest
        return out
    }
}
