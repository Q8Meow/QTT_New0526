import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    POLICY_VERSION,
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.identity_adapter import (
    RP5CIdentityAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    invoke_formula_v34,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    OwnerValuePacketV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    CompareWithNoTradeRequestV1,
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    ComputabilityTerminalRouteV1,
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ComputeComponentRequestV1,
    ComputeStackRequestV1,
    EvaluateTradePlanRequestV1,
    ExplainResolutionRequestV1,
    GetSnapshotViewRequestV1,
    ImplementationVersionPinV1,
    OperationBlockerCodeV1,
    OperationCapabilityClass,
    OperationStatusV1,
    RequestMaterializationWorkOrderRequestV1,
    ResolveApplicableStackRequestV1,
    ResolveContextualComputabilityRequestV1,
    ResolveContextualComputabilityResponseV1,
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
    ST12B_FROZEN_PACKAGE_VERSION,
)
import src.qtt.stage1_prediction_markets.qku_computation_control_plane.service as service_module
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (
    ApplicableStackResolverV1,
)
import src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver as stack_resolver_module
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12B_CENTRAL_SERVICE_OPERATION_IDS,
    ST12B_OPERATION_CAPABILITY_BY_ID,
)


AS_OF = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)
TRACEPARENT = (
    "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
)
STACK_ID = "STACK::MATH-01::MATH-02::V3_4"


class _ExplicitNoEffectTestAdmission:
    """One explicit test-only admission double for legacy service matrices."""

    def admit_operation(self, request: object) -> AgentCapabilityDecisionV1:
        request_id = str(getattr(request, "request_id"))
        operation_id = str(getattr(request, "operation_name"))
        principal_id = str(getattr(request, "principal_id"))
        idempotency_key = str(getattr(request, "idempotency_key"))
        return AgentCapabilityDecisionV1(
            decision_id=f"TEST_DECISION::{request_id}::{operation_id}",
            request_id=request_id,
            task_id=f"TEST_TASK::{request_id}",
            principal_id=principal_id,
            current_agent_id="dashboard_agent",
            source_agent_refs=("AGENT_RT_11",),
            operation_id=operation_id,
            policy_version=POLICY_VERSION,
            decision_state=(
                AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
            ),
            reason_codes=(),
            scope_refs=(
                f"operation_id={operation_id}",
                "test_fixture=EXPLICIT_NO_EFFECT_ADMISSION",
            ),
            idempotency_key=idempotency_key,
            retry_disposition="NO_RETRY_AUTHORITY",
            peer_sod_disposition="TEST_FIXTURE_NO_SELF_APPROVAL",
            safety_state_disposition="NON_MATERIAL_LOCAL_NO_EFFECT",
            terminal_route="QKUComputationControlPlaneV1_NO_EFFECT_REQUEST",
            agent_orch_receipt_ref=(
                f"AGENT_ORCH1::TEST_FIXTURE_RECEIPT::{request_id}"
            ),
            st12c_causation_correlation_refs=(
                f"OperationRequestEnvelopeV1.request_id={request_id}",
                f"OperationRequestEnvelopeV1.idempotency_key={idempotency_key}",
            ),
            evidence_refs=("EXPLICIT_TEST_FIXTURE",),
            alternative_route_refs=("DENY_TASK",),
            disagreement_state="NONE_DECLARED",
            confidence_state="TEST_FIXTURE_ONLY",
            limitation_codes=(
                "NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_RUNTIME_EFFECT",
                "QKU_AND_FORMULA_IMMUTABLE",
            ),
        )


_EXPLICIT_NO_EFFECT_TEST_ADMISSION = _ExplicitNoEffectTestAdmission()


def _scope() -> ComputationScopeV1:
    return ComputationScopeV1(
        market_scope_id="MARKET::SERVICE",
        venue_scope_id="VENUE::SERVICE",
        event_scope_id="EVENT::SERVICE",
        instrument_or_contract_scope_id="CONTRACT::SERVICE",
        mode_context_id="MODE_CONTEXT::CONTRACT_ONLY",
        input_snapshot_id="SNAPSHOT::SERVICE::V1",
    )


