import pytest

from edge_tlm.dag import DagError, topological_order


def test_topological_order_is_stable():
    nodes = [
        {"id": "b", "dependencies": ["a"]},
        {"id": "c", "dependencies": ["a"]},
        {"id": "a", "dependencies": []},
    ]
    assert topological_order(nodes) == ["a", "b", "c"]


def test_missing_dependency_fails_closed():
    with pytest.raises(DagError, match="missing"):
        topological_order([{"id": "b", "dependencies": ["a"]}])


def test_cycle_fails_closed():
    with pytest.raises(DagError, match="cycle"):
        topological_order([
            {"id": "a", "dependencies": ["b"]},
            {"id": "b", "dependencies": ["a"]},
        ])
