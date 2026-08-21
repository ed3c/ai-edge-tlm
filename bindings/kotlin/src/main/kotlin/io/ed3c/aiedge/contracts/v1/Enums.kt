package io.ed3c.aiedge.contracts.v1

enum class ApiMaturity(val wireValue: String) {
    STABLE("STABLE"),
    PREVIEW("PREVIEW"),
    BETA("BETA"),
    COMMUNITY("COMMUNITY"),
    DISABLED("DISABLED");

    companion object { fun fromWire(value: String): ApiMaturity = entries.first { it.wireValue == value } }
}

enum class ArtifactFormat(val wireValue: String) {
    LITERTLM("LITERTLM"),
    TASK("TASK"),
    COREML_PACKAGE("COREML_PACKAGE"),
    ONNX("ONNX"),
    OTHER("OTHER");

    companion object { fun fromWire(value: String): ArtifactFormat = entries.first { it.wireValue == value } }
}

enum class BackendKind(val wireValue: String) {
    CPU("CPU"),
    GPU("GPU"),
    NPU("NPU"),
    ANE("ANE"),
    NNAPI("NNAPI"),
    METAL("METAL"),
    WEBGPU("WEBGPU"),
    UNKNOWN("UNKNOWN");

    companion object { fun fromWire(value: String): BackendKind = entries.first { it.wireValue == value } }
}

enum class ErrorCode(val wireValue: String) {
    CAPABILITY_UNAVAILABLE("CAPABILITY_UNAVAILABLE"),
    POLICY_DENIED("POLICY_DENIED"),
    ARTIFACT_INVALID("ARTIFACT_INVALID"),
    MODEL_LOAD_FAILED("MODEL_LOAD_FAILED"),
    GENERATION_FAILED("GENERATION_FAILED"),
    SCHEMA_INVALID("SCHEMA_INVALID"),
    TOOL_DENIED("TOOL_DENIED"),
    TOOL_FAILED("TOOL_FAILED"),
    VALIDATION_FAILED("VALIDATION_FAILED"),
    TIMEOUT("TIMEOUT"),
    RESOURCE_EXHAUSTED("RESOURCE_EXHAUSTED"),
    CANCELLED("CANCELLED"),
    EXHAUSTED_FALLBACK("EXHAUSTED_FALLBACK"),
    INTERNAL("INTERNAL");

    companion object { fun fromWire(value: String): ErrorCode = entries.first { it.wireValue == value } }
}

enum class EvidenceLane(val wireValue: String) {
    SOURCE("SOURCE"),
    STATIC("STATIC"),
    LOCAL("LOCAL"),
    LIVE_DEVICE("LIVE_DEVICE"),
    PRIVATE("PRIVATE"),
    HUMAN("HUMAN");

    companion object { fun fromWire(value: String): EvidenceLane = entries.first { it.wireValue == value } }
}

enum class EvidenceState(val wireValue: String) {
    PASS("PASS"),
    FAIL("FAIL"),
    ABSENT("ABSENT"),
    NOT_IMPLEMENTED("NOT_IMPLEMENTED"),
    NOT_EXERCISED("NOT_EXERCISED"),
    SKIPPED_BY_POLICY("SKIPPED_BY_POLICY"),
    HUMAN_ADMIT_REQUIRED("HUMAN_ADMIT_REQUIRED");

    companion object { fun fromWire(value: String): EvidenceState = entries.first { it.wireValue == value } }
}

enum class InferenceEventType(val wireValue: String) {
    STARTED("STARTED"),
    TOKEN_DELTA("TOKEN_DELTA"),
    TOOL_PROPOSAL("TOOL_PROPOSAL"),
    TOOL_RESULT("TOOL_RESULT"),
    COMPLETED("COMPLETED"),
    DEGRADED("DEGRADED"),
    FAILED("FAILED"),
    CANCELLED("CANCELLED");

    companion object { fun fromWire(value: String): InferenceEventType = entries.first { it.wireValue == value } }
}

