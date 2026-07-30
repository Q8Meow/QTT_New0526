import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    FreshnessError,
    InputAuthorityError,
    PointInTimeError,
    ReasonCode,
    UnitConversionError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    invoke_formula_v34,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    FormulaInputResolverV1,
    OwnerValuePacketV1,
    RuntimeParameterValueResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    CUMULATIVE_PARAMETER_POLICIES,
    FamilyParameterPolicyCompilerV1,
    RUNTIME_PARAMETER_OWNER_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PointInTimeClocksV1,
    PointInTimeFieldClassV1,
    PointInTimePolicyV1,
    classify_point_in_time_semantics,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    ApplicableStackResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.unit_conversion import (
    ConversionIdentityV1,
    UnitBasisDescriptorV1,
    UnitConversionOwnerV1,
)


AS_OF = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)


def _context(context_id: str = "CTX::ST12B") -> ComputationContextKeyV1:
    return ComputationContextKeyV1(
        context_id=context_id,
        as_of=AS_OF,
        observed_at=AS_OF - timedelta(seconds=1),
        source_epoch_id="EPOCH::ST12B",
        input_version="V1",
        maximum_age=timedelta(days=1),
    )


def _clocks() -> PointInTimeClocksV1:
    observed = AS_OF - timedelta(seconds=1)
    return PointInTimeClocksV1(
        observed_time=observed,
        effective_time=observed,
        available_time=observed,
        received_time=observed,
        processed_time=observed,
        as_of_time=AS_OF,
    )


def _formula_packets(
    math_id: str,
    *,
    context: ComputationContextKeyV1,
    excluded_inputs: frozenset[str] = frozenset(),
) -> tuple[tuple[OwnerValuePacketV1, ...], dict[str, object]]:
    inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
    packets = tuple(
        OwnerValuePacketV1(
            packet_id=f"PACKET::{binding.binding_id}",
            owner_id=binding.accepted_upstream_owner_id,
            packet_type=binding.accepted_packet_or_snapshot_type,
            schema_id=binding.schema_id,
            schema_version=binding.schema_version,
            context_id=context.context_id,
            source_epoch_id=context.source_epoch_id,
            clocks=_clocks(),
            ttl=timedelta(days=1),
            values={binding.exact_field_path: inputs[binding.input_name]},
            authorized_binding_ids=(binding.binding_id,),
            producer_receipt_id=f"RECEIPT::{binding.binding_id}",
            producer_receipt_type=binding.producer_receipt_type,
            source_state_and_claim_lineage=(
                binding.source_state_and_claim_lineage
            ),
            provider_sequence=1,
            revision=1,
        )
        for binding in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        if binding.input_name not in excluded_inputs
    )
    assertions = {
        name: value
        for name, value in inputs.items()
        if name not in excluded_inputs
    }
    return packets, assertions


def test_all_142_formula_inputs_resolve_from_exact_owner_packets() -> None:
    context = _context()
    resolved_input_count = 0

    for math_id in FORMULA_INPUT_AUTHORITY_BY_MATH_ID:
        packets, assertions = _formula_packets(math_id, context=context)
        resolution = FormulaInputResolverV1.resolve(
            math_id,
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(packets),
            caller_assertions=assertions,
        )
        invoke_formula_v34(math_id, resolution.authoritative_values)
        resolved_input_count += len(resolution.inputs)

    assert resolved_input_count == 142


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    (
        ({"owner_id": "NonCanonicalOwnerV1"}, ReasonCode.INPUT_OWNER_MISMATCH),
        ({"source_conflict": True}, ReasonCode.SOURCE_CONFLICT),
    ),
)
def test_owner_and_source_conflicts_fail_closed(
    mutation: dict[str, object],
    reason_code: ReasonCode,
) -> None:
    context = _context()
    packets, assertions = _formula_packets("MATH-01", context=context)
    packets = (replace(packets[0], **mutation), *packets[1:])

    with pytest.raises(InputAuthorityError) as caught:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(packets),
            caller_assertions=assertions,
        )
    assert caught.value.reason_code is reason_code


def test_caller_value_and_stale_packet_cannot_override_owner_truth() -> None:
    context = _context()
    packets, assertions = _formula_packets("MATH-01", context=context)

    with pytest.raises(InputAuthorityError) as conflict:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(packets),
            caller_assertions={**assertions, "contract_price": "0.48"},
        )
    assert conflict.value.reason_code is ReasonCode.INPUT_VALUE_CONFLICT

    old = AS_OF - timedelta(days=2)
    stale_clocks = PointInTimeClocksV1(
        observed_time=old,
        effective_time=old,
        available_time=old,
        received_time=old,
        processed_time=old,
        as_of_time=AS_OF,
    )
    stale_packets = (replace(packets[0], clocks=stale_clocks), *packets[1:])
    with pytest.raises(FreshnessError) as stale:
        FormulaInputResolverV1.resolve(
            "MATH-01",
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1(stale_packets),
        )
    assert stale.value.reason_code is ReasonCode.FRESHNESS_VIOLATION


