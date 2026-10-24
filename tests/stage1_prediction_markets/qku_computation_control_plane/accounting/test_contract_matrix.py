"""Centralized 16-row Tranche-C accounting contract matrix."""

from dataclasses import FrozenInstanceError, fields, replace
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal, Inexact, Rounded, ROUND_CEILING, ROUND_FLOOR, localcontext
from fractions import Fraction
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (
    implementation_registry as implementation_registry_module,
)

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.accounting import (
    AccountingAmountV1,
    AccountingAndTCAServiceV1,
    CASH_STATE_CLASS_REGISTRY,
    CashStateClassV1,
    CashStateProjectionV1,
    CostEmbeddingV1,
    CrossVenueTransferV1,
    EntrySideV1,
    ExposureProjectionV1,
    JournalAccountV1,
    JournalPostingV1,
    JournalTransactionV1,
    NormalBalanceV1,
    PositionEventClassV1,
    PositionEventV1,
    ReconciliationRunV1,
    ReconciliationStateV1,
    TCADecompositionV1,
    project_position_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    QuantizationPolicyV1,
    QuantizationRoundingV1,
    exact_decimal,
    quantize_decimal_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.economic_math import (
    ActivePriceGridRangeV1,
    BinaryBookSnapshotV1,
    FeeScheduleBindingV1,
    FillQuantityDistributionArtifactV1,
    KalshiFeeRoundingInputV1,
    KalshiFeeRoundingResultV1,
    KalshiQuadraticTakerBuyYesFillV1,
    TRANCHE_C_MATH_SPECIFICATIONS,
    binary_book_implied_asks_v1,
    expected_partial_fill_quantity_v1,
    global_prediction_market_fee_v1,
    kalshi_fee_rounding_v1,
    kalshi_quadratic_taker_buy_yes_input_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    NumericDomainError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.idempotency import (
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    canonical_request_json_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.lifecycle import (
    FillAccumulatorV1,
    StateTransitionReceiptV1,
    TransitionDispositionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    InMemoryPersistenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES,
    TRANCHE_C_PARAMETER_APPLICATION_BINDINGS,
    TRANCHE_C_PARAMETER_POLICIES,
    TrancheCDrawdownCalibrationArtifactV1,
    TrancheCParameterEvidenceClassV1,
    TrancheCParameterEvidenceV1,
    TrancheCExplicitParameterValueV1,
    TrancheCParameterPolicyClassV1,
    resolve_tranche_c_parameter_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    TRANCHE_C_IMPLEMENTATION_REGISTRY,
    compute_math_36_kalshi_binary_book_transform,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.outbox import (
    OutboxIntentRecordV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    EconomicEventRecordV1,
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    TypedEconomicAmountV1,
    ValueLineageEdgeV1,
    SourceUseScopeV1, SourceUseOriginalContentV1, SourceUseControlRecordV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.rollback import (
    build_journal_reversal_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import (
    SQLiteReferenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.transaction import (
    TransactionRetryPolicyV1,
    TransactionTerminalStateV1,
    TrancheCAtomicRecordSetV1,
    TrancheCUnitOfWorkV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12C_CONTROL_COVERAGE_MATRIX,
    ST12C_NO_EFFECT_FLAGS,
    ST12C_ORIGINAL_TEST_TO_MATRIX_LOCATOR,
    ST12C_REFERENCE_ADAPTER_MATRIX,
    ST12C_REQUIRED_ASSERTION_CLASSES,
    validate_domain,
    validate_st12c_control_coverage_matrix,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
DYNAMIC_OBSERVED_AT = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
DYNAMIC_EVALUATED_AT = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
DYNAMIC_RESOLUTION_AT = datetime(2026, 1, 1, 0, 2, tzinfo=UTC)
DYNAMIC_VALID_UNTIL = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
ACCOUNTING_CASES = tuple(row for row in ST12C_CONTROL_COVERAGE_MATRIX if row.domain == "accounting")


def _source_use_action_proposals(moment):
    from datetime import timedelta
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
        SourceUseScopeV1, SourceUseOriginalContentV1, SourceUseReviewFactsV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import Stage1VenueProfileIdV1

    scope = SourceUseScopeV1(Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
        "KALSHI_PUBLIC_MARKET_EVENT_SERIES", "KALSHI_PUBLIC_FEE_OBSERVATION_V1",
        "OBSERVED_FEE_SCENARIO_INTERNAL", "PROCESS_MEMORY_ONLY", "NO_REDISTRIBUTION_NO_EXTERNAL_AI_FORWARDING",
        "SYNTHETIC::ACCOUNT")
    facts = SourceUseReviewFactsV1("SYNTHETIC::DOCUMENT", "SYNTHETIC_V1", "SYNTHETIC::AGREEMENT", "SYNTHETIC_V1",
        moment - timedelta(seconds=1), moment - timedelta(seconds=2), moment - timedelta(seconds=2),
        moment + timedelta(minutes=1), ("SYNTHETIC_CHANGE",), ("SYNTHETIC_ONLY_INTERNAL_USE",), ("NO_NATIVE_QUALIFICATION",))
    review = SourceUseOriginalContentV1("Synthetic review only; no actual source or legal acceptance.", None, None,
        "UTC_INSTANT", facts.factual_checked_at_utc.isoformat(), facts.document_ref, facts.document_version,
        facts.source_effective_at_utc, facts.source_expires_at_utc)
    declaration = SourceUseOriginalContentV1("Synthetic owner declaration only.", None, None, "UNKNOWN", None,
        None, None, moment - timedelta(seconds=2), moment + timedelta(minutes=1))
    return scope, review, facts, declaration


def test_source_use_admission_integration(monkeypatch, reference_directory, capsys):
    from datetime import timedelta
    from tests.stage1_prediction_markets.qku_computation_control_plane.security.test_deserialization_safety import _synthetic_source_use_root
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import SourceUseObservationRequestV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
        InMemoryPersistenceAdapterV1, OwnerControlMemoryAdapterV1, PersistenceAvailabilityV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import SQLiteReferenceAdapterV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.transaction import TrancheCUnitOfWorkV1, TransactionRetryPolicyV1

    moment = datetime(2026, 10, 20, 12, tzinfo=UTC)
    seconds = int((moment - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds())
    clock = dict(wall=seconds * 1_000_000_000, mono=10_000_000_000)
    monkeypatch.setattr(source.time, "time_ns", lambda: clock["wall"])
    monkeypatch.setattr(source.time, "monotonic_ns", lambda: clock["mono"])
    scope, review, facts, declaration = _source_use_action_proposals(moment)
    with _synthetic_source_use_root() as h:
        authority = h.authority
        assert type(authority._adapter) is OwnerControlMemoryAdapterV1
        assert authority._adapter.availability is PersistenceAvailabilityV1.AVAILABLE_OWNER_CONTROL_EPHEMERAL
        assert h.controller.read_status_v1()["state"] == "DENIED"
        review_proposal = dict(action="REVIEW_ACCEPT", scope=scope, original=review, review_facts=facts,
                               requested_expires_at_utc=moment + timedelta(minutes=1))
        for invalid in (None,):
            with pytest.raises(ComputationControlPlaneError):
                h.controller.prepare_action_v1(deterministic_json({**review_proposal, "original": invalid}).encode())
        for expires in (moment + timedelta(minutes=2), moment + timedelta(minutes=16)):
            with pytest.raises(ComputationControlPlaneError):
                h.controller.prepare_action_v1(deterministic_json({**review_proposal, "requested_expires_at_utc": expires}).encode())
        first = h.sign(review_proposal)
        assert first.event.typed_payload.generation_before == 0 and first.event.typed_payload.generation_after == 1
        assert first.declaration is None and first.review.typed_payload.content == review
        assert first.review.authority_class == "RECORDED_NOT_AUTHENTICATED_NOT_ADMITTED"
        assert source.read_recorded_source_use_status_v1(adapter=authority._adapter,
            stream_id=first.review.typed_payload.stream_id, evaluated_at_utc=moment).admission_eligible is False
        assert h.controller.read_status_v1()["state"] == "DENIED"
        use_proposal = dict(action="USE_ADMIT", scope=scope, original=declaration,
            expected_review_ref=first.review.record_id, requested_expires_at_utc=moment + timedelta(seconds=55))
        with pytest.raises(ComputationControlPlaneError):
            h.controller.prepare_action_v1(deterministic_json({**use_proposal,
                "requested_expires_at_utc": moment + timedelta(seconds=61)}).encode())
        second = h.sign(use_proposal)
        assert second.event.typed_payload.review_event_ref == first.event.record_id
        assert second.event.typed_payload.generation_after == 2
        assert h.controller.read_status_v1()["state"] == "ACTIVE"
        binding = next(iter(authority._bindings.values()))
        assert binding._permit is None
        assert binding._source.checked_at_utc == facts.factual_checked_at_utc
        assert binding._source.currentization_owner_id == h.enrollment.owner_ref
        assert first.event.record_id in binding._source.receipt_id
        fills = (KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal(".5")),)
        request = SourceUseObservationRequestV1("SYNTHETIC::MARKET", fills, Decimal(".01"), Decimal(0),
                                                moment + timedelta(seconds=50), 50_000_000_000)
        third = h.sign(dict(action="OBSERVE_ONCE", scope=scope, expected_declaration_ref=second.declaration.record_id,
            expected_review_ref=second.review.record_id, observation=request))
        assert third.event.typed_payload.generation_before == third.event.typed_payload.generation_after == 2
        assert third.event.typed_payload.review_event_ref == first.event.record_id
        assert third.event.typed_payload.use_event_ref == second.event.record_id
        assert len(authority._adapter._tables["receipt_records"]) == 5 and authority._counter == 3
        operational = next(row for row in authority._bindings.values() if row._permit is not None)
        permit = operational._permit
        arguments = dict(source_receipt=operational._source, rights_receipt=operational._rights,
            account_scope=scope.account_scope_ref, internal_use_class=scope.internal_use_class,
            permitted_retention_class=scope.permitted_retention_class, expected_market_ticker=request.market_ticker,
            process_epoch_id=authority._process_ref, monotonic_clock_id=authority._clock_ref,
            operating_authorization_ref=third.event.record_id, authorization_expires_at_utc=request.expires_at_utc,
            deadline_monotonic_ns=permit._deadline, source_use_binding=operational)
        owner = source.KalshiFeeObservationOwnerV1(**arguments)
        assert permit._owner is owner
        with pytest.raises(ComputationControlPlaneError):
            source.KalshiFeeObservationOwnerV1(**arguments)
        with pytest.raises(ComputationControlPlaneError):
            owner._check_inputs_v1(fills, Decimal(".0001"), Decimal(0))
        detached = authority._adapter.load_committed_source_action_v1(third.event.record_id)
        assert detached == third.event and detached is not third.event
        assert detached.typed_payload is not third.event.typed_payload
        batch = authority._adapter._registered_batches[first.event.record_id]
        before_bindings = tuple(authority._bindings)
        duplicate = authority._uow.commit_source_use_action_v1(originals=batch["originals"], event=first.event,
            expected_event_ref=None, expected_declaration_ref=None, expected_review_ref=None, verified_action=batch["verified"])
        assert duplicate.disposition == "EXACT_DUPLICATE" and duplicate.current_event == third.event
        assert tuple(authority._bindings) == before_bindings and authority._counter == 3
        for operation in (lambda: authority._adapter.get_record(first.event.record_id), authority._adapter.begin_transaction,
                          lambda: TrancheCUnitOfWorkV1(authority._adapter, TransactionRetryPolicyV1(2))):
            with pytest.raises(ComputationControlPlaneError):
                operation()
        reference = InMemoryPersistenceAdapterV1()
        tx = reference.begin_transaction()
        with pytest.raises(ComputationControlPlaneError):
            reference.insert_receipt_record(tx, first.event)
        tx.rollback()
        database = SQLiteReferenceAdapterV1(reference_directory / "source-use-action-denial.sqlite",
            busy_timeout_ms=0, max_transaction_attempts=1)
        try:
            with pytest.raises(ComputationControlPlaneError):
                database.insert_receipt_record(None, first.event)
        finally:
            database.close()
        for offset, expected in ((54, "ACTIVE"), (55, "EXPIRED_OR_NOT_CURRENT"), (56, "EXPIRED_OR_NOT_CURRENT")):
            clock["wall"] = (seconds + offset) * 1_000_000_000
            clock["mono"] = 10_000_000_000 + offset * 1_000_000_000
            assert h.controller.read_status_v1()["state"] == expected
        authority.stop_v1()
        assert h.controller.read_status_v1()["state"] == "STOPPED"
        assert h.controller.read_status_v1()["expiry"] == second.event.typed_payload.expires_at_utc.isoformat()
        with pytest.raises(ComputationControlPlaneError):
            owner._check_inputs_v1(fills, Decimal(".01"), Decimal(0))

    clock.update(wall=seconds * 1_000_000_000, mono=10_000_000_000)
    _assert_source_use_cancel_and_thread_binding(moment)
    _assert_source_use_atomic_and_currentness(moment)
    _assert_source_use_withdrawal_fences()
    _assert_source_use_controller_publication()
    _assert_source_use_authority_boundaries(moment)
    _assert_source_use_capacity(moment)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def _assert_source_use_cancel_and_thread_binding(moment):
    from threading import Event, Thread
    from datetime import timedelta
    from src.qtt.service import owner_source_use as service
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import SourceUseObservationRequestV1
    from tests.stage1_prediction_markets.qku_computation_control_plane.security.test_deserialization_safety import _synthetic_source_use_root

    for action in ('REVIEW_ACCEPT', 'USE_ADMIT', 'OBSERVE_ONCE'):
        with _synthetic_source_use_root() as h:
            scope, review, facts, declaration = _source_use_action_proposals(moment)
            proposal = dict(action='REVIEW_ACCEPT', scope=scope, original=review, review_facts=facts,
                requested_expires_at_utc=moment + timedelta(seconds=60))
            if action != 'REVIEW_ACCEPT':
                reviewed = h.sign(proposal)
                proposal = dict(action='USE_ADMIT', scope=scope, original=declaration,
                    expected_review_ref=reviewed.review.record_id, requested_expires_at_utc=moment + timedelta(seconds=55))
            if action == 'OBSERVE_ONCE':
                used = h.sign(proposal)
                proposal = dict(action=action, scope=scope, expected_declaration_ref=used.declaration.record_id,
                    expected_review_ref=used.review.record_id, observation=SourceUseObservationRequestV1(
                        'SYNTHETIC::MARKET', (KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal('.5')),),
                        Decimal('.01'), Decimal(0), moment + timedelta(seconds=50), 50_000_000_000))
            entered, release = Event(), Event()
            errors, proofs, responses = [], [], []
            real_verify = service._verify_source_use_response_v1
            before = h.authority._head
            old_counter = h.authority._counter

            def blocked_verify(*args, **kwargs):
                responses.append(args[1])
                entered.set()
                assert release.wait(5)
                proof = real_verify(*args, **kwargs)
                proofs.append(proof)
                return proof

            def complete():
                try:
                    h.sign(proposal, via_controller=True)
                except BaseException as error:
                    errors.append(error)

            with pytest.MonkeyPatch.context() as patch:
                patch.setattr(service, '_verify_source_use_response_v1', blocked_verify)
                worker = Thread(target=complete)
                worker.start()
                try:
                    assert entered.wait(5)
                    pending = h.authority._completion_pending
                    assert pending is not None and h.authority._pending is None and h.root.operation is None
                    h.controller.cancel_v1()
                    assert h.authority._valid_completion is None
                finally:
                    release.set()
                    worker.join(5)
                assert not worker.is_alive()
            assert len(proofs) == len(errors) == 1 and isinstance(errors[0], ComputationControlPlaneError)
            assert h.authority._counter == old_counter + 1 == proofs[0].counter
            assert h.authority._head is before and h.authority._active_permit is None
            assert h.controller._result is None and h.authority._completion_pending is None
            assert not h.root.completed
            with pytest.raises(ComputationControlPlaneError):
                h.authority.complete_action_v1(pending.request_ref, responses[0])

    # Every original capture prepares/charges on its own thread. An attempted
    # transfer of that exact pending object cannot consume either request count.
    with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
        real_prepare = source.KalshiFeeObservationOwnerV1._prepare_read_v1
        rejected = []

        def prepare(owner, *args):
            prepared = real_prepare(owner, *args)
            attempts, started = owner._attempts, owner._config.source_use_binding._permit._started
            def other_thread():
                try:
                    owner._recheck_and_charge_v1(prepared)
                except ComputationControlPlaneError as error:
                    rejected.append(error)
            worker = Thread(target=other_thread)
            worker.start(); worker.join(5)
            assert not worker.is_alive()
            assert owner._attempts == attempts and owner._config.source_use_binding._permit._started == started
            return prepared

        patch.setattr(source.KalshiFeeObservationOwnerV1, '_prepare_read_v1', prepare)
        h.owner.capture()
        assert len(rejected) == h.owner._attempts == len(h.sends) == 3


def _assert_source_use_atomic_and_currentness(moment):
    from datetime import timedelta
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import persistence as storage
    from tests.stage1_prediction_markets.qku_computation_control_plane.security.test_deserialization_safety import _synthetic_source_use_root

    for phase in ("prepare", "begin", "validate", "original", "event", "complete", "commit_before", "commit_after", "rollback", "publish"):
        with _synthetic_source_use_root() as h, pytest.MonkeyPatch.context() as patch:
            authority, adapter = h.authority, h.authority._adapter
            scope, review, facts, declaration = _source_use_action_proposals(moment)
            proposal = dict(action="REVIEW_ACCEPT", scope=scope, original=review, review_facts=facts,
                            requested_expires_at_utc=moment + timedelta(seconds=60))
            if phase == "publish":
                reviewed = h.sign(proposal)
                proposal = dict(action="USE_ADMIT", scope=scope, original=declaration,
                    expected_review_ref=reviewed.review.record_id, requested_expires_at_utc=moment + timedelta(seconds=55))
            before = {name: dict(rows) for name, rows in adapter._tables.items()}
            before_count = len(before["receipt_records"])
            primary = RuntimeError("synthetic source-use atomic failure")
            def fail(*args, **kwargs):
                raise primary
            if phase == "prepare":
                patch.setattr(adapter, "_prepare_action_batch_v1", fail)
            elif phase == "begin":
                patch.setattr(adapter, "begin_transaction", fail)
            elif phase in ("validate", "complete"):
                original = adapter._validate_action_batch_v1
                def validate(transaction, *, complete):
                    if complete == (phase == "complete"):
                        raise primary
                    return original(transaction, complete=complete)
                patch.setattr(adapter, "_validate_action_batch_v1", validate)
            elif phase in ("original", "event", "rollback"):
                original = adapter.insert_receipt_record
                count = [0]
                def insert(transaction, row):
                    count[0] += 1
                    if count[0] == (2 if phase == "event" else 1):
                        raise primary
                    return original(transaction, row)
                patch.setattr(adapter, "insert_receipt_record", insert)
                if phase == "rollback":
                    original_rollback = storage._InMemoryTransactionV1.rollback
                    def rollback(transaction):
                        original_rollback(transaction)
                        raise RuntimeError("synthetic rollback failure")
                    patch.setattr(storage._InMemoryTransactionV1, "rollback", rollback)
            elif phase in ("commit_before", "commit_after"):
                original = adapter._commit
                def commit(transaction):
                    if phase == "commit_after":
                        original(transaction)
                    raise primary
                patch.setattr(adapter, "_commit", commit)
            elif phase == "publish":
                patch.setattr(authority, "_issue_binding_v1", fail)
            with pytest.raises(RuntimeError) as failure:
                h.sign(proposal)
            assert failure.value is primary
            assert authority._stopped and authority._use is None and not authority._bindings
            assert authority._active_permit is None and authority._pending is None
            assert adapter._active_transaction is None and authority._counter == h.counter[0]
            if phase in ("commit_after", "publish"):
                assert len(adapter._tables["receipt_records"]) == before_count + 2
            else:
                assert adapter._tables == before
            assert adapter._source_use_integrity_failed_v1 is (phase in ("commit_before", "commit_after", "rollback"))
            assert h.controller.read_status_v1()["state"] == "STOPPED"

    # Real successful proofs exercise all counter transitions; all-zero is
    # accepted without asserting cloning resistance or cross-process continuity.
    for counters, accepted in (((0, 0), True), ((0, 2), True), ((2, 3), True), ((2, 2), False), ((2, 1), False)):
        with _synthetic_source_use_root() as h:
            scope, review, facts, _ = _source_use_action_proposals(moment)
            proposal = dict(action="REVIEW_ACCEPT", scope=scope, original=review, review_facts=facts,
                            requested_expires_at_utc=moment + timedelta(seconds=60))
            h.counter[0] = counters[0] - 1
            first = h.sign(proposal)
            h.counter[0] = counters[1] - 1
            if accepted:
                second = h.sign(proposal)
                assert second.review == first.review and second.event.typed_payload.generation_after == 2
                assert second.event.typed_payload.original_event_refs == ()
                assert second.event.typed_payload.review_facts.factual_checked_at_utc == facts.factual_checked_at_utc
            else:
                with pytest.raises(ComputationControlPlaneError):
                    h.sign(proposal)
                assert h.authority._stopped and h.authority._head == first.event


def _assert_source_use_withdrawal_fences():
    from threading import Event, Thread
    from src.qtt.pretrade import pr169_pretrade1_resolvers as pretrade
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source

    def withdraw(h):
        head = h.issuer.authority._head.typed_payload
        return h.issuer.sign(dict(action="WITHDRAW_USE", scope=head.scope,
            expected_declaration_ref=head.declaration_ref, expected_review_ref=head.review_ref,
            reason="SYNTHETIC_OWNER_WITHDRAWAL"))

    with _synthetic_kalshi_observation() as h:
        withdraw(h)
        with pytest.raises(ComputationControlPlaneError):
            h.owner.capture()
        assert not h.connections and not h.sends and h.owner._attempts == 0

    for stop in (False, True):
        for boundary in range(3):
            def invalidate(h, index):
                if index == boundary:
                    h.issuer.controller.stop_v1() if stop else withdraw(h)
            with _synthetic_kalshi_observation(on_send=invalidate) as h:
                with pytest.raises(ComputationControlPlaneError):
                    h.owner.capture()
                assert len(h.sends) == h.owner._attempts == boundary + 1
                assert h.owner._issued_cohort is None
                assert h.issuer.controller.read_status_v1()["already_started"] is True
                assert h.issuer.authority._last_operating_permit._started == boundary + 1

    for winner in ("withdrawal", "publication"):
        with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
            cohort = h.owner.capture()
            entered, release, finished = Event(), Event(), Event()
            results, errors = [], []
            original = pretrade.compose_kalshi_quadratic_taker_buy_yes_cashflows_v1
            def calculate(**kwargs):
                entered.set()
                assert release.wait(5)
                return original(**kwargs)
            patch.setattr(pretrade, "compose_kalshi_quadratic_taker_buy_yes_cashflows_v1", calculate)
            def compose():
                try:
                    results.append(pretrade.compose_kalshi_observed_fee_scenario_cashflows_v1(
                        profile_id="KALSHI_US_DCM_DIRECT", currency="USD", source_owner=h.owner, cohort=cohort,
                        expected_market_ticker="SYNTHETIC::MARKET", as_of_monotonic_ns=cohort.available_monotonic_ns,
                        fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal(".5")),),
                        balance_increment=Decimal(".01"), prior_rounding_overpayment=Decimal(0)))
                except BaseException as error:
                    errors.append(error)
                finally:
                    finished.set()
            worker = Thread(target=compose)
            worker.start()
            try:
                assert entered.wait(5)
                if winner == "withdrawal":
                    withdraw(h)
                release.set()
                assert finished.wait(5)
            finally:
                release.set()
                worker.join(5)
            assert not worker.is_alive()
            if winner == "publication":
                assert not errors and len(results) == 1 and results[0].platform_fee_total == Decimal("1.75")
                assert h.kwargs["source_use_binding"]._permit._published
                withdraw(h)
            else:
                assert not results and len(errors) == 1 and isinstance(errors[0], ComputationControlPlaneError)
            assert h.issuer.authority._use is None
            assert h.issuer.controller.read_status_v1()["already_started"] is True
            assert h.issuer.authority._last_operating_permit._started == 3


def _assert_source_use_controller_publication():
    from threading import Event, Thread
    from src.qtt.pretrade import pr169_pretrade1_resolvers as pretrade
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source

    def withdraw(h):
        head = h.issuer.authority._head.typed_payload
        return h.issuer.sign(dict(action="WITHDRAW_USE", scope=head.scope,
            expected_declaration_ref=head.declaration_ref, expected_review_ref=head.review_ref,
            reason="SYNTHETIC_OWNER_WITHDRAWAL"))

    for changed in ("source_receipt", "expected_market_ticker", "deadline_monotonic_ns"):
        with _synthetic_kalshi_observation() as h:
            arguments = dict(h.authorize())
            permit = arguments["source_use_binding"]._permit
            assert permit._owner is None
            with pytest.raises(ComputationControlPlaneError):
                source.KalshiFeeObservationOwnerV1(**{**arguments, changed: None})
            assert permit._failed and permit._owner is not None and h.issuer.authority._active_permit is None
            with pytest.raises(ComputationControlPlaneError):
                source.KalshiFeeObservationOwnerV1(**arguments)
            assert not h.connections

    for boundary in ("outer_result", "before_display", "after_display"):
        with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
            entered, release = Event(), Event()
            results, errors = [], []
            original = pretrade.KalshiObservedFeeScenarioResultV1.__post_init__
            def construct(result):
                original(result)
                entered.set()
                assert release.wait(5)
            patch.setattr(pretrade.KalshiObservedFeeScenarioResultV1, "__post_init__", construct)
            def operate():
                try:
                    results.append(h.authorize(via_controller=True))
                except BaseException as error:
                    errors.append(error)
            worker = Thread(target=operate)
            worker.start()
            try:
                assert entered.wait(5)
                if boundary == "outer_result":
                    withdraw(h)
            finally:
                release.set()
                worker.join(5)
            assert not worker.is_alive() and len(h.sends) == 3
            controller = h.issuer.controller
            if boundary == "outer_result":
                assert len(errors) == 1 and isinstance(errors[0], ComputationControlPlaneError)
                assert not results and controller._result is None and controller._display_model is None
                assert not h.issuer.authority._last_operating_permit._published
            else:
                assert not errors and len(results) == 1 and results[0]["state"] == "ACTIVE"
                assert h.issuer.authority._last_operating_permit._published
                assert controller._result[0].cashflows.platform_fee_total == Decimal("1.75")
                assert controller._result[0].cashflows.entry_trade_cashflow_total == Decimal("-50")
                if boundary == "after_display":
                    model = controller._display_result_v1()
                    assert Decimal(model["platform_fee_total"]) == Decimal("1.75") and "HISTORICAL RESULT" in model["label"]
                    assert "source_receipt_ref" not in model and "account_scope" not in model
                withdraw(h)
                with pytest.raises(ComputationControlPlaneError):
                    controller._display_result_v1()
                if boundary == "before_display":
                    assert controller._display_model is None
                else:
                    assert controller._display_model is model  # Already displayed history stays labeled.
            assert not h.issuer.root.completed and controller.read_status_v1()["already_started"] is True


def _assert_source_use_authority_boundaries(moment):
    from datetime import timedelta
    import time
    from src.qtt.service import owner_source_use as service
    from tests.stage1_prediction_markets.qku_computation_control_plane.security.test_deserialization_safety import _synthetic_source_use_root

    base = int(moment.timestamp()) * 1_000_000_000
    for kind in ("pending", "session"):
        for offset in (-1, 0, 1):
            clock = dict(wall=base, mono=10_000_000_000)
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr(time, "time_ns", lambda: clock["wall"])
                patch.setattr(time, "monotonic_ns", lambda: clock["mono"])
                with _synthetic_source_use_root() as h:
                    scope, review, facts, unused = _source_use_action_proposals(moment)
                    expiry = moment + timedelta(seconds=900)
                    facts = replace(facts, source_expires_at_utc=expiry)
                    review = replace(review, claimed_expires_at_utc=expiry)
                    proposal = dict(action="REVIEW_ACCEPT", scope=scope, original=review, review_facts=facts,
                                    requested_expires_at_utc=expiry)
                    if kind == "session":
                        clock.update(wall=base + 780_000_000_000, mono=790_000_000_000)
                    def advance():
                        seconds = 120 if kind == "pending" else 900
                        clock.update(wall=base + seconds * 1_000_000_000 + offset,
                                     mono=10_000_000_000 + seconds * 1_000_000_000 + offset)
                    if offset < 0:
                        result = h.sign(proposal, via_controller=True, before_complete=advance)
                        assert result["action"] == "REVIEW_ACCEPT" and h.authority._head is not None
                    else:
                        with pytest.raises(ComputationControlPlaneError):
                            h.sign(proposal, via_controller=True, before_complete=advance)
                        assert h.authority._head is None and not h.authority._bindings
                    reference, pending, raw = h.completions[-1]
                    assert pending.deadline_monotonic_ns == (130_000_000_000 if kind == "pending" else 910_000_000_000)
                    assert not h.root.completed and h.authority._pending is None
                    with pytest.raises(ComputationControlPlaneError):
                        h.controller.complete_action_v1(reference, raw)

    for failure in ("signature", "head", "original", "scope", "cleared_scope"):
        with _synthetic_source_use_root() as h, pytest.MonkeyPatch.context() as patch:
            scope, review, facts, declaration = _source_use_action_proposals(moment)
            reviewed = h.sign(dict(action="REVIEW_ACCEPT", scope=scope, original=review, review_facts=facts,
                                  requested_expires_at_utc=moment + timedelta(seconds=60)))
            proposal = dict(action="USE_ADMIT", scope=scope, original=declaration,
                expected_review_ref=reviewed.review.record_id, requested_expires_at_utc=moment + timedelta(seconds=55))
            real_verify = service._verify_source_use_response_v1
            observed = []
            def verify(*args, **kwargs):
                proof = real_verify(*args, **kwargs)
                observed.append(proof)
                if failure == "scope":
                    h.authority._selected_scope = replace(scope, account_scope_ref="SYNTHETIC::OTHER")
                elif failure == "cleared_scope":
                    h.authority._selected_scope = None
                elif failure == "head":
                    patch.setattr(h.authority._adapter, "load_committed_source_action_head_v1", lambda reference: None)
                elif failure == "original":
                    old = h.authority._adapter.load_committed_source_use_record_v1
                    def changed(reference):
                        row = old(reference)
                        return replace(row, typed_payload=replace(row.typed_payload,
                            content=replace(row.typed_payload.content, original_text="SYNTHETIC changed original")))
                    patch.setattr(h.authority._adapter, "load_committed_source_use_record_v1", changed)
                return proof
            patch.setattr(service, "_verify_source_use_response_v1", verify)
            before = {name: dict(rows) for name, rows in h.authority._adapter._tables.items()}
            transform = (lambda raw: replace(raw, signature=b"synthetic invalid proof")) if failure == "signature" else None
            with pytest.raises((ComputationControlPlaneError, ValueError)):
                h.sign(proposal, via_controller=True, transform_response=transform)
            assert bool(observed) is (failure != "signature")
            assert h.authority._use is None and not h.authority._bindings and h.controller._result is None
            assert h.authority._adapter._tables == before and not h.root.completed
            reference, unused, raw = h.completions[-1]
            with pytest.raises(ComputationControlPlaneError):
                h.controller.complete_action_v1(reference, raw)


def _assert_source_use_capacity(moment):
    from datetime import timedelta
    from src.qtt.service import owner_source_use as service
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import _source_use_reconstruct_spine_v1
    from tests.stage1_prediction_markets.qku_computation_control_plane.security.test_deserialization_safety import _synthetic_source_use_root

    scope, review, facts, unused = _source_use_action_proposals(moment)
    proposal = dict(action="REVIEW_ACCEPT", scope=scope, original=review, review_facts=facts,
                    requested_expires_at_utc=moment + timedelta(seconds=60))
    with _synthetic_source_use_root() as h:
        for unused in range(253):
            h.sign(proposal)
        rows = h.authority._adapter._tables["receipt_records"]
        assert len(rows) == 254
        previous = dict(rows)
        # A different original uses the full reserved two-record allowance.
        h.sign({**proposal, "original": replace(review, original_text="SYNTHETIC second source review.")})
        rows = h.authority._adapter._tables["receipt_records"]
        assert len(rows) == 256 and all(rows[key] == value for key, value in previous.items())
        before = dict(rows)
        with pytest.MonkeyPatch.context() as patch:
            def no_prompt(*args, **kwargs):
                raise AssertionError("capacity must refuse before challenge/native confirmation")
            patch.setattr(service, "_begin_source_use_authentication_v1", no_prompt)
            with pytest.raises(ComputationControlPlaneError):
                h.controller.prepare_action_v1(deterministic_json(proposal).encode())
            assert h.authority._pending is None and h.root.operation is None
            h.controller.stop_v1()
        assert h.authority._stopped and not h.authority._bindings and h.authority._use is None
        assert h.authority._adapter._tables["receipt_records"] == before
        with pytest.raises(ComputationControlPlaneError):
            h.controller.prepare_action_v1(deterministic_json(proposal).encode())

    # Whole canonical spines are bounded, not just their source text. The exact
    # byte ceiling times the independently enforced 256 rows is exactly16MiB.
    row = _source_use_record()
    padding = 65536 - len(deterministic_json(row).encode())
    content = replace(row.typed_payload.content, original_text=row.typed_payload.content.original_text + "x" * padding)
    exact = replace(row, typed_payload=replace(row.typed_payload, content=content))
    assert len(deterministic_json(exact).encode()) == 65536
    assert _source_use_reconstruct_spine_v1(exact) == exact
    with pytest.raises(ComputationControlPlaneError):
        replace(exact, typed_payload=replace(exact.typed_payload,
            content=replace(content, original_text=content.original_text + "x")))
    assert 256 * len(deterministic_json(exact).encode()) == 16 * 1024 * 1024
    with _synthetic_source_use_root() as restarted:
        assert restarted.controller.read_status_v1()["state"] == "DENIED"
        assert restarted.authority._head is None and restarted.authority._counter == 0
        assert not restarted.authority._bindings and not restarted.authority._adapter._tables["receipt_records"]


def _source_use_record(stream="synthetic-owner", sequence=1, action="RECORD", *,
                       subject="OWNER_DECLARATION", content=None, scope=None, recorded=NOW,
                       input_class="SYNTHETIC_TEST"):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import Stage1VenueProfileIdV1

    if scope is None:
        scope = SourceUseScopeV1(Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
            "KALSHI_PUBLIC_MARKET_EVENT_SERIES", "KALSHI_PUBLIC_FEE_OBSERVATION_V1",
            "OBSERVED_FEE_SCENARIO_INTERNAL", "PROCESS_MEMORY_ONLY",
            "NO_REDISTRIBUTION_NO_EXTERNAL_AI_FORWARDING", None)
    if content is None and action != "WITHDRAW":
        content = SourceUseOriginalContentV1(" \tSYNTHETIC café 漢字\r\n  reference statement only.\n ",
            None, None, "UNKNOWN", None,
            "https://synthetic.invalid/document" if subject == "SOURCE_REVIEW" else None,
            "synthetic-edition" if subject == "SOURCE_REVIEW" else None, None, None)
    aggregate = "SOURCE_USE::" + stream
    payload = SourceUseControlRecordV1(stream, subject, sequence, action,
        None if action == "RECORD" else f"{aggregate}::{sequence - 1:020d}", scope, content,
        None if action == "RECORD" else "synthetic lifecycle reason", input_class)
    return EconomicReceiptEventSpineV1(f"{aggregate}::{sequence:020d}", EconomicRecordTypeV1.SOURCE_USE_CONTROL,
        "SOURCE_USE_CONTROL_V1", "QTT_SOURCE_USE_CUSTODY", "QTT_SOURCE_USE_CUSTODY",
        "synthetic-context", recorded, recorded, "synthetic-cause", "synthetic-correlation",
        "synthetic-trace", "synthetic-tracestate", sequence, aggregate, sequence,
        "RECORDED_NOT_AUTHENTICATED_NOT_ADMITTED", payload)


def _source_use_adapter(kind, path, *, attempts=1):
    return (InMemoryPersistenceAdapterV1() if kind == "memory" else
            SQLiteReferenceAdapterV1(path, busy_timeout_ms=0, max_transaction_attempts=attempts))


def _source_use_counts(adapter):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.migrations import APPEND_ONLY_TABLES_V1

    if isinstance(adapter, SQLiteReferenceAdapterV1):
        return {table: adapter._connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in APPEND_ONLY_TABLES_V1}
    return {table: len(rows) for table, rows in adapter._tables.items()}


def _source_use_append(adapter, record, *, attempts=1):
    return TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(attempts)).append_source_use_control_v1(
        record=record, expected_previous_record_ref=record.typed_payload.predecessor_record_ref)


def _assert_source_use_lifecycle(kind, directory, monkeypatch):
    from copy import copy
    from datetime import timedelta
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        PersistenceContractError, PointInTimeError, TransactionContractError,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
        RecordedSourceUseStatusV1, read_recorded_source_use_status_v1,
    )

    path = directory / (kind + "-source-use.db")
    adapter = _source_use_adapter(kind, path)
    peer = _source_use_adapter(kind, path) if kind == "sqlite" else adapter
    try:
        def status(at=NOW):
            return read_recorded_source_use_status_v1(adapter=adapter, stream_id="synthetic-owner", evaluated_at_utc=at)

        missing = status()
        assert (missing.state, missing.current_head_record_ref, missing.current_sequence,
                missing.subject_kind, missing.recorded_at_utc, missing.admission_eligible) == (
                    "MISSING", None, None, None, None, False)
        with pytest.raises(TypeError):
            RecordedSourceUseStatusV1("synthetic-owner", None, None, None, None, NOW, "MISSING", admission_eligible=True)
        original = _source_use_record()
        first = _source_use_append(adapter, original)
        assert first.disposition == "APPENDED" and first.record == first.current_head == original
        assert first.record is not original and first.record.typed_payload is not original.typed_payload
        assert status().state == "RECORDED_UNVERIFIED" and status().admission_eligible is False
        stored_text = original.typed_payload.content.original_text
        object.__setattr__(original.typed_payload.content, "original_text", "synthetic input mutation after commit")
        assert adapter.load_committed_source_use_record_v1(original.record_id).typed_payload.content.original_text == stored_text
        original = first.record
        loaded = adapter.load_committed_source_use_record_v1(original.record_id)
        object.__setattr__(loaded.typed_payload.content, "original_text", "synthetic tampering")
        assert adapter.load_committed_source_use_record_v1(original.record_id).typed_payload.content.original_text == stored_text
        generic = adapter.get_record(original.record_id)
        object.__setattr__(generic.typed_payload.content, "original_text", "synthetic generic-read mutation")
        assert adapter.load_committed_source_use_record_v1(original.record_id).typed_payload.content.original_text == stored_text
        assert adapter.load_committed_source_use_head_v1("synthetic-owner").typed_payload.scope.account_scope_ref is None
        review = _source_use_record("synthetic-review", subject="SOURCE_REVIEW")
        review = replace(review, typed_payload=replace(review.typed_payload,
            content=replace(review.typed_payload.content, reported_time_kind="CALENDAR_DATE", reported_time_text="2026-01-01")))
        _source_use_append(adapter, review)
        assert adapter.load_committed_source_use_record_v1(review.record_id) == review
        assert adapter.load_committed_source_use_record_v1(_source_use_record("synthetic-missing").record_id) is None
        start, expiry = NOW + timedelta(minutes=1), NOW + timedelta(minutes=2)
        replacement = _source_use_record(sequence=2, action="SUPERSEDE", recorded=NOW + timedelta(seconds=10),
            content=replace(original.typed_payload.content, original_text="SYNTHETIC replacement\t\r\n",
                reported_time_kind="UTC_INSTANT", reported_time_text="2026-01-01T00:00:00.1Z",
                claimed_effective_at_utc=start, claimed_expires_at_utc=expiry))
        second = _source_use_append(adapter, replacement)
        assert (second.disposition, second.current_head.sequence, second.current_head.typed_payload.predecessor_record_ref) == (
            "APPENDED", 2, "SOURCE_USE::synthetic-owner::00000000000000000001")
        with pytest.raises(PointInTimeError) as future:
            status()
        assert future.value.reason_code is ReasonCode.POINT_IN_TIME_VIOLATION
        assert status(NOW + timedelta(seconds=10)).state == "CLAIMED_NOT_YET_EFFECTIVE_UNVERIFIED"
        assert status(start).state == "RECORDED_UNVERIFIED"
        assert status(expiry).state == "CLAIMED_EXPIRED_UNVERIFIED"
        assert status(expiry + timedelta(days=1)).admission_eligible is False
        before = _source_use_counts(adapter)
        for duplicate in (original, replacement):
            result = _source_use_append(adapter, duplicate)
            assert result.disposition == "EXACT_DUPLICATE" and result.record == duplicate and result.current_head == replacement
        assert _source_use_counts(adapter) == before

        withdrawal = _source_use_record(sequence=3, action="WITHDRAW", recorded=NOW + timedelta(seconds=20))
        transaction = adapter.begin_transaction()
        try:
            for reader, argument in ((adapter.load_committed_source_use_record_v1, original.record_id),
                                     (adapter.get_record, original.record_id),
                                     (adapter.load_committed_source_use_head_v1, "synthetic-owner")):
                with pytest.raises(TransactionContractError) as caught:
                    reader(argument)
                assert caught.value.reason_code is ReasonCode.TRANSACTION_STATE_INVALID
            for reader, argument in ((adapter.load_source_use_record_for_update_v1, original.record_id),
                                     (adapter.load_source_use_head_for_update_v1, "synthetic-owner")):
                with pytest.raises(TransactionContractError):
                    reader(copy(transaction), argument)
            assert adapter.load_source_use_record_for_update_v1(transaction, original.record_id) == original
            adapter.insert_receipt_record(transaction, withdrawal)
            assert adapter.load_source_use_head_for_update_v1(transaction, "synthetic-owner") == withdrawal
            if kind == "sqlite":
                assert peer.load_committed_source_use_head_v1("synthetic-owner") == replacement
                assert peer.load_committed_source_use_record_v1(withdrawal.record_id) is None
                with pytest.raises(TransactionContractError):
                    peer.load_source_use_head_for_update_v1(transaction, "synthetic-owner")
        finally:
            transaction.rollback()
        with pytest.raises(TransactionContractError):
            adapter.load_source_use_record_for_update_v1(transaction, original.record_id)
        assert adapter.load_committed_source_use_head_v1("synthetic-owner") == replacement
        assert _source_use_counts(adapter) == before
        # Two correctly owned writers read the same predecessor, then interleave stale proposals.
        observed = peer.load_committed_source_use_head_v1("synthetic-owner")
        assert observed == replacement
        alternative = _source_use_record(sequence=3, action="SUPERSEDE", recorded=withdrawal.recorded_at)
        _source_use_append(adapter, withdrawal)
        with pytest.raises(PersistenceContractError) as loser:
            _source_use_append(peer, alternative)
        assert loser.value.reason_code is ReasonCode.PERSISTENCE_CONFLICT
        assert peer.load_committed_source_use_head_v1("synthetic-owner") == withdrawal
        with pytest.raises(PointInTimeError):
            status(NOW + timedelta(seconds=19))
        projected = status(withdrawal.recorded_at)
        assert (projected.state, projected.current_sequence, projected.admission_eligible) == (
            "WITHDRAWAL_RECORDED_UNVERIFIED", 3, False)
        assert {field.name for field in fields(projected)} == {
            "stream_id", "current_head_record_ref", "current_sequence", "subject_kind",
            "recorded_at_utc", "evaluated_at_utc", "state", "admission_eligible",
        }
        with pytest.raises(PersistenceContractError):
            _source_use_append(adapter, _source_use_record(sequence=4, action="SUPERSEDE", recorded=expiry))
        with pytest.raises(ContractValidationError):
            TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1)).append_source_use_control_v1(
                record=original, expected_previous_record_ref=original.record_id)
        # Observe actual UOW orchestration: old identity lookup is transactional, then read-only commit.
        calls = []
        begin, head_read, record_read = (adapter.begin_transaction, adapter.load_source_use_head_for_update_v1,
                                         adapter.load_source_use_record_for_update_v1)
        def traced_begin():
            calls.append("begin")
            tx = begin()
            commit = tx.commit
            def traced_commit():
                calls.append("commit")
                commit()
            tx.commit = traced_commit
            return tx
        def traced_head(tx, stream):
            calls.append("head")
            return head_read(tx, stream)
        def traced_record(tx, ref):
            calls.append("record")
            return record_read(tx, ref)
        with monkeypatch.context() as patch:
            patch.setattr(adapter, "begin_transaction", traced_begin)
            patch.setattr(adapter, "load_source_use_head_for_update_v1", traced_head)
            patch.setattr(adapter, "load_source_use_record_for_update_v1", traced_record)
            result = _source_use_append(adapter, original)
        assert calls == ["begin", "head", "record", "commit"]
        assert result.disposition == "EXACT_DUPLICATE" and result.record == original and result.current_head == withdrawal
        counts = _source_use_counts(adapter)
        assert len(counts) == 10 and counts["receipt_records"] == 4
        assert all(count == 0 for table, count in counts.items() if table != "receipt_records")
        assert adapter.production_selection_state.startswith("NO_DEFAULT")
        if kind == "sqlite":
            peer.close()
            adapter.close()
            adapter = _source_use_adapter(kind, path)
            assert adapter.load_committed_source_use_record_v1(original.record_id) == original
            assert adapter.load_committed_source_use_record_v1(replacement.record_id) == replacement
            assert adapter.load_committed_source_use_record_v1(review.record_id) == review
            assert status(expiry).state == "WITHDRAWAL_RECORDED_UNVERIFIED"
            assert _source_use_counts(adapter) == counts
    finally:
        if kind == "sqlite":
            adapter.close()
            peer.close()


def _assert_source_use_rejections(kind, directory):
    from copy import copy
    from datetime import timedelta
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import PersistenceContractError

    adapter = _source_use_adapter(kind, directory / (kind + "-source-use-rejections.db"))
    try:
        original = _source_use_record(recorded=NOW + timedelta(seconds=5))
        _source_use_append(adapter, original)
        second = _source_use_record(sequence=2, action="SUPERSEDE", recorded=original.recorded_at)
        different_scope = replace(second, typed_payload=replace(second.typed_payload,
            scope=replace(second.typed_payload.scope, account_scope_ref="synthetic-other-account")))
        different_input = replace(second, typed_payload=replace(second.typed_payload, input_class="UNVERIFIED_SUBMISSION"))
        changed_subject = _source_use_record(sequence=2, action="SUPERSEDE", subject="SOURCE_REVIEW", recorded=original.recorded_at)
        changed_identity = replace(original, typed_payload=replace(original.typed_payload,
            content=replace(original.typed_payload.content, original_text="SYNTHETIC conflicting original")))
        for candidate in (different_scope, different_input, changed_subject, changed_identity,
                _source_use_record(sequence=2, action="SUPERSEDE"),
                _source_use_record(sequence=3, action="SUPERSEDE", recorded=original.recorded_at),
                _source_use_record("synthetic-absent", sequence=2, action="SUPERSEDE")):
            for direct in (False, True):
                before = _source_use_counts(adapter)
                transaction = adapter.begin_transaction() if direct else None
                try:
                    with pytest.raises(PersistenceContractError) as caught:
                        if direct:
                            adapter.insert_receipt_record(transaction, candidate)
                        else:
                            _source_use_append(adapter, candidate)
                    assert caught.value.reason_code is ReasonCode.PERSISTENCE_CONFLICT
                finally:
                    if transaction is not None:
                        transaction.rollback()
                assert _source_use_counts(adapter) == before
        for malformed in (None, True, 1, "", "SOURCE_USE::synthetic-owner::1", "SOURCE_USE::synthetic-owner::00000000000000000000",
                          "SOURCE_USE::synthetic-owner::09223372036854775808", "source_use::synthetic-owner::00000000000000000001"):
            with pytest.raises(ContractValidationError) as caught:
                adapter.load_committed_source_use_record_v1(malformed)
            assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
        for malformed in (None, 1, True, "", "synthetic/owner", "é", "a" * 65):
            with pytest.raises(ContractValidationError):
                adapter.load_committed_source_use_head_v1(malformed)
        # Forged frozen objects must be reconstructed before direct insertion or UOW begin.
        candidates = []
        for name, value in (("sequence", True), ("aggregate_version", "1"), ("authority_class", "ADMITTED"),
                            ("effective_at", NOW.isoformat()), ("record_type", EconomicRecordTypeV1.ECONOMIC_EVENT)):
            forged = copy(original)
            object.__setattr__(forged, name, value)
            candidates.append(forged)
        empty_payload = object.__new__(SourceUseControlRecordV1)
        forged = copy(original)
        object.__setattr__(forged, "typed_payload", empty_payload)
        candidates.append(forged)
        for forged in candidates:
            with pytest.raises(ContractValidationError):
                _source_use_append(adapter, forged) if forged.typed_payload is not empty_payload else TrancheCUnitOfWorkV1(
                    adapter, TransactionRetryPolicyV1(1)).append_source_use_control_v1(record=forged, expected_previous_record_ref=None)
            transaction = adapter.begin_transaction()
            try:
                with pytest.raises(ContractValidationError):
                    adapter.insert_receipt_record(transaction, forged)
            finally:
                transaction.rollback()
        assert _source_use_counts(adapter)["receipt_records"] == 1
    finally:
        if kind == "sqlite":
            adapter.close()


def _assert_source_use_failure_truth(kind, directory, monkeypatch):
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import PersistenceContractError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import PersistenceAvailabilityV1

    for failure in ("commit_before", "commit_after", "insert_rollback_failure"):
        adapter = _source_use_adapter(kind, directory / (kind + "-" + failure + ".db"), attempts=3)
        original = _source_use_record()
        primary = RuntimeError("synthetic primary failure")
        calls = []
        begin = adapter.begin_transaction
        def begin_injected():
            calls.append("begin")
            tx = begin()
            commit, rollback = tx.commit, tx.rollback
            def fail_commit():
                calls.append("commit")
                if failure == "commit_after":
                    commit()
                raise primary
            def traced_rollback():
                calls.append("rollback")
                rollback()
                if failure == "insert_rollback_failure":
                    raise RuntimeError("synthetic confidential cleanup detail")
            tx.commit, tx.rollback = fail_commit, traced_rollback
            return tx
        def fail_insert(*_args):
            raise primary
        try:
            with monkeypatch.context() as patch:
                patch.setattr(adapter, "begin_transaction", begin_injected)
                if failure == "insert_rollback_failure":
                    patch.setattr(adapter, "insert_receipt_record", fail_insert)
                with pytest.raises(RuntimeError) as caught:
                    _source_use_append(adapter, original, attempts=3)
                assert caught.value is primary
            assert calls.count("begin") == 1
            assert calls.count("rollback") == (0 if failure == "commit_after" else 1)
            assert _source_use_counts(adapter)["receipt_records"] == (1 if failure == "commit_after" else 0)
            assert adapter.availability is PersistenceAvailabilityV1.INTEGRITY_FAILURE
            if failure == "insert_rollback_failure":
                assert primary.__notes__ == ["source-use rollback failed; persistence integrity is unknown"]
            with pytest.raises(PersistenceContractError):
                adapter.load_committed_source_use_head_v1("synthetic-owner")
        finally:
            if kind == "sqlite":
                adapter.close()
    if kind == "sqlite":
        import sqlite3

        path = directory / "synthetic-source-use-busy.db"
        holder = _source_use_adapter(kind, path, attempts=3)
        contender = _source_use_adapter(kind, path, attempts=3)
        transaction = holder.begin_transaction()
        calls = []
        begin = contender.begin_transaction
        def counted_begin():
            calls.append("begin")
            return begin()
        try:
            with monkeypatch.context() as patch:
                patch.setattr(contender, "begin_transaction", counted_begin)
                with pytest.raises(PersistenceContractError) as caught:
                    _source_use_append(contender, _source_use_record(), attempts=3)
            assert caught.value.reason_code is ReasonCode.REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT
            assert isinstance(caught.value.__cause__, sqlite3.OperationalError)
            assert calls == ["begin"]
        finally:
            transaction.rollback()
            holder.close()
            contender.close()


def test_source_use_record_custody(reference_directory, monkeypatch) -> None:
    """Synthetic original custody on both reference adapters; no authentic intake."""
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import PersistenceAdapterV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import PersistenceContractError

    # Existing subclasses can retain the old abstract interface and deny the new feature.
    for name in ("load_committed_source_use_record_v1", "load_committed_source_use_head_v1",
                 "load_source_use_record_for_update_v1", "load_source_use_head_for_update_v1"):
        assert name not in PersistenceAdapterV1.__abstractmethods__
        reader = getattr(PersistenceAdapterV1, name)
        arguments = ((_source_use_record().record_id if "record" in name else "synthetic-owner"),)
        if "for_update" in name:
            arguments = (object(), *arguments)
        with pytest.raises(PersistenceContractError) as caught:
            reader(InMemoryPersistenceAdapterV1(), *arguments)
        assert caught.value.reason_code is ReasonCode.PERSISTENCE_UNAVAILABLE
    def no_transport(*_args, **_kwargs):
        raise AssertionError("synthetic custody must not construct a transport")
    with monkeypatch.context() as patch:
        patch.setattr("http.client.HTTPSConnection", no_transport)
        for kind in ("memory", "sqlite"):
            _assert_source_use_lifecycle(kind, reference_directory, monkeypatch)
            _assert_source_use_rejections(kind, reference_directory)
            _assert_source_use_failure_truth(kind, reference_directory, monkeypatch)


@pytest.fixture
def reference_directory():
    with TemporaryDirectory(prefix="qtt-st12c-") as directory:
        yield Path(directory)


def _amount(value: str, *, basis: str = "SETTLED") -> AccountingAmountV1:
    return AccountingAmountV1(value, "USD", "USD", basis, 2, "TEST::CENT")


def _accounts(*, second_basis: str = "SETTLED") -> dict[str, JournalAccountV1]:
    return {
        "cash": JournalAccountV1("cash", "ASSET", NormalBalanceV1.DEBIT, "USD", "USD", "SETTLED", "ACTIVE"),
        "clearing": JournalAccountV1("clearing", "LIABILITY", NormalBalanceV1.CREDIT, "USD", "USD", second_basis, "ACTIVE"),
    }


def _journal(*, credit: str = "1.00") -> tuple[JournalTransactionV1, tuple[JournalPostingV1, ...]]:
    postings = (
        JournalPostingV1("posting-debit", "journal-1", "cash", EntrySideV1.DEBIT, "1.00", "USD", "USD", "SETTLED", 2, NOW, NOW, "event-1"),
        JournalPostingV1("posting-credit", "journal-1", "clearing", EntrySideV1.CREDIT, credit, "USD", "USD", "SETTLED", 2, NOW, NOW, "event-1"),
    )
    return JournalTransactionV1("journal-1", "FILL", ("event-1",), tuple(row.posting_id for row in postings), NOW, NOW, "FILL_ACCEPTED", "DETERMINISTIC_FIXTURE"), postings


@pytest.mark.parametrize("case", ACCOUNTING_CASES, ids=lambda row: row.control_slug)
def test_accounting_contract_matrix(case) -> None:
    assert case.required_assertion_classes == ST12C_REQUIRED_ASSERTION_CLASSES
    assert case.adapter_applicability == ST12C_REFERENCE_ADAPTER_MATRIX
    assert case.expected_no_effect_flags == ST12C_NO_EFFECT_FLAGS
    assert all(flag.startswith("NO_") for flag in case.expected_no_effect_flags)
    assert validate_domain("accounting").passed

    slug = case.control_slug
    if slug == "capital-and-reserves":
        value = AccountingAndTCAServiceV1.deployable_capital(
            settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("10.00"),
            owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
            reconciliation_state=ReconciliationStateV1.RECONCILED,
        )
        mutated = AccountingAndTCAServiceV1.deployable_capital(
            settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("11.00"),
            owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
            reconciliation_state=ReconciliationStateV1.RECONCILED,
        )
        assert (value, mutated) == (Decimal("82.00"), Decimal("81.00"))
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.deployable_capital(
                settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("10.00", basis="PROJECTED"),
                owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
                reconciliation_state=ReconciliationStateV1.RECONCILED,
            )
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.deployable_capital(
                settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("-1.00"),
                owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
                reconciliation_state=ReconciliationStateV1.RECONCILED,
            )
    elif slug == "cash-state-separation":
        assert len(CASH_STATE_CLASS_REGISTRY) == 12
        assert len({row.value for row in CashStateClassV1}) == 12
        assert CashStateClassV1.UNREALIZED_PNL is not CashStateClassV1.SETTLED_SPENDABLE_CASH
        with pytest.raises(ValueError):
            CashStateClassV1("REALIZED_CASH")
        projected = CashStateProjectionV1("cash-p", CashStateClassV1.PROJECTED_EXECUTABLE_NET_CASH, "10.00", "USD", "PROJECTED", ("event",), ("journal",), NOW, NOW, ReconciliationStateV1.RECONCILED)
        settled = CashStateProjectionV1("cash-s", CashStateClassV1.SETTLED_SPENDABLE_CASH, "10.00", "USD", "SETTLED", ("event",), ("journal",), NOW, NOW, ReconciliationStateV1.RECONCILED)
        assert projected.cash_class is not settled.cash_class and projected.basis != settled.basis
    elif slug == "correction-and-reversal":
        journal, postings = _journal()
        bundle = build_journal_reversal_v1(
            original_transaction=journal, original_postings=postings,
            reversal_receipt_id="reversal-1", reversal_event_ref="event-reversal",
            reversal_transaction_id="journal-reversal", reversal_posting_ids=("reversal-debit", "reversal-credit"),
            requested_amount_by_original_posting=None, previously_reversed_by_original_posting={},
            reason_code="CORRECTION", authority_ref="OWNER", effective_at=NOW, recorded_at=NOW,
        )
        assert bundle.transaction.reversal_of_transaction_id == journal.journal_transaction_id
        assert all(row.decimal == 0 for row in bundle.receipt.remaining_reversible_amounts)
        with pytest.raises(ComputationControlPlaneError):
            build_journal_reversal_v1(
                original_transaction=journal, original_postings=postings,
                reversal_receipt_id="reversal-2", reversal_event_ref="event-reversal-2",
                reversal_transaction_id="journal-reversal-2", reversal_posting_ids=("r3", "r4"),
                requested_amount_by_original_posting={"posting-debit": "2", "posting-credit": "2"},
                previously_reversed_by_original_posting={}, reason_code="BAD", authority_ref="OWNER",
                effective_at=NOW, recorded_at=NOW,
            )
    elif slug == "cross-venue-conservation":
        transfer = CrossVenueTransferV1("transfer", "venue-a", "venue-b", _amount("10.00"), "posting-a", "posting-b", "PENDING_IN_TRANSIT")
        assert transfer.source_venue_ref != transfer.destination_venue_ref
        AccountingAndTCAServiceV1.validate_reserve_conservation(
            available_cash=_amount("60.00"), reserved_cash=_amount("20.00"), pending_cash=_amount("10.00"),
            owner_protected_cash=_amount("5.00"), quarantined_cash=_amount("5.00"), accepted_cash_basis=_amount("100.00"),
        )
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.validate_reserve_conservation(
                available_cash=_amount("60.00"), reserved_cash=_amount("20.00"), pending_cash=_amount("10.00"),
                owner_protected_cash=_amount("5.00"), quarantined_cash=_amount("4.00"), accepted_cash_basis=_amount("100.00"),
            )
    elif slug == "decimal-boundaries":
        assert exact_decimal("1.2500", field_name="money") == Decimal("1.2500")
        with pytest.raises(ComputationControlPlaneError):
            exact_decimal(1.25, field_name="money")
        with pytest.raises(ComputationControlPlaneError):
            AccountingAmountV1("+1.00", "USD", "USD", "SETTLED", 2, "TEST")
        with pytest.raises(ComputationControlPlaneError):
            AccountingAmountV1("1.0", "USD", "USD", "SETTLED", 2, "TEST")
    elif slug == "double-entry-conservation":
        journal, postings = _journal()
        AccountingAndTCAServiceV1.validate_journal(journal, postings, _accounts())
        bad_journal, bad_postings = _journal(credit="0.99")
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.validate_journal(bad_journal, bad_postings, _accounts())
    elif slug == "exposure-aggregation":
        projection = ExposureProjectionV1("exposure-1", (("VENUE_A|USD|PAYOUT_1|NET", "10"),), ("10",), ("position-1",), NOW, NOW)
        assert projection.signed_exposure_values == (Decimal("10"),)
        with pytest.raises(ComputationControlPlaneError):
            ExposureProjectionV1("bad", (("VENUE_A", "10"), ("VENUE_A", "10")), ("10", "-10"), ("p1",), NOW, NOW)
    elif slug == "fee-rebate-treatment":
        _assert_kalshi_rounding_values()
        _assert_kalshi_quadratic_taker_values()
        binding = FeeScheduleBindingV1("CATEGORY", "venue", "market-category", "v1", "source-epoch", datetime(2025, 1, 1, tzinfo=UTC), None, NOW, ("PLATFORM_FEE", "BUILDER_FEE_SEPARATE_ADDITIVE"), (("PLATFORM_FEE", ".05"),))
        policy = QuantizationPolicyV1("fee-5dp", "fee", "0.00001", QuantizationRoundingV1.HALF_EVEN, "USD", "USD", "FEE", 5, binding.binding_ref)
        fee = global_prediction_market_fee_v1(contracts="100", fee_rate=".05", price=".5", schedule_binding=binding, quantization_policy=policy, receipt_id="fee-r1")
        changed_binding = FeeScheduleBindingV1("CATEGORY-CHANGED", "venue", "market-category", "v2", "source-epoch-2", datetime(2025, 1, 1, tzinfo=UTC), None, NOW, ("PLATFORM_FEE", "BUILDER_FEE_SEPARATE_ADDITIVE"), (("PLATFORM_FEE", ".04"),))
        changed_policy = QuantizationPolicyV1("fee-5dp-changed", "fee", "0.00001", QuantizationRoundingV1.HALF_EVEN, "USD", "USD", "FEE", 5, changed_binding.binding_ref)
        changed = global_prediction_market_fee_v1(contracts="100", fee_rate=".04", price=".5", schedule_binding=changed_binding, quantization_policy=changed_policy, receipt_id="fee-r2")
        assert (fee.amount_after_rounding, changed.amount_after_rounding) == (Decimal("1.25000"), Decimal("1.00000"))
        with pytest.raises(ComputationControlPlaneError):
            global_prediction_market_fee_v1(contracts="100", fee_rate=".05", price=".5", schedule_binding=object(), quantization_policy=policy, receipt_id="bad")
        with pytest.raises(ComputationControlPlaneError):
            global_prediction_market_fee_v1(contracts="100", fee_rate=".04", price=".5", schedule_binding=binding, quantization_policy=policy, receipt_id="spoofed-rate")
    elif slug == "fill-branch-accounting":
        artifact = FillQuantityDistributionArtifactV1("distribution", "1", "source", "scope", 30, NOW, datetime(2027, 1, 1, tzinfo=UTC), "100", "0", (("0", ".2"), ("50", ".3"), ("100", ".5")))
        mutated = FillQuantityDistributionArtifactV1("distribution-2", "1", "source", "scope", 30, NOW, datetime(2027, 1, 1, tzinfo=UTC), "100", "0", (("0", ".3"), ("50", ".3"), ("100", ".4")))
        assert expected_partial_fill_quantity_v1(artifact=artifact) == Decimal("65")
        assert expected_partial_fill_quantity_v1(artifact=mutated) == Decimal("55")
        with pytest.raises(ComputationControlPlaneError):
            expected_partial_fill_quantity_v1(artifact=FillQuantityDistributionArtifactV1("bad", "1", "source", "scope", 30, NOW, datetime(2027, 1, 1, tzinfo=UTC), "100", "0", (("0", ".2"), ("100", ".7"))))
        fills = FillAccumulatorV1("100", (("fill-1", 1, NOW, "40", canonical_request_json_v1({"q": "40"})), ("fill-1", 1, NOW, "40", canonical_request_json_v1({"q": "40"}))))
        assert fills.filled_quantity == Decimal("40")
    elif slug == "pnl-classification":
        pnl = {CashStateClassV1.MARKED_PNL, CashStateClassV1.UNREALIZED_PNL, CashStateClassV1.REALIZED_EXIT_NET_CASH, CashStateClassV1.REALIZED_SETTLEMENT_NET_CASH}
        assert len(pnl) == 4 and CashStateClassV1.SETTLED_SPENDABLE_CASH not in pnl
    elif slug == "position-lifecycle":
        fill = PositionEventV1("accepted-fill", "cause-fill", PositionEventClassV1.ACCEPTED_FILL, 1, "10", "4.00", NOW, NOW, canonical_request_json_v1({"q": "10"}))
        position = project_position_v1(position_id="position-1", venue_ref="venue", market_ref="market", contract_ref="contract", outcome_or_side="YES", events=(fill, fill))
        assert position.event_refs == ("accepted-fill",)
        with pytest.raises(ComputationControlPlaneError):
            project_position_v1(position_id="position-2", venue_ref="venue", market_ref="market", contract_ref="contract", outcome_or_side="YES", events=())
    elif slug == "reconciliation":
        run = ReconciliationRunV1("run-1", ("projection",), "injected-snapshot", NOW, ("break",), ReconciliationStateV1.MATERIAL_BREAK, True)
        assert run.blocks_new_exposure
        with pytest.raises(ComputationControlPlaneError):
            ReconciliationRunV1("run-2", ("projection",), "snapshot", NOW, ("break",), ReconciliationStateV1.UNKNOWN, False)
    elif slug == "rounding-and-quantization":
        _assert_kalshi_rounding_boundaries()
        _assert_kalshi_quadratic_taker_boundaries()
        policy = QuantizationPolicyV1("cent", "amount", ".01", QuantizationRoundingV1.HALF_EVEN, "USD", "USD", "SETTLED", 2, "OWNER")
        receipt = quantize_decimal_v1("1.005", policy=policy, receipt_id="rounding-1")
        assert (receipt.pre_value, receipt.post_value, receipt.residual) == (Decimal("1.005"), Decimal("1.00"), Decimal("0.005"))
        with pytest.raises(ComputationControlPlaneError):
            quantize_decimal_v1(1.005, policy=policy, receipt_id="bad")
    elif slug == "settlement-resolution":
        assert CashStateClassV1.PENDING_CASH.value != CashStateClassV1.REALIZED_SETTLEMENT_NET_CASH.value
        assert CashStateClassV1.REALIZED_SETTLEMENT_NET_CASH.value != CashStateClassV1.SETTLED_SPENDABLE_CASH.value
        pending = CashStateProjectionV1("pending", CashStateClassV1.PENDING_CASH, "10.00", "USD", "CONTESTED", ("settlement-fixture",), ("journal",), NOW, NOW, ReconciliationStateV1.UNKNOWN)
        assert pending.reconciliation_state is ReconciliationStateV1.UNKNOWN and pending.cash_class is CashStateClassV1.PENDING_CASH
    elif slug == "tca-decomposition":
        attribution = tuple((name, CostEmbeddingV1.EXPLICIT) for name in ("spread_cost", "slippage_cost", "impact_cost", "fees", "rebates", "latency_cost", "adverse_selection_cost", "opportunity_cost", "other_declared_costs"))
        tca = TCADecompositionV1("tca-1", "decision", ("fill",), "1", "0", "0", "1", "-.25", "0", "0", "0", "0", "1.75", attribution)
        assert tca.total_cost == Decimal("1.75")
        with pytest.raises(ComputationControlPlaneError):
            TCADecompositionV1("bad", "decision", ("fill",), "1", "0", "0", "1", "-.25", "0", "0", "0", "0", "2", attribution)
    elif slug == "unit-and-basis":
        touches = binary_book_implied_asks_v1(
            snapshot=BinaryBookSnapshotV1(
                "book", "sequence", "source", "USD", "PAYOUT",
                ("0.40", "0.42"), ("0.50", "0.56"), "1", 5, 5,
                "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS",
                (ActivePriceGridRangeV1("0.00", "1.00", "0.01"),),
            )
        )
        assert (touches.yes_implied_ask, touches.no_implied_ask) == (Decimal("0.44"), Decimal("0.58"))
        journal, postings = _journal()
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.validate_journal(journal, postings, _accounts(second_basis="PROJECTED"))
    else:  # pragma: no cover - the meta-test makes this unreachable
        raise AssertionError(f"unhandled control case {slug}")


def _kalshi_integer_oracle(revenue, model_fee, increment, prior):
    """Independent integer microdollar oracle, with Euclidean signed division."""
    principal = Fraction(revenue) * 1_000_000
    fee_units = Fraction(model_fee) * 1_000_000
    grid = int(Fraction(increment) * 1_000_000)
    carried = int(Fraction(prior) * 1_000_000)
    whole, remainder = divmod(fee_units.numerator, fee_units.denominator)
    charged = whole + int(remainder != 0)
    balance_units, rounding = divmod(int(principal) - charged, grid)
    refunded = min((carried + rounding) // grid, (charged + rounding) // grid) * grid
    return tuple(Fraction(value, 1_000_000) for value in (
        charged, rounding, refunded, charged + rounding - refunded,
        balance_units * grid + refunded, carried + rounding - refunded,
    ))


def _kalshi_values(result):
    return tuple(getattr(result, field.name) for field in fields(result))


def _assert_kalshi_rounding_values():
    golden = (
        (("-.055", ".00363825", ".01", "0"), (".003639", ".001361", "0", ".005", "-.06", ".001361")),
        (("-.055", ".00363825", ".0001", "0"), (".003639", ".000061", "0", ".0037", "-.0587", ".000061")),
        (("-.004", "0", ".01", ".006"), ("0", ".006", "0", ".006", "-.01", ".012")),
        (("0", ".01", ".01", ".012"), (".01", "0", ".01", "0", "0", ".002")),
        ((".055", ".00363825", ".01", "0"), (".003639", ".001361", "0", ".005", ".05", ".001361")),
        (("0", "0", ".01", "0"), ("0", "0", "0", "0", "0", "0")),
    )
    for inputs, expected in golden:
        revenue, fee, grid, carry = map(Decimal, inputs)
        result = kalshi_fee_rounding_v1(
            revenue=revenue, model_fee=fee, balance_increment=grid,
            prior_rounding_overpayment=carry,
        )
        assert _kalshi_values(result) == tuple(map(Decimal, expected))
    for revenue, fee, grid, carry in product(
        map(Decimal, ("-10", "-.055", "-.004", "-.000001", "0", ".000001", ".055", "10")),
        map(Decimal, ("0", ".0000001", ".000001", ".00363825", ".01", "1.75")),
        map(Decimal, (".0001", ".01")),
        map(Decimal, ("0", ".000001", ".000099", ".004", ".009999", ".012")),
    ):
        before = tuple(value.as_tuple() for value in (revenue, fee, grid, carry))
        result = kalshi_fee_rounding_v1(
            revenue=revenue, model_fee=fee, balance_increment=grid,
            prior_rounding_overpayment=carry,
        )
        actual = _kalshi_values(result)
        assert tuple(map(Fraction, actual)) == _kalshi_integer_oracle(revenue, fee, grid, carry)
        trade, rounding, rebate, net, balance, after = map(Fraction, actual)
        assert 0 <= rounding < Fraction(grid)
        assert 0 <= trade - Fraction(fee) < Fraction(1, 1_000_000)
        assert net >= 0 and rebate >= 0 and after >= 0
        assert (rebate / Fraction(grid)).denominator == 1
        assert (balance / Fraction(grid)).denominator == 1
        assert balance == Fraction(revenue) - net
        assert Fraction(carry) + rounding == rebate + after
        assert all(value.as_tuple().exponent == -6 for value in actual)
        assert all(not value.is_signed() for value in actual if value.is_zero())
        assert before == tuple(value.as_tuple() for value in (revenue, fee, grid, carry))
        continued = kalshi_fee_rounding_v1(
            revenue=Decimal(0), model_fee=Decimal(".01"), balance_increment=grid,
            prior_rounding_overpayment=result.rounding_overpayment_after,
        )
        assert tuple(map(Fraction, _kalshi_values(continued))) == _kalshi_integer_oracle(
            Decimal(0), Decimal(".01"), grid, result.rounding_overpayment_after,
        )
    row = KalshiFeeRoundingInputV1(Decimal("-.055"), Decimal(".011"))
    assert not hasattr(row, "__dict__") and not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        row.revenue = Decimal(0)
    with pytest.raises(FrozenInstanceError):
        result.net_fee = Decimal(0)


def _assert_kalshi_rounding_boundaries():
    class DecimalSubclass(Decimal):
        pass

    valid = dict(revenue=Decimal("-.055"), model_fee=Decimal(".00363825"),
                 balance_increment=Decimal(".01"), prior_rounding_overpayment=Decimal(0))
    invalid_common = (
        *((value, ReasonCode.INVALID_NUMERIC_INPUT) for value in
          (True, False, 1, 0.01, "0.01", None, {}, DecimalSubclass("0.01"))),
        *((Decimal(value), ReasonCode.NONFINITE_NUMERIC_INPUT) for value in
          ("NaN", "sNaN", "Infinity", "-Infinity")),
        *((Decimal(value), ReasonCode.OUT_OF_DOMAIN) for value in
          ("-0", "-0.000000", "1e101", "1e-101", "0e-129", "0e129", "1." + "0" * 128)),
    )
    for name in valid:
        for value, reason in invalid_common:
            with pytest.raises(ComputationControlPlaneError) as rejected:
                kalshi_fee_rounding_v1(**{**valid, name: value})
            assert rejected.value.reason_code is reason
        with pytest.raises(TypeError):
            kalshi_fee_rounding_v1(**{key: value for key, value in valid.items() if key != name})
    for name, value in (
        ("revenue", Decimal(".0000001")),
        ("model_fee", Decimal("-.01")),
        ("balance_increment", Decimal(0)),
        ("balance_increment", Decimal(".001")),
        ("balance_increment", Decimal("-.01")),
        ("prior_rounding_overpayment", Decimal("-.01")),
        ("prior_rounding_overpayment", Decimal(".0000001")),
    ):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            kalshi_fee_rounding_v1(**{**valid, name: value})
        assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for name in ("revenue", "model_fee"):
        for value, reason in invalid_common:
            with pytest.raises(ComputationControlPlaneError) as rejected:
                KalshiFeeRoundingInputV1(**{key: value if key == name else valid[key] for key in ("revenue", "model_fee")})
            assert rejected.value.reason_code is reason
    for changes in (
        {"revenue": Decimal("-9.99e100"), "model_fee": Decimal("9.99e100")},
        {"revenue": Decimal(".000001"), "model_fee": Decimal(0),
         "prior_rounding_overpayment": Decimal("9" * 101 + "." + "9" * 6)},
    ):
        with pytest.raises(ComputationControlPlaneError) as rejected:
            kalshi_fee_rounding_v1(**{**valid, **changes})
        assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for revenue, fee in (("1." + "0" * 127, "1e-100"), ("1e100", "0e-128"), ("0e128", "0")):
        result = kalshi_fee_rounding_v1(**{**valid, "revenue": Decimal(revenue), "model_fee": Decimal(fee)})
        assert tuple(map(Fraction, _kalshi_values(result))) == _kalshi_integer_oracle(
            Decimal(revenue), Decimal(fee), valid["balance_increment"], valid["prior_rounding_overpayment"],
        )
    result = kalshi_fee_rounding_v1(**valid)
    for field in fields(result):
        for value, reason in (*invalid_common, (Decimal(".0000001"), ReasonCode.OUT_OF_DOMAIN)):
            with pytest.raises(ComputationControlPlaneError) as rejected:
                replace(result, **{field.name: value})
            assert rejected.value.reason_code is reason
        if field.name != "balance_change":
            with pytest.raises(ComputationControlPlaneError) as rejected:
                replace(result, **{field.name: Decimal("-.01")})
            assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    with pytest.raises(ComputationControlPlaneError) as rejected:
        replace(result, net_fee=Decimal(".006"))
    assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for precision, rounding in product((1, 7, 28), (ROUND_CEILING, ROUND_FLOOR)):
        with localcontext() as ambient:
            ambient.prec = precision
            ambient.rounding = rounding
            ambient.Emin, ambient.Emax = -2, 2
            ambient.traps[Inexact] = ambient.traps[Rounded] = True
            ambient.flags[Inexact] = True
            before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                      ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
            rounded = kalshi_fee_rounding_v1(**valid)
            assert _kalshi_values(rounded) == tuple(map(Decimal, (".003639", ".001361", "0", ".005", "-.06", ".001361")))
            KalshiFeeRoundingInputV1(valid["revenue"], valid["model_fee"])
            with pytest.raises(ComputationControlPlaneError):
                kalshi_fee_rounding_v1(**{**valid, "model_fee": Decimal("sNaN")})
            after = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                     ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
            assert before == after


def _kalshi_quadratic_integer_oracle(contracts, price, multiplier):
    """Independent integer hundredths-of-contract / ten-thousandths price law."""
    quantity_units, price_units = Fraction(contracts) * 100, Fraction(price) * 10_000
    assert quantity_units.denominator == price_units.denominator == 1
    q, p, m = quantity_units.numerator, price_units.numerator, Fraction(multiplier)
    return (
        Fraction(-q * p, 1_000_000),
        Fraction(7 * m.numerator * q * p * (10_000 - p), 10**12 * m.denominator),
    )


def _assert_kalshi_quadratic_taker_values():
    golden = (
        ("100", ".5", "1", "-50", "1.75"),
        ("100", ".5", "2", "-50", "3.50"),
        ("100", ".6", "1", "-60", "1.68"),
        (".1", ".55", "2.1", "-.055", ".00363825"),
        (".01", ".0001", "1", "-.000001", ".000000069993"),
        ("50", ".5", "1", "-25", ".875"),
        ("3.75", ".4321", ".5", "-1.620375", ".0322073836875"),
        ("1", ".5", "0", "-.5", "0"),
    )
    for quantity, price, multiplier, revenue, fee in golden:
        fill = KalshiQuadraticTakerBuyYesFillV1(Decimal(quantity), Decimal(price))
        result = kalshi_quadratic_taker_buy_yes_input_v1(fill=fill, fee_multiplier=Decimal(multiplier))
        assert type(result) is KalshiFeeRoundingInputV1
        assert (result.revenue, result.model_fee) == (Decimal(revenue), Decimal(fee))
        assert result.revenue.as_tuple().exponent == -6
        assert not result.model_fee.is_signed() if result.model_fee.is_zero() else result.model_fee > 0
    for quantity, price, multiplier in product(
        map(Decimal, (".01", ".1", "1", "3.75", "25", "100")),
        map(Decimal, (".0001", ".1", ".4321", ".5", ".55", ".9", ".9999")),
        map(Decimal, ("0", ".000001", ".5", "1", "2", "2.1")),
    ):
        fill = KalshiQuadraticTakerBuyYesFillV1(quantity, price)
        before = (quantity.as_tuple(), price.as_tuple(), multiplier.as_tuple())
        result = kalshi_quadratic_taker_buy_yes_input_v1(fill=fill, fee_multiplier=multiplier)
        expected = _kalshi_quadratic_integer_oracle(quantity, price, multiplier)
        assert (Fraction(result.revenue), Fraction(result.model_fee)) == expected
        complement = kalshi_quadratic_taker_buy_yes_input_v1(
            fill=replace(fill, yes_price=Decimal(1) - price), fee_multiplier=multiplier,
        )
        assert complement.model_fee == result.model_fee
        assert Fraction(complement.revenue) == -Fraction(quantity) * (1 - Fraction(price))
        for scaled in (
            kalshi_quadratic_taker_buy_yes_input_v1(fill=replace(fill, contracts=quantity * 2), fee_multiplier=multiplier),
            kalshi_quadratic_taker_buy_yes_input_v1(fill=fill, fee_multiplier=multiplier * 2),
        ):
            assert Fraction(scaled.model_fee) == expected[1] * 2
        for grid, carry in product(map(Decimal, (".01", ".0001")), map(Decimal, ("0", ".004", ".012"))):
            rounded = kalshi_fee_rounding_v1(
                revenue=result.revenue, model_fee=result.model_fee,
                balance_increment=grid, prior_rounding_overpayment=carry,
            )
            assert tuple(map(Fraction, _kalshi_values(rounded))) == _kalshi_integer_oracle(*expected, grid, carry)
        assert before == (fill.contracts.as_tuple(), fill.yes_price.as_tuple(), multiplier.as_tuple())
    fractional = kalshi_quadratic_taker_buy_yes_input_v1(
        fill=KalshiQuadraticTakerBuyYesFillV1(Decimal(".1"), Decimal(".55")), fee_multiplier=Decimal("2.1"),
    )
    for grid, expected_net, expected_balance in ((".01", ".005", "-.06"), (".0001", ".0037", "-.0587")):
        rounded = kalshi_fee_rounding_v1(
            revenue=fractional.revenue, model_fee=fractional.model_fee,
            balance_increment=Decimal(grid), prior_rounding_overpayment=Decimal(0),
        )
        assert (rounded.net_fee, rounded.balance_change) == (Decimal(expected_net), Decimal(expected_balance))
    trailing = KalshiQuadraticTakerBuyYesFillV1(Decimal("1.00"), Decimal(".50000"))
    assert kalshi_quadratic_taker_buy_yes_input_v1(fill=trailing, fee_multiplier=Decimal("1.000")) == KalshiFeeRoundingInputV1(Decimal("-.5"), Decimal(".0175"))
    assert tuple(field.name for field in fields(trailing)) == ("contracts", "yes_price")
    assert not hasattr(trailing, "__dict__")
    for name in ("contracts", "yes_price"):
        with pytest.raises(FrozenInstanceError):
            setattr(trailing, name, Decimal(0))


def _assert_kalshi_quadratic_taker_boundaries():
    class DecimalSubclass(Decimal):
        pass

    class FillSubclass(KalshiQuadraticTakerBuyYesFillV1):
        pass

    fill_values = dict(contracts=Decimal(1), yes_price=Decimal(".5"))
    fill = KalshiQuadraticTakerBuyYesFillV1(**fill_values)
    valid = dict(fill=fill, fee_multiplier=Decimal(1))
    invalid = (
        *((value, ReasonCode.INVALID_NUMERIC_INPUT) for value in (True, False, 1, .01, "1", None, {}, DecimalSubclass("1"))),
        *((Decimal(value), ReasonCode.NONFINITE_NUMERIC_INPUT) for value in ("NaN", "sNaN", "Infinity", "-Infinity")),
        *((Decimal(value), ReasonCode.OUT_OF_DOMAIN) for value in ("-0", "-0.00000", "1e101", "1e-101", "0e-129", "0e129", "1." + "0" * 128, "-1")),
    )
    for name in ("contracts", "yes_price", "fee_multiplier"):
        domain_values = {"contracts": ("0", ".001"), "yes_price": ("0", "1", ".00001"), "fee_multiplier": ()}
        domain = tuple((Decimal(value), ReasonCode.OUT_OF_DOMAIN) for value in domain_values[name])
        for value, reason in (*invalid, *domain):
            if name == "fee_multiplier":
                with pytest.raises(NumericDomainError) as rejected:
                    kalshi_quadratic_taker_buy_yes_input_v1(**{**valid, name: value})
            else:
                with pytest.raises(NumericDomainError) as rejected:
                    KalshiQuadraticTakerBuyYesFillV1(**{**fill_values, name: value})
                assert rejected.value.reason_code is reason
                # Bypass construction only to prove producer revalidation, not admission.
                malformed = object.__new__(KalshiQuadraticTakerBuyYesFillV1)
                for field, supplied in {**fill_values, name: value}.items():
                    object.__setattr__(malformed, field, supplied)
                with pytest.raises(NumericDomainError) as rejected:
                    kalshi_quadratic_taker_buy_yes_input_v1(**{**valid, "fill": malformed})
            assert rejected.value.reason_code is reason
    for bad in (None, {}, (Decimal(1), Decimal(".5")), FillSubclass(**fill_values), KalshiFeeRoundingInputV1(Decimal("-.5"), Decimal(0))):
        with pytest.raises(ContractValidationError) as rejected:
            kalshi_quadratic_taker_buy_yes_input_v1(**{**valid, "fill": bad})
        assert rejected.value.reason_code is ReasonCode.INVALID_CONTRACT
    for callable_, kwargs in ((KalshiQuadraticTakerBuyYesFillV1, fill_values), (kalshi_quadratic_taker_buy_yes_input_v1, valid)):
        for omitted in kwargs:
            with pytest.raises(TypeError):
                callable_(**{key: value for key, value in kwargs.items() if key != omitted})
        with pytest.raises(TypeError):
            callable_(**kwargs, unknown=True)
    with pytest.raises(TypeError):
        kalshi_quadratic_taker_buy_yes_input_v1(fill, Decimal(1))
    for quantity, price, multiplier in (("1e100", ".5", "1e100"), (".01", ".0001", "1e-100")):
        with pytest.raises(NumericDomainError) as rejected:
            kalshi_quadratic_taker_buy_yes_input_v1(
                fill=KalshiQuadraticTakerBuyYesFillV1(Decimal(quantity), Decimal(price)), fee_multiplier=Decimal(multiplier),
            )
        assert rejected.value.reason_code is ReasonCode.OUT_OF_DOMAIN
    for precision, rounding in product((1, 7, 28), (ROUND_CEILING, ROUND_FLOOR)):
        with localcontext() as ambient:
            ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax = precision, rounding, -2, 2
            ambient.traps[Inexact] = ambient.traps[Rounded] = True
            ambient.flags[Inexact] = True
            before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                      ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
            actual = kalshi_quadratic_taker_buy_yes_input_v1(
                fill=KalshiQuadraticTakerBuyYesFillV1(Decimal(".1"), Decimal(".55")), fee_multiplier=Decimal("2.1"),
            )
            assert (actual.revenue, actual.model_fee) == (Decimal("-.055"), Decimal(".00363825"))
            for bad, reason in invalid:
                with pytest.raises(NumericDomainError) as rejected:
                    kalshi_quadratic_taker_buy_yes_input_v1(fill=fill, fee_multiplier=bad)
                assert rejected.value.reason_code is reason
            for name in fill_values:
                with pytest.raises(NumericDomainError) as rejected:
                    KalshiQuadraticTakerBuyYesFillV1(**{**fill_values, name: Decimal("sNaN")})
                assert rejected.value.reason_code is ReasonCode.NONFINITE_NUMERIC_INPUT
            after = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                     ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
            assert before == after


def _atomic_records(*, credit: str = "1.00", claim_id: str = "claim-1", claim_key: str = "key-1", no_fill: bool = False):
    if no_fill:
        event = EconomicEventRecordV1("event-no-fill", "NO_FILL", "AccountingAndTCAServiceV1", "aggregate-no-fill", 1, NOW, NOW, ("fixture",), (), "FLAT", "FLAT", "DETERMINISTIC_FIXTURE")
        spine = EconomicReceiptEventSpineV1("receipt-no-fill", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, "cause-no-fill", "correlation-no-fill", "00-trace-no-fill", "trace-state", 1, "aggregate-no-fill", 1, "CONTRACT_ONLY", event)
        transition = StateTransitionReceiptV1("transition-no-fill", "aggregate-no-fill", "POSITION_STATE_MACHINE_V1", "FLAT", "NO_FILL", "FLAT", TransitionDispositionV1.REJECTED, "event-identity-no-fill", 0, 0, NOW, NOW, "NO_FILL", False)
        claim = IdempotencyClaimReceiptV1(claim_id, claim_key, "COMMAND", canonical_request_json_v1({"command": "no-fill"}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
        return TrancheCAtomicRecordSetV1(claim, (spine,), (event,), (), None, (), transition, "receipt-no-fill")
    journal, postings = _journal(credit=credit)
    amount = TypedEconomicAmountV1("1.00", "USD", "USD", "SETTLED", 2, "TEST::CENT")
    event = EconomicEventRecordV1("event-1", "FILL", "AccountingAndTCAServiceV1", "aggregate-1", 1, NOW, NOW, ("fixture",), (amount,), "FLAT", "OPEN", "DETERMINISTIC_FIXTURE")
    spine = EconomicReceiptEventSpineV1("receipt-1", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, "cause", "correlation", "00-trace", "trace-state", 1, "aggregate-1", 1, "CONTRACT_ONLY", event)
    transition = StateTransitionReceiptV1("transition-1", "aggregate-1", "POSITION_STATE_MACHINE_V1", "FLAT", "FILL", "OPEN", TransitionDispositionV1.ACCEPTED, "event-identity", 0, 1, NOW, NOW, "ACCEPTED", False)
    claim = IdempotencyClaimReceiptV1(claim_id, claim_key, "COMMAND", canonical_request_json_v1({"command": "one"}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
    lineage = ValueLineageEdgeV1(
        "lineage-1", "receipt-1", "typed_payload", "event-1", "typed_amounts[0]",
        "1.00", "1.00", "USD", "USD", "SETTLED", "SETTLED", "IDENTITY", "MATERIAL",
        NOW, NOW, "cause-lineage", "correlation-lineage", "node-receipt", "node-event",
        "IDENTITY_NO_CONVERSION",
    )
    return TrancheCAtomicRecordSetV1(claim, (spine,), (event,), (lineage,), journal, postings, transition, "receipt-1")


def _reversal_atomic_records(
    *,
    suffix: str = "atomic",
    claim_key: str = "key-reversal",
    request_token: str = "full",
    requested_amount: str | None = None,
    previously_reversed: str | None = None,
    aggregate_version: int = 2,
    original_transaction: JournalTransactionV1 | None = None,
    original_postings: tuple[JournalPostingV1, ...] | None = None,
    reversal_transaction_id: str | None = None,
    remaining_override: str | None = None,
) -> TrancheCAtomicRecordSetV1:
    if original_transaction is None or original_postings is None:
        original_transaction, original_postings = _journal()
    event_id = f"event-reversal-{suffix}"
    transaction_id = reversal_transaction_id or f"journal-reversal-{suffix}"
    requested = (
        None
        if requested_amount is None
        else {
            posting.posting_id: requested_amount
            for posting in original_postings
        }
    )
    prior = (
        {}
        if previously_reversed is None
        else {
            posting.posting_id: previously_reversed
            for posting in original_postings
        }
    )
    bundle = build_journal_reversal_v1(
        original_transaction=original_transaction,
        original_postings=original_postings,
        reversal_receipt_id=f"reversal-{suffix}",
        reversal_event_ref=event_id,
        reversal_transaction_id=transaction_id,
        reversal_posting_ids=tuple(
            f"reversal-{suffix}-{index}"
            for index in range(len(original_postings))
        ),
        requested_amount_by_original_posting=requested,
        previously_reversed_by_original_posting=prior,
        reason_code="CORRECTION",
        authority_ref="OWNER_FIXTURE",
        effective_at=NOW,
        recorded_at=NOW,
    )
    reversal_receipt = bundle.receipt
    if remaining_override is not None:
        reversal_receipt = replace(
            reversal_receipt,
            remaining_reversible_amounts=tuple(
                AccountingAmountV1(
                    remaining_override,
                    posting.currency_or_asset,
                    posting.ledger_unit,
                    posting.basis,
                    posting.scale,
                    "IDENTITY_FROM_ORIGINAL_POSTING",
                )
                for posting in original_postings
            ),
        )
    amount = TypedEconomicAmountV1("1.00", "USD", "USD", "SETTLED", 2, "TEST::CENT")
    event = EconomicEventRecordV1(event_id, "CORRECTION", "AccountingAndTCAServiceV1", "aggregate-1", aggregate_version, NOW, NOW, (original_transaction.journal_transaction_id,), (amount,), "OPEN", "OPEN", "DETERMINISTIC_FIXTURE")
    spine = EconomicReceiptEventSpineV1(f"receipt-reversal-{suffix}", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, f"cause-reversal-{suffix}", f"correlation-reversal-{suffix}", f"00-trace-reversal-{suffix}", "trace-state", aggregate_version, "aggregate-1", aggregate_version, "CONTRACT_ONLY", event)
    transition = StateTransitionReceiptV1(f"transition-reversal-{suffix}", "aggregate-1", "POSITION_STATE_MACHINE_V1", "OPEN", "CORRECTION", "OPEN", TransitionDispositionV1.ACCEPTED, f"event-identity-reversal-{suffix}", aggregate_version - 1, aggregate_version, NOW, NOW, "CORRECTION", False)
    claim = IdempotencyClaimReceiptV1(f"claim-reversal-{suffix}", claim_key, "REVERSAL", canonical_request_json_v1({"command": "reverse", "original": original_transaction.journal_transaction_id, "request": request_token}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
    return TrancheCAtomicRecordSetV1(
        claim, (spine,), (event,), (), bundle.transaction, bundle.postings,
        transition, f"receipt-reversal-{suffix}", reversal_links=(reversal_receipt,),
    )


@pytest.mark.parametrize("adapter_kind", ("memory", "sqlite"))
def test_reference_adapter_atomic_commit_rollback_and_replay(adapter_kind, reference_directory) -> None:
    adapter = (
        InMemoryPersistenceAdapterV1()
        if adapter_kind == "memory"
        else SQLiteReferenceAdapterV1(reference_directory / "reference.db", busy_timeout_ms=0, max_transaction_attempts=1)
    )
    unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
    committed = unit.execute(unit_of_work_id="uow-1", records=_atomic_records(), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    original_before_reversal = deterministic_json(adapter.get_record("journal-1"))
    reversed_receipt = unit.execute(unit_of_work_id="uow-reversal", records=_reversal_atomic_records(), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    replayed = unit.execute(unit_of_work_id="uow-2", records=_atomic_records(), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    duplicate_delivery = unit.execute(unit_of_work_id="uow-3", records=_atomic_records(claim_id="claim-2", claim_key="key-2"), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    no_fill = unit.execute(unit_of_work_id="uow-no-fill", records=_atomic_records(claim_id="claim-no-fill", claim_key="key-no-fill", no_fill=True), accounts={}, started_at=NOW, completed_at=NOW)
    assert committed.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert reversed_receipt.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert replayed.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert duplicate_delivery.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert no_fill.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert replayed.committed_record_refs == ("receipt-1",)
    assert adapter.get_idempotency_result("key-1") == "receipt-1"
    assert adapter.get_idempotency_result("key-2") == "receipt-1"
    assert adapter.get_idempotency_result("key-no-fill") == "receipt-no-fill"
    assert deterministic_json(adapter.get_record("journal-1")) == original_before_reversal
    assert adapter.get_record("reversal-atomic") is not None
    assert len(adapter.reconstruct_as_of(effective_cutoff=NOW, recorded_cutoff=NOW, aggregate_scope=())) == 17
    assert len(adapter.reconstruct_as_of(effective_cutoff=NOW, recorded_cutoff=NOW, aggregate_scope=("aggregate-1",))) == 6
    assert deterministic_json(adapter.get_record("receipt-1")) == deterministic_json(_atomic_records().receipt_records[0])
    with pytest.raises(ComputationControlPlaneError):
        replace(
            _atomic_records(claim_id="claim-circular", claim_key="key-circular"),
            optional_outbox_intent=OutboxIntentRecordV1(
                "outbox-circular", "NO_WRITE", "aggregate-1", "outbox-circular", NOW
            ),
        )
    if hasattr(adapter, "close"):
        adapter.close()

    if adapter_kind == "sqlite":
        contention_path = reference_directory / "contention.db"
        holder = SQLiteReferenceAdapterV1(contention_path, busy_timeout_ms=0, max_transaction_attempts=1)
        contender = SQLiteReferenceAdapterV1(contention_path, busy_timeout_ms=0, max_transaction_attempts=1)
        holder_transaction = holder.begin_transaction()
        holder.acquire_idempotency_claim(
            holder_transaction,
            _atomic_records(claim_id="claim-holder", claim_key="key-contention").idempotency_claim,
        )
        contention = TrancheCUnitOfWorkV1(contender, TransactionRetryPolicyV1(1)).execute(
            unit_of_work_id="uow-contention",
            records=_atomic_records(claim_id="claim-contender", claim_key="key-contention"),
            accounts=_accounts(),
            started_at=NOW,
            completed_at=NOW,
        )
        assert contention.transaction_state is TransactionTerminalStateV1.RETRY_EXHAUSTED
        assert contender.get_idempotency_result("key-contention") is None
        holder_transaction.rollback()
        holder.close()
        contender.close()

    rollback_adapter = (
        InMemoryPersistenceAdapterV1()
        if adapter_kind == "memory"
        else SQLiteReferenceAdapterV1(reference_directory / "rollback.db", busy_timeout_ms=0, max_transaction_attempts=1)
    )
    rolled_back = TrancheCUnitOfWorkV1(rollback_adapter, TransactionRetryPolicyV1(1)).execute(
        unit_of_work_id="uow-bad", records=_atomic_records(credit="0.99"), accounts=_accounts(), started_at=NOW, completed_at=NOW
    )
    assert rolled_back.transaction_state is TransactionTerminalStateV1.ROLLED_BACK
    assert rollback_adapter.get_record("receipt-1") is None
    assert rollback_adapter.get_idempotency_result("key-1") is None
    if hasattr(rollback_adapter, "close"):
        rollback_adapter.close()

    _assert_f13_reference_storage(adapter_kind, reference_directory)
    _assert_f13_transaction_truth(adapter_kind, reference_directory)
    _assert_f14_native_and_storage(adapter_kind)
    if adapter_kind == 'memory':
        _assert_kalshi_observation_custody()



@contextmanager
def _synthetic_kalshi_observation(*, bodies=None, headers=None, status=200, on_read=None,
                                 on_send=None, on_close=None, on_tls=None, fills=None,
                                 balance_increment=Decimal('.01'), prior_rounding_overpayment=Decimal(0),
                                 source_lifetime=60, use_lifetime=60):
    """Real signed synthetic issuer plus offline transport; no native qualification."""
    import ssl
    from datetime import timedelta
    from types import SimpleNamespace
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import SourceUseObservationRequestV1
    from tests.stage1_prediction_markets.qku_computation_control_plane.security.test_deserialization_safety import _synthetic_source_use_root

    moment = datetime(2026, 10, 20, 12, tzinfo=UTC)
    delta = moment - datetime(1970, 1, 1, tzinfo=UTC)
    clock = dict(wall=(delta.days * 86400 + delta.seconds) * 1_000_000_000, mono=10_000_000_000)
    raw = bodies if bodies is not None else (
        b'{"market":{"ticker":"SYNTHETIC::MARKET","event_ticker":"SYNTHETIC::EVENT"}}',
        b'{"event":{"event_ticker":"SYNTHETIC::EVENT","series_ticker":"SYNTHETIC::SERIES","fee_type_override":null,"fee_multiplier_override":null}}',
        b'{"series":{"ticker":"SYNTHETIC::SERIES","fee_type":"quadratic","fee_multiplier":1}}',
    )
    kwargs = {}
    harness = SimpleNamespace(clock=clock, bodies=raw, kwargs=kwargs, connections=[], sends=[], closes=[], reads=[], tls_preparations=[], owner=None)
    real_context = ssl.create_default_context

    def create_context():
        harness.tls_preparations.append(len(harness.tls_preparations))
        context = real_context()
        if on_tls is not None:
            on_tls(harness, harness.tls_preparations[-1])
        return context

    class Response:
        def __init__(self, index):
            self.index = index
            self.status = status

        def getheaders(self):
            return headers if headers is not None else [('Content-Type', 'application/json'), ('Content-Length', str(len(raw[self.index])))]

        def read(self, limit):
            harness.reads.append((self.index, limit))
            assert limit == 65_537
            if on_read is not None:
                on_read(harness, self.index)
            return raw[self.index]

    class Connection:
        def __init__(self, host, port, *, timeout, context):
            self.index = len(harness.connections)
            harness.connections.append((host, port, timeout, context))
            assert host == 'external-api.kalshi.com' and port == 443
            assert 0 < timeout <= 20 and context.check_hostname is True and context.verify_mode == ssl.CERT_REQUIRED

        def request(self, method, target, *, body, headers):
            harness.sends.append((method, target, body, dict(headers)))
            if on_send is not None:
                on_send(harness, self.index)

        def getresponse(self):
            return Response(self.index)

        def close(self):
            harness.closes.append(self.index)
            if on_close is not None:
                on_close(harness, self.index)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("http.client.HTTPSConnection", Connection)
        patch.setattr(ssl, 'create_default_context', create_context)
        patch.setattr(source.time, 'time_ns', lambda: clock['wall'])
        patch.setattr(source.time, 'monotonic_ns', lambda: clock['mono'])
        with _synthetic_source_use_root() as issuer:
            scope, review, facts, declaration = _source_use_action_proposals(moment)
            facts = replace(facts, source_expires_at_utc=moment + timedelta(seconds=source_lifetime))
            review = replace(review, claimed_expires_at_utc=facts.source_expires_at_utc)
            declaration = replace(declaration, claimed_expires_at_utc=moment + timedelta(seconds=use_lifetime))
            reviewed = issuer.sign(dict(action='REVIEW_ACCEPT', scope=scope, original=review, review_facts=facts,
                requested_expires_at_utc=facts.source_expires_at_utc))
            used = issuer.sign(dict(action='USE_ADMIT', scope=scope, original=declaration,
                expected_review_ref=reviewed.review.record_id,
                requested_expires_at_utc=min(facts.source_expires_at_utc, declaration.claimed_expires_at_utc)))
            financial_fills = fills if fills is not None else (KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal('.5')),)

            def authorize(*, via_controller=False):
                if harness.owner is not None:
                    harness.owner.revoke()
                request = SourceUseObservationRequestV1('SYNTHETIC::MARKET', financial_fills,
                    balance_increment, prior_rounding_overpayment,
                    moment + timedelta(seconds=min(50, source_lifetime, use_lifetime)), 50_000_000_000)
                observed = issuer.sign(dict(action='OBSERVE_ONCE', scope=scope,
                    expected_declaration_ref=used.declaration.record_id,
                    expected_review_ref=used.review.record_id, observation=request), via_controller=via_controller)
                if via_controller:
                    return observed
                binding = next(value for value in issuer.authority._bindings.values()
                    if value._permit is not None and value._permit._event.record_id == observed.event.record_id)
                kwargs.update(source_receipt=binding._source, rights_receipt=binding._rights,
                    account_scope=scope.account_scope_ref, internal_use_class=scope.internal_use_class,
                    permitted_retention_class=scope.permitted_retention_class, expected_market_ticker=request.market_ticker,
                    process_epoch_id=issuer.authority._process_ref, monotonic_clock_id=issuer.authority._clock_ref,
                    operating_authorization_ref=observed.event.record_id, authorization_expires_at_utc=request.expires_at_utc,
                    deadline_monotonic_ns=binding._permit._deadline, source_use_binding=binding)
                return kwargs

            harness.authorize, harness.issuer = authorize, issuer
            harness.owner = source.KalshiFeeObservationOwnerV1(**authorize())
            yield harness
            assert harness.closes == list(range(len(harness.connections)))


def _assert_kalshi_observation_custody():
    from copy import copy
    from dataclasses import fields
    from datetime import timedelta
    from inspect import Parameter, signature
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError, ContractValidationError, PointInTimeError

    owner_type = source.KalshiFeeObservationOwnerV1

    def reject_reinitialization(h):
        state, attempts, cohort = h.owner._state, h.owner._attempts, h.owner._issued_cohort
        with pytest.raises(ContractValidationError):
            h.owner.__init__(**h.kwargs)
        assert h.owner._state == state and h.owner._attempts == attempts
        assert h.owner._issued_cohort is cohort

    with _synthetic_kalshi_observation() as h:
        assert all(p.kind is Parameter.KEYWORD_ONLY and p.default is Parameter.empty
                   for name, p in signature(owner_type).parameters.items() if name != 'source_use_binding')
        assert signature(owner_type).parameters['source_use_binding'].default is None
        assert set(signature(owner_type).parameters) == set(h.kwargs)
        assert not h.connections and h.owner._state == 'NEW'
        reject_reinitialization(h)
        for impostor in (copy(h.owner), object.__new__(owner_type)):
            with pytest.raises(ContractValidationError):
                impostor.capture()
            with pytest.raises(ContractValidationError):
                impostor.revoke()
        assert not h.connections and h.owner._state == 'NEW'
        cohort = h.owner.capture()
        assert h.owner._state == 'READY' and h.owner._issued_cohort is cohort and h.owner._pending is None
        assert h.owner._attempts == 3 and len(h.sends) == 3
        reject_reinitialization(h)
        assert [row[1] for row in h.sends] == [
            '/trade-api/v2/markets/SYNTHETIC%3A%3AMARKET',
            '/trade-api/v2/events/SYNTHETIC%3A%3AEVENT?exclude_markets=true',
            '/trade-api/v2/series/SYNTHETIC%3A%3ASERIES']
        assert all(row[0] == 'GET' and row[2] is None and row[3] == {
            'Accept': 'application/json', 'Accept-Encoding': 'identity', 'Connection': 'close'} for row in h.sends)
        assert all(row.raw_body is raw for row, raw in zip(cohort.observations, h.bodies))
        assert cohort.fee_multiplier == Decimal(1) and cohort.fee_basis == 'OBSERVED_SERIES_BASE'
        assert all(row.request_wall_ns == row.received_wall_ns == h.clock['wall']
                   and row.request_monotonic_ns == row.received_monotonic_ns == h.clock['mono'] for row in cohort.observations)
        query = dict(cohort=cohort, expected_market_ticker='SYNTHETIC::MARKET', as_of_monotonic_ns=cohort.available_monotonic_ns)
        copied_owner = copy(h.owner)
        with pytest.raises(ContractValidationError):
            copied_owner.resolve_scenario_multiplier(**query)
        assert h.owner.resolve_scenario_multiplier(**query) is cohort.fee_multiplier
        for supplied in (copy(cohort), replace(cohort), replace(cohort, process_epoch_id='OTHER'), replace(cohort, monotonic_clock_id='OTHER'), object()):
            with pytest.raises(ContractValidationError):
                h.owner.resolve_scenario_multiplier(**{**query, 'cohort': supplied})
        for value in (cohort.available_monotonic_ns-1, h.clock['mono']+1, True, 1.5, -1, 2**63):
            with pytest.raises(PointInTimeError):
                h.owner.resolve_scenario_multiplier(**{**query, 'as_of_monotonic_ns': value})
        with pytest.raises(ContractValidationError) as mismatch:
            h.owner.resolve_scenario_multiplier(**{**query, 'expected_market_ticker': 'OTHER'})
        assert mismatch.value.reason_code is source.ReasonCode.INPUT_SCOPE_MISMATCH
        with pytest.raises(ContractValidationError):
            h.owner.capture()
        with pytest.raises(ComputationControlPlaneError):
            owner_type(**h.kwargs)
        other = owner_type(**{**h.kwargs, 'source_use_binding': None})
        with pytest.raises(ContractValidationError):
            other.resolve_scenario_multiplier(**query)
        other.revoke()
        h.owner.revoke(); h.owner.revoke()
        reject_reinitialization(h)
        with pytest.raises(ContractValidationError):
            copied_owner.resolve_scenario_multiplier(**query)
        with pytest.raises(ContractValidationError):
            h.owner.resolve_scenario_multiplier(**query)
        assert len(h.sends) == 3 and cohort.observations[0].raw_body is h.bodies[0]
        baseline = h.bodies

    def failed_capture(**kwargs):
        with _synthetic_kalshi_observation(**kwargs) as h:
            with pytest.raises(ComputationControlPlaneError) as failure:
                h.owner.capture()
            assert h.owner._state in ('FAILED', 'REVOKED') and h.owner._issued_cohort is None
            assert h.owner._pending is None
            reject_reinitialization(h)
            before = len(h.connections)
            with pytest.raises(ContractValidationError):
                h.owner.capture()
            assert len(h.connections) == before
            assert 'PRIVATE_TRANSPORT_TEXT' not in str(failure.value)
            return before, len(h.sends), failure.value

    for body_index, body, expected_sends in (
        (0, baseline[0].replace(b'SYNTHETIC::MARKET', b'OTHER'), 1),
        (0, b'{"market":{}}', 1), (0, b'{"market":null}', 1),
        (0, baseline[0][:-1] + b',"access_token":"SECRET"}', 1),
        (1, baseline[1].replace(b'SYNTHETIC::EVENT', b'OTHER'), 2),
        (1, b'{"event":{}}', 2),
        (2, baseline[2].replace(b'SYNTHETIC::SERIES', b'OTHER'), 3),
        (2, baseline[2].replace(b'quadratic', b'linear'), 3),
        (2, baseline[2].replace(b':1}', b':-1}'), 3),
    ):
        bodies = list(baseline); bodies[body_index] = body
        assert failed_capture(bodies=tuple(bodies))[1] == expected_sends
    for index in (0, 1):
        for token in (b'1', b'true', b'null'):
            bodies = list(baseline)
            bodies[index] = bodies[index][:-2] + b',"exchange_index":' + token + b'}}'
            assert failed_capture(bodies=tuple(bodies))[1] == index + 1
    for value in (b'"2000-01-01T00:00:00Z"', b'false', b'0'):
        bodies = (baseline[0][:-2]+b',"fee_waiver_expiration_time":'+value+b'}}', *baseline[1:])
        assert failed_capture(bodies=bodies)[1] == 3
    for invalid in (b'{}', b'null', b'\xff', b'{"market":{"ticker":NaN}}', b'x'*65_537):
        assert failed_capture(bodies=(invalid,*baseline[1:]))[1] == 1
    for status in (True, 199, 201, 301, 304, 401, 429, 500):
        assert failed_capture(status=status)[1] == 1
    normal = [('Content-Type', 'application/json')]
    for headers in (
        [], [('Content-Type', 'text/html')], normal*2,
        [('Content-Type', 'application/json;charset=ascii')], [('Content-Type', 'application/json;foo=utf-8')],
        normal+[('Content-Encoding','gzip')], normal+[('Content-Encoding','identity')]*2,
        normal+[('Transfer-Encoding','gzip')], normal+[('Transfer-Encoding','chunked')]*2,
        normal+[('Transfer-Encoding','chunked'),('Content-Length','1')],
        normal+[('Content-Length','1')]*2,
        *(normal+[('Content-Length', value)] for value in ('0','-1','+1',' 1','1 ','1,1','65537','9'*1000,'１','1')),
        normal+[('Other','x')]*100, normal+[('Other','x'*65_536)], normal+[('Other','\u2603')],
    ):
        assert failed_capture(headers=headers)[1] == 1
    for headers in (normal, [('Content-Type','APPLICATION/JSON; charset="UTF-8"'),('Transfer-Encoding','CHUNKED')],
                    normal+[('Content-Encoding','identity'),('Set-Cookie','ignored')]):
        with _synthetic_kalshi_observation(headers=headers) as h:
            assert h.owner.capture().fee_multiplier == 1
            assert all('Cookie' not in row[3] for row in h.sends)
    for key, replacement in (('event_ticker', b'fee_changes'), ('event_ticker', b'..')):
        assert failed_capture(bodies=(baseline[0].replace(b'SYNTHETIC::EVENT', replacement),*baseline[1:]))[1] == 1
    with _synthetic_kalshi_observation(bodies=tuple(row.replace(b'SYNTHETIC::EVENT',b'E/%2F?#') for row in baseline)) as h:
        assert h.owner.capture().event_ticker == 'E/%2F?#'
        assert h.sends[1][1] == '/trade-api/v2/events/E%2F%252F%3F%23?exclude_markets=true'

    for change in (
        lambda k: {'source_receipt': object()}, lambda k: {'rights_receipt': object()},
        lambda k: {'source_receipt': replace(k['source_receipt'], source_id='OTHER')},
        lambda k: {'source_receipt': replace(k['source_receipt'], source_contract_version='OTHER')},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], source_id='OTHER')},
        lambda k: {'source_receipt': replace(k['source_receipt'], profile_id=source.Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT)},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], profile_id=source.Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT)},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], internal_use_class='OTHER')},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], permitted_retention_class='OTHER')},
        lambda k: {'internal_use_class':'OTHER'}, lambda k: {'permitted_retention_class':'OTHER'},
        lambda k: {'account_scope':'OTHER'}, lambda k: {'operating_authorization_ref':''},
        lambda k: {'authorization_expires_at_utc':datetime(2026,10,20,12,tzinfo=UTC)},
        lambda k: {'authorization_expires_at_utc':datetime(2026,10,20,12)},
        lambda k: {'deadline_monotonic_ns':10_000_000_000}, lambda k: {'deadline_monotonic_ns':70_000_000_001},
        lambda k: {'deadline_monotonic_ns':True}, lambda k: {'expected_market_ticker':'..'},
        lambda k: {'source_receipt':replace(k['source_receipt'], checked_at_utc=datetime(2026,10,18,tzinfo=UTC), effective_at_utc=datetime(2026,10,18,tzinfo=UTC))},
    ):
        with _synthetic_kalshi_observation() as h:
            with pytest.raises(ComputationControlPlaneError):
                owner_type(**{**h.kwargs, **change(h.kwargs)})
            assert not h.tls_preparations and not h.connections and not h.sends
    class OwnerSubclass(owner_type):
        pass
    class SourceSubclass(source.PITSourceCurrentizationReceiptV1):
        pass
    class RightsSubclass(source.PITRightsAdmissionReceiptV1):
        pass
    with _synthetic_kalshi_observation() as h:
        with pytest.raises(ContractValidationError):
            OwnerSubclass(**h.kwargs)
        for key, subtype in (('source_receipt', SourceSubclass), ('rights_receipt', RightsSubclass)):
            original = h.kwargs[key]
            subclass_receipt = subtype(**{field.name: getattr(original, field.name) for field in fields(original)})
            with pytest.raises(ContractValidationError):
                owner_type(**{**h.kwargs, key: subclass_receipt})
        assert not h.tls_preparations and not h.connections and not h.sends
    def timeout(h, index):
        raise TimeoutError('PRIVATE_TRANSPORT_TEXT')
    for hook in ('on_read','on_send','on_close'):
        result = failed_capture(**{hook:timeout})
        assert result[1] == 1 and str(result[2]).endswith('KALSHI_OBSERVATION_TRANSPORT')
    def late(h,index):
        h.clock['mono'] = h.kwargs['deadline_monotonic_ns']
    def backward(h,index):
        h.clock['wall'] -= 1
    def backward_monotonic(h,index):
        h.clock['mono'] -= 1
    def revoke(h,index):
        h.owner.revoke()
    for hook in (late,backward,backward_monotonic,revoke):
        assert failed_capture(on_read=hook)[1] == 1
    for samples in ((9_999_999_999, 10_000_000_000), (10_000_000_001, 10_000_000_000)):
        with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
            clock_samples = iter(samples)
            patch.setattr(source.time, 'monotonic_ns', lambda: next(clock_samples))
            with pytest.raises(PointInTimeError):
                h.owner.capture()
            assert h.owner._state == 'FAILED' and h.owner._issued_cohort is None
            assert not h.tls_preparations and not h.connections and not h.sends
    def slow_tls(h, index):
        h.clock['mono'] = h.kwargs['deadline_monotonic_ns'] - 1_000_000_000
    with _synthetic_kalshi_observation(on_tls=slow_tls) as h:
        assert h.owner.capture().fee_multiplier == 1
        assert [row[2] for row in h.connections] == [1.0, 1.0, 1.0]
    with _synthetic_kalshi_observation(on_tls=late) as h:
        with pytest.raises(PointInTimeError):
            h.owner.capture()
        assert h.tls_preparations == [0] and not h.connections and not h.sends
        assert h.owner._state == 'FAILED' and h.owner._issued_cohort is None
    with _synthetic_kalshi_observation() as h:
        h.owner.revoke()
        with pytest.raises(ContractValidationError):
            h.owner.capture()
        assert not h.connections
    for expired in ('mono','wall'):
        with _synthetic_kalshi_observation() as h:
            cohort = h.owner.capture()
            if expired == 'mono':
                h.clock['mono'] = h.kwargs['deadline_monotonic_ns']
            else:
                h.clock['wall'] += 50_000_000_000
            with pytest.raises(PointInTimeError):
                h.owner.resolve_scenario_multiplier(cohort=cohort, expected_market_ticker=cohort.market_ticker,
                                                   as_of_monotonic_ns=cohort.available_monotonic_ns)
            assert h.owner._state == 'FAILED'
    with _synthetic_kalshi_observation() as h:
        real_link = source.decode_kalshi_market_linked_series_fee_candidate_v1
        def slow_link(**kwargs):
            result = real_link(**kwargs)
            h.clock['mono'] = h.kwargs['deadline_monotonic_ns']
            return result
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(source, 'decode_kalshi_market_linked_series_fee_candidate_v1', slow_link)
            with pytest.raises(PointInTimeError):
                h.owner.capture()
        assert len(h.sends) == 3 and h.owner._issued_cohort is None
    def interrupt(h,index):
        raise KeyboardInterrupt()
    with _synthetic_kalshi_observation(on_read=interrupt) as h:
        with pytest.raises(KeyboardInterrupt):
            h.owner.capture()
        assert h.owner._state == 'FAILED' and h.owner._issued_cohort is None

    _assert_kalshi_scenario_session()


