package io.ed3c.aiedge.adapters.android.systemgenai

import io.ed3c.aiedge.contracts.v1.ApiMaturity
import io.ed3c.aiedge.contracts.v1.BackendKind
import io.ed3c.aiedge.contracts.v1.CapabilityProfile
import io.ed3c.aiedge.contracts.v1.ErrorCode
import io.ed3c.aiedge.contracts.v1.ErrorDetail
import io.ed3c.aiedge.contracts.v1.InferenceEvent
import io.ed3c.aiedge.contracts.v1.InferenceEventType
import io.ed3c.aiedge.contracts.v1.InferenceRequest
import io.ed3c.aiedge.contracts.v1.JsonString
import io.ed3c.aiedge.contracts.v1.Modality
import io.ed3c.aiedge.contracts.v1.PlatformKind
import io.ed3c.aiedge.contracts.v1.ProviderDescriptor
import io.ed3c.aiedge.contracts.v1.ProviderKind
import io.ed3c.aiedge.contracts.v1.TaskKind
import io.ed3c.aiedge.contracts.v1.TermsState
import io.ed3c.aiedge.contracts.v1.ToolProposal
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

enum class AvailabilityState { AVAILABLE, UNAVAILABLE, STALE }
enum class FallbackTarget { EMBEDDED_TLM, FAIL_CLOSED }

data class CapabilityRevision(
    val osVersion: String,
    val systemModelRevision: String,
    val sdkApiVersion: String
) {
    init {
        require(osVersion.isNotBlank())
        require(systemModelRevision.isNotBlank())
        require(sdkApiVersion.isNotBlank())
    }

    val key: String
        get() = listOf(osVersion, systemModelRevision, sdkApiVersion).joinToString("|")
}

data class AndroidSystemCapabilityObservation(
    val deviceModel: String,
    val availableMemoryMb: Long,
    val supportedBackends: List<BackendKind>,
    val supportedModalities: List<Modality>,
    val maxActiveSessions: Long,
    val availability: AvailabilityState,
    val revision: CapabilityRevision,
    val observedAtEpochMs: Long,
    val reason: String? = null
) {
    init {
        require(deviceModel.isNotBlank())
        require(availableMemoryMb >= 0)
        require(maxActiveSessions >= 0)
        require(observedAtEpochMs >= 0)
        if (availability != AvailabilityState.AVAILABLE) require(!reason.isNullOrBlank())
    }
}

data class AndroidSystemCapabilitySnapshot(
    val revisionKey: String,
    val observedAtEpochMs: Long,
    val availability: AvailabilityState,
    val capabilityProfile: CapabilityProfile,
    val providerDescriptor: ProviderDescriptor,
    val reason: String? = null
)

data class FallbackDecision(
    val target: FallbackTarget,
    val reason: String,
    val networkAllowed: Boolean = false
) {
    init {
        require(reason.isNotBlank())
        require(!networkAllowed) { "System adapter fallback cannot silently enable network" }
    }
}

data class AdapterExecution(
    val requestId: String,
    val traceId: String,
    val revisionKey: String?,
    val events: List<InferenceEvent>,
    val fallback: FallbackDecision?
)

class CancellationToken {
    private val cancelled = AtomicBoolean(false)
    fun cancel() { cancelled.set(true) }
    fun isCancelled(): Boolean = cancelled.get()
}

sealed interface ProviderChunk {
    data class Text(val value: String) : ProviderChunk
    data class ToolCandidate(
        val proposalId: String,
        val toolName: String,
        val arguments: Map<String, io.ed3c.aiedge.contracts.v1.JsonValue>,
        val rawModelOutput: String
    ) : ProviderChunk
    data class Failure(val message: String, val retryable: Boolean) : ProviderChunk
    data object Completed : ProviderChunk
}

fun interface AndroidSystemSession {
    fun stream(request: InferenceRequest): Sequence<ProviderChunk>
}

class CapabilityCache(private val maxAgeMs: Long) {
    private val snapshot = AtomicReference<AndroidSystemCapabilitySnapshot?>(null)

    init { require(maxAgeMs > 0) }

    fun put(value: AndroidSystemCapabilitySnapshot) { snapshot.set(value) }

    fun read(expectedRevisionKey: String, nowEpochMs: Long): AndroidSystemCapabilitySnapshot? {
        val current = snapshot.get() ?: return null
        if (current.revisionKey != expectedRevisionKey) return current.copy(
            availability = AvailabilityState.STALE,
            reason = "revision changed"
        )
        if (nowEpochMs < current.observedAtEpochMs || nowEpochMs - current.observedAtEpochMs > maxAgeMs) {
            return current.copy(availability = AvailabilityState.STALE, reason = "capability observation expired")
        }
        return current
    }
}

