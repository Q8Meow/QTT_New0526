from dataclasses import fields
from datetime import UTC, datetime, timedelta

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    IdentityResolutionV1,
    OperationBlockerCodeV1,
    OperationCapabilityClass,
    OperationSideEffectClass,
    OperationStatusV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    OPERATION_SCHEMA_REGISTRY,
    TRANCHE_A_OPERATION_CONTRACTS,
    validate_operation_contract_closure,
)


COMMON_REQUEST = (
    "request_id",
    "operation_name",
    "requested_at",
    "principal_id",
    "capability_bundle_id",
    "context",
    "idempotency_key",
    "traceparent",
    "tracestate",
)
COMMON_RESPONSE = (
    "response_id",
    "operation_name",
    "request_id",
    "completed_at",
    "status",
    "context",
    "warnings",
    "blocker_codes",
    "receipt_refs",
    "traceparent",
    "tracestate",
)
EXPECTED = (
    ("ST10-OP::01", "resolve_identity", "UnifiedCanonicalIdentityPlaneV1", "ResolveIdentityRequestV1", "ResolveIdentityResponseV1", ("identity_query",), "identity_resolution"),
    ("ST10-OP::02", "resolve_contextual_computability", "QKUComputationControlPlaneV1", "ResolveContextualComputabilityRequestV1", "ResolveContextualComputabilityResponseV1", ("component_id", "required_computability_classes"), "computability"),
    ("ST10-OP::03", "resolve_applicable_stack", "QKUComputationControlPlaneV1", "ResolveApplicableStackRequestV1", "ResolveApplicableStackResponseV1", ("trade_plan_candidate_id", "required_launch_roles"), "stack_resolution"),
    ("ST10-OP::04", "resolve_required_inputs", "QKUComputationControlPlaneV1", "ResolveRequiredInputsRequestV1", "ResolveRequiredInputsResponseV1", ("component_ids", "include_optional"), "input_resolution"),
    ("ST10-OP::05", "compute_component", "QKUComputationControlPlaneV1", "ComputeComponentRequestV1", "ComputeComponentResponseV1", ("component_id", "input_values", "expected_output_schema_ref"), "component_result"),
    ("ST10-OP::06", "compute_stack", "QKUComputationControlPlaneV1", "ComputeStackRequestV1", "ComputeStackResponseV1", ("stack_id", "component_ids", "input_values"), "stack_result"),
    ("ST10-OP::07", "compare_with_no_trade", "QKUComputationControlPlaneV1", "CompareWithNoTradeRequestV1", "CompareWithNoTradeResponseV1", ("trade_plan_candidate_id", "no_trade_candidate_id", "comparison_basis"), "comparison"),
    ("ST10-OP::08", "evaluate_trade_plan", "QKUComputationControlPlaneV1", "EvaluateTradePlanRequestV1", "EvaluateTradePlanResponseV1", ("trade_plan_candidate_id", "stack_id", "accounting_tca_view_ref", "risk_cash_state_ref", "no_trade_candidate_id"), "evaluation"),
    ("ST10-OP::09", "get_snapshot_view", "QKUComputationControlPlaneV1", "GetSnapshotViewRequestV1", "GetSnapshotViewResponseV1", ("snapshot_id", "view_class", "include_value_lineage"), "snapshot_view"),
    ("ST10-OP::10", "explain_resolution", "QKUComputationControlPlaneV1", "ExplainResolutionRequestV1", "ExplainResolutionResponseV1", ("resolution_receipt_id", "explanation_scope", "max_evidence_items"), "explanation"),
    ("ST10-OP::11", "submit_candidate_proposal", "QKUComputationControlPlaneV1", "SubmitCandidateProposalRequestV1", "SubmitCandidateProposalResponseV1", ("candidate_kind", "proposed_specification", "source_candidate_refs", "requested_owner_review"), "proposal"),
    ("ST10-OP::12", "request_materialization_work_order", "QKUComputationControlPlaneV1", "RequestMaterializationWorkOrderRequestV1", "RequestMaterializationWorkOrderResponseV1", ("missing_contract_ids", "reason_codes", "priority", "requested_owner"), "work_order"),
    ("ST10-OP::13", "compile_replay_paper_cohort", "ReplayPaperCohortCompilerV1", "CompileReplayPaperCohortRequestV1", "CompileReplayPaperCohortResponseV1", ("template_ids", "requested_lanes", "input_lock_id", "campaign_execution_requested"), "cohort_compilation"),
    ("ST10-OP::14", "register_replay_paper_result", "ComputationEvidenceServiceV1", "RegisterReplayPaperResultRequestV1", "RegisterReplayPaperResultResponseV1", ("cohort_instance_id", "lane", "input_lock_id", "result_packet"), "registration"),
    ("ST10-OP::15", "build_evidence_bundle", "ComputationEvidenceServiceV1", "BuildEvidenceBundleRequestV1", "BuildEvidenceBundleResponseV1", ("component_id", "input_lock_id", "evidence_record_refs", "required_lanes"), "evidence_bundle"),
)


def _common_request(operation_name: str) -> dict[str, object]:
    moment = datetime(2026, 7, 24, 12, tzinfo=UTC)
    return {
        "request_id": "request-1",
        "operation_name": operation_name,
        "requested_at": moment,
        "principal_id": "principal-1",
        "capability_bundle_id": "default-deny",
        "context": ComputationContextKeyV1(
            "context-1",
            moment,
            moment,
            "source-epoch",
            "input-v1",
            timedelta(minutes=1),
        ),
        "idempotency_key": "economic-intent-1",
        "traceparent": (
            "00-4bf92f3577b34da6a3ce929d0e0e4736-"
            "00f067aa0ba902b7-01"
        ),
        "tracestate": "vendor=value",
    }


