import Foundation
import AIEdgeContracts

public enum ReleaseIntegrityState: String, Sendable { case pinnedImmutable = "PINNED_IMMUTABLE"; case releasedWithIntegrityWarning = "RELEASED_WITH_INTEGRITY_WARNING"; case unavailable = "UNAVAILABLE" }

public struct LiteRtLmAppleReleasePin: Sendable, Equatable {
    public let tag: String; public let releaseCommitPrefix: String; public let swiftMaturity: ApiMaturity; public let integrityState: ReleaseIntegrityState
    public init(tag:String, releaseCommitPrefix:String, swiftMaturity:ApiMaturity, integrityState:ReleaseIntegrityState) {
        precondition(!tag.isEmpty && releaseCommitPrefix.count >= 7)
        precondition(swiftMaturity == .preview, "Swift LiteRT-LM must remain PREVIEW until owning source evidence changes")
        self.tag=tag; self.releaseCommitPrefix=releaseCommitPrefix; self.swiftMaturity=swiftMaturity; self.integrityState=integrityState
    }
}

public struct AdmittedArtifact: Sendable, Equatable {
    public let ref: ModelArtifactRef; public let p4ReceiptCommit: String; public let p4ReceiptBlob: String
    public init(ref: ModelArtifactRef, p4ReceiptCommit:String, p4ReceiptBlob:String) {
        precondition(ref.format == .litertlm); precondition(ref.license_plane == .modelWeights && ref.terms_state == .accepted)
        precondition(ref.sha256.count == 64 && ref.tokenizer_sha256?.count == 64); precondition(p4ReceiptCommit.count == 40 && p4ReceiptBlob.count == 40)
        self.ref=ref; self.p4ReceiptCommit=p4ReceiptCommit; self.p4ReceiptBlob=p4ReceiptBlob
    }
}

public enum RuntimeChunk: Sendable, Equatable { case text(String); case toolCandidate(id:String,name:String,arguments:[String:JSONValue],raw:String); case memoryPressure(String); case failure(String,retryable:Bool); case completed }
public protocol EmbeddedSession: AnyObject, Sendable { var observedBackend: BackendKind { get }; func chunks(for request: InferenceRequest) throws -> [RuntimeChunk]; func cancel(); func close() }
public protocol EmbeddedRuntime: Sendable { var runtimeID:String { get }; var runtimeRevision:String { get }; var supportedBackends:Set<BackendKind> { get }; func open(artifact:AdmittedArtifact,backend:BackendKind)throws->any EmbeddedSession }

public final class CancellationToken: @unchecked Sendable {
    private let lock=NSLock(); private var value=false
    public init(){}; public func cancel(){lock.lock();value=true;lock.unlock()}; public func isCancelled()->Bool{lock.lock();defer{lock.unlock()};return value}
}

public struct EmbeddedExecutionReceipt: Sendable, Equatable {
    public let requestID:String; public let traceID:String; public let runtimeID:String; public let runtimeRevision:String
    public let releaseTag:String; public let releaseCommitPrefix:String; public let swiftMaturity:ApiMaturity; public let releaseIntegrityState:ReleaseIntegrityState
    public let artifactSHA256:String; public let tokenizerSHA256:String; public let requestedBackend:BackendKind; public let selectedBackend:BackendKind; public let observedBackend:BackendKind
    public let fallbackReason:String?; public let p4ReceiptCommit:String; public let p4ReceiptBlob:String; public let terminalEvent:InferenceEventType
}
public struct AdapterExecution: Sendable, Equatable { public let events:[InferenceEvent]; public let receipt:EmbeddedExecutionReceipt? }
public enum AdapterError: Error, Equatable { case invalidRequest, uiThreadLoad, noBackend, unsupportedObservedBackend, releaseUnavailable, artifactMismatch }

