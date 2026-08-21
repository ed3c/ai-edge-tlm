package io.ed3c.aiedge.adapters.android.systemgenai

import io.ed3c.aiedge.contracts.v1.*

private fun request(id: String = "req-1") = InferenceRequest(
    schema = "ai-edge-tlm/inference-request/v1",
    request_id = id,
    trace_id = "trace-$id",
    task_id = "task-1",
    task_kind = TaskKind.FUNCTION_CALLING,
    messages = listOf(Message(MessageRole.USER, "schedule a meeting")),
    capability_profile = CapabilityProfile(PlatformKind.ANDROID, "16", "fake-device", 4096, true, listOf(BackendKind.UNKNOWN), listOf(Modality.TEXT), 1),
    resource_budget = ResourceBudget(1024, 256, 5_000, 512, false)
)

private fun availableObservation(revision: String = "model-r1", time: Long = 1000) = AndroidSystemCapabilityObservation(
    deviceModel = "fake-device",
    availableMemoryMb = 4096,
    supportedBackends = listOf(BackendKind.UNKNOWN),
    supportedModalities = listOf(Modality.TEXT),
    maxActiveSessions = 1,
    availability = AvailabilityState.AVAILABLE,
    revision = CapabilityRevision("16", revision, "prompt-api-beta-1"),
    observedAtEpochMs = time
)

fun main() {
    val adapter = AndroidSystemProviderAdapter()
    val snapshot = adapter.probe(availableObservation())
    check(snapshot.capabilityProfile.supports_system_model)
    check(!snapshot.providerDescriptor.requires_network)
    check(snapshot.providerDescriptor.kind == ProviderKind.SYSTEM_MODEL)

    val session = AndroidSystemSession {
        sequenceOf(
            ProviderChunk.Text("hello"),
            ProviderChunk.ToolCandidate("proposal-1", "calendar.create", mapOf("title" to JsonString("sync")), "raw-tool-output"),
            ProviderChunk.Completed
        )
    }
    val execution = adapter.execute(request(), snapshot, session)
    check(execution.requestId == "req-1")
    check(execution.traceId == "trace-req-1")
    check(execution.fallback == null)
    check(execution.events.map { it.type } == listOf(InferenceEventType.STARTED, InferenceEventType.TOKEN_DELTA, InferenceEventType.TOOL_PROPOSAL, InferenceEventType.COMPLETED))
    check(execution.events[2].tool_proposal?.tool_name == "calendar.create")
    check(execution.events[2].tool_proposal?.model_output_digest?.length == 64)

    val unavailable = adapter.probe(availableObservation().copy(availability = AvailabilityState.UNAVAILABLE, reason = "device unsupported"))
    val unavailableExecution = adapter.execute(request("req-2"), unavailable, session)
    check(unavailableExecution.events.single().error?.code == ErrorCode.CAPABILITY_UNAVAILABLE)
    check(unavailableExecution.fallback?.target == FallbackTarget.EMBEDDED_TLM)
    check(unavailableExecution.fallback?.networkAllowed == false)

    val cache = CapabilityCache(maxAgeMs = 500)
    cache.put(snapshot)
    check(cache.read(snapshot.revisionKey, 1200)?.availability == AvailabilityState.AVAILABLE)
    val newRevisionKey = CapabilityRevision("16", "model-r2", "prompt-api-beta-1").key
    check(cache.read(newRevisionKey, 1200)?.availability == AvailabilityState.STALE)
    check(cache.read(snapshot.revisionKey, 2000)?.availability == AvailabilityState.STALE)


    val preCancelledToken = CancellationToken().also { it.cancel() }
    val preCancelled = adapter.execute(request("req-pre-cancel"), snapshot, session, preCancelledToken)
    check(preCancelled.events.map { it.type } == listOf(InferenceEventType.STARTED, InferenceEventType.CANCELLED))
    check(preCancelled.fallback == null)

    val cancellation = CancellationToken()
    val cancellingSession = AndroidSystemSession {
        sequence {
            yield(ProviderChunk.Text("first"))
            cancellation.cancel()
            yield(ProviderChunk.Text("second"))
        }
    }
    val cancelled = adapter.execute(request("req-3"), snapshot, cancellingSession, cancellation)
    check(cancelled.events.last().type == InferenceEventType.CANCELLED)
    check(cancelled.events.last().error?.details?.get("trace_id") == JsonString("trace-req-3"))

    val invalidStream = adapter.execute(request("req-4"), snapshot, AndroidSystemSession { sequenceOf(ProviderChunk.Text("only")) })
    check(invalidStream.events.last().error?.code == ErrorCode.VALIDATION_FAILED)
    check(invalidStream.fallback?.target == FallbackTarget.EMBEDDED_TLM)

    println("P3A Kotlin fake-provider tests PASS")
}
