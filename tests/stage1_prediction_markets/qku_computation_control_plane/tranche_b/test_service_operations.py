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


def _assert_lp02_issued_public_service(handle, *, off_grid=False, failure_mode="withdraw"):
    """Called by the existing PIT matrix after actual synthetic durable issuance."""
    import copy
    import time
    from types import MappingProxyType
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as resolver
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import service as service_owner
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import handoff
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    publication = handoff._require_public_publication_handle_v1(publication=handle)
    state, = publication[3].values()
    now = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=(publication[8]+999)//1000)
    context = replace(_context(component_ids=("MATH-36",)),
        context_id="SYN::SERVICE::"+("OFF_GRID" if off_grid else failure_mode),
        as_of=now, observed_at=now, source_epoch_id=publication[10], input_version=publication[11],
        maximum_age=timedelta(seconds=2) if failure_mode == "expiry" else timedelta(days=1),
        scope=ComputationScopeV1(state.market_id, state.profile_id.value, publication[4][0].event_id_or_none,
            state.instrument_id, "MODE_CONTEXT::CONTRACT_ONLY", state.state_id))
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-36"]
    registry = resolver.issue_public_owner_registry_v1(publication=handle, context=context,
        binding_ids=tuple(row.binding_id for row in bindings), source_bindings=publication[5])
    assert resolver.issue_public_owner_registry_v1(publication=handle, context=context,
        binding_ids=tuple(row.binding_id for row in bindings), source_bindings=publication[5]) is registry
    assert publication[12] is False
    resolved = resolver.FormulaInputResolverV1.resolve("MATH-36", context=context, owner_registry=registry)
    assert len(resolved.receipt_refs) == len(set(resolved.receipt_refs))
    assert resolved.receipt_refs.count(publication[7].record_id) == 1
    with pytest.raises(ComputationControlPlaneError, match="freshness budget changed"):
        registry.packet_for(context=replace(context, maximum_age=context.maximum_age/2), binding_id=bindings[0].binding_id)
    for forged in (copy.copy(registry), CanonicalOwnerPacketRegistryV1(registry.packets)):
        with pytest.raises(ComputationControlPlaneError, match="custody"):
            forged.packet_for(context=context, binding_id=bindings[0].binding_id)
    with pytest.raises(ComputationControlPlaneError):
        resolver.issue_public_owner_registry_v1(publication=object(), context=context,
            binding_ids=tuple(row.binding_id for row in bindings), source_bindings=publication[5])
    with pytest.raises(ComputationControlPlaneError, match="predates"):
        resolver.issue_public_owner_registry_v1(publication=handle,
            context=replace(context, as_of=now-timedelta(days=1), observed_at=now-timedelta(days=1)),
            binding_ids=tuple(row.binding_id for row in bindings), source_bindings=publication[5])

    class CountAdmission(_ExplicitNoEffectTestAdmission):
        count = 0

        def admit_operation(self, request):
            self.count += 1
            return super().admit_operation(request)

    admission = CountAdmission()
    service = QKUComputationControlPlaneV1(owner_registry=registry, agent_capability_resolver=admission)
    request = ComputeComponentRequestV1(**dict(_common("compute_component", context=context), requested_at=now),
        component_id="MATH-36", input_values=TypedValueRecordV1((TypedValueV1(
            "book_sequence", TypedValueKindV1.INTEGER, 7, "sequence", "provider"),)),
        expected_output_schema_ref="MATH-36::OUTPUT")
    response = service.compute_component(request)
    if off_grid:
        assert admission.count == 1 and response.status is OperationStatusV1.REJECTED
        assert response.component_result.formula_output is None
        assert response.component_result.evidence_refs == (ReasonCode.OUT_OF_DOMAIN.value,)
        return
    assert admission.count == 1 and response.status is OperationStatusV1.SUCCEEDED
    assert dict(response.component_result.formula_output.value) == {
        "best_yes_bid": Decimal("0.49"), "best_no_bid": Decimal("0.49"),
        "derived_yes_ask": Decimal("0.51"), "derived_no_ask": Decimal("0.51"), "book_sequence": 7}
    if failure_mode == "withdraw":
        _assert_lp02_operation_dispositions(registry,context,request,publication[7].record_id)
        _assert_lp02_math39_service(handle,context)
    original = service_owner.invoke_formula_v34
    permission = publication[1]._binding
    wall = time.time_ns()

    def withdraw_after_value(*args, **kwargs):
        value = original(*args, **kwargs)
        if failure_mode == "expiry":
            # Metadata was observed one second before this book; two seconds
            # of economic TTL expire exactly one second after issuance here.
            patch.setattr(time, "time_ns", lambda: wall+1_000_000_000)
        elif failure_mode == "regression":
            patch.setattr(time, "time_ns", lambda: wall+1000)
            registry.packet_for(context=context, binding_id=bindings[0].binding_id)
            patch.setattr(time, "time_ns", lambda: wall+500)
        elif failure_mode == "owner_inputs":
            permission._owner._inputs = MappingProxyType(dict(permission._owner._inputs))
        else:
            permission._failed = True
        return value

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(service_owner, "invoke_formula_v34", withdraw_after_value)
        with pytest.raises(ComputationControlPlaneError):
            service.compute_component(request)
    assert admission.count == 2
    # Known public receipts cannot shed custody by selecting another context.
    explanation = ExplainResolutionRequestV1(**dict(_common("explain_resolution", context=replace(
        context, context_id=context.context_id+"::OTHER")), requested_at=now),
        resolution_receipt_id=publication[7].record_id, explanation_scope="SUMMARY", max_evidence_items=20)
    with pytest.raises(ComputationControlPlaneError):
        service.explain_resolution(explanation)
    assert admission.count == 3


def _assert_lp02_operation_dispositions(registry,context,compute_request,publication_ref):
    """Invoke the fifteen preserved operations with an actual public registry."""
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        CompileReplayPaperCohortRequestV1,RegisterReplayPaperResultRequestV1,BuildEvidenceBundleRequestV1)
    class Admission(_ExplicitNoEffectTestAdmission):
        def __init__(self):self.names=[]
        def admit_operation(self,request):
            self.names.append(request.operation_name)
            return super().admit_operation(request)
    admission=Admission()
    service=QKUComputationControlPlaneV1(owner_registry=registry,agent_capability_resolver=admission)
    def common(name):return dict(_common(name,context=context),requested_at=context.as_of)
    requests=(
        ResolveIdentityRequestV1(**common('resolve_identity'),identity_query=_text_record('math_spec_id','MATH-36')),
        ResolveContextualComputabilityRequestV1(**common('resolve_contextual_computability'),component_id='MATH-36',
            required_computability_classes=(ComputabilityClassV1.SPECIFICATION_COMPUTABLE,
                ComputabilityClassV1.FIXTURE_COMPUTABLE,ComputabilityClassV1.CONTEXT_COMPUTABLE)),
        ResolveApplicableStackRequestV1(**common('resolve_applicable_stack'),trade_plan_candidate_id='SYN::PLAN',required_launch_roles=('MATH-36',)),
        ResolveRequiredInputsRequestV1(**common('resolve_required_inputs'),component_ids=('MATH-36',),include_optional=False),
        compute_request,
        ComputeStackRequestV1(**common('compute_stack'),stack_id=STACK_ID,component_ids=('MATH-36',),
            input_values=TypedValueRecordV1((TypedValueV1('MATH-36.book_sequence',TypedValueKindV1.INTEGER,7,'sequence','provider'),))),
        CompareWithNoTradeRequestV1(**common('compare_with_no_trade'),trade_plan_candidate_id='SYN::PLAN',
            no_trade_candidate_id='SYN::NO_TRADE',comparison_basis='EXACT_NET_FRICTION_BASIS'),
        EvaluateTradePlanRequestV1(**common('evaluate_trade_plan'),trade_plan_candidate_id='SYN::PLAN',stack_id=STACK_ID,
            accounting_tca_view_ref='SYN::ACCOUNTING',risk_cash_state_ref='SYN::RISK',no_trade_candidate_id='SYN::NO_TRADE'),
        GetSnapshotViewRequestV1(**common('get_snapshot_view'),snapshot_id=registry.packets[0].packet_id,
            view_class='OWNER_PACKET_LINEAGE',include_value_lineage=True),
        ExplainResolutionRequestV1(**common('explain_resolution'),resolution_receipt_id=publication_ref,
            explanation_scope='EXACT_TYPED_RECEIPT',max_evidence_items=10),
        SubmitCandidateProposalRequestV1(**common('submit_candidate_proposal'),candidate_kind='FORMULA_SUCCESSOR',
            proposed_specification=_text_record('candidate_state','PROVISIONAL'),source_candidate_refs=(publication_ref,),requested_owner_review=True),
        RequestMaterializationWorkOrderRequestV1(**common('request_materialization_work_order'),missing_contract_ids=('SYN::MISSING',),
            reason_codes=(OperationBlockerCodeV1.INPUT_OWNER_MISSING,),priority='OWNER_REVIEW',requested_owner='CanonicalOwnerV1'),
        CompileReplayPaperCohortRequestV1(**common('compile_replay_paper_cohort'),template_ids=('SYN::TEMPLATE',),
            requested_lanes=('REPLAY',),input_lock_id='SYN::LOCK',campaign_execution_requested=False),
        RegisterReplayPaperResultRequestV1(**common('register_replay_paper_result'),cohort_instance_id='SYN::COHORT',lane='REPLAY',
            input_lock_id='SYN::LOCK',result_packet=_text_record('result','UNAVAILABLE')),
        BuildEvidenceBundleRequestV1(**common('build_evidence_bundle'),component_id='MATH-36',input_lock_id='SYN::LOCK',
            evidence_record_refs=(publication_ref,),required_lanes=('REPLAY',)),
    )
    expected=('SUCCEEDED','SUCCEEDED','BLOCKED','SUCCEEDED','SUCCEEDED','BLOCKED','BLOCKED','BLOCKED',
        'SUCCEEDED','SUCCEEDED','SUCCEEDED','SUCCEEDED',None,None,None)
    finalized=[]
    original=service_module._finalize_public_response_v1
    def finalize(**kwargs):
        finalized.append(kwargs['response'])
        return original(**kwargs)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(service_module,'_finalize_public_response_v1',finalize)
        for index,(request,status) in enumerate(zip(requests,expected,strict=True)):
            before=len(finalized)
            if status is None:
                with pytest.raises(ComputationControlPlaneError,match='requires the injected canonical'):
                    getattr(service,request.operation_name)(request)
            else:
                response=getattr(service,request.operation_name)(request)
                assert response.status.value==status
                assert len(finalized)-before==int(index!=0)
                if index in (10,11):
                    record=response.proposal if index==10 else response.work_order
                    assert record.no_authority_flag is True
            assert admission.names==[row.operation_name for row in requests[:index+1]]
    assert len(requests)==15 and len(finalized)==11