def _assert_kalshi_scenario_session():
    from copy import copy
    from datetime import timedelta
    from inspect import Parameter, signature
    from src.qtt.pretrade import pr169_pretrade1_resolvers as pretrade
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import PointInTimeError

    session_type = pretrade.KalshiFeeScenarioSessionV1
    result_type = pretrade.KalshiObservedFeeScenarioResultV1
    fills = (KalshiQuadraticTakerBuyYesFillV1(Decimal(100), Decimal('.5')),)
    inputs = dict(fills=fills, balance_increment=Decimal('.01'), prior_rounding_overpayment=Decimal(0))

    def start(h, **changes):
        h.session = session_type(**{**h.authorize(), **changes})
        h.owner = h.session._KalshiFeeScenarioSessionV1__owner
        assert type(h.owner) is source.KalshiFeeObservationOwnerV1
        return h.session

    def state(session):
        return session._KalshiFeeScenarioSessionV1__state

    def terminal(h, expected):
        assert state(h.session) == expected
        assert h.owner._pending is None and h.owner._issued_cohort is None
        count = len(h.sends)
        with pytest.raises(ContractValidationError, match='KALSHI_SCENARIO_SESSION_STATE'):
            h.session.evaluate(**inputs)
        with pytest.raises(ContractValidationError, match='KALSHI_SCENARIO_SESSION_STATE'):
            h.session.__init__(**h.kwargs)
        h.session.revoke(); h.session.revoke()
        assert state(h.session) == expected and len(h.sends) == count

    with _synthetic_kalshi_observation() as h:
        session = start(h)
        assert set(signature(session_type).parameters) == set(h.kwargs)
        assert all(p.kind is Parameter.KEYWORD_ONLY and p.default is Parameter.empty
                   for name, p in signature(session_type).parameters.items() if name != 'source_use_binding')
        assert signature(session_type).parameters['source_use_binding'].default is None
        assert set(signature(session.evaluate).parameters) == set(inputs)
        assert all(p.kind is Parameter.KEYWORD_ONLY and p.default is Parameter.empty
                   for p in signature(session.evaluate).parameters.values())
        assert not hasattr(session, '__dict__') and not h.connections and not h.sends
        with pytest.raises(ContractValidationError):
            session.__init__(**h.kwargs)
        for impostor in (copy(session), object.__new__(session_type)):
            for operation in (lambda: impostor.evaluate(**inputs), impostor.revoke):
                with pytest.raises(ContractValidationError, match='KALSHI_SCENARIO_SESSION_ASSOCIATION'):
                    operation()
        class SessionSubclass(session_type):
            pass
        with pytest.raises(ContractValidationError):
            SessionSubclass(**h.kwargs)
        assert state(session) == 'NEW' and h.owner._state == 'NEW' and not h.connections
        captures, composed, resolved = [], [], []
        real_capture = source.KalshiFeeObservationOwnerV1.capture
        real_compose = pretrade.compose_kalshi_observed_fee_scenario_cashflows_v1
        real_resolve = source.KalshiFeeObservationOwnerV1.resolve_scenario_multiplier
        def capture_spy(owner):
            cohort = real_capture(owner)
            captures.append((owner, cohort))
            return cohort
        def compose_spy(**kwargs):
            cash = real_compose(**kwargs)
            composed.append((kwargs, cash))
            return cash
        def resolve_spy(owner, **kwargs):
            resolved.append((owner, kwargs))
            return real_resolve(owner, **kwargs)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(source.KalshiFeeObservationOwnerV1, 'capture', capture_spy)
            patch.setattr(pretrade, 'compose_kalshi_observed_fee_scenario_cashflows_v1', compose_spy)
            patch.setattr(source.KalshiFeeObservationOwnerV1, 'resolve_scenario_multiplier', resolve_spy)
            result = session.evaluate(**inputs)
        assert len(captures) == len(composed) == 1 and len(resolved) == 4
        owner, cohort = captures[0]
        assert owner is h.owner and all(row[0] is owner and row[1]['cohort'] is cohort for row in resolved)
        assert all(row[1] == resolved[0][1] for row in resolved[1:])
        assert composed[0][0]['source_owner'] is owner and composed[0][0]['cohort'] is cohort
        assert result.cashflows is composed[0][1] and result.fills is fills
        assert all(composed[0][0][name] is value for name, value in inputs.items())
        assert [row[1] for row in h.sends] == [
            '/trade-api/v2/markets/SYNTHETIC%3A%3AMARKET',
            '/trade-api/v2/events/SYNTHETIC%3A%3AEVENT?exclude_markets=true',
            '/trade-api/v2/series/SYNTHETIC%3A%3ASERIES']
        assert result.cashflows.platform_fee_total == Decimal('1.75')
        assert result.fee_basis == 'OBSERVED_SERIES_BASE' and result.fee_multiplier is cohort.fee_multiplier
        assert (result.market_ticker, result.event_ticker, result.series_ticker) == (
            cohort.market_ticker, cohort.event_ticker, cohort.series_ticker)
        assert result.source_receipt_ref is h.kwargs['source_receipt'].receipt_id
        assert result.rights_receipt_ref is h.kwargs['rights_receipt'].receipt_id
        for name in ('account_scope', 'operating_authorization_ref', 'process_epoch_id', 'monotonic_clock_id'):
            assert getattr(result, name) is h.kwargs[name]
        assert result.available_wall_ns == cohort.available_wall_ns == h.clock['wall']
        assert result.available_monotonic_ns == cohort.available_monotonic_ns == result.evaluated_monotonic_ns
        assert result.evidence_class == 'OBSERVED_FEE_HYPOTHETICAL_SCENARIO'
        assert [field.name for field in fields(result)] == [
            'cashflows', 'market_ticker', 'event_ticker', 'series_ticker', 'fee_basis', 'fee_multiplier',
            'source_receipt_ref', 'rights_receipt_ref', 'account_scope', 'operating_authorization_ref',
            'process_epoch_id', 'monotonic_clock_id', 'available_wall_ns', 'available_monotonic_ns',
            'evaluated_monotonic_ns', 'fills', 'balance_increment', 'prior_rounding_overpayment', 'evidence_class']
        assert not fields(result)[-1].init and not hasattr(result, '__dict__')
        with pytest.raises(FrozenInstanceError):
            result.fee_basis = 'NATIVE'
        terminal(h, 'CONSUMED')
        assert result.cashflows.platform_fee_total == Decimal('1.75')
        baseline = h.bodies

    for name in ('source_receipt', 'rights_receipt', 'authorization_expires_at_utc', 'deadline_monotonic_ns'):
        with _synthetic_kalshi_observation() as h:
            kwargs = dict(h.kwargs); del kwargs[name]
            with pytest.raises(TypeError):
                session_type(**kwargs)
            assert not h.connections and not h.sends
    for change in (
        lambda k: {'source_receipt': object()}, lambda k: {'rights_receipt': object()},
        lambda k: {'account_scope': 'OTHER'}, lambda k: {'internal_use_class': 'OTHER'},
        lambda k: {'permitted_retention_class': 'OTHER'},
        lambda k: {'source_receipt': replace(k['source_receipt'], source_id='OTHER')},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], source_id='OTHER')},
        lambda k: {'source_receipt': replace(k['source_receipt'], checked_at_utc=k['source_receipt'].checked_at_utc + timedelta(seconds=2))},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], checked_at_utc=k['rights_receipt'].checked_at_utc + timedelta(seconds=2))},
        lambda k: {'source_receipt': replace(k['source_receipt'], checked_at_utc=k['source_receipt'].checked_at_utc - timedelta(days=2), effective_at_utc=k['source_receipt'].effective_at_utc - timedelta(days=2))},
        lambda k: {'source_receipt': replace(k['source_receipt'], expires_at_utc=k['source_receipt'].checked_at_utc + timedelta(seconds=1))},
        lambda k: {'rights_receipt': replace(k['rights_receipt'], expires_at_utc=k['rights_receipt'].checked_at_utc + timedelta(seconds=1))},
        lambda k: {'authorization_expires_at_utc': k['authorization_expires_at_utc'] - timedelta(seconds=50)},
        lambda k: {'deadline_monotonic_ns': 10_000_000_000},
    ):
        with _synthetic_kalshi_observation() as h:
            with pytest.raises(ComputationControlPlaneError):
                start(h, **change(h.kwargs))
            assert not h.connections and not h.sends and not h.tls_preparations

    class FillSubclass(KalshiQuadraticTakerBuyYesFillV1):
        pass
    malformed = [None, [], (), fills * 4097, (object(),),
                 (FillSubclass(Decimal(1), Decimal('.5')),), (object.__new__(KalshiQuadraticTakerBuyYesFillV1),)]
    for name in ('contracts', 'yes_price'):
        for value in (True, '1', 0.5, Decimal('NaN'), Decimal('sNaN'), Decimal('Infinity'), Decimal('-1'), Decimal('0')):
            row = object.__new__(KalshiQuadraticTakerBuyYesFillV1)
            for field in fields(KalshiQuadraticTakerBuyYesFillV1):
                object.__setattr__(row, field.name, value if field.name == name else getattr(fills[0], field.name))
            malformed.append((row,))
    with _synthetic_kalshi_observation() as h:
        session = start(h)
        bad_inputs = [{'fills': value} for value in malformed]
        for name in ('balance_increment', 'prior_rounding_overpayment'):
            bad_inputs.extend({name: value} for value in (
                True, '0.01', .01, Decimal('NaN'), Decimal('sNaN'), Decimal('Infinity'), Decimal('-.01'), Decimal('.0000001')))
        bad_inputs += [{'balance_increment': Decimal('0')}, {'balance_increment': Decimal('.001')}]
        for changes in bad_inputs:
            with pytest.raises(ComputationControlPlaneError):
                session.evaluate(**{**inputs, **changes})
            assert state(session) == 'NEW' and h.owner._state == 'NEW'
            assert not h.connections and not h.sends
        assert session.evaluate(**inputs).cashflows.platform_fee_total == Decimal('1.75')
        terminal(h, 'CONSUMED')

    for field in ('market_ticker', 'event_ticker', 'series_ticker', 'source_receipt_ref', 'rights_receipt_ref',
                  'account_scope', 'operating_authorization_ref', 'process_epoch_id', 'monotonic_clock_id'):
        for value in ('', ' leading', 'two words', 'line\nbreak', True):
            with pytest.raises(ContractValidationError):
                replace(result, **{field: value})
    for changes in ({'cashflows': object()}, {'cashflows': object.__new__(pretrade.KalshiConditionalCashflowTermsV1)},
                    {'fee_basis': 'NATIVE'}, {'fee_basis': True}, {'fee_multiplier': Decimal('-1')},
                    {'fee_multiplier': True}, {'fee_multiplier': Decimal('NaN')}, {'fills': []},
                    {'balance_increment': Decimal('.001')}, {'prior_rounding_overpayment': Decimal('-1')}):
        with pytest.raises(ComputationControlPlaneError):
            replace(result, **changes)
    for field in ('available_wall_ns', 'available_monotonic_ns', 'evaluated_monotonic_ns'):
        for value in (True, 1.0, '1', -1, 2**63):
            with pytest.raises(PointInTimeError):
                replace(result, **{field: value})
    with pytest.raises(PointInTimeError):
        replace(result, evaluated_monotonic_ns=result.available_monotonic_ns - 1)
    for grid, prior, fee, rebate, carry in (
        ('.01', '.009', '1.76', '.01', '.009'), ('.0001', '.00009', '1.75', '0', '.00009')):
        raw = (*baseline[:2], baseline[2].replace(b'"fee_multiplier":1', b'"fee_multiplier":0.5'))
        with _synthetic_kalshi_observation(bodies=raw, fills=fills * 2,
                balance_increment=Decimal(grid), prior_rounding_overpayment=Decimal(prior)) as h:
            value = start(h).evaluate(fills=fills * 2, balance_increment=Decimal(grid), prior_rounding_overpayment=Decimal(prior))
            assert value.fee_multiplier == Decimal('.5')
            assert value.cashflows == pretrade.KalshiConditionalCashflowTermsV1(
                Decimal('-100'), Decimal(fee), Decimal(rebate), Decimal(carry))
            terminal(h, 'CONSUMED')

    raw = (*baseline[:2], baseline[2].replace(b'"fee_multiplier":1', b'"fee_multiplier":1000'))
    with _synthetic_kalshi_observation(bodies=raw,
            fills=(KalshiQuadraticTakerBuyYesFillV1(Decimal('1e100'), Decimal('.5')),)) as h:
        with pytest.raises(NumericDomainError) as failure:
            start(h).evaluate(**{**inputs, 'fills': (KalshiQuadraticTakerBuyYesFillV1(Decimal('1e100'), Decimal('.5')), )})
        assert failure.value.reason_code is ReasonCode.OUT_OF_DOMAIN and len(h.sends) == 3
        terminal(h, 'FAILED')
    raw = (baseline[0][:-2] + b',"fee_waiver_expiration_time":"SYNTHETIC"}}', *baseline[1:])
    with _synthetic_kalshi_observation(bodies=raw) as h:
        with pytest.raises(ContractValidationError, match='KALSHI_OBSERVATION_MODIFIER'):
            start(h).evaluate(**inputs)
        terminal(h, 'FAILED')

    _assert_kalshi_session_failures(start, terminal, inputs)
    _assert_kalshi_session_concurrency(start, terminal, inputs)


