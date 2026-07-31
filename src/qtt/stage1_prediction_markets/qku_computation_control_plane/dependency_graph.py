"""Typed dependency-DAG compilation, closure, units, timing, and failure propagation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

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


class FrozenDependencyKindV1(StrEnum):
    DATA_FLOW_EDGE = "DATA_FLOW_EDGE"
    CALLABLE_OR_SUBROUTINE_DEPENDENCY = "CALLABLE_OR_SUBROUTINE_DEPENDENCY"
    SHARED_POLICY_OR_METHOD_DEPENDENCY = "SHARED_POLICY_OR_METHOD_DEPENDENCY"


@dataclass(frozen=True, slots=True)
class FrozenDependencyRelationshipV1:
    edge_id: str
    kind: FrozenDependencyKindV1
    producer_math_spec_id: str
    consumer_math_spec_id: str
    producer_output_field: str
    producer_output_schema_ref: str
    consumer_input_field: str | None
    conversion_ref: str
    point_in_time_rule: str
    type_shape_unit_basis_rule: str
    failure_route: str
    consumer_call_site: str | None = None
    producer_version_ref: str = "FROZEN_V3_4"
    consumer_version_ref: str = "FROZEN_V3_4"
    terminal_state: str = "EXACT_EDGE_CLOSED"

    def __post_init__(self) -> None:
        required = (
            self.edge_id,
            self.producer_math_spec_id,
            self.consumer_math_spec_id,
            self.producer_output_field,
            self.producer_output_schema_ref,
            self.conversion_ref,
            self.point_in_time_rule,
            self.type_shape_unit_basis_rule,
            self.failure_route,
        )
        if any(not isinstance(value, str) or not value for value in required):
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_UNKNOWN,
                "frozen dependency relationship is incomplete",
            )
        if self.kind is FrozenDependencyKindV1.DATA_FLOW_EDGE:
            if not self.consumer_input_field or self.consumer_call_site is not None:
                raise DependencyGraphError(
                    ReasonCode.DEPENDENCY_UNKNOWN,
                    "data flow requires one consumer field and no callable fiction",
                )
        elif not self.consumer_call_site or self.consumer_input_field is not None:
            raise DependencyGraphError(
                ReasonCode.DEPENDENCY_UNKNOWN,
                "callable/policy lineage cannot invent a consumer data field",
            )


_FROZEN_DEPENDENCY_RELATIONSHIPS = (
    FrozenDependencyRelationshipV1(
        edge_id="EDGE::MATH-01::MATH-02",
        kind=FrozenDependencyKindV1.DATA_FLOW_EDGE,
        producer_math_spec_id="MATH-01",
        consumer_math_spec_id="MATH-02",
        producer_output_field="implied_probability",
        producer_output_schema_ref="MATH-01::OUTPUT",
        consumer_input_field="market_implied_probability",
        conversion_ref="CONVERSION::DECIMAL_PROBABILITY_TO_FINITE_FLOAT64_V1",
        point_in_time_rule="SAME_CONTEXT_SNAPSHOT",
        type_shape_unit_basis_rule=(
            "Decimal scalar probability -> float64 scalar probability through "
            "EXACT_DECIMAL_TO_FINITE_FLOAT64_PROBABILITY_ADAPTER_V1"
        ),
        failure_route="DEPENDENCY_UNRESOLVED_BLOCK_CONTEXT_AND_STACK",
    ),
    FrozenDependencyRelationshipV1(
        edge_id="EDGE::MATH-03::MATH-05",
        kind=FrozenDependencyKindV1.CALLABLE_OR_SUBROUTINE_DEPENDENCY,
        producer_math_spec_id="MATH-03",
        consumer_math_spec_id="MATH-05",
        producer_output_field="midpoint",
        producer_output_schema_ref="MATH-03::OUTPUT",
        consumer_input_field=None,
        conversion_ref="NOT_APPLICABLE_WITH_TYPED_REASON",
        point_in_time_rule="SAME_BOOK_SNAPSHOT",
        type_shape_unit_basis_rule="NO_INTER_FORMULA_DATA_FIELD; procedure reuse only",
        failure_route="SUBROUTINE_FAILURE_BLOCKS_MATH_05",
        consumer_call_site=(
            "MATH-05.relative_spread_from_raw_book invokes registered MATH-03 "
            "procedure with its own best_bid,best_ask,payout inputs"
        ),
    ),
    FrozenDependencyRelationshipV1(
        edge_id="EDGE::MATH-04::MATH-05",
        kind=FrozenDependencyKindV1.CALLABLE_OR_SUBROUTINE_DEPENDENCY,
        producer_math_spec_id="MATH-04",
        consumer_math_spec_id="MATH-05",
        producer_output_field="full_spread",
        producer_output_schema_ref="MATH-04::OUTPUT",
        consumer_input_field=None,
        conversion_ref="NOT_APPLICABLE_WITH_TYPED_REASON",
        point_in_time_rule="SAME_BOOK_SNAPSHOT",
        type_shape_unit_basis_rule="NO_INTER_FORMULA_DATA_FIELD; procedure reuse only",
        failure_route="SUBROUTINE_FAILURE_BLOCKS_MATH_05",
        consumer_call_site=(
            "MATH-05.relative_spread_from_raw_book invokes registered MATH-04 "
            "procedure with its own best_bid,best_ask,payout inputs"
        ),
    ),
    FrozenDependencyRelationshipV1(
        edge_id="EDGE::MATH-17::MATH-18",
        kind=FrozenDependencyKindV1.CALLABLE_OR_SUBROUTINE_DEPENDENCY,
        producer_math_spec_id="MATH-17",
        consumer_math_spec_id="MATH-18",
        producer_output_field="probabilistic_sharpe_ratio",
        producer_output_schema_ref="MATH-17::OUTPUT",
        consumer_input_field=None,
        conversion_ref="NOT_APPLICABLE_WITH_TYPED_REASON",
        point_in_time_rule="SAME_EVIDENCE_WINDOW_AND_SHARPE_BASIS",
        type_shape_unit_basis_rule=(
            "NO_INTER_FORMULA_DATA_FIELD; shared registered PSR procedure"
        ),
        failure_route="SUBROUTINE_FAILURE_BLOCKS_MATH_18",
        consumer_call_site=(
            "MATH-18 computes the same PSR normal-CDF subroutine against the "
            "deflated reference threshold; no MATH-17 result packet is an input"
        ),
    ),
    FrozenDependencyRelationshipV1(
        edge_id="EDGE::MATH-20::MATH-21",
        kind=FrozenDependencyKindV1.SHARED_POLICY_OR_METHOD_DEPENDENCY,
        producer_math_spec_id="MATH-20",
        consumer_math_spec_id="MATH-21",
        producer_output_field="folds",
        producer_output_schema_ref="MATH-20::OUTPUT",
        consumer_input_field=None,
        conversion_ref="NOT_APPLICABLE_WITH_TYPED_REASON",
        point_in_time_rule="SAME_INTERVAL_LEDGER_AND_DECISION_TIME",
        type_shape_unit_basis_rule=(
            "SHARED_POLICY_ONLY; CPCV constructs its own split records from raw "
            "intervals and group parameters"
        ),
        failure_route="POLICY_RESOLUTION_FAILURE_BLOCKS_MATH_21",
        consumer_call_site=(
            "MATH-21 applies the frozen MATH-20 half-open interval overlap, "
            "purge, and time-duration embargo law to each CPCV split"
        ),
    ),
    FrozenDependencyRelationshipV1(
        edge_id="EDGE::MATH-46::MATH-47",
        kind=FrozenDependencyKindV1.CALLABLE_OR_SUBROUTINE_DEPENDENCY,
        producer_math_spec_id="MATH-46",
        consumer_math_spec_id="MATH-47",
        producer_output_field="canonical_qubo",
        producer_output_schema_ref="MATH-46::OUTPUT",
        consumer_input_field=None,
        conversion_ref="MATH46RawQuboCanonicalizationAdapterV1",
        point_in_time_rule="SAME_FORMULATION_VERSION_AND_OBJECTIVE_SCALE_RECEIPT",
        type_shape_unit_basis_rule=(
            "IMMUTABLE_RAW_FIELD_ADAPTER_OUTPUTS_CANONICAL_QUBO_MODEL_V1; "
            "no undeclared data field"
        ),
        failure_route="DEPENDENCY_UNRESOLVED_BLOCK_CONTEXT_AND_STACK",
        consumer_call_site=(
            "MATH-47 invokes MATH46RawQuboCanonicalizationAdapterV1 over its "
            "declared raw representation/diagonal/upper/full/constant inputs "
            "before the Ising transform"
        ),
    ),
)

FROZEN_DEPENDENCY_RELATIONSHIPS: Mapping[
    str, FrozenDependencyRelationshipV1
] = MappingProxyType(
    {edge.edge_id: edge for edge in _FROZEN_DEPENDENCY_RELATIONSHIPS}
)
if (
    len(FROZEN_DEPENDENCY_RELATIONSHIPS) != 6
    or sum(
        edge.kind is FrozenDependencyKindV1.DATA_FLOW_EDGE
        for edge in FROZEN_DEPENDENCY_RELATIONSHIPS.values()
    )
    != 1
    or sum(
        edge.kind is FrozenDependencyKindV1.CALLABLE_OR_SUBROUTINE_DEPENDENCY
        for edge in FROZEN_DEPENDENCY_RELATIONSHIPS.values()
    )
    != 4
    or sum(
        edge.kind is FrozenDependencyKindV1.SHARED_POLICY_OR_METHOD_DEPENDENCY
        for edge in FROZEN_DEPENDENCY_RELATIONSHIPS.values()
    )
    != 1
):
    raise DependencyGraphError(
        ReasonCode.DEPENDENCY_UNKNOWN,
        "v3.4 requires exactly 1 data, 4 callable, and 1 shared-policy relationship",
    )
