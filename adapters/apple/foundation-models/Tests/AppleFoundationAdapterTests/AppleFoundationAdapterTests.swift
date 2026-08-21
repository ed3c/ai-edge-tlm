import XCTest
import AIEdgeContracts
@testable import AppleFoundationAdapter

final class AppleFoundationAdapterTests: XCTestCase {
    private func request(_ id: String = "req-1") -> InferenceRequest {
        InferenceRequest(
            schema: "ai-edge-tlm/inference-request/v1",
            request_id: id,
            trace_id: "trace-\(id)",
            task_id: "task-1",
            task_kind: .functionCalling,
            messages: [Message(role: .user, content: "schedule a meeting")],
            capability_profile: CapabilityProfile(
                platform: .ios,
                os_version: "23A1",
                device_model: "fake-iphone",
                available_memory_mb: 4096,
                supports_system_model: true,
                supported_backends: [.unknown],
                supported_modalities: [.text],
                max_active_sessions: 1
            ),
            resource_budget: ResourceBudget(
                max_input_tokens: 1024,
                max_output_tokens: 256,
                timeout_ms: 5000,
                max_memory_mb: 512,
                allow_network: false
            )
        )
    }

    private func observation(
        availability: AvailabilityState = .available,
        reason: AvailabilityReason = .available,
        model: String = "model-r1",
        time: Int64 = 1000,
        lane: EvidenceLane = .local
    ) -> AppleSystemCapabilityObservation {
        AppleSystemCapabilityObservation(
            deviceModel: "fake-iphone",
            availableMemoryMB: 4096,
            availability: availability,
            reason: reason,
            revision: AppleCapabilityRevision(osBuild: "23A1", systemModelRevision: model, sdkAPIVersion: "foundation-models-beta-1", region: "US"),
            observedAtEpochMS: time,
            evidenceLane: lane
        )
    }

    private func profile(model: String = "model-r1") -> PromptProfile {
        PromptProfile(
            profileID: "calendar.function-calling",
            version: "1",
            osBuild: "23A1",
            systemModelRevision: model,
            instructionSHA256: String(repeating: "a", count: 64)
        )
    }

    func testAvailableStreamAndToolProposalRemainCandidates() async throws {
        let adapter = AppleFoundationModelsAdapter()
        let snapshot = adapter.probe(observation())
        let session = FakeAppleSystemSession(chunks: [
            .text("hello"),
            .toolCandidate(
                proposalID: "proposal-1",
                toolName: "calendar.create",
                arguments: ["title": .string("sync")],
                rawModelOutput: "raw-tool-output"
            ),
            .completed
        ])
        let execution = try await adapter.execute(
            request: request(),
            snapshot: snapshot,
            profile: profile(),
            sessionID: "session-1",
            session: session
        )
        XCTAssertNil(execution.fallback)
        XCTAssertEqual(execution.events.map(\.type), [.started, .tokenDelta, .toolProposal, .completed])
        XCTAssertEqual(execution.events[2].tool_proposal?.tool_name, "calendar.create")
        XCTAssertEqual(execution.events[2].tool_proposal?.model_output_digest, "70c07a15ee24d499e8ae7979fab9cd17b32e46ba7fb830e636f88eb6916c2725")
        XCTAssertFalse(snapshot.providerDescriptor.requires_network)
    }

    func testUnavailableFallsBackToEmbeddedWithoutNetwork() async throws {
        let adapter = AppleFoundationModelsAdapter()
        let snapshot = adapter.probe(observation(availability: .unavailable, reason: .deviceUnsupported))
        let execution = try await adapter.execute(
            request: request("req-2"), snapshot: snapshot, profile: profile(), sessionID: "session-2", session: FakeAppleSystemSession(chunks: [])
        )
        XCTAssertEqual(execution.events.single?.error?.code, .capabilityUnavailable)
        XCTAssertEqual(execution.fallback?.providerKind, .embeddedModel)
        XCTAssertEqual(execution.fallback?.networkAllowed, false)
    }

