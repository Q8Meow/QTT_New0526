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
    InputResolutionError,
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
    compiled_dependency_edge_ref_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationReadinessStateV1,
    FallbackEnvelopeV1,
    InputOriginV1,
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
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    MARKET_PROBABILITY_EDGE_TEMPLATE,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    get_source_state,
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
        origin=InputOriginV1.OWNER_SUPPLIED_PURE_COMPUTATION_INPUT,
        value_lineage_ref=f"value::{value.name}::v1",
        precision_policy="DECIMAL_CONTEXT_PRECISION_34",
        rounding_policy="NO_IMPLICIT_QUANTIZATION",
        producer_ref="test_resolution_pipeline::_evidence",
        consumer_refs=("QKUComputationControlPlaneServiceV1",),
        pure_computation_authority_ref="ST12B_CERTIFIED_TEST_FIXTURE",
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


def test_origin_binding_derivation_and_field_class_pit_matrix() -> None:
    resolver = RequiredInputResolverV1(
        admitted_pure_computation_authority_refs=(
            "ST12B_CERTIFIED_TEST_FIXTURE",
        )
    )
    values = TypedValueRecordV1(
        (
            TypedValueV1(
                "contract_price",
                TypedValueKindV1.DECIMAL,
                Decimal("0.47"),
                "currency",
                "per_contract",
            ),
            TypedValueV1(
                "payout_per_winning_contract",
                TypedValueKindV1.DECIMAL,
                Decimal("1"),
                "currency",
                "per_contract",
            ),
        )
    )
    source_context = replace(_context(), source_epoch_id="epoch2")

    def canonical(
        value: TypedValueV1,
        source_state_id: str,
    ) -> ContextualInputValueV1:
        return ContextualInputValueV1(
            typed_value=value,
            point_in_time=replace(
                _pit(value.name),
                source_epoch_id="epoch2",
            ),
            freshness_policy=FreshnessPolicyV1(
                policy_id=f"canonical-ttl::{value.name}",
                ttl=timedelta(days=7),
                parameter_policy_ref="ST10-SOURCE::07",
                stale_behavior="FAIL_CLOSED",
            ),
            origin=InputOriginV1.CANONICAL_SOURCE_STATE,
            value_lineage_ref=f"canonical::{value.name}",
            precision_policy="DECIMAL_CONTEXT_PRECISION_34",
            rounding_policy="NO_IMPLICIT_QUANTIZATION",
            producer_ref="canonical-source-fixture",
            consumer_refs=("QKUComputationControlPlaneServiceV1",),
            source_state_id=source_state_id,
        )

    valid = resolver.resolve(
        component_id="MATH-01",
        context=source_context,
        supplied_values=values,
        contextual_evidence=tuple(
            canonical(value, "ST10-SOURCE::07")
            for value in values.fields
        ),
    )
    fake = resolver.resolve(
        component_id="MATH-01",
        context=source_context,
        supplied_values=values,
        contextual_evidence=tuple(
            canonical(value, "UNREGISTERED::FAKE_STATE")
            for value in values.fields
        ),
    )
    forged_assertions = resolver.resolve(
        component_id="MATH-01",
        context=source_context,
        supplied_values=values,
        contextual_evidence=tuple(
            replace(
                canonical(value, "ST10-SOURCE::07"),
                source_identity="UNREGISTERED::FAKE_SOURCE",
                source_epoch_id="epoch2",
                rights_state="CALLER_ASSERTED_RIGHTS",
            )
            for value in values.fields
        ),
    )
    pure = resolver.resolve(
        component_id="MATH-01",
        context=_context(),
        supplied_values=values,
        contextual_evidence=tuple(_evidence(value) for value in values.fields),
    )
    pure_paper = resolver.resolve(
        component_id="MATH-01",
        context=_context(),
        supplied_values=values,
        contextual_evidence=tuple(_evidence(value) for value in values.fields),
        mode="PAPER",
    )
    unprivileged = RequiredInputResolverV1().resolve(
        component_id="MATH-01",
        context=_context(),
        supplied_values=values,
        contextual_evidence=tuple(_evidence(value) for value in values.fields),
    )
    assert valid.computable
    assert (
        valid.source_readiness_state
        is ComputationReadinessStateV1.SOURCE_CONTEXT_COMPUTABLE
    )
    assert len(valid.canonical_source_binding_receipts) == 2
    source_07 = get_source_state("ST10-SOURCE::07")
    assert all(
        receipt.binding_rule_id == "ST12-SOURCE-RULE::007"
        and receipt.source_state_id == source_07.source_state_id
        and receipt.stable_source_identity
        == source_07.stable_source_identity
        and receipt.rights_state == source_07.rights_and_use_state
        for receipt in valid.canonical_source_binding_receipts
    )
    assert not fake.computable
    assert fake.blocker_codes == (ReasonCode.SOURCE_BINDING_REQUIRED,)
    assert not forged_assertions.computable
    assert forged_assertions.blocker_codes == (ReasonCode.SOURCE_CONFLICT,)
    assert (
        pure.source_readiness_state
        is ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
    )
    assert not pure.source_owner_refs
    assert not pure_paper.computable
    assert ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED in pure_paper.blocker_codes
    assert not unprivileged.computable
    assert (
        ReasonCode.INPUT_ORIGIN_NOT_AUTHORIZED
        in unprivileged.blocker_codes
    )

    market = TypedValueV1(
        "market_implied_probability",
        TypedValueKindV1.FLOAT64,
        0.47,
        "probability",
        "unit_interval",
    )
    calibrated = TypedValueV1(
        "calibrated_model_probability",
        TypedValueKindV1.FLOAT64,
        0.60,
        "probability",
        "unit_interval",
    )
    edge = MARKET_PROBABILITY_EDGE_TEMPLATE.edges[0]
    assert not hasattr(ContextualInputValueV1, "from_service_derived")
    derived = ContextualInputValueV1._from_service_derived(
        typed_value=market,
        point_in_time=_pit(market.name),
        freshness_policy=FreshnessPolicyV1(
            "derived-ttl",
            timedelta(minutes=5),
            "upstream-min-ttl",
            "FAIL_CLOSED",
        ),
        value_lineage_ref="derived::MATH-01::p_market",
        precision_policy="DECLARED_DECIMAL_TO_FLOAT64_METHOD_BOUNDARY",
        rounding_policy="NO_IMPLICIT_QUANTIZATION",
        producer_ref="MATH-01",
        consumer_refs=(
            "MATH-02",
            "QKUComputationControlPlaneServiceV1",
        ),
        upstream_execution_receipt_ref="EXECUTION::UPSTREAM",
        upstream_component_id="MATH-01",
        compiled_dependency_edge_ref=compiled_dependency_edge_ref_v1(edge),
        lineage_readiness_state=(
            ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
        ),
    )
    derived_receipt = resolver.resolve(
        component_id="MATH-02",
        context=_context(),
        supplied_values=TypedValueRecordV1((calibrated, market)),
        contextual_evidence=(_evidence(calibrated), derived),
        compiled_dependency_graph=(
            MARKET_PROBABILITY_EDGE_TEMPLATE.compiled_graph
        ),
    )
    assert derived_receipt.computable
    assert (
        derived_receipt.source_readiness_state
        is ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
    )
    derived_row = next(
        row
        for row in derived_receipt.inputs
        if row.input_field_id == "market_implied_probability"
    )
    assert (
        derived_row.upstream_execution_receipt_ref
        == "EXECUTION::UPSTREAM"
    )
    assert (
        derived_row.compiled_dependency_edge_ref
        == compiled_dependency_edge_ref_v1(edge)
    )
    with pytest.raises(InputResolutionError) as forged:
        ContextualInputValueV1(
            typed_value=market,
            point_in_time=_pit(market.name),
            freshness_policy=FreshnessPolicyV1(
                "forged-ttl",
                timedelta(minutes=5),
                "caller",
                "FAIL_CLOSED",
            ),
            origin=InputOriginV1.IN_PROCESS_DERIVED_VALUE,
            value_lineage_ref="forged",
            precision_policy="forged",
            rounding_policy="forged",
            producer_ref="MATH-01",
            consumer_refs=(
                "MATH-02",
                "QKUComputationControlPlaneServiceV1",
            ),
            upstream_execution_receipt_ref="FORGED",
            upstream_component_id="MATH-01",
            compiled_dependency_edge_ref=compiled_dependency_edge_ref_v1(edge),
            lineage_readiness_state=(
                ComputationReadinessStateV1.SOURCE_CONTEXT_COMPUTABLE
            ),
        )
    assert forged.value.reason_code is ReasonCode.DERIVED_LINEAGE_INVALID

    future = MOMENT + timedelta(microseconds=1)
    pit_cases = (
        (
            replace(_pit("observation"), observed_time=future),
            PointInTimeStateV1.UNAVAILABLE_AT_DECISION,
        ),
        (
            replace(
                _pit(
                    "scheduled",
                    field_class=(
                        PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT
                    ),
                ),
                effective_time=future,
            ),
            PointInTimeStateV1.AVAILABLE,
        ),
        (
            replace(
                _pit(
                    "revision",
                    field_class=PointInTimeFieldClassV1.REVISION,
                ),
                observed_time=future,
            ),
            PointInTimeStateV1.REVISION_LEAKAGE_BLOCKED,
        ),
        *(
            (
                replace(
                    _pit(name, field_class=field_class),
                    **{time_name: future},
                ),
                PointInTimeStateV1.REVISION_LEAKAGE_BLOCKED,
            )
            for name, field_class in (
                ("outcome", PointInTimeFieldClassV1.EVENT_OUTCOME),
                ("settlement", PointInTimeFieldClassV1.SETTLEMENT),
            )
            for time_name in ("observed_time", "effective_time")
        ),
    )
    for evidence, expected_state in pit_cases:
        assert (
            PointInTimeResolverV1.resolve(evidence, _context()).state
            is expected_state
        )
    precedence = PointInTimeResolverV1.resolve(
        replace(
            _pit(
                "precedence",
                field_class=PointInTimeFieldClassV1.EVENT_OUTCOME,
            ),
            source_epoch_id="wrong-epoch",
            observed_time=future,
            source_available_time=future,
        ),
        _context(),
    )
    assert precedence.state is PointInTimeStateV1.EPOCH_MISMATCH_BLOCKED
    assert precedence.blocker_codes[0] is ReasonCode.SOURCE_EPOCH_MISSING


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
        ),
        admitted_pure_computation_authority_refs=(
            "ST12B_CERTIFIED_TEST_FIXTURE",
        ),
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
