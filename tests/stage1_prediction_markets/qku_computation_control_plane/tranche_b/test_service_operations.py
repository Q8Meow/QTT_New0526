"""Real numeric execution proofs for the one Tranche-B service surface."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (
    service as service_module,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    StackResolutionError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.freshness import (
    FreshnessPolicyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    ContextualInputValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputationReadinessStateV1,
    ComputeComponentRequestV1,
    ComputeStackRequestV1,
    ExplainResolutionRequestV1,
    InputOriginV1,
    OperationBlockerCodeV1,
    OperationStatusV1,
    ParameterApplicationTargetV1,
    ResolveApplicableStackRequestV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    ActiveMarketPriceGridV1,
    ActiveMarketPriceStructureV1,
    ParameterPolicyResolverV1,
    PriceGridIntervalV1,
    RuntimeParameterBindingOriginV1,
    RuntimeParameterBindingV1,
    get_parameter_policy,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeFieldClassV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    safe_json_loads,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    AGENT_DUTY_ROUTES,
    INSTITUTIONAL_FEATURE_SOCKETS,
    QKUComputationControlPlaneServiceV1,
    StructuredResolutionExplanationV1,
    output_schema_ref,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    MATH_IO_CONTRACTS,
    RequirementResolutionStateV1,
    get_component_execution_requirement,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    StackApplicabilityContextV1,
)


AS_OF = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
OBSERVED = AS_OF - timedelta(seconds=30)
TRACEPARENT = "00-11111111111111111111111111111111-2222222222222222-01"


@pytest.fixture(scope="module")
def service() -> QKUComputationControlPlaneServiceV1:
    return QKUComputationControlPlaneServiceV1(
        repo_root=Path.cwd(),
        pure_computation_authority_refs=(
            "ST12B_CERTIFIED_TEST_FIXTURE",
        ),
    )


def _context(input_version: str) -> ComputationContextKeyV1:
    return ComputationContextKeyV1(
        context_id="ST12B-REAL-NUMERIC",
        as_of=AS_OF,
        observed_at=OBSERVED,
        source_epoch_id="TEST-EPOCH-2026-07-27",
        input_version=input_version,
        maximum_age=timedelta(minutes=5),
    )


def _evidence(
    value: TypedValueV1,
    context: ComputationContextKeyV1,
) -> ContextualInputValueV1:
    point_in_time = PointInTimeEvidenceV1(
        evidence_id=f"PIT::{context.input_version}::{value.name}",
        field_id=value.name,
        field_class=PointInTimeFieldClassV1.OBSERVATION,
        observed_time=OBSERVED,
        effective_time=OBSERVED,
        source_available_time=OBSERVED,
        strategy_available_time=OBSERVED,
        received_time=OBSERVED,
        processed_time=OBSERVED,
        as_of_time=AS_OF,
        source_epoch_id=context.source_epoch_id,
        source_revision_id=f"REV::{context.input_version}",
    )
    return ContextualInputValueV1(
        typed_value=value,
        point_in_time=point_in_time,
        freshness_policy=FreshnessPolicyV1(
            policy_id=f"TTL::{value.name}",
            ttl=context.maximum_age,
            parameter_policy_ref="ComputationContextKeyV1::maximum_age",
            stale_behavior="FAIL_CLOSED_OR_REGISTERED_FALLBACK",
        ),
        origin=InputOriginV1.OWNER_SUPPLIED_PURE_COMPUTATION_INPUT,
        value_lineage_ref=f"VALUE::{context.input_version}::{value.name}",
        precision_policy="DECIMAL34_OR_DECLARED_FLOAT64_METHOD_BOUNDARY",
        rounding_policy="NO_IMPLICIT_QUANTIZATION",
        producer_ref="ST12B_CERTIFIED_INTEGRATION_VECTOR",
        consumer_refs=("QKUComputationControlPlaneServiceV1",),
        pure_computation_authority_ref="ST12B_CERTIFIED_TEST_FIXTURE",
    )


def _component_request(
    price: Decimal,
    *,
    suffix: str,
) -> tuple[
    ComputeComponentRequestV1,
    tuple[ContextualInputValueV1, ...],
]:
    context = _context(f"COMPONENT-{suffix}")
    values = TypedValueRecordV1(
        (
            TypedValueV1(
                "contract_price",
                TypedValueKindV1.DECIMAL,
                price,
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
    return (
        ComputeComponentRequestV1(
            request_id=f"REQUEST-COMPONENT-{suffix}",
            operation_name="compute_component",
            requested_at=AS_OF,
            principal_id="ST12B-TEST",
            capability_bundle_id="NO-EFFECT",
            context=context,
            idempotency_key=f"ECONOMIC-IDEMPOTENCY-COMPONENT-{suffix}",
            traceparent=TRACEPARENT,
            tracestate="",
            component_id="MATH-01",
            input_values=values,
            expected_output_schema_ref=output_schema_ref("MATH-01"),
        ),
        tuple(_evidence(value, context) for value in values.fields),
    )


def _stack_request(
    price: Decimal,
    *,
    suffix: str,
) -> tuple[
    ComputeStackRequestV1,
    StackApplicabilityContextV1,
    tuple[ContextualInputValueV1, ...],
]:
    context = _context(f"STACK-{suffix}")
    values = TypedValueRecordV1(
        (
            TypedValueV1(
                "contract_price",
                TypedValueKindV1.DECIMAL,
                price,
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
            TypedValueV1(
                "calibrated_model_probability",
                TypedValueKindV1.FLOAT64,
                0.60,
                "probability",
                "unit_interval",
            ),
        )
    )
    request = ComputeStackRequestV1(
        request_id=f"REQUEST-STACK-{suffix}",
        operation_name="compute_stack",
        requested_at=AS_OF,
        principal_id="ST12B-TEST",
        capability_bundle_id="NO-EFFECT",
        context=context,
        idempotency_key=f"ECONOMIC-IDEMPOTENCY-STACK-{suffix}",
        traceparent=TRACEPARENT,
        tracestate="",
        stack_id="ST12B::TEMPLATE::MARKET_PROBABILITY_EDGE",
        component_ids=("MATH-01", "MATH-02"),
        input_values=values,
    )
    applicability = StackApplicabilityContextV1(
        trade_plan_candidate_id=f"TRADE-PLAN-{suffix}",
        context_key=context,
        venue="OWNER_SUPPLIED_PURE_COMPUTATION",
        market_family="PREDICTION_MARKETS",
        market_category="binary_event",
        mode="CONTRACT_ONLY",
        required_roles=("market_implied_probability", "edge_probability"),
        owner_intent_ref=f"OWNER-INTENT-{suffix}",
        input_lock_ref=f"INPUT-LOCK-{suffix}",
        source_readiness_receipt_refs=(f"PURE-COMPUTATION-{suffix}",),
        consumer_refs=("READINESS1", "PRETRADE1", "SVC1", "AGENT-ORCH1"),
        input_readiness_state=(
            ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
        ),
    )
    return (
        request,
        applicability,
        tuple(_evidence(value, context) for value in values.fields),
    )


def _pure_component_request(
    component_id: str,
    values: TypedValueRecordV1,
    *,
    suffix: str,
) -> tuple[ComputeComponentRequestV1, tuple[ContextualInputValueV1, ...]]:
    context = _context(f"{component_id}-{suffix}")
    request = ComputeComponentRequestV1(
        request_id=f"REQUEST-{component_id}-{suffix}",
        operation_name="compute_component",
        requested_at=AS_OF,
        principal_id="ST12B-TEST",
        capability_bundle_id="NO-EFFECT",
        context=context,
        idempotency_key=f"ECONOMIC-IDEMPOTENCY-{component_id}-{suffix}",
        traceparent=TRACEPARENT,
        tracestate="",
        component_id=component_id,
        input_values=values,
        expected_output_schema_ref=output_schema_ref(component_id),
    )
    return request, tuple(_evidence(value, context) for value in values.fields)


def _math_36_request(
    *,
    suffix: str,
    yes_bids: str = '["0.40","0.42"]',
) -> tuple[ComputeComponentRequestV1, tuple[ContextualInputValueV1, ...]]:
    contract = MATH_IO_CONTRACTS["MATH-36"]
    by_name = {field.name: field for field in contract.inputs}
    values = TypedValueRecordV1(
        (
            TypedValueV1(
                "yes_bids",
                TypedValueKindV1.TEXT,
                yes_bids,
                by_name["yes_bids"].unit,
                by_name["yes_bids"].basis,
            ),
            TypedValueV1(
                "no_bids",
                TypedValueKindV1.TEXT,
                '["0.54","0.56"]',
                by_name["no_bids"].unit,
                by_name["no_bids"].basis,
            ),
            TypedValueV1(
                "payout",
                TypedValueKindV1.DECIMAL,
                Decimal("1.00"),
                by_name["payout"].unit,
                by_name["payout"].basis,
            ),
        )
    )
    return _pure_component_request("MATH-36", values, suffix=suffix)


def _math_36_runtime_bindings(
    context: ComputationContextKeyV1,
) -> tuple[RuntimeParameterBindingV1, ...]:
    interval = PriceGridIntervalV1(
        lower=Decimal("0"),
        upper=Decimal("1"),
        step=Decimal("0.01"),
    )
    controls = {
        "ST10-PARAM::2212": ActiveMarketPriceGridV1(
            market_id="MARKET::CERTIFIED-CONTRACT-FIXTURE",
            venue="KALSHI",
            payout=Decimal("1"),
            intervals=(interval,),
        ),
        "ST10-PARAM::2213": ActiveMarketPriceStructureV1(
            market_id="MARKET::CERTIFIED-CONTRACT-FIXTURE",
            structure_class=(
                "KALSHI_ACTIVE_MARKET_OBJECT_PRICE_LEVEL_STRUCTURE"
            ),
            intervals=(interval,),
        ),
    }
    return tuple(
        RuntimeParameterBindingV1(
            binding_id=f"RUNTIME-BINDING::{parameter_id}",
            parameter_id=parameter_id,
            parameter_symbol=get_parameter_policy(parameter_id).parameter_symbol,
            typed_control=control,
            origin=(
                RuntimeParameterBindingOriginV1.CERTIFIED_CONTRACT_FIXTURE
            ),
            source_snapshot_ref=(
                f"CERTIFIED-CONTRACT-FIXTURE::{parameter_id}"
            ),
            source_epoch_id=context.source_epoch_id,
            observed_time=OBSERVED,
            source_available_time=OBSERVED,
            effective_time=OBSERVED,
            as_of_time=context.as_of,
            scope_refs=(
                "MATH-36",
                "QKUComputationControlPlaneServiceV1",
            ),
            unit_or_basis=(
                get_parameter_policy(parameter_id).effective_unit_or_basis
            ),
            freshness_policy=FreshnessPolicyV1(
                policy_id=f"RUNTIME-TTL::{parameter_id}",
                ttl=context.maximum_age,
                parameter_policy_ref=parameter_id,
                stale_behavior="FAIL_CLOSED_OR_REGISTERED_FALLBACK",
            ),
            fixture_authority_ref="ST12B_CERTIFIED_TEST_FIXTURE",
        )
        for parameter_id, control in controls.items()
    )


def test_registered_component_computes_actual_numeric_output_and_mutates(
    service: QKUComputationControlPlaneServiceV1,
) -> None:
    request, evidence = _component_request(Decimal("0.47"), suffix="BASE")
    response = service.compute_component(
        request,
        contextual_evidence=evidence,
    )
    changed_request, changed_evidence = _component_request(
        Decimal("0.52"),
        suffix="MUTATION",
    )
    changed = service.compute_component(
        changed_request,
        contextual_evidence=changed_evidence,
    )

    assert response.status is OperationStatusV1.SUCCEEDED
    assert response.component_result.readiness_state is (
        ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
    )
    assert (
        response.component_result.computability_receipt.resolution.readiness_state
        is ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
    )
    assert response.component_result.output_values.fields[0].value == Decimal(
        "0.47"
    )
    assert changed.component_result.output_values.fields[0].value == Decimal(
        "0.52"
    )
    assert (
        response.component_result.execution_receipt.implementation_id
        == "MATH-01::1.1R1"
    )
    assert (
        response.component_result.execution_receipt.output_json
        != changed.component_result.execution_receipt.output_json
    )


def test_dependency_closed_stack_consumes_actual_upstream_output(
    service: QKUComputationControlPlaneServiceV1,
) -> None:
    request, applicability, evidence = _stack_request(
        Decimal("0.47"),
        suffix="BASE",
    )
    response = service.compute_stack(
        request,
        applicability=applicability,
        contextual_evidence=evidence,
    )
    changed_request, changed_applicability, changed_evidence = _stack_request(
        Decimal("0.52"),
        suffix="MUTATION",
    )
    changed = service.compute_stack(
        changed_request,
        applicability=changed_applicability,
        contextual_evidence=changed_evidence,
    )

    assert response.status is OperationStatusV1.SUCCEEDED
    assert response.stack_result.readiness_state is (
        ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
    )
    assert all(
        result.readiness_state
        is ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
        for result in response.stack_result.component_results
    )
    assert response.stack_result.execution_receipt.topological_order == (
        "MATH-01",
        "MATH-02",
    )
    assert response.stack_result.output_values.fields[0].value == pytest.approx(
        0.13
    )
    assert changed.stack_result.output_values.fields[0].value == pytest.approx(
        0.08
    )
    downstream_input = next(
        row
        for row in response.stack_result.component_results[1]
        .input_resolution_receipt.inputs
        if row.input_field_id == "market_implied_probability"
    )
    assert downstream_input.resolved_value == pytest.approx(0.47)
    assert downstream_input.producer_ref == "MATH-01"
    edge_ref = response.stack_result.execution_receipt.edge_consumption_refs[0]
    assert "MATH-01.p_market->MATH-02.market_implied_probability" in edge_ref
    assert "DECLARED_DECIMAL_TO_FLOAT64_METHOD_BOUNDARY" in edge_ref


def test_component_requirements_parameters_and_public_stack_boundary_matrix(
    service: QKUComputationControlPlaneServiceV1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    math_36_requirement = get_component_execution_requirement("MATH-36")
    assert math_36_requirement.required_parameter_policy_ids == (
        "ST10-PARAM::2212",
        "ST10-PARAM::2213",
    )

    missing_request, missing_evidence = _math_36_request(suffix="MISSING")
    missing = service.compute_component(
        missing_request,
        contextual_evidence=missing_evidence,
    )
    assert missing.status is OperationStatusV1.BLOCKED
    assert missing.component_result.output_values is None
    assert (
        ReasonCode.PARAMETER_RUNTIME_BINDING_REQUIRED
        in missing.component_result.blocker_reason_codes
    )
    assert (
        missing.component_result.input_resolution_receipt.parameter_policy_refs
        == math_36_requirement.required_parameter_policy_ids
    )

    mismatch = service.compute_component(
        missing_request,
        contextual_evidence=missing_evidence,
        parameter_ids=(),
    )
    assert mismatch.status is OperationStatusV1.BLOCKED
    assert (
        ReasonCode.PARAMETER_ASSERTION_MISMATCH
        in mismatch.component_result.blocker_reason_codes
    )
    assert (
        OperationBlockerCodeV1.PARAMETER_REQUIREMENT_MISMATCH
        in mismatch.blocker_codes
    )

    bindings = _math_36_runtime_bindings(missing_request.context)
    executed = service.compute_component(
        missing_request,
        contextual_evidence=missing_evidence,
        runtime_parameter_bindings=bindings,
    )
    assert executed.status is OperationStatusV1.SUCCEEDED
    assert executed.component_result.readiness_state is (
        ComputationReadinessStateV1.PURE_COMPUTATION_ONLY
    )
    asks = safe_json_loads(
        executed.component_result.output_values.fields[0].value
    )
    assert asks["yes_implied_ask"] == "0.44"
    assert asks["no_implied_ask"] == "0.58"
    parameter_receipts = (
        executed.component_result.execution_receipt.parameter_resolution_receipt_refs
    )
    assert len(parameter_receipts) == 2
    assert tuple(
        resolution.parameter_id
        for resolution in executed.component_result.parameter_resolutions
    ) == math_36_requirement.required_parameter_policy_ids
    assert all(
        resolution.application_target
        is ParameterApplicationTargetV1.PRE_CALL_ADMISSION_GUARD
        and resolution.secondary_application_targets
        == (ParameterApplicationTargetV1.POST_CALL_OUTPUT_VALIDATOR,)
        and resolution.receipt_id in parameter_receipts
        for resolution in executed.component_result.parameter_resolutions
    )

    off_grid_request, off_grid_evidence = _math_36_request(
        suffix="OFF-GRID",
        yes_bids='["0.40","0.425"]',
    )
    off_grid = service.compute_component(
        off_grid_request,
        contextual_evidence=off_grid_evidence,
        runtime_parameter_bindings=(
            _math_36_runtime_bindings(off_grid_request.context)
        ),
    )
    assert off_grid.status is OperationStatusV1.BLOCKED
    assert off_grid.component_result.output_values is None
    assert (
        ReasonCode.PARAMETER_OUT_OF_POLICY
        in off_grid.component_result.blocker_reason_codes
    )
    assert off_grid.component_result.fallback_receipt is not None
    assert off_grid.component_result.terminal_route.endswith("OR_NO_TRADE")

    unbound = ParameterPolicyResolverV1.resolve(
        "ST10-PARAM::2212",
        runtime_binding=bindings[0],
        context=missing_request.context,
        application_target=(
            ParameterApplicationTargetV1.RECEIPT_ONLY_NONMATERIAL
        ),
        required_scope_refs=(
            "MATH-36",
            "QKUComputationControlPlaneServiceV1",
        ),
    )
    assert not unbound.computable
    assert (
        unbound.blocker_reason_code
        is ReasonCode.PARAMETER_APPLICATION_UNBOUND
    )
    unauthorized_fixture = ParameterPolicyResolverV1.resolve(
        "ST10-PARAM::2212",
        runtime_binding=bindings[0],
        context=missing_request.context,
        application_target=(
            ParameterApplicationTargetV1.PRE_CALL_ADMISSION_GUARD
        ),
        secondary_application_targets=(
            ParameterApplicationTargetV1.POST_CALL_OUTPUT_VALIDATOR,
        ),
        required_scope_refs=(
            "MATH-36",
            "QKUComputationControlPlaneServiceV1",
        ),
    )
    assert not unauthorized_fixture.computable
    assert (
        unauthorized_fixture.blocker_reason_code
        is ReasonCode.CAPABILITY_DENIED
    )

    certified_empty_contract = MATH_IO_CONTRACTS["MATH-08"]
    certified_empty_inputs = {
        field.name: field for field in certified_empty_contract.inputs
    }
    empty_values = TypedValueRecordV1(
        (
            TypedValueV1(
                "p",
                TypedValueKindV1.FLOAT64,
                0.70,
                certified_empty_inputs["p"].unit,
                certified_empty_inputs["p"].basis,
            ),
            TypedValueV1(
                "y",
                TypedValueKindV1.INTEGER,
                1,
                certified_empty_inputs["y"].unit,
                certified_empty_inputs["y"].basis,
            ),
        )
    )
    empty_request, empty_evidence = _pure_component_request(
        "MATH-08",
        empty_values,
        suffix="CERTIFIED-EMPTY",
    )
    empty_requirement = get_component_execution_requirement("MATH-08")
    assert (
        empty_requirement.terminal_requirement_resolution_state
        is RequirementResolutionStateV1.EXPLICITLY_CERTIFIED_EMPTY_REQUIREMENTS
    )
    assert empty_requirement.required_parameter_policy_ids == ()
    empty = service.compute_component(
        empty_request,
        contextual_evidence=empty_evidence,
    )
    assert empty.status is OperationStatusV1.SUCCEEDED
    assert empty.component_result.output_values.fields[0].value == pytest.approx(
        0.09
    )

    owner_requirement_lookup = (
        service_module.get_component_execution_requirement
    )

    def unresolved_lookup(component_id: str):
        requirement = owner_requirement_lookup(component_id)
        if component_id != "MATH-08":
            return requirement
        return replace(
            requirement,
            terminal_requirement_resolution_state=(
                RequirementResolutionStateV1.UNRESOLVED_REQUIREMENTS_FAIL_CLOSED
            ),
            missing_owner_refs=(
                "OWNER::MISSING-EXACT-SOURCE-OR-PARAMETER-CROSSWALK",
            ),
        )

    monkeypatch.setattr(
        service_module,
        "get_component_execution_requirement",
        unresolved_lookup,
    )
    unresolved = service.compute_component(
        empty_request,
        contextual_evidence=empty_evidence,
    )
    assert unresolved.status is OperationStatusV1.BLOCKED
    assert unresolved.blocker_codes == (
        OperationBlockerCodeV1.EXECUTION_REQUIREMENTS_UNRESOLVED,
    )
    assert unresolved.component_result.output_values is None
    assert (
        ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED
        in unresolved.component_result.blocker_reason_codes
    )
    assert any(
        (
            ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED.value in ref
            or ref
            == "OWNER::MISSING-EXACT-SOURCE-OR-PARAMETER-CROSSWALK"
        )
        for ref in (
            unresolved.component_result.input_resolution_receipt.blocker_detail_refs
        )
    )
    assert (
        "OWNER::MISSING-EXACT-SOURCE-OR-PARAMETER-CROSSWALK"
        in unresolved.component_result.input_resolution_receipt.blocker_detail_refs
    )
    monkeypatch.setattr(
        service_module,
        "get_component_execution_requirement",
        owner_requirement_lookup,
    )

    stack_request, stack_applicability, stack_evidence = _stack_request(
        Decimal("0.47"),
        suffix="NO-APPLICABLE",
    )
    orphan_parameter_assertion = service.compute_stack(
        stack_request,
        applicability=stack_applicability,
        contextual_evidence=stack_evidence,
        parameter_ids_by_component={
            "MATH-36": ("ST10-PARAM::2212", "ST10-PARAM::2213"),
        },
    )
    assert orphan_parameter_assertion.status is OperationStatusV1.BLOCKED
    assert orphan_parameter_assertion.blocker_codes == (
        OperationBlockerCodeV1.PARAMETER_REQUIREMENT_MISMATCH,
    )
    no_applicable = replace(
        stack_applicability,
        venue="UNREGISTERED-EXACT-VENUE",
        input_readiness_state=(
            ComputationReadinessStateV1.SOURCE_CONTEXT_COMPUTABLE
        ),
    )
    resolution_request = ResolveApplicableStackRequestV1(
        request_id="REQUEST-RESOLVE-NO-APPLICABLE",
        operation_name="resolve_applicable_stack",
        requested_at=AS_OF,
        principal_id="ST12B-TEST",
        capability_bundle_id="NO-EFFECT",
        context=stack_request.context,
        idempotency_key="ECONOMIC-IDEMPOTENCY-RESOLVE-NO-APPLICABLE",
        traceparent=TRACEPARENT,
        tracestate="",
        trade_plan_candidate_id=no_applicable.trade_plan_candidate_id,
        required_launch_roles=no_applicable.required_roles,
    )
    with pytest.raises(StackResolutionError) as strict:
        service._stack_resolver.resolve(no_applicable)
    assert strict.value.reason_code is ReasonCode.STACK_NOT_APPLICABLE
    resolved = service.resolve_applicable_stack(
        resolution_request,
        applicability=no_applicable,
    )
    computed = service.compute_stack(
        stack_request,
        applicability=no_applicable,
        contextual_evidence=stack_evidence,
    )
    assert resolved.status is OperationStatusV1.BLOCKED
    assert computed.status is OperationStatusV1.BLOCKED
    assert resolved.blocker_codes == (
        OperationBlockerCodeV1.STACK_NOT_APPLICABLE,
    )
    assert computed.blocker_codes == (
        OperationBlockerCodeV1.STACK_NOT_APPLICABLE,
    )
    assert resolved.stack_resolution.selected_stack_id is None
    assert computed.stack_result.selected_stack_id is None
    assert resolved.stack_resolution.resolution_receipt is not None
    assert computed.stack_result.stack_resolution_receipt is not None
    for receipt in (
        resolved.stack_resolution.resolution_receipt,
        computed.stack_result.stack_resolution_receipt,
    ):
        assert not any(
            (
                receipt.provider_effect,
                receipt.private_state_effect,
                receipt.replay_or_paper_execution_effect,
                receipt.qpu_effect,
                receipt.mode_or_grant_effect,
                receipt.order_release_effect,
            )
        )

    def unexpected_failure(_resolver, _applicability):
        raise RuntimeError("unexpected programming failure")

    monkeypatch.setattr(
        type(service._stack_resolver),
        "resolve",
        unexpected_failure,
    )
    with pytest.raises(RuntimeError, match="unexpected programming failure"):
        service.resolve_applicable_stack(
            resolution_request,
            applicability=no_applicable,
        )


def test_service_routes_and_structured_explanation_are_scope_pure(
    service: QKUComputationControlPlaneServiceV1,
) -> None:
    request, evidence = _component_request(Decimal("0.47"), suffix="EXPLAIN")
    computed = service.compute_component(
        request,
        contextual_evidence=evidence,
    )
    receipt_id = computed.component_result.execution_receipt.receipt_id
    explanation_request = ExplainResolutionRequestV1(
        request_id="REQUEST-EXPLAIN",
        operation_name="explain_resolution",
        requested_at=AS_OF,
        principal_id="ST12B-TEST",
        capability_bundle_id="NO-EFFECT",
        context=request.context,
        idempotency_key="ECONOMIC-IDEMPOTENCY-EXPLAIN",
        traceparent=TRACEPARENT,
        tracestate="",
        resolution_receipt_id=receipt_id,
        explanation_scope="OWNER_TYPED_AUDIT",
        max_evidence_items=100,
    )
    explained = service.explain_resolution(
        explanation_request,
        resolution=computed.component_result,
        owner_preferences_and_candidate_assertions=("OWNER_TARGET_IS_NOT_FACT",),
    )

    assert explained.status is OperationStatusV1.SUCCEEDED
    assert isinstance(
        explained.explanation,
        StructuredResolutionExplanationV1,
    )
    assert explained.explanation.trusted_typed_input_facts
    assert explained.explanation.owner_preferences_and_candidate_assertions == (
        "OWNER_TARGET_IS_NOT_FACT",
    )
    assert explained.explanation.formula_and_implementation_lineage
    assert explained.explanation.point_in_time_and_freshness_state
    assert "NO_QPU_EFFECT" in explained.explanation.forbidden_effects
    assert len(service.service_bindings) == 15
    assert len(AGENT_DUTY_ROUTES) == 8
    assert len(INSTITUTIONAL_FEATURE_SOCKETS) == 9
