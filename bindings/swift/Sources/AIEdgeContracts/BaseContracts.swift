import Foundation

/// Observed device capabilities; requested capabilities are not proof of actual runtime selection.
public struct CapabilityProfile: Codable, Equatable, Sendable {
    public let platform: PlatformKind
    public let os_version: String
    public let device_model: String
    public let available_memory_mb: Int64
    public let supports_system_model: Bool
    public let supported_backends: [BackendKind]
    public let supported_modalities: [Modality]
    public let max_active_sessions: Int64

    public init(
        platform: PlatformKind,
        os_version: String,
        device_model: String,
        available_memory_mb: Int64,
        supports_system_model: Bool,
        supported_backends: [BackendKind],
        supported_modalities: [Modality],
        max_active_sessions: Int64
    ) {
        self.platform = platform
        self.os_version = os_version
        self.device_model = device_model
        self.available_memory_mb = available_memory_mb
        self.supports_system_model = supports_system_model
        self.supported_backends = supported_backends
        self.supported_modalities = supported_modalities
        self.max_active_sessions = max_active_sessions
    }
}

/// Provider-neutral message.
public struct Message: Codable, Equatable, Sendable {
    public let role: MessageRole
    public let content: String
    public let name: String?

    public init(
        role: MessageRole,
        content: String,
        name: String? = nil
    ) {
        self.role = role
        self.content = content
        self.name = name
    }
}

/// Content-addressed model identity; source-code license and model terms remain separate.
public struct ModelArtifactRef: Codable, Equatable, Sendable {
    public let model_id: String
    public let revision: String
    public let sha256: String
    public let format: ArtifactFormat
    public let quantization: String?
    public let tokenizer_sha256: String?
    public let license_plane: LicensePlane
    public let terms_state: TermsState

    public init(
        model_id: String,
        revision: String,
        sha256: String,
        format: ArtifactFormat,
        quantization: String? = nil,
        tokenizer_sha256: String? = nil,
        license_plane: LicensePlane,
        terms_state: TermsState
    ) {
        self.model_id = model_id
        self.revision = revision
        self.sha256 = sha256
        self.format = format
        self.quantization = quantization
        self.tokenizer_sha256 = tokenizer_sha256
        self.license_plane = license_plane
        self.terms_state = terms_state
    }
}

/// Provider-neutral routing descriptor; contains no SDK types.
public struct ProviderDescriptor: Codable, Equatable, Sendable {
    public let provider_id: String
    public let kind: ProviderKind
    public let maturity: ApiMaturity
    public let task_kinds: [TaskKind]
    public let supported_backends: [BackendKind]
    public let requires_network: Bool
    public let terms_state: TermsState

    public init(
        provider_id: String,
        kind: ProviderKind,
        maturity: ApiMaturity,
        task_kinds: [TaskKind],
        supported_backends: [BackendKind],
        requires_network: Bool,
        terms_state: TermsState
    ) {
        self.provider_id = provider_id
        self.kind = kind
        self.maturity = maturity
        self.task_kinds = task_kinds
        self.supported_backends = supported_backends
        self.requires_network = requires_network
        self.terms_state = terms_state
    }
}

/// Host-owned bounded resource envelope.
public struct ResourceBudget: Codable, Equatable, Sendable {
    public let max_input_tokens: Int64
    public let max_output_tokens: Int64
    public let timeout_ms: Int64
    public let max_memory_mb: Int64
    public let allow_network: Bool

    public init(
        max_input_tokens: Int64,
        max_output_tokens: Int64,
        timeout_ms: Int64,
        max_memory_mb: Int64,
        allow_network: Bool
    ) {
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.timeout_ms = timeout_ms
        self.max_memory_mb = max_memory_mb
        self.allow_network = allow_network
    }
}

/// Immutable Git subject used by every receipt.
public struct SubjectRef: Codable, Equatable, Sendable {
    public let repository: String
    public let commit_sha: String
    public let tree_sha: String?

    public init(
        repository: String,
        commit_sha: String,
        tree_sha: String? = nil
    ) {
        self.repository = repository
        self.commit_sha = commit_sha
        self.tree_sha = tree_sha
    }
}
