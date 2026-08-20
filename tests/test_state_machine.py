import pytest

from edge_tlm.state_machine import RequestState, RequestStateMachine


def test_happy_path():
    machine = RequestStateMachine()
    for state in [
        RequestState.CAPABILITY_PROBED,
        RequestState.POLICY_EVALUATED,
        RequestState.PROVIDER_SELECTED,
        RequestState.MODEL_READY,
        RequestState.SKILL_METADATA_MATCHED,
        RequestState.PLAN_COMPILED,
        RequestState.EXECUTING,
        RequestState.VALIDATING,
        RequestState.SUCCEEDED,
    ]:
        machine.transition(state, "test")
    assert machine.state is RequestState.SUCCEEDED
    assert len(machine.receipts) == 9


def test_invalid_transition_is_rejected():
    machine = RequestStateMachine()
    with pytest.raises(ValueError, match="invalid transition"):
        machine.transition(RequestState.SUCCEEDED, "skip gates")
