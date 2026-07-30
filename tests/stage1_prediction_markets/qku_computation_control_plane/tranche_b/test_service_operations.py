import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.identity_adapter import (
    RP5CIdentityAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    OwnerValuePacketV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    CompareWithNoTradeRequestV1,
    ComputabilityClassV1,
    ComputeComponentRequestV1,
    ComputeStackRequestV1,
    EvaluateTradePlanRequestV1,
    ExplainResolutionRequestV1,
    GetSnapshotViewRequestV1,
    OperationBlockerCodeV1,
    OperationCapabilityClass,
    OperationStatusV1,
    RequestMaterializationWorkOrderRequestV1,
    ResolveApplicableStackRequestV1,
    ResolveContextualComputabilityRequestV1,
    ResolveIdentityRequestV1,
    ResolveRequiredInputsRequestV1,
    SubmitCandidateProposalRequestV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PointInTimeClocksV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12B_CENTRAL_SERVICE_OPERATION_IDS,
    ST12B_OPERATION_CAPABILITY_BY_ID,
)


AS_OF = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)
TRACEPARENT = (
    "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
)


def _context() -> ComputationContextKeyV1:
    return ComputationContextKeyV1(
        context_id="CTX::SERVICE",
        as_of=AS_OF,
        observed_at=AS_OF - timedelta(seconds=1),
        source_epoch_id="EPOCH::SERVICE",
        input_version="V1",
        maximum_age=timedelta(days=1),
    )


def _packets(
    context: ComputationContextKeyV1,
) -> tuple[OwnerValuePacketV1, ...]:
    clocks = PointInTimeClocksV1(
        observed_time=AS_OF - timedelta(seconds=1),
        effective_time=AS_OF - timedelta(seconds=1),
        available_time=AS_OF - timedelta(seconds=1),
        received_time=AS_OF - timedelta(seconds=1),
        processed_time=AS_OF - timedelta(seconds=1),
        as_of_time=AS_OF,
    )
    packets = []
    for math_id in ("MATH-01", "MATH-02"):
        inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
        for binding in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]:
            if (
                math_id == "MATH-02"
                and binding.input_name == "market_implied_probability"
            ):
                continue
            packets.append(
                OwnerValuePacketV1(
                    packet_id=f"PACKET::{binding.binding_id}",
                    owner_id=binding.accepted_upstream_owner_id,
                    packet_type=binding.accepted_packet_or_snapshot_type,
                    schema_id=binding.schema_id,
                    schema_version=binding.schema_version,
                    context_id=context.context_id,
                    source_epoch_id=context.source_epoch_id,
                    clocks=clocks,
                    ttl=timedelta(days=1),
                    values={
                        binding.exact_field_path: inputs[binding.input_name]
                    },
                    authorized_binding_ids=(binding.binding_id,),
                    producer_receipt_id=f"RECEIPT::{binding.binding_id}",
                    producer_receipt_type=binding.producer_receipt_type,
                    source_state_and_claim_lineage=(
                        binding.source_state_and_claim_lineage
                    ),
                    provider_sequence=1,
                    revision=1,
                )
            )
    return tuple(packets)


def _common(operation_name: str) -> dict[str, object]:
    return {
        "request_id": f"REQUEST::{operation_name}",
        "operation_name": operation_name,
        "requested_at": AS_OF,
        "principal_id": "OWNER::TEST",
        "capability_bundle_id": "CAPABILITY::READ_ONLY_TEST",
        "context": _context(),
        "idempotency_key": f"IDEMPOTENCY::{operation_name}",
        "traceparent": TRACEPARENT,
        "tracestate": "",
    }


def _text_record(name: str, value: str) -> TypedValueRecordV1:
    return TypedValueRecordV1(
        (
            TypedValueV1(
                name=name,
                kind=TypedValueKindV1.TEXT,
                value=value,
                unit="identity",
                basis="canonical",
            ),
        )
    )


def _component_record() -> TypedValueRecordV1:
    return TypedValueRecordV1(
        (
            TypedValueV1(
                "contract_price",
                TypedValueKindV1.DECIMAL,
                Decimal("0.47"),
                "currency per contract",
                "declared contract",
            ),
            TypedValueV1(
                "payout_per_winning_contract",
                TypedValueKindV1.DECIMAL,
                Decimal("1.00"),
                "currency per winning contract",
                "declared contract",
            ),
        )
    )


