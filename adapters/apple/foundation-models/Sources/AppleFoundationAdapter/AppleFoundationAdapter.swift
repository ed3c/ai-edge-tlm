import Foundation
import AIEdgeContracts

public final class AppleFoundationModelsAdapter: Sendable {
    private let providerID: String
    private let maturity: ApiMaturity
    private let termsState: TermsState
    private let registry: SessionIsolationRegistry

    public init(
        providerID: String = "apple.foundation-models",
        maturity: ApiMaturity = .beta,
        termsState: TermsState = .reviewRequired,
        registry: SessionIsolationRegistry = .init()
    ) {
        precondition(!providerID.isEmpty)
        self.providerID = providerID
        self.maturity = maturity
        self.termsState = termsState
        self.registry = registry
    }

    public func probe(_ observation: AppleSystemCapabilityObservation) -> AppleSystemCapabilitySnapshot {
        let available = observation.availability == .available
        return AppleSystemCapabilitySnapshot(
            revisionKey: observation.revision.key,
            observedAtEpochMS: observation.observedAtEpochMS,
            availability: observation.availability,
            reason: observation.reason,
            capabilityProfile: CapabilityProfile(
                platform: .ios,
                os_version: observation.revision.osBuild,
                device_model: observation.deviceModel,
                available_memory_mb: observation.availableMemoryMB,
                supports_system_model: available,
                supported_backends: available ? [.unknown] : [],
                supported_modalities: available ? [.text] : [],
                max_active_sessions: available ? 1 : 0
            ),
            providerDescriptor: ProviderDescriptor(
                provider_id: providerID,
                kind: .systemModel,
                maturity: maturity,
                task_kinds: [.chat, .summarize, .structuredGeneration, .functionCalling],
                supported_backends: available ? [.unknown] : [],
                requires_network: false,
                terms_state: termsState
            ),
            evidenceLane: observation.evidenceLane
        )
    }

    public func execute(
        request: InferenceRequest,
        snapshot: AppleSystemCapabilitySnapshot,
        profile: PromptProfile,
        sessionID: String,
        session: any AppleSystemSession,
        cancellation: CancellationToken = .init()
    ) async throws -> AdapterExecution {
        guard request.schema == "ai-edge-tlm/inference-request/v1", !request.request_id.isEmpty, !request.trace_id.isEmpty else {
            throw AdapterError.invalidRequest
        }
        if snapshot.availability == .stale { throw AdapterError.staleCapability }
        if snapshot.availability != .available || !snapshot.capabilityProfile.supports_system_model {
            return failure(
                request: request,
                snapshot: snapshot,
                code: .capabilityUnavailable,
                message: snapshot.reason.rawValue,
                retryable: true,
                fallback: FallbackDecision(reason: snapshot.reason.rawValue)
            )
        }
        guard profile.admits(snapshot) else { throw AdapterError.promptProfileMismatch }

        try await registry.admit(sessionID: sessionID, requestID: request.request_id)
        if await cancellation.isCancelled() {
            await registry.release(sessionID: sessionID)
            return cancelledExecution(request: request, snapshot: snapshot, message: "request cancelled before provider execution")
        }

        do {
            try await session.prewarm(profile: profile)
            var events = [InferenceEvent(
                schema: "ai-edge-tlm/inference-event/v1",
                request_id: request.request_id,
                sequence: 0,
                type: .started
            )]
            var sequence: Int64 = 1
            var terminal = false

            for try await chunk in session.stream(request: request, profile: profile) {
                if await cancellation.isCancelled() {
                    await session.cancel()
                    events.append(cancelledEvent(request: request, sequence: sequence, message: "request cancelled"))
                    terminal = true
                    break
                }
                switch chunk {
                case .text(let value):
                    guard !value.isEmpty else { throw AdapterError.invalidRequest }
                    events.append(InferenceEvent(
                        schema: "ai-edge-tlm/inference-event/v1",
                        request_id: request.request_id,
                        sequence: sequence,
                        type: .tokenDelta,
                        text_delta: value
                    ))
                    sequence += 1
                case .toolCandidate(let proposalID, let toolName, let arguments, let rawModelOutput):
                    guard !proposalID.isEmpty, !toolName.isEmpty else { throw AdapterError.invalidRequest }
                    events.append(InferenceEvent(
                        schema: "ai-edge-tlm/inference-event/v1",
                        request_id: request.request_id,
                        sequence: sequence,
                        type: .toolProposal,
                        tool_proposal: ToolProposal(
                            proposal_id: proposalID,
                            tool_name: toolName,
                            arguments: arguments,
                            model_output_digest: SHA256.hex(rawModelOutput)
                        )
                    ))
                    sequence += 1
                case .contextWindowExceeded:
                    events.append(InferenceEvent(
                        schema: "ai-edge-tlm/inference-event/v1",
                        request_id: request.request_id,
                        sequence: sequence,
                        type: .degraded,
                        error: ErrorDetail(
                            code: .resourceExhausted,
                            message: "context window exceeded",
                            retryable: false,
                            provider_id: providerID,
                            details: ["trace_id": .string(request.trace_id)]
                        ),
                        finish_reason: "fallback_required"
                    ))
                    terminal = true
                case .failure(let message, let retryable):
                    events.append(InferenceEvent(
                        schema: "ai-edge-tlm/inference-event/v1",
                        request_id: request.request_id,
                        sequence: sequence,
                        type: .failed,
                        error: ErrorDetail(
                            code: .generationFailed,
                            message: message,
                            retryable: retryable,
                            provider_id: providerID,
                            details: ["trace_id": .string(request.trace_id)]
                        ),
                        finish_reason: "provider_failure"
                    ))
                    terminal = true
                case .completed:
                    events.append(InferenceEvent(
                        schema: "ai-edge-tlm/inference-event/v1",
                        request_id: request.request_id,
                        sequence: sequence,
                        type: .completed,
                        finish_reason: "stop"
                    ))
                    terminal = true
                }
                if terminal { break }
            }

            if !terminal {
                events.append(InferenceEvent(
                    schema: "ai-edge-tlm/inference-event/v1",
                    request_id: request.request_id,
                    sequence: sequence,
                    type: .failed,
                    error: ErrorDetail(
                        code: .validationFailed,
                        message: "provider stream ended without terminal event",
                        retryable: false,
                        provider_id: providerID,
                        details: ["trace_id": .string(request.trace_id)]
                    ),
                    finish_reason: "invalid_stream"
                ))
            }
            await registry.release(sessionID: sessionID)
            let fallback = [.failed, .degraded].contains(events.last!.type)
                ? FallbackDecision(reason: "system provider unavailable or failed")
                : nil
            return AdapterExecution(
                requestID: request.request_id,
                traceID: request.trace_id,
                revisionKey: snapshot.revisionKey,
                events: events,
                fallback: fallback
            )
        } catch let error as AdapterError {
            await registry.release(sessionID: sessionID)
            return failure(
                request: request,
                snapshot: snapshot,
                code: .validationFailed,
                message: String(describing: error),
                retryable: false,
                fallback: FallbackDecision(reason: "provider output validation failed")
            )
        } catch {
            await registry.release(sessionID: sessionID)
            return failure(
                request: request,
                snapshot: snapshot,
                code: .generationFailed,
                message: "system provider session failed",
                retryable: false,
                fallback: FallbackDecision(reason: "system provider session failed")
            )
        }
    }