def test_five_point_in_time_classes_have_one_central_policy() -> None:
    semantic_cases = {
        "one current observation": PointInTimeFieldClassV1.OBSERVATION,
        "scheduled fact; effective time may be later": (
            PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT
        ),
        "future revisions forbidden": PointInTimeFieldClassV1.REVISION,
        "event_outcome effective state": PointInTimeFieldClassV1.EVENT_OUTCOME,
        "settlement state": PointInTimeFieldClassV1.SETTLEMENT,
    }
    context = _context()

    assert {
        classify_point_in_time_semantics(text)
        for text in semantic_cases
    } == set(PointInTimeFieldClassV1)
    for index, (text, field_class) in enumerate(semantic_cases.items()):
        clocks = _clocks()
        if field_class is PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT:
            clocks = replace(clocks, effective_time=AS_OF + timedelta(days=1))
        receipt = PointInTimePolicyV1.validate(
            receipt_id=f"PIT::{index}",
            field_class=classify_point_in_time_semantics(text),
            clocks=clocks,
            context=context,
        )
        assert receipt.admitted
        assert receipt.field_class is field_class

    with pytest.raises(PointInTimeError) as future_outcome:
        PointInTimePolicyV1.validate(
            receipt_id="PIT::FUTURE_OUTCOME",
            field_class=PointInTimeFieldClassV1.EVENT_OUTCOME,
            clocks=replace(
                _clocks(),
                effective_time=AS_OF + timedelta(microseconds=1),
            ),
            context=context,
        )
    assert (
        future_outcome.value.reason_code
        is ReasonCode.POINT_IN_TIME_VIOLATION
    )


def test_runtime_parameter_hold_and_terminal_application_receipt() -> None:
    context = _context("CTX::RUNTIME_PARAMETER")
    parameter_id = "ST10-PARAM::2197"
    binding = RUNTIME_PARAMETER_OWNER_BINDINGS[parameter_id]
    packet = OwnerValuePacketV1(
        packet_id=f"PACKET::{binding.binding_id}",
        owner_id=binding.accepted_upstream_owner_id,
        packet_type=binding.accepted_packet_or_snapshot_type,
        schema_id=binding.schema_id,
        schema_version=binding.schema_version,
        context_id=context.context_id,
        source_epoch_id=context.source_epoch_id,
        clocks=_clocks(),
        ttl=timedelta(days=1),
        values={binding.exact_field_path: True},
        authorized_binding_ids=(binding.binding_id,),
        producer_receipt_id=f"RECEIPT::{binding.binding_id}",
        producer_receipt_type=binding.producer_receipt_type,
        source_state_and_claim_lineage=str(
            binding.raw["source_state_and_claim_lineage"]
        ),
        provider_sequence=1,
        revision=1,
    )
    resolution = RuntimeParameterValueResolverV1.resolve(
        parameter_id,
        context=context,
        owner_registry=CanonicalOwnerPacketRegistryV1((packet,)),
        caller_assertion=True,
    )

    assert resolution.resolved.value is True
    assert (
        resolution.resolved.owner_id == binding.accepted_upstream_owner_id
    )
    with pytest.raises(InputAuthorityError) as conflict:
        RuntimeParameterValueResolverV1.resolve(
            parameter_id,
            context=context,
            owner_registry=CanonicalOwnerPacketRegistryV1((packet,)),
            caller_assertion=False,
        )
    assert conflict.value.reason_code is ReasonCode.INPUT_VALUE_CONFLICT

    compiled = FamilyParameterPolicyCompilerV1.compile(
        "FAMILY_POLICY::CM-05A2"
    )
    assert compiled.parameter_ids == ("ST10-PARAM::0973",)
    assert compiled.application_receipts[0].ultimate_owner == (
        CUMULATIVE_PARAMETER_POLICIES[
            "ST10-PARAM::0973"
        ].ultimate_owner
    )
    assert compiled.application_receipts[0].no_effect_authority is True
    assert "NOT_TERMINAL_CONSUMER" in compiled.compiler_role


def test_unit_conversion_and_dependency_stack_propagate_actual_value() -> None:
    context = _context("CTX::STACK")
    source = UnitBasisDescriptorV1(
        "Decimal",
        "scalar",
        "dimensionless",
        "winning payout-normalized probability",
    )
    target = UnitBasisDescriptorV1(
        "float64",
        "scalar",
        "probability points",
        "unit interval",
    )
    converted, receipt = UnitConversionOwnerV1.convert(
        conversion_id=(
            ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64
        ),
        value=Decimal("0.47"),
        source=source,
        target=target,
        context=context,
        receipt_id="CONVERSION::TEST",
    )
    assert converted == 0.47
    assert receipt.source_value == Decimal("0.47")
    with pytest.raises(UnitConversionError):
        UnitConversionOwnerV1.convert(
            conversion_id=(
                ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64
            ),
            value=Decimal("0.47"),
            source=replace(source, basis="wrong basis"),
            target=target,
            context=context,
            receipt_id="CONVERSION::FORBIDDEN",
        )

    math_01_packets, math_01_assertions = _formula_packets(
        "MATH-01", context=context
    )
    math_02_packets, math_02_assertions = _formula_packets(
        "MATH-02",
        context=context,
        excluded_inputs=frozenset({"market_implied_probability"}),
    )
    execution = ApplicableStackResolverV1.execute(
        stack_id="STACK::MATH-01::MATH-02::V3_4",
        component_ids=("MATH-01", "MATH-02"),
        context=context,
        owner_registry=CanonicalOwnerPacketRegistryV1(
            (*math_01_packets, *math_02_packets)
        ),
        caller_assertions_by_math_id={
            "MATH-01": math_01_assertions,
            "MATH-02": math_02_assertions,
        },
    )
    assert execution.component_outputs == (Decimal("0.47"), 0.14)
    assert execution.propagation_receipt.producer_value == Decimal("0.47")
    assert execution.propagation_receipt.consumer_value == 0.47
    assert execution.propagation_receipt.mutation_propagates is True
