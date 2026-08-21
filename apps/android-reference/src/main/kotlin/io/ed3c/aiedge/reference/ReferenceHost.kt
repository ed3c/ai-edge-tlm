package io.ed3c.aiedge.reference

import io.ed3c.aiedge.contracts.v1.*

data class HostAdmission(val decision: String, val effect: String, val idempotencyKey: String?)

class ReferenceHost {
    fun selectProvider(system: ProviderDescriptor?, embedded: ProviderDescriptor): ProviderDescriptor {
        if (system != null && system.kind == ProviderKind.SYSTEM_MODEL && !system.requires_network) return system
        require(embedded.kind == ProviderKind.EMBEDDED_MODEL && !embedded.requires_network) { "offline embedded provider required" }
        return embedded
    }

    fun admitProposal(proposal: ToolProposal, allowedTool: String, effect: String, confirmed: Boolean): HostAdmission {
        if (proposal.tool_name != allowedTool) return HostAdmission("DENY", effect, null)
        if (effect != "PURE" && !confirmed) return HostAdmission("REQUIRE_CONFIRMATION", effect, null)
        return HostAdmission("ALLOW", effect, "p8-${proposal.proposal_id}")
    }

    fun goldenScenario(): String {
        val embedded = ProviderDescriptor("embedded.fake", ProviderKind.EMBEDDED_MODEL, ApiMaturity.STABLE, listOf(TaskKind.FUNCTION_CALLING), listOf(BackendKind.CPU), false, TermsState.ACCEPTED)
        val selected = selectProvider(null, embedded)
        val proposal = ToolProposal("proposal-1", "save_note", mapOf("text" to JsonString("hello")), "a".repeat(64))
        val admission = admitProposal(proposal, "save_note", "WRITE_LOCAL", true)
        return "{\"network_allowed\":false,\"observed_backend\":\"CPU\",\"provider\":\"${selected.provider_id}\",\"route\":\"EMBEDDED\",\"tool_decision\":\"${admission.decision}\",\"tool_effect\":\"${admission.effect}\",\"tool_name\":\"${proposal.tool_name}\"}"
    }
}