def _assert_kalshi_session_failures(start, terminal, inputs):
    from datetime import timedelta
    from src.qtt.pretrade import pr169_pretrade1_resolvers as pretrade
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import PointInTimeError

    with _synthetic_kalshi_observation() as h:
        start(h).revoke()
        terminal(h, 'REVOKED')
        assert not h.sends
    for response_index in range(3):
        def revoke_on_read(h, index):
            if index == response_index:
                h.session.revoke()
        with _synthetic_kalshi_observation(on_read=revoke_on_read) as h:
            with pytest.raises(ContractValidationError):
                start(h).evaluate(**inputs)
            assert len(h.sends) == response_index + 1
            terminal(h, 'REVOKED')

    for receipt_name in ('source_receipt', 'rights_receipt'):
        lifetime = {'source_lifetime': 2} if receipt_name == 'source_receipt' else {'use_lifetime': 2}
        with _synthetic_kalshi_observation(**lifetime) as h, pytest.MonkeyPatch.context() as patch:
            start(h)
            real_post = pretrade.KalshiObservedFeeScenarioResultV1.__post_init__
            def expire(result):
                real_post(result)
                h.clock['wall'] += 2_000_000_000
            patch.setattr(pretrade.KalshiObservedFeeScenarioResultV1, '__post_init__', expire)
            with pytest.raises(ComputationControlPlaneError):
                h.session.evaluate(**inputs)
            assert len(h.sends) == 3
            terminal(h, 'FAILED')

    for stage in ('after_capture', 'composition', 'result'):
        with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
            start(h)
            if stage == 'after_capture':
                real_capture = source.KalshiFeeObservationOwnerV1.capture
                def revoke_after_capture(owner):
                    cohort = real_capture(owner)
                    h.session.revoke()
                    return cohort
                patch.setattr(source.KalshiFeeObservationOwnerV1, 'capture', revoke_after_capture)
            elif stage == 'composition':
                real_compose = pretrade.compose_kalshi_observed_fee_scenario_cashflows_v1
                def revoke_after_composition(**kwargs):
                    cash = real_compose(**kwargs)
                    h.session.revoke()
                    return cash
                patch.setattr(pretrade, 'compose_kalshi_observed_fee_scenario_cashflows_v1', revoke_after_composition)
            else:
                real_post = pretrade.KalshiObservedFeeScenarioResultV1.__post_init__
                def revoke_after_result(result):
                    real_post(result)
                    h.session.revoke()
                patch.setattr(pretrade.KalshiObservedFeeScenarioResultV1, '__post_init__', revoke_after_result)
            with pytest.raises(ContractValidationError):
                h.session.evaluate(**inputs)
            assert len(h.sends) == 3
            terminal(h, 'REVOKED')

    for change in ('deadline', 'authorization', 'wall_reversal', 'mono_reversal', 'future_evaluation'):
        with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
            start(h)
            real_post = pretrade.KalshiObservedFeeScenarioResultV1.__post_init__
            def change_after_result(result):
                real_post(result)
                if change == 'deadline':
                    h.clock['mono'] = h.kwargs['deadline_monotonic_ns']
                elif change == 'authorization':
                    h.clock['wall'] += 50_000_000_000
                elif change == 'wall_reversal':
                    h.clock['wall'] -= 1
                elif change == 'mono_reversal':
                    h.clock['mono'] -= 1
            patch.setattr(pretrade.KalshiObservedFeeScenarioResultV1, '__post_init__', change_after_result)
            if change == 'future_evaluation':
                real_capture = source.KalshiFeeObservationOwnerV1.capture
                def future_after_capture(owner):
                    cohort = real_capture(owner)
                    samples = iter((h.clock['mono'] + 1,))
                    patch.setattr(pretrade.time, 'monotonic_ns', lambda: next(samples, h.clock['mono']))
                    return cohort
                patch.setattr(source.KalshiFeeObservationOwnerV1, 'capture', future_after_capture)
            with pytest.raises(PointInTimeError) as failure:
                h.session.evaluate(**inputs)
            assert failure.value.reason_code is ReasonCode.POINT_IN_TIME_VIOLATION and len(h.sends) == 3
            terminal(h, 'FAILED')

    for stage in ('capture', 'arithmetic', 'result', 'cleanup'):
        primary = NumericDomainError(ReasonCode.OUT_OF_DOMAIN, 'SYNTHETIC_PRIMARY')
        def fail_read(h, index):
            raise primary
        with _synthetic_kalshi_observation(on_read=fail_read if stage == 'capture' else None) as h:
            start(h)
            with pytest.MonkeyPatch.context() as patch:
                if stage == 'arithmetic':
                    real_math = pretrade.kalshi_quadratic_taker_buy_yes_input_v1
                    def fail_math(**kwargs):
                        real_math(**kwargs)
                        raise primary
                    patch.setattr(pretrade, 'kalshi_quadratic_taker_buy_yes_input_v1', fail_math)
                elif stage in ('result', 'cleanup'):
                    real_post = pretrade.KalshiObservedFeeScenarioResultV1.__post_init__
                    def fail_post(result):
                        real_post(result)
                        raise primary
                    patch.setattr(pretrade.KalshiObservedFeeScenarioResultV1, '__post_init__', fail_post)
                if stage == 'cleanup':
                    real_revoke = source.KalshiFeeObservationOwnerV1.revoke
                    def fail_cleanup(owner):
                        real_revoke(owner)
                        raise RuntimeError('SYNTHETIC_PRIVATE_CLEANUP_TEXT')
                    patch.setattr(source.KalshiFeeObservationOwnerV1, 'revoke', fail_cleanup)
                with pytest.raises(NumericDomainError) as failure:
                    h.session.evaluate(**inputs)
                assert failure.value is primary
                if stage == 'cleanup':
                    assert failure.value.__notes__ == ['KALSHI_SCENARIO_SESSION_CLEANUP_FAILED']
                    assert 'SYNTHETIC_PRIVATE_CLEANUP_TEXT' not in str(failure.value)
            assert len(h.sends) == (1 if stage == 'capture' else 3)
            terminal(h, 'FAILED')