    public func cancel(session: any AppleSystemSession, token: CancellationToken) async {
        await token.cancel()
        await session.cancel()
    }

    private func cancelledEvent(request: InferenceRequest, sequence: Int64, message: String) -> InferenceEvent {
        InferenceEvent(
            schema: "ai-edge-tlm/inference-event/v1",
            request_id: request.request_id,
            sequence: sequence,
            type: .cancelled,
            error: ErrorDetail(
                code: .cancelled,
                message: message,
                retryable: false,
                provider_id: providerID,
                details: ["trace_id": .string(request.trace_id)]
            ),
            finish_reason: "cancelled"
        )
    }

    private func cancelledExecution(request: InferenceRequest, snapshot: AppleSystemCapabilitySnapshot, message: String) -> AdapterExecution {
        let events = [
            InferenceEvent(
                schema: "ai-edge-tlm/inference-event/v1",
                request_id: request.request_id,
                sequence: 0,
                type: .started
            ),
            cancelledEvent(request: request, sequence: 1, message: message)
        ]
        return AdapterExecution(
            requestID: request.request_id,
            traceID: request.trace_id,
            revisionKey: snapshot.revisionKey,
            events: events,
            fallback: nil
        )
    }

    private func failure(
        request: InferenceRequest,
        snapshot: AppleSystemCapabilitySnapshot,
        code: ErrorCode,
        message: String,
        retryable: Bool,
        fallback: FallbackDecision
    ) -> AdapterExecution {
        let event = InferenceEvent(
            schema: "ai-edge-tlm/inference-event/v1",
            request_id: request.request_id,
            sequence: 0,
            type: .failed,
            error: ErrorDetail(
                code: code,
                message: message,
                retryable: retryable,
                provider_id: providerID,
                details: ["trace_id": .string(request.trace_id)]
            ),
            finish_reason: "fallback_required"
        )
        return AdapterExecution(
            requestID: request.request_id,
            traceID: request.trace_id,
            revisionKey: snapshot.revisionKey,
            events: [event],
            fallback: fallback
        )
    }
}
