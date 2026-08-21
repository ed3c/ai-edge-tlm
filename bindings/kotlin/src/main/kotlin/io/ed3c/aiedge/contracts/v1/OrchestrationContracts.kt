package io.ed3c.aiedge.contracts.v1

data class ExecutionPlan(
    val schema: String,
    val plan_id: String,
    val request_id: String,
    val nodes: List<PlanNode>,
    val fallback_edges: List<FallbackEdge>,
    val max_parallelism: Long,
    val max_steps: Long
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["schema"] = schema
        out["plan_id"] = plan_id
        out["request_id"] = request_id
        out["nodes"] = nodes.map { item -> item.toWireValue() }
        out["fallback_edges"] = fallback_edges.map { item -> item.toWireValue() }
        out["max_parallelism"] = max_parallelism
        out["max_steps"] = max_steps
        return out
    }
}

data class FallbackEdge(
    val from_node: String,
    val on_codes: List<ErrorCode>,
    val to_node: String
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["from_node"] = from_node
        out["on_codes"] = on_codes.map { item -> item.wireValue }
        out["to_node"] = to_node
        return out
    }
}

data class PlanNode(
    val node_id: String,
    val operation: String,
    val input_from: List<String>,
    val provider_requirements: List<ProviderKind>,
    val tool_name: String? = null,
    val effect: ToolEffect,
    val timeout_ms: Long,
    val retry: RetryPolicy,
    val output_schema_uri: String
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["node_id"] = node_id
        out["operation"] = operation
        out["input_from"] = input_from.map { item -> item }
        out["provider_requirements"] = provider_requirements.map { item -> item.wireValue }
        tool_name?.let { value -> out["tool_name"] = value }
        out["effect"] = effect.wireValue
        out["timeout_ms"] = timeout_ms
        out["retry"] = retry.toWireValue()
        out["output_schema_uri"] = output_schema_uri
        return out
    }
}

data class ProviderSelectionDecision(
    val request_id: String,
    val selected_provider_id: String,
    val fallback_provider_ids: List<String>,
    val rationale: String,
    val observed_backends: List<BackendKind>
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["request_id"] = request_id
        out["selected_provider_id"] = selected_provider_id
        out["fallback_provider_ids"] = fallback_provider_ids.map { item -> item }
        out["rationale"] = rationale
        out["observed_backends"] = observed_backends.map { item -> item.wireValue }
        return out
    }
}

data class RetryPolicy(
    val max_attempts: Long,
    val base_delay_ms: Long,
    val max_delay_ms: Long,
    val jitter: Boolean
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["max_attempts"] = max_attempts
        out["base_delay_ms"] = base_delay_ms
        out["max_delay_ms"] = max_delay_ms
        out["jitter"] = jitter
        return out
    }
}
