"""DAG validation helpers for PR162E dependency reports."""

from __future__ import annotations

from collections.abc import Mapping
import heapq

from .contracts import PluginPackageContractError, PluginPackageReasonCodeV1


def _canonical_node_id(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.IDENTITY_INVALID,
            f"{field_name} must be nonempty canonical text",
        )
    return value


def compile_selected_package_dependency_order_v1(
    node_ids: tuple[str, ...],
    dependency_edges: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    """Compile one deterministic dependency order with lexicographic Kahn."""

    if type(node_ids) is not tuple:
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "node_ids must be an exact tuple",
        )
    canonical_nodes = tuple(
        _canonical_node_id(node_id, "node_id") for node_id in node_ids
    )
    if len(canonical_nodes) != len(set(canonical_nodes)):
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.NODE_DUPLICATE,
            "node_ids contain a duplicate identity",
        )
    if type(dependency_edges) is not tuple:
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "dependency_edges must be an exact tuple",
        )

    node_set = set(canonical_nodes)
    seen_edges: set[tuple[str, str]] = set()
    indegree = {node_id: 0 for node_id in canonical_nodes}
    successors: dict[str, list[str]] = {node_id: [] for node_id in canonical_nodes}
    for raw_edge in dependency_edges:
        if type(raw_edge) is not tuple or len(raw_edge) != 2:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "each dependency edge must be an exact two-item tuple",
            )
        producer = _canonical_node_id(raw_edge[0], "edge producer")
        consumer = _canonical_node_id(raw_edge[1], "edge consumer")
        edge = (producer, consumer)
        if edge in seen_edges:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.EDGE_DUPLICATE,
                "dependency_edges contain a duplicate edge",
            )
        seen_edges.add(edge)
        if producer not in node_set or consumer not in node_set:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE,
                "dependency edge references an unknown node",
            )
        if producer == consumer:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.SELF_EDGE,
                "dependency edge may not reference itself",
            )
        indegree[consumer] += 1
        successors[producer].append(consumer)

    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    emitted: list[str] = []
    while ready:
        node_id = heapq.heappop(ready)
        emitted.append(node_id)
        for successor in sorted(successors[node_id]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(ready, successor)
    if len(emitted) != len(canonical_nodes):
        blocked = tuple(sorted(node_id for node_id, degree in indegree.items() if degree))
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.DEPENDENCY_CYCLE,
            f"dependency cycle blocks nodes: {','.join(blocked)}",
        )
    return tuple(emitted)


def _legacy_dependency_graph(
    nodes: list[dict[str, object]],
) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    if type(nodes) is not list:
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "legacy dependency rows must be an exact list",
        )
    node_ids: list[str] = []
    edges: list[tuple[str, str]] = []
    for row in nodes:
        if not isinstance(row, Mapping) or "node_id" not in row:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "legacy dependency row must contain node_id",
            )
        node_id = _canonical_node_id(row["node_id"], "node_id")
        node_ids.append(node_id)
        dependencies = row.get("dependency_node_ids", ())
        if "dependency_node_ids" in row and type(dependencies) not in {list, tuple}:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "dependency_node_ids must be a list or tuple when present",
            )
        parsed_dependencies = tuple(
            _canonical_node_id(dependency, "dependency_node_id")
            for dependency in dependencies
        )
        if len(parsed_dependencies) != len(set(parsed_dependencies)):
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.EDGE_DUPLICATE,
                "legacy dependency row contains a duplicate dependency",
            )
        edges.extend((dependency, node_id) for dependency in parsed_dependencies)
    return tuple(node_ids), tuple(edges)


def topological_order(nodes: list[dict[str, object]]) -> list[str]:
    node_ids, edges = _legacy_dependency_graph(nodes)
    return list(compile_selected_package_dependency_order_v1(node_ids, edges))


def has_cycle(nodes: list[dict[str, object]]) -> bool:
    node_ids, edges = _legacy_dependency_graph(nodes)
    try:
        compile_selected_package_dependency_order_v1(node_ids, edges)
    except PluginPackageContractError as exc:
        if exc.reason_code is PluginPackageReasonCodeV1.DEPENDENCY_CYCLE:
            return True
        raise
    return False
