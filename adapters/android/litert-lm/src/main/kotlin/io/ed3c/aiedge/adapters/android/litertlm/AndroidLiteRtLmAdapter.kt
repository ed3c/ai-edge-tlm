package io.ed3c.aiedge.adapters.android.litertlm

import io.ed3c.aiedge.contracts.v1.*
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean

private val SHA256_RE = Regex("^[0-9a-f]{64}$")

enum class ReleaseIntegrityState { PINNED_IMMUTABLE, RELEASED_WITH_INTEGRITY_WARNING, UNAVAILABLE }

data class LiteRtLmReleasePin(val tag: String, val releaseCommitPrefix: String, val kotlinMaturity: ApiMaturity, val swiftMaturity: ApiMaturity, val integrityState: ReleaseIntegrityState) {
    init {
        require(tag.isNotBlank())
        require(releaseCommitPrefix.matches(Regex("^[0-9a-f]{7,40}$")))
        require(kotlinMaturity == ApiMaturity.STABLE)
        require(swiftMaturity == ApiMaturity.PREVIEW)
    }
}

data class AdmittedArtifact(val ref: ModelArtifactRef, val p4ReceiptCommit: String, val p4ReceiptBlob: String) {
    init {
        require(ref.format == ArtifactFormat.LITERTLM)
        require(ref.license_plane == LicensePlane.MODEL_WEIGHTS)
        require(ref.terms_state == TermsState.ACCEPTED)
        require(SHA256_RE.matches(ref.sha256))
        require(ref.tokenizer_sha256?.let(SHA256_RE::matches) == true)
        require(p4ReceiptCommit.matches(Regex("^[0-9a-f]{40}$")))
        require(p4ReceiptBlob.matches(Regex("^[0-9a-f]{40}$")))
    }
}

data class RuntimeLoadContext(val isUiThread: Boolean, val nowEpochMs: Long)
data class BackendSelection(val requested: BackendKind, val selected: BackendKind, val fallbackReason: String? = null) {
    init {
        require(selected in setOf(BackendKind.CPU, BackendKind.GPU, BackendKind.NPU))
        if (requested != selected) require(!fallbackReason.isNullOrBlank())
    }
}

sealed interface RuntimeChunk {
    data class Text(val value: String) : RuntimeChunk
    data class ToolCandidate(val proposalId: String, val toolName: String, val arguments: Map<String, JsonValue>, val rawModelOutput: String) : RuntimeChunk
    data class Failure(val message: String, val retryable: Boolean, val resourceExhausted: Boolean = false) : RuntimeChunk
    data object Completed : RuntimeChunk
}

interface EmbeddedSession : AutoCloseable {
    val observedBackend: BackendKind
    fun stream(request: InferenceRequest): Sequence<RuntimeChunk>
    fun cancel()
}

interface EmbeddedRuntime {
    val runtimeId: String
    val runtimeRevision: String
    val supportedBackends: Set<BackendKind>
    fun open(artifact: AdmittedArtifact, selectedBackend: BackendKind): EmbeddedSession
}

class CancellationToken {
    private val cancelled = AtomicBoolean(false)
    fun cancel() { cancelled.set(true) }
    fun isCancelled(): Boolean = cancelled.get()
}

data class EmbeddedExecutionReceipt(
    val requestId: String,
    val traceId: String,
    val runtimeId: String,
    val runtimeRevision: String,
    val releaseTag: String,
    val releaseCommitPrefix: String,
    val releaseIntegrityState: ReleaseIntegrityState,
    val artifactSha256: String,
    val tokenizerSha256: String,
    val requestedBackend: BackendKind,
    val selectedBackend: BackendKind,
    val observedBackend: BackendKind,
    val fallbackReason: String?,
    val p4ReceiptCommit: String,
    val p4ReceiptBlob: String,
    val terminalEvent: InferenceEventType,
)

data class AdapterExecution(val events: List<InferenceEvent>, val receipt: EmbeddedExecutionReceipt?)

class AndroidLiteRtLmAdapter(private val releasePin: LiteRtLmReleasePin, private val runtime: EmbeddedRuntime, private val providerId: String = "android-litert-lm") {
    fun providerDescriptor(): ProviderDescriptor = ProviderDescriptor(
        provider_id = providerId,
        kind = ProviderKind.EMBEDDED_MODEL,
        maturity = releasePin.kotlinMaturity,
        task_kinds = listOf(TaskKind.CHAT, TaskKind.SUMMARIZE, TaskKind.STRUCTURED_GENERATION, TaskKind.FUNCTION_CALLING),
        supported_backends = runtime.supportedBackends.sortedBy { it.wireValue },
        requires_network = false,
        terms_state = TermsState.REVIEW_REQUIRED,
    )

    fun selectBackend(requested: BackendKind): BackendSelection {
        require(requested in setOf(BackendKind.CPU, BackendKind.GPU, BackendKind.NPU))
        if (requested in runtime.supportedBackends) return BackendSelection(requested, requested)
        if (BackendKind.CPU in runtime.supportedBackends) return BackendSelection(requested, BackendKind.CPU, "requested backend unavailable; explicit CPU fallback")
        throw IllegalStateException("no admitted backend available")
    }

