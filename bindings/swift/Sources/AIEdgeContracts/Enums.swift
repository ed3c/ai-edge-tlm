import Foundation

public enum ApiMaturity: String, Codable, Equatable, Sendable {
    case stable = "STABLE"
    case preview = "PREVIEW"
    case beta = "BETA"
    case community = "COMMUNITY"
    case disabled = "DISABLED"
}

public enum ArtifactFormat: String, Codable, Equatable, Sendable {
    case litertlm = "LITERTLM"
    case task = "TASK"
    case coremlPackage = "COREML_PACKAGE"
    case onnx = "ONNX"
    case other = "OTHER"
}

public enum BackendKind: String, Codable, Equatable, Sendable {
    case cpu = "CPU"
    case gpu = "GPU"
    case npu = "NPU"
    case ane = "ANE"
    case nnapi = "NNAPI"
    case metal = "METAL"
    case webgpu = "WEBGPU"
    case unknown = "UNKNOWN"
}

public enum ErrorCode: String, Codable, Equatable, Sendable {
    case capabilityUnavailable = "CAPABILITY_UNAVAILABLE"
    case policyDenied = "POLICY_DENIED"
    case artifactInvalid = "ARTIFACT_INVALID"
    case modelLoadFailed = "MODEL_LOAD_FAILED"
    case generationFailed = "GENERATION_FAILED"
    case schemaInvalid = "SCHEMA_INVALID"
    case toolDenied = "TOOL_DENIED"
    case toolFailed = "TOOL_FAILED"
    case validationFailed = "VALIDATION_FAILED"
    case timeout = "TIMEOUT"
    case resourceExhausted = "RESOURCE_EXHAUSTED"
    case cancelled = "CANCELLED"
    case exhaustedFallback = "EXHAUSTED_FALLBACK"
    case _internal = "INTERNAL"
}

public enum EvidenceLane: String, Codable, Equatable, Sendable {
    case source = "SOURCE"
    case _static = "STATIC"
    case local = "LOCAL"
    case liveDevice = "LIVE_DEVICE"
    case _private = "PRIVATE"
    case human = "HUMAN"
}

public enum EvidenceState: String, Codable, Equatable, Sendable {
    case pass = "PASS"
    case fail = "FAIL"
    case absent = "ABSENT"
    case notImplemented = "NOT_IMPLEMENTED"
    case notExercised = "NOT_EXERCISED"
    case skippedByPolicy = "SKIPPED_BY_POLICY"
    case humanAdmitRequired = "HUMAN_ADMIT_REQUIRED"
}

public enum InferenceEventType: String, Codable, Equatable, Sendable {
    case started = "STARTED"
    case tokenDelta = "TOKEN_DELTA"
    case toolProposal = "TOOL_PROPOSAL"
    case toolResult = "TOOL_RESULT"
    case completed = "COMPLETED"
    case degraded = "DEGRADED"
    case failed = "FAILED"
    case cancelled = "CANCELLED"
}

public enum LicensePlane: String, Codable, Equatable, Sendable {
    case sourceCode = "SOURCE_CODE"
    case modelWeights = "MODEL_WEIGHTS"
    case dataset = "DATASET"
    case service = "SERVICE"
    case sdkStore = "SDK_STORE"
    case trademark = "TRADEMARK"
    case exportControl = "EXPORT_CONTROL"
    case unknown = "UNKNOWN"
}

public enum MessageRole: String, Codable, Equatable, Sendable {
    case system = "SYSTEM"
    case user = "USER"
    case assistant = "ASSISTANT"
    case tool = "TOOL"
}

public enum Modality: String, Codable, Equatable, Sendable {
    case text = "TEXT"
    case image = "IMAGE"
    case audio = "AUDIO"
}

public enum PlatformKind: String, Codable, Equatable, Sendable {
    case android = "ANDROID"
    case ios = "IOS"
    case macos = "MACOS"
    case linux = "LINUX"
    case windows = "WINDOWS"
    case web = "WEB"
    case embedded = "EMBEDDED"
}

public enum ProviderKind: String, Codable, Equatable, Sendable {
    case systemModel = "SYSTEM_MODEL"
    case embeddedModel = "EMBEDDED_MODEL"
    case cloud = "CLOUD"
}

public enum ResultState: String, Codable, Equatable, Sendable {
    case succeeded = "SUCCEEDED"
    case failed = "FAILED"
    case cancelled = "CANCELLED"
}

public enum SkillTrustState: String, Codable, Equatable, Sendable {
    case trusted = "TRUSTED"
    case untrusted = "UNTRUSTED"
    case rejected = "REJECTED"
}

public enum TaskKind: String, Codable, Equatable, Sendable {
    case chat = "CHAT"
    case summarize = "SUMMARIZE"
    case structuredGeneration = "STRUCTURED_GENERATION"
    case functionCalling = "FUNCTION_CALLING"
    case vision = "VISION"
    case asr = "ASR"
    case textPolishing = "TEXT_POLISHING"
    case embedding = "EMBEDDING"
    case custom = "CUSTOM"
}

public enum TermsState: String, Codable, Equatable, Sendable {
    case notRequired = "NOT_REQUIRED"
    case reviewRequired = "REVIEW_REQUIRED"
    case humanAdmitRequired = "HUMAN_ADMIT_REQUIRED"
    case accepted = "ACCEPTED"
    case rejected = "REJECTED"
}

public enum ToolDecision: String, Codable, Equatable, Sendable {
    case allow = "ALLOW"
    case deny = "DENY"
    case requireConfirmation = "REQUIRE_CONFIRMATION"
}

public enum ToolEffect: String, Codable, Equatable, Sendable {
    case pure = "PURE"
    case readLocal = "READ_LOCAL"
    case writeLocal = "WRITE_LOCAL"
    case externalSideEffect = "EXTERNAL_SIDE_EFFECT"
}