def _pins(
    component_ids: tuple[str, ...],
) -> tuple[ImplementationVersionPinV1, ...]:
    return tuple(
        ImplementationVersionPinV1(
            math_spec_id=component_id,
            implementation_id=IMPLEMENTATION_REGISTRY[
                component_id
            ].contract.implementation_id,
        )
        for component_id in component_ids
    )


def _context(
    *,
    component_ids: tuple[str, ...] = ("MATH-01",),
    dependency_graph_id: str | None = None,
    dependency_graph_version: str | None = None,
    binding_profile_version: str = ST12B_FROZEN_PACKAGE_VERSION,
    parameter_policy_version: str = ST12B_FROZEN_PACKAGE_VERSION,
    implementation_versions: tuple[
        ImplementationVersionPinV1, ...
    ] | None = None,
) -> ComputationExecutionContextV1:
    return ComputationExecutionContextV1(
        context_id="CTX::SERVICE",
        as_of=AS_OF,
        observed_at=AS_OF - timedelta(seconds=1),
        source_epoch_id="EPOCH::SERVICE",
        input_version="V1",
        maximum_age=timedelta(days=1),
        scope=_scope(),
        binding_profile_version=binding_profile_version,
        parameter_policy_version=parameter_policy_version,
        implementation_versions=(
            implementation_versions
            if implementation_versions is not None
            else _pins(component_ids)
        ),
        dependency_graph_id=dependency_graph_id,
        dependency_graph_version=(
            dependency_graph_version or "3.4"
            if dependency_graph_id is not None
            else None
        ),
    )


