"""Atomic Tranche-C unit of work across typed semantic and persistence owners."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Mapping

from .accounting import AccountingAndTCAServiceV1, JournalAccountV1, JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import parse_utc
from .errors import ComputationControlPlaneError, ContractValidationError, PersistenceContractError, ReasonCode, TransactionContractError
from .idempotency import IdempotencyClaimReceiptV1, IdempotencyOutcomeV1
from .lifecycle import StateTransitionReceiptV1
from .outbox import OutboxIntentRecordV1
from .persistence import PersistenceAdapterV1, PersistenceAvailabilityV1, PersistenceTransactionV1
from .receipts import EconomicEventRecordV1, EconomicReceiptEventSpineV1, ValueLineageEdgeV1, validate_lineage_acyclic_v1
from .rollback import (
    JournalReversalBundleV1,
    ReversalReceiptV1,
    validate_reversal_bundle_against_history_v1,
)


class TransactionTerminalStateV1(StrEnum):
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    CONFLICT = "CONFLICT"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class TransactionRetryPolicyV1:
    max_transaction_attempts: int
    retryable_classes: frozenset[str] = frozenset({"REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT"})

    def __post_init__(self) -> None:
        if isinstance(self.max_transaction_attempts, bool) or not isinstance(self.max_transaction_attempts, int) or self.max_transaction_attempts < 1:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "explicit positive max_transaction_attempts is required")
        if not isinstance(self.retryable_classes, frozenset) or any(not value for value in self.retryable_classes):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "retryable_classes must be explicit")


@dataclass(frozen=True, slots=True)
class TransactionCommitReceiptV1:
    unit_of_work_id: str
    transaction_state: TransactionTerminalStateV1
    attempt_count: int
    committed_record_refs: tuple[str, ...]
    idempotency_claim_ref: str
    started_at: datetime | str
    completed_at: datetime | str
    failure_code: str | None
    retryable: bool

    def __post_init__(self) -> None:
        for name in ("unit_of_work_id", "idempotency_claim_ref"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
        if not isinstance(self.transaction_state, TransactionTerminalStateV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "transaction_state must be terminal and typed")
        if isinstance(self.attempt_count, bool) or not isinstance(self.attempt_count, int) or self.attempt_count < 1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "attempt_count must be positive")
        if not isinstance(self.committed_record_refs, tuple) or any(not isinstance(ref, str) or not ref for ref in self.committed_record_refs):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "committed_record_refs must be a string tuple")
        if len(self.committed_record_refs) != len(set(self.committed_record_refs)):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "committed_record_refs must be unique")
        if type(self.retryable) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "retryable must be bool")
        started = parse_utc(self.started_at, field_name="started_at")
        completed = parse_utc(self.completed_at, field_name="completed_at")
        if completed < started:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "completed_at precedes started_at")
        if self.transaction_state is TransactionTerminalStateV1.COMMITTED:
            if self.failure_code is not None or not self.committed_record_refs or self.retryable:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "committed receipt has contradictory failure fields")
        elif not self.failure_code or self.committed_record_refs:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "noncommitted receipt requires failure and no committed refs")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "completed_at", completed)


@dataclass(frozen=True, slots=True)
class TrancheCAtomicRecordSetV1:
    idempotency_claim: IdempotencyClaimReceiptV1
    receipt_records: tuple[EconomicReceiptEventSpineV1, ...]
    economic_events: tuple[EconomicEventRecordV1, ...]
    value_lineage_edges: tuple[ValueLineageEdgeV1, ...]
    journal_transaction: JournalTransactionV1 | None
    journal_postings: tuple[JournalPostingV1, ...]
    state_transition: StateTransitionReceiptV1
    result_record_ref: str
    optional_outbox_intent: OutboxIntentRecordV1 | None = None
    reversal_links: tuple[ReversalReceiptV1, ...] = ()
    reconciliation_breaks: tuple[ReconciliationBreakReceiptV1, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.idempotency_claim, IdempotencyClaimReceiptV1) or self.idempotency_claim.claim_state.value != "ACQUIRED":
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "atomic record set requires a newly ACQUIRED idempotency claim")
        if not self.receipt_records and not self.economic_events:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "atomic record set requires at least one receipt or economic event")
        for name, rows, expected in (
            ("receipt_records", self.receipt_records, EconomicReceiptEventSpineV1),
            ("economic_events", self.economic_events, EconomicEventRecordV1),
            ("value_lineage_edges", self.value_lineage_edges, ValueLineageEdgeV1),
            ("journal_postings", self.journal_postings, JournalPostingV1),
            ("reversal_links", self.reversal_links, ReversalReceiptV1),
            ("reconciliation_breaks", self.reconciliation_breaks, ReconciliationBreakReceiptV1),
        ):
            if not isinstance(rows, tuple) or any(not isinstance(row, expected) for row in rows):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be a typed tuple")
        if not isinstance(self.state_transition, StateTransitionReceiptV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "one typed legal state transition is required")
        if self.journal_transaction is not None and not isinstance(self.journal_transaction, JournalTransactionV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "journal_transaction must be typed when supplied")
        if not self.result_record_ref:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "result_record_ref is required")
        identity_rows = [
            self.idempotency_claim.claim_id,
            *(record.record_id for record in self.receipt_records),
            *(event.economic_event_id for event in self.economic_events),
            *(edge.lineage_edge_id for edge in self.value_lineage_edges),
            *(posting.posting_id for posting in self.journal_postings),
            self.state_transition.transition_id,
            *(row.reversal_receipt_id for row in self.reversal_links),
            *(row.break_receipt_id for row in self.reconciliation_breaks),
        ]
        identities = set(identity_rows)
        event_by_id = {event.economic_event_id: event for event in self.economic_events}
        for record in self.receipt_records:
            if record.record_type.value == "ECONOMIC_EVENT":
                payload = record.typed_payload
                if not isinstance(payload, EconomicEventRecordV1) or event_by_id.get(payload.economic_event_id) != payload:
                    raise ContractValidationError(
                        ReasonCode.INVALID_CONTRACT,
                        "economic-event spine payload must close to the exact atomic economic event",
                    )
        if self.journal_transaction is None:
            if self.journal_postings:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "postings require one journal transaction")
            if any(event.event_class not in {"NO_FILL", "PREFLIGHT_BLOCKED", "NO_ECONOMIC_EFFECT"} for event in self.economic_events):
                raise ContractValidationError(ReasonCode.ACCOUNTING_IMBALANCE, "economic-effect events require a journal transaction")
        else:
            identities.add(self.journal_transaction.journal_transaction_id)
            identity_rows.append(self.journal_transaction.journal_transaction_id)
            if len(self.journal_postings) < 2:
                raise ContractValidationError(ReasonCode.ACCOUNTING_IMBALANCE, "journal transaction requires at least two postings")
            if any(event.event_class == "NO_FILL" for event in self.economic_events):
                raise ContractValidationError(ReasonCode.ACCOUNTING_IMBALANCE, "NO_FILL cannot create journal postings")
            event_ids = {event.economic_event_id for event in self.economic_events}
            if set(self.journal_transaction.economic_event_refs) != event_ids:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "journal must reference the atomic economic events exactly")
            if tuple(posting.posting_id for posting in self.journal_postings) != self.journal_transaction.posting_refs:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "journal posting identities do not match")
            if any(posting.source_event_ref not in event_ids for posting in self.journal_postings):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "posting source event is outside the atomic record set")
        if self.optional_outbox_intent is not None:
            if not isinstance(self.optional_outbox_intent, OutboxIntentRecordV1):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "optional outbox intent must be typed")
            if self.optional_outbox_intent.payload_record_ref not in identities:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "outbox payload must reference the atomic record set")
            identities.add(self.optional_outbox_intent.outbox_intent_id)
            identity_rows.append(self.optional_outbox_intent.outbox_intent_id)
        if len(identity_rows) != len(set(identity_rows)):
            raise ContractValidationError(ReasonCode.PERSISTENCE_CONFLICT, "atomic record identities must be globally unique")
        if self.result_record_ref not in identities:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "idempotency result must bind a record in the same atomic set")
        journal_is_reversal = (
            self.journal_transaction is not None
            and self.journal_transaction.reversal_of_transaction_id is not None
        )
        reversal_link_count = len(self.reversal_links)
        if (
            reversal_link_count not in {0, 1}
            or journal_is_reversal != (reversal_link_count == 1)
        ):
            raise ContractValidationError(
                ReasonCode.REVERSAL_INVALID,
                "typed reversal journal and exact reversal link must be bijective",
            )
        if journal_is_reversal:
            assert self.journal_transaction is not None
            reversal_link = self.reversal_links[0]
            if (
                reversal_link.original_event_or_transaction_ref
                != self.journal_transaction.reversal_of_transaction_id
                or reversal_link.reversal_transaction_ref
                != self.journal_transaction.journal_transaction_id
                or reversal_link.reversal_event_ref
                not in self.journal_transaction.economic_event_refs
            ):
                raise ContractValidationError(
                    ReasonCode.REVERSAL_INVALID,
                    "reversal link does not close to its exact atomic reversal journal",
                )
        validate_lineage_acyclic_v1(self.value_lineage_edges)


class TrancheCUnitOfWorkV1:
    """Compose writes only; economic meaning remains with accounting/lifecycle owners."""

    def __init__(self, adapter: PersistenceAdapterV1, retry_policy: TransactionRetryPolicyV1) -> None:
        if not isinstance(adapter, PersistenceAdapterV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed PersistenceAdapterV1 is required")
        if adapter.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "durable operation requires available reference persistence")
        if not isinstance(retry_policy, TransactionRetryPolicyV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed transaction retry policy is required")
        adapter_attempts = getattr(adapter, "max_transaction_attempts", retry_policy.max_transaction_attempts)
        if adapter_attempts != retry_policy.max_transaction_attempts:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "adapter and unit-of-work retry limits must match")
        self._adapter = adapter
        self._retry_policy = retry_policy

    @staticmethod
    def _receipt(
        *, unit_of_work_id: str, state: TransactionTerminalStateV1, attempt: int,
        refs: tuple[str, ...], claim_ref: str, started_at: datetime | str,
        completed_at: datetime | str, failure_code: str | None, retryable: bool,
    ) -> TransactionCommitReceiptV1:
        return TransactionCommitReceiptV1(unit_of_work_id, state, attempt, refs, claim_ref, started_at, completed_at, failure_code, retryable)

    def execute(
        self,
        *,
        unit_of_work_id: str,
        records: TrancheCAtomicRecordSetV1,
        accounts: Mapping[str, JournalAccountV1],
        started_at: datetime | str,
        completed_at: datetime | str,
    ) -> TransactionCommitReceiptV1:
        refs = (
            *(record.record_id for record in records.receipt_records),
            *(event.economic_event_id for event in records.economic_events),
            *(edge.lineage_edge_id for edge in records.value_lineage_edges),
            *((records.journal_transaction.journal_transaction_id,) if records.journal_transaction else ()),
            *(posting.posting_id for posting in records.journal_postings),
            records.state_transition.transition_id,
            *((records.optional_outbox_intent.outbox_intent_id,) if records.optional_outbox_intent else ()),
            *(row.reversal_receipt_id for row in records.reversal_links),
            *(row.break_receipt_id for row in records.reconciliation_breaks),
        )
        # Local validation only: this prospective object is never emitted as evidence.
        prospective = self._receipt(
            unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.COMMITTED,
            attempt=1, refs=refs, claim_ref=records.idempotency_claim.claim_id,
            started_at=started_at, completed_at=completed_at, failure_code=None, retryable=False,
        )
        started_at, completed_at = prospective.started_at, prospective.completed_at
        for attempt in range(1, self._retry_policy.max_transaction_attempts + 1):
            transaction: PersistenceTransactionV1 | None = None
            try:
                transaction = self._adapter.begin_transaction()
            except PersistenceContractError as exc:
                retryable_begin = exc.reason_code.value in self._retry_policy.retryable_classes
                if retryable_begin and attempt < self._retry_policy.max_transaction_attempts:
                    continue
                return self._receipt(
                    unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.RETRY_EXHAUSTED,
                    attempt=attempt, refs=(), claim_ref=records.idempotency_claim.claim_id,
                    started_at=started_at, completed_at=completed_at,
                    failure_code=(ReasonCode.TRANSACTION_RETRY_EXHAUSTED.value if retryable_begin else exc.reason_code.value), retryable=False,
                )
            phase = "precommit"

            def rollback_owned() -> None:
                nonlocal phase
                phase = "rollback_attempted"
                transaction.rollback()
                if transaction.is_active:
                    raise TransactionContractError(
                        ReasonCode.TRANSACTION_STATE_INVALID,
                        "owned rollback returned with an active transaction",
                    )
                phase = "rollback_returned"

            try:
                claim = self._adapter.acquire_idempotency_claim(transaction, records.idempotency_claim)
                if claim.outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD:
                    result = self._receipt(
                        unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.COMMITTED,
                        attempt=attempt, refs=(claim.original_result_ref,), claim_ref=claim.claim_ref,
                        started_at=started_at, completed_at=completed_at, failure_code=None, retryable=False,
                    )
                    rollback_owned()
                    return result
                if claim.outcome in {IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD, IdempotencyOutcomeV1.IN_PROGRESS}:
                    reason = ReasonCode.IDEMPOTENCY_CONFLICT if claim.outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD else ReasonCode.IDEMPOTENCY_IN_PROGRESS
                    result = self._receipt(
                        unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.CONFLICT,
                        attempt=attempt, refs=(), claim_ref=claim.claim_ref, started_at=started_at,
                        completed_at=completed_at, failure_code=reason.value, retryable=False,
                    )
                    rollback_owned()
                    return result
                original_reversal_ref = (
                    records.journal_transaction.reversal_of_transaction_id
                    if records.journal_transaction is not None
                    else None
                )
                if original_reversal_ref is not None:
                    if len(records.reversal_links) != 1:
                        raise ContractValidationError(
                            ReasonCode.REVERSAL_INVALID,
                            "typed reversal journal requires exactly one reversal link",
                        )
                    reversal = records.reversal_links[0]
                    if (
                        reversal.original_event_or_transaction_ref
                        != original_reversal_ref
                        or reversal.reversal_transaction_ref
                        != records.journal_transaction.journal_transaction_id
                        or reversal.reversal_event_ref
                        not in records.journal_transaction.economic_event_refs
                    ):
                        raise ContractValidationError(
                            ReasonCode.REVERSAL_INVALID,
                            "reversal admission does not close to the typed journal",
                        )
                    history = self._adapter.load_committed_reversal_history(
                        transaction,
                        original_reversal_ref,
                    )
                    validate_reversal_bundle_against_history_v1(
                        history=history,
                        proposed=JournalReversalBundleV1(
                            records.journal_transaction,
                            records.journal_postings,
                            reversal,
                        ),
                    )
                elif records.reversal_links:
                    raise ContractValidationError(
                        ReasonCode.REVERSAL_INVALID,
                        "reversal link cannot exist without a typed reversal journal",
                    )
                if records.journal_transaction is not None:
                    AccountingAndTCAServiceV1.validate_journal(records.journal_transaction, records.journal_postings, accounts)
                for record in records.receipt_records:
                    self._adapter.insert_receipt_record(transaction, record)
                for event in records.economic_events:
                    self._adapter.insert_economic_event(transaction, event)
                for edge in records.value_lineage_edges:
                    self._adapter.insert_value_lineage_edge(transaction, edge)
                if records.journal_transaction is not None:
                    self._adapter.insert_journal_transaction(transaction, records.journal_transaction)
                    for posting in records.journal_postings:
                        self._adapter.insert_journal_posting(transaction, posting)
                self._adapter.insert_state_transition(transaction, records.state_transition)
                if records.optional_outbox_intent is not None:
                    self._adapter.insert_outbox_intent(transaction, records.optional_outbox_intent)
                for reversal in records.reversal_links:
                    self._adapter.insert_reversal_link(transaction, reversal)
                for reconciliation_break in records.reconciliation_breaks:
                    self._adapter.insert_reconciliation_break(transaction, reconciliation_break)
                self._adapter.bind_idempotency_result(transaction, claim.claim_ref, records.result_record_ref, parse_utc(completed_at, field_name="completed_at"))
                result = self._receipt(
                    unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.COMMITTED,
                    attempt=attempt, refs=refs, claim_ref=claim.claim_ref,
                    started_at=started_at, completed_at=completed_at, failure_code=None, retryable=False,
                )
                phase = "commit_attempted"
                transaction.commit()
                phase = "commit_returned"
                return result
            except Exception as exc:
                # Inactivity alone says nothing about whether this operation rolled back.
                # Failed/finished explicit cleanup must never be attempted a second time.
                if phase in {"rollback_attempted", "rollback_returned"} or not transaction.is_active:
                    raise
                commit_attempted = phase in {"commit_attempted", "commit_returned"}
                try:
                    rollback_owned()
                except Exception as cleanup_error:
                    raise cleanup_error from exc
                if commit_attempted or not isinstance(exc, ComputationControlPlaneError):
                    raise
                return self._receipt(
                    unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.ROLLED_BACK,
                    attempt=attempt, refs=(), claim_ref=records.idempotency_claim.claim_id,
                    started_at=started_at, completed_at=completed_at,
                    failure_code=exc.reason_code.value, retryable=False,
                )
        raise AssertionError("bounded retry loop must terminate")


# F14 pure recovery/composition law; no independent transaction implementation.
import copy
from .context import _native_require, _native_obj, _native_ident, _native_utc_nanoseconds
from .serialization import _native_retail_strict_equal_v1, _f14_require_v1


def _native_retail_private_recovery_plan_v1(scope, record_refs, snapshot, *, expected_scope, current_source_snapshot_ref, current_revocation_epoch, process_epoch_id, monotonic_clock_id, recorded_cutoff):
    """Derive the next bounded issuance step from an owner-supplied read snapshot.

    This pure reference neither reads storage nor authenticates its input. The
    existing storage/source/connector owners must construct the snapshot after
    trusted readback. Returned actions are plans, never capabilities or effects.
    """
    scope_fields = ('profile', 'ledger_account_ref', 'source_binding_ref', 'source_context_ref', 'capture_epoch_ref', 'partition_ref')
    _native_obj(scope, scope_fields)
    _native_obj(expected_scope, scope_fields)

    def text(value):
        _native_require(type(value) is str, 'PRIVATE_ISSUANCE_TEXT')
        return _native_ident(value)

    def integer(value):
        _native_require(type(value) is int and 0 <= value <= 2 ** 63 - 1, 'PRIVATE_ISSUANCE_INTEGER')
        return value
    for item in (scope, expected_scope):
        for value in item.values():
            text(value)
    _native_require(_native_retail_strict_equal_v1(scope, expected_scope) and scope['profile'] == 'POLYMARKET_US_RETAIL_DIRECT', 'PRIVATE_ISSUANCE_SCOPE')
    phases = ('raw', 'transport', 'capture_commit', 'publication', 'companion', 'companion_commit')
    _native_obj(record_refs, phases + ('clock_proofs',))
    for phase in phases:
        text(record_refs[phase])
    proofs = record_refs['clock_proofs']
    _native_require(type(proofs) is list and len(proofs) <= 3, 'PRIVATE_ISSUANCE_PROOFS')
    for value in proofs:
        text(value)
    ids = [record_refs[k] for k in phases] + proofs
    _native_require(len(ids) == len(set(ids)), 'PRIVATE_ISSUANCE_REFERENCE_ALIAS')
    _native_obj(snapshot, ('source_snapshot_ref', 'revocation_epoch', 'process_epoch_id', 'monotonic_clock_id', 'storage_state', 'committed_record_refs', 'observations', 'snapshot_observed_at', 'snapshot_monotonic_ns', 'publication_state'))
    for key in ('source_snapshot_ref', 'process_epoch_id', 'monotonic_clock_id'):
        text(snapshot[key])
    text(current_source_snapshot_ref)
    text(process_epoch_id)
    text(monotonic_clock_id)
    integer(current_revocation_epoch)
    integer(snapshot['revocation_epoch'])
    now = integer(snapshot['snapshot_monotonic_ns'])
    visible_at = _native_utc_nanoseconds(snapshot['snapshot_observed_at'])
    cutoff = _native_utc_nanoseconds(recorded_cutoff)
    state = snapshot['storage_state']
    _native_require(type(state) is str and state in ('ACTIVE_TRANSACTION', 'OUTCOME_UNKNOWN', 'READBACK_UNAVAILABLE', 'READBACK_CONFLICT', 'COMMITTED_SNAPSHOT'), 'PRIVATE_ISSUANCE_STORAGE_STATE')
    refs = snapshot['committed_record_refs']
    _native_require(type(refs) is list and len(refs) <= 9, 'PRIVATE_ISSUANCE_RECORD_SET')
    for value in refs:
        text(value)
    _native_require(len(refs) == len(set(refs)) and set(refs) <= set(ids), 'PRIVATE_ISSUANCE_RECORD_SET')
    publication_state = snapshot['publication_state']
    _native_require(type(publication_state) is str and publication_state in ('NOT_ATTEMPTED', 'OUTCOME_UNKNOWN', 'OBSERVED'), 'PRIVATE_ISSUANCE_PUBLICATION_STATE')
    obs = snapshot['observations']
    _native_obj(obs, ('capture_commit', 'publication', 'companion_commit'))
    times = []
    for phase in ('capture_commit', 'publication', 'companion_commit'):
        value = obs[phase]
        if value is None:
            continue
        _native_obj(value, ('observed_at', 'monotonic_ns'))
        _native_utc_nanoseconds(value['observed_at'])
        n = integer(value['monotonic_ns'])
        _native_require(n <= now, 'PRIVATE_ISSUANCE_OBSERVATION_AFTER_SNAPSHOT')
        times.append(n)
    _native_require(times == sorted(times), 'PRIVATE_ISSUANCE_OBSERVATION_ORDER')
    _native_require(obs['publication'] is None or obs['capture_commit'] is not None, 'PRIVATE_ISSUANCE_OBSERVATION_ORDER')
    _native_require(obs['companion_commit'] is None or obs['publication'] is not None, 'PRIVATE_ISSUANCE_OBSERVATION_ORDER')

    def result(action, stage, planned=()):
        return {'state': 'PRIVATE_ISSUANCE_PLAN_ONLY', 'action': action, 'committed_stage': stage, 'planned_record_refs': list(planned), 'snapshot_bound_ns_text': str(visible_at), 'source_accepted': False, 'witnesses_authenticated': False, 'storage_qualified': False, 'record_written': False, 'publication_performed': False, 'replay_admitted': False, 'posts_cash': False, 'releases_reservation': False, 'runtime_effect_authorized': False}
    blocked = {'ACTIVE_TRANSACTION': 'WAIT_FOR_OWNED_TRANSACTION', 'OUTCOME_UNKNOWN': 'RESOLVE_COMMIT_OUTCOME_NO_RESUBMISSION', 'READBACK_UNAVAILABLE': 'HOLD_STORAGE_UNAVAILABLE', 'READBACK_CONFLICT': 'QUARANTINE_READBACK_CONFLICT'}
    if state in blocked:
        return result(blocked[state], 'UNKNOWN')
    a = {record_refs['raw'], record_refs['transport']}
    b = {record_refs['capture_commit'], record_refs['publication'], record_refs['companion'], *proofs}
    c = {record_refs['companion_commit']}
    observed = set(refs)
    sets = (set(), a, a | b, a | b | c)
    _native_require(observed in sets, 'PRIVATE_ISSUANCE_ATOMIC_PREFIX')
    stage = sets.index(observed)
    _native_require(not (stage == 0 and publication_state != 'NOT_ATTEMPTED') and (not (stage >= 2 and publication_state == 'NOT_ATTEMPTED')), 'PRIVATE_ISSUANCE_PUBLICATION_STATE')
    _native_require(obs['publication'] is None or publication_state == 'OBSERVED', 'PRIVATE_ISSUANCE_PUBLICATION_STATE')
    if visible_at > cutoff:
        return result('HOLD_SNAPSHOT_AFTER_RECORDED_CUTOFF', stage)
    if snapshot['source_snapshot_ref'] != current_source_snapshot_ref or snapshot['revocation_epoch'] != current_revocation_epoch:
        return result('REQUALIFY_SOURCE_NO_PUBLICATION', stage)
    same_domain = snapshot['process_epoch_id'] == process_epoch_id and snapshot['monotonic_clock_id'] == monotonic_clock_id
    if not same_domain:
        return result('HISTORICAL_CHAIN_VALIDATION_ONLY' if stage == 3 else 'RECAPTURE_NEW_EPOCH_NO_BACKDATE', stage)
    if publication_state == 'OUTCOME_UNKNOWN':
        return result('RESOLVE_PUBLICATION_OUTCOME_NO_REPUBLISH', stage)
    if stage == 1 and publication_state == 'OBSERVED':
        _native_require(obs['publication'] is not None, 'PRIVATE_ISSUANCE_PUBLICATION_STATE')
    if stage == 0:
        _native_require(all((value is None for value in obs.values())), 'PRIVATE_ISSUANCE_ORPHAN_OBSERVATION')
        return result('CAPTURE_AUTHORIZED_READ_ONLY_RESPONSE', stage, sorted(a))
    if stage == 1:
        _native_require(obs['companion_commit'] is None, 'PRIVATE_ISSUANCE_ORPHAN_OBSERVATION')
        if obs['capture_commit'] is None:
            return result('OBSERVE_CAPTURE_COMMIT_UPPER_BOUND', stage)
        if obs['publication'] is None:
            return result('PUBLISH_THROUGH_EXISTING_OWNER', stage)
        return result('COMMIT_COMPANION_GROUP', stage, sorted(b))
    if stage == 2:
        if obs['companion_commit'] is None:
            return result('OBSERVE_COMPANION_COMMIT_UPPER_BOUND', stage)
        return result('COMMIT_COMPLETION_WITNESS', stage, sorted(c))
    return result('VALIDATE_EXISTING_EVIDENCE_JOIN_AND_REPLAY', stage)


def _native_retail_private_composition_plan_v1(scope, record_refs, snapshot, publication_intent, *, expected_scope, current_source_snapshot_ref, current_revocation_epoch, process_epoch_id, monotonic_clock_id, recorded_cutoff, source_snapshot_after_ref, revocation_epoch_after):
    """Intent-aware F14-F17 planning; no IO, authenticated inputs or authority.

    Validate the expanded atomic sets BEFORE projecting to the preserved F16
    planner. The additional intent is an existing non-dispatchable outbox row,
    not a seventh private-evidence witness phase. After-read source validation
    is defense in depth; the real implementation must ALSO hold the source
    fence across grouped committed read and reference-slot exposure.
    """
    scope_fields = ('profile', 'ledger_account_ref', 'source_binding_ref', 'source_context_ref', 'capture_epoch_ref', 'partition_ref')
    _native_obj(scope, scope_fields)
    _native_obj(expected_scope, scope_fields)
    _native_obj(record_refs, ('raw', 'transport', 'capture_commit', 'publication', 'companion', 'companion_commit', 'clock_proofs', 'publication_intent'))
    _native_obj(publication_intent, ('outbox_intent_id', 'topic_class', 'aggregate_id', 'payload_record_ref', 'created_at', 'dispatch_state', 'dispatch_attempt_count', 'next_eligible_at', 'authority_class'))

    def exact_id(value):
        _native_require(type(value) is str, 'PRIVATE_COMPOSITION_ID')
        return _native_ident(value)

    def exact_counter(value):
        _native_require(type(value) is int and 0 <= value <= 2 ** 63 - 1, 'PRIVATE_COMPOSITION_COUNTER')
        return value
    intent_ref = exact_id(record_refs['publication_intent'])
    _native_require(exact_id(publication_intent['outbox_intent_id']) == intent_ref, 'PRIVATE_COMPOSITION_INTENT_BINDING')
    _native_require(type(publication_intent['topic_class']) is str and publication_intent['topic_class'] == 'PRIVATE_OBSERVATION_REFERENCE_PUBLICATION', 'PRIVATE_COMPOSITION_INTENT_KIND')
    _native_require(exact_id(publication_intent['payload_record_ref']) == record_refs['raw'] and exact_id(publication_intent['aggregate_id']) == expected_scope.get('ledger_account_ref'), 'PRIVATE_COMPOSITION_INTENT_BINDING')
    _native_utc_nanoseconds(publication_intent['created_at'])
    _native_require(type(publication_intent['dispatch_state']) is str and publication_intent['dispatch_state'] == 'RECORDED_NOT_DISPATCHABLE' and (type(publication_intent['authority_class']) is str) and (publication_intent['authority_class'] == 'NO_WRITE_CONTRACT_ONLY') and (type(publication_intent['dispatch_attempt_count']) is int) and (publication_intent['dispatch_attempt_count'] == 0) and (publication_intent['next_eligible_at'] is None), 'PRIVATE_COMPOSITION_OUTBOX_EFFECT_FORBIDDEN')
    base_refs = copy.deepcopy(record_refs)
    del base_refs['publication_intent']
    _native_require(type(base_refs['clock_proofs']) is list and len(base_refs['clock_proofs']) <= 3, 'PRIVATE_COMPOSITION_PROOFS')
    names = ('raw', 'transport', 'capture_commit', 'publication', 'companion', 'companion_commit')
    identities = [exact_id(base_refs[name]) for name in names]
    identities.extend((exact_id(value) for value in base_refs['clock_proofs']))
    identities.append(intent_ref)
    _native_require(len(identities) == len(set(identities)), 'PRIVATE_COMPOSITION_REFERENCE_ALIAS')
    _native_obj(snapshot, ('source_snapshot_ref', 'revocation_epoch', 'process_epoch_id', 'monotonic_clock_id', 'storage_state', 'committed_record_refs', 'observations', 'snapshot_observed_at', 'snapshot_monotonic_ns', 'publication_state'))
    committed = snapshot['committed_record_refs']
    _native_require(type(committed) is list and len(committed) <= 10, 'PRIVATE_COMPOSITION_RECORD_SET')
    for value in committed:
        exact_id(value)
    _native_require(len(committed) == len(set(committed)) and set(committed) <= set(identities), 'PRIVATE_COMPOSITION_RECORD_SET')
    after_ref = exact_id(source_snapshot_after_ref)
    after_generation = exact_counter(revocation_epoch_after)
    exact_id(current_source_snapshot_ref)
    exact_counter(current_revocation_epoch)
    a = {record_refs['raw'], record_refs['transport'], intent_ref}
    b = {record_refs['capture_commit'], record_refs['publication'], record_refs['companion'], *record_refs['clock_proofs']}
    c = {record_refs['companion_commit']}
    if snapshot['storage_state'] == 'COMMITTED_SNAPSHOT':
        _native_require(set(committed) in (set(), a, a | b, a | b | c), 'PRIVATE_COMPOSITION_ATOMIC_PREFIX')
    projected = copy.deepcopy(snapshot)
    projected['committed_record_refs'] = [value for value in committed if value != intent_ref]
    planned = _native_retail_private_recovery_plan_v1(scope, base_refs, projected, expected_scope=expected_scope, current_source_snapshot_ref=current_source_snapshot_ref, current_revocation_epoch=current_revocation_epoch, process_epoch_id=process_epoch_id, monotonic_clock_id=monotonic_clock_id, recorded_cutoff=recorded_cutoff)
    if snapshot['storage_state'] == 'COMMITTED_SNAPSHOT' and snapshot['publication_state'] == 'OBSERVED':
        present = set(committed)
        if a | b <= present:
            _native_require(snapshot['observations']['capture_commit'] is not None and snapshot['observations']['publication'] is not None, 'PRIVATE_COMPOSITION_OBSERVATION_MEMBERSHIP')
        if a | b | c <= present:
            _native_require(snapshot['observations']['companion_commit'] is not None, 'PRIVATE_COMPOSITION_OBSERVATION_MEMBERSHIP')
    prior_blocks = {'WAIT_FOR_OWNED_TRANSACTION', 'RESOLVE_COMMIT_OUTCOME_NO_RESUBMISSION', 'HOLD_STORAGE_UNAVAILABLE', 'QUARANTINE_READBACK_CONFLICT', 'HOLD_SNAPSHOT_AFTER_RECORDED_CUTOFF'}
    if planned['action'] not in prior_blocks and snapshot['storage_state'] == 'COMMITTED_SNAPSHOT' and (intent_ref in committed):
        created = _native_utc_nanoseconds(publication_intent['created_at'])
        _native_require(created <= _native_utc_nanoseconds(snapshot['snapshot_observed_at']), 'PRIVATE_COMPOSITION_INTENT_TIME')
        capture_observation = snapshot['observations']['capture_commit']
        if capture_observation is not None:
            _native_require(created <= _native_utc_nanoseconds(capture_observation['observed_at']), 'PRIVATE_COMPOSITION_INTENT_TIME')
    if planned['action'] not in prior_blocks and (after_ref != current_source_snapshot_ref or after_generation != current_revocation_epoch):
        planned['action'] = 'REQUALIFY_SOURCE_NO_PUBLICATION'
        planned['planned_record_refs'] = []
    if planned['action'] == 'CAPTURE_AUTHORIZED_READ_ONLY_RESPONSE':
        planned['planned_record_refs'] = sorted(a)
    planned['state'] = 'PRIVATE_COMPOSITION_PLAN_ONLY'
    planned['publication_intent_ref'] = intent_ref
    return planned


def _f14_physical_prefix_v1(proof_count: int, present: frozenset[str]) -> int:
    """Exact semantic AND control membership; never an authentication gate."""
    _f14_require_v1(type(proof_count) is int and 0 <= proof_count <= 3, 'F14_PHYSICAL_PROOFS')
    _f14_require_v1(type(present) is frozenset and all((type(x) is str for x in present)), 'F14_PHYSICAL_SET')
    a = frozenset(('raw', 'transport', 'intent', 'A.claim', 'A.result', 'A.transition'))
    b = frozenset(('capture', 'publication', 'companion', 'B.claim', 'B.result', 'B.transition', *(f'proof{i}' for i in range(proof_count))))
    c = frozenset(('completion', 'C.claim', 'C.result', 'C.transition'))
    stages = (frozenset(), a, a | b, a | b | c)
    _f14_require_v1(present in stages, 'F14_PHYSICAL_PARTIAL_BATCH')
    return stages.index(present)
