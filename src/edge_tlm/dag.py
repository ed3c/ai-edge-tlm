from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable, Mapping


class DagError(ValueError):
    pass


def topological_order(nodes: Iterable[Mapping[str, Any]]) -> list[str]:
    """Return a stable topological order and reject duplicate/missing/cyclic nodes."""
    by_id: dict[str, Mapping[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            raise DagError("node id is required")
        if node_id in by_id:
            raise DagError(f"duplicate node id: {node_id}")
        by_id[node_id] = node

    indegree = {node_id: 0 for node_id in by_id}
    children: dict[str, list[str]] = defaultdict(list)
    for node_id, node in by_id.items():
        for dep in node.get("dependencies", []):
            if dep not in by_id:
                raise DagError(f"node {node_id} depends on missing node {dep}")
            indegree[node_id] += 1
            children[dep].append(node_id)

    ready = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while ready:
        current = ready.popleft()
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if len(order) != len(by_id):
        blocked = sorted(node_id for node_id, degree in indegree.items() if degree > 0)
        raise DagError(f"cycle detected among: {', '.join(blocked)}")
    return order