public final class AppleLiteRtLmAdapter: Sendable {
    private let releasePin:LiteRtLmAppleReleasePin; private let runtime:any EmbeddedRuntime; private let providerID:String
    public init(releasePin:LiteRtLmAppleReleasePin,runtime:any EmbeddedRuntime,providerID:String="apple-litert-lm"){self.releasePin=releasePin;self.runtime=runtime;self.providerID=providerID}
    public func providerDescriptor()->ProviderDescriptor { ProviderDescriptor(provider_id:providerID,kind:.embeddedModel,maturity:.preview,task_kinds:[.chat,.summarize,.structuredGeneration,.functionCalling],supported_backends:runtime.supportedBackends.sorted{$0.rawValue<$1.rawValue},requires_network:false,terms_state:.reviewRequired) }
    public func selectBackend(_ requested:BackendKind)throws->(BackendKind,String?){ guard [.cpu,.gpu].contains(requested) else{throw AdapterError.noBackend}; if runtime.supportedBackends.contains(requested){return(requested,nil)}; if runtime.supportedBackends.contains(.cpu){return(.cpu,"requested backend unavailable; explicit CPU fallback")}; throw AdapterError.noBackend }
    public func execute(request:InferenceRequest,artifact:AdmittedArtifact,requestedBackend:BackendKind,isMainThread:Bool,cancellation:CancellationToken = .init())throws->AdapterExecution {
        guard releasePin.swiftMaturity == .preview, releasePin.integrityState != .unavailable else { throw AdapterError.releaseUnavailable }
        guard !isMainThread else { throw AdapterError.uiThreadLoad }
        guard request.schema == "ai-edge-tlm/inference-request/v1", !request.request_id.isEmpty, !request.trace_id.isEmpty, request.resource_budget.allow_network == false else { throw AdapterError.invalidRequest }
        guard let model=request.model_ref, model.sha256==artifact.ref.sha256, model.tokenizer_sha256==artifact.ref.tokenizer_sha256, model.terms_state == .accepted, model.format == .litertlm else { throw AdapterError.artifactMismatch }
        if cancellation.isCancelled(){return AdapterExecution(events:[cancelled(request,0,"cancelled before runtime open")],receipt:nil)}
        let (selected,fallback)=try selectBackend(requestedBackend); let session=try runtime.open(artifact:artifact,backend:selected); defer{session.close()}
        guard runtime.supportedBackends.contains(session.observedBackend), [.cpu,.gpu].contains(session.observedBackend) else { throw AdapterError.unsupportedObservedBackend }
        var events=[InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:0,type:.started)]; var sequence:Int64=1; var terminal=false
        for chunk in try session.chunks(for:request){
            if cancellation.isCancelled(){session.cancel();events.append(cancelled(request,sequence,"cancelled during generation"));terminal=true;break}
            switch chunk {
            case .text(let value): guard !value.isEmpty else { throw AdapterError.invalidRequest }; events.append(InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.tokenDelta,text_delta:value));sequence+=1
            case .toolCandidate(let id,let name,let args,let raw): guard !id.isEmpty && !name.isEmpty else{throw AdapterError.invalidRequest};events.append(InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.toolProposal,tool_proposal:ToolProposal(proposal_id:id,tool_name:name,arguments:args,model_output_digest:SHA256.hex(raw))));sequence+=1
            case .memoryPressure(let message): events.append(InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.failed,error:ErrorDetail(code:.resourceExhausted,message:message,retryable:false,provider_id:providerID)));terminal=true
            case .failure(let message,let retryable):events.append(InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.failed,error:ErrorDetail(code:.generationFailed,message:message,retryable:retryable,provider_id:providerID)));terminal=true
            case .completed:events.append(InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.completed,finish_reason:"stop"));terminal=true
            }
            if terminal{break}
        }
        if !terminal{events.append(InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.failed,error:ErrorDetail(code:.generationFailed,message:"runtime ended without terminal event",retryable:false,provider_id:providerID)))}
        return AdapterExecution(events:events,receipt:EmbeddedExecutionReceipt(requestID:request.request_id,traceID:request.trace_id,runtimeID:runtime.runtimeID,runtimeRevision:runtime.runtimeRevision,releaseTag:releasePin.tag,releaseCommitPrefix:releasePin.releaseCommitPrefix,swiftMaturity:releasePin.swiftMaturity,releaseIntegrityState:releasePin.integrityState,artifactSHA256:artifact.ref.sha256,tokenizerSHA256:artifact.ref.tokenizer_sha256!,requestedBackend:requestedBackend,selectedBackend:selected,observedBackend:session.observedBackend,fallbackReason:fallback,p4ReceiptCommit:artifact.p4ReceiptCommit,p4ReceiptBlob:artifact.p4ReceiptBlob,terminalEvent:events.last!.type))
    }
    private func cancelled(_ request:InferenceRequest,_ sequence:Int64,_ message:String)->InferenceEvent{InferenceEvent(schema:"ai-edge-tlm/inference-event/v1",request_id:request.request_id,sequence:sequence,type:.cancelled,error:ErrorDetail(code:.cancelled,message:message,retryable:false,provider_id:providerID))}
}
