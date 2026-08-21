package io.ed3c.aiedge.adapters.android.litertlm

import io.ed3c.aiedge.contracts.v1.*

private const val SHA_A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
private const val SHA_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
private const val P4_COMMIT = "6b90db1654d10cd34ad093890af4209daf810b7d"
private const val P4_BLOB = "a7266eeb48b85cb66086431805e84394e4a61627"

class FakeSession(override val observedBackend: BackendKind, private val chunks: List<RuntimeChunk>) : EmbeddedSession {
    var cancelled = false
    override fun stream(request: InferenceRequest): Sequence<RuntimeChunk> = chunks.asSequence()
    override fun cancel() { cancelled = true }
    override fun close() = Unit
}

class FakeRuntime(override val supportedBackends: Set<BackendKind>, private val observed: BackendKind, private val chunks: List<RuntimeChunk>) : EmbeddedRuntime {
    override val runtimeId = "litert-lm"
    override val runtimeRevision = "v0.14.0-test-double"
    var openCalls = 0
    override fun open(artifact: AdmittedArtifact, selectedBackend: BackendKind): EmbeddedSession { openCalls += 1; return FakeSession(observed, chunks) }
}

fun artifact(): AdmittedArtifact = AdmittedArtifact(ModelArtifactRef("tiny-tool", "1", SHA_A, ArtifactFormat.LITERTLM, "int4", SHA_B, LicensePlane.MODEL_WEIGHTS, TermsState.ACCEPTED), P4_COMMIT, P4_BLOB)
fun request(ref: ModelArtifactRef = artifact().ref): InferenceRequest = InferenceRequest(
    "ai-edge-tlm/inference-request/v1", "req-1", "trace-1", "task-1", TaskKind.FUNCTION_CALLING,
    listOf(Message(MessageRole.USER, "open settings")),
    CapabilityProfile(PlatformKind.ANDROID, "16", "test-device", 4096, false, listOf(BackendKind.CPU), listOf(Modality.TEXT), 1),
    ResourceBudget(1024, 128, 5000, 1024, false), model_ref = ref,
)
fun release() = LiteRtLmReleasePin("v0.14.0", "80f301f", ApiMaturity.STABLE, ApiMaturity.PREVIEW, ReleaseIntegrityState.RELEASED_WITH_INTEGRITY_WARNING)

fun main() {
    run {
        val runtime = FakeRuntime(setOf(BackendKind.CPU), BackendKind.CPU, listOf(RuntimeChunk.Text("ok"), RuntimeChunk.Completed))
        val execution = AndroidLiteRtLmAdapter(release(), runtime).execute(request(), artifact(), BackendKind.NPU, RuntimeLoadContext(false, 1))
        check(execution.receipt!!.requestedBackend == BackendKind.NPU)
        check(execution.receipt!!.selectedBackend == BackendKind.CPU)
        check(execution.receipt!!.observedBackend == BackendKind.CPU)
        check(execution.events.last().type == InferenceEventType.COMPLETED)
    }
    run {
        val runtime = FakeRuntime(setOf(BackendKind.CPU), BackendKind.CPU, listOf(RuntimeChunk.ToolCandidate("p1", "open_settings", mapOf("page" to JsonString("privacy")), "raw-call"), RuntimeChunk.Completed))
        val execution = AndroidLiteRtLmAdapter(release(), runtime).execute(request(), artifact(), BackendKind.CPU, RuntimeLoadContext(false, 1))
        check(execution.events.first { it.type == InferenceEventType.TOOL_PROPOSAL }.tool_proposal!!.tool_name == "open_settings")
    }
    run {
        val runtime = FakeRuntime(setOf(BackendKind.CPU), BackendKind.CPU, listOf(RuntimeChunk.Completed))
        val token = CancellationToken().also { it.cancel() }
        val execution = AndroidLiteRtLmAdapter(release(), runtime).execute(request(), artifact(), BackendKind.CPU, RuntimeLoadContext(false, 1), token)
        check(runtime.openCalls == 0); check(execution.events.single().type == InferenceEventType.CANCELLED)
    }
    run {
        val runtime = FakeRuntime(setOf(BackendKind.CPU), BackendKind.CPU, listOf(RuntimeChunk.Completed))
        var failed = false
        try { AndroidLiteRtLmAdapter(release(), runtime).execute(request(), artifact(), BackendKind.CPU, RuntimeLoadContext(true, 1)) } catch (_: IllegalArgumentException) { failed = true }
        check(failed)
    }
    run {
        val runtime = FakeRuntime(setOf(BackendKind.CPU), BackendKind.CPU, listOf(RuntimeChunk.Completed))
        val mismatched = artifact().ref.copy(tokenizer_sha256 = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
        var failed = false
        try { AndroidLiteRtLmAdapter(release(), runtime).execute(request(mismatched), artifact(), BackendKind.CPU, RuntimeLoadContext(false, 1)) } catch (_: IllegalArgumentException) { failed = true }
        check(failed)
    }
    println("P3C Kotlin fake-runtime tests PASS")
}
