import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, Inexact, Rounded, ROUND_CEILING, ROUND_FLOOR, localcontext
from fractions import Fraction
from pathlib import Path

import pytest

from src.qtt.pretrade import pr169_pretrade1_resolvers as pretrade_module
from src.qtt.pretrade.pr169_pretrade1_resolvers import (
    KalshiConditionalCashflowTermsV1,
    compose_kalshi_conditional_cashflows_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.economic_math import (
    KalshiFeeRoundingInputV1,
    kalshi_fee_rounding_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    POLICY_VERSION,
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
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
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    CURRENT_NAMED_OUTPUT_CONTRACTS,
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


def test_service_exposes_exact_fifteen_operations_and_preserves_tranche_b_projection() -> None:
    service = _service()
    exact_operation_names = (
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
        "compile_replay_paper_cohort",
        "register_replay_paper_result",
        "build_evidence_bundle",
    )
    exact_operation_ids = (
        "ST10-OP::01",
        "ST10-OP::02",
        "ST10-OP::03",
        "ST10-OP::04",
        "ST10-OP::05",
        "ST10-OP::06",
        "ST10-OP::07",
        "ST10-OP::08",
        "ST10-OP::09",
        "ST10-OP::10",
        "ST10-OP::11",
        "ST10-OP::12",
        "ST10-OP::13",
        "ST10-OP::14",
        "ST10-OP::15",
    )

    assert ST12B_CENTRAL_SERVICE_OPERATION_IDS == exact_operation_ids[:12]
    assert tuple(ST12B_OPERATION_CAPABILITY_BY_ID) == exact_operation_ids
    assert all(callable(getattr(service, name)) for name in exact_operation_names)
    assert all(
        ST12B_OPERATION_CAPABILITY_BY_ID[operation_id]
        is OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
        for operation_id in exact_operation_ids[12:]
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


    _assert_kalshi_conditional_service(monkeypatch, invocations)


def _assert_kalshi_conditional_service(monkeypatch, invocations):
    """Synthetic arithmetic/owner fixtures only; no native acceptance or effects."""
    profile = "KALSHI_US_DCM_DIRECT"
    row = KalshiFeeRoundingInputV1(Decimal("-.055"), Decimal(".011"))
    rows = (row,) * 3
    common = dict(profile_id=profile, currency="USD", balance_increment=Decimal(".01"),
                  prior_rounding_overpayment=Decimal(0))
    calls = []

    def counted_rounding(**kwargs):
        calls.append((kwargs["revenue"], kwargs["model_fee"], kwargs["prior_rounding_overpayment"]))
        return kalshi_fee_rounding_v1(**kwargs)

    monkeypatch.setattr(pretrade_module, "kalshi_fee_rounding_v1", counted_rounding)
    whole = compose_kalshi_conditional_cashflows_v1(**common, fills=rows)
    assert calls == [(Decimal("-.055"), Decimal(".011"), Decimal(carry)) for carry in ("0", ".004", ".008")]
    assert tuple(getattr(whole, field.name) for field in fields(whole)) == tuple(map(Decimal, ("-.165", ".045", ".01", ".002")))
    assert rows == (row, row, row)
    assert not hasattr(whole, "__dict__")
    with pytest.raises(FrozenInstanceError):
        whole.expected_rebate_total = Decimal(0)
    for split in (1, 2):
        prefix = compose_kalshi_conditional_cashflows_v1(**common, fills=rows[:split])
        tail = compose_kalshi_conditional_cashflows_v1(
            **{**common, "prior_rounding_overpayment": prefix.rounding_overpayment_after}, fills=rows[split:],
        )
        for name in ("entry_trade_cashflow_total", "platform_fee_total", "expected_rebate_total"):
            assert Fraction(getattr(prefix, name)) + Fraction(getattr(tail, name)) == Fraction(getattr(whole, name))
        assert tail.rounding_overpayment_after == whole.rounding_overpayment_after
    reset = compose_kalshi_conditional_cashflows_v1(**common, fills=rows[-1:])
    assert reset.expected_rebate_total == 0
    assert tail.expected_rebate_total == Decimal(".01")
    mixed = (KalshiFeeRoundingInputV1(Decimal("-.004"), Decimal(0)),
             KalshiFeeRoundingInputV1(Decimal(0), Decimal(".01")))
    calls.clear()
    released = compose_kalshi_conditional_cashflows_v1(
        **{**common, "prior_rounding_overpayment": Decimal(".006")}, fills=mixed,
    )
    assert calls == [(Decimal("-.004"), Decimal(0), Decimal(".006")), (Decimal(0), Decimal(".01"), Decimal(".012"))]
    assert tuple(getattr(released, field.name) for field in fields(released)) == tuple(map(Decimal, ("-.004", ".016", ".01", ".002")))
    calls.clear()
    maximum = compose_kalshi_conditional_cashflows_v1(
        **common, fills=(KalshiFeeRoundingInputV1(Decimal(0), Decimal(0)),) * 4096,
    )
    assert len(calls) == 4096
    assert all(getattr(maximum, field.name) == 0 for field in fields(maximum))

    class StringSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    class RowSubclass(KalshiFeeRoundingInputV1):
        pass

    for changes in (
        *(({"profile_id": value}) for value in ("POLYMARKET_US_RETAIL_DIRECT", "GEMINI_TITAN_DIRECT", "FORECASTEX_IBKR", "KALSHI", profile.lower(), StringSubclass(profile), None)),
        *(({"currency": value}) for value in ("EUR", "usd", StringSubclass("USD"), None)),
        *(({"fills": value}) for value in ((), list(rows), iter(rows), TupleSubclass(rows), (object(),), (RowSubclass(row.revenue, row.model_fee),), rows * 1366)),
    ):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            compose_kalshi_conditional_cashflows_v1(**{**common, "fills": rows, **changes})
        assert rejected.value.reason_code is ReasonCode.INVALID_CONTRACT
    for omitted in (*common, "fills"):
        with pytest.raises(TypeError):
            compose_kalshi_conditional_cashflows_v1(**{key: value for key, value in {**common, "fills": rows}.items() if key != omitted})
    for changes in ({"balance_increment": Decimal(".001")}, {"prior_rounding_overpayment": Decimal("-0")}, {"prior_rounding_overpayment": Decimal(".0000001")}):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            compose_kalshi_conditional_cashflows_v1(**{**common, **changes}, fills=rows)
        assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for field in fields(whole):
        for bad, reason in (("0", ReasonCode.INVALID_NUMERIC_INPUT), (Decimal("sNaN"), ReasonCode.NONFINITE_NUMERIC_INPUT), (Decimal("-0"), ReasonCode.OUT_OF_DOMAIN), (Decimal(".0000001"), ReasonCode.OUT_OF_DOMAIN), (Decimal("1e101"), ReasonCode.OUT_OF_DOMAIN)):
            with pytest.raises(ComputationControlPlaneError) as rejected:
                replace(whole, **{field.name: bad})
            assert rejected.value.reason_code is reason
        if field.name != "entry_trade_cashflow_total":
            with pytest.raises(ComputationControlPlaneError) as rejected:
                replace(whole, **{field.name: Decimal("-.01")})
            assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    with pytest.raises(ComputationControlPlaneError):
        replace(whole, expected_rebate_total=Decimal(".046"))
    precise34 = Decimal("1234567890123456789012345678901234")
    precise35 = Decimal("12345678901234567890123456789012345")
    admitted34 = compose_kalshi_conditional_cashflows_v1(
        **common, fills=(KalshiFeeRoundingInputV1(precise34, Decimal(0)),),
    )
    assert admitted34.entry_trade_cashflow_total == precise34
    for name in ("entry_trade_cashflow_total", "platform_fee_total", "expected_rebate_total"):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            replace(whole, **{name: precise35})
        assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for fills in ((KalshiFeeRoundingInputV1(precise35, Decimal(0)),),
                  (KalshiFeeRoundingInputV1(Decimal("9e100"), Decimal(0)),) * 2):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            compose_kalshi_conditional_cashflows_v1(**common, fills=fills)
        assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for precision in (1, 7, 28):
        for rounding in (ROUND_CEILING, ROUND_FLOOR):
            with localcontext() as ambient:
                ambient.prec, ambient.rounding = precision, rounding
                ambient.Emin, ambient.Emax = -2, 2
                ambient.traps[Inexact] = ambient.traps[Rounded] = True
                ambient.flags[Rounded] = True
                before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                          ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert compose_kalshi_conditional_cashflows_v1(**common, fills=rows) == whole
                after = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                         ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert before == after

    # These six clocks and all owner packets are explicitly synthetic fixtures.
    moment = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
    context = ComputationExecutionContextV1(
        context_id="SYNTHETIC::KALSHI::MATH06", as_of=moment,
        observed_at=moment - timedelta(seconds=1), source_epoch_id="SYNTHETIC::EPOCH",
        input_version="SYNTHETIC_V1", maximum_age=timedelta(days=1),
        scope=ComputationScopeV1(
            market_scope_id="SYNTHETIC::MARKET", venue_scope_id=profile,
            event_scope_id="SYNTHETIC::EVENT", instrument_or_contract_scope_id="SYNTHETIC::CONTRACT",
            mode_context_id="MODE_CONTEXT::CONTRACT_ONLY", input_snapshot_id="SYNTHETIC::SNAPSHOT",
        ),
        binding_profile_version=ST12B_FROZEN_PACKAGE_VERSION,
        parameter_policy_version=ST12B_FROZEN_PACKAGE_VERSION,
        implementation_versions=_pins(("MATH-06",)),
    )
    clocks = PointInTimeClocksV1(
        observed_time=moment - timedelta(seconds=1), effective_time=moment - timedelta(seconds=1),
        available_time=moment - timedelta(seconds=1), received_time=moment - timedelta(seconds=1),
        processed_time=moment - timedelta(seconds=1), as_of_time=moment,
    )
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-06"]
    schema = CURRENT_NAMED_OUTPUT_CONTRACTS["MATH-06"]
    roster_before = (tuple(IMPLEMENTATION_REGISTRY), tuple(ST12B_OPERATION_CAPABILITY_BY_ID))
    assert tuple(pin.implementation_id for pin in context.implementation_versions) == ("MATH-06::2.0.0",)

    def fixture_values(terms):
        return {
            "p_win": Decimal(".55"), "p_void": Decimal(0), "fill_probability": Decimal(".8"),
            "entry_trade_cashflow_total": terms.entry_trade_cashflow_total,
            "win_terminal_cashflow_total": Decimal(100), "lose_terminal_cashflow_total": Decimal(0),
            "void_terminal_cashflow_total": Decimal(50), "no_fill_cashflow_total": Decimal(0),
            "platform_fee_total": terms.platform_fee_total, "builder_fee_total": Decimal(0),
            "other_fee_total": Decimal(0), "expected_rebate_total": terms.expected_rebate_total,
            "exit_slippage_reserve_total": Decimal(".10"), "market_impact_reserve_total": Decimal(".20"),
            "latency_adverse_selection_reserve_total": Decimal(".30"), "capital_time_cost_reserve_total": Decimal(".40"),
            "cashflow_basis": "SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE",
        }

    def fixture_packets(values):
        assert set(values) == {binding.input_name for binding in bindings}
        return tuple(OwnerValuePacketV1(
            packet_id=f"SYNTHETIC::{binding.binding_id}", owner_id=binding.accepted_upstream_owner_id,
            packet_type=binding.accepted_packet_or_snapshot_type, schema_id=binding.schema_id,
            schema_version=binding.schema_version, context_id=context.context_id, scope=context.scope,
            source_epoch_id=context.source_epoch_id, input_version=context.input_version,
            clocks=clocks, ttl=timedelta(days=1), values={binding.exact_field_path: values[binding.input_name]},
            authorized_binding_ids=(binding.binding_id,), producer_receipt_id=f"SYNTHETIC_RECEIPT::{binding.binding_id}",
            producer_receipt_type=binding.producer_receipt_type,
            source_state_and_claim_lineage=binding.source_state_and_claim_lineage,
            provider_sequence=1, revision=1,
        ) for binding in bindings)

    def fixture_request(values, selected_context=context):
        return ComputeComponentRequestV1(
            **{**_common("compute_component", context=selected_context), "requested_at": moment},
            component_id="MATH-06", expected_output_schema_ref=schema.schema_id,
            input_values=TypedValueRecordV1(tuple(TypedValueV1(
                name=binding.input_name,
                kind=TypedValueKindV1.TEXT if binding.input_name == "cashflow_basis" else TypedValueKindV1.DECIMAL,
                value=values[binding.input_name], unit=binding.unit_or_basis, basis="SYNTHETIC_CONDITIONAL_FIXTURE",
            ) for binding in bindings)),
        )

    def evaluate(values, packets=None, selected_context=context):
        selected_packets = fixture_packets(values) if packets is None else packets
        snapshots = tuple(dict(packet.values) for packet in selected_packets)
        registry = CanonicalOwnerPacketRegistryV1(selected_packets)
        service = QKUComputationControlPlaneV1(registry, agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION)
        invocations.clear()
        response = service.compute_component(fixture_request(values, selected_context))
        assert registry.packets == selected_packets
        assert snapshots == tuple(dict(packet.values) for packet in selected_packets)
        assert response.component_result.no_authority_flag is True
        return response

    for principal, fee, expected in (("-50", "1.75", "1.8"), ("-50", "3.50", ".4"), ("-60", "1.68", "-6.144"), ("-60", "1.75", "-6.2")):
        terms = compose_kalshi_conditional_cashflows_v1(
            **common, fills=(KalshiFeeRoundingInputV1(Decimal(principal), Decimal(fee)),),
        )
        assert terms.entry_trade_cashflow_total == Decimal(principal)
        assert terms.platform_fee_total == Decimal(fee) and terms.expected_rebate_total == 0
        assert Fraction(Decimal(expected)) == Fraction(4, 5) * (Fraction(principal) + 55 - Fraction(fee) - 1)
        values = fixture_values(terms)
        response = evaluate(values)
        assert response.status is OperationStatusV1.SUCCEEDED
        assert invocations == ["MATH-06"]
        output = response.component_result.formula_output
        assert output.execution_context is context and output.no_authority_flag is True
        assert output.implementation_id == "MATH-06::2.0.0"
        assert output.output_schema_ref == schema.schema_id
        assert output.output_schema_version == schema.schema_version
        assert set(output.value) == {"expected_net_cash", "expected_net_cash_if_filled", "expected_terminal_cashflow", "p_lose"}
        assert output.value["expected_net_cash"] == Decimal(expected)
        assert Fraction(output.value["expected_net_cash_if_filled"]) == Fraction(Decimal(expected)) / Fraction(4, 5)
        assert output.value["expected_terminal_cashflow"] == Decimal(55)
        assert output.value["p_lose"] == Decimal(".45")
        assert values == fixture_values(terms)
    no_fill = evaluate({**values, "fill_probability": Decimal(0)})
    assert no_fill.status is OperationStatusV1.SUCCEEDED
    assert no_fill.component_result.formula_output.value["expected_net_cash"] == 0
    credited_values = fixture_values(whole)
    credited = evaluate(credited_values)
    uncredited = evaluate({**credited_values, "expected_rebate_total": Decimal(0)})
    assert credited.status is uncredited.status is OperationStatusV1.SUCCEEDED
    credited_value = credited.component_result.formula_output.value["expected_net_cash"]
    uncredited_value = uncredited.component_result.formula_output.value["expected_net_cash"]
    assert credited_value == Decimal("43.04") and uncredited_value == Decimal("43.032")
    assert Fraction(credited_value) - Fraction(uncredited_value) == Fraction(1, 125)
    assert "rounding_overpayment_after" not in credited_values
    packets = fixture_packets(credited_values)
    target = next(packet for packet in packets if packet.authorized_binding_ids == ("FIVAB::MATH-06::platform_fee_total",))
    for changed, reason in (
        (None, ReasonCode.INPUT_OWNER_MISSING),
        (replace(target, ttl=timedelta(microseconds=1)), ReasonCode.FRESHNESS_VIOLATION),
        (replace(target, source_conflict=True), ReasonCode.SOURCE_CONFLICT),
        # Context IDs index separate registries; a foreign context has no candidate.
        (replace(target, context_id="SYNTHETIC::WRONG_CONTEXT"), ReasonCode.INPUT_OWNER_MISSING),
        (replace(target, scope=replace(context.scope, venue_scope_id="SYNTHETIC::OTHER_VENUE")), ReasonCode.INPUT_SCOPE_MISMATCH),
    ):
        variant = tuple(changed if packet is target else packet for packet in packets if packet is not target or changed is not None)
        rejected = evaluate(credited_values, variant)
        assert rejected.status is not OperationStatusV1.SUCCEEDED
        assert rejected.component_result.formula_output is None
        assert reason.value in rejected.receipt_refs
        assert invocations == []
    wrong_assertion = evaluate({**credited_values, "platform_fee_total": Decimal(".046")}, packets)
    assert wrong_assertion.status is not OperationStatusV1.SUCCEEDED
    assert ReasonCode.INPUT_VALUE_CONFLICT.value in wrong_assertion.receipt_refs
    assert wrong_assertion.component_result.formula_output is None and invocations == []
    wrong_context = evaluate(credited_values, packets, replace(context, scope=replace(context.scope, venue_scope_id="SYNTHETIC::OTHER_VENUE")))
    assert wrong_context.status is not OperationStatusV1.SUCCEEDED
    assert ReasonCode.INPUT_SCOPE_MISMATCH.value in wrong_context.receipt_refs
    assert wrong_context.component_result.formula_output is None and invocations == []
    assert roster_before == (tuple(IMPLEMENTATION_REGISTRY), tuple(ST12B_OPERATION_CAPABILITY_BY_ID))


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
