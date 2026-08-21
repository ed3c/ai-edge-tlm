import Foundation

/// Host-owned bounded execution DAG.
public struct ExecutionPlan: Codable, Equatable, Sendable {
    public let schema: String
    public let plan_id: String
    public let request_id: String
    public let nodes: [PlanNode]
    public let fallback_edges: [FallbackEdge]
    public let max_parallelism: Int64
    public let max_steps: Int64

    public init(
        schema: String,
        plan_id: String,
        request_id: String,
        nodes: [PlanNode],
        fallback_edges: [FallbackEdge],
        max_parallelism: Int64,
        max_steps: Int64
    ) {
        self.schema = schema
        self.plan_id = plan_id
        self.request_id = request_id
        self.nodes = nodes
        self.fallback_edges = fallback_edges
        self.max_parallelism = max_parallelism
        self.max_steps = max_steps
    }
}

/// Explicit failure edge; silent fallback is forbidden.
public struct FallbackEdge: Codable, Equatable, Sendable {
    public let from_node: String
    public let on_codes: [ErrorCode]
    public let to_node: String

    public init(
        from_node: String,
        on_codes: [ErrorCode],
        to_node: String
    ) {
        self.from_node = from_node
        self.on_codes = on_codes
        self.to_node = to_node
    }
}

/// One bounded DAG operation.
public struct PlanNode: Codable, Equatable, Sendable {
    public let node_id: String
    public let operation: String
    public let input_from: [String]
    public let provider_requirements: [ProviderKind]
    public let tool_name: String?
    public let effect: ToolEffect
    public let timeout_ms: Int64
    public let retry: RetryPolicy
    public let output_schema_uri: String

    public init(
        node_id: String,
        operation: String,
        input_from: [String],
        provider_requirements: [ProviderKind],
        tool_name: String? = nil,
        effect: ToolEffect,
        timeout_ms: Int64,
        retry: RetryPolicy,
        output_schema_uri: String
    ) {
        self.node_id = node_id
        self.operation = operation
        self.input_from = input_from
        self.provider_requirements = provider_requirements
        self.tool_name = tool_name
        self.effect = effect
        self.timeout_ms = timeout_ms
        self.retry = retry
        self.output_schema_uri = output_schema_uri
    }
}

/// Deterministic provider selection receipt.
public struct ProviderSelectionDecision: Codable, Equatable, Sendable {
    public let request_id: String
    public let selected_provider_id: String
    public let fallback_provider_ids: [String]
    public let rationale: String
    public let observed_backends: [BackendKind]

    public init(
        request_id: String,
        selected_provider_id: String,
        fallback_provider_ids: [String],
        rationale: String,
        observed_backends: [BackendKind]
    ) {
        self.request_id = request_id
        self.selected_provider_id = selected_provider_id
        self.fallback_provider_ids = fallback_provider_ids
        self.rationale = rationale
        self.observed_backends = observed_backends
    }
}

/// Bounded host retry policy.
public struct RetryPolicy: Codable, Equatable, Sendable {
    public let max_attempts: Int64
    public let base_delay_ms: Int64
    public let max_delay_ms: Int64
    public let jitter: Bool

    public init(
        max_attempts: Int64,
        base_delay_ms: Int64,
        max_delay_ms: Int64,
        jitter: Bool
    ) {
        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.jitter = jitter
    }
}