def test_operation_roster_and_top_level_schemas_are_exact() -> None:
    operations = validate_operation_contract_closure()
    assert operations is TRANCHE_A_OPERATION_CONTRACTS
    assert tuple(OPERATION_SCHEMA_REGISTRY) == tuple(row[0] for row in EXPECTED)
    actual = tuple(
        (
            operation.operation_id,
            operation.operation_name,
            operation.owner,
            operation.request_type,
            operation.response_type,
            tuple(field.name for field in operation.request_fields),
            tuple(field.name for field in operation.response_fields),
        )
        for operation in operations
    )
    assert actual == tuple(
        (
            operation_id,
            operation_name,
            owner,
            request_type,
            response_type,
            (*COMMON_REQUEST, *request_tail),
            (*COMMON_RESPONSE, response_tail),
        )
        for (
            operation_id,
            operation_name,
            owner,
            request_type,
            response_type,
            request_tail,
            response_tail,
        ) in EXPECTED
    )
    assert all(operation.schema_version == "1.4.0" for operation in operations)
    assert all(
        operation.capability_class
        is OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
        and operation.side_effect_class
        is OperationSideEffectClass.PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT
        and not operation.runtime_effect_authorized
        and not operation.provider_effect_authorized
        for operation in operations
    )
    assert not {
        "resolve_formula",
        "compile_contract",
        "execute_formula",
    } & {operation.operation_name for operation in operations}


def test_request_response_strictness_trace_and_determinism() -> None:
    operation = OPERATION_SCHEMA_REGISTRY["ST10-OP::01"]
    values = _common_request(operation.operation_name)
    values["identity_query"] = TypedValueRecordV1(
        (
            TypedValueV1(
                "formula_id",
                TypedValueKindV1.TEXT,
                "FORMULA_QKU",
                "identifier",
                "RP5C",
            ),
        )
    )
    request = operation.bind_request(**values)
    request_json = operation.request_json(request)
    operation.validate_request_json(request, request_json)
    assert request_json == operation.request_json(request)
    with pytest.raises(ContractValidationError):
        operation.validate_request_json(request, request_json + " ")

    response = operation.bind_response(
        request,
        response_id="response-1",
        operation_name=operation.operation_name,
        request_id=request.request_id,
        completed_at=request.requested_at,
        status=OperationStatusV1.SUCCEEDED,
        context=request.context,
        warnings=(),
        blocker_codes=(),
        receipt_refs=("identity-receipt-1",),
        traceparent=request.traceparent,
        tracestate=request.tracestate,
        identity_resolution=IdentityResolutionV1(
            "identity-resolution-1",
            "RETURN_READ_ONLY_VIEW",
            ("identity-receipt-1",),
        ),
    )
    response_json = operation.response_json(response)
    operation.validate_response_json(response, response_json)
    assert tuple(field.name for field in fields(type(response))) == (
        *COMMON_RESPONSE,
        "identity_resolution",
    )

    for mutation in (
        {key: value for key, value in values.items() if key != "identity_query"},
        {**values, "extra": "forbidden"},
        {**values, "operation_name": "resolve_identity_suffix"},
        {**values, "idempotency_key": values["request_id"]},
        {
            **values,
            "idempotency_key": "00f067aa0ba902b7",
        },
        {
            **values,
            "idempotency_key": values["tracestate"],
        },
        {**values, "traceparent": "00-" + "0" * 32 + "-" + "1" * 16 + "-01"},
        {**values, "tracestate": "a=" + "x" * 513},
        {**values, "tracestate": "1vendor=value"},
        {**values, "tracestate": "tenant@1system=value"},
    ):
        with pytest.raises(ContractValidationError):
            operation.bind_request(**mutation)
    operation.bind_request(
        **{**values, "tracestate": "1tenant@system_id=value"}
    )
    with pytest.raises(ContractValidationError):
        operation.bind_response(
            request,
            response_id="response-2",
            operation_name=operation.operation_name,
            request_id=request.request_id,
            completed_at=request.requested_at,
            status=OperationStatusV1.BLOCKED,
            context=request.context,
            warnings=("duplicate", "duplicate"),
            blocker_codes=(OperationBlockerCodeV1.INVALID_REQUEST,),
            receipt_refs=(),
            traceparent=request.traceparent,
            tracestate=request.tracestate,
            identity_resolution=IdentityResolutionV1(
                "identity-resolution-2",
                "FAIL_CLOSED",
                (),
            ),
        )


def test_replay_paper_named_operation_is_contract_definition_only() -> None:
    operation = OPERATION_SCHEMA_REGISTRY["ST10-OP::13"]
    values = _common_request(operation.operation_name)
    values.update(
        {
            "template_ids": ("template-1",),
            "requested_lanes": ("REPLAY", "PAPER"),
            "input_lock_id": "input-lock-1",
            "campaign_execution_requested": False,
        }
    )
    request = operation.bind_request(**values)
    assert request.campaign_execution_requested is False
    with pytest.raises(ContractValidationError):
        operation.bind_request(
            **{**values, "campaign_execution_requested": True}
        )