def _assert_lp02_math39_service(handle, base_context):
    """Real public history plus separately declared synthetic order-priority facts."""
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import ST12D_MATH_IMPLEMENTATION_REGISTRY
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import handoff

    publication=handoff._require_public_publication_handle_v1(publication=handle)
    context=replace(base_context,context_id=base_context.context_id+'::QUEUE',implementation_versions=(
        ImplementationVersionPinV1('MATH-39',ST12D_MATH_IMPLEMENTATION_REGISTRY['MATH-39'].contract.implementation_id),))
    bindings=CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID['MATH-39']
    by_name={row.input_name:row for row in bindings}
    history=handoff._public_committed_translations_v1(publication=handle)
    assert len(history)==7
    event_time=datetime(2026,8,30,12,0,tzinfo=UTC)
    ack=owner.Math39OrderAcknowledgementV1('SYN::ORDER',context.scope.venue_scope_id,
        context.scope.instrument_or_contract_scope_id,'YES_BID',Decimal('0.49'),event_time,event_time,
        'PRICE_TIME_FIFO','SYN::SEPARATE_PRIORITY_EVIDENCE','units','ACKNOWLEDGED_INSERTION_POINT','SYN::ACK_RECEIPT')
    events=tuple(owner.Math39SequencedBookEventV1(row.observation_ref,index+1,
        owner.Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER if index==0 else owner.Math39BookEventKindV1.PRIOR_ADDITION,
        ack.venue_id,ack.instrument_id,ack.side,ack.price,Decimal('123456.78' if index==0 else '0.01'),
        event_time,context.as_of,ack.order_id,ack.venue_evidence_ref,ack.unit,ack.basis,'SYN::PRIORITY_RECEIPT')
        for index,row in enumerate(history))
    clocks=PointInTimeClocksV1(event_time,event_time,context.as_of,context.as_of,context.as_of,context.as_of)
    def packet(name,value,receipt):
        row=by_name[name]
        return OwnerValuePacketV1('SYN::QUEUE_PACKET::'+name,row.accepted_upstream_owner_id,row.accepted_packet_or_snapshot_type,
            row.schema_id,row.schema_version,context.context_id,context.scope,context.source_epoch_id,context.input_version,
            clocks,context.maximum_age,{row.exact_field_path:value},(row.binding_id,),receipt,row.producer_receipt_type,
            row.source_state_and_claim_lineage,provider_sequence=7 if name=='sequenced_book_events' else None,
            revision='SYN::ACK_REVISION::1' if name=='order_ack' else None)
    book_packet=packet('sequenced_book_events',events,'SYN::PRIORITY_RECEIPT')
    ack_packet=packet('order_ack',ack,'SYN::ACK_RECEIPT')
    dependencies=CanonicalOwnerPacketRegistryV1((book_packet,ack_packet))
    for absent in (None,CanonicalOwnerPacketRegistryV1((book_packet,)),CanonicalOwnerPacketRegistryV1((ack_packet,))):
        with pytest.raises(ComputationControlPlaneError):
            owner._issue_public_order_history_registry_v1(publication=handle,context=context,source_bindings=publication[5],dependencies=absent)
    for changed in (replace(events[1],quantity=Decimal('0.02')),replace(events[1],sequence=3),
                    replace(events[1],event_kind=owner.Math39BookEventKindV1.PRIOR_CANCELLATION),
                    replace(events[1],event_id='SYN::UNRETAINED'),replace(events[1],event_time=event_time+timedelta(microseconds=1))):
        altered=CanonicalOwnerPacketRegistryV1((replace(book_packet,values={by_name['sequenced_book_events'].exact_field_path:
            (events[0],changed,*events[2:])}),ack_packet))
        with pytest.raises(ComputationControlPlaneError):
            owner._issue_public_order_history_registry_v1(publication=handle,context=context,source_bindings=publication[5],dependencies=altered)
    registry=owner._issue_public_order_history_registry_v1(publication=handle,context=context,source_bindings=publication[5],dependencies=dependencies)
    raw=registry.packet_for(context=context,binding_id=by_name['sequenced_book_events'].binding_id)
    assert raw.producer_receipt_id==publication[7].record_id
    assert tuple(row.sequence for row in raw.values['book.sequenced_book_events'])==(1,2,3,4,5,6,7)
    service=QKUComputationControlPlaneV1(owner_registry=registry,agent_capability_resolver=_ExplicitNoEffectTestAdmission())
    request=ComputeComponentRequestV1(**dict(_common('compute_component',context=context),requested_at=context.as_of),
        component_id='MATH-39',input_values=TypedValueRecordV1((TypedValueV1('displayed_quantity_before_order',
            TypedValueKindV1.DECIMAL,Decimal('123456.78'),'units','ACKNOWLEDGED_INSERTION_POINT'),)),
        expected_output_schema_ref='MATH-39::OUTPUT')
    response=service.compute_component(request)
    assert response.status is OperationStatusV1.SUCCEEDED
    assert response.component_result.formula_output.value==Decimal('123456.84')
    with pytest.raises(ComputationControlPlaneError):
        CanonicalOwnerPacketRegistryV1(registry.packets).packet_for(context=context,binding_id=by_name['sequenced_book_events'].binding_id)


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
    _assert_lp02_frozen_public_bindings()
    _assert_lp02_public_owner_topology_guard()
    _assert_lp02_selected_package_materialization()
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


