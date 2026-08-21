import Foundation
import AIEdgeContracts

public struct FakeAppleSystemSession: AppleSystemSession {
    public let chunks: [ProviderChunk]
    public let prewarmFailure: String?

    public init(chunks: [ProviderChunk], prewarmFailure: String? = nil) {
        self.chunks = chunks
        self.prewarmFailure = prewarmFailure
    }

    public func prewarm(profile: PromptProfile) async throws {
        if let prewarmFailure { throw FakeSessionError.failed(prewarmFailure) }
    }

    public func stream(request: InferenceRequest, profile: PromptProfile) -> AsyncThrowingStream<ProviderChunk, Error> {
        AsyncThrowingStream { continuation in
            for chunk in chunks { continuation.yield(chunk) }
            continuation.finish()
        }
    }
    public func cancel() async {}
}

public enum FakeSessionError: Error, Equatable, Sendable { case failed(String) }