def _stack_record() -> TypedValueRecordV1:
    return TypedValueRecordV1(
        (
            TypedValueV1(
                "MATH-01.contract_price",
                TypedValueKindV1.DECIMAL,
                Decimal("0.47"),
                "currency per contract",
                "declared contract",
            ),
            TypedValueV1(
                "MATH-01.payout_per_winning_contract",
                TypedValueKindV1.DECIMAL,
                Decimal("1.00"),
                "currency per winning contract",
                "declared contract",
            ),
            TypedValueV1(
                "MATH-02.calibrated_model_probability",
                TypedValueKindV1.FLOAT64,
                0.61,
                "probability",
                "calibrated model",
            ),
            TypedValueV1(
                "MATH-02.calibration_state",
                TypedValueKindV1.TEXT,
                "CALIBRATED_FOR_DECLARED_CONTEXT",
                "state",
                "calibration receipt",
            ),
        )
    )


def _service() -> QKUComputationControlPlaneV1:
    repo_root = Path(__file__).resolve().parents[4]
    context = _context()
    return QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(_packets(context)),
        identity_adapter=RP5CIdentityAdapterV1(repo_root),
    )


def test_service_exposes_exact_twelve_operations_and_holds_three_schemas() -> None:
    service = _service()
    operation_names = (
        "resolve_identity",
        "resolve_contextual_computability",
        "resolve_applicable_stack",
        "resolve_required_inputs",
        "compute_component",
        "compute_stack",
        "compare_with_no_trade",
        "evaluate_trade_plan",
        "get_snapshot_view",
        "explain_resolution",
        "submit_candidate_proposal",
        "request_materialization_work_order",
    )

    assert len(ST12B_CENTRAL_SERVICE_OPERATION_IDS) == 12
    assert all(callable(getattr(service, name)) for name in operation_names)
    assert not hasattr(service, "compile_replay_paper_cohort")
    assert not hasattr(service, "register_replay_paper_result")
    assert not hasattr(service, "build_evidence_bundle")
    assert all(
        ST12B_OPERATION_CAPABILITY_BY_ID[operation_id]
        is OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
        for operation_id in ("ST10-OP::13", "ST10-OP::14", "ST10-OP::15")
    )


def test_identity_computability_stack_and_required_input_resolution() -> None:
    service = _service()

    math_identity = service.resolve_identity(
        ResolveIdentityRequestV1(
            **_common("resolve_identity"),
            identity_query=_text_record("math_spec_id", "MATH-01"),
        )
    )
    formula_identity = service.resolve_identity(
        ResolveIdentityRequestV1(
            **{
                **_common("resolve_identity"),
                "request_id": "REQUEST::resolve_identity::formula",
                "idempotency_key": "IDEMPOTENCY::resolve_identity::formula",
            },
            identity_query=_text_record("formula_id", "FORMULA_QKU"),
        )
    )
    computability = service.resolve_contextual_computability(
        ResolveContextualComputabilityRequestV1(
            **_common("resolve_contextual_computability"),
            component_id="MATH-01",
            required_computability_classes=tuple(ComputabilityClassV1),
        )
    )
    stack = service.resolve_applicable_stack(
        ResolveApplicableStackRequestV1(
            **_common("resolve_applicable_stack"),
            trade_plan_candidate_id="TRADE_PLAN::TEST",
            required_launch_roles=("MATH-01", "MATH-02"),
        )
    )
    required = service.resolve_required_inputs(
        ResolveRequiredInputsRequestV1(
            **_common("resolve_required_inputs"),
            component_ids=("MATH-01",),
            include_optional=False,
        )
    )

    assert math_identity.status is OperationStatusV1.SUCCEEDED
    assert math_identity.identity_resolution.identity_ref == "MATH-01"
    assert formula_identity.status is OperationStatusV1.SUCCEEDED
    assert (
        formula_identity.identity_resolution.identity_ref
        == "RP5C_IDENTITY_00000001"
    )
    assert computability.status is OperationStatusV1.SUCCEEDED
    assert computability.computability.context.computable
    assert stack.status is OperationStatusV1.SUCCEEDED
    assert (
        stack.stack_resolution.stack_id
        == "STACK::MATH-01::MATH-02::V3_4"
    )
    assert required.status is OperationStatusV1.SUCCEEDED
    assert len(required.input_resolution.resolved_input_names) == 2


