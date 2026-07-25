"""Typed dependency-DAG compilation, closure, units, timing, and failure propagation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .context import exact_decimal
from .errors import DependencyGraphError, ReasonCode
from .models import DependencyEdgeV1, DependencyNodeV1


@dataclass(frozen=True, slots=True)
class UnitConversionV1:
    supplied_unit: str
    required_unit: str
    factor: Decimal

    def __post_init__(self) -> None:
        if (
            not isinstance(self.supplied_unit, str)
            or not self.supplied_unit
            or not isinstance(self.required_unit, str)
            or not self.required_unit
        ):
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_UNIT_MISMATCH,
                "conversion units are required",
            )
        value = exact_decimal(self.factor, field_name="factor")
        if value <= 0:
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_UNIT_MISMATCH,
                "conversion factor must be positive",
            )
        object.__setattr__(self, "factor", value)


@dataclass(frozen=True, slots=True)
class CompiledDependencyGraphV1:
    nodes: tuple[DependencyNodeV1, ...]
    edges: tuple[DependencyEdgeV1, ...]
    topological_order: tuple[str, ...]
    conversions: tuple[UnitConversionV1, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, tuple) or any(
            not isinstance(node, DependencyNodeV1) for node in self.nodes
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "compiled dependency nodes must be typed immutable values",
            )
        if not isinstance(self.edges, tuple) or any(
            not isinstance(edge, DependencyEdgeV1) for edge in self.edges
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "compiled dependency edges must be typed immutable values",
            )
        if not isinstance(self.conversions, tuple) or any(
            not isinstance(item, UnitConversionV1) for item in self.conversions
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "compiled conversions must be typed immutable values",
            )
        node_ids = tuple(node.node_id for node in self.nodes)
        if (
            not isinstance(self.topological_order, tuple)
            or set(self.topological_order) != set(node_ids)
            or len(self.topological_order) != len(node_ids)
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "topological order must contain every node exactly once",
            )

    def selected_closure(self, selected_ids: tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(selected_ids, tuple) or any(
            not isinstance(item, str) or not item for item in selected_ids
        ) or len(set(selected_ids)) != len(selected_ids):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "selected dependency ids must be an immutable string tuple",
            )
        known = {node.node_id for node in self.nodes}
        unknown = set(selected_ids) - known
        if unknown:
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_UNKNOWN,
                f"unknown selected dependencies: {sorted(unknown)}",
            )
        required = set(selected_ids)
        changed = True
        while changed:
            changed = False
            for edge in self.edges:
                if edge.downstream_id in required and edge.upstream_id not in required:
                    required.add(edge.upstream_id)
                    changed = True
        return tuple(item for item in self.topological_order if item in required)

    def propagate_failures(self, failed_ids: tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(failed_ids, tuple) or any(
            not isinstance(item, str) or not item for item in failed_ids
        ) or len(set(failed_ids)) != len(failed_ids):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "failed dependency ids must be an immutable string tuple",
            )
        unknown = set(failed_ids) - {node.node_id for node in self.nodes}
        if unknown:
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_UNKNOWN,
                f"unknown failed dependencies: {sorted(unknown)}",
            )
        impacted = set(failed_ids)
        changed = True
        while changed:
            changed = False
            for edge in self.edges:
                if edge.upstream_id in impacted and edge.downstream_id not in impacted:
                    impacted.add(edge.downstream_id)
                    changed = True
        return tuple(item for item in self.topological_order if item in impacted)


class DependencyGraphCompilerV1:
    _TIMING_ORDER = {
        "POINT_IN_TIME": 0,
        "SNAPSHOT": 1,
        "NEARLINE": 2,
        "OFFLINE": 3,
    }

    @classmethod
    def compile(
        cls,
        nodes: tuple[DependencyNodeV1, ...],
        edges: tuple[DependencyEdgeV1, ...],
        conversions: tuple[UnitConversionV1, ...] = (),
    ) -> CompiledDependencyGraphV1:
        if not isinstance(nodes, tuple) or any(
            not isinstance(node, DependencyNodeV1) for node in nodes
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "dependency nodes must be typed immutable values",
            )
        if not isinstance(edges, tuple) or any(
            not isinstance(edge, DependencyEdgeV1) for edge in edges
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "dependency edges must be typed immutable values",
            )
        if not isinstance(conversions, tuple) or any(
            not isinstance(item, UnitConversionV1) for item in conversions
        ):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "unit conversions must be typed immutable values",
            )
        by_id = {node.node_id: node for node in nodes}
        if len(by_id) != len(nodes):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT, "dependency node ids must be unique"
            )
        conversion_keys = {
            (item.supplied_unit, item.required_unit) for item in conversions
        }
        if len(conversion_keys) != len(conversions):
            raise DependencyGraphError(
                ReasonCode.INVALID_CONTRACT,
                "unit conversion pairs must be unique",
            )
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in by_id}
        indegree = {node_id: 0 for node_id in by_id}
        seen_edges: set[tuple[str, str]] = set()
        for edge in edges:
            if edge.upstream_id not in by_id or edge.downstream_id not in by_id:
                raise DependencyGraphError(
                    ReasonCode.DEPENDENCY_UNKNOWN,
                    f"edge references an unknown node: {edge}",
                )
            key = (edge.upstream_id, edge.downstream_id)
            if key in seen_edges:
                raise DependencyGraphError(
                    ReasonCode.INVALID_CONTRACT, f"duplicate dependency edge: {key}"
                )
            seen_edges.add(key)
            if (
                edge.supplied_unit != edge.required_unit
                and (edge.supplied_unit, edge.required_unit) not in conversion_keys
            ):
                raise DependencyGraphError(
                    ReasonCode.DEPENDENCY_UNIT_MISMATCH,
                    f"no declared conversion for {edge.supplied_unit} -> "
                    f"{edge.required_unit}",
                )
            upstream_timing = by_id[edge.upstream_id].timing_class
            downstream_timing = edge.timing_class
            if (
                upstream_timing not in cls._TIMING_ORDER
                or downstream_timing not in cls._TIMING_ORDER
                or cls._TIMING_ORDER[upstream_timing]
                > cls._TIMING_ORDER[downstream_timing]
            ):
                raise DependencyGraphError(
                    ReasonCode.DEPENDENCY_TIMING_MISMATCH,
                    f"{upstream_timing} cannot satisfy {downstream_timing}",
                )
            outgoing[edge.upstream_id].append(edge.downstream_id)
            indegree[edge.downstream_id] += 1

        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        ordered: list[str] = []
        while ready:
            node_id = ready.pop(0)
            ordered.append(node_id)
            for downstream in sorted(outgoing[node_id]):
                indegree[downstream] -= 1
                if indegree[downstream] == 0:
                    ready.append(downstream)
                    ready.sort()
        if len(ordered) != len(nodes):
            cyclic = sorted(node_id for node_id, degree in indegree.items() if degree)
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_CYCLE,
                f"dependency cycle detected: {cyclic}",
            )
        return CompiledDependencyGraphV1(
            nodes=nodes,
            edges=edges,
            topological_order=tuple(ordered),
            conversions=conversions,
        )
