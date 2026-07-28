from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (
    UnitConversionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    FallbackResolutionError,
    ReasonCode,
    UnitConversionError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.fallback import (
    CERTIFIED_FAIL_CLOSED_FALLBACK,
    RegisteredFallbackResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.freshness import (
    DeadlineBudgetV1,
    DeadlineResolverV1,
    FreshnessPolicyV1,
    FreshnessResolverV1,
    FreshnessStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    ContextualInputValueV1,
    InputAvailabilityStateV1,
    RequiredInputResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    FallbackEnvelopeV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeFieldClassV1,
    PointInTimeResolverV1,
    PointInTimeStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.unit_conversion import (
    RegisteredUnitConversionV1,
    UnitConversionRegistryV1,
)


MOMENT = datetime(2026, 7, 27, 12, tzinfo=UTC)


def _context(*, observed: datetime = MOMENT) -> ComputationContextKeyV1:
    return ComputationContextKeyV1(
        context_id="context::st12b::vector",
        as_of=MOMENT,
        observed_at=observed,
        source_epoch_id="epoch::st12b::vector",
        input_version="input-lock::st12b::vector",
        maximum_age=timedelta(minutes=5),
    )


def _pit(
    field_id: str,
    *,
    observed: datetime = MOMENT,
    effective: datetime = MOMENT,
    available: datetime = MOMENT,
    field_class: PointInTimeFieldClassV1 = (
        PointInTimeFieldClassV1.OBSERVATION
    ),
) -> PointInTimeEvidenceV1:
    return PointInTimeEvidenceV1(
        evidence_id=f"evidence::{field_id}",
        field_id=field_id,
        field_class=field_class,
        observed_time=observed,
        effective_time=effective,
        source_available_time=available,
        strategy_available_time=available,
        received_time=available,
        processed_time=available,
        as_of_time=MOMENT,
        source_epoch_id="epoch::st12b::vector",
        source_revision_id=f"revision::{field_id}",
    )


def _evidence(value: TypedValueV1) -> ContextualInputValueV1:
    return ContextualInputValueV1(
        typed_value=value,
        point_in_time=_pit(value.name),
        freshness_policy=FreshnessPolicyV1(
            policy_id=f"ttl::{value.name}",
            ttl=timedelta(minutes=5),
            parameter_policy_ref=f"test-vector::{value.name}::ttl",
            stale_behavior="FAIL_CLOSED_OR_REGISTERED_FALLBACK",
        ),
        source_identity="OWNER_SUPPLIED_TYPED_TEST_VECTOR",
        source_state_id="source-state::typed-test-vector",
        source_epoch_id="epoch::st12b::vector",
        rights_state="AUTHORIZED_PURE_COMPUTATION_INPUT",
        value_lineage_ref=f"value::{value.name}::v1",
        precision_policy="DECIMAL_CONTEXT_PRECISION_34",
        rounding_policy="NO_IMPLICIT_QUANTIZATION",
        producer_ref="test_resolution_pipeline::_evidence",
        consumer_refs=("QKUComputationControlPlaneServiceV1",),
        fallback_ref="FALLBACK::NO_EFFECT_FAIL_CLOSED",
    )


def test_point_in_time_preserves_time_domains_and_blocks_leakage() -> None:
    scheduled = _pit(
        "scheduled_fact",
        effective=MOMENT + timedelta(days=1),
        field_class=PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT,
    )
    receipt = PointInTimeResolverV1.resolve(scheduled, _context())
    assert receipt.available
    assert scheduled.observed_time < scheduled.effective_time

    leaked = _pit(
        "settlement",
        available=MOMENT + timedelta(microseconds=1),
        field_class=PointInTimeFieldClassV1.SETTLEMENT,
    )
    receipt = PointInTimeResolverV1.resolve(leaked, _context())
    assert receipt.state is PointInTimeStateV1.REVISION_LEAKAGE_BLOCKED
    assert ReasonCode.REVISION_LEAKAGE in receipt.blocker_codes

    with pytest.raises(ContractValidationError):
        replace(scheduled, observed_time=datetime(2026, 7, 27, 12))


def test_freshness_ttl_boundary_materiality_and_monotonic_deadline() -> None:
    policy = FreshnessPolicyV1(
        "ttl::exact",
        timedelta(seconds=60),
        "certified-ttl-row",
        "FAIL_CLOSED",
    )
    exact = FreshnessResolverV1.resolve_field(
        subject_id="field::exact",
        observed_time=MOMENT - timedelta(seconds=60),
        as_of_time=MOMENT,
        policy=policy,
    )
    stale = FreshnessResolverV1.resolve_field(
        subject_id="field::stale",
        observed_time=MOMENT - timedelta(seconds=60, microseconds=1),
        as_of_time=MOMENT,
        policy=policy,
    )
    unknown = FreshnessResolverV1.resolve_field(
        subject_id="field::unknown",
        observed_time=MOMENT,
        as_of_time=MOMENT,
        policy=FreshnessPolicyV1(
            "ttl::unknown",
            None,
            "NO_DEFAULT_REQUIRES_CALIBRATION",
            "FAIL_CLOSED",
        ),
    )
    assert exact.state is FreshnessStateV1.FRESH
    assert stale.state is FreshnessStateV1.STALE
    assert unknown.state is FreshnessStateV1.UNKNOWN_FAIL_CLOSED

    closure = FreshnessResolverV1.resolve_closure(
        subject_id="component::materiality",
        scope="COMPONENT",
        dependencies=((exact, True), (stale, False)),
        as_of_time=MOMENT,
    )
    assert closure.fresh

    budget = DeadlineBudgetV1(
        deadline_id="deadline::vector",
        budget_seconds=Decimal("0.5"),
        parameter_policy_ref="certified-deadline-row",
        started_monotonic=Decimal("10"),
    )
    assert DeadlineResolverV1.resolve(
        budget,
        monotonic_clock=lambda: 10.5,
    ).within_budget
    exhausted = DeadlineResolverV1.resolve(
        budget,
        monotonic_clock=lambda: 10.500001,
    )
    assert exhausted.blocker_codes == (ReasonCode.DEADLINE_EXHAUSTED,)


def _conversion(
    conversion_id: str,
    source: str,
    target: str,
    factor: str,
) -> RegisteredUnitConversionV1:
    return RegisteredUnitConversionV1(
        conversion_id=conversion_id,
        identity=UnitConversionV1(source, target, Decimal(factor)),
        supplied_basis="per_contract",
        required_basis="per_contract",
        precision_quantum=None,
        rounding_rule=None,
        source_claim_ref=f"formal::{conversion_id}",
    )


def test_conversion_is_explicit_exact_unique_and_acyclic() -> None:
    registry = UnitConversionRegistryV1(
        (_conversion("conversion::cents", "cents", "currency", "0.01"),)
    )
    receipt = registry.resolve(
        value=Decimal("47"),
        supplied_unit="cents",
        required_unit="currency",
        supplied_basis="per_contract",
        required_basis="per_contract",
    )
    assert receipt.resolved_value == Decimal("0.47")
    assert receipt.conversion_path == ("conversion::cents",)

    with pytest.raises(UnitConversionError) as missing:
        UnitConversionRegistryV1().resolve(
            value=Decimal("47"),
            supplied_unit="percent",
            required_unit="fraction",
            supplied_basis="dimensionless",
            required_basis="dimensionless",
        )
    assert missing.value.reason_code is ReasonCode.BASIS_CONVERSION_FORBIDDEN

    with pytest.raises(UnitConversionError) as ambiguous:
        UnitConversionRegistryV1(
            (
                _conversion("conversion::a-b", "a", "b", "1"),
                _conversion("conversion::a-c", "a", "c", "1"),
                _conversion("conversion::c-b", "c", "b", "1"),
            )
        )
    assert ambiguous.value.reason_code is ReasonCode.UNIT_CONVERSION_AMBIGUOUS

    with pytest.raises(UnitConversionError) as cyclic:
        UnitConversionRegistryV1(
            (
                _conversion("conversion::a-b", "a", "b", "1"),
                _conversion("conversion::b-a", "b", "a", "1"),
            )
        )
    assert cyclic.value.reason_code is ReasonCode.UNIT_CONVERSION_CYCLE


def test_required_input_resolution_derives_schema_pit_ttl_and_conversion() -> None:
    contract_price = TypedValueV1(
        "contract_price",
        TypedValueKindV1.DECIMAL,
        Decimal("47"),
        "cents",
        "per_contract",
    )
    payout = TypedValueV1(
        "payout_per_winning_contract",
        TypedValueKindV1.DECIMAL,
        Decimal("1"),
        "currency",
        "per_contract",
    )
    resolver = RequiredInputResolverV1(
        conversion_registry=UnitConversionRegistryV1(
            (
                _conversion(
                    "conversion::cents-to-currency",
                    "cents",
                    "currency",
                    "0.01",
                ),
            )
        )
    )
    receipt = resolver.resolve(
        component_id="MATH-01",
        context=_context(),
        supplied_values=TypedValueRecordV1((contract_price, payout)),
        contextual_evidence=(_evidence(contract_price), _evidence(payout)),
        dependency_refs=("DAG::MATH-01",),
    )
    assert receipt.computable
    assert receipt.arguments == {
        "contract_price": Decimal("0.47"),
        "payout_per_winning_contract": Decimal("1"),
    }
    assert receipt.inputs[0].conversion_receipt is not None
    assert all(row.resolved for row in receipt.inputs)

    missing = resolver.resolve(
        component_id="MATH-01",
        context=_context(),
        supplied_values=TypedValueRecordV1((contract_price,)),
        contextual_evidence=(_evidence(contract_price),),
    )
    assert not missing.computable
    assert missing.inputs[1].state is InputAvailabilityStateV1.MISSING_REQUIRED
    assert missing.blocker_codes == (ReasonCode.REQUIRED_INPUT_MISSING,)


def test_registered_fallback_is_compatible_acyclic_and_no_effect() -> None:
    resolver = RegisteredFallbackResolverV1(
        (CERTIFIED_FAIL_CLOSED_FALLBACK,)
    )
    receipt = resolver.resolve(
        fallback_id="FALLBACK::NO_EFFECT_FAIL_CLOSED",
        source_component_id="MATH-46",
        trigger_reason_code=ReasonCode.DEADLINE_EXHAUSTED,
        supplied_unit="DECLARED",
        required_unit="DECLARED",
        supplied_basis="DECLARED",
        required_basis="DECLARED",
        timing_class="OFFLINE",
        freshness_state="UNKNOWN_FAIL_CLOSED",
        mode="CONTRACT_ONLY",
        consumer_ref="quantum_optimizer_agent",
    )
    assert receipt.resolved_target.endswith("OR_NO_TRADE")
    assert all(
        (
            receipt.no_write_effect,
            receipt.no_provider_effect,
            receipt.no_private_state_effect,
            receipt.no_llm_effect,
            receipt.no_qpu_effect,
            receipt.no_order_effect,
        )
    )

    first = replace(
        CERTIFIED_FAIL_CLOSED_FALLBACK,
        envelope=FallbackEnvelopeV1(
            "FALLBACK::CYCLE-A",
            ("ST12B_STACK_NOT_COMPUTABLE",),
            "FALLBACK::CYCLE-B",
        ),
        target_component_or_terminal="FALLBACK::CYCLE-B",
    )
    second = replace(
        CERTIFIED_FAIL_CLOSED_FALLBACK,
        envelope=FallbackEnvelopeV1(
            "FALLBACK::CYCLE-B",
            ("ST12B_STACK_NOT_COMPUTABLE",),
            "FALLBACK::CYCLE-A",
        ),
        target_component_or_terminal="FALLBACK::CYCLE-A",
    )
    with pytest.raises(FallbackResolutionError) as cycle:
        RegisteredFallbackResolverV1((first, second))
    assert cycle.value.reason_code is ReasonCode.FALLBACK_CYCLE