def test_component_and_stack_operations_return_frozen_typed_outputs() -> None:
    service = _service()
    component = service.compute_component(
        ComputeComponentRequestV1(
            **_common("compute_component"),
            component_id="MATH-01",
            input_values=_component_record(),
            expected_output_schema_ref="MATH-01::OUTPUT",
        )
    )
    stack = service.compute_stack(
        ComputeStackRequestV1(
            **_common("compute_stack"),
            stack_id="STACK::MATH-01::MATH-02::V3_4",
            component_ids=("MATH-01", "MATH-02"),
            input_values=_stack_record(),
        )
    )

    assert component.status is OperationStatusV1.SUCCEEDED
    assert component.component_result.formula_output is not None
    assert (
        component.component_result.formula_output.value == Decimal("0.47")
    )
    assert (
        component.component_result.formula_output.output_schema_version
        == "ST12B_OUTPUT_V3_4"
    )
    assert stack.status is OperationStatusV1.SUCCEEDED
    assert tuple(
        output.value for output in stack.stack_result.component_outputs
    ) == (Decimal("0.47"), 0.14)
    assert len(stack.stack_result.conversion_receipt_refs) == 2
    assert all(
        output.no_authority_flag
        for output in stack.stack_result.component_outputs
    )


def test_downstream_routes_views_and_no_effect_records_are_typed() -> None:
    service = _service()
    responses = (
        service.compare_with_no_trade(
            CompareWithNoTradeRequestV1(
                **_common("compare_with_no_trade"),
                trade_plan_candidate_id="TRADE::1",
                no_trade_candidate_id="NO_TRADE::1",
                comparison_basis="EXACT_NET_FRICTION_BASIS",
            )
        ),
        service.evaluate_trade_plan(
            EvaluateTradePlanRequestV1(
                **_common("evaluate_trade_plan"),
                trade_plan_candidate_id="TRADE::1",
                stack_id="STACK::MATH-01::MATH-02::V3_4",
                accounting_tca_view_ref="ACCOUNTING::1",
                risk_cash_state_ref="RISK::1",
                no_trade_candidate_id="NO_TRADE::1",
            )
        ),
        service.get_snapshot_view(
            GetSnapshotViewRequestV1(
                **_common("get_snapshot_view"),
                snapshot_id=service.owner_registry.packets[0].packet_id,
                view_class="OWNER_PACKET_LINEAGE",
                include_value_lineage=True,
            )
        ),
        service.explain_resolution(
            ExplainResolutionRequestV1(
                **_common("explain_resolution"),
                resolution_receipt_id="RECEIPT::RESOLUTION::1",
                explanation_scope="EXACT_TYPED_RECEIPT",
                max_evidence_items=10,
            )
        ),
        service.submit_candidate_proposal(
            SubmitCandidateProposalRequestV1(
                **_common("submit_candidate_proposal"),
                candidate_kind="FORMULA_SUCCESSOR",
                proposed_specification=_text_record(
                    "candidate_state", "PROVISIONAL"
                ),
                source_candidate_refs=("SOURCE::CANDIDATE::1",),
                requested_owner_review=True,
            )
        ),
        service.request_materialization_work_order(
            RequestMaterializationWorkOrderRequestV1(
                **_common("request_materialization_work_order"),
                missing_contract_ids=("MISSING::1",),
                reason_codes=(
                    OperationBlockerCodeV1.INPUT_OWNER_MISSING,
                ),
                priority="OWNER_REVIEW",
                requested_owner="CanonicalOwnerV1",
            )
        ),
    )

    assert tuple(response.status for response in responses) == (
        OperationStatusV1.BLOCKED,
        OperationStatusV1.BLOCKED,
        OperationStatusV1.SUCCEEDED,
        OperationStatusV1.SUCCEEDED,
        OperationStatusV1.SUCCEEDED,
        OperationStatusV1.SUCCEEDED,
    )
    assert responses[4].proposal.proposal_state == "NO_EFFECT_RECORD"
    assert responses[4].proposal.no_authority_flag is True
    assert responses[5].work_order.work_order_state == "NO_EFFECT_RECORD"
    assert responses[5].work_order.no_authority_flag is True


def test_expected_failure_translates_without_fabricated_result() -> None:
    service = _service()
    response = service.compute_component(
        ComputeComponentRequestV1(
            **_common("compute_component"),
            component_id="MATH-UNKNOWN",
            input_values=_component_record(),
            expected_output_schema_ref="MATH-UNKNOWN::OUTPUT",
        )
    )

    assert response.status is OperationStatusV1.REJECTED
    assert response.blocker_codes
    assert response.component_result.formula_output is None
    assert response.component_result.no_authority_flag is True
