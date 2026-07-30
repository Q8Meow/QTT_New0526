"""Exact dependency closure and sole registered MATH-01 -> MATH-02 stack."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from .bindings import (
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FormulaInputAdmissionClassV1,
    FormulaInputAuthorityBindingV1,
)
from .dependency_graph import (
    FROZEN_DEPENDENCY_RELATIONSHIPS,
    FrozenDependencyKindV1,
    FrozenDependencyRelationshipV1,
)
from .errors import (
    FreshnessError,
    InputAuthorityError,
    PointInTimeError,
    ReasonCode,
    StackResolutionError,
)
from .implementation_registry import IMPLEMENTATION_REGISTRY, invoke_formula_v34
from .input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    FormulaInputResolutionV1,
    FormulaInputResolverV1,
    OwnerValuePacketV1,
    _resolve_formula_input_binding,
    _validate_formula_input_context,
)
from .models import (
    ComputationExecutionContextV1,
    ImplementationVersionPinV1,
)
from .oracle_contracts import GOLDEN_VECTOR_BY_MATH_ID, ORACLE_BY_MATH_ID
from .point_in_time import PointInTimeClocksV1
from .specification import (
    FROZEN_FORMULA_INPUT_CONTRACTS,
    FROZEN_FORMULA_REQUIREMENTS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from .unit_conversion import (
    ConversionIdentityV1,
    UnitBasisDescriptorV1,
    UnitConversionOwnerV1,
    UnitConversionReceiptV1,
)


@dataclass(frozen=True, slots=True)
class RegisteredFormulaStackV1:
    stack_id: str
    component_ids: tuple[str, ...]
    data_edge_id: str
    stack_version: str
    current_mode_admission: str

    def __post_init__(self) -> None:
        if (
            self.stack_id != "STACK::MATH-01::MATH-02::V3_4"
            or self.component_ids != ("MATH-01", "MATH-02")
            or self.data_edge_id != "EDGE::MATH-01::MATH-02"
            or self.stack_version != "3.4"
            or self.current_mode_admission
            != "CONTRACT_AND_FIXTURE_ONLY_NO_MODE_ACTIVATION"
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "registered stack differs from the sole frozen data-flow stack",
            )


REGISTERED_FORMULA_STACKS: Mapping[str, RegisteredFormulaStackV1] = (
    MappingProxyType(
        {
            "STACK::MATH-01::MATH-02::V3_4": RegisteredFormulaStackV1(
                stack_id="STACK::MATH-01::MATH-02::V3_4",
                component_ids=("MATH-01", "MATH-02"),
                data_edge_id="EDGE::MATH-01::MATH-02",
                stack_version="3.4",
                current_mode_admission=(
                    "CONTRACT_AND_FIXTURE_ONLY_NO_MODE_ACTIVATION"
                ),
            )
        }
    )
)


@dataclass(frozen=True, slots=True)
class _StackComponentContextClosureV1:
    math_spec_id: str
    blocker_reasons: tuple[ReasonCode, ...]
    resolved_external_input_receipt_refs: tuple[str, ...]
    dependency_producible_input_refs: tuple[str, ...]
    dependency_edge_refs: tuple[str, ...]
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            not self.math_spec_id
            or not isinstance(self.blocker_reasons, tuple)
            or any(
                not isinstance(reason, ReasonCode)
                for reason in self.blocker_reasons
            )
            or len(set(self.blocker_reasons)) != len(self.blocker_reasons)
            or any(
                not isinstance(ref, str) or not ref
                for refs in (
                    self.resolved_external_input_receipt_refs,
                    self.dependency_producible_input_refs,
                    self.dependency_edge_refs,
                )
                for ref in refs
            )
            or self.no_authority_flag is not True
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "component context-preflight closure is malformed",
            )

    @property
    def context_computable(self) -> bool:
        return not self.blocker_reasons

    @property
    def receipt_refs(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    *self.resolved_external_input_receipt_refs,
                    *self.dependency_producible_input_refs,
                    *self.dependency_edge_refs,
                )
            )
        )


@dataclass(frozen=True, slots=True)
class _SelectedStackContextClosureV1:
    execution_context: ComputationExecutionContextV1
    stack_id: str
    stack_version: str
    component_ids: tuple[str, ...]
    component_closures: tuple[_StackComponentContextClosureV1, ...]
    full_stack_blocker_reasons: tuple[ReasonCode, ...]
    resolved_external_input_receipt_refs: tuple[str, ...]
    dependency_producible_input_refs: tuple[str, ...]
    dependency_edge_refs: tuple[str, ...]
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or self.execution_context.dependency_graph_id != self.stack_id
            or self.execution_context.dependency_graph_version
            != self.stack_version
            or tuple(
                closure.math_spec_id for closure in self.component_closures
            )
            != self.component_ids
            or tuple(
                dict.fromkeys(
                    reason
                    for closure in self.component_closures
                    for reason in closure.blocker_reasons
                )
            )
            != self.full_stack_blocker_reasons
            or any(
                closure.no_authority_flag is not True
                for closure in self.component_closures
            )
            or self.no_authority_flag is not True
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "selected-stack context-preflight closure is malformed",
            )

    @property
    def stack_computable(self) -> bool:
        return not self.full_stack_blocker_reasons

    @property
    def closure_ref(self) -> str:
        return (
            f"NO_EXECUTION_STACK_CLOSURE::{self.stack_id}::"
            f"{self.stack_version}::{self.execution_context.context_id}::"
            f"{self.execution_context.scope.input_snapshot_id}::"
            f"{self.execution_context.input_version}"
        )

    @property
    def receipt_refs(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    self.closure_ref,
                    *self.resolved_external_input_receipt_refs,
                    *self.dependency_producible_input_refs,
                    *self.dependency_edge_refs,
                )
            )
        )

    def component_for(
        self, math_spec_id: str
    ) -> _StackComponentContextClosureV1 | None:
        return next(
            (
                closure
                for closure in self.component_closures
                if closure.math_spec_id == math_spec_id
            ),
            None,
        )


@dataclass(frozen=True, slots=True)
class DependencyValuePropagationReceiptV1:
    receipt_id: str
    edge_id: str
    producer_math_spec_id: str
    producer_implementation_id: str
    producer_output_schema_ref: str
    producer_output_field: str
    consumer_math_spec_id: str
    consumer_implementation_id: str
    consumer_input_field: str
    producer_value: Decimal
    consumer_value: float
    execution_context: ComputationExecutionContextV1
    conversion_receipt_id: str
    mutation_propagates: bool = True
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            self.edge_id != "EDGE::MATH-01::MATH-02"
            or self.producer_math_spec_id != "MATH-01"
            or self.consumer_math_spec_id != "MATH-02"
            or self.producer_output_field != "implied_probability"
            or self.consumer_input_field != "market_implied_probability"
            or not isinstance(self.producer_value, Decimal)
            or not isinstance(self.consumer_value, float)
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or not self.conversion_receipt_id
            or self.mutation_propagates is not True
            or self.no_authority_flag is not True
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "data-flow propagation receipt is incomplete or fabricated",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


@dataclass(frozen=True, slots=True)
class FormulaStackExecutionV1:
    stack: RegisteredFormulaStackV1
    execution_context: ComputationExecutionContextV1
    component_inputs: tuple[FormulaInputResolutionV1, ...]
    component_outputs: tuple[object, ...]
    dependency_packet: OwnerValuePacketV1
    conversion_receipt: UnitConversionReceiptV1
    propagation_receipt: DependencyValuePropagationReceiptV1
    receipt_refs: tuple[str, ...]
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or len(self.component_inputs) != 2
            or len(self.component_outputs) != 2
            or self.component_inputs[0].math_spec_id != "MATH-01"
            or self.component_inputs[1].math_spec_id != "MATH-02"
            or not isinstance(self.dependency_packet, OwnerValuePacketV1)
            or self.dependency_packet.context_id
            != self.execution_context.context_id
            or self.dependency_packet.clocks.as_of_time
            != self.execution_context.as_of
            or self.dependency_packet.source_epoch_id
            != self.execution_context.source_epoch_id
            or self.dependency_packet.input_version
            != self.execution_context.input_version
            or self.dependency_packet.scope != self.execution_context.scope
            or any(
                resolution.execution_context is not self.execution_context
                for resolution in self.component_inputs
            )
            or self.conversion_receipt.execution_context
            is not self.execution_context
            or self.propagation_receipt.execution_context
            is not self.execution_context
            or self.propagation_receipt.conversion_receipt_id
            != self.conversion_receipt.receipt_id
            or self.no_authority_flag is not True
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "stack execution is not dependency-closed",
            )


class ApplicableStackResolverV1:
    """Resolve exactly one stack; every other formula remains an individual route."""

    @staticmethod
    def resolve(
        *,
        stack_id: str,
        stack_version: str,
        component_ids: tuple[str, ...],
    ) -> RegisteredFormulaStackV1:
        try:
            stack = REGISTERED_FORMULA_STACKS[stack_id]
        except KeyError as exc:
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                f"no registered formula stack exists for {stack_id}",
            ) from exc
        if component_ids != stack.component_ids:
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                "requested component sequence differs from the exact registered stack",
            )
        if stack_version != stack.stack_version:
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                "requested dependency graph version is not the registered stack version",
            )
        return stack

    @staticmethod
    def execute(
        *,
        stack_id: str,
        component_ids: tuple[str, ...],
        context: ComputationExecutionContextV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertions_by_math_id: Mapping[
            str, Mapping[str, object]
        ] | None = None,
    ) -> FormulaStackExecutionV1:
        if (
            not isinstance(context, ComputationExecutionContextV1)
            or context.dependency_graph_id != stack_id
            or context.dependency_graph_version is None
        ):
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                "stack execution requires the exact context dependency graph",
            )
        stack = ApplicableStackResolverV1.resolve(
            stack_id=stack_id,
            stack_version=context.dependency_graph_version,
            component_ids=component_ids,
        )
        expected_pins = tuple(
            ImplementationVersionPinV1(
                math_spec_id=component_id,
                implementation_id=IMPLEMENTATION_REGISTRY[
                    component_id
                ].contract.implementation_id,
            )
            for component_id in stack.component_ids
        )
        if context.implementation_versions != expected_pins:
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "stack implementation pins differ from the ordered registered components",
            )
        assertions = caller_assertions_by_math_id or MappingProxyType({})
        unknown = set(assertions) - set(stack.component_ids)
        if unknown:
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                f"stack assertions contain unknown components: {sorted(unknown)}",
            )
        math_01_inputs = FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=owner_registry,
            caller_assertions=assertions.get("MATH-01"),
        )
        math_01_output = invoke_formula_v34(
            "MATH-01", math_01_inputs.authoritative_values
        )
        if not isinstance(math_01_output, Decimal):
            raise StackResolutionError(
                ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                "MATH-01 did not produce its exact Decimal output",
            )
        converted, conversion_receipt = UnitConversionOwnerV1.convert(
            conversion_id=(
                ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64
            ),
            value=math_01_output,
            source=UnitBasisDescriptorV1(
                "Decimal",
                "scalar",
                "dimensionless",
                "winning payout-normalized probability",
            ),
            target=UnitBasisDescriptorV1(
                "float64",
                "scalar",
                "probability points",
                "unit interval",
            ),
            context=context,
            receipt_id=f"CONVERSION::{context.context_id}::MATH-01::MATH-02",
        )
        if not isinstance(converted, float):
            raise StackResolutionError(
                ReasonCode.UNIT_CONVERSION_FAILED,
                "MATH-01 data edge did not produce finite float64",
            )
        source_packets = tuple(
            owner_registry.packet_by_id(packet_id)
            for packet_id in math_01_inputs.packet_refs
        )
        derived_clocks = PointInTimeClocksV1(
            observed_time=max(packet.clocks.observed_time for packet in source_packets),
            effective_time=max(
                packet.clocks.effective_time for packet in source_packets
            ),
            available_time=max(
                packet.clocks.available_time for packet in source_packets
            ),
            received_time=max(
                packet.clocks.received_time for packet in source_packets
            ),
            processed_time=max(
                packet.clocks.processed_time for packet in source_packets
            ),
            as_of_time=context.as_of,
        )
        dependency_packet = OwnerValuePacketV1(
            packet_id=f"EXECUTION::MATH-01::{context.context_id}",
            owner_id="QKUComputationControlPlaneV1.MATH-01",
            packet_type="ComputationExecutionReceiptV1::MATH-01",
            schema_id="ComputationExecutionReceiptV1::MATH-01::SCHEMA",
            schema_version="1.0.0",
            context_id=context.context_id,
            scope=context.scope,
            source_epoch_id=context.source_epoch_id,
            input_version=context.input_version,
            clocks=derived_clocks,
            ttl=min(
                (packet.ttl for packet in source_packets),
                default=context.maximum_age,
            ),
            values={"output.implied_probability": converted},
            authorized_binding_ids=(
                "FIVAB::MATH-02::market_implied_probability",
            ),
            producer_receipt_id=f"RECEIPT::MATH-01::{context.context_id}",
            producer_receipt_type=(
                "ComputationExecutionReceiptV1::MATH-01ReceiptV1"
            ),
            source_state_and_claim_lineage=(
                "QKUComputationControlPlaneV1.MATH-01 -> "
                "ComputationExecutionReceiptV1::MATH-01.output.implied_probability "
                "-> MATH-02.market_implied_probability"
            ),
            provider_sequence=f"MATH-01::{context.input_version}",
        )
        downstream_registry = owner_registry.with_internal_computation_receipt(
            dependency_packet
        )
        math_02_inputs = FormulaInputResolverV1.resolve(
            "MATH-02",
            context=context,
            owner_registry=downstream_registry,
            caller_assertions=assertions.get("MATH-02"),
        )
        if (
            math_02_inputs.authoritative_values["market_implied_probability"]
            != converted
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "actual converted producer value was not routed to MATH-02",
            )
        math_02_output = invoke_formula_v34(
            "MATH-02", math_02_inputs.authoritative_values
        )
        propagation = DependencyValuePropagationReceiptV1(
            receipt_id=f"PROPAGATION::{context.context_id}::MATH-01::MATH-02",
            edge_id=stack.data_edge_id,
            producer_math_spec_id="MATH-01",
            producer_implementation_id=(
                IMPLEMENTATION_REGISTRY["MATH-01"].contract.implementation_id
            ),
            producer_output_schema_ref="MATH-01::OUTPUT",
            producer_output_field="implied_probability",
            consumer_math_spec_id="MATH-02",
            consumer_implementation_id=(
                IMPLEMENTATION_REGISTRY["MATH-02"].contract.implementation_id
            ),
            consumer_input_field="market_implied_probability",
            producer_value=math_01_output,
            consumer_value=converted,
            execution_context=context,
            conversion_receipt_id=conversion_receipt.receipt_id,
        )
        return FormulaStackExecutionV1(
            stack=stack,
            execution_context=context,
            component_inputs=(math_01_inputs, math_02_inputs),
            component_outputs=(math_01_output, math_02_output),
            dependency_packet=dependency_packet,
            conversion_receipt=conversion_receipt,
            propagation_receipt=propagation,
            receipt_refs=tuple(
                dict.fromkeys(
                    (
                        *math_01_inputs.receipt_refs,
                        dependency_packet.producer_receipt_id,
                        conversion_receipt.receipt_id,
                        propagation.receipt_id,
                        *math_02_inputs.receipt_refs,
                    )
                )
            ),
        )


def _registered_data_flow_edge_for_binding(
    *,
    stack: RegisteredFormulaStackV1,
    component_ids: tuple[str, ...],
    consumer_index: int,
    binding: FormulaInputAuthorityBindingV1,
) -> FrozenDependencyRelationshipV1 | None:
    candidates = tuple(
        edge
        for edge in FROZEN_DEPENDENCY_RELATIONSHIPS.values()
        if (
            edge.kind is FrozenDependencyKindV1.DATA_FLOW_EDGE
            and edge.consumer_math_spec_id == binding.math_spec_id
            and edge.consumer_input_field == binding.input_name
        )
    )
    if not candidates:
        return None
    if len(candidates) != 1:
        raise StackResolutionError(
            ReasonCode.DEPENDENCY_CLOSURE_FAILED,
            f"{binding.binding_id} has ambiguous registered data-flow edges",
        )
    edge = candidates[0]
    producer_index = (
        component_ids.index(edge.producer_math_spec_id)
        if edge.producer_math_spec_id in component_ids
        else -1
    )
    producer_output = FROZEN_NAMED_OUTPUT_CONTRACTS.get(
        edge.producer_math_spec_id
    )
    consumer_input = FROZEN_FORMULA_INPUT_CONTRACTS.get(
        edge.consumer_math_spec_id
    )
    expected_owner = (
        f"QKUComputationControlPlaneV1.{edge.producer_math_spec_id}"
    )
    expected_packet_type = (
        f"ComputationExecutionReceiptV1::{edge.producer_math_spec_id}"
    )
    expected_schema_id = f"{expected_packet_type}::SCHEMA"
    expected_receipt_type = f"{expected_packet_type}ReceiptV1"
    expected_lineage = (
        f"{expected_owner} -> {expected_packet_type}.output."
        f"{edge.producer_output_field} -> {edge.consumer_math_spec_id}."
        f"{edge.consumer_input_field}"
    )
    try:
        conversion = ConversionIdentityV1(edge.conversion_ref)
    except ValueError as exc:
        raise StackResolutionError(
            ReasonCode.DEPENDENCY_CLOSURE_FAILED,
            f"{edge.edge_id} has no registered conversion identity",
        ) from exc
    if (
        edge.edge_id != stack.data_edge_id
        or producer_index < 0
        or producer_index >= consumer_index
        or producer_output is None
        or producer_output.schema_id != edge.producer_output_schema_ref
        or producer_output.output_name != edge.producer_output_field
        or consumer_input is None
        or edge.consumer_input_field
        not in consumer_input.declared_input_keys
        or edge.producer_version_ref != "FROZEN_V3_4"
        or edge.consumer_version_ref != "FROZEN_V3_4"
        or edge.terminal_state != "EXACT_EDGE_CLOSED"
        or edge.point_in_time_rule != "SAME_CONTEXT_SNAPSHOT"
        or conversion
        is not ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64
        or binding.admission_class
        is not FormulaInputAdmissionClassV1.EXACT_REGISTERED_UPSTREAM_RECEIPT_REQUIRED_BEFORE_CONTEXTUAL_COMPUTABILITY
        or binding.accepted_upstream_owner_id != expected_owner
        or binding.accepted_packet_or_snapshot_type != expected_packet_type
        or binding.schema_id != expected_schema_id
        or binding.schema_version != "1.0.0"
        or binding.exact_field_path
        != f"output.{edge.producer_output_field}"
        or binding.producer_receipt_type != expected_receipt_type
        or binding.source_state_and_claim_lineage != expected_lineage
    ):
        raise StackResolutionError(
            ReasonCode.DEPENDENCY_CLOSURE_FAILED,
            f"{binding.binding_id} is not supplied by the exact selected data edge",
        )
    return edge


def _preflight_registered_stack_context_closure(
    *,
    stack_id: str,
    stack_version: str,
    component_ids: tuple[str, ...],
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
) -> _SelectedStackContextClosureV1:
    """Resolve full-stack input/dependency closure without invoking a formula."""

    stack = ApplicableStackResolverV1.resolve(
        stack_id=stack_id,
        stack_version=stack_version,
        component_ids=component_ids,
    )
    expected_pins = tuple(
        ImplementationVersionPinV1(
            math_spec_id=component_id,
            implementation_id=IMPLEMENTATION_REGISTRY[
                component_id
            ].contract.implementation_id,
        )
        for component_id in component_ids
        if component_id in IMPLEMENTATION_REGISTRY
    )
    if (
        len(expected_pins) != len(component_ids)
        or context.implementation_versions != expected_pins
    ):
        raise StackResolutionError(
            ReasonCode.DEPENDENCY_CLOSURE_FAILED,
            "stack preflight implementation pins are incomplete or altered",
        )
    global_blocker: ReasonCode | None = None
    try:
        context = _validate_formula_input_context(context)
    except (InputAuthorityError, PointInTimeError, FreshnessError) as exc:
        global_blocker = exc.reason_code
    empty_assertions: Mapping[str, object] = MappingProxyType({})
    component_closures: list[_StackComponentContextClosureV1] = []
    for consumer_index, component_id in enumerate(component_ids):
        blockers: list[ReasonCode] = (
            [global_blocker] if global_blocker is not None else []
        )
        external_receipts: list[str] = []
        dependency_inputs: list[str] = []
        dependency_edges: list[str] = []
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID.get(component_id)
        input_contract = FROZEN_FORMULA_INPUT_CONTRACTS.get(component_id)
        component_contracts_closed = (
            component_id in FROZEN_FORMULA_REQUIREMENTS
            and bindings is not None
            and input_contract is not None
            and component_id in FROZEN_NAMED_OUTPUT_CONTRACTS
            and component_id in IMPLEMENTATION_REGISTRY
            and component_id in ORACLE_BY_MATH_ID
            and component_id in GOLDEN_VECTOR_BY_MATH_ID
            and tuple(binding.input_name for binding in bindings)
            == input_contract.declared_input_keys
        )
        if not component_contracts_closed:
            blockers.append(ReasonCode.DEPENDENCY_CLOSURE_FAILED)
        elif global_blocker is None:
            assert bindings is not None
            for binding in bindings:
                try:
                    edge = _registered_data_flow_edge_for_binding(
                        stack=stack,
                        component_ids=component_ids,
                        consumer_index=consumer_index,
                        binding=binding,
                    )
                    if edge is not None:
                        dependency_inputs.append(binding.binding_id)
                        dependency_edges.append(edge.edge_id)
                        continue
                    resolved = _resolve_formula_input_binding(
                        component_id,
                        binding=binding,
                        context=context,
                        owner_registry=owner_registry,
                        caller_assertions=empty_assertions,
                    )
                except (
                    InputAuthorityError,
                    PointInTimeError,
                    FreshnessError,
                    StackResolutionError,
                ) as exc:
                    blockers.append(exc.reason_code)
                    continue
                external_receipts.extend(
                    (
                        resolved.producer_receipt_id,
                        resolved.point_in_time_receipt.receipt_id,
                        resolved.freshness_receipt.receipt_id,
                    )
                )
        component_closures.append(
            _StackComponentContextClosureV1(
                math_spec_id=component_id,
                blocker_reasons=tuple(dict.fromkeys(blockers)),
                resolved_external_input_receipt_refs=tuple(
                    dict.fromkeys(external_receipts)
                ),
                dependency_producible_input_refs=tuple(
                    dict.fromkeys(dependency_inputs)
                ),
                dependency_edge_refs=tuple(
                    dict.fromkeys(dependency_edges)
                ),
            )
        )
    full_stack_blockers = tuple(
        dict.fromkeys(
            reason
            for closure in component_closures
            for reason in closure.blocker_reasons
        )
    )
    return _SelectedStackContextClosureV1(
        execution_context=context,
        stack_id=stack.stack_id,
        stack_version=stack.stack_version,
        component_ids=stack.component_ids,
        component_closures=tuple(component_closures),
        full_stack_blocker_reasons=full_stack_blockers,
        resolved_external_input_receipt_refs=tuple(
            dict.fromkeys(
                ref
                for closure in component_closures
                for ref in closure.resolved_external_input_receipt_refs
            )
        ),
        dependency_producible_input_refs=tuple(
            dict.fromkeys(
                ref
                for closure in component_closures
                for ref in closure.dependency_producible_input_refs
            )
        ),
        dependency_edge_refs=tuple(
            dict.fromkeys(
                ref
                for closure in component_closures
                for ref in closure.dependency_edge_refs
            )
        ),
    )


if (
    len(REGISTERED_FORMULA_STACKS) != 1
    or sum(
        edge.kind is FrozenDependencyKindV1.DATA_FLOW_EDGE
        for edge in FROZEN_DEPENDENCY_RELATIONSHIPS.values()
    )
    != 1
):
    raise StackResolutionError(
        ReasonCode.DEPENDENCY_CLOSURE_FAILED,
        "v3.4 permits exactly one registered dependency-closed formula stack",
    )
