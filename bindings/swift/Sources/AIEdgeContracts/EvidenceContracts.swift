import Foundation

/// Benchmark identity that separates requested and runtime-observed backends.
public struct BenchmarkReceipt: Codable, Equatable, Sendable {
    public let schema: String
    public let subject: SubjectRef
    public let model_ref: ModelArtifactRef
    public let device_model: String
    public let os_version: String
    public let requested_backend: BackendKind
    public let observed_backend: BackendKind
    public let runtime_id: String
    public let runtime_version: String
    public let input_tokens: Int64
    public let output_tokens: Int64
    public let ttft_ms: Double
    public let prefill_tokens_per_second: Double
    public let decode_tokens_per_second: Double
    public let peak_rss_mb: Double
    public let thermal_state: String
    public let evidence_lane: EvidenceLane
    public let state: EvidenceState
    public let notes: String?

    public init(
        schema: String,
        subject: SubjectRef,
        model_ref: ModelArtifactRef,
        device_model: String,
        os_version: String,
        requested_backend: BackendKind,
        observed_backend: BackendKind,
        runtime_id: String,
        runtime_version: String,
        input_tokens: Int64,
        output_tokens: Int64,
        ttft_ms: Double,
        prefill_tokens_per_second: Double,
        decode_tokens_per_second: Double,
        peak_rss_mb: Double,
        thermal_state: String,
        evidence_lane: EvidenceLane,
        state: EvidenceState,
        notes: String? = nil
    ) {
        self.schema = schema
        self.subject = subject
        self.model_ref = model_ref
        self.device_model = device_model
        self.os_version = os_version
        self.requested_backend = requested_backend
        self.observed_backend = observed_backend
        self.runtime_id = runtime_id
        self.runtime_version = runtime_version
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.ttft_ms = ttft_ms
        self.prefill_tokens_per_second = prefill_tokens_per_second
        self.decode_tokens_per_second = decode_tokens_per_second
        self.peak_rss_mb = peak_rss_mb
        self.thermal_state = thermal_state
        self.evidence_lane = evidence_lane
        self.state = state
        self.notes = notes
    }
}

/// One evidence-lane-scoped gate result.
public struct GateResult: Codable, Equatable, Sendable {
    public let gate_id: String
    public let state: EvidenceState
    public let evidence_lane: EvidenceLane
    public let exact_result: String
    public let proves: String
    public let does_not_prove: String

    public init(
        gate_id: String,
        state: EvidenceState,
        evidence_lane: EvidenceLane,
        exact_result: String,
        proves: String,
        does_not_prove: String
    ) {
        self.gate_id = gate_id
        self.state = state
        self.evidence_lane = evidence_lane
        self.exact_result = exact_result
        self.proves = proves
        self.does_not_prove = does_not_prove
    }
}

/// Context Capsule-independent public implementation handoff.
public struct HandoffReceipt: Codable, Equatable, Sendable {
    public let schema: String
    public let task_id: String
    public let subject: SubjectRef
    public let parent_subjects: [SubjectRef]
    public let changed_paths: [String]
    public let output_digests: [String: String]
    public let gates: [GateResult]
    public let next_authority: String

    public init(
        schema: String,
        task_id: String,
        subject: SubjectRef,
        parent_subjects: [SubjectRef],
        changed_paths: [String],
        output_digests: [String: String],
        gates: [GateResult],
        next_authority: String
    ) {
        self.schema = schema
        self.task_id = task_id
        self.subject = subject
        self.parent_subjects = parent_subjects
        self.changed_paths = changed_paths
        self.output_digests = output_digests
        self.gates = gates
        self.next_authority = next_authority
    }
}