def _assert_kalshi_session_concurrency(start, terminal, inputs):
    from threading import Event, Thread
    from src.qtt.pretrade import pr169_pretrade1_resolvers as pretrade

    # Bound every worker using the existing two-second event/join convention.
    for action in ('competing_evaluate', 'revoke'):
        entered, release = Event(), Event()
        outcomes, competing = [], []
        def blocked_read(h, index):
            if index == 0:
                entered.set()
                assert release.wait(2)
        with _synthetic_kalshi_observation(on_read=blocked_read) as h:
            start(h)
            def evaluate():
                try:
                    outcomes.append(h.session.evaluate(**inputs))
                except BaseException as error:
                    outcomes.append(error)
            def contend():
                try:
                    if action == 'revoke':
                        h.session.revoke()
                        competing.append('REVOKED')
                    else:
                        h.session.evaluate(**{**inputs, 'fills': []})
                except BaseException as error:
                    competing.append(error)
            first, second = Thread(target=evaluate), Thread(target=contend)
            first.start()
            try:
                assert entered.wait(2)
                second.start()
                second.join(2)
                assert not second.is_alive() and len(competing) == 1
                if action == 'competing_evaluate':
                    assert type(competing[0]) is ContractValidationError
                    assert str(competing[0]).endswith('KALSHI_SCENARIO_SESSION_STATE')
                    assert h.session._KalshiFeeScenarioSessionV1__state == 'RUNNING'
                else:
                    assert competing == ['REVOKED']
            finally:
                release.set()
                first.join(2)
                if second.ident is not None:
                    second.join(2)
            assert not first.is_alive() and not second.is_alive() and len(outcomes) == 1
            if action == 'competing_evaluate':
                assert type(outcomes[0]) is pretrade.KalshiObservedFeeScenarioResultV1
                terminal(h, 'CONSUMED')
            else:
                assert isinstance(outcomes[0], ContractValidationError) and len(h.sends) == 1
                terminal(h, 'REVOKED')

    # A revoke winning the gap between input validation and claim prevents any send.
    with _synthetic_kalshi_observation() as h, pytest.MonkeyPatch.context() as patch:
        start(h)
        real_preflight = pretrade._kalshi_scenario_inputs_v1
        def revoke_after_preflight(*args):
            real_preflight(*args)
            h.session.revoke()
        patch.setattr(pretrade, '_kalshi_scenario_inputs_v1', revoke_after_preflight)
        with pytest.raises(ContractValidationError, match='KALSHI_SCENARIO_SESSION_STATE'):
            h.session.evaluate(**inputs)
        assert not h.connections and not h.sends
        terminal(h, 'REVOKED')