def _assert_lp02_selected_package_materialization():
    """Invoke the canonical launch/package owners and preserve every held role."""
    from copy import deepcopy
    from src.qtt.plugins.registry import _validate_launch_projection
    from src.qtt.plugins.contracts import PluginPackageContractError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import stage1_launch_graph as launch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.plugin_adapter import SelectedComponentPackageAdapterV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import OwnerAdapterError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import NO_EFFECTS_V1

    graph = launch.build_stage1_launch_graph_v2()
    assert launch.validate_stage1_launch_graph_v2(graph).terminal_state.value == 'VALIDATED_NO_EFFECT'
    projection = launch.stage1_launch_graph_projection_v2()
    assert projection['graph'] == json.loads(deterministic_json(graph))
    first = SelectedComponentPackageAdapterV1.build_projection(deepcopy(projection))
    second = SelectedComponentPackageAdapterV1.build_projection(deepcopy(projection))
    view = SelectedComponentPackageAdapterV1.build_view(deepcopy(projection))
    other_view = SelectedComponentPackageAdapterV1.build_view(deepcopy(projection))
    assert view.canonical_projection_json.encode() == other_view.canonical_projection_json.encode()
    manifest = first['manifest']
    assert first == second
    role_ids = tuple(f'ROLE-{index:02}' for index in range(1,29))
    assert tuple(row.role_id for row in graph.roles) == role_ids
    assert tuple(row.launch_role_id for row in manifest.entries) == role_ids
    assert tuple(row.package_component_id for row in manifest.entries) == tuple('S1PKG::'+role for role in role_ids)
    assert manifest.package_version.canonical == view.package_version == '1.0.0'
    assert all(row.package_version.canonical == '1.0.0' for row in manifest.entries)
    edges = {('S1PKG::'+dependency,'S1PKG::'+role.role_id)
        for role in graph.roles for dependency in role.direct_prerequisite_role_ids}
    assert len(edges) == 102 and set(manifest.dependency_edges) == edges
    assert tuple(manifest.topological_order) == tuple('S1PKG::'+role for role in graph.topological_order)
    assert (view.entry_count,view.edge_count,view.operation_count) == (28,102,5)
    assert (view.admitted_count,view.evidence_held_count,view.implementation_held_count) == (11,5,12)
    assert view.active_live_profile_ids == () and view.no_effects is NO_EFFECTS_V1
    assert view.selected_profile_ids == ('GEMINI_TITAN_DIRECT','POLYMARKET_US_RETAIL_DIRECT','KALSHI_US_DCM_DIRECT')
    assert view.excluded_profile_ids == ('FORECASTEX_IBKR','FORECASTEX_DIRECT_MEMBER')
    families = (
        '', '', '', 'ORDERBOOK_STATE_PLUGIN STALE_BOOK_DIAGNOSTIC_PLUGIN STALE_BOOK_REPAIR_PLUGIN',
        'FEATURE_TRANSFORM_PLUGIN SIGNAL_SCORING_PLUGIN', 'FORMULA_PLUGIN',
        'PROBABILITY_CALIBRATION_PLUGIN CALIBRATION_ERROR_PLUGIN',
        'PARAMETER_STACK_PLUGIN HOLDOUT_CONFIDENCE_PLUGIN LOWER_CONFIDENCE_BOUND_PLUGIN',
        'EXECUTION_COST_PLUGIN', 'SLIPPAGE_IMPACT_PLUGIN IMPL_SHORTFALL_PLUGIN',
        'FILL_MODEL_PLUGIN PARTIAL_FILL_PLUGIN NO_FILL_PLUGIN', 'QUEUE_RISK_PLUGIN QUEUE_SURVIVAL_PLUGIN',
        'ADVERSE_SELECTION_PLUGIN', 'LATENCY_DECAY_PLUGIN', 'EXPECTED_VALUE_PLUGIN EXECUTION_COST_PLUGIN',
        'LOWER_CONFIDENCE_BOUND_PLUGIN NO_TRADE_REASON_PLUGIN DECISION_RULE_PLUGIN', '', 'RISK_BUDGET_PLUGIN',
        'THRESHOLD_POLICY_PLUGIN DECISION_RULE_PLUGIN',
        'PORTFOLIO_UTILITY_PLUGIN MARGINAL_UTILITY_PLUGIN DIVERSIFICATION_PLUGIN CORRELATION_CLUSTER_PLUGIN COMMON_DRIVER_EXPOSURE_PLUGIN RISK_BUDGET_PLUGIN',
        'AGGRESSION_LADDER_PLUGIN CANCEL_REPLACE_PLUGIN DECISION_RULE_PLUGIN', 'DECISION_RULE_PLUGIN THRESHOLD_POLICY_PLUGIN',
        'TCA_PLUGIN EDGE_ATTRIBUTION_PLUGIN IMPL_SHORTFALL_PLUGIN', '', '', 'CLASSICAL_FALLBACK_PLUGIN',
        'QUANTUM_RECIPE_PLUGIN QUBO_ADAPTER_PLUGIN BQM_ADAPTER_PLUGIN ISING_ADAPTER_PLUGIN CQM_ADAPTER_PLUGIN DQM_ADAPTER_PLUGIN QUAD_PROGRAM_ADAPTER_PLUGIN HYBRID_ROUTE_PLUGIN INTERPRET_BACK_VALIDATOR_PLUGIN PROOF_VECTOR_VALIDATOR_PLUGIN FEASIBILITY_VALIDATOR_PLUGIN COEFFICIENT_SCALING_PLUGIN UNIT_NORMALIZATION_PLUGIN PRECISION_BINNING_PLUGIN PENALTY_TUNING_PLUGIN QUBIT_COST_ESTIMATOR_PLUGIN EMBEDDING_READINESS_PLUGIN QUANTUM_SHOT_BUDGET_STRUCTURAL_PLUGIN ANNEAL_SCHEDULE_STRUCTURAL_PLUGIN',
        'AGENT_WORK_ORDER_ROUTE GOVERNANCE_REVIEW_ROUTE COMMANDER_DAG_ROUTE',
    )
    assert tuple(row.plugin_family_refs for row in view.entries) == tuple(tuple(row.split()) for row in families)
    rollback_kinds = ('DISABLE_TO_NO_EFFECT','UNAVAILABLE_OWNER_REVIEW_REQUIRED','NO_TRADE','DETERMINISTIC_CLASSICAL_FALLBACK')
    rollback_indices = (0,1,0,2,0,0,2,2,1,0,2,1,2,2,0,2,1,0,0,2,2,1,2,0,1,0,3,0)
    assert tuple(row.rollback_target_kind for row in view.entries) == tuple(rollback_kinds[index] for index in rollback_indices)
    assert {(row.package_component_id,row.fallback_component_id_or_none) for row in view.entries
        if row.fallback_component_id_or_none is not None} == {('S1PKG::ROLE-27','S1PKG::ROLE-26')}
    rollback = first['rollback_and_supersession']
    assert rollback.predecessor_package_version_or_none is None
    assert rollback.superseded_package_versions == rollback.retained_predecessor_versions == rollback.disabled_component_ids == ()
    assert rollback.supersession_state.value == 'INITIAL_CURRENT_NO_PREDECESSOR'
    assert first['reproducibility'].second_build_byte_equal is True
    assert first['reproducibility'].pure_build_effect_count == 0
    public_path = 'src/qtt/stage1_prediction_markets/selected_venues/market_data.py'
    references = {(row.launch_role_id,path,'EXISTING_CANONICAL_OWNER') for row in manifest.entries for path in row.existing_owner_paths}
    references |= {(row.launch_role_id,path,'FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED') for row in manifest.entries for path in row.future_owner_paths}
    assert len(references) == 68 and len({row[1] for row in references}) == 34
    assert {row for row in references if row[1] == public_path} == {
        ('ROLE-02',public_path,'EXISTING_CANONICAL_OWNER'),('ROLE-04',public_path,'EXISTING_CANONICAL_OWNER')}
    assert sum(row[2]=='EXISTING_CANONICAL_OWNER' for row in references) == 59
    assert sum(row[2]=='FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED' for row in references) == 9
    assert all(row.admission_state == 'HELD_IMPLEMENTATION_MISSING_NO_ADMISSION'
        for row in view.entries if row.launch_role_id in {'ROLE-02','ROLE-04'})
    assert _validate_launch_projection(deepcopy(projection))
    mutations = []
    wrong = deepcopy(projection)
    wrong['graph']['roles'][1]['path_refs'][-1]['disposition'] = 'FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED'
    wrong['graph']['roles'][8]['path_refs'][-1]['disposition'] = 'EXISTING_CANONICAL_OWNER'
    assert sum(ref['disposition']=='EXISTING_CANONICAL_OWNER' for row in wrong['graph']['roles'] for ref in row['path_refs']) == 59
    mutations.append(wrong)
    wrong = deepcopy(projection)
    wrong['graph']['roles'][3]['path_refs'][0]['path'] = 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py'
    mutations.append(wrong)
    missing = deepcopy(projection)
    missing['graph']['roles'][1]['path_refs'].pop()
    mutations.append(missing)
    duplicate = deepcopy(projection)
    duplicate['graph']['roles'][3]['path_refs'].append(deepcopy(duplicate['graph']['roles'][3]['path_refs'][0]))
    mutations.append(duplicate)
    for changed in mutations:
        with pytest.raises(PluginPackageContractError): _validate_launch_projection(changed)
        with pytest.raises(OwnerAdapterError): SelectedComponentPackageAdapterV1.build_projection(changed)
    for kind in ('readiness','live_profile','write_authority','scope_authority','exclusion'):
        changed = deepcopy(projection)
        if kind == 'readiness': changed['graph']['roles'][1]['disposition'] = 'BINDING_ONLY_GAP'
        elif kind == 'live_profile': changed['graph']['scope']['active_live_profile_ids'] = ['KALSHI_US_DCM_DIRECT']
        elif kind == 'write_authority': changed['graph']['no_effects'][next(iter(changed['graph']['no_effects']))] = True
        elif kind == 'scope_authority': changed['graph']['scope']['authority_class'] = 'UNAUTHORIZED_LIVE_AUTHORITY'
        else: changed['graph']['scope']['excluded_profile_ids'].pop()
        with pytest.raises(OwnerAdapterError): SelectedComponentPackageAdapterV1.build_projection(changed)


def _assert_lp02_public_owner_topology_guard():
    """Exercise the actual guard; neighboring thread patterns remain denied."""
    import ast
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import validation as owner
    from tools.independent_validate_qku_computation_control_plane_operations import _runtime_topology_failures

    trees=owner._package_ast()
    relative='src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py'
    path=owner.REPO_ROOT/relative
    text=path.read_text(encoding='utf-8')
    assert len(owner._public_owner_thread_imports_v1(relative,ast.parse(text)))==5
    assert owner._no_runtime_topology()
    assert not _runtime_topology_failures('source_policy.py',ast.parse(text))
    assert not owner._public_owner_thread_imports_v1(relative.replace('source_policy.py','service.py'),ast.parse(text))
    mutations=(
        text.replace('import threading','import threading as threads',1),
        text.replace('threading.RLock()','threading.Thread()',1),
        text.replace('threading.get_ident()','threading.get_ident(1)',1),
        text.replace('threading.get_ident()','threading.current_thread()',1),
        text.replace('def _public_binding_facts_v1(','def _neighbor_public_binding_facts_v1(',1),
        text+'\ndef neighboring_owner():\n    return threading.RLock()\n',
        text+'\nthreading = object()\n',
        text+'\nfrom threading import Thread\n',
        text+'\nthread_factory = threading.RLock\n',
        text+'\nimport math as threading\n',
        text+'\nfrom math import pi as threading\n',
        text.replace('def _public_binding_facts_v1(binding)', 'def _public_binding_facts_v1(binding, threading=None)',1),
        text+'\ndef threading():\n    pass\n',
        text+'\nclass threading:\n    pass\n',
        text+'\ntry:\n    pass\nexcept Exception as threading:\n    pass\n',
        text.replace('threading.RLock()', '(lambda: threading.RLock())()',1),
        text.replace('threading.get_ident()', '(lambda: threading.get_ident())()',1),
        text.replace('\nimport threading\n', '\nif True:\n    import threading\n',1),
        text.replace('\nimport threading\n', '\ntry:\n    import threading\nexcept ImportError:\n    pass\n',1),
        text+'\ndef _public_binding_facts_v1(binding):\n    pass\n',
    )
    for changed in mutations:
        assert changed!=text
        mutated=ast.parse(changed)
        assert _runtime_topology_failures('source_policy.py',mutated)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(owner,'_package_ast',lambda:tuple((p,mutated if p==path else tree) for p,tree in trees))
            assert not owner._no_runtime_topology()


