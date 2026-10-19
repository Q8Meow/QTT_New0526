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
    compose_kalshi_quadratic_taker_buy_yes_cashflows_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.economic_math import (
    KalshiFeeRoundingInputV1,
    KalshiQuadraticTakerBuyYesFillV1,
    kalshi_fee_rounding_v1,
    kalshi_quadratic_taker_buy_yes_input_v1,
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

    # New fixed-family path uses the same fixture owners and actual MATH-06.
    taker_common = {**common, "fee_multiplier": Decimal("1.00")}
    portion = KalshiQuadraticTakerBuyYesFillV1(Decimal(25), Decimal(".5"))
    portions = (portion,) * 4
    producer_calls, composed_calls, composed_results = [], [], []

    def counted_producer(**kwargs):
        compiled = kalshi_quadratic_taker_buy_yes_input_v1(**kwargs)
        producer_calls.append((kwargs, compiled))
        return compiled

    def counted_composer(**kwargs):
        composed_calls.append(kwargs)
        result = compose_kalshi_conditional_cashflows_v1(**kwargs)
        composed_results.append(result)
        return result

    with monkeypatch.context() as delegated:
        delegated.setattr(pretrade_module, "kalshi_quadratic_taker_buy_yes_input_v1", counted_producer)
        delegated.setattr(pretrade_module, "compose_kalshi_conditional_cashflows_v1", counted_composer)
        # A different price plus repeated rows proves order and multiplicity.
        ordered = (KalshiQuadraticTakerBuyYesFillV1(Decimal(50), Decimal(".4")), *portions)
        delegated_result = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**taker_common, fills=ordered)
        assert len(producer_calls) == len(ordered) and len(composed_calls) == 1
        assert all(call["fill"] is row and call["fee_multiplier"] is taker_common["fee_multiplier"]
                   for (call, _), row in zip(producer_calls, ordered))
        compiled_rows = composed_calls[0]["fills"]
        assert type(compiled_rows) is tuple and len(compiled_rows) == len(ordered)
        assert all(compiled is observed for compiled, (_, observed) in zip(compiled_rows, producer_calls))
        assert tuple((r.revenue, r.model_fee) for r in compiled_rows) == (
            (Decimal(-20), Decimal(".84")), *((Decimal("-12.5"), Decimal(".4375")),) * 4,
        )
        for name in common:
            assert composed_calls[0][name] is taker_common[name]
        assert delegated_result is composed_results[0]

        class TakerSubclass(KalshiQuadraticTakerBuyYesFillV1):
            pass

        for changes in (
            *(({"profile_id": value}) for value in ("KALSHI", "POLYMARKET_US_RETAIL_DIRECT", "GEMINI_TITAN_DIRECT", "FORECASTEX_IBKR", profile.lower(), StringSubclass(profile), None)),
            *(({"currency": value}) for value in ("EUR", "usd", StringSubclass("USD"), None)),
            *(({"fills": value}) for value in ((), list(portions), iter(portions), TupleSubclass(portions), (object(),), (portion, row), (TakerSubclass(portion.contracts, portion.yes_price),), (portion,) * 4097)),
        ):
            with pytest.raises(ContractValidationError) as rejected:
                compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**{**taker_common, "fills": portions, **changes})
            assert rejected.value.reason_code is ReasonCode.INVALID_CONTRACT
            assert len(producer_calls) == len(ordered) and len(composed_calls) == 1

    for omitted in (*taker_common, "fills"):
        with pytest.raises(TypeError):
            compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**{
                key: value for key, value in {**taker_common, "fills": portions}.items() if key != omitted
            })
    with pytest.raises(TypeError):
        compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**taker_common, fills=portions, unknown=True)
    with pytest.raises(TypeError):
        compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(profile, "USD", portions, Decimal(1), Decimal(".01"), Decimal(0))
    for changes, reason in (
        ({"fee_multiplier": "1"}, ReasonCode.INVALID_NUMERIC_INPUT),
        ({"fee_multiplier": Decimal("sNaN")}, ReasonCode.NONFINITE_NUMERIC_INPUT),
        ({"fee_multiplier": Decimal("-0")}, ReasonCode.OUT_OF_DOMAIN),
        ({"fee_multiplier": Decimal("-1")}, ReasonCode.OUT_OF_DOMAIN),
        ({"balance_increment": ".01"}, ReasonCode.INVALID_NUMERIC_INPUT),
        ({"balance_increment": Decimal(".001")}, ReasonCode.OUT_OF_DOMAIN),
        ({"prior_rounding_overpayment": Decimal("sNaN")}, ReasonCode.NONFINITE_NUMERIC_INPUT),
        ({"prior_rounding_overpayment": Decimal("-0")}, ReasonCode.OUT_OF_DOMAIN),
        ({"prior_rounding_overpayment": Decimal(".0000001")}, ReasonCode.OUT_OF_DOMAIN),
    ):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**{**taker_common, **changes}, fills=portions)
        assert rejected.value.reason_code is reason

    def assert_taker_service(terms, expected, payout=100):
        actual_values = {
            **fixture_values(terms), "win_terminal_cashflow_total": Decimal(payout),
            "void_terminal_cashflow_total": Decimal(payout // 2),
        }
        saved_values = dict(actual_values)
        actual = evaluate(actual_values)
        assert actual.status is OperationStatusV1.SUCCEEDED and invocations == ["MATH-06"]
        output = actual.component_result.formula_output
        assert output.execution_context is context and output.no_authority_flag is True
        assert output.implementation_id == "MATH-06::2.0.0"
        assert (output.output_schema_ref, output.output_schema_version) == (schema.schema_id, schema.schema_version)
        assert set(output.value) == {"expected_net_cash", "expected_net_cash_if_filled", "expected_terminal_cashflow", "p_lose"}
        assert output.value["expected_net_cash"] == Decimal(expected)
        assert Fraction(output.value["expected_net_cash_if_filled"]) == Fraction(expected) / Fraction(4, 5)
        assert Fraction(output.value["expected_terminal_cashflow"]) == Fraction(11, 20) * payout
        assert output.value["p_lose"] == Decimal(".45")
        assert Fraction(expected) == Fraction(4, 5) * (
            Fraction(terms.entry_trade_cashflow_total) + Fraction(11, 20) * payout
            - Fraction(terms.platform_fee_total) + Fraction(terms.expected_rebate_total) - 1
        )
        assert actual_values == saved_values and "rounding_overpayment_after" not in actual_values
        return actual_values, output.value["expected_net_cash"]

    for quantity, price, multiplier, principal, cent_fee, fine_fee, payout, cent_expected, fine_expected in (
        ("100", ".5", "1", "-50", "1.75", "1.75", 100, "1.8", "1.8"),
        ("100", ".5", "2", "-50", "3.50", "3.50", 100, ".4", ".4"),
        ("100", ".6", "1", "-60", "1.68", "1.68", 100, "-6.144", "-6.144"),
        ("50", ".5", "1", "-25", ".88", ".875", 50, ".496", ".5"),
    ):
        for grid, charge, expected in ((".01", cent_fee, cent_expected), (".0001", fine_fee, fine_expected)):
            terms = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
                **{**taker_common, "balance_increment": Decimal(grid), "fee_multiplier": Decimal(multiplier)},
                fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(quantity), Decimal(price)),),
            )
            assert type(terms) is KalshiConditionalCashflowTermsV1
            assert terms.entry_trade_cashflow_total == Decimal(principal)
            assert terms.platform_fee_total == Decimal(charge) and terms.expected_rebate_total == 0
            assert terms.rounding_overpayment_after == (Decimal(".005") if quantity == "50" and grid == ".01" else Decimal(0))
            assert_taker_service(terms, expected, payout)

    taker_whole = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**taker_common, fills=portions)
    assert tuple(getattr(taker_whole, field.name) for field in fields(taker_whole)) == tuple(map(Decimal, ("-50", "1.76", ".01", "0")))
    taker_values, taker_cash = assert_taker_service(taker_whole, "1.8")
    taker_no_credit = evaluate({**taker_values, "expected_rebate_total": Decimal(0)})
    assert taker_no_credit.status is OperationStatusV1.SUCCEEDED
    no_credit_cash = taker_no_credit.component_result.formula_output.value["expected_net_cash"]
    assert no_credit_cash == Decimal("1.792")
    assert Fraction(taker_cash) - Fraction(no_credit_cash) == Fraction(".008")
    taker_no_fill = evaluate({**taker_values, "fill_probability": Decimal(0)})
    assert taker_no_fill.status is OperationStatusV1.SUCCEEDED
    assert taker_no_fill.component_result.formula_output.value["expected_net_cash"] == 0
    taker_packets = fixture_packets(taker_values)
    taker_wrong_assertion = evaluate({**taker_values, "platform_fee_total": Decimal("1.75")}, taker_packets)
    assert taker_wrong_assertion.status is not OperationStatusV1.SUCCEEDED
    assert taker_wrong_assertion.component_result.formula_output is None and invocations == []
    assert ReasonCode.INPUT_VALUE_CONFLICT.value in taker_wrong_assertion.receipt_refs

    for grid in map(Decimal, (".01", ".0001")):
        scenario = {**taker_common, "balance_increment": grid}
        continuous = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**scenario, fills=portions)
        for split in (1, 2, 3):
            prefix = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**scenario, fills=portions[:split])
            suffix = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
                **{**scenario, "prior_rounding_overpayment": prefix.rounding_overpayment_after}, fills=portions[split:],
            )
            for name in ("entry_trade_cashflow_total", "platform_fee_total", "expected_rebate_total"):
                assert Fraction(getattr(prefix, name)) + Fraction(getattr(suffix, name)) == Fraction(getattr(continuous, name))
            assert suffix.rounding_overpayment_after == continuous.rounding_overpayment_after
        mixed_terms = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
            **scenario, fills=tuple(KalshiQuadraticTakerBuyYesFillV1(Decimal(50), Decimal(price)) for price in (".4", ".6")),
        )
        assert tuple(getattr(mixed_terms, field.name) for field in fields(mixed_terms)) == tuple(map(Decimal, ("-50", "1.68", "0", "0")))
        assert_taker_service(mixed_terms, "1.856")
        maximum = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
            **{**scenario, "fee_multiplier": Decimal(0)},
            fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(1), Decimal(".5")),) * 4096,
        )
        assert tuple(getattr(maximum, field.name) for field in fields(maximum)) == tuple(map(Decimal, ("-2048", "0", "0", "0")))
    reset_half = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**taker_common, fills=portions[:2])
    assert reset_half.expected_rebate_total == 0 and taker_whole.expected_rebate_total == Decimal(".01")
    zero_multiplier = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(
        **{**taker_common, "fee_multiplier": Decimal(0)},
        fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(".01"), Decimal(".5")),),
    )
    assert tuple(getattr(zero_multiplier, field.name) for field in fields(zero_multiplier)) == tuple(map(Decimal, ("-.005", ".005", "0", ".005")))
    # The raw producer admits its own bounded domain; MATH-06 totals constrain composition.
    precise_fill = KalshiQuadraticTakerBuyYesFillV1(Decimal("24691357802469135780246913578024690"), Decimal(".5"))
    assert kalshi_quadratic_taker_buy_yes_input_v1(fill=precise_fill, fee_multiplier=Decimal(0)).revenue == Decimal("-12345678901234567890123456789012345")
    with pytest.raises(ComputationControlPlaneError) as rejected:
        compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**{**taker_common, "fee_multiplier": Decimal(0)}, fills=(precise_fill,))
    assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for precision in (1, 7, 28):
        for rounding in (ROUND_CEILING, ROUND_FLOOR):
            with localcontext() as ambient:
                ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax = precision, rounding, -2, 2
                ambient.traps[Inexact] = ambient.traps[Rounded] = True
                ambient.flags[Rounded] = True
                before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                          ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**taker_common, fills=portions) == taker_whole
                with pytest.raises(ComputationControlPlaneError) as rejected:
                    compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**{**taker_common, "fee_multiplier": Decimal("sNaN")}, fills=portions)
                assert rejected.value.reason_code is ReasonCode.NONFINITE_NUMERIC_INPUT
                after = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                         ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert before == after
    assert roster_before == (tuple(IMPLEMENTATION_REGISTRY), tuple(ST12B_OPERATION_CAPABILITY_BY_ID))

    # Unadmitted literal Series bytes feed the same synthetic owners and MATH-06.
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source_owner
    series_wrapper = pretrade_module.compose_kalshi_series_quadratic_taker_buy_yes_cashflows_v1
    ticker = "QTT-SYNTHETIC-SERIES"
    raw_one = b'{"series":{"ticker":"QTT-SYNTHETIC-SERIES","fee_type":"quadratic","fee_multiplier":1}}'
    source_rosters_before = (
        tuple(source_owner.CERTIFIED_SOURCE_STATES), tuple(source_owner.SOURCE_CURRENTIZATION_OVERLAYS),
        tuple(source_owner.SOURCE_STATE_BY_ID), tuple(source_owner.SOURCE_OVERLAY_BY_ID),
        tuple(source_owner.ST12H_SOURCE_BINDINGS), tuple(source_owner.ST12H_SOURCE_CURRENTIZATION_RULES),
    )
    series_common = {**common, "raw_series_response": raw_one, "expected_series_ticker": ticker}
    decoder_calls, candidate_results, taker_calls, taker_results = [], [], [], []
    real_decoder = source_owner.decode_kalshi_quadratic_series_fee_candidate_v1

    def counted_decoder(**kwargs):
        decoder_calls.append(kwargs)
        candidate = real_decoder(**kwargs)
        candidate_results.append(candidate)
        return candidate

    def counted_taker(**kwargs):
        taker_calls.append(kwargs)
        result = compose_kalshi_quadratic_taker_buy_yes_cashflows_v1(**kwargs)
        taker_results.append(result)
        return result

    with monkeypatch.context() as delegated:
        delegated.setattr(pretrade_module, "decode_kalshi_quadratic_series_fee_candidate_v1", counted_decoder)
        delegated.setattr(pretrade_module, "compose_kalshi_quadratic_taker_buy_yes_cashflows_v1", counted_taker)
        ordered = (KalshiQuadraticTakerBuyYesFillV1(Decimal(50), Decimal(".4")), *portions)
        forwarded = series_wrapper(**series_common, fills=ordered)
        assert len(decoder_calls) == len(taker_calls) == 1
        assert decoder_calls[0]["raw_response"] is raw_one
        assert decoder_calls[0]["expected_series_ticker"] is ticker
        assert taker_calls[0]["fee_multiplier"] is candidate_results[0].fee_multiplier
        assert taker_calls[0]["fills"] is ordered
        assert tuple((r.contracts, r.yes_price) for r in ordered) == (
            (Decimal(50), Decimal(".4")), *((Decimal(25), Decimal(".5")),) * 4,
        )
        for name in common:
            assert taker_calls[0][name] is series_common[name]
        assert forwarded is taker_results[0]
        for changes in (
            *(({"profile_id": value}) for value in ("KALSHI", "POLYMARKET_US_RETAIL_DIRECT", "GEMINI_TITAN_DIRECT", "FORECASTEX_IBKR", StringSubclass(profile), None)),
            *(({"currency": value}) for value in ("usd", "EUR", StringSubclass("USD"), None)),
        ):
            decoder_calls.clear(); taker_calls.clear(); invocations.clear()
            with pytest.raises(ContractValidationError) as rejected:
                series_wrapper(**{**series_common, "raw_series_response": b"malformed", **changes}, fills=portions)
            assert rejected.value.reason_code is ReasonCode.INVALID_CONTRACT
            assert decoder_calls == taker_calls == invocations == []
        for changes, reason in (
            ({"expected_series_ticker": "OTHER"}, ReasonCode.INPUT_SCOPE_MISMATCH),
            ({"raw_series_response": b"{"}, ReasonCode.INVALID_CONTRACT),
            ({"raw_series_response": b"{}"}, ReasonCode.INCOMPLETE_CONTRACT),
            ({"raw_series_response": raw_one.replace(b'"quadratic"', b'"flat"')}, ReasonCode.INVALID_CONTRACT),
        ):
            decoder_calls.clear(); taker_calls.clear(); invocations.clear()
            with pytest.raises(ContractValidationError) as rejected:
                series_wrapper(**{**series_common, **changes}, fills=portions)
            assert rejected.value.reason_code is reason
            assert len(decoder_calls) == 1 and taker_calls == invocations == []
        malformed_row = object.__new__(KalshiQuadraticTakerBuyYesFillV1)
        object.__setattr__(malformed_row, "contracts", Decimal(".001"))
        object.__setattr__(malformed_row, "yes_price", Decimal(".5"))
        for changes, reason in (
            *(({"fills": value}, ReasonCode.INVALID_CONTRACT) for value in ((), list(portions), iter(portions), TupleSubclass(portions), (object(),), (portion,) * 4097)),
            ({"fills": (malformed_row,)}, ReasonCode.OUT_OF_DOMAIN),
            ({"balance_increment": ".01"}, ReasonCode.INVALID_NUMERIC_INPUT),
            ({"balance_increment": Decimal(".001")}, ReasonCode.OUT_OF_DOMAIN),
            ({"prior_rounding_overpayment": Decimal("sNaN")}, ReasonCode.NONFINITE_NUMERIC_INPUT),
            ({"prior_rounding_overpayment": Decimal("-0")}, ReasonCode.OUT_OF_DOMAIN),
            ({"prior_rounding_overpayment": Decimal(".0000001")}, ReasonCode.OUT_OF_DOMAIN),
            ({"raw_series_response": raw_one.replace(b'"fee_multiplier":1', b'"fee_multiplier":1e100'),
              "fills": (KalshiQuadraticTakerBuyYesFillV1(Decimal("1e100"), Decimal(".5")),)}, ReasonCode.OUT_OF_DOMAIN),
        ):
            decoder_calls.clear(); taker_calls.clear(); invocations.clear()
            with pytest.raises(ComputationControlPlaneError) as rejected:
                series_wrapper(**{**series_common, "fills": portions, **changes})
            assert rejected.value.reason_code is reason
            assert len(decoder_calls) == len(taker_calls) == 1 and invocations == []
        decoder_calls.clear(); taker_calls.clear()
        for omitted in (*series_common, "fills"):
            with pytest.raises(TypeError):
                series_wrapper(**{key: value for key, value in {**series_common, "fills": portions}.items() if key != omitted})
        with pytest.raises(TypeError):
            series_wrapper(**series_common, fills=portions, fee_multiplier=Decimal(2))
        with pytest.raises(TypeError):
            series_wrapper(profile, "USD", raw_one, ticker, portions, Decimal(".01"), Decimal(0))
        assert decoder_calls == taker_calls == []

    consumed = []
    for quantity, price, token, grid, literals, expected in (
        ("100", ".5", b"1", ".01", ("-50", "1.75", "0", "0"), "1.8"),
        ("100", ".5", b"2", ".01", ("-50", "3.5", "0", "0"), ".4"),
        ("100", ".6", b"1.0", ".0001", ("-60", "1.68", "0", "0"), "-6.144"),
        ("50", ".5", b"1e0", ".01", ("-25", ".88", "0", ".005"), ".496"),
        ("50", ".5", b"1e0", ".0001", ("-25", ".875", "0", "0"), ".5"),
    ):
        supplied = raw_one.replace(b'"fee_multiplier":1', b'"fee_multiplier":' + token)
        declared_fills = (KalshiQuadraticTakerBuyYesFillV1(Decimal(quantity), Decimal(price)),)
        before_fills = tuple((fill.contracts, fill.yes_price) for fill in declared_fills)
        terms = series_wrapper(**{**series_common, "raw_series_response": supplied, "balance_increment": Decimal(grid)}, fills=declared_fills)
        assert type(terms) is KalshiConditionalCashflowTermsV1
        assert tuple(getattr(terms, field.name) for field in fields(terms)) == tuple(map(Decimal, literals))
        _, cash = assert_taker_service(terms, expected, int(quantity))
        consumed.append(cash)
        assert before_fills == tuple((fill.contracts, fill.yes_price) for fill in declared_fills)
        assert supplied == raw_one.replace(b'"fee_multiplier":1', b'"fee_multiplier":' + token)
    assert consumed[:2] == [Decimal("1.8"), Decimal(".4")]
    additive = raw_one[:-2] + b',"last_updated_ts":"not-admission","title":"synthetic","exchange_index":9,"accepted":true},"metadata":[1,2]}'
    metadata_terms = series_wrapper(**{**series_common, "raw_series_response": additive}, fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal(".5")),))
    assert_taker_service(metadata_terms, "1.8")

    def assert_fractional_series_service(terms, payout, expected):
        actual_values = {**fixture_values(terms), "win_terminal_cashflow_total": Decimal(payout),
                         "void_terminal_cashflow_total": Decimal(0)}
        saved_values = dict(actual_values)
        actual = evaluate(actual_values)
        assert actual.status is OperationStatusV1.SUCCEEDED and invocations == ["MATH-06"]
        output = actual.component_result.formula_output
        assert output.execution_context is context and output.no_authority_flag is True
        assert output.implementation_id == "MATH-06::2.0.0"
        assert (output.output_schema_ref, output.output_schema_version) == (schema.schema_id, schema.schema_version)
        assert output.value["expected_net_cash"] == Decimal(expected)
        assert Fraction(output.value["expected_terminal_cashflow"]) == Fraction(11, 20) * Fraction(payout)
        assert Fraction(expected) == Fraction(4, 5) * (
            Fraction(terms.entry_trade_cashflow_total) + Fraction(11, 20) * Fraction(payout)
            - Fraction(terms.platform_fee_total) + Fraction(terms.expected_rebate_total) - 1
        )
        assert actual_values == saved_values and "rounding_overpayment_after" not in actual_values

    fractional_raw = raw_one.replace(b'"fee_multiplier":1', b'"fee_multiplier":2.1')
    fractional_fill = KalshiQuadraticTakerBuyYesFillV1(Decimal(".1"), Decimal(".55"))
    for grid, literals in ((".01", ("-.055", ".005", "0", ".001361")),
                           (".0001", ("-.055", ".0037", "0", ".000061"))):
        producer_calls.clear()
        with monkeypatch.context() as delegated:
            delegated.setattr(pretrade_module, "kalshi_quadratic_taker_buy_yes_input_v1", counted_producer)
            terms = series_wrapper(**{**series_common, "raw_series_response": fractional_raw, "balance_increment": Decimal(grid)}, fills=(fractional_fill,))
        assert len(producer_calls) == 1 and producer_calls[0][1].model_fee == Decimal(".00363825")
        assert tuple(getattr(terms, field.name) for field in fields(terms)) == tuple(map(Decimal, literals))
        assert_fractional_series_service(terms, ".1", "-.804" if grid == ".01" else "-.80296")

    series_whole = series_wrapper(**series_common, fills=portions)
    assert tuple(getattr(series_whole, field.name) for field in fields(series_whole)) == tuple(map(Decimal, ("-50", "1.76", ".01", "0")))
    series_values, series_cash = assert_taker_service(series_whole, "1.8")
    no_refund = evaluate({**series_values, "expected_rebate_total": Decimal(0)})
    assert no_refund.status is OperationStatusV1.SUCCEEDED
    assert no_refund.component_result.formula_output.value["expected_net_cash"] == Decimal("1.792")
    assert Fraction(series_cash) - Fraction(no_refund.component_result.formula_output.value["expected_net_cash"]) == Fraction(".008")
    prefix = series_wrapper(**series_common, fills=portions[:2])
    suffix = series_wrapper(**{**series_common, "prior_rounding_overpayment": prefix.rounding_overpayment_after}, fills=portions[2:])
    for name in ("entry_trade_cashflow_total", "platform_fee_total", "expected_rebate_total"):
        assert Fraction(getattr(prefix, name)) + Fraction(getattr(suffix, name)) == Fraction(getattr(series_whole, name))
    assert suffix.rounding_overpayment_after == series_whole.rounding_overpayment_after
    mixed_series = series_wrapper(**series_common, fills=tuple(KalshiQuadraticTakerBuyYesFillV1(Decimal(50), Decimal(p)) for p in (".4", ".6")))
    assert tuple(getattr(mixed_series, field.name) for field in fields(mixed_series)) == tuple(map(Decimal, ("-50", "1.68", "0", "0")))
    assert_taker_service(mixed_series, "1.856")
    zero_raw = raw_one.replace(b'"fee_multiplier":1', b'"fee_multiplier":0')
    zero_terms = series_wrapper(**{**series_common, "raw_series_response": zero_raw}, fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(".01"), Decimal(".5")),))
    assert tuple(getattr(zero_terms, field.name) for field in fields(zero_terms)) == tuple(map(Decimal, ("-.005", ".005", "0", ".005")))
    assert_fractional_series_service(zero_terms, ".01", "-.8036")
    maximum = series_wrapper(**{**series_common, "raw_series_response": zero_raw}, fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(1), Decimal(".5")),) * 4096)
    assert tuple(getattr(maximum, field.name) for field in fields(maximum)) == tuple(map(Decimal, ("-2048", "0", "0", "0")))
    assert_taker_service(maximum, "163.04", 4096)
    no_fill = evaluate({**series_values, "fill_probability": Decimal(0)})
    assert no_fill.status is OperationStatusV1.SUCCEEDED and no_fill.component_result.formula_output.value["expected_net_cash"] == 0
    rejected = evaluate({**series_values, "platform_fee_total": Decimal("1.75")}, fixture_packets(series_values))
    assert rejected.status is not OperationStatusV1.SUCCEEDED and rejected.component_result.formula_output is None
    assert ReasonCode.INPUT_VALUE_CONFLICT.value in rejected.receipt_refs and invocations == []
    for precision in (1, 7, 28):
        for rounding in (ROUND_CEILING, ROUND_FLOOR):
            with localcontext() as ambient:
                ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax = precision, rounding, -2, 2
                ambient.traps[Inexact] = ambient.traps[Rounded] = True
                ambient.flags[Rounded] = True
                before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                          ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert series_wrapper(**series_common, fills=portions) == series_whole
                with pytest.raises(ContractValidationError):
                    series_wrapper(**{**series_common, "raw_series_response": raw_one.replace(b'"fee_multiplier":1', b'"fee_multiplier":-0')}, fills=portions)
                assert before == (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                                  ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
    assert source_rosters_before == (
        tuple(source_owner.CERTIFIED_SOURCE_STATES), tuple(source_owner.SOURCE_CURRENTIZATION_OVERLAYS),
        tuple(source_owner.SOURCE_STATE_BY_ID), tuple(source_owner.SOURCE_OVERLAY_BY_ID),
        tuple(source_owner.ST12H_SOURCE_BINDINGS), tuple(source_owner.ST12H_SOURCE_CURRENTIZATION_RULES),
    )
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