class AndroidSystemProviderAdapter(
    private val providerId: String = "android-system-genai",
    private val maturity: ApiMaturity = ApiMaturity.BETA,
    private val termsState: TermsState = TermsState.REVIEW_REQUIRED
) {
    init { require(providerId.isNotBlank()) }

    fun probe(observation: AndroidSystemCapabilityObservation): AndroidSystemCapabilitySnapshot {
        val supportsSystemModel = observation.availability == AvailabilityState.AVAILABLE
        val profile = CapabilityProfile(
            platform = PlatformKind.ANDROID,
            os_version = observation.revision.osVersion,
            device_model = observation.deviceModel,
            available_memory_mb = observation.availableMemoryMb,
            supports_system_model = supportsSystemModel,
            supported_backends = if (supportsSystemModel) observation.supportedBackends else emptyList(),
            supported_modalities = if (supportsSystemModel) observation.supportedModalities else emptyList(),
            max_active_sessions = if (supportsSystemModel) observation.maxActiveSessions else 0
        )
        val descriptor = ProviderDescriptor(
            provider_id = providerId,
            kind = ProviderKind.SYSTEM_MODEL,
            maturity = maturity,
            task_kinds = listOf(TaskKind.CHAT, TaskKind.SUMMARIZE, TaskKind.STRUCTURED_GENERATION, TaskKind.FUNCTION_CALLING),
            supported_backends = if (supportsSystemModel) observation.supportedBackends else emptyList(),
            requires_network = false,
            terms_state = termsState
        )
        return AndroidSystemCapabilitySnapshot(
            revisionKey = observation.revision.key,
            observedAtEpochMs = observation.observedAtEpochMs,
            availability = observation.availability,
            capabilityProfile = profile,
            providerDescriptor = descriptor,
            reason = observation.reason
        )
    }

    fun execute(
        request: InferenceRequest,
        snapshot: AndroidSystemCapabilitySnapshot,
        session: AndroidSystemSession,
        cancellation: CancellationToken = CancellationToken()
    ): AdapterExecution {
        require(request.request_id.isNotBlank())
        require(request.trace_id.isNotBlank())

        if (snapshot.availability != AvailabilityState.AVAILABLE || !snapshot.capabilityProfile.supports_system_model) {
            val message = snapshot.reason ?: "system model unavailable"
            return failedExecution(
                request = request,
                snapshot = snapshot,
                code = ErrorCode.CAPABILITY_UNAVAILABLE,
                message = message,
                retryable = true,
                fallback = FallbackDecision(FallbackTarget.EMBEDDED_TLM, message)
            )
        }

        if (cancellation.isCancelled()) {
            val cancelled = listOf(
                InferenceEvent(
                    schema = "ai-edge-tlm/inference-event/v1",
                    request_id = request.request_id,
                    sequence = 0,
                    type = InferenceEventType.STARTED
                ),
                InferenceEvent(
                    schema = "ai-edge-tlm/inference-event/v1",
                    request_id = request.request_id,
                    sequence = 1,
                    type = InferenceEventType.CANCELLED,
                    error = ErrorDetail(
                        code = ErrorCode.CANCELLED,
                        message = "request cancelled before provider execution",
                        retryable = false,
                        provider_id = providerId,
                        details = mapOf("trace_id" to JsonString(request.trace_id))
                    ),
                    finish_reason = "cancelled"
                )
            )
            return AdapterExecution(request.request_id, request.trace_id, snapshot.revisionKey, cancelled, null)
        }

        val events = mutableListOf(
            InferenceEvent(
                schema = "ai-edge-tlm/inference-event/v1",
                request_id = request.request_id,
                sequence = 0,
                type = InferenceEventType.STARTED
            )
        )
        var sequence = 1L
        var terminal = false

        try {
            for (chunk in session.stream(request)) {
                if (cancellation.isCancelled()) {
                    events += InferenceEvent(
                        schema = "ai-edge-tlm/inference-event/v1",
                        request_id = request.request_id,
                        sequence = sequence,
                        type = InferenceEventType.CANCELLED,
                        error = ErrorDetail(
                            code = ErrorCode.CANCELLED,
                            message = "request cancelled",
                            retryable = false,
                            provider_id = providerId,
                            details = mapOf("trace_id" to JsonString(request.trace_id))
                        ),
                        finish_reason = "cancelled"
                    )
                    terminal = true
                    break
                }
                when (chunk) {
                    is ProviderChunk.Text -> {
                        require(chunk.value.isNotEmpty()) { "empty text delta" }
                        events += InferenceEvent(
                            schema = "ai-edge-tlm/inference-event/v1",
                            request_id = request.request_id,
                            sequence = sequence++,
                            type = InferenceEventType.TOKEN_DELTA,
                            text_delta = chunk.value
                        )
                    }
                    is ProviderChunk.ToolCandidate -> {
                        val digest = sha256(chunk.rawModelOutput)
                        events += InferenceEvent(
                            schema = "ai-edge-tlm/inference-event/v1",
                            request_id = request.request_id,
                            sequence = sequence++,
                            type = InferenceEventType.TOOL_PROPOSAL,
                            tool_proposal = ToolProposal(
                                proposal_id = chunk.proposalId,
                                tool_name = chunk.toolName,
                                arguments = chunk.arguments,
                                model_output_digest = digest
                            )
                        )
                    }
                    is ProviderChunk.Failure -> {
                        events += InferenceEvent(
                            schema = "ai-edge-tlm/inference-event/v1",
                            request_id = request.request_id,
                            sequence = sequence,
                            type = InferenceEventType.FAILED,
                            error = ErrorDetail(
                                code = ErrorCode.GENERATION_FAILED,
                                message = chunk.message,
                                retryable = chunk.retryable,
                                provider_id = providerId,
                                details = mapOf("trace_id" to JsonString(request.trace_id))
                            ),
                            finish_reason = "provider_failure"
                        )
                        terminal = true
                    }
                    ProviderChunk.Completed -> {
                        events += InferenceEvent(
                            schema = "ai-edge-tlm/inference-event/v1",
                            request_id = request.request_id,
                            sequence = sequence,
                            type = InferenceEventType.COMPLETED,
                            finish_reason = "stop"
                        )
                        terminal = true
                    }
                }
                if (terminal) break
            }
        } catch (error: Exception) {
            events += InferenceEvent(
                schema = "ai-edge-tlm/inference-event/v1",
                request_id = request.request_id,
                sequence = sequence,
                type = InferenceEventType.FAILED,
                error = ErrorDetail(
                    code = ErrorCode.INTERNAL,
                    message = error.message ?: "system provider failure",
                    retryable = false,
                    provider_id = providerId,
                    details = mapOf("trace_id" to JsonString(request.trace_id))
                ),
                finish_reason = "adapter_exception"
            )
            terminal = true
        }

        if (!terminal) {
            events += InferenceEvent(
                schema = "ai-edge-tlm/inference-event/v1",
                request_id = request.request_id,
                sequence = sequence,
                type = InferenceEventType.FAILED,
                error = ErrorDetail(
                    code = ErrorCode.VALIDATION_FAILED,
                    message = "provider stream ended without a terminal event",
                    retryable = false,
                    provider_id = providerId,
                    details = mapOf("trace_id" to JsonString(request.trace_id))
                ),
                finish_reason = "invalid_stream"
            )
        }

        val terminalType = events.last().type
        val fallback = when (terminalType) {
            InferenceEventType.FAILED -> FallbackDecision(FallbackTarget.EMBEDDED_TLM, "system provider failed")
            else -> null
        }
        return AdapterExecution(request.request_id, request.trace_id, snapshot.revisionKey, events, fallback)
    }

    private fun failedExecution(
        request: InferenceRequest,
        snapshot: AndroidSystemCapabilitySnapshot,
        code: ErrorCode,
        message: String,
        retryable: Boolean,
        fallback: FallbackDecision
    ): AdapterExecution {
        val event = InferenceEvent(
            schema = "ai-edge-tlm/inference-event/v1",
            request_id = request.request_id,
            sequence = 0,
            type = InferenceEventType.FAILED,
            error = ErrorDetail(
                code = code,
                message = message,
                retryable = retryable,
                provider_id = providerId,
                details = mapOf("trace_id" to JsonString(request.trace_id))
            ),
            finish_reason = "fallback_required"
        )
        return AdapterExecution(request.request_id, request.trace_id, snapshot.revisionKey, listOf(event), fallback)
    }

    private fun sha256(value: String): String = MessageDigest.getInstance("SHA-256")
        .digest(value.toByteArray(Charsets.UTF_8))
        .joinToString("") { byte -> "%02x".format(byte) }
}