def _f13_storage_fixture():
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import receipts as owner
    body = {
        "schema_version": "1", "record_id": "private-clock", "raw_record_ref": "raw-clock",
        "scope": dict(profile="POLYMARKET_US_RETAIL_DIRECT", ledger_account_ref="aggregate-1",
                      source_binding_ref="private-binding", source_context_ref="context",
                      capture_epoch_ref="capture-epoch", partition_ref="partition"),
        "raw_body_utf8": ' {"event":"2026-01-01T00:00:00.000000001Z","amount":1.20} ',
        "raw_byte_limit": 4096, "provider_event_pointer_or_none": "/event",
        "clock_proof_refs": dict(provider_publication_time_utc_or_none=None,
                                revision_effective_time_utc_or_none=None,
                                settlement_finality_time_utc_or_none=None),
        "clocks": {
            "provider_event_time_utc_or_none": "2026-01-01T00:00:00.000000001Z",
            "provider_publication_time_utc_or_none": None,
            "qtt_received_at_utc": "2026-01-01T00:00:00.000000002Z", "qtt_received_monotonic_ns": 1,
            "qtt_parse_completed_at_utc": "2026-01-01T00:00:00.000000003Z", "qtt_parse_completed_monotonic_ns": 2,
            "durable_commit_completed_at_utc": "2026-01-01T00:00:00.000000004Z", "durable_commit_completed_monotonic_ns": 3,
            "strategy_available_at_utc": "2026-01-01T00:00:00.000000005Z", "strategy_available_monotonic_ns": 4,
            "revision_effective_time_utc_or_none": None, "settlement_finality_time_utc_or_none": None,
            "process_epoch_id": "process", "monotonic_clock_id": "monotonic",
            "wall_clock_source_id": "wall", "clock_quality_receipt_ref": "quality",
            "wall_clock_uncertainty_ns": 0,
        },
        "capture_commit_ref": "capture-commit", "publication_witness_ref": "publication",
        "commit_evidence_class": "COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY",
        "issued_at": "2026-01-01T00:00:00.000000009Z", "issued_monotonic_ns": 5,
    }
    canonical = owner._native_retail_clock_companion(body)["canonical_payload_json"]
    private = EconomicReceiptEventSpineV1(
        "private-clock", EconomicRecordTypeV1.PRIVATE_OBSERVATION_CLOCK, "1",
        "INFORMATIONAL_FIXTURE", "QKUComputationControlPlaneV1", "context",
        NOW, NOW, "private-cause", "private-correlation", "private-trace", "trace-state",
        0, "aggregate-1", 0, "CONTRACT_ONLY",
        owner.PrivateObservationClockReceiptV1("private-clock", canonical),
    )
    return body, private


def _f13_rollback_owned_transaction(tx) -> None:
    if tx.is_active:
        tx.rollback()


def _f13_close_owned_adapter(adapter) -> None:
    if isinstance(adapter, SQLiteReferenceAdapterV1):
        active = adapter._active_transaction
        if active is not None and active.is_active:
            # A transaction owner already attempted genuine rollback. Close this
            # test-owned connection without automatically retrying that method.
            adapter._connection.close()
        else:
            adapter.close()


