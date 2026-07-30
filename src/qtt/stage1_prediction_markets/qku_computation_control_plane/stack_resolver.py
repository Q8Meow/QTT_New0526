"""Exact dependency closure and sole registered MATH-01 -> MATH-02 stack."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from .context import ComputationContextKeyV1
from .dependency_graph import (
    FROZEN_DEPENDENCY_RELATIONSHIPS,
    FrozenDependencyKindV1,
)
from .errors import ReasonCode, StackResolutionError
from .implementation_registry import invoke_formula_v34
from .input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    FormulaInputResolutionV1,
    FormulaInputResolverV1,
    OwnerValuePacketV1,
)
from .point_in_time import PointInTimeClocksV1
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
    context_id: str
    conversion_receipt_id: str
    mutation_propagates: bool = True

    def __post_init__(self) -> None:
        if (
            self.edge_id != "EDGE::MATH-01::MATH-02"
            or self.producer_math_spec_id != "MATH-01"
            or self.consumer_math_spec_id != "MATH-02"
            or self.producer_output_field != "implied_probability"
            or self.consumer_input_field != "market_implied_probability"
            or not isinstance(self.producer_value, Decimal)
            or not isinstance(self.consumer_value, float)
            or not self.context_id
            or not self.conversion_receipt_id
            or self.mutation_propagates is not True
        ):
            raise StackResolutionError(
                ReasonCode.DEPENDENCY_CLOSURE_FAILED,
                "data-flow propagation receipt is incomplete or fabricated",
            )


@dataclass(frozen=True, slots=True)
class FormulaStackExecutionV1:
    stack: RegisteredFormulaStackV1
    component_inputs: tuple[FormulaInputResolutionV1, ...]
    component_outputs: tuple[object, ...]
    conversion_receipt: UnitConversionReceiptV1
    propagation_receipt: DependencyValuePropagationReceiptV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            len(self.component_inputs) != 2
            or len(self.component_outputs) != 2
            or self.component_inputs[0].math_spec_id != "MATH-01"
            or self.component_inputs[1].math_spec_id != "MATH-02"
            or self.propagation_receipt.conversion_receipt_id
            != self.conversion_receipt.receipt_id
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
        return stack

    @staticmethod
    def execute(
        *,
        stack_id: str,
        component_ids: tuple[str, ...],
        context: ComputationContextKeyV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertions_by_math_id: Mapping[
            str, Mapping[str, object]
        ] | None = None,
    ) -> FormulaStackExecutionV1:
        stack = ApplicableStackResolverV1.resolve(
            stack_id=stack_id, component_ids=component_ids
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
            source_epoch_id=context.source_epoch_id,
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
        from .implementation_registry import IMPLEMENTATION_REGISTRY

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
            context_id=context.context_id,
            conversion_receipt_id=conversion_receipt.receipt_id,
        )
        return FormulaStackExecutionV1(
            stack=stack,
            component_inputs=(math_01_inputs, math_02_inputs),
            component_outputs=(math_01_output, math_02_output),
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
