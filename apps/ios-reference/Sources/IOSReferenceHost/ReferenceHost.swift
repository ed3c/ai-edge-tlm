import Foundation
import AIEdgeContracts

public enum ReferenceHostError: Error { case noOfflineProvider }
public struct HostAdmission: Sendable, Equatable { public let decision:String; public let effect:String; public let idempotencyKey:String? }

public struct ReferenceHost: Sendable {
    public init() {}
    public func selectProvider(system: ProviderDescriptor?, embedded: ProviderDescriptor) throws -> ProviderDescriptor {
        if let system, system.kind == .systemModel, system.requires_network == false { return system }
        guard embedded.kind == .embeddedModel, embedded.requires_network == false else { throw ReferenceHostError.noOfflineProvider }
        return embedded
    }
    public func admitProposal(_ proposal: ToolProposal, allowedTool:String, effect:String, confirmed:Bool) -> HostAdmission {
        if proposal.tool_name != allowedTool { return HostAdmission(decision:"DENY",effect:effect,idempotencyKey:nil) }
        if effect != "PURE" && !confirmed { return HostAdmission(decision:"REQUIRE_CONFIRMATION",effect:effect,idempotencyKey:nil) }
        return HostAdmission(decision:"ALLOW",effect:effect,idempotencyKey:"p8-\(proposal.proposal_id)")
    }
    public func goldenScenario() throws -> String {
        let embedded=ProviderDescriptor(provider_id:"embedded.fake",kind:.embeddedModel,maturity:.stable,task_kinds:[.functionCalling],supported_backends:[.cpu],requires_network:false,terms_state:.accepted)
        let selected=try selectProvider(system:nil,embedded:embedded)
        let proposal=ToolProposal(proposal_id:"proposal-1",tool_name:"save_note",arguments:["text":.string("hello")],model_output_digest:String(repeating:"a",count:64))
        let admission=admitProposal(proposal,allowedTool:"save_note",effect:"WRITE_LOCAL",confirmed:true)
        return "{\"network_allowed\":false,\"observed_backend\":\"CPU\",\"provider\":\"\(selected.provider_id)\",\"route\":\"EMBEDDED\",\"tool_decision\":\"\(admission.decision)\",\"tool_effect\":\"\(admission.effect)\",\"tool_name\":\"\(proposal.tool_name)\"}"
    }
}