def _assert_f13_reference_storage(adapter_kind, directory) -> None:
    from contextlib import ExitStack
    from copy import deepcopy
    from dataclasses import fields
    import json
    import sqlite3
    from threading import Event, Thread
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import receipts as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError, PersistenceContractError, SerializationSafetyError, TransactionContractError,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import NoEffectFlagsV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import PersistenceAvailabilityV1

    with ExitStack() as adapters:
        def make(name):
            adapter = (InMemoryPersistenceAdapterV1() if adapter_kind == "memory" else
                       SQLiteReferenceAdapterV1(directory / (name + ".db"), busy_timeout_ms=0, max_transaction_attempts=1))
            adapters.callback(_f13_close_owned_adapter, adapter)
            return adapter

        body, private = _f13_storage_fixture()
        adapter = make("private-storage")
        assert adapter.load_committed_private_clock_receipt_v1("missing") is None
        for record_ref in (None, 1, "", " bad", "x" * 257):
            with pytest.raises(ContractValidationError):
                adapter.load_committed_private_clock_receipt_v1(record_ref)
        tx = adapter.begin_transaction()
        try:
            adapter.insert_receipt_record(tx, private)
            generic = adapter.get_record(private.record_id)
            assert (generic is None) if adapter_kind == "memory" else type(generic) is dict
            with pytest.raises(TransactionContractError) as caught:
                adapter.load_committed_private_clock_receipt_v1("missing")
            assert caught.value.reason_code is ReasonCode.TRANSACTION_STATE_INVALID
        finally:
            _f13_rollback_owned_transaction(tx)
        assert adapter.load_committed_private_clock_receipt_v1(private.record_id) is None

        tx = adapter.begin_transaction()
        try:
            adapter.insert_receipt_record(tx, private)
            tx.commit()
        finally:
            _f13_rollback_owned_transaction(tx)
        loaded = adapter.load_committed_private_clock_receipt_v1(private.record_id)
        assert type(loaded) is EconomicReceiptEventSpineV1 and loaded is not private
        assert type(loaded.typed_payload) is owner.PrivateObservationClockReceiptV1
        assert type(loaded.no_effect_flags) is NoEffectFlagsV1
        assert deterministic_json(loaded) == deterministic_json(private)
        assert loaded.typed_payload.canonical_payload_json == private.typed_payload.canonical_payload_json
        assert set(json.loads(loaded.typed_payload.canonical_payload_json)) == set(body)
        assert tuple(field.name for field in fields(loaded.typed_payload)) == ("record_id", "canonical_payload_json")
        assert all(type(getattr(loaded.no_effect_flags, field.name)) is bool and
                   getattr(loaded.no_effect_flags, field.name) is False for field in fields(NoEffectFlagsV1))
        # Existing generic shape/selection behavior remains compatible.
        assert type(adapter.get_record(private.record_id)) is (EconomicReceiptEventSpineV1 if adapter_kind == "memory" else dict)
        assert len(adapter.reconstruct_as_of(effective_cutoff=NOW, recorded_cutoff=NOW, aggregate_scope=("aggregate-1",))) == 1
        requirements = dict(
            requires_cross_clock_comparison=False, requires_provider_event_time=True,
            requires_provider_publication_time=False, requires_revision_at_decision=False,
            requires_finality_at_decision=False, provider_publication_time_is_source_proven=False,
            maximum_wall_clock_uncertainty_ns_or_none=None, required_process_epoch_id_or_none=None,
            required_monotonic_clock_id_or_none=None,
        )
        replay = owner._native_retail_clock_replay(
            loaded.typed_payload.canonical_payload_json, expected_record_id=loaded.record_id,
            expected_scope=body["scope"], original_raw_body=body["raw_body_utf8"].encode(),
            requirements=requirements, decision_time=body["clocks"]["strategy_available_at_utc"],
            recorded_cutoff=body["issued_at"],
        )
        assert replay["source_accepted"] is replay["durable_commit_proven"] is replay["runtime_effect_authorized"] is False
        tx = adapter.begin_transaction()
        try:
            adapter.insert_receipt_record(tx, private)
            with pytest.raises(PersistenceContractError) as caught:
                adapter.insert_receipt_record(tx, replace(private, sequence=1))
            assert caught.value.reason_code is ReasonCode.PERSISTENCE_CONFLICT
        finally:
            _f13_rollback_owned_transaction(tx)
        assert deterministic_json(adapter.load_committed_private_clock_receipt_v1(private.record_id)) == deterministic_json(private)

        original_mapping = json.loads(deterministic_json(private))
        mutations = (
            lambda row: row.pop("traceparent"),
            lambda row: row.update(extra=False),
            lambda row: row.update(record_type="ECONOMIC_EVENT"),
            lambda row: row.update(schema_version=1),
            lambda row: row.update(schema_version="2"),
            lambda row: row.update(record_id="other"),
            lambda row: row.update(context_ref="other"),
            lambda row: row.update(aggregate_id="other"),
            lambda row: row.update(effective_at="2026-01-01T00:00:00.000001+00:00"),
            lambda row: row.update(recorded_at="2026-01-01T00:00:00Z"),
            lambda row: row.update(sequence=True),
            lambda row: row.update(aggregate_version=0.0),
            lambda row: row.update(causation_id=row["correlation_id"]),
            lambda row: row.update(traceparent=row["record_id"]),
            lambda row: row["typed_payload"].update(extra=False),
            lambda row: row["typed_payload"].update(record_id="other"),
            lambda row: row["typed_payload"].update(canonical_payload_json=1),
            lambda row: row["no_effect_flags"].pop("capital_mutation_allowed"),
            lambda row: row["no_effect_flags"].update(capital_mutation_allowed=0),
            lambda row: row["no_effect_flags"].update(order_release_allowed=True),
        )
        for mutate in mutations:
            damaged = deepcopy(original_mapping)
            mutate(damaged)
            with pytest.raises(PersistenceContractError) as caught:
                owner._private_clock_reconstruct_spine_v1(damaged, expected_record_id=private.record_id)
            assert caught.value.reason_code is ReasonCode.SCHEMA_MISMATCH
        for field, value in (("schema_version", 1), ("record_id", 3), ("clocks", []),
                             ("profile", "OTHER"), ("raw_record_ref", body["record_id"])):
            damaged = deepcopy(original_mapping)
            damaged_body = deepcopy(body)
            if field == "profile":
                damaged_body["scope"][field] = value
            else:
                damaged_body[field] = value
            damaged["typed_payload"]["canonical_payload_json"] = json.dumps(damaged_body)
            with pytest.raises(PersistenceContractError) as caught:
                owner._private_clock_reconstruct_spine_v1(damaged, expected_record_id=private.record_id)
            assert caught.value.reason_code is ReasonCode.SCHEMA_MISMATCH

        fake_type = type("PrivateObservationClockReceiptV1", (), {"__module__": owner.__name__})
        fake = fake_type()
        fake.record_id, fake.canonical_payload_json = private.record_id, private.typed_payload.canonical_payload_json
        for field, value in (
            ("typed_payload", fake), ("record_type", EconomicRecordTypeV1.ECONOMIC_EVENT),
            ("record_type", "PRIVATE_OBSERVATION_CLOCK"), ("sequence", True),
            ("effective_at", NOW.isoformat()), ("recorded_at", NOW.replace(tzinfo=None)),
            ("semantic_owner", 12),
        ):
            damaged = deepcopy(private)
            object.__setattr__(damaged, field, value)
            tx = adapter.begin_transaction()
            try:
                with pytest.raises(PersistenceContractError) as caught:
                    adapter.insert_receipt_record(tx, damaged)
                assert caught.value.reason_code is ReasonCode.SCHEMA_MISMATCH
            finally:
                _f13_rollback_owned_transaction(tx)
        damaged_flags = deepcopy(private)
        object.__setattr__(damaged_flags.no_effect_flags, "capital_mutation_allowed", 0)
        with pytest.raises(PersistenceContractError):
            owner._private_clock_reconstruct_spine_v1(damaged_flags, expected_record_id=private.record_id)
        if adapter_kind == "memory":
            damaged = deepcopy(private)
            object.__setattr__(damaged, "sequence", True)
            try:
                for corrupt in (damaged, None):
                    adapter._tables["receipt_records"][private.record_id] = corrupt
                    with pytest.raises(PersistenceContractError) as caught:
                        adapter.load_committed_private_clock_receipt_v1(private.record_id)
                    assert caught.value.reason_code is ReasonCode.SCHEMA_MISMATCH
            finally:
                adapter._tables["receipt_records"][private.record_id] = private
            for failure_point in (None, "readiness", "locked", "worker"):
                started, finished, observed, errors = Event(), Event(), [], []
                initiating = (RuntimeError("synthetic worker failure") if failure_point == "worker" else
                              AssertionError("synthetic owned-lock assertion"))
                tx = None

                def read_after_lock():
                    try:
                        started.set()
                        observed.append(adapter.load_committed_private_clock_receipt_v1(private.record_id))
                        if failure_point == "worker":
                            raise initiating
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        finished.set()

                thread = Thread(target=read_after_lock)

                def read_with_cleanup():
                    nonlocal tx
                    worker_started = False
                    tx = adapter.begin_transaction()
                    try:
                        with pytest.MonkeyPatch.context() as patch:
                            if failure_point == "readiness":
                                original_wait = started.wait

                                def fail_readiness(timeout):
                                    assert original_wait(timeout)
                                    assert tx.is_active and not finished.is_set()
                                    raise initiating

                                patch.setattr(started, "wait", fail_readiness)
                            thread.start()
                            worker_started = True
                            assert started.wait(2)
                            assert not finished.wait(0.02)
                            if failure_point == "locked":
                                assert tx.is_active
                                raise initiating
                    finally:
                        try:
                            _f13_rollback_owned_transaction(tx)
                        finally:
                            if worker_started:
                                thread.join(2)
                                assert not thread.is_alive()
                                if errors:
                                    raise errors[0]

                if failure_point is None:
                    read_with_cleanup()
                else:
                    with pytest.raises(type(initiating)) as caught:
                        read_with_cleanup()
                    assert caught.value is initiating
                assert tx is not None and not tx.is_active
                assert not thread.daemon
                assert finished.is_set() and not thread.is_alive()
                assert deterministic_json(observed[0]) == deterministic_json(private)
                assert errors == ([initiating] if failure_point == "worker" else [])
        else:
            # An actual active connection with a cleared wrapper marker is still rejected.
            adapter._connection.execute("BEGIN IMMEDIATE")
            try:
                with pytest.raises(TransactionContractError):
                    adapter.load_committed_private_clock_receipt_v1(private.record_id)
                assert adapter._connection.in_transaction is True
            finally:
                if adapter._connection.in_transaction:
                    adapter._connection.execute("ROLLBACK")
            for availability in (PersistenceAvailabilityV1.UNAVAILABLE, PersistenceAvailabilityV1.INTEGRITY_FAILURE):
                with pytest.MonkeyPatch.context() as patch:
                    patch.setattr(adapter, "_availability", availability)
                    with pytest.raises(PersistenceContractError) as caught:
                        adapter.load_committed_private_clock_receipt_v1(private.record_id)
                    assert caught.value.reason_code is ReasonCode.PERSISTENCE_UNAVAILABLE
            errors = []
            def wrong_thread():
                try:
                    adapter.load_committed_private_clock_receipt_v1(private.record_id)
                except BaseException as exc:
                    errors.append(exc)
            thread = Thread(target=wrong_thread)
            worker_started = False
            try:
                thread.start()
                worker_started = True
            finally:
                if worker_started:
                    thread.join(2)
                    assert not thread.is_alive()
                    if errors and not isinstance(errors[0], PersistenceContractError):
                        raise errors[0]
            assert not thread.is_alive() and len(errors) == 1
            assert type(errors[0]) is PersistenceContractError and isinstance(errors[0].__cause__, sqlite3.Error)
            adapter.close()
            with pytest.raises(PersistenceContractError) as caught:
                adapter.load_committed_private_clock_receipt_v1(private.record_id)
            assert caught.value.reason_code is ReasonCode.PERSISTENCE_UNAVAILABLE
            assert isinstance(caught.value.__cause__, sqlite3.Error)
            adapter = make("private-storage")
            assert adapter.load_committed_private_clock_receipt_v1(private.record_id).typed_payload.canonical_payload_json == private.typed_payload.canonical_payload_json
            row = (private.record_id, NOW.isoformat(), NOW.isoformat(), private.aggregate_id, deterministic_json(private))
            sql_mutations = (
                (1, "2026-01-01T00:00:01+00:00", ReasonCode.SCHEMA_MISMATCH),
                (2, "2026-01-01T00:00:00Z", ReasonCode.SCHEMA_MISMATCH),
                (3, "other", ReasonCode.SCHEMA_MISMATCH),
                (4, row[4].encode(), ReasonCode.SCHEMA_MISMATCH),
                (4, " " + row[4], ReasonCode.PERSISTENCE_CONFLICT),
                (4, '{"record_id":"private-clock","record_id":"private-clock"}', ReasonCode.SERIALIZATION_UNSAFE),
                (4, '{"api_key":"synthetic-private-marker"}', ReasonCode.SECRET_MATERIAL_REJECTED),
            )
            for index, (column, value, reason) in enumerate(sql_mutations):
                tampered = make("private-tampered-" + str(index))
                try:
                    changed = list(row)
                    changed[column] = value
                    tampered._connection.execute("INSERT INTO receipt_records VALUES(?,?,?,?,?)", changed)
                    with pytest.raises((PersistenceContractError, SerializationSafetyError)) as caught:
                        tampered.load_committed_private_clock_receipt_v1(private.record_id)
                    assert caught.value.reason_code is reason
                    assert "synthetic-private-marker" not in str(caught.value)
                finally:
                    _f13_close_owned_adapter(tampered)
            from src.qtt.stage1_prediction_markets.qku_computation_control_plane import sqlite_reference as sqlite_owner
            for failure in (RecursionError("synthetic recursion"), UnicodeError("synthetic unicode")):
                def decode_failure(_text):
                    raise failure
                with pytest.MonkeyPatch.context() as patch:
                    patch.setattr(sqlite_owner, "safe_json_loads", decode_failure)
                    with pytest.raises(SerializationSafetyError, match="F13_STORED_ENVELOPE_INVALID") as caught:
                        adapter.load_committed_private_clock_receipt_v1(private.record_id)
                    assert caught.value.__cause__ is failure
            adapter.close()

            # The assertion leaves both the owned transaction and connection terminal
            # before TemporaryDirectory attempts to release its SQLite files.
            initiating = AssertionError("synthetic SQLite fixture assertion")
            with TemporaryDirectory(prefix="qtt-f13-cleanup-", dir=directory) as release_directory:
                released_path = Path(release_directory)
                with pytest.raises(AssertionError) as caught:
                    with ExitStack() as owned:
                        failed_adapter = SQLiteReferenceAdapterV1(
                            released_path / "owned.db", busy_timeout_ms=0, max_transaction_attempts=1,
                        )
                        owned.callback(_f13_close_owned_adapter, failed_adapter)
                        tx = failed_adapter.begin_transaction()
                        owned.callback(_f13_rollback_owned_transaction, tx)
                        failed_adapter.insert_receipt_record(tx, private)
                        raise initiating
                assert caught.value is initiating
                assert not tx.is_active and failed_adapter._active_transaction is None
                with pytest.raises(sqlite3.ProgrammingError):
                    failed_adapter._connection.execute("SELECT 1")
            assert not released_path.exists()


def _assert_f13_transaction_truth(adapter_kind, directory) -> None:
    from contextlib import ExitStack
    from copy import deepcopy
    from datetime import timedelta
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError, PersistenceContractError, TransactionContractError,
    )

    def make(name, attempts=1):
        return (InMemoryPersistenceAdapterV1() if adapter_kind == "memory" else
                SQLiteReferenceAdapterV1(directory / (name + ".db"), busy_timeout_ms=0, max_transaction_attempts=attempts))

    _body, private = _f13_storage_fixture()
    base = _atomic_records()
    event = replace(base.economic_events[0], source_record_refs=(*base.economic_events[0].source_record_refs, private.record_id))
    records = replace(base, receipt_records=(replace(base.receipt_records[0], typed_payload=event), private),
                      economic_events=(event,))
    for index, invalid in enumerate((
        dict(unit_of_work_id=""), dict(started_at=NOW + timedelta(seconds=1)),
        dict(started_at=NOW.replace(tzinfo=None)), dict(completed_at="not-a-time"),
    )):
        adapter = make("prevalidation-" + str(index))
        try:
            unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
            calls = []
            def begin_forbidden():
                calls.append("begin")
                raise AssertionError("invalid receipt metadata reached storage")
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr(adapter, "begin_transaction", begin_forbidden)
                with pytest.raises(ContractValidationError):
                    unit.execute(**{**dict(unit_of_work_id="valid", records=records, accounts=_accounts(),
                                           started_at=NOW, completed_at=NOW), **invalid})
            assert calls == [] and adapter.get_record(private.record_id) is None
        finally:
            _f13_close_owned_adapter(adapter)
    for index, corrupt in enumerate(("claim", "references")):
        adapter = make("prevalidation-identity-" + str(index))
        try:
            damaged = deepcopy(records)
            if corrupt == "claim":
                object.__setattr__(damaged.idempotency_claim, "claim_id", "")
            else:
                object.__setattr__(damaged.receipt_records[0], "record_id", damaged.economic_events[0].economic_event_id)
            unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr(adapter, "begin_transaction", begin_forbidden)
                with pytest.raises(ContractValidationError):
                    unit.execute(unit_of_work_id="valid", records=damaged, accounts=_accounts(), started_at=NOW, completed_at=NOW)
            assert calls == [] and adapter.get_record(private.record_id) is None
        finally:
            _f13_close_owned_adapter(adapter)

    def run_case(case, *, assertion_failure=None, observation=None):
        attempts = 2 if case == "begin-retry-actual-claim" else 1
        adapter = make("truth-" + case + ("-assertion" if assertion_failure is not None else ""), attempts)
        try:
            with ExitStack() as transactions:
                original_begin = adapter.begin_transaction

                def begin_owned():
                    tx = original_begin()
                    transactions.callback(_f13_rollback_owned_transaction, tx)
                    return tx

                with pytest.MonkeyPatch.context() as patch:
                    patch.setattr(adapter, "begin_transaction", begin_owned)
                    unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(attempts))
                    historical = case.startswith("historical") or case.startswith("replay") or case.startswith("conflict")
                    if historical:
                        assert unit.execute(unit_of_work_id="prior", records=records, accounts=_accounts(),
                                            started_at=NOW, completed_at=NOW).transaction_state is TransactionTerminalStateV1.COMMITTED
                    counts = dict(begin=0, commit=0, rollback=0)
                    initiating = PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "synthetic initiating failure")
                    cleanup = PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "synthetic cleanup failure")
                    original_acquire = adapter.acquire_idempotency_claim
                    original_receipt = unit._receipt
                    latest = []
                    def validate_before_commit(**kwargs):
                        assert counts["commit"] == 0, "receipt construction occurred after commit attempt"
                        return original_receipt(**kwargs)
                    patch.setattr(unit, "_receipt", validate_before_commit)
                    def begin():
                        counts["begin"] += 1
                        if case == "begin-retry-actual-claim" and counts["begin"] == 1:
                            raise PersistenceContractError(ReasonCode.REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT, "synthetic begin contention")
                        tx = begin_owned()
                        latest.append(tx)
                        original_commit, original_rollback = tx.commit, tx.rollback
                        if observation is not None:
                            observation.update(adapter=adapter, tx=tx, begin=original_begin,
                                               rollback=original_rollback, counts=counts)
                        def commit():
                            counts["commit"] += 1
                            if case in {"active-commit-error", "commit-cleanup-error", "commit-cleanup-stays-active"}:
                                raise initiating
                            if case == "inactive-commit-error":
                                original_rollback()
                                raise initiating
                            original_commit()
                            if case == "after-commit-error":
                                raise initiating
                        def rollback():
                            counts["rollback"] += 1
                            if case.endswith("rollback-error") or case == "commit-cleanup-error":
                                raise cleanup
                            if case.endswith("rollback-stays-active") or case == "commit-cleanup-stays-active":
                                return
                            original_rollback()
                        patch.setattr(tx, "commit", commit)
                        patch.setattr(tx, "rollback", rollback)
                        return tx
                    patch.setattr(adapter, "begin_transaction", begin)
                    if case in {"precommit-error", "inactive-precommit-error", "rollback-error", "rollback-stays-active"}:
                        def fail_event(tx, _event):
                            if case == "inactive-precommit-error":
                                # Simulate backend-local cleanup without a coordinator rollback witness.
                                original_type_rollback = type(tx).rollback
                                original_type_rollback(tx)
                            raise initiating
                        patch.setattr(adapter, "insert_economic_event", fail_event)
                    if case == "begin-retry-actual-claim":
                        def acquire(tx, claim):
                            return original_acquire(tx, replace(claim, claim_id="actual-acquired-claim"))
                        patch.setattr(adapter, "acquire_idempotency_claim", acquire)
                    actual_records = records
                    if case.startswith("conflict"):
                        actual_records = replace(records, idempotency_claim=replace(
                            records.idempotency_claim, canonical_request_json=canonical_request_json_v1({"command": "other"}),
                        ))
                    args = dict(unit_of_work_id="current", records=actual_records, accounts=_accounts(),
                                started_at=NOW, completed_at=NOW + timedelta(seconds=1))
                    if case in {"commit-return", "historical-replay", "conflict", "begin-retry-actual-claim", "precommit-error"}:
                        result = unit.execute(**args)
                        expected = (TransactionTerminalStateV1.ROLLED_BACK if case == "precommit-error" else
                                    TransactionTerminalStateV1.CONFLICT if case == "conflict" else TransactionTerminalStateV1.COMMITTED)
                        assert result.transaction_state is expected
                        if case == "historical-replay":
                            assert result.committed_record_refs == (records.result_record_ref,)
                            assert counts == dict(begin=1, commit=0, rollback=1)
                        elif case == "begin-retry-actual-claim":
                            assert result.attempt_count == 2 and result.idempotency_claim_ref == "actual-acquired-claim"
                            assert counts == dict(begin=2, commit=1, rollback=0)
                        elif case in {"precommit-error", "conflict"}:
                            assert counts == dict(begin=1, commit=0, rollback=1)
                        else:
                            assert counts == dict(begin=1, commit=1, rollback=0)
                    else:
                        with pytest.raises((PersistenceContractError, TransactionContractError)) as caught:
                            unit.execute(**args)
                        if "rollback-stays-active" in case or case == "commit-cleanup-stays-active":
                            assert type(caught.value) is TransactionContractError
                            assert caught.value.reason_code is ReasonCode.TRANSACTION_STATE_INVALID
                            if case in {"rollback-stays-active", "commit-cleanup-stays-active"}:
                                assert caught.value.__cause__ is initiating
                        elif "rollback-error" in case or case == "commit-cleanup-error":
                            assert caught.value is cleanup
                            if case in {"rollback-error", "commit-cleanup-error"}:
                                assert caught.value.__cause__ is initiating
                        else:
                            assert caught.value is initiating
                        assert counts["begin"] == 1
                        expected_rollback = 0 if case in {"after-commit-error", "inactive-commit-error", "inactive-precommit-error"} else 1
                        assert counts["rollback"] == expected_rollback
                        assert counts["commit"] == (1 if case in {
                            "after-commit-error", "active-commit-error", "inactive-commit-error",
                            "commit-cleanup-error", "commit-cleanup-stays-active",
                        } else 0)
                    if assertion_failure is not None:
                        assert latest[-1].is_active
                        raise assertion_failure
            should_exist = historical or case in {"commit-return", "after-commit-error", "begin-retry-actual-claim"}
            assert (adapter.get_record(private.record_id) is not None) is should_exist
            assert (adapter.get_record(event.economic_event_id) is not None) is should_exist
            if should_exist:
                assert adapter.load_committed_private_clock_receipt_v1(private.record_id).typed_payload.canonical_payload_json == private.typed_payload.canonical_payload_json
        finally:
            _f13_close_owned_adapter(adapter)

    for case in (
        "commit-return", "after-commit-error", "active-commit-error", "inactive-commit-error",
        "precommit-error", "inactive-precommit-error", "rollback-error", "rollback-stays-active",
        "commit-cleanup-error", "commit-cleanup-stays-active",
        "historical-replay", "replay-rollback-error", "replay-rollback-stays-active",
        "conflict", "conflict-rollback-error", "begin-retry-actual-claim",
    ):
        run_case(case)

    initiating = AssertionError("synthetic coordinator-scope assertion")
    observation = {}
    with pytest.raises(AssertionError) as caught:
        run_case("rollback-error", assertion_failure=initiating, observation=observation)
    assert caught.value is initiating
    assert not observation["tx"].is_active
    assert observation["adapter"].begin_transaction == observation["begin"]
    assert observation["tx"].rollback == observation["rollback"]
    # The test's genuine cleanup is outside the production fault counters.
    assert observation["counts"] == dict(begin=1, commit=0, rollback=1)
    if adapter_kind == "sqlite":
        import sqlite3
        with pytest.raises(sqlite3.ProgrammingError):
            observation["adapter"]._connection.execute("SELECT 1")


REVERSAL_HISTORY_SCENARIOS = (
    "full-then-full",
    "partial-then-remainder",
    "partial-then-over",
    "same-key-replay",
    "same-key-conflict",
    "same-uow-original",
    "receipt-remaining-mismatch",
    "journal-link-bijection",
)


@pytest.mark.parametrize("adapter_kind", ("memory", "sqlite"))
@pytest.mark.parametrize("scenario", REVERSAL_HISTORY_SCENARIOS)
def test_persisted_reversal_history_matrix(
    adapter_kind, scenario, reference_directory
) -> None:
    adapter = (
        InMemoryPersistenceAdapterV1()
        if adapter_kind == "memory"
        else SQLiteReferenceAdapterV1(
            reference_directory / f"reversal-{scenario}.db",
            busy_timeout_ms=0,
            max_transaction_attempts=1,
        )
    )
    unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
    if scenario == "same-uow-original":
        original, original_postings = _journal()
        before = deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        )
        result = unit.execute(
            unit_of_work_id="uow-same-uow",
            records=_reversal_atomic_records(
                suffix="same-uow",
                original_transaction=original,
                original_postings=original_postings,
                reversal_transaction_id=original.journal_transaction_id,
            ),
            accounts=_accounts(),
            started_at=NOW,
            completed_at=NOW,
        )
        assert result.transaction_state is TransactionTerminalStateV1.ROLLED_BACK
        assert result.failure_code == ReasonCode.REVERSAL_INVALID.value
        assert deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        ) == before
        assert adapter.get_record("journal-1") is None
        if hasattr(adapter, "close"):
            adapter.close()
        return

    original_result = unit.execute(
        unit_of_work_id=f"uow-original-{scenario}",
        records=_atomic_records(),
        accounts=_accounts(),
        started_at=NOW,
        completed_at=NOW,
    )
    assert original_result.transaction_state is TransactionTerminalStateV1.COMMITTED

    if scenario == "journal-link-bijection":
        valid = _reversal_atomic_records(suffix="bijection")
        assert valid.journal_transaction is not None
        link = valid.reversal_links[0]
        before = deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        )
        mutations = (
            {"reversal_links": ()},
            {
                "journal_transaction": replace(
                    valid.journal_transaction,
                    reversal_of_transaction_id=None,
                )
            },
            {
                "reversal_links": (
                    replace(
                        link,
                        original_event_or_transaction_ref="journal-other",
                    ),
                )
            },
            {
                "reversal_links": (
                    replace(link, reversal_event_ref="event-other"),
                )
            },
        )
        for mutation in mutations:
            with pytest.raises(ComputationControlPlaneError):
                replace(valid, **mutation)
            assert deterministic_json(
                adapter.reconstruct_as_of(
                    effective_cutoff=NOW,
                    recorded_cutoff=NOW,
                    aggregate_scope=(),
                )
            ) == before
            assert (
                adapter.get_idempotency_result(
                    valid.idempotency_claim.idempotency_key
                )
                is None
            )
        unwritten_refs = (
            *(record.record_id for record in valid.receipt_records),
            *(event.economic_event_id for event in valid.economic_events),
            valid.journal_transaction.journal_transaction_id,
            *(posting.posting_id for posting in valid.journal_postings),
            valid.state_transition.transition_id,
            link.reversal_receipt_id,
        )
        assert all(adapter.get_record(ref) is None for ref in unwritten_refs)
        if hasattr(adapter, "close"):
            adapter.close()
        return

    if scenario == "receipt-remaining-mismatch":
        first_result = None
        proposed = _reversal_atomic_records(
            suffix="bad-remaining",
            remaining_override="0.01",
        )
    else:
        first_full = scenario == "full-then-full"
        first_records = _reversal_atomic_records(
            suffix="a",
            claim_key="key-reversal-a",
            request_token="full-a" if first_full else "partial-a",
            requested_amount=None if first_full else "0.40",
        )
        first_result = unit.execute(
            unit_of_work_id=f"uow-first-{scenario}",
            records=first_records,
            accounts=_accounts(),
            started_at=NOW,
            completed_at=NOW,
        )
        assert first_result.transaction_state is TransactionTerminalStateV1.COMMITTED
        if scenario == "full-then-full":
            proposed = _reversal_atomic_records(
                suffix="b", request_token="full-b", aggregate_version=3
            )
        elif scenario == "partial-then-remainder":
            proposed = _reversal_atomic_records(
                suffix="b",
                request_token="remainder-b",
                requested_amount="0.60",
                previously_reversed="0.40",
                aggregate_version=3,
            )
        elif scenario == "partial-then-over":
            proposed = _reversal_atomic_records(
                suffix="b",
                request_token="over-b",
                requested_amount="0.70",
                aggregate_version=3,
            )
        elif scenario == "same-key-replay":
            proposed = _reversal_atomic_records(
                suffix="b",
                claim_key="key-reversal-a",
                request_token="partial-a",
                requested_amount="0.40",
                aggregate_version=3,
            )
        else:
            proposed = _reversal_atomic_records(
                suffix="b",
                claim_key="key-reversal-a",
                request_token="conflicting-payload",
                requested_amount="0.40",
                aggregate_version=3,
            )

    before_second = deterministic_json(
        adapter.reconstruct_as_of(
            effective_cutoff=NOW,
            recorded_cutoff=NOW,
            aggregate_scope=(),
        )
    )
    second_result = unit.execute(
        unit_of_work_id=f"uow-second-{scenario}",
        records=proposed,
        accounts=_accounts(),
        started_at=NOW,
        completed_at=NOW,
    )
    if scenario == "partial-then-remainder":
        assert second_result.transaction_state is TransactionTerminalStateV1.COMMITTED
    elif scenario == "same-key-replay":
        assert second_result.transaction_state is TransactionTerminalStateV1.COMMITTED
        assert first_result is not None
        assert second_result.committed_record_refs == first_result.committed_record_refs[:1]
        assert deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        ) == before_second
    elif scenario == "same-key-conflict":
        assert second_result.transaction_state is TransactionTerminalStateV1.CONFLICT
        assert second_result.failure_code == ReasonCode.IDEMPOTENCY_CONFLICT.value
    else:
        assert second_result.transaction_state is TransactionTerminalStateV1.ROLLED_BACK
        assert second_result.failure_code == ReasonCode.REVERSAL_INVALID.value

    if scenario not in {"partial-then-remainder", "same-key-replay"}:
        assert deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        ) == before_second
        assert adapter.get_record(proposed.reversal_links[0].reversal_receipt_id) is None
        assert adapter.get_record(proposed.journal_transaction.journal_transaction_id) is None
        assert all(
            adapter.get_record(posting.posting_id) is None
            for posting in proposed.journal_postings
        )

    history_transaction = adapter.begin_transaction()
    history = adapter.load_committed_reversal_history(
        history_transaction, "journal-1"
    )
    history_transaction.rollback()
    assert all(
        row.cumulative_reversed_amount.decimal
        + row.remaining_reversible_amount.decimal
        == row.original_posting.magnitude
        for row in history.posting_history
    )
    if scenario in {"full-then-full", "partial-then-remainder"}:
        assert all(
            row.remaining_reversible_amount.decimal == 0
            for row in history.posting_history
        )
    if hasattr(adapter, "close"):
        adapter.close()