def _packets(
    context: ComputationExecutionContextV1,
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
                    scope=context.scope,
                    source_epoch_id=context.source_epoch_id,
                    input_version=context.input_version,
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


def _common(
    operation_name: str,
    *,
    context: ComputationExecutionContextV1 | None = None,
) -> dict[str, object]:
    return {
        "request_id": f"REQUEST::{operation_name}",
        "operation_name": operation_name,
        "requested_at": AS_OF,
        "principal_id": "OWNER::TEST",
        "capability_bundle_id": "CAPABILITY::READ_ONLY_TEST",
        "context": context or _context(),
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
        agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION,
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
            **_common(
                "resolve_contextual_computability",
                context=_context(
                    component_ids=("MATH-01", "MATH-02"),
                    dependency_graph_id=STACK_ID,
                ),
            ),
            component_id="MATH-01",
            required_computability_classes=tuple(ComputabilityClassV1),
        )
    )
    stack = service.resolve_applicable_stack(
        ResolveApplicableStackRequestV1(
            **_common(
                "resolve_applicable_stack",
                context=_context(
                    component_ids=("MATH-01", "MATH-02"),
                    dependency_graph_id=STACK_ID,
                ),
            ),
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


def test_service_plan_and_stack_admission_matrix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service()
    invocations: list[str] = []

    def counted_invoke(math_spec_id: str, inputs: object) -> object:
        invocations.append(math_spec_id)
        return invoke_formula_v34(math_spec_id, inputs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        service_module,
        "invoke_formula_v34",
        counted_invoke,
    )
    monkeypatch.setattr(
        stack_resolver_module,
        "invoke_formula_v34",
        counted_invoke,
    )

    stack_context = _context(
        component_ids=("MATH-01", "MATH-02"),
        dependency_graph_id=STACK_ID,
    )
    external_packets = _packets(stack_context)
    derived_binding_id = "FIVAB::MATH-02::market_implied_probability"
    assert all(
        derived_binding_id not in packet.authorized_binding_ids
        for packet in external_packets
    )

    def contextual_response(
        component_id: str,
        packets: tuple[OwnerValuePacketV1, ...],
    ) -> ResolveContextualComputabilityResponseV1:
        contextual_service = QKUComputationControlPlaneV1(
            CanonicalOwnerPacketRegistryV1(packets),
            agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION,
        )
        return contextual_service.resolve_contextual_computability(
            ResolveContextualComputabilityRequestV1(
                **_common(
                    "resolve_contextual_computability",
                    context=stack_context,
                ),
                component_id=component_id,
                required_computability_classes=tuple(
                    ComputabilityClassV1
                ),
            )
        )

    invocations.clear()
    exact_contextual = tuple(
        contextual_response(component_id, external_packets)
        for component_id in ("MATH-01", "MATH-02")
    )
    assert all(
        response.computability.context.computable
        and response.computability.stack.computable
        for response in exact_contextual
    )
    assert all(
        any(
            ref.startswith("NO_EXECUTION_STACK_CLOSURE::")
            for ref in response.receipt_refs
        )
        for response in exact_contextual
    )
    math_02_contextual = exact_contextual[1]
    assert derived_binding_id in (
        math_02_contextual.computability.context.dependency_receipt_refs
    )
    assert (
        "EDGE::MATH-01::MATH-02"
        in math_02_contextual.computability.context.dependency_receipt_refs
    )
    assert invocations == []

    upstream_binding_id = "FIVAB::MATH-01::contract_price"
    missing_upstream_packets = tuple(
        packet
        for packet in external_packets
        if upstream_binding_id not in packet.authorized_binding_ids
    )
    invocations.clear()
    missing_upstream = contextual_response(
        "MATH-02", missing_upstream_packets
    )
    assert not missing_upstream.computability.context.computable
    assert missing_upstream.computability.context.blocker_codes == (
        ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE,
    )
    assert (
        missing_upstream.computability.context.terminal_route
        is ComputabilityTerminalRouteV1.STACK_CLOSURE
    )
    assert derived_binding_id not in (
        missing_upstream.computability.context.dependency_receipt_refs
    )
    assert (
        "EDGE::MATH-01::MATH-02"
        in missing_upstream.computability.context.dependency_receipt_refs
    )
    assert not missing_upstream.computability.stack.computable
    assert missing_upstream.computability.stack.blocker_codes == (
        ComputabilityBlockerCodeV1.INPUT_OWNER_MISSING,
        ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE,
    )
    assert invocations == []

    calibrated_binding_id = (
        "FIVAB::MATH-02::calibrated_model_probability"
    )
    missing_downstream_packets = tuple(
        packet
        for packet in external_packets
        if calibrated_binding_id not in packet.authorized_binding_ids
    )
    invocations.clear()
    missing_downstream = contextual_response(
        "MATH-01", missing_downstream_packets
    )
    assert missing_downstream.computability.context.computable
    assert not missing_downstream.computability.stack.computable
    assert missing_downstream.computability.stack.blocker_codes == (
        ComputabilityBlockerCodeV1.INPUT_OWNER_MISSING,
    )
    assert invocations == []

    calibrated_packet = next(
        packet
        for packet in external_packets
        if calibrated_binding_id in packet.authorized_binding_ids
    )
    downstream_packet_cases = (
        (
            replace(
                calibrated_packet,
                scope=replace(
                    stack_context.scope,
                    market_scope_id="MARKET::WRONG",
                ),
            ),
            ComputabilityBlockerCodeV1.INPUT_SCOPE_MISMATCH,
        ),
        (
            replace(
                calibrated_packet,
                ttl=timedelta(microseconds=1),
            ),
            ComputabilityBlockerCodeV1.FRESHNESS_VIOLATION,
        ),
    )
    for replacement_packet, expected_blocker in downstream_packet_cases:
        variant_packets = tuple(
            replacement_packet
            if packet.packet_id == calibrated_packet.packet_id
            else packet
            for packet in external_packets
        )
        invocations.clear()
        downstream_rejected = contextual_response(
            "MATH-01", variant_packets
        )
        assert downstream_rejected.computability.context.computable
        assert not downstream_rejected.computability.stack.computable
        assert expected_blocker in (
            downstream_rejected.computability.stack.blocker_codes
        )
        assert invocations == []

    component_context = _context()
    component = service.compute_component(
        ComputeComponentRequestV1(
            **_common("compute_component", context=component_context),
            component_id="MATH-01",
            input_values=_component_record(),
            expected_output_schema_ref="MATH-01::OUTPUT",
        )
    )
    assert invocations == ["MATH-01"]

    invocations.clear()
    stack = service.compute_stack(
        ComputeStackRequestV1(
            **_common("compute_stack", context=stack_context),
            stack_id=STACK_ID,
            component_ids=("MATH-01", "MATH-02"),
            input_values=_stack_record(),
        )
    )
    assert invocations == ["MATH-01", "MATH-02"]

    assert component.status is OperationStatusV1.SUCCEEDED
    assert component.component_result.formula_output is not None
    assert (
        component.component_result.formula_output.value == Decimal("0.47")
    )
    assert (
        component.component_result.formula_output.output_schema_version
        == "ST12B_OUTPUT_V3_4"
    )
    assert (
        component.component_result.formula_output.execution_context
        is component_context
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
    assert all(
        output.execution_context is stack_context
        for output in stack.stack_result.component_outputs
    )
    assert tuple(
        (pin.math_spec_id, pin.implementation_id)
        for pin in stack_context.implementation_versions
    ) == (
        ("MATH-01", "MATH-01::1.1R1"),
        ("MATH-02", "MATH-02::1.1R1"),
    )

    wrong_pin = (
        ImplementationVersionPinV1(
            math_spec_id="MATH-01",
            implementation_id="MATH-01::WRONG",
        ),
    )
    component_mismatches = (
        _context(implementation_versions=wrong_pin),
        _context(component_ids=("MATH-01", "MATH-02")),
        _context(binding_profile_version="3.5"),
        _context(parameter_policy_version="3.5"),
        _context(
            component_ids=("MATH-01", "MATH-02"),
            dependency_graph_id=STACK_ID,
        ),
    )
    for mismatched_context in component_mismatches:
        invocations.clear()
        rejected = service.compute_component(
            ComputeComponentRequestV1(
                **_common(
                    "compute_component",
                    context=mismatched_context,
                ),
                component_id="MATH-01",
                input_values=_component_record(),
                expected_output_schema_ref="MATH-01::OUTPUT",
            )
        )
        assert rejected.status is not OperationStatusV1.SUCCEEDED
        assert rejected.component_result.formula_output is None
        assert invocations == []

    stack_mismatches = (
        (
            _context(
                component_ids=("MATH-01",),
                dependency_graph_id=STACK_ID,
            ),
            STACK_ID,
            ("MATH-01", "MATH-02"),
        ),
        (
            _context(
                component_ids=("MATH-01", "MATH-02"),
                dependency_graph_id="STACK::UNKNOWN",
            ),
            "STACK::UNKNOWN",
            ("MATH-01", "MATH-02"),
        ),
        (
            _context(
                component_ids=("MATH-01", "MATH-02"),
                dependency_graph_id=STACK_ID,
                dependency_graph_version="9.9",
            ),
            STACK_ID,
            ("MATH-01", "MATH-02"),
        ),
        (
            _context(
                component_ids=("MATH-02", "MATH-01"),
                dependency_graph_id=STACK_ID,
            ),
            STACK_ID,
            ("MATH-02", "MATH-01"),
        ),
        (
            _context(
                component_ids=("MATH-01", "MATH-02", "MATH-03"),
                dependency_graph_id=STACK_ID,
            ),
            STACK_ID,
            ("MATH-01", "MATH-02", "MATH-03"),
        ),
        (
            stack_context,
            "STACK::UNKNOWN",
            ("MATH-01", "MATH-02"),
        ),
    )
    for mismatched_context, stack_id, component_ids in stack_mismatches:
        invocations.clear()
        rejected = service.compute_stack(
            ComputeStackRequestV1(
                **_common(
                    "compute_stack",
                    context=mismatched_context,
                ),
                stack_id=stack_id,
                component_ids=component_ids,
                input_values=_stack_record(),
            )
        )
        assert rejected.status is not OperationStatusV1.SUCCEEDED
        assert rejected.stack_result.component_outputs == ()
        assert invocations == []

    invocations.clear()
    with pytest.raises(ContractValidationError) as missing_graph:
        ResolveContextualComputabilityRequestV1(
            **_common("resolve_contextual_computability"),
            component_id="MATH-01",
            required_computability_classes=(
                ComputabilityClassV1.STACK_COMPUTABLE,
            ),
        )
    assert missing_graph.value.reason_code is ReasonCode.NO_APPLICABLE_STACK
    assert invocations == []

    exact_stack = service.resolve_applicable_stack(
        ResolveApplicableStackRequestV1(
            **_common(
                "resolve_applicable_stack",
                context=stack_context,
            ),
            trade_plan_candidate_id="TRADE_PLAN::EXACT",
            required_launch_roles=("MATH-01", "MATH-02"),
        )
    )
    unknown_stack = service.resolve_applicable_stack(
        ResolveApplicableStackRequestV1(
            **_common(
                "resolve_applicable_stack",
                context=_context(
                    component_ids=("MATH-01", "MATH-02"),
                    dependency_graph_id="STACK::UNKNOWN",
                ),
            ),
            trade_plan_candidate_id="TRADE_PLAN::UNKNOWN",
            required_launch_roles=("MATH-01", "MATH-02"),
        )
    )
    assert exact_stack.status is OperationStatusV1.SUCCEEDED
    assert exact_stack.stack_resolution.stack_id == STACK_ID
    assert unknown_stack.status is not OperationStatusV1.SUCCEEDED
    assert (
        OperationBlockerCodeV1.NO_APPLICABLE_STACK
        in unknown_stack.blocker_codes
    )
    assert invocations == []


def test_execution_context_propagates_through_stack(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service()
    context = _context(
        component_ids=("MATH-01", "MATH-02"),
        dependency_graph_id=STACK_ID,
    )
    captured = []
    original_execute = ApplicableStackResolverV1.execute

    def capture_execution(**kwargs: object) -> object:
        execution = original_execute(**kwargs)  # type: ignore[arg-type]
        captured.append(execution)
        return execution

    monkeypatch.setattr(
        ApplicableStackResolverV1,
        "execute",
        staticmethod(capture_execution),
    )
    request = ComputeStackRequestV1(
        **_common("compute_stack", context=context),
        stack_id=STACK_ID,
        component_ids=("MATH-01", "MATH-02"),
        input_values=_stack_record(),
    )
    response = service.compute_stack(request)

    assert response.status is OperationStatusV1.SUCCEEDED
    assert len(captured) == 1
    execution = captured[0]
    assert request.context is context
    assert execution.execution_context is context
    assert all(
        resolution.execution_context is context
        for resolution in execution.component_inputs
    )
    assert execution.dependency_packet.scope is context.scope
    assert execution.dependency_packet.context_id == context.context_id
    assert execution.dependency_packet.clocks.as_of_time == context.as_of
    assert (
        execution.dependency_packet.source_epoch_id
        == context.source_epoch_id
    )
    assert execution.dependency_packet.input_version == context.input_version
    assert (
        execution.dependency_packet.scope.input_snapshot_id
        == context.scope.input_snapshot_id
    )
    assert execution.conversion_receipt.execution_context is context
    assert execution.propagation_receipt.execution_context is context
    assert all(
        output.execution_context is context
        for output in response.stack_result.component_outputs
    )
    assert response.context is context
    assert execution.no_authority_flag is True
    assert execution.conversion_receipt.no_authority_flag is True
    assert execution.propagation_receipt.no_authority_flag is True
    assert all(
        output.no_authority_flag
        for output in response.stack_result.component_outputs
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