enum class LicensePlane(val wireValue: String) {
    SOURCE_CODE("SOURCE_CODE"),
    MODEL_WEIGHTS("MODEL_WEIGHTS"),
    DATASET("DATASET"),
    SERVICE("SERVICE"),
    SDK_STORE("SDK_STORE"),
    TRADEMARK("TRADEMARK"),
    EXPORT_CONTROL("EXPORT_CONTROL"),
    UNKNOWN("UNKNOWN");

    companion object { fun fromWire(value: String): LicensePlane = entries.first { it.wireValue == value } }
}

enum class MessageRole(val wireValue: String) {
    SYSTEM("SYSTEM"),
    USER("USER"),
    ASSISTANT("ASSISTANT"),
    TOOL("TOOL");

    companion object { fun fromWire(value: String): MessageRole = entries.first { it.wireValue == value } }
}

enum class Modality(val wireValue: String) {
    TEXT("TEXT"),
    IMAGE("IMAGE"),
    AUDIO("AUDIO");

    companion object { fun fromWire(value: String): Modality = entries.first { it.wireValue == value } }
}

enum class PlatformKind(val wireValue: String) {
    ANDROID("ANDROID"),
    IOS("IOS"),
    MACOS("MACOS"),
    LINUX("LINUX"),
    WINDOWS("WINDOWS"),
    WEB("WEB"),
    EMBEDDED("EMBEDDED");

    companion object { fun fromWire(value: String): PlatformKind = entries.first { it.wireValue == value } }
}

enum class ProviderKind(val wireValue: String) {
    SYSTEM_MODEL("SYSTEM_MODEL"),
    EMBEDDED_MODEL("EMBEDDED_MODEL"),
    CLOUD("CLOUD");

    companion object { fun fromWire(value: String): ProviderKind = entries.first { it.wireValue == value } }
}

enum class ResultState(val wireValue: String) {
    SUCCEEDED("SUCCEEDED"),
    FAILED("FAILED"),
    CANCELLED("CANCELLED");

    companion object { fun fromWire(value: String): ResultState = entries.first { it.wireValue == value } }
}

enum class SkillTrustState(val wireValue: String) {
    TRUSTED("TRUSTED"),
    UNTRUSTED("UNTRUSTED"),
    REJECTED("REJECTED");

    companion object { fun fromWire(value: String): SkillTrustState = entries.first { it.wireValue == value } }
}

enum class TaskKind(val wireValue: String) {
    CHAT("CHAT"),
    SUMMARIZE("SUMMARIZE"),
    STRUCTURED_GENERATION("STRUCTURED_GENERATION"),
    FUNCTION_CALLING("FUNCTION_CALLING"),
    VISION("VISION"),
    ASR("ASR"),
    TEXT_POLISHING("TEXT_POLISHING"),
    EMBEDDING("EMBEDDING"),
    CUSTOM("CUSTOM");

    companion object { fun fromWire(value: String): TaskKind = entries.first { it.wireValue == value } }
}

enum class TermsState(val wireValue: String) {
    NOT_REQUIRED("NOT_REQUIRED"),
    REVIEW_REQUIRED("REVIEW_REQUIRED"),
    HUMAN_ADMIT_REQUIRED("HUMAN_ADMIT_REQUIRED"),
    ACCEPTED("ACCEPTED"),
    REJECTED("REJECTED");

    companion object { fun fromWire(value: String): TermsState = entries.first { it.wireValue == value } }
}

enum class ToolDecision(val wireValue: String) {
    ALLOW("ALLOW"),
    DENY("DENY"),
    REQUIRE_CONFIRMATION("REQUIRE_CONFIRMATION");

    companion object { fun fromWire(value: String): ToolDecision = entries.first { it.wireValue == value } }
}

enum class ToolEffect(val wireValue: String) {
    PURE("PURE"),
    READ_LOCAL("READ_LOCAL"),
    WRITE_LOCAL("WRITE_LOCAL"),
    EXTERNAL_SIDE_EFFECT("EXTERNAL_SIDE_EFFECT");

    companion object { fun fromWire(value: String): ToolEffect = entries.first { it.wireValue == value } }
}