def _binary_book_snapshot(**changes) -> BinaryBookSnapshotV1:
    values = {
        "snapshot_ref": "book-snapshot",
        "sequence_ref": "sequence-5",
        "source_binding_ref": "source-binding",
        "unit": "USD",
        "basis": "PAYOUT",
        "yes_bids": ("0.40", "0.42"),
        "no_bids": ("0.50", "0.56"),
        "payout": "1.00",
        "book_sequence": 5,
        "expected_sequence": 5,
        "book_state": "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS",
        "active_price_grid_ranges": (
            ActivePriceGridRangeV1("0.00", "1.00", "0.01"),
        ),
    }
    values.update(changes)
    return BinaryBookSnapshotV1(**values)


def test_math_36_canonical_snapshot_and_compatibility_matrix(monkeypatch) -> None:
    assert TRANCHE_C_MATH_SPECIFICATIONS["MATH-36"].implementation is binary_book_implied_asks_v1
    assert TRANCHE_C_IMPLEMENTATION_REGISTRY["MATH-36"].callable is binary_book_implied_asks_v1
    assert IMPLEMENTATION_REGISTRY["MATH-36"].callable is compute_math_36_kalshi_binary_book_transform

    snapshot = _binary_book_snapshot()
    canonical = binary_book_implied_asks_v1(snapshot=snapshot)
    calls: list[BinaryBookSnapshotV1] = []

    def _canonical_spy(*, snapshot):
        calls.append(snapshot)
        return binary_book_implied_asks_v1(snapshot=snapshot)

    monkeypatch.setattr(
        implementation_registry_module,
        "binary_book_implied_asks_v1",
        _canonical_spy,
    )
    compatibility = compute_math_36_kalshi_binary_book_transform(
        snapshot.yes_bids,
        snapshot.no_bids,
        snapshot.payout,
        snapshot.book_sequence,
        snapshot.expected_sequence,
        snapshot.book_state,
        ({"minimum": "0.00", "maximum": "1.00", "step": "0.01"},),
    )
    assert len(calls) == 1
    assert compatibility == {
        "best_yes_bid": Decimal("0.42"),
        "best_no_bid": Decimal("0.56"),
        "derived_yes_ask": canonical.yes_implied_ask,
        "derived_no_ask": canonical.no_implied_ask,
        "book_sequence": canonical.book_sequence,
    }
    assert (
        canonical.snapshot_ref,
        canonical.sequence_ref,
        canonical.source_binding_ref,
        canonical.book_sequence,
    ) == (
        snapshot.snapshot_ref,
        snapshot.sequence_ref,
        snapshot.source_binding_ref,
        snapshot.book_sequence,
    )
    mutations = (
        {"expected_sequence": 4},
        {"book_state": "NONCONTIGUOUS"},
        {"yes_bids": ("0.405", "0.42")},
        {"payout": "1.005"},
    )
    for mutation in mutations:
        with pytest.raises(ComputationControlPlaneError):
            _binary_book_snapshot(**mutation)


def _parameter_evidence(
    parameter_id: str,
    evidence_class: TrancheCParameterEvidenceClassV1,
    *,
    evidence_ref: str | None = None,
    **changes,
) -> TrancheCParameterEvidenceV1:
    policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
    binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
    values = {
        "evidence_class": evidence_class,
        "evidence_ref": evidence_ref or f"evidence::{parameter_id}",
        "family_evidence_binding_ref": str(
            policy.raw["family_evidence_binding_ref"]
        ),
        "value_source_class": str(policy.raw["effective_value_source_class"]),
        "source_or_binding_refs": tuple(
            policy.raw["effective_source_state_refs"]
        ),
        "source_currentization_refs": tuple(
            policy.raw["source_currentization_refs"]
        ),
        "active_scope_ref": str(policy.raw["master_plan_section_id"]),
        "source_epoch_ref": str(policy.raw["currentization_version"]),
        "canonical_owner_ref": policy.canonical_owner,
        "authority_ref": binding.active_stage1_value_authority,
        "declared_unit_or_basis": str(policy.raw["effective_unit_or_basis"]),
        "observed_at": DYNAMIC_OBSERVED_AT,
        "evaluated_at": DYNAMIC_EVALUATED_AT,
        "valid_until": DYNAMIC_VALID_UNTIL,
        "constraint_refs": (
            policy.reference_range_or_constraint,
            str(policy.raw["effective_bounded_search_space_or_fit_constraint"]),
            str(policy.raw["effective_unit_or_basis"]),
        ),
    }
    values.update(changes)
    return TrancheCParameterEvidenceV1(**values)


def _drawdown_calibration_artifact(
    **changes,
) -> TrancheCDrawdownCalibrationArtifactV1:
    policy = TRANCHE_C_PARAMETER_POLICIES["ST10-PARAM::1531"]
    binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS["ST10-PARAM::1531"]
    values = {
        "calibration_bundle_ref": "calibration::drawdown-ra-11b",
        "approved_sleeve_max_drawdown_budget": Decimal("0.10"),
        "warning_threshold": Decimal("0.05"),
        "freeze_threshold": Decimal("0.10"),
        "canonical_owner_ref": policy.canonical_owner,
        "authority_ref": binding.active_stage1_value_authority,
        "active_scope_ref": str(policy.raw["master_plan_section_id"]),
        "source_epoch_ref": str(policy.raw["currentization_version"]),
        "observed_at": DYNAMIC_OBSERVED_AT,
        "evaluated_at": DYNAMIC_EVALUATED_AT,
        "valid_until": DYNAMIC_VALID_UNTIL,
    }
    values.update(changes)
    return TrancheCDrawdownCalibrationArtifactV1(**values)


PARAMETER_ADMISSIBILITY_CASES = (
    "fixed-pass",
    "fixed-alternate",
    "singleton-pass",
    "singleton-alternate",
    "bounded-pass",
    "bounded-outside",
    "bounded-wrong-type",
    "bounded-wrong-unit",
    "source-pass",
    "source-missing-evidence",
    "calibration-pass",
    "calibration-missing-evidence",
    "unsupported-structural-constraint",
)


@pytest.mark.parametrize("case", PARAMETER_ADMISSIBILITY_CASES)
def test_parameter_admissibility_matrix(case) -> None:
    fixed_id = "ST10-PARAM::0115"
    singleton_id = "ST10-PARAM::1544"
    bounded_id = "ST10-PARAM::0064"
    source_id = "ST10-PARAM::3277"
    calibration_id = "ST10-PARAM::1531"
    structural_id = "ST10-PARAM::3797"
    parameter_id = {
        "fixed-pass": fixed_id,
        "fixed-alternate": fixed_id,
        "singleton-pass": singleton_id,
        "singleton-alternate": singleton_id,
        "bounded-pass": bounded_id,
        "bounded-outside": bounded_id,
        "bounded-wrong-type": bounded_id,
        "bounded-wrong-unit": bounded_id,
        "source-pass": source_id,
        "source-missing-evidence": source_id,
        "calibration-pass": calibration_id,
        "calibration-missing-evidence": calibration_id,
        "unsupported-structural-constraint": structural_id,
    }[case]
    policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
    binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
    value: object = policy.day1_seed_or_resolution_rule
    unit: str | None = None
    evidence: TrancheCParameterEvidenceV1 | None = None
    calibration_artifact: TrancheCDrawdownCalibrationArtifactV1 | None = None
    expected_pass = case.endswith("pass")
    if case == "fixed-alternate":
        value = "ALLOWED"
    elif case == "singleton-pass":
        value, unit = Decimal("1.0"), "gross leverage cap"
    elif case == "singleton-alternate":
        value, unit = Decimal("1.1"), "gross leverage cap"
    elif case == "bounded-pass":
        value, unit = Decimal("0.00"), "USD"
    elif case == "bounded-outside":
        value, unit = Decimal("-0.01"), "USD"
    elif case == "bounded-wrong-type":
        value, unit = "0.00", "USD"
    elif case == "bounded-wrong-unit":
        value, unit = Decimal("0.00"), "EUR"
    elif case.startswith("source"):
        unit = str(policy.raw["effective_unit_or_basis"])
        if case == "source-pass":
            evidence = _parameter_evidence(
                parameter_id,
                TrancheCParameterEvidenceClassV1.SOURCE_OR_RUNTIME_BINDING,
            )
    elif case.startswith("calibration"):
        value = Decimal("0.05")
        unit = str(policy.raw["effective_unit_or_basis"])
        if case == "calibration-pass":
            calibration_artifact = _drawdown_calibration_artifact()
            evidence = _parameter_evidence(
                parameter_id,
                TrancheCParameterEvidenceClassV1.CALIBRATED_ARTIFACT,
                evidence_ref=calibration_artifact.calibration_bundle_ref,
            )
    elif case == "unsupported-structural-constraint":
        value = {"id_": "EXACT_CONTRACT_OR_PACKET_IDENTITY"}

    explicit = TrancheCExplicitParameterValueV1(
        parameter_id=parameter_id,
        value=value,
        canonical_owner=policy.canonical_owner,
        authority_ref=binding.active_stage1_value_authority,
        source_packet_ref=(
            evidence.evidence_ref
            if evidence is not None
            else f"packet::{case}"
        ),
        declared_unit_or_basis=unit,
        evidence=evidence,
        drawdown_calibration_artifact=calibration_artifact,
    )
    resolution_at = (
        DYNAMIC_RESOLUTION_AT
        if TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES[parameter_id]
        in {
            TrancheCParameterPolicyClassV1.SOURCE_OR_RUNTIME_BOUND,
            TrancheCParameterPolicyClassV1.CALIBRATION_REQUIRED,
        }
        else None
    )
    if not expected_pass:
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=explicit,
                resolution_at=resolution_at,
            )
        return
    resolved = resolve_tranche_c_parameter_v1(
        parameter_id,
        explicit_value=explicit,
        resolution_at=resolution_at,
    )
    assert resolved.admissibility_receipt.terminal_state == "PASS"
    assert (
        resolved.value_or_rule
        == resolved.admissibility_receipt.canonical_normalized_value
    )
    assert resolved.admissibility_receipt.policy_class is TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES[parameter_id]


def test_dynamic_parameter_evidence_compound_matrix() -> None:
    source_ids = tuple(
        parameter_id
        for parameter_id, policy_class in
        TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES.items()
        if policy_class
        is TrancheCParameterPolicyClassV1.SOURCE_OR_RUNTIME_BOUND
    )
    assert len(source_ids) == 2
    for parameter_id in source_ids:
        policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
        binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
        evidence = _parameter_evidence(
            parameter_id,
            TrancheCParameterEvidenceClassV1.SOURCE_OR_RUNTIME_BINDING,
        )
        explicit = TrancheCExplicitParameterValueV1(
            parameter_id=parameter_id,
            value=policy.day1_seed_or_resolution_rule,
            canonical_owner=policy.canonical_owner,
            authority_ref=binding.active_stage1_value_authority,
            source_packet_ref=evidence.evidence_ref,
            declared_unit_or_basis=str(policy.raw["effective_unit_or_basis"]),
            evidence=evidence,
        )
        resolved = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=explicit,
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
        receipt = resolved.admissibility_receipt
        assert (
            receipt.active_scope_ref,
            receipt.source_epoch_ref,
            receipt.family_evidence_binding_ref,
            receipt.value_source_class,
            receipt.resolution_at,
        ) == (
            evidence.active_scope_ref,
            evidence.source_epoch_ref,
            evidence.family_evidence_binding_ref,
            evidence.value_source_class,
            DYNAMIC_RESOLUTION_AT,
        )
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=explicit,
            )
        future_observed = datetime(2026, 1, 1, 0, 3, tzinfo=UTC)
        evidence_mutations = (
            {"valid_until": DYNAMIC_RESOLUTION_AT},
            {
                "observed_at": future_observed,
                "evaluated_at": future_observed,
            },
            {"active_scope_ref": "WRONG_SCOPE"},
            {"source_epoch_ref": "WRONG_EPOCH"},
            {"value_source_class": "WRONG_VALUE_SOURCE"},
            {"family_evidence_binding_ref": "WRONG_FAMILY_BINDING"},
            {"source_or_binding_refs": ("WRONG_SOURCE_STATE",)},
            {"source_currentization_refs": ("WRONG_CURRENTIZATION",)},
            {"authority_ref": "WRONG_AUTHORITY"},
            {"canonical_owner_ref": "WRONG_OWNER"},
            {"declared_unit_or_basis": "WRONG_UNIT"},
        )
        for mutation in evidence_mutations:
            bad_evidence = replace(evidence, **mutation)
            with pytest.raises(ComputationControlPlaneError):
                resolve_tranche_c_parameter_v1(
                    parameter_id,
                    explicit_value=replace(explicit, evidence=bad_evidence),
                    resolution_at=DYNAMIC_RESOLUTION_AT,
                )
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=replace(explicit, value="AMBIGUOUS_TOKEN"),
                resolution_at=DYNAMIC_RESOLUTION_AT,
            )
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=replace(
                    explicit,
                    authority_ref="WRONG_AUTHORITY",
                    declared_unit_or_basis="WRONG_UNIT",
                ),
                resolution_at=DYNAMIC_RESOLUTION_AT,
            )

    drawdown_bundle = _drawdown_calibration_artifact()
    drawdown_resolutions = {}
    for parameter_id, value in (
        ("ST10-PARAM::1531", drawdown_bundle.warning_threshold),
        ("ST10-PARAM::1532", drawdown_bundle.freeze_threshold),
    ):
        policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
        binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
        evidence = _parameter_evidence(
            parameter_id,
            TrancheCParameterEvidenceClassV1.CALIBRATED_ARTIFACT,
            evidence_ref=drawdown_bundle.calibration_bundle_ref,
        )
        explicit = TrancheCExplicitParameterValueV1(
            parameter_id=parameter_id,
            value=value,
            canonical_owner=policy.canonical_owner,
            authority_ref=binding.active_stage1_value_authority,
            source_packet_ref=evidence.evidence_ref,
            declared_unit_or_basis=str(policy.raw["effective_unit_or_basis"]),
            evidence=evidence,
            drawdown_calibration_artifact=drawdown_bundle,
        )
        drawdown_resolutions[parameter_id] = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=explicit,
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
    assert drawdown_resolutions["ST10-PARAM::1531"].value_or_rule == Decimal("0.05")
    assert drawdown_resolutions["ST10-PARAM::1532"].value_or_rule == Decimal("0.10")
    assert {
        resolution.admissibility_receipt.calibration_bundle_ref
        for resolution in drawdown_resolutions.values()
    } == {drawdown_bundle.calibration_bundle_ref}

    warning_policy = TRANCHE_C_PARAMETER_POLICIES["ST10-PARAM::1531"]
    warning_binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS["ST10-PARAM::1531"]
    warning_evidence = _parameter_evidence(
        "ST10-PARAM::1531",
        TrancheCParameterEvidenceClassV1.CALIBRATED_ARTIFACT,
        evidence_ref=drawdown_bundle.calibration_bundle_ref,
    )
    warning_explicit = TrancheCExplicitParameterValueV1(
        parameter_id="ST10-PARAM::1531",
        value=drawdown_bundle.warning_threshold,
        canonical_owner=warning_policy.canonical_owner,
        authority_ref=warning_binding.active_stage1_value_authority,
        source_packet_ref=warning_evidence.evidence_ref,
        declared_unit_or_basis=str(
            warning_policy.raw["effective_unit_or_basis"]
        ),
        evidence=warning_evidence,
        drawdown_calibration_artifact=drawdown_bundle,
    )
    with pytest.raises(ComputationControlPlaneError):
        resolve_tranche_c_parameter_v1(
            "ST10-PARAM::1531",
            explicit_value=replace(
                warning_explicit,
                drawdown_calibration_artifact=None,
            ),
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
    artifact_mutations = (
        {"approved_sleeve_max_drawdown_budget": None},
        {"approved_sleeve_max_drawdown_budget": 0.1},
        {"approved_sleeve_max_drawdown_budget": Decimal("NaN")},
        {"freeze_threshold": Decimal("Infinity")},
        {"warning_threshold": Decimal("0.04")},
        {"freeze_threshold": Decimal("0.09")},
        {
            "warning_threshold": Decimal("0.10"),
            "freeze_threshold": Decimal("0.10"),
        },
        {"active_scope_ref": "WRONG_SCOPE"},
        {"source_epoch_ref": "WRONG_EPOCH"},
        {"canonical_owner_ref": "WRONG_OWNER"},
        {"authority_ref": "WRONG_AUTHORITY"},
        {"valid_until": DYNAMIC_RESOLUTION_AT},
        {"calibration_bundle_ref": "calibration::mixed-bundle"},
    )
    for mutation in artifact_mutations:
        with pytest.raises(ComputationControlPlaneError):
            mutated_bundle = _drawdown_calibration_artifact(**mutation)
            resolve_tranche_c_parameter_v1(
                "ST10-PARAM::1531",
                explicit_value=replace(
                    warning_explicit,
                    drawdown_calibration_artifact=mutated_bundle,
                ),
                resolution_at=DYNAMIC_RESOLUTION_AT,
            )


def test_control_coverage_meta_matrix() -> None:
    validate_st12c_control_coverage_matrix()
    rows = ST12C_CONTROL_COVERAGE_MATRIX
    assert len(rows) == 25
    assert sum(row.domain == "accounting" for row in rows) == 16
    assert sum(row.domain == "execution" for row in rows) == 9
    assert len(ST12C_ORIGINAL_TEST_TO_MATRIX_LOCATOR) == 25
    assert {math_id for row in rows for math_id in row.math_oracle_vector_links} == {f"MATH-{number}" for number in range(26, 39)}
    root = Path(__file__).resolve().parents[1]
    assert tuple(path.name for path in (root / "accounting").glob("test_*.py")) == ("test_contract_matrix.py",)
    assert tuple(path.name for path in (root / "execution").glob("test_*.py")) == ("test_contract_matrix.py",)
    repo_root = Path(__file__).resolve().parents[4]
    assert (repo_root / "tools" / "independent_validate_qku_computation_control_plane_accounting.py").is_file()
    assert (repo_root / "tools" / "independent_validate_qku_computation_control_plane_execution.py").is_file()
    assert len(rows) + 2 == 27
    assert len(TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES) == 80
    assert set(TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES) == set(TRANCHE_C_PARAMETER_POLICIES)
    assert set(TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES.values()) == set(TrancheCParameterPolicyClassV1)
    source_bound = tuple(
        parameter_id
        for parameter_id, policy in TRANCHE_C_PARAMETER_POLICIES.items()
        if policy.applicability_state == "SOURCE_BOUND_MUTABLE_VALUE"
    )
    assert len(source_bound) == 2
    for parameter_id in source_bound:
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(parameter_id)
        policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
        binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
        evidence = _parameter_evidence(
            parameter_id,
            TrancheCParameterEvidenceClassV1.SOURCE_OR_RUNTIME_BINDING,
        )
        resolved = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=TrancheCExplicitParameterValueV1(
                parameter_id,
                policy.day1_seed_or_resolution_rule,
                policy.canonical_owner,
                binding.active_stage1_value_authority,
                evidence.evidence_ref,
                str(policy.raw["effective_unit_or_basis"]),
                evidence,
            ),
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
        assert resolved.authority_ref == binding.active_stage1_value_authority
        assert resolved.admissibility_receipt.terminal_state == "PASS"
    dormant = next(
        parameter_id
        for parameter_id, policy in TRANCHE_C_PARAMETER_POLICIES.items()
        if policy.applicability_state == "DORMANT_FUTURE_MARKET_PRESERVED_FAIL_CLOSED"
    )
    with pytest.raises(ComputationControlPlaneError):
        resolve_tranche_c_parameter_v1(dormant)


def _f14_offline_owners(patch, operation, *, proofs=0):
    from datetime import UTC, datetime, timedelta
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as source
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import PrivateObservationPublisherV1
    from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
        bind_private_runtime_credential_v1, RetailPrivateIngressV1, RetailPrivateReadRequestV1)
    from tests.source_evidence.test_s1_pit_data_phase_a_01 import _f14_reference_cases
    args, expected = next((args, expected) for args, expected in _f14_reference_cases()
        if args[2]['operation'] == operation)
    now = datetime(2026, 9, 13, 0, 0, 1, tzinfo=UTC)
    delta = now - datetime(1970, 1, 1, tzinfo=UTC)
    wall = (delta.days * 86400 + delta.seconds) * 1_000_000_000
    ticker = [1000, wall]
    def mono():
        ticker[0] += 1000
        return ticker[0]
    def wall_clock():
        ticker[1] += 1000
        return ticker[1]
    patch.setattr(source.time, 'monotonic_ns', mono)
    patch.setattr(source.time, 'time_ns', wall_clock)
    start, end = now - timedelta(minutes=1), now + timedelta(hours=1)
    profile = source.Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
    current = source.PITSourceCurrentizationReceiptV1('current', profile, 'source', '1', start, start,
        end, 'synthetic-currentization', ('SOURCE_CHANGE',), False, True)
    rights = source.PITRightsAdmissionReceiptV1('rights', profile, 'account', 'source', 'agreement', '1',
        'SYNTHETIC_INTERNAL_USE', 'ADMITTED_INTERNAL_USE', start, end, ('RIGHTS_CHANGE',), False,
        'SYNTHETIC_RETAIN', 'NO_REDISTRIBUTION')
    session = source.RetailPrivateSessionBindingV1(dict(args[0]['scope']), 'snapshot', 'authentication',
        'session', 7, current, rights, start, end, (operation,))
    registry = source.RetailPrivateSourceRegistryV1(process_epoch_id='process', monotonic_clock_id='monotonic')
    registry.bind_session(session)
    grant = source.RetailPrivateRuntimeGrantV1('grant', session, start, end, 'process', 'monotonic',
        'synthetic-wall', 'synthetic-clock-quality', 1, 1, 10**12, 3)
    registry.issue_grant(grant)
    # Public RFC8032 empty-message known-answer vector, never operational credentials.
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
        '9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60'))
    assert key.sign(b'').hex() == ('e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555f'
        'b8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b')
    handle = bind_private_runtime_credential_v1(session_binding=session,
        api_key_id='00000000-0000-4000-8000-000000000014', private_key=key, source_registry=registry)
    assert '9d61' not in repr(handle) and '00000000' not in repr(handle)
    requirement = dict(args[3]['requirements'])
    facts = {}
    for role, flag in tuple(zip(('publication','revision','finality'),
            ('requires_provider_publication_time','requires_revision_at_decision','requires_finality_at_decision')))[:proofs]:
        requirement[flag] = True
        if role == 'publication': requirement['provider_publication_time_is_source_proven'] = True
        facts[role] = dict(timestamp='2026-09-13T00:00:00.000000000Z',
            source_record_ref='current', source_binding_ref='source')
    registry.bind_clock_facts(grant_id=grant.grant_id, request_ref=args[2]['request_ref'],
        item_key=args[2]['item_key'], facts_by_role=facts)
    request = RetailPrivateReadRequestV1(grant, operation, dict(args[2]), None, requirement, 65536)
    ingress = RetailPrivateIngressV1(source_registry=registry, credential_handle=handle)
    publisher = PrivateObservationPublisherV1(source_registry=registry)
    return request, ingress, registry, publisher, args[3]['original_raw_body'], expected, ticker


def _f14_scripted_transport(patch, request, ingress, raw, *, failure=None, on_native_event=None):
    import base64, json, ssl, types
    calls = []
    def signature(headers, path):
        assert set(headers) == ({'X-PM-Access-Key', 'X-PM-Timestamp', 'X-PM-Signature'}
            | ({'Accept', 'Accept-Encoding'} if not request.operation.startswith('WS_') else set()))
        if not request.operation.startswith('WS_'):
            assert headers['Accept-Encoding'] == 'identity' and headers['Accept'] == 'application/json'
        message = (headers['X-PM-Timestamp'] + 'GET' + path).encode('ascii')
        ingress.credential_handle.private_key.public_key().verify(base64.b64decode(headers['X-PM-Signature']), message)
    class Rest:
        status = 200
        def request(self, method, target, body, headers):
            calls.append('request')
            assert ingress.source_registry._remaining[request.grant.grant_id] == 0
            assert method == 'GET' and body is None and target.startswith('/v1/')
            signature(headers, target.split('?')[0])
            if failure == 'request': raise TimeoutError('synthetic transport timeout')
        def getresponse(self): return self
        def getheaders(self):
            return [('Content-Type','application/json; charset=utf-8'), ('Content-Length',str(len(raw)))] + (
                [('Content-Length',str(len(raw)))] if failure == 'duplicate_length' else [])
        def read(self, amount):
            calls.append('read')
            assert amount == request.maximum_raw_bytes + 1
            if on_native_event is not None: on_native_event('received')
            if failure == 'revoke': ingress.source_registry.revoke(request.grant.session_binding, 8)
            if failure == 'deadline':
                patch.setattr(ingress.source_registry._validate_grant_v1.__globals__['time'],
                    'monotonic_ns', lambda: request.grant.deadline_monotonic_ns)
            return raw
        def close(self): calls.append('close')
    def rest(host, port, *, timeout, context):
        calls.append('construct')
        assert host == 'api.polymarket.us' and port == 443 and 0 < timeout <= 10
        assert context.check_hostname is True and context.verify_mode == ssl.CERT_REQUIRED
        if on_native_event is not None: on_native_event('constructed')
        return Rest()
    class WS:
        response = types.SimpleNamespace(status_code=101)
        def __enter__(self): return self
        def __exit__(self, *unused): calls.append('close')
        def send(self, subscription):
            calls.append('subscribe')
            body = json.loads(subscription)['subscribe']
            assert body['requestId'] == request.consumer['request_ref']
        def recv(self, *, timeout):
            calls.append('recv')
            assert timeout > 0
            if on_native_event is not None: on_native_event('received')
            if failure == 'binary': return raw
            if request.operation == 'WS_BALANCE' and calls.count('recv') == 1:
                return json.dumps(dict(requestId='request', subscriptionType='SUBSCRIPTION_TYPE_ACCOUNT_BALANCE',
                    accountBalancesSnapshot={'balances':[{'currency':'USD','currentBalance':100,'buyingPower':100}]}))
            return raw.decode('utf-8')
    def ws(uri, **kwargs):
        calls.append('connect')
        assert set(kwargs) == {'ssl', 'additional_headers', 'proxy', 'compression',
            'open_timeout', 'ping_interval', 'ping_timeout', 'close_timeout',
            'max_size', 'max_queue', 'logger'}
        assert ingress.source_registry._remaining[request.grant.grant_id] == 0
        assert uri == 'wss://api.polymarket.us/v1/ws/private'
        assert kwargs['proxy'] is None and kwargs['compression'] is None
        assert (kwargs['ping_interval'], kwargs['ping_timeout'], kwargs['close_timeout'], kwargs['max_queue']) == (20,20,10,16)
        assert 0 < kwargs['open_timeout'] <= 10 and kwargs['max_size'] == request.maximum_raw_bytes
        assert kwargs['logger'].disabled and not kwargs['logger'].propagate
        signature(kwargs['additional_headers'], '/v1/ws/private')
        if on_native_event is not None: on_native_event('constructed')
        return WS()
    modules = {name: types.ModuleType(name) for name in
        ('http', 'http.client', 'websockets', 'websockets.sync', 'websockets.sync.client')}
    for name in ('http', 'websockets', 'websockets.sync'):
        modules[name].__path__ = []
    modules['http'].client = modules['http.client']
    modules['http.client'].HTTPSConnection = rest
    modules['websockets'].sync = modules['websockets.sync']
    modules['websockets.sync'].client = modules['websockets.sync.client']
    modules['websockets.sync.client'].connect = ws
    return calls, modules


def _f14_fresh_adapter(kind):
    return (InMemoryPersistenceAdapterV1() if kind == 'memory' else
        SQLiteReferenceAdapterV1(':memory:', busy_timeout_ms=0, max_transaction_attempts=1))