def _assert_lp02_frozen_public_bindings():
    """Independent exact 20-row oracle from the approved LP02 binding map."""
    expected = json.loads('''[{"binding_id":"FIVAB::MATH-01::contract_price","math_spec_id":"MATH-01","input_name":"contract_price","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.contract_price","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[0,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-01"},{"binding_id":"FIVAB::MATH-03::best_bid","math_spec_id":"MATH-03","input_name":"best_bid","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.best_bid","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[0,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-03"},{"binding_id":"FIVAB::MATH-03::best_ask","math_spec_id":"MATH-03","input_name":"best_ask","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.best_ask","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[bid,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-03"},{"binding_id":"FIVAB::MATH-03::same_instrument_snapshot","math_spec_id":"MATH-03","input_name":"same_instrument_snapshot","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.same_instrument_snapshot","input_type":"boolean","unit_or_basis":"identity invariant","domain":"true","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-03"},{"binding_id":"FIVAB::MATH-03::snapshot_state","math_spec_id":"MATH-03","input_name":"snapshot_state","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.snapshot_state","input_type":"enum","unit_or_basis":"book state","domain":"CURRENT_CONTIGUOUS_BOOK","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-03"},{"binding_id":"FIVAB::MATH-04::best_bid","math_spec_id":"MATH-04","input_name":"best_bid","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.best_bid","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[0,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-04"},{"binding_id":"FIVAB::MATH-04::best_ask","math_spec_id":"MATH-04","input_name":"best_ask","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.best_ask","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[bid,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-04"},{"binding_id":"FIVAB::MATH-04::same_instrument_snapshot","math_spec_id":"MATH-04","input_name":"same_instrument_snapshot","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.same_instrument_snapshot","input_type":"boolean","unit_or_basis":"identity invariant","domain":"true","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-04"},{"binding_id":"FIVAB::MATH-04::snapshot_state","math_spec_id":"MATH-04","input_name":"snapshot_state","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.snapshot_state","input_type":"enum","unit_or_basis":"book state","domain":"CURRENT_CONTIGUOUS_BOOK","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-04"},{"binding_id":"FIVAB::MATH-05::best_bid","math_spec_id":"MATH-05","input_name":"best_bid","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.best_bid","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[0,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-05"},{"binding_id":"FIVAB::MATH-05::best_ask","math_spec_id":"MATH-05","input_name":"best_ask","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.best_ask","input_type":"Decimal string","unit_or_basis":"currency per contract","domain":"[bid,payout]","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-05"},{"binding_id":"FIVAB::MATH-05::same_instrument_snapshot","math_spec_id":"MATH-05","input_name":"same_instrument_snapshot","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.same_instrument_snapshot","input_type":"boolean","unit_or_basis":"identity invariant","domain":"true","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-05"},{"binding_id":"FIVAB::MATH-05::snapshot_state","math_spec_id":"MATH-05","input_name":"snapshot_state","accepted_upstream_owner_id":"SelectedVenuePublicMarketDataOwnerV1","accepted_packet_or_snapshot_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1","schema_id":"PointInTimeExecutableMarketOrOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_state.snapshot_state","input_type":"enum","unit_or_basis":"book state","domain":"CURRENT_CONTIGUOUS_BOOK","producer_receipt_type":"PointInTimeExecutableMarketOrOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"provider-native sequence/revision required for order-book fields; immutable snapshot identity otherwise","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-05"},{"binding_id":"FIVAB::MATH-36::yes_bids","math_spec_id":"MATH-36","input_name":"yes_bids","accepted_upstream_owner_id":"KalshiAcceptedOrderBookStateOwnerV1","accepted_packet_or_snapshot_type":"KalshiPointInTimeOrderBookSnapshotV1","schema_id":"KalshiPointInTimeOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"orderbook.yes_bids","input_type":"list[Decimal string]","unit_or_basis":"currency per YES contract","domain":"nonempty ascending active grid","producer_receipt_type":"KalshiPointInTimeOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"Kalshi snapshot sequence and contiguous-delta receipt","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"},{"binding_id":"FIVAB::MATH-36::no_bids","math_spec_id":"MATH-36","input_name":"no_bids","accepted_upstream_owner_id":"KalshiAcceptedOrderBookStateOwnerV1","accepted_packet_or_snapshot_type":"KalshiPointInTimeOrderBookSnapshotV1","schema_id":"KalshiPointInTimeOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"orderbook.no_bids","input_type":"list[Decimal string]","unit_or_basis":"currency per NO contract","domain":"nonempty ascending active grid","producer_receipt_type":"KalshiPointInTimeOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"Kalshi snapshot sequence and contiguous-delta receipt","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"},{"binding_id":"FIVAB::MATH-36::payout","math_spec_id":"MATH-36","input_name":"payout","accepted_upstream_owner_id":"KalshiMarketMetadataOwnerV1","accepted_packet_or_snapshot_type":"KalshiVersionedMarketPriceRangeAndPayoutSnapshotV1","schema_id":"KalshiVersionedMarketPriceRangeAndPayoutSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_metadata.payout","input_type":"Decimal string","unit_or_basis":"currency per winning contract","domain":">0","producer_receipt_type":"KalshiVersionedMarketPriceRangeAndPayoutSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"market metadata revision/effective version","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"},{"binding_id":"FIVAB::MATH-36::book_sequence","math_spec_id":"MATH-36","input_name":"book_sequence","accepted_upstream_owner_id":"KalshiAcceptedOrderBookStateOwnerV1","accepted_packet_or_snapshot_type":"KalshiPointInTimeOrderBookSnapshotV1","schema_id":"KalshiPointInTimeOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"orderbook.book_sequence","input_type":"int","unit_or_basis":"provider sequence","domain":"exact current sequence","producer_receipt_type":"KalshiPointInTimeOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"Kalshi snapshot sequence and contiguous-delta receipt","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"},{"binding_id":"FIVAB::MATH-36::expected_sequence","math_spec_id":"MATH-36","input_name":"expected_sequence","accepted_upstream_owner_id":"KalshiAcceptedOrderBookStateOwnerV1","accepted_packet_or_snapshot_type":"KalshiPointInTimeOrderBookSnapshotV1","schema_id":"KalshiPointInTimeOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"orderbook.expected_sequence","input_type":"int","unit_or_basis":"local expected sequence","domain":"must equal book_sequence","producer_receipt_type":"KalshiPointInTimeOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"Kalshi snapshot sequence and contiguous-delta receipt","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"},{"binding_id":"FIVAB::MATH-36::book_state","math_spec_id":"MATH-36","input_name":"book_state","accepted_upstream_owner_id":"KalshiAcceptedOrderBookStateOwnerV1","accepted_packet_or_snapshot_type":"KalshiPointInTimeOrderBookSnapshotV1","schema_id":"KalshiPointInTimeOrderBookSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"orderbook.book_state","input_type":"enum","unit_or_basis":"book state","domain":"CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS","producer_receipt_type":"KalshiPointInTimeOrderBookSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"Kalshi snapshot sequence and contiguous-delta receipt","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"},{"binding_id":"FIVAB::MATH-36::price_ranges","math_spec_id":"MATH-36","input_name":"price_ranges","accepted_upstream_owner_id":"KalshiMarketMetadataOwnerV1","accepted_packet_or_snapshot_type":"KalshiVersionedMarketPriceRangeAndPayoutSnapshotV1","schema_id":"KalshiVersionedMarketPriceRangeAndPayoutSnapshotV1::SCHEMA","schema_version":"1.0.0","exact_field_path":"market_metadata.price_ranges","input_type":"list[record]","unit_or_basis":"market-specific fixed-point price grid","domain":"nonempty min/max/step records","producer_receipt_type":"KalshiVersionedMarketPriceRangeAndPayoutSnapshotV1ReceiptV1","required_clock_fields":["observed_time","effective_time","available_time","received_time","processed_time","as_of_time"],"provider_native_sequence_or_revision":"market metadata revision/effective version","current_admitted_mode":"CONTRACT_AND_INDEPENDENT_ORACLE_FIXTURE_ONLY; CONTEXT_COMPUTABLE_BLOCKED_UNTIL_ACCEPTED_OWNER_PACKET","consumer":"FormulaExecutionContractV1::MATH-36"}]''')
    owners = {row['accepted_upstream_owner_id'] for row in expected}
    selected = {row.binding_id:row for bindings in FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values()
        for row in bindings if row.accepted_upstream_owner_id in owners}
    assert len(expected)==20 and set(selected)=={row['binding_id'] for row in expected}
    for row in expected:
        actual=selected[row['binding_id']]
        assert {name:list(getattr(actual,name)) if type(getattr(actual,name)) is tuple else getattr(actual,name)
            for name in row}==row


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


