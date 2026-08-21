import Foundation
import AIEdgeContracts

public enum AvailabilityState: String, Codable, Equatable, Sendable {
    case available = "AVAILABLE"
    case unavailable = "UNAVAILABLE"
    case stale = "STALE"
}

public enum AvailabilityReason: String, Codable, Equatable, Sendable {
    case available = "AVAILABLE"
    case deviceUnsupported = "DEVICE_UNSUPPORTED"
    case osUnsupported = "OS_UNSUPPORTED"
    case regionUnsupported = "REGION_UNSUPPORTED"
    case modelUnavailable = "MODEL_UNAVAILABLE"
    case termsNotAdmitted = "TERMS_NOT_ADMITTED"
    case revisionChanged = "REVISION_CHANGED"
    case observationExpired = "OBSERVATION_EXPIRED"
    case unknown = "UNKNOWN"
}

public struct AppleCapabilityRevision: Codable, Equatable, Sendable {
    public let osBuild: String
    public let systemModelRevision: String
    public let sdkAPIVersion: String
    public let region: String

    public init(osBuild: String, systemModelRevision: String, sdkAPIVersion: String, region: String) {
        precondition(!osBuild.isEmpty && !systemModelRevision.isEmpty && !sdkAPIVersion.isEmpty && !region.isEmpty)
        self.osBuild = osBuild
        self.systemModelRevision = systemModelRevision
        self.sdkAPIVersion = sdkAPIVersion
        self.region = region
    }

    public var key: String { [osBuild, systemModelRevision, sdkAPIVersion, region].joined(separator: "|") }
}

public struct AppleSystemCapabilityObservation: Codable, Equatable, Sendable {
    public let deviceModel: String
    public let availableMemoryMB: Int64
    public let availability: AvailabilityState
    public let reason: AvailabilityReason
    public let revision: AppleCapabilityRevision
    public let observedAtEpochMS: Int64
    public let evidenceLane: EvidenceLane

    public init(
        deviceModel: String,
        availableMemoryMB: Int64,
        availability: AvailabilityState,
        reason: AvailabilityReason,
        revision: AppleCapabilityRevision,
        observedAtEpochMS: Int64,
        evidenceLane: EvidenceLane = .local
    ) {
        precondition(!deviceModel.isEmpty && availableMemoryMB >= 0 && observedAtEpochMS >= 0)
        precondition((availability == .available) == (reason == .available))
        self.deviceModel = deviceModel
        self.availableMemoryMB = availableMemoryMB
        self.availability = availability
        self.reason = reason
        self.revision = revision
        self.observedAtEpochMS = observedAtEpochMS
        self.evidenceLane = evidenceLane
    }
}

public struct AppleSystemCapabilitySnapshot: Equatable, Sendable {
    public let revisionKey: String
    public let observedAtEpochMS: Int64
    public let availability: AvailabilityState
    public let reason: AvailabilityReason
    public let capabilityProfile: CapabilityProfile
    public let providerDescriptor: ProviderDescriptor
    public let evidenceLane: EvidenceLane
}

public struct PromptProfile: Codable, Equatable, Sendable {
    public let profileID: String
    public let version: String
    public let osBuild: String
    public let systemModelRevision: String
    public let instructionSHA256: String

    public init(profileID: String, version: String, osBuild: String, systemModelRevision: String, instructionSHA256: String) {
        precondition(!profileID.isEmpty && !version.isEmpty)
        precondition(instructionSHA256.count == 64 && instructionSHA256.allSatisfy { $0.isHexDigit })
        self.profileID = profileID
        self.version = version
        self.osBuild = osBuild
        self.systemModelRevision = systemModelRevision
        self.instructionSHA256 = instructionSHA256.lowercased()
    }

    public func admits(_ snapshot: AppleSystemCapabilitySnapshot) -> Bool {
        let parts = snapshot.revisionKey.split(separator: "|", omittingEmptySubsequences: false)
        guard parts.count == 4 else { return false }
        return parts[0] == Substring(osBuild) && parts[1] == Substring(systemModelRevision)
    }
}

public struct FallbackDecision: Equatable, Sendable {
    public let providerID: String
    public let providerKind: ProviderKind
    public let reason: String
    public let networkAllowed: Bool

    public init(providerID: String = "apple.litert", providerKind: ProviderKind = .embeddedModel, reason: String, networkAllowed: Bool = false) {
        precondition(!reason.isEmpty)
        precondition(!networkAllowed, "system adapter may not silently enable network")
        self.providerID = providerID
        self.providerKind = providerKind
        self.reason = reason
        self.networkAllowed = networkAllowed
    }
}

public struct AdapterExecution: Equatable, Sendable {
    public let requestID: String
    public let traceID: String
    public let revisionKey: String?
    public let events: [InferenceEvent]
    public let fallback: FallbackDecision?
}

public enum ProviderChunk: Equatable, Sendable {
    case text(String)
    case toolCandidate(proposalID: String, toolName: String, arguments: [String: JSONValue], rawModelOutput: String)
    case contextWindowExceeded
    case failure(message: String, retryable: Bool)
    case completed
}

public protocol AppleSystemSession: Sendable {
    func prewarm(profile: PromptProfile) async throws
    func stream(request: InferenceRequest, profile: PromptProfile) -> AsyncThrowingStream<ProviderChunk, Error>
    func cancel() async
}

public actor CancellationToken {
    private var cancelled = false
    public init() {}
    public func cancel() { cancelled = true }
    public func isCancelled() -> Bool { cancelled }
}

public actor SessionIsolationRegistry {
    private var owners: [String: String] = [:]
    public init() {}

    public func admit(sessionID: String, requestID: String) throws {
        if let current = owners[sessionID], current != requestID {
            throw AdapterError.sessionOwnershipConflict
        }
        owners[sessionID] = requestID
    }

    public func release(sessionID: String) { owners.removeValue(forKey: sessionID) }
    public func activeCount() -> Int { owners.count }
}

public enum AdapterError: Error, Equatable, Sendable {
    case staleCapability
    case promptProfileMismatch
    case sessionOwnershipConflict
    case invalidRequest
}

public struct CapabilityCache: Sendable {
    public let maxAgeMS: Int64
    public init(maxAgeMS: Int64) { precondition(maxAgeMS > 0); self.maxAgeMS = maxAgeMS }

    public func admit(
        _ snapshot: AppleSystemCapabilitySnapshot,
        expectedRevisionKey: String,
        nowEpochMS: Int64
    ) -> AppleSystemCapabilitySnapshot {
        if snapshot.revisionKey != expectedRevisionKey {
            return AppleSystemCapabilitySnapshot(
                revisionKey: snapshot.revisionKey,
                observedAtEpochMS: snapshot.observedAtEpochMS,
                availability: .stale,
                reason: .revisionChanged,
                capabilityProfile: snapshot.capabilityProfile,
                providerDescriptor: snapshot.providerDescriptor,
                evidenceLane: snapshot.evidenceLane
            )
        }
        if nowEpochMS < snapshot.observedAtEpochMS || nowEpochMS - snapshot.observedAtEpochMS > maxAgeMS {
            return AppleSystemCapabilitySnapshot(
                revisionKey: snapshot.revisionKey,
                observedAtEpochMS: snapshot.observedAtEpochMS,
                availability: .stale,
                reason: .observationExpired,
                capabilityProfile: snapshot.capabilityProfile,
                providerDescriptor: snapshot.providerDescriptor,
                evidenceLane: snapshot.evidenceLane
            )
        }
        return snapshot
    }
}