def _assert_f14_native_and_storage(adapter_kind):
    import copy, sys
    from dataclasses import replace
    from src.qtt.stage1_prediction_markets.private_state_receipts import handoff
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import serialization as codec
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
        PrivateEvidenceReadRequestV1, _f14_reconstruct_snapshot_v1)
    from tests.source_evidence.test_s1_pit_data_phase_a_01 import _f14_reference_cases
    absent = object()
    for operation, boundary in ((operation, boundary) for operation in ('BALANCES', 'WS_POSITION')
            for boundary in ('reservation', 'constructed', 'received')):
        for competition in ('distinct_request', 'same_request_other_publisher'):
            with pytest.MonkeyPatch.context() as patch:
                request, ingress, registry, publisher, raw, expected, _ = _f14_offline_owners(patch, operation)
                other_grant = replace(request.grant, grant_id='competing-grant')
                registry.issue_grant(other_grant)
                registry.bind_clock_facts(grant_id=other_grant.grant_id,
                    request_ref=request.consumer['request_ref'], item_key=request.consumer['item_key'],
                    facts_by_role={})
                other_request = type(request)(other_grant, operation, handoff._f14_plain_v1(request.consumer),
                    None, handoff._f14_plain_v1(request.requirements), request.maximum_raw_bytes)
                other_publisher = type(publisher)(source_registry=registry)
                adapter = _f14_fresh_adapter(adapter_kind)
                calls, modules = _f14_scripted_transport(patch, request, ingress, raw,
                    on_native_event=lambda stage: competing_call() if stage == boundary else None)
                originals = {name: sys.modules.get(name, absent) for name in modules}
                reentries = []
                acquired_tokens, cleanup_calls, commits = [], [], []
                finish = ingress._finish_attempt_v1
                execute = handoff.TrancheCUnitOfWorkV1.execute
                def recorded_finish(token):
                    cleanup_calls.append(token)
                    return finish(token)
                def recorded_commit(unit, **kwargs):
                    committed = execute(unit, **kwargs)
                    commits.append((kwargs, committed))
                    return committed
                patch.setattr(ingress, '_finish_attempt_v1', recorded_finish)
                patch.setattr(handoff.TrancheCUnitOfWorkV1, 'execute', recorded_commit)
                def competing_call():
                    state = dict(vars(ingress))
                    token = ingress._coordinator_token
                    assert token is not None and token is not request
                    assert ingress._active_request is (None if boundary == 'reservation' else request)
                    if boundary == 'received' and operation == 'BALANCES':
                        assert ingress._response_headers is not None and ingress._charged is True
                    remaining = dict(registry._remaining)
                    requests = dict(publisher._requests)
                    before_calls = list(calls)
                    before_cleanup = list(cleanup_calls)
                    contender = other_request if competition == 'distinct_request' else request
                    target = publisher if competition == 'distinct_request' else other_publisher
                    with pytest.raises(ComputationControlPlaneError, match='F14_INGRESS_ATTEMPT_ACTIVE'):
                        handoff.run_retail_private_observation_once_v1(contender, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=target)
                    assert set(vars(ingress)) == set(state)
                    assert all(getattr(ingress, key) is value for key, value in state.items())
                    assert registry._remaining == remaining and calls == before_calls
                    assert publisher._requests == requests and not other_publisher._requests
                    assert not publisher._slots and not other_publisher._slots
                    assert cleanup_calls == before_cleanup
                    for foreign in (None, object(), request, other_request):
                        ingress._finish_attempt_v1(foreign)
                        assert all(getattr(ingress, key) is value for key, value in state.items())
                    acquired_tokens.append(token)
                    reentries.append(competition)
                class Reservations(dict):
                    def __setitem__(self, key, value):
                        if boundary == 'reservation' and key == id(request) and value[1] is None:
                            competing_call()
                        return super().__setitem__(key, value)
                publisher._requests = Reservations()
                try:
                    with pytest.MonkeyPatch.context() as patcher:
                        for key, value in modules.items():
                            patcher.setitem(sys.modules, key, value)
                        result = handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=publisher)
                        assert result['selected_values'] == expected['selected_values']
                        assert all(value is False for value in result.values() if type(value) is bool)
                        assert reentries == [competition] and calls[-1] == 'close'
                        assert registry._remaining == {'grant': 0, 'competing-grant': 1}
                        assert len(acquired_tokens) == 1 and cleanup_calls[-1] is acquired_tokens[0]
                        assert ingress._coordinator_token is None and ingress._active_request is None
                        assert ingress._prepared is None and ingress._attempt_id is None
                        assert ingress._response_headers is None and ingress._charged is False
                        cached_calls = []
                        def cached_during_next():
                            state = dict(vars(ingress))
                            token = ingress._coordinator_token
                            assert token is not None and token is not acquired_tokens[0]
                            assert ingress._active_request is other_request
                            remaining = dict(registry._remaining)
                            before_calls, before_cleanup = list(next_calls), list(cleanup_calls)
                            requests = dict(publisher._requests)
                            assert handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                                source_registry=registry, adapter=adapter, publisher=publisher) == result
                            assert cleanup_calls == before_cleanup
                            for foreign in (acquired_tokens[0], object(), None, other_request):
                                ingress._finish_attempt_v1(foreign)
                                assert all(getattr(ingress, key) is value for key, value in state.items())
                            assert registry._remaining == remaining and next_calls == before_calls
                            assert publisher._requests == requests
                            cached_calls.append(token)
                        next_calls, next_modules = _f14_scripted_transport(patch, other_request, ingress, raw,
                            on_native_event=lambda stage: cached_during_next() if stage == 'constructed' else None)
                        with pytest.MonkeyPatch.context() as next_patcher:
                            for key, value in next_modules.items():
                                next_patcher.setitem(sys.modules, key, value)
                            next_result = handoff.run_retail_private_observation_once_v1(other_request, ingress=ingress,
                                source_registry=registry, adapter=adapter, publisher=publisher)
                        assert next_result['selected_values'] == expected['selected_values']
                        assert all(value is False for value in next_result.values() if type(value) is bool)
                        assert len(cached_calls) == 1 and cleanup_calls[-1] is cached_calls[0]
                        assert next_calls[-1] == 'close' and registry._remaining == {'grant': 0, 'competing-grant': 0}
                        assert ingress._coordinator_token is None and ingress._active_request is None
                        assert ingress._prepared is None and ingress._attempt_id is None
                        assert ingress._response_headers is None and ingress._charged is False
                        assert len(commits) == 6
                        assert all(row[1].transaction_state is TransactionTerminalStateV1.COMMITTED for row in commits)
                        assert [row[0]['unit_of_work_id'].split(':')[-2] for row in commits] == ['A', 'B', 'C'] * 2
                        assert len(registry._captures) == 2
                        for entry in registry._captures.values():
                            read = handoff._f14_allocation_v1(request.grant.session_binding.scope, entry[4], ())
                            snapshot = adapter.load_committed_private_evidence_snapshot_v1(read)
                            immutable_read = PrivateEvidenceReadRequestV1(read.scope, read.record_refs, read.phase_control_refs)
                            assert adapter.load_committed_private_evidence_snapshot_v1(immutable_read) == snapshot
                            assert len(snapshot.present_record_refs) == 16
                            raw_row = adapter.load_committed_private_evidence_witness_v1(read.record_refs['raw'])
                            assert codec._f14_load_canonical_v1(raw_row.typed_payload.canonical_payload_json,
                                codec._F14_PHASES['RAW'])['raw_body_utf8'].encode('utf-8') == raw
                            for extra in (None, False, True, 0, 'extra', [], (), {}):
                                with pytest.raises(ComputationControlPlaneError):
                                    adapter.load_committed_private_evidence_snapshot_v1(PrivateEvidenceReadRequestV1(
                                        read.scope, read.record_refs, {**read.phase_control_refs, 'EXTRA': extra}))
                            assert adapter.load_committed_private_evidence_snapshot_v1(read) == snapshot
                finally:
                    try:
                        for key, original in originals.items():
                            if original is absent:
                                assert key not in sys.modules
                            else:
                                assert key in sys.modules and sys.modules[key] is original
                    finally:
                        if adapter_kind == 'sqlite': adapter.close()
    from contextlib import contextmanager
    from src.qtt.stage1_prediction_markets.private_state_receipts import request as request_owner
    for boundary in ('fence_exit', 'reserve', 'prepare', 'sign', 'charge', 'receive', 'store', 'publication', 'resolve'):
        with pytest.MonkeyPatch.context() as patch:
            request, ingress, registry, publisher, raw, expected, _ = _f14_offline_owners(patch, 'BALANCES')
            adapter = _f14_fresh_adapter(adapter_kind)
            calls, modules = _f14_scripted_transport(patch, request, ingress, raw,
                on_native_event=lambda stage: fail() if boundary == 'receive' and stage == 'received' else None)
            originals = {name: sys.modules.get(name, absent) for name in modules}
            cleanups, failures, charges = [], [], []
            finish, charge, fenced, observe = (ingress._finish_attempt_v1, registry._charge_v1,
                registry.fenced, registry._observe_v1)
            def cleanup(token):
                assert token is ingress._coordinator_token and token is not None
                cleanups.append((token, registry._remaining[request.grant.grant_id]))
                return finish(token)
            def fail(*args, **kwargs):
                assert ingress._coordinator_token is not None
                failures.append(boundary)
                raise RuntimeError('scripted ' + boundary + ' failure')
            def charged(grant, operation):
                charge(grant, operation)
                charges.append(grant.grant_id)
                if boundary == 'charge': fail()
            @contextmanager
            def failing_fence(*args, **kwargs):
                with fenced(*args, **kwargs) as session:
                    yield session
                    if not failures: fail()
            class FailedReservation(dict):
                def __setitem__(self, key, value):
                    super().__setitem__(key, value)
                    if key == id(request) and value[1] is None: fail()
            def publication_clock(grant):
                if publisher._slots and not failures:
                    assert all(slot['state'] == 'OUTCOME_UNKNOWN' for slot in publisher._slots.values())
                    fail()
                return observe(grant)
            patch.setattr(ingress, '_finish_attempt_v1', cleanup)
            # A rejected, unissued grant cannot acquire, reserve, charge or release.
            unissued = replace(request.grant, grant_id='unissued')
            invalid_request = type(request)(unissued, request.operation, handoff._f14_plain_v1(request.consumer),
                None, handoff._f14_plain_v1(request.requirements), request.maximum_raw_bytes)
            with pytest.raises(ComputationControlPlaneError, match='F14_INGRESS_GRANT'):
                handoff.run_retail_private_observation_once_v1(invalid_request, ingress=ingress,
                    source_registry=registry, adapter=adapter, publisher=publisher)
            assert not cleanups and not calls and not publisher._requests and not publisher._slots
            assert ingress._coordinator_token is None and registry._remaining == {'grant': 1}
            if boundary == 'reserve': publisher._requests = FailedReservation()
            try:
                with pytest.MonkeyPatch.context() as patcher:
                    for key, value in modules.items():
                        patcher.setitem(sys.modules, key, value)
                    with pytest.MonkeyPatch.context() as fault:
                        fault.setattr(registry, '_charge_v1', charged)
                        if boundary == 'fence_exit': fault.setattr(registry, 'fenced', failing_fence)
                        if boundary == 'prepare': fault.setattr(request_owner.ssl, 'create_default_context', fail)
                        if boundary == 'sign': fault.setattr(request_owner, '_f14_signing_message_v1', fail)
                        if boundary == 'store': fault.setattr(adapter, 'insert_receipt_record', fail)
                        if boundary == 'publication': fault.setattr(registry, '_observe_v1', publication_clock)
                        if boundary == 'resolve': fault.setattr(publisher, 'resolve_committed_private_observation_v1', fail)
                        with pytest.raises(ComputationControlPlaneError):
                            handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                                source_registry=registry, adapter=adapter, publisher=publisher)
                    assert failures == [boundary] and len(cleanups) == 1
                    remaining = 1 if boundary in ('fence_exit', 'reserve', 'prepare', 'sign') else 0
                    assert registry._remaining == {'grant': remaining}
                    assert charges == ([] if remaining else ['grant'])
                    assert cleanups[0][1] == remaining
                    assert ingress._coordinator_token is None and ingress._active_request is None
                    assert ingress._prepared is None and ingress._attempt_id is None
                    assert ingress._response_headers is None and ingress._charged is False
                    assert publisher._requests[id(request)] == (request, None)
                    if boundary in ('publication', 'resolve'):
                        assert len(publisher._slots) == 1
                        slot = next(iter(publisher._slots.values()))
                        assert slot['state'] == ('OUTCOME_UNKNOWN' if boundary == 'publication' else 'PENDING')
                        assert slot['result'] is None
                    else:
                        assert not publisher._slots
                    pending = {key: dict(value) for key, value in publisher._slots.items()}
                    before_calls = list(calls)
                    with pytest.raises(ComputationControlPlaneError, match='F14_INGRESS_ATTEMPT_OUTCOME_UNKNOWN'):
                        handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=publisher)
                    assert calls == before_calls and len(cleanups) == 1
                    assert publisher._slots == pending and registry._remaining == {'grant': remaining}
                    # A new grant/request may use the released receiver without replaying the held request.
                    next_grant = replace(request.grant, grant_id='after-failure')
                    registry.issue_grant(next_grant)
                    registry.bind_clock_facts(grant_id=next_grant.grant_id,
                        request_ref=request.consumer['request_ref'], item_key=request.consumer['item_key'], facts_by_role={})
                    next_request = type(request)(next_grant, request.operation, handoff._f14_plain_v1(request.consumer),
                        None, handoff._f14_plain_v1(request.requirements), request.maximum_raw_bytes)
                    next_calls, next_modules = _f14_scripted_transport(patch, next_request, ingress, raw)
                    with pytest.MonkeyPatch.context() as next_patcher:
                        for key, value in next_modules.items(): next_patcher.setitem(sys.modules, key, value)
                        result = handoff.run_retail_private_observation_once_v1(next_request, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=publisher)
                    assert result['selected_values'] == expected['selected_values']
                    assert all(value is False for value in result.values() if type(value) is bool)
                    assert next_calls[-1] == 'close' and len(cleanups) == 2
                    assert cleanups[0][0] is not cleanups[1][0]
                    assert registry._remaining == {'grant': remaining, 'after-failure': 0}
                    assert publisher._requests[id(request)] == (request, None)
                    assert all(publisher._slots[key] == value for key, value in pending.items())
                    assert ingress._coordinator_token is None and ingress._active_request is None
            finally:
                try:
                    for key, original in originals.items():
                        if original is absent:
                            assert key not in sys.modules
                        else:
                            assert key in sys.modules and sys.modules[key] is original
                finally:
                    if adapter_kind == 'sqlite': adapter.close()
    operations = ('ACTIVITY_TRADE','ACTIVITY_RESOLUTION','ACTIVITY_FUNDING','POSITIONS','BALANCES','WS_POSITION','WS_BALANCE')
    for operation in operations:
        for proof_count in range(4):
            with pytest.MonkeyPatch.context() as patch:
                request, ingress, registry, publisher, raw, expected, ticker = _f14_offline_owners(patch, operation, proofs=proof_count)
                adapter = _f14_fresh_adapter(adapter_kind)
                calls, modules = _f14_scripted_transport(patch, request, ingress, raw)
                originals = {name: sys.modules.get(name, absent) for name in modules}
                commits = []
                execute = handoff.TrancheCUnitOfWorkV1.execute
                def recorded_execute(unit, **kwargs):
                    result = execute(unit, **kwargs)
                    commits.append((kwargs, result))
                    return result
                patch.setattr(handoff.TrancheCUnitOfWorkV1, 'execute', recorded_execute)
                try:
                    with pytest.MonkeyPatch.context() as patcher:
                        for name, module in modules.items():
                            patcher.setitem(sys.modules, name, module)
                        result = handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=publisher)
                        assert result['selected_values'] == expected['selected_values']
                        assert all(value is False for value in result.values() if type(value) is bool)
                        assert len(commits) == 3 and all(row[1].transaction_state is TransactionTerminalStateV1.COMMITTED for row in commits)
                        assert calls[-1] == 'close' and registry._remaining['grant'] == 0
                        count = len(calls)
                        assert handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=publisher) == result
                        assert len(calls) == count
                        entry = next(iter(registry._captures.values()))
                        attempt = entry[4]
                        read = handoff._f14_allocation_v1(request.grant.session_binding.scope, attempt,
                            tuple(('publication','revision','finality')[:proof_count]))
                        snapshot = adapter.load_committed_private_evidence_snapshot_v1(read)
                        assert len(snapshot.present_record_refs) == 16 + proof_count
                        raw_row = adapter.load_committed_private_evidence_witness_v1(read.record_refs['raw'])
                        assert codec._f14_load_canonical_v1(raw_row.typed_payload.canonical_payload_json,
                            codec._F14_PHASES['RAW'])['raw_body_utf8'].encode('utf-8') == raw
                        assert adapter.load_committed_private_evidence_witness_v1('missing') is None
                        with pytest.raises(ComputationControlPlaneError):
                            adapter.load_committed_private_evidence_witness_v1(read.record_refs['companion'])
                        with pytest.raises(TypeError): snapshot.records_by_ref['forged'] = raw_row
                        tx = adapter.begin_transaction()
                        try:
                            with pytest.raises(ComputationControlPlaneError): adapter.load_committed_private_evidence_snapshot_v1(read)
                        finally: tx.rollback()
                        # Exact old claim replay does not manufacture a second batch or timestamp.
                        old_kwargs = commits[0][0]
                        replay = execute(handoff.TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1, frozenset())), **old_kwargs)
                        assert replay.committed_record_refs == (read.record_refs['raw'],)
                        assert adapter.load_committed_private_evidence_snapshot_v1(read).present_record_refs == snapshot.present_record_refs
                        if operation == 'ACTIVITY_TRADE':
                            _assert_f14_corrupt_committed_views(adapter_kind, adapter, read)
                        registry.revoke(request.grant.session_binding, 8)
                        with pytest.raises(ComputationControlPlaneError):
                            handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                                source_registry=registry, adapter=adapter, publisher=publisher)
                        assert adapter.load_committed_private_evidence_snapshot_v1(read).present_record_refs == snapshot.present_record_refs
                finally:
                    try:
                        for name, original in originals.items():
                            if original is absent:
                                assert name not in sys.modules
                            else:
                                assert name in sys.modules
                                assert sys.modules[name] is original
                    finally:
                        if adapter_kind == 'sqlite': adapter.close()
    for failure, operation in (('request','BALANCES'),('duplicate_length','BALANCES'),
            ('revoke','BALANCES'),('deadline','BALANCES'),('binary','WS_POSITION')):
        with pytest.MonkeyPatch.context() as patch:
            request, ingress, registry, publisher, raw, _, _ = _f14_offline_owners(patch, operation)
            adapter = _f14_fresh_adapter(adapter_kind)
            calls, modules = _f14_scripted_transport(patch, request, ingress, raw, failure=failure)
            originals = {name: sys.modules.get(name, absent) for name in modules}
            try:
                with pytest.MonkeyPatch.context() as patcher:
                    for name, module in modules.items():
                        patcher.setitem(sys.modules, name, module)
                    with pytest.raises(ComputationControlPlaneError):
                        handoff.run_retail_private_observation_once_v1(request, ingress=ingress,
                            source_registry=registry, adapter=adapter, publisher=publisher)
                    assert calls[-1] == 'close' and registry._remaining['grant'] == 0
                    assert not publisher._slots
                    if failure == 'duplicate_length': assert 'read' not in calls
            finally:
                try:
                    for name, original in originals.items():
                        if original is absent:
                            assert name not in sys.modules
                        else:
                            assert name in sys.modules
                            assert sys.modules[name] is original
                finally:
                    if adapter_kind == 'sqlite': adapter.close()
    if adapter_kind == 'memory':
        _assert_f14_composition_prefixes()
        import ast
        import os
        import subprocess
        from tools import independent_validate_qku_computation_control_plane_execution as independent
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy

        repo_root = Path(__file__).resolve().parents[4]
        workflow_name = '.github/workflows/qtt_validation.yml'
        workflow_bytes = (repo_root / workflow_name).read_bytes()
        assert source_policy._st12h_validate_workflow_contract(repo_root) == (workflow_name,)
        with TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            workflow = fixture_root / workflow_name
            workflow.parent.mkdir(parents=True)
            workflow.write_bytes(workflow_bytes)
            assert source_policy._st12h_validate_workflow_contract(fixture_root) == (workflow_name,)
            for old, new in (
                (b'uses: actions/setup-python@v5', b'uses: actions/setup-python@v4'),
                (b"python-version: '3.14.6'", b"python-version: '3.14.5'"),
                (b'python -m pip install pytest==9.1.1', b'python -m pip install pytest==9.1.0'),
                (b'          - phase: post-validation\n', b''),
                (b'      - validation_shards\n', b'      - unexpected_dependency\n'),
            ):
                assert old in workflow_bytes
                workflow.write_bytes(workflow_bytes.replace(old, new, 1))
                with pytest.raises(source_policy.SourcePolicyError) as failure:
                    source_policy._st12h_validate_workflow_contract(fixture_root)
                assert failure.value.reason_code.value == 'ST12A_SOURCE_EPOCH_STALE'
            workflow.write_bytes(workflow_bytes + b'          - phase: post-validation\n')
            with pytest.raises(source_policy.SourcePolicyError) as failure:
                source_policy._st12h_validate_workflow_contract(fixture_root)
            assert failure.value.reason_code.value == 'ST12A_SOURCE_EPOCH_STALE'
            parser_limit = 256 * 1024
            at_limit = workflow_bytes + b'#' + b'x' * (parser_limit - len(workflow_bytes) - 2) + b'\n'
            assert len(at_limit) == parser_limit
            workflow.write_bytes(at_limit)
            assert source_policy._st12h_validate_workflow_contract(fixture_root) == (workflow_name,)
            workflow.write_bytes(at_limit + b'x')
            with pytest.raises(source_policy.SourcePolicyError) as failure:
                source_policy._st12h_validate_workflow_contract(fixture_root)
            assert failure.value.reason_code.value == 'ST12A_SOURCE_EPOCH_STALE'
            workflow.unlink()
            with pytest.raises(source_policy.SourcePolicyError) as failure:
                source_policy._st12h_validate_workflow_contract(fixture_root)
            assert failure.value.reason_code.value == 'ST12A_SOURCE_EPOCH_MISSING'
        assert (repo_root / workflow_name).read_bytes() == workflow_bytes

        independent_source = Path(independent.__file__).read_bytes().decode('utf-8')
        economic_tree = independent._tree('economic_math.py')
        context_tree = independent._tree('context.py')
        independent._validate_execution_math_owner_ast(
            economic_tree, context_tree, ast.parse(independent_source),
        )
        for mutation in (
            'import src', 'import qtt', 'import src.qtt as aliased',
            'from src import qtt', 'from qtt.domain import value',
            'def _unused():\n    import qtt.domain',
            'if False:\n    from src.qtt import value',
        ):
            with pytest.raises(ValueError, match='independent execution validator imports production source'):
                independent._validate_execution_math_owner_ast(
                    economic_tree, context_tree,
                    ast.parse(independent_source + '\n' + mutation + '\n'),
                )
        for unrelated in ('import src_peer', 'from qtt_peer import value'):
            independent._validate_execution_math_owner_ast(
                economic_tree, context_tree,
                ast.parse(independent_source + '\n' + unrelated + '\n'),
            )

        code = '\n'.join((
            'import importlib.abc, sys',
            "assert not any(name.split('.', 1)[0] in {'src', 'qtt'} for name in sys.modules)",
            'class ProductionImportBoundary(importlib.abc.MetaPathFinder):',
            '    def find_spec(self, fullname, path=None, target=None):',
            "        if fullname.split('.', 1)[0] in {'src', 'qtt'}:",
            "            raise ImportError('production import rejected: ' + fullname)",
            '        return None',
            'sys.meta_path.insert(0, ProductionImportBoundary())',
            'from tools import independent_validate_qku_computation_control_plane_execution as independent',
            'result = independent.main()',
            'assert result == 0',
            "assert not any(name.split('.', 1)[0] in {'src', 'qtt'} for name in sys.modules)",
            'raise SystemExit(result)',
        ))
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        completed = subprocess.run(
            [sys.executable, '-B', '-c', code], cwd=repo_root, env=environment,
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding='utf-8', timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        assert independent.SUCCESS + ' controls=9 identities=8 gates=13 lifecycle=NO_WRITE effects=0 blockers=9' in completed.stdout.splitlines()
        assert completed.stderr == ''


def _assert_f14_corrupt_committed_views(kind, adapter, request):
    import copy, json
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import _f14_reconstruct_snapshot_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.migrations import APPEND_ONLY_TABLES_V1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
    if kind == 'memory':
        rows = {table: {rid: deterministic_json(value) for rid,value in items.items()} for table,items in adapter._tables.items()}
    else:
        with adapter._f14_read_rows_v1(frozenset(value for values in request.phase_control_refs.values()
                for value in values.values()) | frozenset(adapter.load_committed_private_evidence_snapshot_v1(request).present_record_refs)) as (rows, mirrors):
            rows = copy.deepcopy(rows)
    names = list(adapter.load_committed_private_evidence_snapshot_v1(request).present_record_refs)
    assert not any(rows[table] for table in ('economic_events','journal_transactions','journal_postings','value_lineage_edges','reversal_links','reconciliation_breaks'))
    for table, values in rows.items():
        for rid in values:
            for mutation in ('missing','alias','other_table'):
                bad = copy.deepcopy(rows)
                if mutation == 'missing': del bad[table][rid]
                elif mutation == 'alias': bad[table]['same-count-alias'] = bad[table].pop(rid)
                else: bad['journal_transactions'][rid] = '{}'
                with pytest.raises(ComputationControlPlaneError): _f14_reconstruct_snapshot_v1(request, bad)
    # Plant a valid-looking altered payload in actual committed storage in a fresh adapter.
    changed = request.record_refs['raw']
    clone = _f14_fresh_adapter(kind)
    try:
        if kind == 'memory':
            clone._tables = {table: dict(values) for table,values in adapter._tables.items()}
            clone._tables['receipt_records'][changed] = replace(adapter._tables['receipt_records'][changed], sequence=1)
        else:
            for table in APPEND_ONLY_TABLES_V1:
                cursor = adapter._connection.execute(f'SELECT * FROM {table}')
                try: records = cursor.fetchall()
                finally: cursor.close()
                for values in records:
                    values = list(values)
                    if table == 'receipt_records' and values[0] == changed:
                        payload = json.loads(values[-1]); payload['sequence'] = 1
                        values[-1] = deterministic_json(payload)
                    cursor = clone._connection.execute(f"INSERT INTO {table} VALUES({','.join('?' for _ in values)})", tuple(values))
                    cursor.close()
        with pytest.raises(ComputationControlPlaneError, match='F14_STORAGE_PLAN_ACTUAL_MISMATCH'):
            clone.load_committed_private_evidence_snapshot_v1(request)
    finally:
        if kind == 'sqlite': clone.close()


def _assert_f14_composition_prefixes():
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.transaction import _native_retail_private_composition_plan_v1
    from tests.source_evidence.test_s1_pit_data_phase_a_01 import _f14_reference_cases
    scope = _f14_reference_cases()[0][0][0]['scope']
    checked = accepted = 0
    for proofs in range(4):
        names = ['raw','transport','intent','capture','published','companion',*[f'proof-{i}' for i in range(proofs)],'seal']
        valid = [[], names[:3], names[:-1], names]
        refs = dict(raw='raw',transport='transport',publication_intent='intent',capture_commit='capture',
            publication='published',companion='companion',companion_commit='seal',clock_proofs=[f'proof-{i}' for i in range(proofs)])
        intent = dict(outbox_intent_id='intent',topic_class='PRIVATE_OBSERVATION_REFERENCE_PUBLICATION',
            aggregate_id='account',payload_record_ref='raw',created_at='2026-09-13T00:00:00.000000002Z',
            dispatch_state='RECORDED_NOT_DISPATCHABLE',dispatch_attempt_count=0,next_eligible_at=None,
            authority_class='NO_WRITE_CONTRACT_ONLY')
        kw = dict(expected_scope=dict(scope),current_source_snapshot_ref='snapshot',current_revocation_epoch=7,
            process_epoch_id='process',monotonic_clock_id='monotonic',recorded_cutoff='2026-09-13T00:00:00.000000008Z',
            source_snapshot_after_ref='snapshot',revocation_epoch_after=7)
        for mask in range(1 << len(names)):
            selected = [value for i,value in enumerate(names) if mask & (1 << i)]
            stage = valid.index(selected) if selected in valid else None
            observations = dict(capture_commit=None,publication=None,companion_commit=None)
            if stage is not None and stage >= 2:
                observations['capture_commit'] = dict(observed_at='2026-09-13T00:00:00.000000003Z',monotonic_ns=3)
                observations['publication'] = dict(observed_at='2026-09-13T00:00:00.000000004Z',monotonic_ns=4)
            if stage == 3: observations['companion_commit'] = dict(observed_at='2026-09-13T00:00:00.000000006Z',monotonic_ns=6)
            snapshot = dict(source_snapshot_ref='snapshot',revocation_epoch=7,process_epoch_id='process',
                monotonic_clock_id='monotonic',storage_state='COMMITTED_SNAPSHOT',committed_record_refs=selected,
                observations=observations,snapshot_observed_at='2026-09-13T00:00:00.000000008Z',snapshot_monotonic_ns=8,
                publication_state='OBSERVED' if stage is not None and stage >= 2 else 'NOT_ATTEMPTED')
            checked += 1
            if stage is None:
                with pytest.raises(ComputationControlPlaneError, match='PRIVATE_COMPOSITION_ATOMIC_PREFIX'):
                    _native_retail_private_composition_plan_v1(dict(scope),refs,snapshot,intent,**kw)
            else:
                out = _native_retail_private_composition_plan_v1(dict(scope),refs,snapshot,intent,**kw)
                assert out['committed_stage'] == stage and out['runtime_effect_authorized'] is False
                accepted += 1
    assert (checked,accepted) == (1920,16)
