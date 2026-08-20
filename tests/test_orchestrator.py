from edge_tlm.orchestrator import DeterministicOrchestrator
from edge_tlm.policy import ProviderCandidate, Requirements
from edge_tlm.state_machine import RequestState


def test_orchestrator_executes_host_compiled_order():
    calls = []
    nodes = [
        {"id": "parse", "dependencies": []},
        {"id": "validate", "dependencies": ["parse"]},
    ]

    def execute(node_id, inputs):
        calls.append(node_id)
        return {"node": node_id, "inputs": sorted(inputs)}

    result = DeterministicOrchestrator().run(
        requirements=Requirements(True, "local-only", False),
        candidates=[ProviderCandidate("embedded", True, True, frozenset({"text"}), "stable", 0)],
        pipeline_nodes=nodes,
        execute_step=execute,
    )
    assert result.state is RequestState.SUCCEEDED
    assert calls == ["parse", "validate"]


def test_orchestrator_does_not_silently_fallback():
    result = DeterministicOrchestrator().run(
        requirements=Requirements(True, "local-only", False),
        candidates=[ProviderCandidate("cloud", True, False, frozenset({"text"}), "stable", 0)],
        pipeline_nodes=[{"id": "parse", "dependencies": []}],
        execute_step=lambda *_: {},
    )
    assert result.state is RequestState.REJECTED
    assert result.provider_id is None