def _assert_lp02_conditional_cash_services(terms,profile,count,expected_net,publication_fee=None,
        expected_registry_denial=None,expected_expiry_ns=None,settlement_outcome=None):
    """Feed the real MATH-06/07 owners with explicitly synthetic dependencies."""
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import service as service_owner

    for math_id in ('MATH-06','MATH-07'):
        context=replace(_context(component_ids=(math_id,)),context_id='SYN::LP02_CASH::'+math_id,
            scope=ComputationScopeV1('SYN::MARKET',profile,'SYN::EVENT','SYN::CONTRACT','MODE_CONTEXT::CONTRACT_ONLY','SYN::SNAPSHOT'))
        if publication_fee is not None:
            from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import handoff
            from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as resolver
            publication,account,fills=publication_fee
            entry=handoff._require_public_publication_handle_v1(publication=publication)
            metadata,=entry[4]
            as_of=datetime(1970,1,1,tzinfo=UTC)+timedelta(microseconds=(entry[8]+999)//1000)
            context=replace(context,context_id=json.dumps(('SYN::LP02_CASH',math_id,
                    entry[7].typed_payload.source_use_action_ref),separators=(',',':')),
                as_of=as_of,observed_at=as_of-timedelta(seconds=1),
                source_epoch_id=entry[10],input_version=entry[11],scope=ComputationScopeV1(metadata.market_id,profile,
                    metadata.event_id_or_none or 'SYN::NO_EVENT_RELATION',metadata.instrument_id,
                    'MODE_CONTEXT::CONTRACT_ONLY',entry[7].record_id))
        clocks=PointInTimeClocksV1(*(context.as_of-timedelta(seconds=1) for _ in range(5)),context.as_of)
        values=dict(fill_probability=Decimal(1),entry_trade_cashflow_total=terms['entry_trade_cashflow_total'],
            no_fill_cashflow_total=Decimal(0),platform_fee_total=terms['platform_fee_total'],builder_fee_total=Decimal(0),
            other_fee_total=Decimal(0),expected_rebate_total=terms['expected_rebate_total'],exit_slippage_reserve_total=Decimal(0),
            market_impact_reserve_total=Decimal(0),latency_adverse_selection_reserve_total=Decimal(0),capital_time_cost_reserve_total=Decimal(0),
            cashflow_basis='SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE')
        if math_id=='MATH-06':
            values.update(p_win=Decimal('.6'),p_void=Decimal(0),win_terminal_cashflow_total=Decimal(count),
                lose_terminal_cashflow_total=Decimal(0),void_terminal_cashflow_total=Decimal(0))
        else:
            values.update(outcome_ids=('WIN','LOSE'),outcome_probabilities=('0.6','0.4'),
                outcome_terminal_cashflow_totals=(count,'0'),probability_simplex_tolerance=Decimal(0))
        bindings=FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        assert set(values)=={row.input_name for row in bindings}
        packets=tuple(OwnerValuePacketV1(packet_id='SYN::LP02_CASH::'+row.binding_id,owner_id=row.accepted_upstream_owner_id,
            packet_type=row.accepted_packet_or_snapshot_type,schema_id=row.schema_id,schema_version=row.schema_version,
            context_id=context.context_id,scope=context.scope,source_epoch_id=context.source_epoch_id,input_version=context.input_version,
            clocks=clocks,ttl=context.maximum_age,values={row.exact_field_path:values[row.input_name]},authorized_binding_ids=(row.binding_id,),
            producer_receipt_id='SYN::LP02_CASH_RECEIPT::'+row.binding_id,producer_receipt_type=row.producer_receipt_type,
            source_state_and_claim_lineage=row.source_state_and_claim_lineage,provider_sequence=1,revision=1) for row in bindings)
        request=ComputeComponentRequestV1(**_common('compute_component',context=context),component_id=math_id,
            expected_output_schema_ref=CURRENT_NAMED_OUTPUT_CONTRACTS[math_id].schema_id,
            input_values=TypedValueRecordV1((TypedValueV1('platform_fee_total',TypedValueKindV1.DECIMAL,
                terms['platform_fee_total'],next(row.unit_or_basis for row in bindings if row.input_name=='platform_fee_total'),
                'SYNTHETIC_CONDITIONAL_FIXTURE'),)))
        invoked=[]
        original=service_owner.invoke_formula_v34
        def invoke(component_id,inputs):
            invoked.append(component_id)
            return original(component_id,inputs)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(service_owner,'invoke_formula_v34',invoke)
            registry=CanonicalOwnerPacketRegistryV1(packets)
            if publication_fee is not None:
                fee_names={'entry_trade_cashflow_total','platform_fee_total','expected_rebate_total'}
                if settlement_outcome is not None and math_id=='MATH-06':
                    fee_names.add('win_terminal_cashflow_total' if settlement_outcome=='YES' else 'lose_terminal_cashflow_total')
                fee_bindings=tuple(row.binding_id for row in bindings if row.input_name in fee_names)
                kwargs=dict(publication=publication,context=context,binding_ids=fee_bindings,source_bindings=entry[5],
                    applicability=account,fills=fills,order_ref='SYN::FRESH_HYPOTHETICAL_ORDER',prior_unrounded=Decimal(0),
                    prior_collected=Decimal(0),prior_rounding_overpayment=Decimal(0),carry_evidence_refs=(),
                    fresh_hypothetical_order=True,include_deferred_taker_rebate=False)
                if expected_registry_denial is not None:
                    with pytest.raises(ComputationControlPlaneError,match=expected_registry_denial):
                        resolver._issue_public_fee_registry_v1(**kwargs)
                    continue
                fee_registry=resolver._issue_public_fee_registry_v1(**kwargs)
                for source in entry[5]:
                    remaining=tuple(row for row in entry[5] if row is not source)
                    if remaining:
                        with pytest.raises(ComputationControlPlaneError):
                            resolver._issue_public_fee_registry_v1(**{**kwargs,'source_bindings':remaining})
                if math_id=='MATH-06':
                    unsupported=('lose_terminal_cashflow_total' if settlement_outcome=='YES' else 'win_terminal_cashflow_total')
                    with pytest.raises(ComputationControlPlaneError):
                        resolver._issue_public_fee_registry_v1(**{**kwargs,
                            'binding_ids':('FIVAB::MATH-06::'+unsupported,)})
                for row in bindings:
                    if row.input_name in fee_names:
                        actual=fee_registry.packet_for(context=context,binding_id=row.binding_id)
                        assert actual.values[row.exact_field_path]==values[row.input_name]
                        assert actual.owner_id=='PRETRADE1' and actual.provider_sequence is None
                for changes in ({'applicability':replace(account)},
                    {'binding_ids':(next(row.binding_id for row in bindings if row.input_name=='fill_probability'),)},
                    {'source_bindings':tuple(replace(row) for row in entry[5])},
                    {'context':replace(context,source_epoch_id='SYN::OTHER_EPOCH')},
                    {'fresh_hypothetical_order':False,'carry_evidence_refs':()},
                    {'fresh_hypothetical_order':True,'prior_collected':Decimal(1)}):
                    with pytest.raises(ComputationControlPlaneError):resolver._issue_public_fee_registry_v1(**{**kwargs,**changes})
                detached=CanonicalOwnerPacketRegistryV1(tuple(replace(packet) for packet in fee_registry.packets))
                with pytest.raises(ComputationControlPlaneError):detached.packet_for(context=context,binding_id=fee_bindings[0])
                dependencies=CanonicalOwnerPacketRegistryV1(tuple(packet for packet in packets
                    if not set(packet.authorized_binding_ids)&set(fee_bindings)))
                registry=resolver._join_public_owner_dependencies_v1(registry=fee_registry,dependencies=dependencies)
            service=QKUComputationControlPlaneV1(registry,agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION)
            response=service.compute_component(request)
            assert response.status is OperationStatusV1.SUCCEEDED and invoked==[math_id]
            assert response.component_result.formula_output.value['expected_net_cash']==Decimal(expected_net)
            assert response.component_result.no_authority_flag is True
            missing=next(packet for packet in packets if packet.owner_id=='CalibratedProbabilityModelOwnerV1')
            missing_registry=(resolver._join_public_owner_dependencies_v1(registry=fee_registry,
                dependencies=CanonicalOwnerPacketRegistryV1(tuple(packet for packet in dependencies.packets if packet is not missing)))
                if publication_fee is not None else CanonicalOwnerPacketRegistryV1(tuple(packet for packet in packets if packet is not missing)))
            denied=QKUComputationControlPlaneV1(missing_registry,
                agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION).compute_component(request)
            assert denied.status is not OperationStatusV1.SUCCEEDED and invoked==[math_id]
            if expected_expiry_ns is not None:
                import time
                with pytest.MonkeyPatch.context() as expired:
                    expired.setattr(time,'time_ns',lambda:expected_expiry_ns)
                    with pytest.raises(ComputationControlPlaneError):
                        fee_registry.packet_for(context=context,binding_id=fee_bindings[0])
                    with pytest.raises(ComputationControlPlaneError,match='exclusive deadline changed'):
                        service.compute_component(request)
                    assert invoked==[math_id]


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

    from tests.stage1_prediction_markets.qku_computation_control_plane.accounting.test_contract_matrix import _synthetic_kalshi_observation, _scheduled_kalshi_fixture
    # New temporal composition feeds the same real MATH-06 synthetic packet route.
    # Translating the fixture's knowledge instant to this existing context changes no economics.
    for multiplier, grid, expected in (('3','.01','.04'),('6','.01','-.01'),('3','.0001','.046'),('6','.0001','-.006')):
        scheduled_inputs, scheduled_fills = _scheduled_kalshi_fixture(multiplier, moment=moment)
        terms = pretrade_module.compose_kalshi_scheduled_fee_scenario_cashflows_v1(
            **{**common,'balance_increment':Decimal(grid)}, **scheduled_inputs, fills=scheduled_fills)
        values = fixture_values(terms)
        values.update(p_win=Decimal('.6'), p_void=Decimal(0), fill_probability=Decimal(1),
                      win_terminal_cashflow_total=Decimal(3), void_terminal_cashflow_total=Decimal(0),
                      exit_slippage_reserve_total=Decimal(0), market_impact_reserve_total=Decimal(0),
                      latency_adverse_selection_reserve_total=Decimal(0), capital_time_cost_reserve_total=Decimal(0))
        response = evaluate(values)
        assert response.status is OperationStatusV1.SUCCEEDED and invocations == ['MATH-06']
        output = response.component_result.formula_output
        assert output.execution_context is context and output.no_authority_flag is True
        assert output.value['expected_net_cash'] == Decimal(expected)
        assert output.value['expected_terminal_cashflow'] == Decimal('1.8')
        assert Fraction(Decimal(expected)) == Fraction(3,5)*3 + Fraction(terms.entry_trade_cashflow_total) - Fraction(terms.platform_fee_total) + Fraction(terms.expected_rebate_total)
    assert roster_before == (tuple(IMPLEMENTATION_REGISTRY),tuple(ST12B_OPERATION_CAPABILITY_BY_ID))
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as observation_source
    observed_wrapper = pretrade_module.compose_kalshi_observed_fee_scenario_cashflows_v1
    with _synthetic_kalshi_observation() as fixture:
        observed_bodies = fixture.bodies
    observed_fills = (KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal('.50')),)
    observed_rosters = (tuple(observation_source.SOURCE_STATE_BY_ID), tuple(observation_source.SOURCE_OVERLAY_BY_ID))
    for series_multiplier, override, applied, fee, expected in (
        (b'1',False,'1','1.75','1.8'), (b'1',True,'2','3.50','.4'),
        (b'1',False,'1','1.75','1.8'), (b'3',False,'3','5.25','-1.0')):
        event = observed_bodies[1]
        if override:
            event = event.replace(b'"fee_type_override":null',b'"fee_type_override":"quadratic"').replace(
                b'"fee_multiplier_override":null',b'"fee_multiplier_override":2')
        raw = (*observed_bodies[:1],event,observed_bodies[2].replace(b'"fee_multiplier":1',b'"fee_multiplier":'+series_multiplier))
        with _synthetic_kalshi_observation(bodies=raw, fills=observed_fills,
                balance_increment=common['balance_increment'], prior_rounding_overpayment=common['prior_rounding_overpayment']) as fixture:
            cohort = fixture.owner.capture()
            assert cohort.market_ticker == context.scope.market_scope_id
            resolved, delegated_calls, delegated_results = [], [], []
            real_resolve = observation_source.KalshiFeeObservationOwnerV1.resolve_scenario_multiplier
            real_compose = pretrade_module.compose_kalshi_quadratic_taker_buy_yes_cashflows_v1
            def resolve_spy(self, **kwargs):
                resolved.append((self,kwargs)); return real_resolve(self,**kwargs)
            def compose_spy(**kwargs):
                delegated_calls.append(kwargs); result = real_compose(**kwargs); delegated_results.append(result); return result
            observed_kwargs = dict(**common, source_owner=fixture.owner, cohort=cohort,
                expected_market_ticker=context.scope.market_scope_id,
                as_of_monotonic_ns=cohort.available_monotonic_ns, fills=observed_fills)
            with monkeypatch.context() as delegated:
                delegated.setattr(observation_source.KalshiFeeObservationOwnerV1,'resolve_scenario_multiplier',resolve_spy)
                delegated.setattr(pretrade_module,'compose_kalshi_quadratic_taker_buy_yes_cashflows_v1',compose_spy)
                terms = observed_wrapper(**observed_kwargs)
                assert len(resolved) == 2 and len(delegated_calls) == 1 and terms is delegated_results[0]
                assert resolved[0] == resolved[1]  # Original resolution plus final publication fence.
                assert resolved[0][0] is fixture.owner and resolved[0][1]['cohort'] is cohort
                assert delegated_calls[0]['fee_multiplier'] is cohort.fee_multiplier
                for name in (*common,'fills'):
                    assert delegated_calls[0][name] is observed_kwargs[name]
                for changes in ({'profile_id':'KALSHI'},{'currency':'EUR'},{'source_owner':object()},
                                {'cohort':replace(cohort)},{'as_of_monotonic_ns':cohort.available_monotonic_ns-1}):
                    with pytest.raises(ComputationControlPlaneError):
                        observed_wrapper(**{**observed_kwargs,**changes})
                    assert len(delegated_calls) == 1
            assert cohort.fee_multiplier == Decimal(applied) and terms.platform_fee_total == Decimal(fee)
            assert terms.entry_trade_cashflow_total == Decimal(-50) and terms.expected_rebate_total == 0
            if override:
                legacy = pretrade_module.compose_kalshi_market_linked_series_base_cashflows_v1(
                    **common, raw_market_response=raw[0], raw_event_response=raw[1], raw_series_response=raw[2],
                    expected_market_ticker=cohort.market_ticker, fills=observed_fills)
                assert legacy.platform_fee_total == Decimal('1.75') and terms.platform_fee_total == Decimal('3.50')
        # Actual MATH-06 consumption now comes from a fresh one-shot session.
        # The original composer checks above remain independent predecessor coverage.
        with _synthetic_kalshi_observation(bodies=raw, fills=observed_fills,
                balance_increment=common['balance_increment'], prior_rounding_overpayment=common['prior_rounding_overpayment']) as fixture:
            session = pretrade_module.KalshiFeeScenarioSessionV1(**fixture.authorize())
            assert not fixture.connections and not fixture.sends
            scenario = session.evaluate(
                fills=observed_fills, balance_increment=common['balance_increment'],
                prior_rounding_overpayment=common['prior_rounding_overpayment'])
            assert scenario.market_ticker == context.scope.market_scope_id
            assert scenario.fills is observed_fills and scenario.fee_multiplier == Decimal(applied)
            assert scenario.fee_basis == ('OBSERVED_EVENT_OVERRIDE' if override else 'OBSERVED_SERIES_BASE')
            assert scenario.evidence_class == 'OBSERVED_FEE_HYPOTHETICAL_SCENARIO'
            assert len(fixture.sends) == 3
            terms = scenario.cashflows
            assert terms.platform_fee_total == Decimal(fee)
            assert terms.entry_trade_cashflow_total == Decimal(-50) and terms.expected_rebate_total == 0
            assert Fraction(Decimal(expected)) == Fraction(4,5)*(-50+55-Fraction(fee)-1)
            values = fixture_values(terms)
            response = evaluate(values)
            assert response.status is OperationStatusV1.SUCCEEDED and invocations == ['MATH-06']
            assert response.component_result.formula_output.execution_context is context
            assert response.component_result.formula_output.value['expected_net_cash'] == Decimal(expected)
            rejected = evaluate({**values,'platform_fee_total':Decimal('99')},fixture_packets(values))
            assert rejected.status is not OperationStatusV1.SUCCEEDED and invocations == []
            assert ReasonCode.INPUT_VALUE_CONFLICT.value in rejected.receipt_refs
    assert observed_rosters == (tuple(observation_source.SOURCE_STATE_BY_ID), tuple(observation_source.SOURCE_OVERLAY_BY_ID))
    assert roster_before == (tuple(IMPLEMENTATION_REGISTRY),tuple(ST12B_OPERATION_CAPABILITY_BY_ID))

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


    # These supplied identities link only a hypothetical Series-base scenario.
    linked_wrapper = pretrade_module.compose_kalshi_market_linked_series_base_cashflows_v1
    market_raw = b'{"market":{"ticker":"SYNTHETIC::MARKET","event_ticker":"QTT-LINK-EVENT"}}'
    event_raw = b'{"event":{"event_ticker":"QTT-LINK-EVENT","series_ticker":"QTT-LINK-SERIES"}}'
    linked_series_raw = b'{"series":{"ticker":"QTT-LINK-SERIES","fee_type":"quadratic","fee_multiplier":1}}'
    linked_common = {**common, "raw_market_response": market_raw, "raw_event_response": event_raw,
                     "raw_series_response": linked_series_raw, "expected_market_ticker": "SYNTHETIC::MARKET"}
    assert linked_common["expected_market_ticker"] == context.scope.market_scope_id
    link_calls, link_results = [], []
    real_link = source_owner.decode_kalshi_market_linked_series_fee_candidate_v1

    def counted_link(**kwargs):
        link_calls.append(kwargs)
        candidate = real_link(**kwargs)
        link_results.append(candidate)
        return candidate

    with monkeypatch.context() as delegated:
        delegated.setattr(pretrade_module, "decode_kalshi_market_linked_series_fee_candidate_v1", counted_link)
        delegated.setattr(pretrade_module, "compose_kalshi_quadratic_taker_buy_yes_cashflows_v1", counted_taker)
        taker_calls.clear(); taker_results.clear()
        ordered = (KalshiQuadraticTakerBuyYesFillV1(Decimal(50), Decimal(".4")), *portions)
        forwarded = linked_wrapper(**linked_common, fills=ordered)
        assert len(link_calls) == len(taker_calls) == 1
        assert set(link_calls[0]) == {"raw_market_response", "raw_event_response", "raw_series_response", "expected_market_ticker"}
        assert all(link_calls[0][key] is linked_common[key] for key in link_calls[0])
        assert taker_calls[0]["fee_multiplier"] is link_results[0].fee_multiplier
        assert taker_calls[0]["fills"] is ordered and forwarded is taker_results[0]
        assert all(taker_calls[0][key] is linked_common[key] for key in common)
        assert tuple((fill.contracts, fill.yes_price) for fill in ordered) == (
            (Decimal(50), Decimal(".4")), *((Decimal(25), Decimal(".5")),) * 4,
        )
        for changes in ({"profile_id": "KALSHI"}, {"profile_id": StringSubclass(profile)},
                        {"currency": "usd"}, {"currency": StringSubclass("USD")}):
            link_calls.clear(); taker_calls.clear(); invocations.clear()
            with pytest.raises(ContractValidationError) as rejected:
                linked_wrapper(**{**linked_common, "raw_market_response": b"{", **changes}, fills=portions)
            assert rejected.value.reason_code is ReasonCode.INVALID_CONTRACT
            assert str(rejected.value).endswith(": exact Kalshi profile required" if "profile_id" in changes else ": exact USD currency required")
            assert link_calls == taker_calls == invocations == []
        for changes, reason in (
            ({"raw_market_response": market_raw.replace(b"SYNTHETIC::MARKET", b"OTHER-MARKET")}, ReasonCode.INPUT_SCOPE_MISMATCH),
            ({"raw_event_response": event_raw.replace(b"QTT-LINK-EVENT", b"OTHER-EVENT")}, ReasonCode.INPUT_SCOPE_MISMATCH),
            ({"raw_series_response": linked_series_raw.replace(b"QTT-LINK-SERIES", b"OTHER-SERIES")}, ReasonCode.INPUT_SCOPE_MISMATCH),
            ({"raw_series_response": linked_series_raw.replace(b'"quadratic"', b'"flat"')}, ReasonCode.INVALID_CONTRACT),
            ({"raw_series_response": linked_series_raw.replace(b'"fee_multiplier":1', b'"fee_multiplier":-1')}, ReasonCode.INVALID_CONTRACT),
        ):
            link_calls.clear(); taker_calls.clear(); invocations.clear()
            with pytest.raises(ContractValidationError) as rejected:
                linked_wrapper(**{**linked_common, **changes}, fills=portions)
            assert rejected.value.reason_code is reason
            assert len(link_calls) == 1 and taker_calls == invocations == []
        for changes, reason in (
            ({"fills": ()}, ReasonCode.INVALID_CONTRACT),
            ({"fills": (malformed_row,)}, ReasonCode.OUT_OF_DOMAIN),
            ({"balance_increment": Decimal(".001")}, ReasonCode.OUT_OF_DOMAIN),
            ({"prior_rounding_overpayment": Decimal("sNaN")}, ReasonCode.NONFINITE_NUMERIC_INPUT),
        ):
            link_calls.clear(); taker_calls.clear(); invocations.clear()
            with pytest.raises(ComputationControlPlaneError) as rejected:
                linked_wrapper(**{**linked_common, "fills": portions, **changes})
            assert rejected.value.reason_code is reason
            assert len(link_calls) == len(taker_calls) == 1 and invocations == []
        link_calls.clear(); taker_calls.clear()
        from inspect import Parameter, signature
        parameters = signature(linked_wrapper).parameters
        assert set(parameters) == {*linked_common, "fills"} and len(parameters) == 9
        assert all(p.kind is Parameter.KEYWORD_ONLY and p.default is Parameter.empty for p in parameters.values())
        for omitted in parameters:
            with pytest.raises(TypeError):
                linked_wrapper(**{key: value for key, value in {**linked_common, "fills": portions}.items() if key != omitted})
        for extra in ("fee_multiplier", "expected_series_ticker"):
            with pytest.raises(TypeError):
                linked_wrapper(**linked_common, fills=portions, **{extra: None})
        with pytest.raises(TypeError):
            linked_wrapper(profile, "USD", market_raw, event_raw, linked_series_raw, "SYNTHETIC::MARKET", portions, Decimal(".01"), Decimal(0))
        assert link_calls == taker_calls == []

        maximum_fills = (KalshiQuadraticTakerBuyYesFillV1(Decimal(1), Decimal(".5")),) * 4096
        maximum = linked_wrapper(**{**linked_common, "raw_series_response": linked_series_raw.replace(b'"fee_multiplier":1', b'"fee_multiplier":0')}, fills=maximum_fills)
        assert len(link_calls) == len(taker_calls) == 1 and taker_calls[0]["fills"] is maximum_fills
        assert tuple(getattr(maximum, field.name) for field in fields(maximum)) == tuple(map(Decimal, ("-2048", "0", "0", "0")))
        assert_taker_service(maximum, "163.04", 4096)

    linked_consumed = []
    for quantity, price, token, grid, literals, expected in (
        ("100", ".5", b"1", ".01", ("-50", "1.75", "0", "0"), "1.8"),
        ("100", ".5", b"2", ".01", ("-50", "3.5", "0", "0"), ".4"),
        ("100", ".6", b"1.0", ".0001", ("-60", "1.68", "0", "0"), "-6.144"),
        ("50", ".5", b"1e0", ".01", ("-25", ".88", "0", ".005"), ".496"),
        ("50", ".5", b"1e0", ".0001", ("-25", ".875", "0", "0"), ".5"),
    ):
        raw = linked_series_raw.replace(b'"fee_multiplier":1', b'"fee_multiplier":' + token)
        fills = (KalshiQuadraticTakerBuyYesFillV1(Decimal(quantity), Decimal(price)),)
        terms = linked_wrapper(**{**linked_common, "raw_series_response": raw, "balance_increment": Decimal(grid)}, fills=fills)
        assert type(terms) is KalshiConditionalCashflowTermsV1
        assert tuple(getattr(terms, field.name) for field in fields(terms)) == tuple(map(Decimal, literals))
        _, cash = assert_taker_service(terms, expected, int(quantity))
        linked_consumed.append(cash)
        assert tuple((fill.contracts, fill.yes_price) for fill in fills) == ((Decimal(quantity), Decimal(price)),)
    assert linked_consumed[:2] == [Decimal("1.8"), Decimal(".4")]
    renamed = {**linked_common, "raw_event_response": event_raw.replace(b"QTT-LINK-SERIES", b"RENAMED-SERIES"),
               "raw_series_response": linked_series_raw.replace(b"QTT-LINK-SERIES", b"RENAMED-SERIES")}
    assert_taker_service(linked_wrapper(**renamed, fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal(".5")),)), "1.8")

    linked_whole = linked_wrapper(**linked_common, fills=portions)
    assert tuple(getattr(linked_whole, field.name) for field in fields(linked_whole)) == tuple(map(Decimal, ("-50", "1.76", ".01", "0")))
    linked_values, linked_cash = assert_taker_service(linked_whole, "1.8")
    no_refund = evaluate({**linked_values, "expected_rebate_total": Decimal(0)})
    assert no_refund.status is OperationStatusV1.SUCCEEDED and invocations == ["MATH-06"]
    assert no_refund.component_result.formula_output.value["expected_net_cash"] == Decimal("1.792")
    assert Fraction(linked_cash) - Fraction(no_refund.component_result.formula_output.value["expected_net_cash"]) == Fraction(".008")
    prefix = linked_wrapper(**linked_common, fills=portions[:2])
    suffix = linked_wrapper(**{**linked_common, "prior_rounding_overpayment": prefix.rounding_overpayment_after}, fills=portions[2:])
    for name in ("entry_trade_cashflow_total", "platform_fee_total", "expected_rebate_total"):
        assert Fraction(getattr(prefix, name)) + Fraction(getattr(suffix, name)) == Fraction(getattr(linked_whole, name))
    assert suffix.rounding_overpayment_after == linked_whole.rounding_overpayment_after
    for grid, literals in ((".01", ("-.055", ".005", "0", ".001361")),
                           (".0001", ("-.055", ".0037", "0", ".000061"))):
        producer_calls.clear()
        with monkeypatch.context() as delegated:
            delegated.setattr(pretrade_module, "kalshi_quadratic_taker_buy_yes_input_v1", counted_producer)
            terms = linked_wrapper(**{**linked_common, "raw_series_response": linked_series_raw.replace(b'"fee_multiplier":1', b'"fee_multiplier":2.1'),
                                      "balance_increment": Decimal(grid)}, fills=(fractional_fill,))
        assert len(producer_calls) == 1 and producer_calls[0][1].model_fee == Decimal(".00363825")
        assert tuple(getattr(terms, field.name) for field in fields(terms)) == tuple(map(Decimal, literals))
        assert_fractional_series_service(terms, ".1", "-.804" if grid == ".01" else "-.80296")
    rejected = evaluate({**linked_values, "platform_fee_total": Decimal("1.75")}, fixture_packets(linked_values))
    assert rejected.status is not OperationStatusV1.SUCCEEDED and rejected.component_result.formula_output is None
    assert ReasonCode.INPUT_VALUE_CONFLICT.value in rejected.receipt_refs and invocations == []
    assert source_rosters_before == (
        tuple(source_owner.CERTIFIED_SOURCE_STATES), tuple(source_owner.SOURCE_CURRENTIZATION_OVERLAYS),
        tuple(source_owner.SOURCE_STATE_BY_ID), tuple(source_owner.SOURCE_OVERLAY_BY_ID),
        tuple(source_owner.ST12H_SOURCE_BINDINGS), tuple(source_owner.ST12H_SOURCE_CURRENTIZATION_RULES),
    )
    assert roster_before == (tuple(IMPLEMENTATION_REGISTRY), tuple(ST12B_OPERATION_CAPABILITY_BY_ID))
    assert linked_common == {**common, "raw_market_response": market_raw, "raw_event_response": event_raw,
                             "raw_series_response": linked_series_raw, "expected_market_ticker": "SYNTHETIC::MARKET"}


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


