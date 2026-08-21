package io.ed3c.aiedge.contracts.v1

data class BenchmarkReceipt(
    val schema: String,
    val subject: SubjectRef,
    val model_ref: ModelArtifactRef,
    val device_model: String,
    val os_version: String,
    val requested_backend: BackendKind,
    val observed_backend: BackendKind,
    val runtime_id: String,
    val runtime_version: String,
    val input_tokens: Long,
    val output_tokens: Long,
    val ttft_ms: Double,
    val prefill_tokens_per_second: Double,
    val decode_tokens_per_second: Double,
    val peak_rss_mb: Double,
    val thermal_state: String,
    val evidence_lane: EvidenceLane,
    val state: EvidenceState,
    val notes: String? = null
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["schema"] = schema
        out["subject"] = subject.toWireValue()
        out["model_ref"] = model_ref.toWireValue()
        out["device_model"] = device_model
        out["os_version"] = os_version
        out["requested_backend"] = requested_backend.wireValue
        out["observed_backend"] = observed_backend.wireValue
        out["runtime_id"] = runtime_id
        out["runtime_version"] = runtime_version
        out["input_tokens"] = input_tokens
        out["output_tokens"] = output_tokens
        out["ttft_ms"] = ttft_ms
        out["prefill_tokens_per_second"] = prefill_tokens_per_second
        out["decode_tokens_per_second"] = decode_tokens_per_second
        out["peak_rss_mb"] = peak_rss_mb
        out["thermal_state"] = thermal_state
        out["evidence_lane"] = evidence_lane.wireValue
        out["state"] = state.wireValue
        notes?.let { value -> out["notes"] = value }
        return out
    }
}

data class GateResult(
    val gate_id: String,
    val state: EvidenceState,
    val evidence_lane: EvidenceLane,
    val exact_result: String,
    val proves: String,
    val does_not_prove: String
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["gate_id"] = gate_id
        out["state"] = state.wireValue
        out["evidence_lane"] = evidence_lane.wireValue
        out["exact_result"] = exact_result
        out["proves"] = proves
        out["does_not_prove"] = does_not_prove
        return out
    }
}

data class HandoffReceipt(
    val schema: String,
    val task_id: String,
    val subject: SubjectRef,
    val parent_subjects: List<SubjectRef>,
    val changed_paths: List<String>,
    val output_digests: Map<String, String>,
    val gates: List<GateResult>,
    val next_authority: String
) : WireEncodable {
    override fun toWireValue(): Any? {
        val out = linkedMapOf<String, Any?>()
        out["schema"] = schema
        out["task_id"] = task_id
        out["subject"] = subject.toWireValue()
        out["parent_subjects"] = parent_subjects.map { item -> item.toWireValue() }
        out["changed_paths"] = changed_paths.map { item -> item }
        out["output_digests"] = output_digests
        out["gates"] = gates.map { item -> item.toWireValue() }
        out["next_authority"] = next_authority
        return out
    }
}