    func testRevisionAndExpiryBecomeStale() {
        let adapter = AppleFoundationModelsAdapter()
        let snapshot = adapter.probe(observation())
        let cache = CapabilityCache(maxAgeMS: 500)
        XCTAssertEqual(cache.admit(snapshot, expectedRevisionKey: snapshot.revisionKey, nowEpochMS: 1200).availability, .available)
        XCTAssertEqual(cache.admit(snapshot, expectedRevisionKey: "23A1|model-r2|foundation-models-beta-1|US", nowEpochMS: 1200).availability, .stale)
        XCTAssertEqual(cache.admit(snapshot, expectedRevisionKey: snapshot.revisionKey, nowEpochMS: 2000).reason, .observationExpired)
    }

    func testPromptProfileCannotCrossRevision() async throws {
        let adapter = AppleFoundationModelsAdapter()
        do {
            _ = try await adapter.execute(
                request: request("req-3"),
                snapshot: adapter.probe(observation(model: "model-r2")),
                profile: profile(),
                sessionID: "session-3",
                session: FakeAppleSystemSession(chunks: [])
            )
            XCTFail("expected profile mismatch")
        } catch AdapterError.promptProfileMismatch {}
    }

    func testContextWindowFailureIsTypedAndFallsBack() async throws {
        let adapter = AppleFoundationModelsAdapter()
        let execution = try await adapter.execute(
            request: request("req-4"),
            snapshot: adapter.probe(observation()),
            profile: profile(),
            sessionID: "session-4",
            session: FakeAppleSystemSession(chunks: [.contextWindowExceeded])
        )
        XCTAssertEqual(execution.events.last?.type, .degraded)
        XCTAssertEqual(execution.events.last?.error?.code, .resourceExhausted)
        XCTAssertEqual(execution.fallback?.providerID, "apple.litert")
    }

    func testSessionOwnerIsolation() async throws {
        let registry = SessionIsolationRegistry()
        try await registry.admit(sessionID: "shared", requestID: "req-a")
        do {
            try await registry.admit(sessionID: "shared", requestID: "req-b")
            XCTFail("expected ownership conflict")
        } catch AdapterError.sessionOwnershipConflict {}
        await registry.release(sessionID: "shared")
        let activeCount = await registry.activeCount()
        XCTAssertEqual(activeCount, 0)
    }


    func testPreCancelledRequestDoesNotEnterProvider() async throws {
        let adapter = AppleFoundationModelsAdapter()
        let token = CancellationToken()
        await token.cancel()
        let execution = try await adapter.execute(
            request: request("req-cancelled"),
            snapshot: adapter.probe(observation()),
            profile: profile(),
            sessionID: "session-cancelled",
            session: FakeAppleSystemSession(chunks: [.completed]),
            cancellation: token
        )
        XCTAssertEqual(execution.events.map(\.type), [.started, .cancelled])
        XCTAssertNil(execution.fallback)
    }

    func testProviderFailureMapsToTypedEventAndFallback() async throws {
        let adapter = AppleFoundationModelsAdapter()
        let execution = try await adapter.execute(
            request: request("req-provider-error"),
            snapshot: adapter.probe(observation()),
            profile: profile(),
            sessionID: "session-provider-error",
            session: FakeAppleSystemSession(chunks: [], prewarmFailure: "failed")
        )
        XCTAssertEqual(execution.events.single?.error?.code, .generationFailed)
        XCTAssertEqual(execution.fallback?.providerKind, .embeddedModel)
    }

    func testStaticLaneIsNotLiveDevice() {
        let adapter = AppleFoundationModelsAdapter()
        XCTAssertEqual(adapter.probe(observation()).evidenceLane, .local)
        XCTAssertNotEqual(adapter.probe(observation()).evidenceLane, .liveDevice)
    }
}

private extension Array {
    var single: Element? { count == 1 ? self[0] : nil }
}