def _assert_lp02_scalar_service(handle,*,expected_price):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as resolver
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import handoff
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    entry=handoff._require_public_publication_handle_v1(publication=handle)
    state,=entry[3].values()
    now=datetime(1970,1,1,tzinfo=UTC)+timedelta(microseconds=(entry[8]+999)//1000)
    scope=ComputationScopeV1(state.market_id,state.profile_id.value,
        entry[4][0].event_id_or_none or 'SYN::LOCAL_UNAVAILABLE_EVENT',
        state.instrument_id,'MODE_CONTEXT::CONTRACT_ONLY',state.state_id)
    dependency_clocks=PointInTimeClocksV1(now-timedelta(seconds=1),now-timedelta(seconds=1),
        now-timedelta(seconds=1),now-timedelta(seconds=1),now-timedelta(seconds=1),now)

    def service_for(context):
        registry=resolver.issue_public_owner_registry_v1(publication=handle,context=context,
            binding_ids=('FIVAB::MATH-01::contract_price',),source_bindings=entry[5])
        for source in entry[5]:
            remaining=tuple(row for row in entry[5] if row is not source)
            if remaining:
                with pytest.raises(ComputationControlPlaneError):
                    resolver.issue_public_owner_registry_v1(publication=handle,context=context,
                        binding_ids=('FIVAB::MATH-01::contract_price',),source_bindings=remaining)
        packet,=registry.packets
        assert packet.provider_sequence is packet.revision is None
        assert packet.values['market_state.contract_price']==expected_price
        with pytest.raises(ComputationControlPlaneError):
            resolver.FormulaInputResolverV1.resolve('MATH-01',context=context,owner_registry=registry)
        dependencies=[]
        for item in _packets(context):
            if item.authorized_binding_ids==('FIVAB::MATH-01::contract_price',):continue
            values=dict(item.values)
            if 'contract_semantics.payout_per_winning_contract' in values:
                values={'contract_semantics.payout_per_winning_contract':'1'}
            if 'prediction.calibrated_probability' in values:
                values={'prediction.calibrated_probability':0.6}
            dependencies.append(replace(item,packet_id=context.context_id+'::'+item.packet_id,
                clocks=dependency_clocks,values=values))
        joined=resolver._join_public_owner_dependencies_v1(registry=registry,
            dependencies=CanonicalOwnerPacketRegistryV1(tuple(dependencies)))
        return QKUComputationControlPlaneV1(owner_registry=joined,agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION)

    context=replace(_context(component_ids=('MATH-01',)),
        context_id='SYN::SCALAR_COMPONENT::'+state.profile_id.value,as_of=now,observed_at=now,
        source_epoch_id=entry[10],input_version=entry[11],scope=scope)
    service=service_for(context)
    request=ComputeComponentRequestV1(**dict(_common('compute_component',context=context),requested_at=now),
        component_id='MATH-01',input_values=TypedValueRecordV1((_component_record().fields[1],)),
        expected_output_schema_ref='MATH-01::OUTPUT')
    result=service.compute_component(request)
    assert result.status is OperationStatusV1.SUCCEEDED, result
    assert result.component_result.formula_output.value==Decimal(expected_price)
    stack_context=replace(_context(component_ids=('MATH-01','MATH-02'),dependency_graph_id=STACK_ID),
        context_id='SYN::SCALAR_STACK::'+state.profile_id.value,as_of=now,observed_at=now,
        source_epoch_id=entry[10],input_version=entry[11],scope=scope)
    stack_service=service_for(stack_context)
    stack=stack_service.compute_stack(ComputeStackRequestV1(**dict(_common('compute_stack',context=stack_context),requested_at=now),
        stack_id=STACK_ID,component_ids=('MATH-01','MATH-02'),input_values=TypedValueRecordV1((_stack_record().fields[1],))))
    assert stack.status is OperationStatusV1.SUCCEEDED, stack
    assert stack.stack_result.component_outputs[0].value==Decimal(expected_price)
    assert stack.stack_result.component_outputs[1].value==pytest.approx(0.11,abs=1e-15)
    # Retail does not gain sequenced book capabilities from a scalar trade.
    if state.profile_id.value=='POLYMARKET_US_RETAIL_DIRECT':
        with pytest.raises(ComputationControlPlaneError):
            resolver.issue_public_owner_registry_v1(publication=handle,context=context,
                binding_ids=('FIVAB::MATH-03::snapshot_state',),source_bindings=entry[5])
    permission=entry[1]._binding
    original=service_module.invoke_formula_v34
    def invalidate_after_computation(*args,**kwargs):
        value=original(*args,**kwargs)
        permission._failed=True
        return value
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(service_module,'invoke_formula_v34',invalidate_after_computation)
        with pytest.raises(ComputationControlPlaneError):service.compute_component(request)


def _assert_lp02_book_services(handle,*,expected_book):
    from fractions import Fraction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as resolver
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import handoff
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError

    entry=handoff._require_public_publication_handle_v1(publication=handle)
    state,=entry[3].values()
    now=datetime(1970,1,1,tzinfo=UTC)+timedelta(microseconds=(entry[8]+999)//1000)
    bid,ask,midpoint,spread,ratio=expected_book
    for math_id in ('MATH-03','MATH-04','MATH-05'):
        context=replace(_context(component_ids=(math_id,)),
            context_id='SYN::BOOK_SERVICE::'+math_id+'::'+ask,as_of=now,observed_at=now,
            source_epoch_id=entry[10],input_version=entry[11],
            scope=ComputationScopeV1(state.market_id,state.profile_id.value,entry[4][0].event_id_or_none or 'SYN::NO_EVENT_RELATION',
                state.instrument_id,'MODE_CONTEXT::CONTRACT_ONLY',state.state_id))
        bindings=FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        public=tuple(row for row in bindings if row.accepted_upstream_owner_id=='SelectedVenuePublicMarketDataOwnerV1')
        registry=resolver.issue_public_owner_registry_v1(publication=handle,context=context,
            binding_ids=tuple(row.binding_id for row in public),source_bindings=entry[5])
        values={key:value for packet in registry.packets for key,value in packet.values.items()}
        assert values['market_state.best_bid']==bid and values['market_state.best_ask']==ask
        assert values['market_state.snapshot_state']=='CURRENT_CONTIGUOUS_BOOK'
        assert all(packet.provider_sequence==state.last_provider_sequence_end_or_none for packet in registry.packets)
        with pytest.raises(ComputationControlPlaneError):
            resolver.FormulaInputResolverV1.resolve(math_id,context=context,owner_registry=registry)
        payout,=tuple(row for row in bindings if row not in public)
        assert payout.input_name=='payout'
        clocks=PointInTimeClocksV1(now-timedelta(seconds=1),now-timedelta(seconds=1),
            now-timedelta(seconds=1),now-timedelta(seconds=1),now-timedelta(seconds=1),now)
        separately_owned=OwnerValuePacketV1(packet_id=context.context_id+'::PAYOUT',owner_id=payout.accepted_upstream_owner_id,
            packet_type=payout.accepted_packet_or_snapshot_type,schema_id=payout.schema_id,schema_version=payout.schema_version,
            context_id=context.context_id,scope=context.scope,source_epoch_id=context.source_epoch_id,input_version=context.input_version,
            clocks=clocks,ttl=timedelta(days=1),values={payout.exact_field_path:'1'},authorized_binding_ids=(payout.binding_id,),
            producer_receipt_id=context.context_id+'::PAYOUT_RECEIPT',producer_receipt_type=payout.producer_receipt_type,
            source_state_and_claim_lineage=payout.source_state_and_claim_lineage,provider_sequence=None,revision=1)
        joined=resolver._join_public_owner_dependencies_v1(registry=registry,
            dependencies=CanonicalOwnerPacketRegistryV1((separately_owned,)))
        service=QKUComputationControlPlaneV1(owner_registry=joined,agent_capability_resolver=_EXPLICIT_NO_EFFECT_TEST_ADMISSION)
        request=ComputeComponentRequestV1(**dict(_common('compute_component',context=context),requested_at=now),
            component_id=math_id,input_values=TypedValueRecordV1((TypedValueV1('payout',TypedValueKindV1.DECIMAL,
                Decimal('1'),'currency per winning contract','separately owned contract semantics'),)),
            expected_output_schema_ref=math_id+'::OUTPUT')
        response=service.compute_component(request)
        assert response.status is OperationStatusV1.SUCCEEDED, response
        value=response.component_result.formula_output.value
        if math_id=='MATH-03':assert value==Decimal(midpoint)
        elif math_id=='MATH-04':assert value==Decimal(spread)
        else:
            assert abs(Fraction(value['relative_spread_ratio'])-Fraction(*ratio))<Fraction(1,10**24)
            assert abs(Fraction(value['relative_spread_bps'])-Fraction(ratio[0]*10000,ratio[1]))<Fraction(1,10**20)