    fun execute(request: InferenceRequest, artifact: AdmittedArtifact, requestedBackend: BackendKind, context: RuntimeLoadContext, cancellation: CancellationToken = CancellationToken()): AdapterExecution {
        validateRequest(request, artifact, context)
        if (cancellation.isCancelled()) return AdapterExecution(listOf(cancelledEvent(request, 0, "cancelled before runtime open")), null)
        val selection = selectBackend(requestedBackend)
        val session = runtime.open(artifact, selection.selected)
        session.use {
            require(session.observedBackend in runtime.supportedBackends) { "runtime observed unsupported backend" }
            val events = mutableListOf(InferenceEvent("ai-edge-tlm/inference-event/v1", request.request_id, 0, InferenceEventType.STARTED))
            var sequence = 1L
            var terminal = false
            for (chunk in session.stream(request)) {
                if (cancellation.isCancelled()) {
                    session.cancel(); events += cancelledEvent(request, sequence, "cancelled during generation"); terminal = true; break
                }
                when (chunk) {
                    is RuntimeChunk.Text -> {
                        require(chunk.value.isNotEmpty())
                        events += InferenceEvent("ai-edge-tlm/inference-event/v1", request.request_id, sequence++, InferenceEventType.TOKEN_DELTA, text_delta = chunk.value)
                    }
                    is RuntimeChunk.ToolCandidate -> {
                        require(chunk.proposalId.isNotBlank() && chunk.toolName.isNotBlank())
                        events += InferenceEvent(
                            schema = "ai-edge-tlm/inference-event/v1",
                            request_id = request.request_id,
                            sequence = sequence++,
                            type = InferenceEventType.TOOL_PROPOSAL,
                            tool_proposal = ToolProposal(chunk.proposalId, chunk.toolName, chunk.arguments, sha256(chunk.rawModelOutput)),
                        )
                    }
                    is RuntimeChunk.Failure -> {
                        events += InferenceEvent(
                            schema = "ai-edge-tlm/inference-event/v1",
                            request_id = request.request_id,
                            sequence = sequence++,
                            type = InferenceEventType.FAILED,
                            error = ErrorDetail(if (chunk.resourceExhausted) ErrorCode.RESOURCE_EXHAUSTED else ErrorCode.GENERATION_FAILED, chunk.message, chunk.retryable, providerId),
                        )
                        terminal = true
                    }
                    RuntimeChunk.Completed -> {
                        events += InferenceEvent("ai-edge-tlm/inference-event/v1", request.request_id, sequence++, InferenceEventType.COMPLETED, finish_reason = "stop")
                        terminal = true
                    }
                }
                if (terminal) break
            }
            if (!terminal) events += InferenceEvent("ai-edge-tlm/inference-event/v1", request.request_id, sequence, InferenceEventType.FAILED, error = ErrorDetail(ErrorCode.GENERATION_FAILED, "runtime ended without terminal event", false, providerId))
            val receipt = EmbeddedExecutionReceipt(
                request.request_id, request.trace_id, runtime.runtimeId, runtime.runtimeRevision, releasePin.tag, releasePin.releaseCommitPrefix,
                releasePin.integrityState, artifact.ref.sha256, requireNotNull(artifact.ref.tokenizer_sha256), requestedBackend, selection.selected,
                session.observedBackend, selection.fallbackReason, artifact.p4ReceiptCommit, artifact.p4ReceiptBlob, events.last().type,
            )
            return AdapterExecution(events, receipt)
        }
    }

    private fun validateRequest(request: InferenceRequest, artifact: AdmittedArtifact, context: RuntimeLoadContext) {
        require(request.schema == "ai-edge-tlm/inference-request/v1")
        require(request.request_id.isNotBlank() && request.trace_id.isNotBlank())
        require(!context.isUiThread) { "model load/execution must not run on UI thread" }
        require(context.nowEpochMs >= 0)
        require(!request.resource_budget.allow_network) { "embedded adapter refuses network-enabled execution" }
        val requestRef = requireNotNull(request.model_ref) { "embedded execution requires model_ref" }
        require(requestRef.sha256 == artifact.ref.sha256) { "request model digest differs from admitted P4 artifact" }
        require(requestRef.tokenizer_sha256 == artifact.ref.tokenizer_sha256) { "tokenizer digest mismatch" }
        require(requestRef.terms_state == TermsState.ACCEPTED) { "model terms not admitted" }
        require(requestRef.format == ArtifactFormat.LITERTLM)
        require(releasePin.integrityState != ReleaseIntegrityState.UNAVAILABLE)
    }

    private fun cancelledEvent(request: InferenceRequest, sequence: Long, message: String) = InferenceEvent(
        "ai-edge-tlm/inference-event/v1", request.request_id, sequence, InferenceEventType.CANCELLED,
        error = ErrorDetail(ErrorCode.CANCELLED, message, false, providerId),
    )

    private fun sha256(text: String): String = MessageDigest.getInstance("SHA-256").digest(text.toByteArray()).joinToString("") { "%02x".format(it) }
}
