"""Real numeric execution proofs for the one Tranche-B service surface."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.freshness import (
    FreshnessPolicyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    ContextualInputValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputeComponentRequestV1,
    ComputeStackRequestV1,
    ExplainResolutionRequestV1,
    OperationStatusV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeFieldClassV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    AGENT_DUTY_ROUTES,
    INSTITUTIONAL_FEATURE_SOCKETS,
    QKUComputationControlPlaneServiceV1,
    StructuredResolutionExplanationV1,
    output_schema_ref,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    StackApplicabilityContextV1,
)


AS_OF = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
OBSERVED = AS_OF - timedelta(seconds=30)
TRACEPARENT = "00-11111111111111111111111111111111-2222222222222222-01"


@pytest.fixture(scope="module")
def service() -> QKUComputationControlPlaneServiceV1:
    return QKUComputationControlPlaneServiceV1(repo_root=Path.cwd())


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
        source_identity="OWNER_SUPPLIED_TYPED_PURE_COMPUTATION_CONTEXT",
        source_state_id=f"SOURCE-STATE::{context.input_version}",
        source_epoch_id=context.source_epoch_id,
        rights_state="ACCEPTED_OWNER_SUPPLIED_PURE_INPUT",
        value_lineage_ref=f"VALUE::{context.input_version}::{value.name}",
        precision_policy="DECIMAL34_OR_DECLARED_FLOAT64_METHOD_BOUNDARY",
        rounding_policy="NO_IMPLICIT_QUANTIZATION",
        producer_ref="ST12B_CERTIFIED_INTEGRATION_VECTOR",
        consumer_refs=("QKUComputationControlPlaneServiceV1",),
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
        source_readiness_receipt_refs=(f"SOURCE-READINESS-{suffix}",),
        consumer_refs=("READINESS1", "PRETRADE1", "SVC1", "AGENT-ORCH1"),
    )
    return (
        request,
        applicability,
        tuple(_evidence(value, context) for value in values.fields),
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
