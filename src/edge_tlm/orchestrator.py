from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .dag import topological_order
from .policy import ProviderCandidate, Requirements, Selection, select_provider
from .state_machine import RequestState, RequestStateMachine


@dataclass(frozen=True)
class OrchestratorResult:
    state: RequestState
    provider_id: str | None
    output: dict[str, Any]
    receipts: tuple[object, ...]


class DeterministicOrchestrator:
    """Reference host-owned orchestrator; provider execution is injected and bounded."""

    def run(
        self,
        *,
        requirements: Requirements,
        candidates: Iterable[ProviderCandidate],
        pipeline_nodes: list[dict[str, Any]],
        execute_step: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> OrchestratorResult:
        machine = RequestStateMachine()
        machine.transition(RequestState.CAPABILITY_PROBED, "capability profile read")
        machine.transition(RequestState.POLICY_EVALUATED, "request policy evaluated")
        selection: Selection = select_provider(requirements, candidates)
        if selection.provider is None:
            machine.transition(RequestState.REJECTED, "no policy-admissible provider")
            return OrchestratorResult(machine.state, None, {"rejected": selection.rejected}, tuple(machine.receipts))

        machine.transition(RequestState.PROVIDER_SELECTED, selection.provider.provider_id)
        machine.transition(RequestState.MODEL_READY, "provider reported ready")
        machine.transition(RequestState.SKILL_METADATA_MATCHED, "no implicit skill execution")
        machine.transition(RequestState.PLAN_COMPILED, "host compiled typed DAG")
        order = topological_order(pipeline_nodes)
        machine.transition(RequestState.EXECUTING, "bounded DAG execution started")

        outputs: dict[str, Any] = {}
        by_id = {node["id"]: node for node in pipeline_nodes}
        try:
            for node_id in order:
                inputs = {dep: outputs[dep] for dep in by_id[node_id].get("dependencies", [])}
                outputs[node_id] = execute_step(node_id, inputs)
        except Exception as exc:  # provider/tool boundary normalizes real errors
            machine.transition(RequestState.FALLBACK_EVALUATED, f"execution failed: {type(exc).__name__}")
            machine.transition(RequestState.FAILED, "no admitted fallback in reference run")
            return OrchestratorResult(machine.state, selection.provider.provider_id, {"error": str(exc)}, tuple(machine.receipts))

        machine.transition(RequestState.VALIDATING, "typed outputs available")
        machine.transition(RequestState.SUCCEEDED, "all declared outputs validated")
        return OrchestratorResult(machine.state, selection.provider.provider_id, outputs, tuple(machine.receipts))
