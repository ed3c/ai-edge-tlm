import Foundation

/// Typed error shared across provider boundaries.
public struct ErrorDetail: Codable, Equatable, Sendable {
    public let code: ErrorCode
    public let message: String
    public let retryable: Bool
    public let provider_id: String?
    public let details: [String: JSONValue]?

    public init(
        code: ErrorCode,
        message: String,
        retryable: Bool,
        provider_id: String? = nil,
        details: [String: JSONValue]? = nil
    ) {
        self.code = code
        self.message = message
        self.retryable = retryable
        self.provider_id = provider_id
        self.details = details
    }
}

/// Ordered streaming event envelope.
public struct InferenceEvent: Codable, Equatable, Sendable {
    public let schema: String
    public let request_id: String
    public let sequence: Int64
    public let type: InferenceEventType
    public let text_delta: String?
    public let tool_proposal: ToolProposal?
    public let tool_result: ToolResult?
    public let error: ErrorDetail?
    public let finish_reason: String?

    public init(
        schema: String,
        request_id: String,
        sequence: Int64,
        type: InferenceEventType,
        text_delta: String? = nil,
        tool_proposal: ToolProposal? = nil,
        tool_result: ToolResult? = nil,
        error: ErrorDetail? = nil,
        finish_reason: String? = nil
    ) {
        self.schema = schema
        self.request_id = request_id
        self.sequence = sequence
        self.type = type
        self.text_delta = text_delta
        self.tool_proposal = tool_proposal
        self.tool_result = tool_result
        self.error = error
        self.finish_reason = finish_reason
    }
}

/// Top-level inference request. Host policy evaluates it before provider selection.
public struct InferenceRequest: Codable, Equatable, Sendable {
    public let schema: String
    public let request_id: String
    public let trace_id: String
    public let task_id: String
    public let task_kind: TaskKind
    public let messages: [Message]
    public let capability_profile: CapabilityProfile
    public let resource_budget: ResourceBudget
    public let preferred_provider_ids: [String]?
    public let model_ref: ModelArtifactRef?

    public init(
        schema: String,
        request_id: String,
        trace_id: String,
        task_id: String,
        task_kind: TaskKind,
        messages: [Message],
        capability_profile: CapabilityProfile,
        resource_budget: ResourceBudget,
        preferred_provider_ids: [String]? = nil,
        model_ref: ModelArtifactRef? = nil
    ) {
        self.schema = schema
        self.request_id = request_id
        self.trace_id = trace_id
        self.task_id = task_id
        self.task_kind = task_kind
        self.messages = messages
        self.capability_profile = capability_profile
        self.resource_budget = resource_budget
        self.preferred_provider_ids = preferred_provider_ids
        self.model_ref = model_ref
    }
}

/// Validated tool outcome.
public struct ToolResult: Codable, Equatable, Sendable {
    public let proposal_id: String
    public let state: ResultState
    public let output: JSONValue?
    public let error: ErrorDetail?
    public let receipt_subject: SubjectRef?

    public init(
        proposal_id: String,
        state: ResultState,
        output: JSONValue? = nil,
        error: ErrorDetail? = nil,
        receipt_subject: SubjectRef? = nil
    ) {
        self.proposal_id = proposal_id
        self.state = state
        self.output = output
        self.error = error
        self.receipt_subject = receipt_subject
    }
}
