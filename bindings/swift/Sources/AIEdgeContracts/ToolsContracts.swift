import Foundation

/// Metadata-first immutable skill reference.
public struct SkillRef: Codable, Equatable, Sendable {
    public let skill_id: String
    public let version: String
    public let source_uri: String
    public let source_sha256: String
    public let manifest_sha256: String
    public let trust_state: SkillTrustState
    public let required_tools: [String]

    public init(
        skill_id: String,
        version: String,
        source_uri: String,
        source_sha256: String,
        manifest_sha256: String,
        trust_state: SkillTrustState,
        required_tools: [String]
    ) {
        self.skill_id = skill_id
        self.version = version
        self.source_uri = source_uri
        self.source_sha256 = source_sha256
        self.manifest_sha256 = manifest_sha256
        self.trust_state = trust_state
        self.required_tools = required_tools
    }
}

/// Host policy decision for a proposal.
public struct ToolAdmission: Codable, Equatable, Sendable {
    public let proposal_id: String
    public let decision: ToolDecision
    public let policy_reason: String
    public let idempotency_key: String?
    public let admitted_effect: ToolEffect

    public init(
        proposal_id: String,
        decision: ToolDecision,
        policy_reason: String,
        idempotency_key: String? = nil,
        admitted_effect: ToolEffect
    ) {
        self.proposal_id = proposal_id
        self.decision = decision
        self.policy_reason = policy_reason
        self.idempotency_key = idempotency_key
        self.admitted_effect = admitted_effect
    }
}

/// Tool contract exposed to a model; execution authority remains host-owned.
public struct ToolDefinition: Codable, Equatable, Sendable {
    public let tool_name: String
    public let description: String
    public let input_schema_uri: String
    public let effect: ToolEffect
    public let requires_confirmation: Bool
    public let idempotency_required: Bool

    public init(
        tool_name: String,
        description: String,
        input_schema_uri: String,
        effect: ToolEffect,
        requires_confirmation: Bool,
        idempotency_required: Bool
    ) {
        self.tool_name = tool_name
        self.description = description
        self.input_schema_uri = input_schema_uri
        self.effect = effect
        self.requires_confirmation = requires_confirmation
        self.idempotency_required = idempotency_required
    }
}

/// Candidate tool call emitted by a model, never an execution decision.
public struct ToolProposal: Codable, Equatable, Sendable {
    public let proposal_id: String
    public let tool_name: String
    public let arguments: [String: JSONValue]
    public let model_output_digest: String

    public init(
        proposal_id: String,
        tool_name: String,
        arguments: [String: JSONValue],
        model_output_digest: String
    ) {
        self.proposal_id = proposal_id
        self.tool_name = tool_name
        self.arguments = arguments
        self.model_output_digest = model_output_digest
    }
}
