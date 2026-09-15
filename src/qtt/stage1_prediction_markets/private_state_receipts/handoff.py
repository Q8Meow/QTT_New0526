from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
)


def build_private_state_downstream_handoff(
    *,
    private_state_read_receipts: list[Mapping[str, object]],
    account_wallet_balance_receipts: list[Mapping[str, object]],
    linkage_receipts: list[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "private_state_downstream_handoff_id": "PR130_PRIVATE_STATE_DOWNSTREAM_HANDOFF_V1",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "source_repo_pr_label": "PR130",
        "venue_ids_in_scope": list(ACTIVE_STAGE1_VENUES),
        "private_state_read_receipt_ids": [
            record["private_state_read_receipt_id"]
            for record in private_state_read_receipts
        ],
        "account_wallet_balance_receipt_ids": [
            record["account_wallet_balance_receipt_id"]
            for record in account_wallet_balance_receipts
        ],
        "private_state_to_runtime_cash_linkage_receipt_ids": [
            record["private_state_to_runtime_cash_linkage_receipt_id"]
            for record in linkage_receipts
        ],
        "future_credential_alias_secret_no_capture_pr": "PR113",
        "future_market_data_ingest_pr": "PR114",
        "future_orderbook_event_snapshot_pr": "PR115",
        "future_runtime_resolver_snapshot_pr": "PR116",
        "future_atomicrows_bridge_materialization_recommended_after_repo_pr": "PR135",
        "production_downstream_authority": False,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }


from datetime import datetime
from .request import RetailPrivateReadRequestV1, RetailPrivateIngressV1
from .receipt import _f14_selected_native_v1
from ..qku_computation_control_plane.source_policy import (
    RetailPrivateSourceRegistryV1, _f14_ingress_require_v1)
from ..qku_computation_control_plane.input_resolver import PrivateObservationPublisherV1
from ..qku_computation_control_plane.persistence import (
    PersistenceAdapterV1, PersistenceAvailabilityV1, InMemoryPersistenceAdapterV1,
    PrivateEvidenceReadRequestV1, _IdempotencyResultBindingV1)
from ..qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
from ..qku_computation_control_plane.context import _f14_plain_v1, _f14_freeze_v1
from ..qku_computation_control_plane.errors import (
    ComputationControlPlaneError, ContractValidationError, TransactionContractError, ReasonCode)
from ..qku_computation_control_plane.models import NO_EFFECTS_V1
from ..qku_computation_control_plane.receipts import (
    EconomicReceiptEventSpineV1, EconomicRecordTypeV1, PrivateObservationClockReceiptV1,
    _f14_witness_v1, _native_retail_private_evidence_join_v1)
from ..qku_computation_control_plane.serialization import (
    deterministic_json, _f14_dumps_v1, _f14_load_canonical_v1, _f14_native_time_v1,
    _f14_phase_shapes_v1, _F14_PHASES, _F14_CLOCK_BODY, _F14_ROUTES, _F14_FLAG_FIELDS,
    _native_retail_transport_storage_projection_v1)
from ..qku_computation_control_plane.idempotency import IdempotencyClaimReceiptV1, IdempotencyClaimStateV1
from ..qku_computation_control_plane.lifecycle import StateTransitionReceiptV1, TransitionDispositionV1
from ..qku_computation_control_plane.outbox import OutboxIntentRecordV1, OutboxDispatchStateV1
from ..qku_computation_control_plane.transaction import (
    TrancheCUnitOfWorkV1, TrancheCAtomicRecordSetV1, TransactionRetryPolicyV1,
    TransactionTerminalStateV1, _native_retail_private_composition_plan_v1)

_F14_COMPLETION_CLASS = 'COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY'
_F14_PROOF_ROLES = {'publication': 'provider_publication_time_utc_or_none',
    'revision': 'revision_effective_time_utc_or_none', 'finality': 'settlement_finality_time_utc_or_none'}


def _f14_allocation_v1(scope, attempt, roles):
    refs = dict(raw=attempt + ':raw', transport=attempt + ':transport',
        publication_intent=attempt + ':intent', capture_commit=attempt + ':capture',
        publication=attempt + ':publication', companion=attempt + ':companion', companion_commit=attempt + ':seal',
        clock_proofs=tuple(attempt + ':proof:' + role for role in roles))
    controls = {phase: dict(unit_of_work_id=attempt + ':' + phase + ':uow',
        claim_ref=attempt + ':' + phase + ':claim', result_binding_ref=attempt + ':' + phase + ':claim::RESULT',
        transition_ref=attempt + ':' + phase + ':transition') for phase in ('A', 'B', 'C')}
    return PrivateEvidenceReadRequestV1(dict(scope), refs, controls)


def _f14_spine_v1(record_id, payload, scope, time_text, attempt):
    floor = _f14_native_time_v1(time_text)[1]
    return EconomicReceiptEventSpineV1(record_id=record_id,
        record_type=EconomicRecordTypeV1.PRIVATE_OBSERVATION_CLOCK if type(payload) is PrivateObservationClockReceiptV1
            else EconomicRecordTypeV1.PRIVATE_EVIDENCE_WITNESS,
        schema_version='1', semantic_owner='PRIVATE_EVIDENCE_CONFORMANCE',
        implementation_owner='PRIVATE_STATE_RECEIPTS', context_ref=scope['source_context_ref'],
        effective_at=floor, recorded_at=floor, causation_id=attempt + ':cause', correlation_id=attempt + ':correlation',
        traceparent=attempt + ':trace', tracestate=attempt + ':trace-state', sequence=0,
        aggregate_id=scope['ledger_account_ref'], aggregate_version=0,
        authority_class='PRIVATE_EVIDENCE_CONFORMANCE_ONLY', typed_payload=payload, no_effect_flags=NO_EFFECTS_V1)


def _f14_phase_records_v1(phase, read_request, records, intent, metadata_clock, attempt):
    refs, control = read_request.record_refs, read_request.phase_control_refs[phase]
    floor = _f14_native_time_v1(metadata_clock['observed_at'])[1]
    transition = StateTransitionReceiptV1(control['transition_ref'], control['unit_of_work_id'],
        'UNIT_OF_WORK_STATE_MACHINE_V1', 'COMMITTING', 'COMMIT_PHASE', 'COMMITTED',
        TransitionDispositionV1.ACCEPTED, attempt + ':' + phase + ':event', 0, 1,
        floor, floor, 'COMMITTED', False)
    # Serialization is the existing owner's canonical request, retaining all rows.
    text = deterministic_json(dict(phase=phase, scope=dict(read_request.scope), receipt_records=records,
        publication_intent_or_none=intent, state_transition=transition))
    shapes = _f14_phase_shapes_v1(len(refs['clock_proofs']))[phase]
    _f14_load_canonical_v1(text, shapes['request'])
    claim = IdempotencyClaimReceiptV1(control['claim_ref'], attempt + ':' + phase + ':key',
        'PRIVATE_EVIDENCE_PHASE_REFERENCE_ONLY', text, IdempotencyClaimStateV1.ACQUIRED,
        None, floor, None, None)
    _f14_load_canonical_v1(deterministic_json(claim), shapes['claim'])
    result_ref = refs[{'A': 'raw', 'B': 'companion', 'C': 'companion_commit'}[phase]]
    return TrancheCAtomicRecordSetV1(claim, tuple(records), (), (), None, (), transition,
        result_ref, optional_outbox_intent=intent), floor


def _f14_execute_phase_v1(phase, *, request, read_request, adapter, source_registry, records, intent, attempt):
    with source_registry.fenced(request.grant, request.operation):
        clock = source_registry._observe_v1(request.grant)
        record_set, metadata = _f14_phase_records_v1(phase, read_request, records, intent, clock, attempt)
        unit = TrancheCUnitOfWorkV1(adapter,
            TransactionRetryPolicyV1(max_transaction_attempts=1, retryable_classes=frozenset()))
        result = unit.execute(unit_of_work_id=read_request.phase_control_refs[phase]['unit_of_work_id'],
            records=record_set, accounts={}, started_at=metadata, completed_at=metadata)
        expected = tuple(record.record_id for record in records) + (record_set.state_transition.transition_id,)
        if intent is not None:
            expected += (intent.outbox_intent_id,)
        if result.transaction_state is not TransactionTerminalStateV1.COMMITTED or result.committed_record_refs != expected:
            raise TransactionContractError(ReasonCode.RECONCILIATION_REQUIRED, 'F14_PHASE_REQUIRES_COMMITTED_READBACK')
        # This is an actual post-return observation, never execute metadata.
        return source_registry._observe_v1(request.grant)


def _f14_commit_witness_v1(rid, scope, members, clock):
    return dict(record_id=rid, scope=dict(scope), committed_record_refs=list(members),
        evidence_class=_F14_COMPLETION_CLASS, completed_at=clock['observed_at'],
        completed_monotonic_ns=clock['monotonic_ns'], process_epoch_id=clock['process_epoch_id'],
        monotonic_clock_id=clock['monotonic_clock_id'])


def _f14_plan_v1(snapshot, read_clock, request, read_request, observations, publication_state,
        intent, source_registry):
    refs = _f14_plain_v1(read_request.record_refs)
    semantic_ids = {value for key, value in refs.items() if key != 'clock_proofs'} | set(refs['clock_proofs'])
    observed = {name: None if value is None else dict(observed_at=value['observed_at'],
        monotonic_ns=value['monotonic_ns']) for name, value in observations.items()}
    source = request.grant.session_binding
    state = dict(source_snapshot_ref=source.source_snapshot_ref, revocation_epoch=source.revocation_epoch,
        process_epoch_id=request.grant.process_epoch_id, monotonic_clock_id=request.grant.monotonic_clock_id,
        storage_state='COMMITTED_SNAPSHOT', committed_record_refs=sorted(snapshot.present_record_refs & semantic_ids),
        observations=observed, snapshot_observed_at=read_clock['observed_at'],
        snapshot_monotonic_ns=read_clock['monotonic_ns'], publication_state=publication_state)
    return _native_retail_private_composition_plan_v1(dict(source.scope), refs, state,
        _f14_load_canonical_v1(deterministic_json(intent), _f14_phase_shapes_v1(len(refs['clock_proofs']))['A']['publication_intent']),
        expected_scope=dict(source.scope), current_source_snapshot_ref=source.source_snapshot_ref,
        current_revocation_epoch=source.revocation_epoch, process_epoch_id=request.grant.process_epoch_id,
        monotonic_clock_id=request.grant.monotonic_clock_id, recorded_cutoff=read_clock['observed_at'],
        source_snapshot_after_ref=source.source_snapshot_ref, revocation_epoch_after=source.revocation_epoch)


def run_retail_private_observation_once_v1(request: RetailPrivateReadRequestV1, *,
        ingress: RetailPrivateIngressV1, source_registry: RetailPrivateSourceRegistryV1,
        adapter: PersistenceAdapterV1, publisher: PrivateObservationPublisherV1) -> Mapping[str, object]:
    _f14_ingress_require_v1(type(request) is RetailPrivateReadRequestV1
        and type(ingress) is RetailPrivateIngressV1 and type(source_registry) is RetailPrivateSourceRegistryV1
        and type(publisher) is PrivateObservationPublisherV1
        and type(adapter) in (InMemoryPersistenceAdapterV1, SQLiteReferenceAdapterV1)
        and ingress.source_registry is source_registry and publisher.source_registry is source_registry,
        'F14_INGRESS_OWNER_ASSOCIATION')
    _f14_ingress_require_v1(adapter.availability is PersistenceAvailabilityV1.AVAILABLE_REFERENCE,
        'F14_INGRESS_STORAGE_UNAVAILABLE')
    with source_registry.fenced(request.grant, request.operation):
        ingress._validate_request_v1(request)
        with publisher._lock:
            old = publisher._requests.get(id(request))
            if old is not None:
                _f14_ingress_require_v1(old[0] is request and old[1] is not None,
                    'F14_INGRESS_ATTEMPT_OUTCOME_UNKNOWN')
                return _f14_freeze_v1(_f14_plain_v1(old[1]))
            key = (request.grant.grant_id, request.consumer['request_ref'],
                type(request.consumer['item_key']), request.consumer['item_key'])
            _f14_ingress_require_v1(key in source_registry._clock_facts, 'F14_INGRESS_CLOCK_FACT')
            facts = source_registry._clock_facts[key]
            required = {'publication': request.requirements['requires_provider_publication_time']
                    or request.requirements['provider_publication_time_is_source_proven'],
                'revision': request.requirements['requires_revision_at_decision'],
                'finality': request.requirements['requires_finality_at_decision']}
            roles = tuple(role for role in _F14_PROOF_ROLES if required[role])
            _f14_ingress_require_v1(all(role in facts for role in roles), 'F14_INGRESS_CLOCK_FACT')
            publisher._requests[id(request)] = (request, None)
    read_request = intent = observed = None
    observations = dict(capture_commit=None, publication=None, companion_commit=None)
    try:
        observed = (ingress.read_private_message_once(request) if request.operation.startswith('WS_')
            else ingress.read_rest_once(request))
        attempt = source_registry._consume_capture_v1(observed, ingress, request)
        session = request.grant.session_binding
        read_request = _f14_allocation_v1(session.scope, attempt, roles)
        refs, scope = read_request.record_refs, dict(session.scope)
        with source_registry.fenced(request.grant, request.operation):
            source_registry._source_witness_v1(request.grant)
            pointer, provider_time = _f14_selected_native_v1(observed.raw_body, request)
            _f14_ingress_require_v1(not request.requirements['requires_provider_event_time']
                or provider_time is not None, 'F14_INGRESS_CLOCK_MISSING')
            issued = source_registry._observe_v1(request.grant)
            raw_payload = _f14_witness_v1(refs['raw'], 'RAW', dict(scope=scope,
                raw_body_utf8=observed.raw_body.decode('utf-8', 'strict')))
            raw_record = _f14_spine_v1(refs['raw'], raw_payload, scope, issued['observed_at'], attempt)
            received, parsed = observed.received_clock, observed.parsed_clock
            transport = dict(record_id=refs['transport'], scope=scope, raw_record_ref=refs['raw'],
                source_binding_ref=scope['source_binding_ref'], source_snapshot_ref=session.source_snapshot_ref,
                revocation_epoch=session.revocation_epoch, operation=request.operation,
                request_ref=request.consumer['request_ref'], credential_binding_ref=session.credential_binding_ref,
                endpoint=('wss' if request.operation.startswith('WS_') else 'https') + '://api.polymarket.us'
                    + _F14_ROUTES[request.operation], method='GET', response_status=observed.response_status,
                tls_peer_verified=True, request_authentication_verified=True, session_ref=session.session_ref,
                response_received=True, received_at=received['observed_at'], received_monotonic_ns=received['monotonic_ns'],
                parse_completed_at=parsed['observed_at'], parse_completed_monotonic_ns=parsed['monotonic_ns'],
                process_epoch_id=request.grant.process_epoch_id, monotonic_clock_id=request.grant.monotonic_clock_id)
            storage_transport = _native_retail_transport_storage_projection_v1(transport,
                expected_binding_ref=session.credential_binding_ref)
            transport_record = _f14_spine_v1(refs['transport'], _f14_witness_v1(refs['transport'],
                'TRANSPORT', storage_transport), scope, parsed['observed_at'], attempt)
            intent = OutboxIntentRecordV1(refs['publication_intent'], 'PRIVATE_OBSERVATION_REFERENCE_PUBLICATION',
                scope['ledger_account_ref'], refs['raw'], _f14_native_time_v1(issued['observed_at'])[1],
                OutboxDispatchStateV1.RECORDED_NOT_DISPATCHABLE, 0, None, 'NO_WRITE_CONTRACT_ONLY')
        observations['capture_commit'] = _f14_execute_phase_v1('A', request=request, read_request=read_request,
            adapter=adapter, source_registry=source_registry, records=(raw_record, transport_record),
            intent=intent, attempt=attempt)
        observations['publication'] = publisher.publish_private_reference_v1(observed, refs['raw'], refs['capture_commit'])
        with source_registry.fenced(request.grant, request.operation):
            published = observations['publication']
            capture = _f14_commit_witness_v1(refs['capture_commit'], scope,
                (refs['raw'], refs['transport'], refs['publication_intent'],
                 *(v for k, v in read_request.phase_control_refs['A'].items() if k != 'unit_of_work_id')),
                observations['capture_commit'])
            publication = dict(record_id=refs['publication'], scope=scope, raw_record_ref=refs['raw'],
                capture_commit_ref=refs['capture_commit'], source_snapshot_ref=session.source_snapshot_ref,
                revocation_epoch=session.revocation_epoch, published_at=published['observed_at'],
                published_monotonic_ns=published['monotonic_ns'], process_epoch_id=request.grant.process_epoch_id,
                monotonic_clock_id=request.grant.monotonic_clock_id)
            proof_bodies = {role: dict(record_id=rid, scope=scope, subject_raw_record_ref=refs['raw'],
                source_binding_ref=facts[role]['source_binding_ref'], value=facts[role]['timestamp'])
                for role, rid in zip(roles, refs['clock_proofs'], strict=True)}
            proof_records = []
            for role, body in proof_bodies.items():
                proof_issued = source_registry._observe_v1(request.grant)
                proof_records.append(_f14_spine_v1(body['record_id'], _f14_witness_v1(body['record_id'],
                    'CLOCK_PROOF', body), scope, proof_issued['observed_at'], attempt))
            clock = source_registry._observe_v1(request.grant)
            clocks = dict(provider_event_time_utc_or_none=provider_time,
                **{field: facts[role]['timestamp'] if role in roles else None for role, field in _F14_PROOF_ROLES.items()},
                qtt_received_at_utc=received['observed_at'], qtt_parse_completed_at_utc=parsed['observed_at'],
                durable_commit_completed_at_utc=capture['completed_at'], strategy_available_at_utc=published['observed_at'],
                qtt_received_monotonic_ns=received['monotonic_ns'], qtt_parse_completed_monotonic_ns=parsed['monotonic_ns'],
                durable_commit_completed_monotonic_ns=capture['completed_monotonic_ns'],
                strategy_available_monotonic_ns=published['monotonic_ns'],
                wall_clock_uncertainty_ns=request.grant.wall_clock_uncertainty_ns,
                process_epoch_id=request.grant.process_epoch_id, monotonic_clock_id=request.grant.monotonic_clock_id,
                wall_clock_source_id=request.grant.wall_clock_source_id,
                clock_quality_receipt_ref=request.grant.clock_quality_receipt_ref)
            companion = dict(schema_version='1', record_id=refs['companion'], scope=scope, raw_record_ref=refs['raw'],
                raw_body_utf8=observed.raw_body.decode('utf-8', 'strict'), raw_byte_limit=request.maximum_raw_bytes,
                provider_event_pointer_or_none=pointer, clock_proof_refs={field: proof_bodies[role]['record_id']
                    if role in roles else None for role, field in _F14_PROOF_ROLES.items()}, clocks=clocks,
                capture_commit_ref=refs['capture_commit'], publication_witness_ref=refs['publication'],
                commit_evidence_class=_F14_COMPLETION_CLASS, issued_at=clock['observed_at'],
                issued_monotonic_ns=clock['monotonic_ns'])
            b_records = (_f14_spine_v1(refs['capture_commit'], _f14_witness_v1(refs['capture_commit'],
                'CAPTURE_COMMIT', capture), scope, capture['completed_at'], attempt),
                _f14_spine_v1(refs['publication'], _f14_witness_v1(refs['publication'], 'PUBLICATION', publication),
                    scope, published['observed_at'], attempt),
                _f14_spine_v1(refs['companion'], PrivateObservationClockReceiptV1(refs['companion'],
                    _f14_dumps_v1(companion)), scope, clock['observed_at'], attempt), *proof_records)
        observations['companion_commit'] = _f14_execute_phase_v1('B', request=request, read_request=read_request,
            adapter=adapter, source_registry=source_registry, records=b_records, intent=None, attempt=attempt)
        with source_registry.fenced(request.grant, request.operation):
            seal = _f14_commit_witness_v1(refs['companion_commit'], scope,
                (*tuple(record.record_id for record in b_records),
                 *(v for k, v in read_request.phase_control_refs['B'].items() if k != 'unit_of_work_id')),
                observations['companion_commit'])
            seal_record = _f14_spine_v1(refs['companion_commit'], _f14_witness_v1(refs['companion_commit'],
                'COMPANION_COMMIT', seal), scope, seal['completed_at'], attempt)
        _f14_execute_phase_v1('C', request=request, read_request=read_request,
            adapter=adapter, source_registry=source_registry, records=(seal_record,), intent=None, attempt=attempt)
        with source_registry.fenced(request.grant, request.operation):
            snapshot = adapter.load_committed_private_evidence_snapshot_v1(read_request)
            completed = source_registry._observe_v1(request.grant)
            source = source_registry._source_witness_v1(request.grant)
            plan = _f14_plan_v1(snapshot, completed, request, read_request, observations, 'OBSERVED',
                intent, source_registry)
            _f14_ingress_require_v1(plan['action'] == 'VALIDATE_EXISTING_EVIDENCE_JOIN_AND_REPLAY',
                'F14_INGRESS_COMPOSITION_HOLD')
            bodies = {}
            for rid, record in snapshot.records_by_ref.items():
                phase = getattr(record.typed_payload, 'phase', None)
                bodies[rid] = _f14_load_canonical_v1(record.typed_payload.canonical_payload_json,
                    _F14_CLOCK_BODY if phase is None else _F14_PHASES[phase])
            witnesses = dict(source=source,
                transport=_native_retail_transport_storage_projection_v1(bodies[refs['transport']],
                    expected_binding_ref=session.credential_binding_ref, restore=True),
                capture_commit=bodies[refs['capture_commit']], publication=bodies[refs['publication']],
                companion_commit=bodies[refs['companion_commit']],
                clock_proofs={_F14_PROOF_ROLES[role]: bodies[rid]
                    for role, rid in zip(roles, refs['clock_proofs'], strict=True)})
            observation = _native_retail_private_evidence_join_v1(bodies[refs['companion']], witnesses,
                _f14_plain_v1(request.consumer), expected_record_id=refs['companion'], expected_scope=scope,
                expected_source_snapshot_ref=session.source_snapshot_ref,
                expected_credential_binding_ref=session.credential_binding_ref, expected_session_ref=session.session_ref,
                expected_revocation_epoch=session.revocation_epoch, requirements=_f14_plain_v1(request.requirements),
                decision_time=completed['observed_at'], recorded_cutoff=completed['observed_at'],
                original_raw_body=bodies[refs['raw']]['raw_body_utf8'].encode('utf-8'))
            publisher._bind_resolution_v1(observed, snapshot, observation,
                completed['observed_at'], completed['observed_at'])
            result = publisher.resolve_committed_private_observation_v1(snapshot, observation, session,
                completed['observed_at'], completed['observed_at'])
            with publisher._lock:
                publisher._requests[id(request)] = (request, result)
            return result
    except Exception as exc:
        if read_request is not None and intent is not None:
            try:
                with source_registry.fenced(request.grant, request.operation):
                    snapshot = adapter.load_committed_private_evidence_snapshot_v1(read_request)
                    completed = source_registry._observe_v1(request.grant)
                    key = (request.grant.session_binding.source_snapshot_ref, attempt)
                    with publisher._lock:
                        slot = publisher._slots.get(key)
                        state = ('NOT_ATTEMPTED' if slot is None else 'OBSERVED'
                            if slot['state'] in ('PENDING', 'RESOLVED') and slot['published_clock'] is not None
                            else 'OUTCOME_UNKNOWN')
                        if state == 'OBSERVED':
                            observations['publication'] = slot['published_clock']
                    plan = _f14_plan_v1(snapshot, completed, request, read_request, observations, state,
                        intent, source_registry)
            except Exception as read_error:
                raise TransactionContractError(ReasonCode.RECONCILIATION_REQUIRED,
                    'F14_READBACK_UNAVAILABLE_OR_CONFLICT_NO_RESUBMISSION') from read_error
            raise TransactionContractError(ReasonCode.RECONCILIATION_REQUIRED, plan['action']) from exc
        if isinstance(exc, ComputationControlPlaneError):
            raise
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_INGRESS_NATIVE_FAILURE') from exc
    finally:
        ingress._finish_attempt_v1()
