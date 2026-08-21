import Testing
import AIEdgeContracts
@testable import IOSReferenceHost

@Test func embeddedFallbackAndToolAdmission() throws {
    let value = try ReferenceHost().goldenScenario()
    #expect(value.contains("\"provider\":\"embedded.fake\""))
    #expect(value.contains("\"tool_decision\":\"ALLOW\""))
    #expect(value.contains("\"network_allowed\":false"))
}
