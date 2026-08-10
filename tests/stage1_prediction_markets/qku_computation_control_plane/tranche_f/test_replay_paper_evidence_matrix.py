"""Compact ST12-F REPLAY/PAPER/evidence semantic matrix."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from threading import Barrier, Thread

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
    POLICY_VERSION,
)

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ContractValidationError,
    PersistenceContractError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    BuiltEvidenceBundleOutcomeV1,
    ComputationEvidenceBundleV1,
    ComputationEvidenceServiceV1,
    DivergenceAssessmentV1,
    DivergenceTerminalStateV1,
    EvidenceBundleTerminalStateV1,
    EvidenceIdentityDispositionStateV1,
    EvidenceIdentityDispositionV1,
    EvidenceCacheSnapshotV1,
    EvidenceSectionV1,
    FToDEvidenceReferenceQueryV1,
    FToGHandoffReferencesV1,
    IndependentReviewDecisionV1,
    IndependentEvidenceReviewV1,
    IndependentReviewRecordV1,
    PaperResultContractV1,
    RegisterEvidenceControlRequestV1,
    RegisteredLaneResultOutcomeV1,
    ReplayResultContractV1,
    ST12F_EVIDENCE_IDENTITIES_V1,
    ST12F_EVIDENCE_OUTPUT_BINDINGS_V1,
    ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1,
    StaticEvidenceApplicabilityProofV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.cohort_compiler import (
    ReplayPaperCohortCompilationRecordV1,
    ReplayPaperCohortCompilerV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (
    CanonicalReplayPaperInputSnapshotV1,
    ImmutableReplayPaperInputLockV1,
    ST12F_TEMPLATE_IDS_V1,
    build_immutable_replay_paper_input_lock_v1,
    canonical_st12f_parameter_value_refs_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.llm_gateway import (
    AnnotationCitationV1,
    AnnotationClaimV1,
    CanonicalNumericEvidenceValueV1,
    DeterministicEvidenceAnnotationContractV1,
    LLMAdvisoryTaskV1,
    QuotedNumericFactV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import (
    MODEL_RISK_CONTROL_IDS_V1,
    NO_TRADE_CONDITION_IDS_V1,
    ModelRiskAdjudicationBasisV1,
    ModelRiskControlEvidenceV1,
    ModelRiskControlStateV1,
    ModelRiskEvidenceAdjudicatorV1,
    ModelRiskLaneEvidenceV1,
    NoTradeConditionOutcomeV1,
    PermanentNoTradeEvidenceComparisonV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    BuildEvidenceBundleRequestV1,
    CompileReplayPaperCohortRequestV1,
    ComputationExecutionReceiptV1,
    NO_EFFECTS_V1,
    RegisterReplayPaperResultRequestV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    InMemoryPersistenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_benchmark import (
    EconomicComparatorReceiptV1,
    QuantumClassicalNoTradeComparisonV1,
    QuantumEconomicBasisV1,
    QuantumTraceValidationReceiptV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    DurableComputationExecutionReceiptRecordV1,
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    ST12FEvidenceControlReceiptRecordV1,
    ST12FReceiptClassV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)


_SEMANTIC_IDS = (
    "ST12-TEST::122",
    "ST12-TEST::126",
    "ST12-TEST::132",
    "ST12-TEST::133",
    "ST12-TEST::136",
    "ST12-TEST::137",
    "ST12-TEST::138",
    "ST12-TEST::139",
)
_SECTION_FIELDS = (
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
)
_OWNER_BUNDLE_FIELDS = (
    "evidence_id",
    "schema_version",
    "contract_version",
    "evidence_bundle_version",
    "component_or_template_ref",
    "input_lock_id",
    "actual_executed_component_versions",
    "actual_executed_stack_versions",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
    "independent_review_state",
    "failure_and_negative_evidence_states",
    "source_and_provenance_refs",
    "d_evidence_reference_projection",
    "g_handoff_projection",
    "terminal_state",
    "blocker_codes",
)
_OWNER_TRANSITIONS = (
    (
        "INCOMPLETE_MISSING_REPLAY",
        "READY_FOR_INDEPENDENT_REVIEW",
        "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
    ),
    (
        "INCOMPLETE_MISSING_PAPER",
        "READY_FOR_INDEPENDENT_REVIEW",
        "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
    ),
    (
        "READY_FOR_INDEPENDENT_REVIEW",
        "CLOSED_INDEPENDENTLY_VALIDATED",
        "SEPARATE_REVIEW_RECEIPT_PASS_AND_ZERO_HARD_VETOES",
    ),
    (
        "READY_FOR_INDEPENDENT_REVIEW",
        "INDEPENDENT_REVIEW_REJECTED",
        "SEPARATE_REVIEW_RECEIPT_REJECT",
    ),
    (
        "CLOSED_INDEPENDENTLY_VALIDATED",
        "STALE",
        "TTL_SOURCE_EPOCH_PARAMETER_IMPLEMENTATION_OR_CONTEXT_CHANGE",
    ),
    (
        "CLOSED_INDEPENDENTLY_VALIDATED",
        "SUPERSEDED",
        "NEWER_VALIDATED_BUNDLE_VERSION_SAME_IDENTITY",
    ),
)
_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _valid_lock():
    versions = {identity: f"VERSION::{identity}" for identity in ST12F_TEMPLATE_IDS_V1}
    snapshot = CanonicalReplayPaperInputSnapshotV1(
        decision_time=_NOW,
        point_in_time_cutoff=_NOW - timedelta(minutes=1),
        market_scope=("MARKET::CERTIFIED",),
        venue_scope=("VENUE::CERTIFIED",),
        instrument_scope=("INSTRUMENT::CERTIFIED",),
        formula_specification_versions=versions,
        implementation_versions=versions,
        parameter_policy_version="ST12F_PARAMETER_POLICY_V1_4",
        parameter_value_refs=canonical_st12f_parameter_value_refs_v1(),
        source_epochs={"SOURCE::1": "EPOCH::1"},
        data_semantics_version="DATA::V1",
        venue_semantics_version="VENUE::V1",
        accounting_definition={"basis": "NET"},
        fee_assumptions={"policy_ref": "FEE::1"},
        spread_assumptions={"policy_ref": "SPREAD::1"},
        slippage_assumptions={"policy_ref": "SLIPPAGE::1"},
        fill_and_queue_assumptions={"policy_ref": "FILL::1"},
        latency_and_staleness_assumptions={"policy_ref": "LATENCY::1"},
        capacity_and_crowding_assumptions={"policy_ref": "CAPACITY::1"},
        portfolio_and_cash_context={"permanent_no_trade_baseline_ref": "NO-TRADE::1"},
        random_seed_policy={"seed": 7},
        resampling_policy={"trial_family_id": "TRIAL::1"},
        scenario_set_id="SCENARIO::1",
        causation_id="CAUSE::1",
        correlation_id="CORRELATION::1",
        created_by="CANONICAL-OWNER::1",
        created_at=_NOW,
    )
    return build_immutable_replay_paper_input_lock_v1(
        identity_token="VALID-ONEPASS",
        asserted_input_lock_id="ST12F-LOCK::VALID-ONEPASS",
        canonical_snapshot=snapshot,
    )


def _lane(cls=ReplayResultContractV1):
    lane = "REPLAY" if cls is ReplayResultContractV1 else "PAPER"
    template = ST12F_TEMPLATE_IDS_V1[0]
    cutoff = _NOW - timedelta(minutes=1)
    return cls(
        result_id=f"RESULT::{lane}",
        schema_version="QTT_ST12F_LANE_RESULT_CONTRACTS_V1_4",
        contract_version="1.4",
        cohort_template_id=template,
        expected_result_contract_id=f"ST12F-{lane}-CONTRACT::{template}",
        input_lock_id="ST12F-LOCK::VALID-ONEPASS",
        run_reference=f"RUN::{lane}",
        producer_identity=f"PRODUCER::{lane}",
        implementation_versions={"MATH-01": "IMPLEMENTATION::1"},
        source_epochs={"SOURCE::1": "EPOCH::1"},
        point_in_time_cutoff=cutoff,
        accounting_definition="ACCOUNTING::NET::V1",
        scenario_policy={"scenario": "SCENARIO::1"},
        resampling_policy={"trial_family_id": "TRIAL::1"},
        economic_metrics={"utility": "1"},
        tca_metrics={"cost": "0.1"},
        fill_metrics={"fill": "1"},
        latency_metrics={"latency": "1ms"},
        capacity_metrics={"capacity": "1"},
        failure_states=(),
        limitations=("LIMITATION::DECLARED",),
        started_at=cutoff,
        completed_at=cutoff + timedelta(seconds=1),
        available_at=cutoff + timedelta(seconds=2),
        closed_at=cutoff + timedelta(seconds=3),
        fixture_only_not_evidence=True,
    )


def _divergence() -> DivergenceAssessmentV1:
    return DivergenceAssessmentV1(
        assessment_id="DIVERGENCE::1",
        schema_version="QTT_ST12F_DIVERGENCE_ASSESSMENT_V1_4",
        contract_version="1.4",
        input_lock_id="ST12F-LOCK::VALID-ONEPASS",
        cohort_template_id="MATH-01",
        replay_result_ref="RESULT::REPLAY",
        paper_result_ref="RESULT::PAPER",
        metric_deltas={"utility": Decimal("0")},
        directional_agreement=True,
        calibration_delta=Decimal("0"),
        execution_cost_delta=Decimal("0"),
        fill_delta=Decimal("0"),
        latency_delta=Decimal("0"),
        capacity_delta=Decimal("0"),
        regime_delta=Decimal("0"),
        threshold_policy_refs=("THRESHOLD::1",),
        typed_blockers=(),
        terminal_state=DivergenceTerminalStateV1.CONSISTENT_WITHIN_LOCKED_THRESHOLDS,
    )


def _disposition(identity: str) -> EvidenceIdentityDispositionV1:
    return EvidenceIdentityDispositionV1(
        evidence_identity=identity,
        disposition=EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED,
        evidence_record_refs=(f"RECEIPT::{identity}",),
        blocker_codes=(),
        proof_refs=(),
    )


def _sections() -> dict[str, EvidenceSectionV1]:
    rows = tuple(_disposition(identity) for identity in ST12F_EVIDENCE_IDENTITIES_V1)
    output: dict[str, EvidenceSectionV1] = {}
    offset = 0
    for index, name in enumerate(_SECTION_FIELDS):
        width = 8 if index == len(_SECTION_FIELDS) - 1 else 4
        output[name] = EvidenceSectionV1(name, rows[offset : offset + width])
        offset += width
    assert offset == 48
    return output


def _bundle(**section_overrides: EvidenceSectionV1) -> ComputationEvidenceBundleV1:
    sections = _sections()
    sections.update(section_overrides)
    return ComputationEvidenceBundleV1(
        evidence_id="EVIDENCE::1",
        schema_version="QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4",
        contract_version="1.4",
        evidence_bundle_version="BUNDLE::VERSION::1",
        component_or_template_ref="MATH-01",
        input_lock_id="ST12F-LOCK::VALID-ONEPASS",
        actual_executed_component_versions={"MATH-01": "VERSION::1"},
        actual_executed_stack_versions={"STACK::1": "VERSION::1"},
        replay_result_ref="RESULT::REPLAY",
        paper_result_ref="RESULT::PAPER",
        divergence_assessment_ref="DIVERGENCE::1",
        lane_execution_receipt_refs=("RECEIPT::REPLAY", "RECEIPT::PAPER"),
        **sections,
        independent_review_state="READY_FOR_INDEPENDENT_REVIEW",
        failure_and_negative_evidence_states=(),
        source_and_provenance_refs=("SOURCE::1",),
        d_evidence_reference_projection="UNAVAILABLE",
        g_handoff_projection="UNAVAILABLE",
        terminal_state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        blocker_codes=(),
    )


def _review() -> IndependentReviewRecordV1:
    return IndependentReviewRecordV1(
        review_id="REVIEW::1",
        schema_version="QTT_ST12F_INDEPENDENT_REVIEW_RECORD_V1_4",
        contract_version="1.4",
        prior_bundle_ref="BUNDLE::VERSION::1",
        evidence_id="EVIDENCE::1",
        evidence_bundle_version="BUNDLE::VERSION::2",
        input_lock_id="ST12F-LOCK::VALID-ONEPASS",
        reviewer_identity="REVIEWER::INDEPENDENT",
        bundle_producer_identity="PRODUCER::BUNDLE",
        authority_receipt_ref="AUTHORITY::REVIEW",
        reviewed_source_epoch_refs=("EPOCH::1",),
        decision=IndependentReviewDecisionV1.VALIDATED,
        blocker_codes=(),
        reviewed_at=_NOW,
        valid_until=_NOW + timedelta(hours=1),
    )


def _run_st12f_replay_paper_evidence_fixture_preflight_v1() -> tuple[tuple[str, str], ...]:
    lock = _valid_lock()
    replay = _lane()
    divergence = _divergence()
    bundle = _bundle()
    review = _review()
    first_section = bundle.calibration_and_probability_quality
    duplicate_rows = list(first_section.identity_dispositions)
    duplicate_rows[1] = replace(duplicate_rows[1], evidence_identity=duplicate_rows[0].evidence_identity)
    cases = (
        ("ST12-TEST::122", lambda: replace(lock, cohort_template_ids=(lock.cohort_template_ids[1], lock.cohort_template_ids[0], *lock.cohort_template_ids[2:])), ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH, "LOCK_TEMPLATE_ORDER"),
        ("ST12-TEST::126", lambda: replace(replay, expected_result_contract_id="ST12F-PAPER-CONTRACT::MATH-01"), ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "LANE_IDENTITY"),
        ("ST12-TEST::132", lambda: _bundle(calibration_and_probability_quality=EvidenceSectionV1(first_section.section_id, tuple(duplicate_rows))), ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID, "EVIDENCE_IDENTITY_UNION"),
        ("ST12-TEST::133", lambda: replace(divergence, latency_delta=None), ReasonCode.ST12F_EVIDENCE_INCOMPLETE, "DIVERGENCE_INCOMPARABLE"),
        ("ST12-TEST::136", lambda: replace(first_section.identity_dispositions[0], evidence_record_refs=()), ReasonCode.ST12F_EVIDENCE_INCOMPLETE, "EVIDENCE_RECEIPT"),
        ("ST12-TEST::137", lambda: replace(replay, completed_at=replay.started_at - timedelta(seconds=1)), ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID, "LANE_TIME_SEQUENCE"),
        ("ST12-TEST::138", lambda: replace(review, reviewer_identity=review.bundle_producer_identity), ReasonCode.ST12F_SELF_REVIEW_FORBIDDEN, "INDEPENDENT_REVIEW_SEGREGATION"),
        ("ST12-TEST::139", lambda: replace(replay, fixture_only_not_evidence=1), ReasonCode.CONTRACT_OR_TYPE_INVALID, "FIXTURE_EVIDENCE_BOUNDARY"),
    )
    results: list[tuple[str, str]] = []
    for case_id, mutate, reason, stage in cases:
        # Exact seam baselines have already constructed successfully; only the
        # declared field/roster mutation is applied below.
        try:
            mutate()
        except ContractValidationError as exc:
            assert exc.reason_code is reason
        else:
            raise AssertionError(f"{case_id} did not reach {stage}")
        results.append((case_id, stage))
    assert tuple(case_id for case_id, _ in results) == _SEMANTIC_IDS
    return tuple(results)


def test_input_lock_and_lane_contract_matrix() -> None:
    summary = _run_st12f_replay_paper_evidence_fixture_preflight_v1()
    lock = _valid_lock()
    assert len(summary) == 8
    assert len(lock.cohort_template_ids) == 52
    assert len(lock.expected_replay_result_contract_ids) == 52
    assert len(lock.expected_paper_result_contract_ids) == 52
    assert len(lock.parameter_value_refs) == 3096
    assert type(_lane()) is ReplayResultContractV1
    assert type(_lane(PaperResultContractV1)) is PaperResultContractV1


def test_divergence_and_evidence_identity_matrix() -> None:
    assert _divergence().terminal_state is DivergenceTerminalStateV1.CONSISTENT_WITHIN_LOCKED_THRESHOLDS
    bundle = _bundle()
    assert tuple(field.name for field in fields(ComputationEvidenceBundleV1)) == _OWNER_BUNDLE_FIELDS
    noncanonical_payload = json.loads(bundle.canonical_json())
    noncanonical_payload["prior_bundle_ref_or_explicit_absence"] = "EXPLICIT_ABSENCE"
    try:
        ComputationEvidenceBundleV1.from_canonical_mapping(noncanonical_payload)
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.SCHEMA_MISMATCH
    else:
        raise AssertionError("removed noncanonical 31st bundle field was accepted")
    identities = tuple(
        row.evidence_identity
        for name in _SECTION_FIELDS
        for row in getattr(bundle, name).identity_dispositions
    )
    assert len(identities) == len(set(identities)) == 48


def test_independent_review_and_no_effect_matrix() -> None:
    review = _review()
    assert review.no_self_review is True
    assert _bundle().d_evidence_reference_projection == "UNAVAILABLE"
    assert _lane().fixture_only_not_evidence is True


_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


def _runtime_snapshot() -> CanonicalReplayPaperInputSnapshotV1:
    lock = _valid_lock()
    return CanonicalReplayPaperInputSnapshotV1(
        decision_time=lock.decision_time,
        point_in_time_cutoff=lock.point_in_time_cutoff,
        market_scope=lock.market_scope,
        venue_scope=lock.venue_scope,
        instrument_scope=lock.instrument_scope,
        formula_specification_versions=lock.formula_specification_versions,
        implementation_versions=lock.implementation_versions,
        parameter_policy_version=lock.parameter_policy_version,
        parameter_value_refs=lock.parameter_value_refs,
        source_epochs=lock.source_epochs,
        data_semantics_version=lock.data_semantics_version,
        venue_semantics_version=lock.venue_semantics_version,
        accounting_definition=lock.accounting_definition,
        fee_assumptions=lock.fee_assumptions,
        spread_assumptions=lock.spread_assumptions,
        slippage_assumptions=lock.slippage_assumptions,
        fill_and_queue_assumptions=lock.fill_and_queue_assumptions,
        latency_and_staleness_assumptions=lock.latency_and_staleness_assumptions,
        capacity_and_crowding_assumptions=lock.capacity_and_crowding_assumptions,
        portfolio_and_cash_context=lock.portfolio_and_cash_context,
        random_seed_policy=lock.random_seed_policy,
        resampling_policy=lock.resampling_policy,
        scenario_set_id=lock.scenario_set_id,
        causation_id=lock.causation_id,
        correlation_id=lock.correlation_id,
        created_by=lock.created_by,
        created_at=lock.created_at,
    )


class _CommitFailingAdapterV1(InMemoryPersistenceAdapterV1):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next_commit = False

    def _commit(self, transaction: object) -> None:
        if self.fail_next_commit:
            self.fail_next_commit = False
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "injected atomic commit failure",
            )
        super()._commit(transaction)  # type: ignore[arg-type]


@dataclass(slots=True)
class _RuntimeHarnessV1:
    snapshot: CanonicalReplayPaperInputSnapshotV1
    persistence: InMemoryPersistenceAdapterV1
    compiler: ReplayPaperCohortCompilerV1
    service: ComputationEvidenceServiceV1
    compilation: ReplayPaperCohortCompilationRecordV1
    context: ComputationContextKeyV1


class _NoEffectAdmissionV1:
    def admit_operation(self, request: object) -> AgentCapabilityDecisionV1:
        request_id = str(getattr(request, "request_id"))
        operation_id = str(getattr(request, "operation_name"))
        principal_id = str(getattr(request, "principal_id"))
        idempotency_key = str(getattr(request, "idempotency_key"))
        return AgentCapabilityDecisionV1(
            decision_id=f"TEST-DECISION::{request_id}",
            request_id=request_id,
            task_id=f"TEST-TASK::{request_id}",
            principal_id=principal_id,
            current_agent_id="dashboard_agent",
            source_agent_refs=("AGENT_RT_11",),
            operation_id=operation_id,
            policy_version=POLICY_VERSION,
            decision_state=(
                AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
            ),
            reason_codes=(),
            scope_refs=(f"operation_id={operation_id}", "test_fixture=ST12F"),
            idempotency_key=idempotency_key,
            retry_disposition="NO_RETRY_AUTHORITY",
            peer_sod_disposition="TEST_FIXTURE_NO_SELF_APPROVAL",
            safety_state_disposition="NON_MATERIAL_LOCAL_NO_EFFECT",
            terminal_route="QKUComputationControlPlaneV1_NO_EFFECT_REQUEST",
            agent_orch_receipt_ref=f"AGENT-ORCH::TEST::{request_id}",
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


def _compile_request(
    *,
    identity: str,
    context: ComputationContextKeyV1,
) -> CompileReplayPaperCohortRequestV1:
    return CompileReplayPaperCohortRequestV1(
        request_id=f"REQUEST::OP13::{identity}",
        operation_name="compile_replay_paper_cohort",
        requested_at=_NOW,
        principal_id="PRINCIPAL::RUNTIME",
        capability_bundle_id="CAPABILITY::RUNTIME",
        context=context,
        idempotency_key=identity,
        traceparent=_TRACEPARENT,
        tracestate="qtt=runtime",
        template_ids=ST12F_TEMPLATE_IDS_V1,
        requested_lanes=("REPLAY", "PAPER"),
        input_lock_id=f"ST12F-LOCK::{identity}",
        campaign_execution_requested=False,
    )


def _runtime_harness(
    persistence: InMemoryPersistenceAdapterV1 | None = None,
    *,
    identity: str = "RUNTIME-CAMPAIGN",
) -> _RuntimeHarnessV1:
    snapshot = _runtime_snapshot()
    adapter = InMemoryPersistenceAdapterV1() if persistence is None else persistence
    compiler = ReplayPaperCohortCompilerV1(snapshot, adapter)
    context = ComputationContextKeyV1(
        context_id="MATH-01",
        as_of=_NOW,
        observed_at=_NOW,
        source_epoch_id="SOURCE::1=EPOCH::1",
        input_version="INPUT::RUNTIME",
        maximum_age=timedelta(hours=1),
    )
    request = _compile_request(identity=identity, context=context)
    compilation = compiler.compile(request)
    return _RuntimeHarnessV1(
        snapshot=snapshot,
        persistence=adapter,
        compiler=compiler,
        service=ComputationEvidenceServiceV1(compiler, adapter),
        compilation=compilation,
        context=context,
    )


def _runtime_packet(
    harness: _RuntimeHarnessV1,
    lane: str,
    *,
    result_id: str | None = None,
    fixture: bool = False,
    run_reference: str | None = None,
    component: str = "MATH-01",
) -> ReplayResultContractV1 | PaperResultContractV1:
    contract_type = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1
    cutoff = harness.snapshot.point_in_time_cutoff
    return contract_type(
        result_id=f"RESULT::{lane}" if result_id is None else result_id,
        schema_version="QTT_ST12F_LANE_RESULT_CONTRACTS_V1_4",
        contract_version="1.4",
        cohort_template_id=component,
        expected_result_contract_id=f"ST12F-{lane}-CONTRACT::{component}",
        input_lock_id=harness.compilation.input_lock_id,
        run_reference=f"RUN::{lane}" if run_reference is None else run_reference,
        producer_identity=f"PRODUCER::{lane}",
        implementation_versions=harness.snapshot.implementation_versions,
        source_epochs=harness.snapshot.source_epochs,
        point_in_time_cutoff=cutoff,
        accounting_definition=deterministic_json(
            harness.snapshot.accounting_definition
        ),
        scenario_policy={"scenario": harness.snapshot.scenario_set_id},
        resampling_policy=harness.snapshot.resampling_policy,
        economic_metrics={"utility": "1"},
        tca_metrics={"cost": "0.1"},
        fill_metrics={"fill": "1"},
        latency_metrics={"latency": "1ms"},
        capacity_metrics={"capacity": "1"},
        failure_states=(),
        limitations=("LIMITATION::DECLARED",),
        started_at=cutoff,
        completed_at=cutoff + timedelta(seconds=1),
        available_at=cutoff + timedelta(seconds=2),
        closed_at=cutoff + timedelta(seconds=3),
        fixture_only_not_evidence=fixture,
    )


def _register_request(
    harness: _RuntimeHarnessV1,
    lane: str,
    identity: str,
) -> RegisterReplayPaperResultRequestV1:
    placeholder = TypedValueRecordV1(
        (
            TypedValueV1(
                "placeholder",
                TypedValueKindV1.TEXT,
                "preexisting-packet-supplied-separately",
                "unitless",
                "test",
            ),
        )
    )
    return RegisterReplayPaperResultRequestV1(
        request_id=f"REQUEST::OP14::{identity}",
        operation_name="register_replay_paper_result",
        requested_at=_NOW + timedelta(seconds=1),
        principal_id="PRINCIPAL::RUNTIME",
        capability_bundle_id="CAPABILITY::RUNTIME",
        context=harness.context,
        idempotency_key=f"IDEMPOTENCY::OP14::{identity}",
        traceparent=_TRACEPARENT,
        tracestate="qtt=runtime",
        cohort_instance_id=harness.compilation.compilation_id,
        lane=lane,
        input_lock_id=harness.compilation.input_lock_id,
        result_packet=placeholder,
    )


def _register_dual_lanes(
    harness: _RuntimeHarnessV1,
    *,
    identity: str = "",
    component: str = "MATH-01",
) -> tuple[ReplayResultContractV1, PaperResultContractV1]:
    suffix = "" if not identity else f"::{identity}"
    replay_outcome = harness.service.register_result(
        _register_request(harness, "REPLAY", f"REPLAY{suffix}"),
        _runtime_packet(
            harness,
            "REPLAY",
            result_id=f"RESULT::REPLAY{suffix}",
            run_reference=f"RUN::REPLAY{suffix}",
            component=component,
        ),
    )
    paper_outcome = harness.service.register_result(
        _register_request(harness, "PAPER", f"PAPER{suffix}"),
        _runtime_packet(
            harness,
            "PAPER",
            result_id=f"RESULT::PAPER{suffix}",
            run_reference=f"RUN::PAPER{suffix}",
            component=component,
        ),
    )
    assert type(replay_outcome) is RegisteredLaneResultOutcomeV1
    assert type(paper_outcome) is RegisteredLaneResultOutcomeV1
    replay = replay_outcome.registered_result
    paper = paper_outcome.registered_result
    assert type(replay) is ReplayResultContractV1
    assert type(paper) is PaperResultContractV1
    return replay, paper


def _runtime_divergence(
    replay: ReplayResultContractV1,
    paper: PaperResultContractV1,
    *,
    identity: str = "RUNTIME",
) -> DivergenceAssessmentV1:
    return DivergenceAssessmentV1(
        assessment_id=f"DIVERGENCE::{identity}",
        schema_version="QTT_ST12F_DIVERGENCE_ASSESSMENT_V1_4",
        contract_version="1.4",
        input_lock_id=replay.input_lock_id,
        cohort_template_id=replay.cohort_template_id,
        replay_result_ref=replay.result_id,
        paper_result_ref=paper.result_id,
        metric_deltas={"utility": Decimal("0")},
        directional_agreement=True,
        calibration_delta=Decimal("0"),
        execution_cost_delta=Decimal("0"),
        fill_delta=Decimal("0"),
        latency_delta=Decimal("0"),
        capacity_delta=Decimal("0"),
        regime_delta=Decimal("0"),
        threshold_policy_refs=("THRESHOLD::RUNTIME",),
        typed_blockers=(),
        terminal_state=DivergenceTerminalStateV1.CONSISTENT_WITHIN_LOCKED_THRESHOLDS,
    )


def _runtime_conflicting_divergence(
    replay: ReplayResultContractV1,
    paper: PaperResultContractV1,
) -> DivergenceAssessmentV1:
    return replace(
        _runtime_divergence(replay, paper),
        assessment_id="DIVERGENCE::RUNTIME::CONFLICT",
        directional_agreement=False,
        calibration_delta=None,
        typed_blockers=(ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),
        terminal_state=(
            DivergenceTerminalStateV1.INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE
        ),
    )


def _runtime_model_risk(
    replay: ReplayResultContractV1,
    paper: PaperResultContractV1,
    *,
    assessment_id: str,
    evaluated_at: datetime,
    review_receipt_ref: str = "EXPLICIT_ABSENCE",
    independent_review_state: str = "READY_FOR_INDEPENDENT_REVIEW",
    receipt_refs: tuple[str, ...] = ("RECEIPT::MODEL-RISK-UPSTREAM",),
) -> object:
    review_pending = (
        independent_review_state != "CLOSED_INDEPENDENTLY_VALIDATED"
    )
    controls = tuple(
        ModelRiskControlEvidenceV1(
            control_id,
            ModelRiskControlStateV1.PASS_RECEIPTED,
            (f"RECEIPT::{control_id}",),
            (),
            (),
            True,
        )
        for control_id in MODEL_RISK_CONTROL_IDS_V1
    )
    conditions = tuple(
        NoTradeConditionOutcomeV1(
            condition_id,
            review_pending
            and condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED",
            (),
            (
                (ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,)
                if review_pending
                and condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
                else ()
            ),
        )
        for condition_id in NO_TRADE_CONDITION_IDS_V1
    )
    expiry = evaluated_at + timedelta(hours=4)
    basis = ModelRiskAdjudicationBasisV1(
        expected_component_or_template_ref=replay.cohort_template_id,
        evaluated_at=evaluated_at,
        required_evidence_valid_until=expiry,
        required_evidence_receipt_refs=(
            f"ST12F-RECEIPT::{replay.result_id}::REPLAY_REGISTRATION",
            f"ST12F-RECEIPT::{paper.result_id}::PAPER_REGISTRATION",
        ),
        replay_lane=ModelRiskLaneEvidenceV1(
            "REPLAY",
            f"ST12F-RECEIPT::{replay.result_id}::REPLAY_REGISTRATION",
            replay.input_lock_id,
            replay.cohort_template_id,
            replay.closed_at,
            expiry,
        ),
        paper_lane=ModelRiskLaneEvidenceV1(
            "PAPER",
            f"ST12F-RECEIPT::{paper.result_id}::PAPER_REGISTRATION",
            paper.input_lock_id,
            paper.cohort_template_id,
            paper.closed_at,
            expiry,
        ),
        uncertainty_reserve=Decimal("0.05"),
        model_risk_reserve=Decimal("0.05"),
        capacity_hard_veto=False,
        liquidity_hard_veto=False,
        capacity_liquidity_receipt_refs=("RECEIPT::CAPACITY-LIQUIDITY",),
        independent_review_state=independent_review_state,
        independent_review_receipt_ref=review_receipt_ref,
    )
    comparison = PermanentNoTradeEvidenceComparisonV1(
        comparison_id=f"NO-TRADE-COMPARISON::{assessment_id}",
        input_lock_id=replay.input_lock_id,
        execution_adjusted_lcb=Decimal("0.1"),
        candidate_utility=Decimal("1"),
        strongest_classical_utility=Decimal("0.8"),
        no_trade_utility=Decimal("0"),
        strongest_comparator="CANDIDATE",
    )
    return ModelRiskEvidenceAdjudicatorV1().adjudicate(
        assessment_id=assessment_id,
        input_lock_id=replay.input_lock_id,
        controls=controls,
        conditions=conditions,
        comparison=comparison,
        adjudication_basis=basis,
        limitations=("LIMITATION::RUNTIME",),
        receipt_refs=receipt_refs,
    )


def _runtime_quantum(
    input_lock_id: str,
    *,
    math_spec_id: str,
    identity: str,
) -> QuantumTraceValidationReceiptV1:
    basis = QuantumEconomicBasisV1(
        input_lock_id=input_lock_id,
        original_formulation_id="MATH-01",
        objective_sense="MAXIMIZE",
        constraint_refs=("CONSTRAINT::RUNTIME",),
        accounting_basis_ref="ACCOUNTING::NET",
        cost_basis_ref="COST::ALL-IN",
        capacity_basis_ref="CAPACITY::RUNTIME",
        scenario_set_ref="SCENARIO::1",
        resource_budget_ref="RESOURCE::RUNTIME",
        ttl_policy_ref="TTL::RUNTIME",
        version_epoch_pins=("SOURCE::1=EPOCH::1", f"VERSION::{identity}"),
    )
    return QuantumTraceValidationReceiptV1(
        receipt_id=f"QUANTUM-TRACE::{identity}::{math_spec_id}",
        schema_version="QTT_ST12F_QUANTUM_TRACE_VALIDATION_V1_4",
        contract_version="1.4",
        math_spec_id=math_spec_id,
        trace_id=f"TRACE::{identity}::{math_spec_id}",
        input_lock_id=input_lock_id,
        formulation_id="MATH-01",
        comparison_basis=basis,
        selected_candidate_id=f"CANDIDATE::{identity}::{math_spec_id}",
        recomputed_objective=Decimal("1"),
        recomputed_variance_or_explicit_absence=(
            "EXPLICIT_ABSENCE"
            if math_spec_id == "MATH-50"
            else Decimal("0")
        ),
        selected_original_model_feasible=True,
        selected_hard_veto=False,
        original_model_interpret_back_valid=True,
        strongest_classical_receipt_ref=f"CLASSICAL::{identity}",
        no_trade_receipt_ref=f"NO-TRADE::{identity}",
        original_economic_utility=Decimal("1"),
        resource_use=Decimal("1"),
        latency=Decimal("1"),
        deterministic_tie_break=f"CANDIDATE::{identity}::{math_spec_id}",
        effect_counts={
            "ansatz_construction": 0,
            "optimizer": 0,
            "estimator": 0,
            "sampler": 0,
            "transpiler": 0,
            "simulator": 0,
            "provider": 0,
            "qpu": 0,
        },
        terminal_state="VALIDATED_TRACE_ONLY",
    )


def _runtime_comparison(
    quantum: QuantumTraceValidationReceiptV1,
    *,
    identity: str,
) -> QuantumClassicalNoTradeComparisonV1:
    basis = quantum.comparison_basis
    classical = EconomicComparatorReceiptV1(
        receipt_id=f"CLASSICAL::{identity}",
        comparator_class="STRONGEST_CLASSICAL",
        comparison_basis=basis,
        feasible=True,
        hard_veto=False,
        conservative_utility=Decimal("0.8"),
        resource_use=Decimal("1"),
        latency=Decimal("1"),
        deterministic_tie_break=f"CLASSICAL::{identity}",
    )
    no_trade = EconomicComparatorReceiptV1(
        receipt_id=f"NO-TRADE::{identity}",
        comparator_class="NO_TRADE",
        comparison_basis=basis,
        feasible=True,
        hard_veto=False,
        conservative_utility=Decimal("0"),
        resource_use=Decimal("0"),
        latency=Decimal("0"),
        deterministic_tie_break=f"NO-TRADE::{identity}",
    )
    return QuantumClassicalNoTradeComparisonV1(
        comparison_id=f"COMPARISON::{identity}",
        input_lock_id=basis.input_lock_id,
        formulation_id=basis.original_formulation_id,
        comparison_basis=basis,
        validated_quantum=quantum.as_comparator(),
        strongest_classical=classical,
        no_trade=no_trade,
        validated_quantum_receipt_ref=quantum.receipt_id,
        strongest_classical_receipt_ref=classical.receipt_id,
        no_trade_receipt_ref=no_trade.receipt_id,
        quantum_utility=Decimal("1"),
        strongest_classical_utility=Decimal("0.8"),
        no_trade_utility=Decimal("0"),
        delta_quantum_vs_classical=Decimal("0.2"),
        delta_quantum_vs_no_trade=Decimal("1"),
        winner="VALIDATED_QUANTUM",
    )


def _metric_value(output_type: str) -> object:
    if output_type == "Decimal":
        return "0"
    if output_type == "float64":
        return 0.0
    if output_type == "[float64,float64]":
        return [0.0, 0.0]
    if output_type == "float64 matrix":
        return [[0.0]]
    if output_type == "typed path registry":
        return ["fold/path"]
    if output_type in {
        "typed vector",
        "typed fold registry",
    }:
        return [0]
    return {"measured": 0}


def _metric_spine(
    harness: _RuntimeHarnessV1,
    *,
    binding: object,
    record_ref: str,
    recorded_at: datetime,
    comparison: QuantumClassicalNoTradeComparisonV1 | None = None,
    value_override: object | None = None,
    failure_code: str | None = None,
) -> EconomicReceiptEventSpineV1:
    math_spec_id = str(getattr(binding, "math_spec_id"))
    output_name = str(getattr(binding, "output_name"))
    output_type = str(getattr(binding, "output_type"))
    output_unit = str(getattr(binding, "output_unit"))
    value = (
        json.loads(comparison.canonical_json())
        if comparison is not None
        else _metric_value(output_type)
        if value_override is None
        else value_override
    )
    implementation = str(
        harness.snapshot.implementation_versions[math_spec_id]
    )
    receipt = ComputationExecutionReceiptV1(
        receipt_id=record_ref,
        specification_id=math_spec_id,
        implementation_id=implementation,
        input_version=harness.compilation.input_lock_id,
        output_json=deterministic_json({output_name: value}),
    )
    payload = DurableComputationExecutionReceiptRecordV1(
        record_id=record_ref,
        existing_receipt=receipt,
        execution_context_ref=harness.context.context_id,
        input_snapshot_ref=harness.compilation.input_lock_id,
        input_value_lineage_refs=(f"LINEAGE::{record_ref}",),
        dependency_receipt_refs=(),
        started_at=recorded_at,
        completed_at=recorded_at,
        latency_ns=0,
        output_unit=output_unit,
        output_basis=ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1[math_spec_id],
        accounting_class="ST12F_TEST_EVIDENCE",
        fallback_used=False,
        warning_codes=(),
        failure_code=failure_code,
        consumer_ref="MATH-01",
        mode_ref="NO_EFFECT",
    )
    return EconomicReceiptEventSpineV1(
        record_id=record_ref,
        record_type=EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT,
        schema_version="QTT_DURABLE_COMPUTATION_RECEIPT_SPINE_V1",
        semantic_owner="ComputationEvidenceServiceV1",
        implementation_owner="ComputationEvidenceServiceV1",
        context_ref=harness.context.context_id,
        effective_at=recorded_at,
        recorded_at=recorded_at,
        causation_id=harness.snapshot.causation_id,
        correlation_id=harness.snapshot.correlation_id,
        traceparent=_TRACEPARENT,
        tracestate="qtt=runtime",
        sequence=0,
        aggregate_id=record_ref,
        aggregate_version=1,
        authority_class="COMPUTATION_EVIDENCE_NO_EFFECT",
        typed_payload=payload,
        no_effect_flags=NO_EFFECTS_V1,
    )


def _insert_spines(
    persistence: InMemoryPersistenceAdapterV1,
    spines: tuple[EconomicReceiptEventSpineV1, ...],
) -> None:
    transaction = persistence.begin_transaction()
    try:
        for spine in spines:
            persistence.insert_receipt_record(transaction, spine)
        transaction.commit()
    except BaseException:
        if transaction.is_active:
            transaction.rollback()
        raise


def _control_request(
    harness: _RuntimeHarnessV1,
    *,
    identity: str,
    requested_at: datetime,
) -> RegisterEvidenceControlRequestV1:
    return RegisterEvidenceControlRequestV1(
        request_id=f"REQUEST::CONTROL::{identity}",
        requested_at=requested_at,
        principal_id="PRINCIPAL::RUNTIME",
        context=harness.context,
        idempotency_key=f"IDEMPOTENCY::CONTROL::{identity}",
        traceparent=_TRACEPARENT,
        tracestate="qtt=runtime",
        input_lock_id=harness.compilation.input_lock_id,
    )


def _register_control(
    harness: _RuntimeHarnessV1,
    contract: object,
    *,
    identity: str,
    requested_at: datetime,
) -> str:
    return harness.service.register_control(
        _control_request(
            harness,
            identity=identity,
            requested_at=requested_at,
        ),
        contract,
    ).record_id


@dataclass(frozen=True, slots=True)
class _CompleteCustodyV1:
    harness: _RuntimeHarnessV1
    replay: ReplayResultContractV1
    paper: PaperResultContractV1
    dispositions: tuple[EvidenceIdentityDispositionV1, ...]
    component_versions: Mapping[str, object]
    math_refs: tuple[str, ...]
    quantum_50_ref: str
    quantum_51_ref: str
    math_52_ref: str
    static_refs: tuple[str, ...]
    divergence: DivergenceAssessmentV1
    divergence_ref: str


def _sections_from_rows(
    rows: tuple[EvidenceIdentityDispositionV1, ...],
) -> dict[str, EvidenceSectionV1]:
    output: dict[str, EvidenceSectionV1] = {}
    offset = 0
    for index, name in enumerate(_SECTION_FIELDS):
        width = 8 if index == len(_SECTION_FIELDS) - 1 else 4
        output[name] = EvidenceSectionV1(
            name,
            rows[offset : offset + width],
        )
        offset += width
    assert offset == 48
    return output


def _prepare_complete_custody(
    harness: _RuntimeHarnessV1,
    *,
    identity: str,
    time_offset: int,
) -> _CompleteCustodyV1:
    replay, paper = _register_dual_lanes(harness, identity=identity)
    quantum_50 = _runtime_quantum(
        replay.input_lock_id,
        math_spec_id="MATH-50",
        identity=identity,
    )
    quantum_51 = _runtime_quantum(
        replay.input_lock_id,
        math_spec_id="MATH-51",
        identity=identity,
    )
    comparison = _runtime_comparison(quantum_50, identity=identity)
    generic_refs: dict[str, str] = {}
    spines: list[EconomicReceiptEventSpineV1] = []
    receipt_time = _NOW + timedelta(seconds=time_offset)
    for binding in ST12F_EVIDENCE_OUTPUT_BINDINGS_V1:
        if binding.static_not_applicable_allowed or binding.math_spec_id in {
            "MATH-50",
            "MATH-51",
        }:
            continue
        ref = f"ST12F-DURABLE::{identity}::{binding.math_spec_id}"
        generic_refs[binding.math_spec_id] = ref
        spines.append(
            _metric_spine(
                harness,
                binding=binding,
                record_ref=ref,
                recorded_at=receipt_time,
                comparison=(
                    comparison if binding.math_spec_id == "MATH-52" else None
                ),
            )
        )
    _insert_spines(harness.persistence, tuple(spines))
    quantum_50_ref = _register_control(
        harness,
        quantum_50,
        identity=f"{identity}::MATH-50",
        requested_at=receipt_time + timedelta(seconds=1),
    )
    quantum_51_ref = _register_control(
        harness,
        quantum_51,
        identity=f"{identity}::MATH-51",
        requested_at=receipt_time + timedelta(seconds=1),
    )
    divergence = _runtime_divergence(
        replay,
        paper,
        identity=identity,
    )
    divergence_ref = _register_control(
        harness,
        divergence,
        identity=f"{identity}::DIVERGENCE",
        requested_at=receipt_time + timedelta(seconds=1),
    )

    rows: list[EvidenceIdentityDispositionV1] = []
    versions: dict[str, object] = {}
    math_refs: list[str] = []
    static_refs: list[str] = []
    static_ids = {
        "MATH-01",
        "MATH-02",
        "MATH-03",
        "MATH-04",
        "MATH-05",
        "MATH-06",
        "MATH-07",
        "MATH-34",
        "MATH-35",
        "MATH-36",
    }
    for math_spec_id in ST12F_EVIDENCE_IDENTITIES_V1:
        if math_spec_id in static_ids:
            proof = StaticEvidenceApplicabilityProofV1.for_scope(
                math_spec_id=math_spec_id,
                component_or_template_ref="MATH-01",
                input_lock_id=replay.input_lock_id,
            )
            rows.append(
                EvidenceIdentityDispositionV1(
                    math_spec_id,
                    EvidenceIdentityDispositionStateV1.NOT_APPLICABLE_WITH_PROOF,
                    (),
                    (),
                    (proof.proof_id,),
                )
            )
            static_refs.append(proof.proof_id)
            continue
        if math_spec_id == "MATH-50":
            ref = quantum_50_ref
        elif math_spec_id == "MATH-51":
            ref = quantum_51_ref
        else:
            ref = generic_refs[math_spec_id]
            if math_spec_id != "MATH-52":
                math_refs.append(ref)
        rows.append(
            EvidenceIdentityDispositionV1(
                math_spec_id,
                EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED,
                (ref,),
                (),
                (),
            )
        )
        versions[math_spec_id] = harness.snapshot.implementation_versions[
            math_spec_id
        ]
    return _CompleteCustodyV1(
        harness=harness,
        replay=replay,
        paper=paper,
        dispositions=tuple(rows),
        component_versions=versions,
        math_refs=tuple(math_refs),
        quantum_50_ref=quantum_50_ref,
        quantum_51_ref=quantum_51_ref,
        math_52_ref=generic_refs["MATH-52"],
        static_refs=tuple(static_refs),
        divergence=divergence,
        divergence_ref=divergence_ref,
    )


def _bundle_provenance(
    custody: _CompleteCustodyV1,
    *,
    model_risk_ref: str,
    review_ref: str | None = None,
    proof_refs: tuple[str, ...] = (),
) -> tuple[str, ...]:
    lock_ref = (
        f"ST12F-RECEIPT::{custody.replay.input_lock_id}::INPUT_LOCK"
    )
    lane_refs = (
        f"ST12F-RECEIPT::{custody.replay.result_id}::REPLAY_REGISTRATION",
        f"ST12F-RECEIPT::{custody.paper.result_id}::PAPER_REGISTRATION",
    )
    return (
        lock_ref,
        *lane_refs,
        *custody.math_refs,
        custody.divergence_ref,
        model_risk_ref,
        custody.quantum_50_ref,
        custody.quantum_51_ref,
        custody.math_52_ref,
        *(() if review_ref is None else (review_ref,)),
        *proof_refs,
        *custody.static_refs,
    )


def _complete_candidate(
    custody: _CompleteCustodyV1,
    *,
    evidence_id: str,
    version: str,
    state: EvidenceBundleTerminalStateV1,
    model_risk: object,
    model_risk_ref: str,
    review_ref: str | None = None,
    proof_refs: tuple[str, ...] = (),
    blockers: tuple[ReasonCode, ...] = (),
    d_reference: ST12FEvidenceReferenceV1 | str = "UNAVAILABLE",
    g_handoff: FToGHandoffReferencesV1 | str = "UNAVAILABLE",
) -> ComputationEvidenceBundleV1:
    negative: list[str] = []
    review_validated = (
        state
        in {
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.SUPERSEDED,
        }
        and review_ref is not None
    )
    for row in getattr(model_risk, "no_trade_condition_outcomes"):
        if row.active and not (
            row.condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
            and review_validated
        ):
            negative.append(f"NO_TRADE::{row.condition_id}")
    negative.extend(f"LIFECYCLE::{code.value}" for code in blockers)
    lane_refs = (
        f"ST12F-RECEIPT::{custody.replay.result_id}::REPLAY_REGISTRATION",
        f"ST12F-RECEIPT::{custody.paper.result_id}::PAPER_REGISTRATION",
    )
    return ComputationEvidenceBundleV1(
        evidence_id=evidence_id,
        schema_version="QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4",
        contract_version="1.4",
        evidence_bundle_version=version,
        component_or_template_ref="MATH-01",
        input_lock_id=custody.replay.input_lock_id,
        actual_executed_component_versions=custody.component_versions,
        actual_executed_stack_versions={},
        replay_result_ref=custody.replay.result_id,
        paper_result_ref=custody.paper.result_id,
        divergence_assessment_ref=custody.divergence.assessment_id,
        lane_execution_receipt_refs=lane_refs,
        **_sections_from_rows(custody.dispositions),
        independent_review_state=state.value,
        failure_and_negative_evidence_states=tuple(negative),
        source_and_provenance_refs=_bundle_provenance(
            custody,
            model_risk_ref=model_risk_ref,
            review_ref=review_ref,
            proof_refs=proof_refs,
        ),
        d_evidence_reference_projection=d_reference,
        g_handoff_projection=g_handoff,
        terminal_state=state,
        blocker_codes=blockers,
    )


def _bundle_request(
    harness: _RuntimeHarnessV1,
    *,
    identity: str,
    source_refs: tuple[str, ...],
    requested_at: datetime,
) -> BuildEvidenceBundleRequestV1:
    return BuildEvidenceBundleRequestV1(
        request_id=f"REQUEST::OP15::{identity}",
        operation_name="build_evidence_bundle",
        requested_at=requested_at,
        principal_id="PRINCIPAL::RUNTIME",
        capability_bundle_id="CAPABILITY::RUNTIME",
        context=harness.context,
        idempotency_key=f"IDEMPOTENCY::OP15::{identity}",
        traceparent=_TRACEPARENT,
        tracestate="qtt=runtime",
        component_id="MATH-01",
        input_lock_id=harness.compilation.input_lock_id,
        evidence_record_refs=source_refs,
        required_lanes=("REPLAY", "PAPER"),
    )


def _incomplete_candidate(
    harness: _RuntimeHarnessV1,
    replay: ReplayResultContractV1,
    *,
    evidence_id: str,
    version: str,
) -> ComputationEvidenceBundleV1:
    rows = tuple(
        EvidenceIdentityDispositionV1(
            math_spec_id,
            EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON,
            (),
            (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),
            (),
        )
        for math_spec_id in ST12F_EVIDENCE_IDENTITIES_V1
    )
    refs = (
        f"ST12F-RECEIPT::{replay.input_lock_id}::INPUT_LOCK",
        f"ST12F-RECEIPT::{replay.result_id}::REPLAY_REGISTRATION",
    )
    negative = tuple(
        f"DISPOSITION::{math_spec_id}::ST12F_EVIDENCE_INCOMPLETE"
        for math_spec_id in ST12F_EVIDENCE_IDENTITIES_V1
    ) + ("LIFECYCLE::ST12F_EVIDENCE_INCOMPLETE",)
    return ComputationEvidenceBundleV1(
        evidence_id=evidence_id,
        schema_version="QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4",
        contract_version="1.4",
        evidence_bundle_version=version,
        component_or_template_ref="MATH-01",
        input_lock_id=replay.input_lock_id,
        actual_executed_component_versions={},
        actual_executed_stack_versions={},
        replay_result_ref=replay.result_id,
        paper_result_ref="EXPLICIT_ABSENCE",
        divergence_assessment_ref="EXPLICIT_ABSENCE",
        lane_execution_receipt_refs=(refs[1],),
        **_sections_from_rows(rows),
        independent_review_state=(
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER.value
        ),
        failure_and_negative_evidence_states=negative,
        source_and_provenance_refs=refs,
        d_evidence_reference_projection="UNAVAILABLE",
        g_handoff_projection="UNAVAILABLE",
        terminal_state=EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        blocker_codes=(ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),
    )


def _closed_projections(
    *,
    evidence_id: str,
    version: str,
    input_lock_id: str,
    observed_at: datetime,
    valid_until: datetime,
    model_receipt_ref: str,
    math_52_ref: str,
    identity: str,
) -> tuple[ST12FEvidenceReferenceV1, FToGHandoffReferencesV1]:
    bundle_ref = f"ST12F-RECEIPT::{version}::EVIDENCE_BUNDLE_VERSION"
    source_epochs = ("SOURCE::1=EPOCH::1",)
    reference = ST12FEvidenceReferenceV1(
        evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
        evidence_ref=bundle_ref,
        lane="REPLAY_PAPER",
        dataset_grade_ref=f"DATASET-GRADE::{identity}",
        venue_semantic_binding_ref=f"VENUE-SEMANTICS::{identity}",
        cross_venue_equivalence_ref=f"CROSS-VENUE::{identity}",
        observed_at=observed_at,
        valid_until=valid_until,
        policy_version="ST12F_EVIDENCE_POLICY_V1_4",
        causation_id=f"CAUSE::{identity}",
        correlation_id=f"CORRELATION::{identity}",
        input_lock_id=input_lock_id,
        component_or_template_ref="MATH-01",
        evidence_bundle_version=version,
        source_epoch_refs=source_epochs,
        terminal_state=(
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value
        ),
        reference_id=f"D-REFERENCE::{identity}",
        evidence_id=evidence_id,
    )
    handoff = FToGHandoffReferencesV1(
        handoff_id=f"G-HANDOFF::{identity}",
        contract_version="1.4",
        input_lock_id=input_lock_id,
        source_epoch_refs=source_epochs,
        observed_at=observed_at,
        valid_until=valid_until,
        terminal_state=reference.terminal_state,
        evidence_bundle_ref=bundle_ref,
        no_trade_blocker_refs=(),
        champion_challenger_evidence_refs=(model_receipt_ref,),
        portfolio_utility_refs=(f"PORTFOLIO-UTILITY::{identity}",),
        quantum_classical_comparison_receipt_ref=math_52_ref,
    )
    return reference, handoff


def _review_record(
    *,
    identity: str,
    prior_ref: str,
    evidence_id: str,
    candidate_version: str,
    input_lock_id: str,
    reviewed_at: datetime,
) -> IndependentReviewRecordV1:
    return IndependentReviewRecordV1(
        review_id=f"REVIEW::{identity}",
        schema_version="QTT_ST12F_INDEPENDENT_REVIEW_RECORD_V1_4",
        contract_version="1.4",
        prior_bundle_ref=prior_ref,
        evidence_id=evidence_id,
        evidence_bundle_version=candidate_version,
        input_lock_id=input_lock_id,
        reviewer_identity="REVIEWER::INDEPENDENT",
        bundle_producer_identity="ComputationEvidenceServiceV1",
        authority_receipt_ref=f"AGENT-ORCH::REVIEW::{identity}",
        reviewed_source_epoch_refs=("SOURCE::1=EPOCH::1",),
        decision=IndependentReviewDecisionV1.VALIDATED,
        blocker_codes=(),
        reviewed_at=reviewed_at,
        valid_until=reviewed_at + timedelta(hours=4),
    )


def _review_authority(
    review: IndependentReviewRecordV1,
    *,
    context_ref: str,
) -> AgentCapabilityDecisionV1:
    return AgentCapabilityDecisionV1(
        decision_id=f"DECISION::{review.review_id}",
        request_id=f"REQUEST::{review.review_id}",
        task_id=f"TASK::{review.review_id}",
        principal_id="PRINCIPAL::RUNTIME",
        current_agent_id=review.reviewer_identity,
        source_agent_refs=("AGENT_RT_11",),
        operation_id="build_evidence_bundle",
        policy_version=POLICY_VERSION,
        decision_state=(
            AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
        ),
        reason_codes=(),
        scope_refs=(
            "INDEPENDENT_REVIEW_ONLY",
            f"context_ref={context_ref}",
            f"input_lock_id={review.input_lock_id}",
            "component_or_template_ref=MATH-01",
        ),
        idempotency_key=f"IDEMPOTENCY::{review.review_id}",
        retry_disposition="NO_RETRY_AUTHORITY",
        peer_sod_disposition="PEER_CHALLENGE_AND_SOD_ENFORCED",
        safety_state_disposition="NON_MATERIAL_LOCAL_NO_EFFECT",
        terminal_route="INDEPENDENT_REVIEW_ONLY",
        agent_orch_receipt_ref=review.authority_receipt_ref,
        st12c_causation_correlation_refs=(
            f"CAUSE::{review.review_id}",
            f"CORRELATION::{review.review_id}",
        ),
        evidence_refs=(review.prior_bundle_ref,),
        alternative_route_refs=("OWNER_REVIEW",),
        disagreement_state="NONE_DECLARED",
        confidence_state="EXACT_PREEXISTING_AUTHORITY",
        limitation_codes=("NO_RUNTIME_EFFECT",),
    )


class _AgentOrchRowsV1:
    def __init__(
        self,
        authority: AgentCapabilityDecisionV1,
        *,
        context_ref: str,
    ) -> None:
        self._rows = (
            {
                "projection_ref": authority.agent_orch_receipt_ref,
                "task_id": authority.task_id,
                "principal_id": authority.principal_id,
                "current_agent_id": authority.current_agent_id,
                "operation_id": authority.operation_id,
                "context_ref": context_ref,
                "control_plane_only": True,
                "runtime_side_effect_allowed": False,
            },
        )

    def list_decision_receipts(self) -> tuple[dict[str, object], ...]:
        return self._rows


def _persist_review(
    custody: _CompleteCustodyV1,
    review: IndependentReviewRecordV1,
) -> tuple[str, AgentCapabilityDecisionV1]:
    authority = _review_authority(
        review,
        context_ref=custody.harness.context.context_id,
    )
    producer = IndependentEvidenceReviewV1(
        custody.harness.compiler,
        custody.harness.persistence,
        _AgentOrchRowsV1(
            authority,
            context_ref=custody.harness.context.context_id,
        ),
    )
    spine = producer.review_ready_bundle(
        review,
        authority,
        principal_id=authority.principal_id,
        context_ref=custody.harness.context.context_id,
        component_or_template_ref="MATH-01",
        traceparent=_TRACEPARENT,
        tracestate="qtt=runtime",
    )
    return spine.record_id, authority


def _closed_candidate(
    custody: _CompleteCustodyV1,
    *,
    evidence_id: str,
    version: str,
    parent_ref: str,
    identity: str,
    reviewed_at: datetime,
    model_time: datetime,
    build_time: datetime,
) -> tuple[
    ComputationEvidenceBundleV1,
    BuildEvidenceBundleRequestV1,
    IndependentReviewRecordV1,
    str,
    object,
]:
    review = _review_record(
        identity=identity,
        prior_ref=parent_ref,
        evidence_id=evidence_id,
        candidate_version=version,
        input_lock_id=custody.replay.input_lock_id,
        reviewed_at=reviewed_at,
    )
    review_ref, authority = _persist_review(custody, review)
    model = _runtime_model_risk(
        custody.replay,
        custody.paper,
        assessment_id=f"MODEL-RISK::{identity}",
        evaluated_at=model_time,
        review_receipt_ref=review_ref,
        independent_review_state="CLOSED_INDEPENDENTLY_VALIDATED",
        receipt_refs=(
            parent_ref,
            review_ref,
            authority.agent_orch_receipt_ref,
        ),
    )
    model_ref = _register_control(
        custody.harness,
        model,
        identity=f"{identity}::MODEL-RISK",
        requested_at=model_time,
    )
    reference, handoff = _closed_projections(
        evidence_id=evidence_id,
        version=version,
        input_lock_id=custody.replay.input_lock_id,
        observed_at=build_time,
        valid_until=build_time + timedelta(hours=4),
        model_receipt_ref=model_ref,
        math_52_ref=custody.math_52_ref,
        identity=identity,
    )
    candidate = _complete_candidate(
        custody,
        evidence_id=evidence_id,
        version=version,
        state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        model_risk=model,
        model_risk_ref=model_ref,
        review_ref=review_ref,
        d_reference=reference,
        g_handoff=handoff,
    )
    request = _bundle_request(
        custody.harness,
        identity=identity,
        source_refs=candidate.source_and_provenance_refs,
        requested_at=build_time,
    )
    return candidate, request, review, model_ref, model


class _BundleCandidateResolverV1:
    def __init__(
        self,
        candidates: ComputationEvidenceBundleV1
        | Mapping[str, ComputationEvidenceBundleV1],
    ) -> None:
        self._candidates = candidates

    def resolve_bundle_candidate(
        self,
        request: BuildEvidenceBundleRequestV1,
    ) -> ComputationEvidenceBundleV1:
        if isinstance(self._candidates, Mapping):
            return self._candidates[request.request_id]
        return self._candidates


def _typed_lane_packet_record(
    packet: ReplayResultContractV1 | PaperResultContractV1,
) -> TypedValueRecordV1:
    raw = json.loads(packet.canonical_json())
    json_fields = {
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
        "failure_states",
        "limitations",
    }
    values: list[TypedValueV1] = []
    for field in fields(type(packet)):
        value = raw[field.name]
        if field.name in json_fields:
            kind = TypedValueKindV1.TEXT
            value = deterministic_json(value)
        elif field.name == "fixture_only_not_evidence":
            kind = TypedValueKindV1.BOOLEAN
        else:
            kind = TypedValueKindV1.TEXT
        values.append(
            TypedValueV1(
                field.name,
                kind,
                value,
                "unitless",
                "canonical ST12-F lane packet",
            )
        )
    return TypedValueRecordV1(tuple(values))


def _facade(
    harness: _RuntimeHarnessV1,
    service: ComputationEvidenceServiceV1,
) -> QKUComputationControlPlaneV1:
    return QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=_NoEffectAdmissionV1(),
        persistence_adapter=harness.persistence,
        replay_paper_cohort_compiler=harness.compiler,
        computation_evidence_service=service,
    )


def _threaded(
    *actions: Callable[[], object],
) -> tuple[tuple[object | None, ...], tuple[BaseException | None, ...]]:
    results: list[object | None] = [None] * len(actions)
    errors: list[BaseException | None] = [None] * len(actions)

    def run(index: int, action: Callable[[], object]) -> None:
        try:
            results[index] = action()
        except BaseException as exc:
            errors[index] = exc

    threads = tuple(
        Thread(target=run, args=(index, action), daemon=True)
        for index, action in enumerate(actions)
    )
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    return tuple(results), tuple(errors)


def _barrier_after_once(
    instance: object,
    method_name: str,
    barrier: Barrier,
) -> None:
    original = getattr(instance, method_name)
    armed = True

    def wrapped(*args: object, **kwargs: object) -> object:
        nonlocal armed
        result = original(*args, **kwargs)
        if armed:
            armed = False
            barrier.wait(timeout=10)
        return result

    setattr(instance, method_name, wrapped)


def _assert_reason(
    action: Callable[[], object],
    reason: ReasonCode,
    exception_type: type[BaseException] = ContractValidationError,
) -> None:
    try:
        action()
    except exception_type as exc:
        assert getattr(exc, "reason_code", None) is reason
    else:
        raise AssertionError(f"expected {exception_type.__name__}:{reason.value}")


def _control_rows(
    persistence: InMemoryPersistenceAdapterV1,
    *,
    cutoff: datetime,
) -> tuple[EconomicReceiptEventSpineV1, ...]:
    return tuple(
        row
        for row in persistence.reconstruct_as_of(
            effective_cutoff=cutoff,
            recorded_cutoff=cutoff,
            aggregate_scope=(),
        )
        if type(row) is EconomicReceiptEventSpineV1
        and type(row.typed_payload) is ST12FEvidenceControlReceiptRecordV1
    )


def _replace_disposition_ref(
    candidate: ComputationEvidenceBundleV1,
    *,
    math_spec_id: str,
    new_ref: str,
) -> ComputationEvidenceBundleV1:
    rows = [
        row
        for section_name in _SECTION_FIELDS
        for row in getattr(candidate, section_name).identity_dispositions
    ]
    index = next(
        offset
        for offset, row in enumerate(rows)
        if row.evidence_identity == math_spec_id
    )
    old_ref = rows[index].evidence_record_refs[0]
    rows[index] = replace(rows[index], evidence_record_refs=(new_ref,))
    provenance = tuple(
        dict.fromkeys(
            new_ref if ref == old_ref else ref
            for ref in candidate.source_and_provenance_refs
        )
    )
    return replace(
        candidate,
        source_and_provenance_refs=provenance,
        **_sections_from_rows(tuple(rows)),
    )


_CONCURRENCY_CASE_IDS_V1_7 = (
    "OUTCOME-01",
    "OUTCOME-02",
    "OP14-IDENTICAL",
    "OP14-COMPETING",
    "OP15-ROOT-IDENTICAL",
    "OP15-ROOT-COMPETING",
    "OP15-SIBLING",
    "BITEMPORAL",
    "REVIEW",
    "EVIDENCE-48",
    "METRICS-38",
    "TRUTH",
    "STALE-5",
    "SUPERSEDED",
    "CACHE",
)


def test_op14_atomic_restart_conflict_and_fixture_non_poisoning() -> None:
    observed = {"OUTCOME-01", "OP14-IDENTICAL", "OP14-COMPETING"}

    failing_adapter = _CommitFailingAdapterV1()
    failing = _runtime_harness(failing_adapter, identity="ATOMIC")
    before = failing.service._cache_snapshot
    failing_adapter.fail_next_commit = True
    _assert_reason(
        lambda: failing.service.register_result(
            _register_request(failing, "REPLAY", "ATOMIC"),
            _runtime_packet(failing, "REPLAY"),
        ),
        ReasonCode.PERSISTENCE_UNAVAILABLE,
        PersistenceContractError,
    )
    assert failing.service._cache_snapshot is before

    fixture = _runtime_harness(identity="FIXTURE")
    fixture_outcome = fixture.service.register_result(
        _register_request(fixture, "REPLAY", "FIXTURE"),
        _runtime_packet(fixture, "REPLAY", fixture=True),
    )
    assert fixture_outcome.receipt_refs == ()
    real_outcome = fixture.service.register_result(
        replace(
            _register_request(fixture, "REPLAY", "REAL"),
            idempotency_key="IDEMPOTENCY::OP14::REAL",
        ),
        _runtime_packet(fixture, "REPLAY"),
    )
    assert len(real_outcome.receipt_refs) == 1

    identical = _runtime_harness(identity="OP14-IDENTICAL")
    service_a = identical.service
    service_b = ComputationEvidenceServiceV1(
        identical.compiler,
        identical.persistence,
    )
    request_a = _register_request(identical, "REPLAY", "IDENTICAL-A")
    request_b = replace(
        request_a,
        request_id="REQUEST::OP14::IDENTICAL-B",
        idempotency_key="IDEMPOTENCY::OP14::IDENTICAL-B",
    )
    packet = _runtime_packet(
        identical,
        "REPLAY",
        result_id="RESULT::OP14-IDENTICAL",
        run_reference="RUN::OP14-IDENTICAL",
    )
    barrier = Barrier(2)
    _barrier_after_once(service_a, "_durable_lane_index", barrier)
    _barrier_after_once(service_b, "_durable_lane_index", barrier)
    results, errors = _threaded(
        lambda: service_a.register_result(request_a, packet),
        lambda: service_b.register_result(request_b, packet),
    )
    assert errors == (None, None)
    assert all(type(row) is RegisteredLaneResultOutcomeV1 for row in results)
    assert results[0] == results[1]
    assert service_a.register_result(request_a, packet) == results[0]
    identical_rows = tuple(
        row
        for row in _control_rows(
            identical.persistence,
            cutoff=_NOW + timedelta(hours=1),
        )
        if row.typed_payload.receipt_class
        is ST12FReceiptClassV1.REPLAY_REGISTRATION
    )
    assert len(identical_rows) == 1

    competing = _runtime_harness(identity="OP14-COMPETING")
    competing_a = competing.service
    competing_b = ComputationEvidenceServiceV1(
        competing.compiler,
        competing.persistence,
    )
    competing_request_a = _register_request(
        competing,
        "REPLAY",
        "COMPETING-A",
    )
    competing_request_b = replace(
        competing_request_a,
        request_id="REQUEST::OP14::COMPETING-B",
        idempotency_key="IDEMPOTENCY::OP14::COMPETING-B",
    )
    packet_a = _runtime_packet(
        competing,
        "REPLAY",
        result_id="RESULT::OP14-COMPETING-A",
        run_reference="RUN::OP14-COMPETING-A",
    )
    packet_b = _runtime_packet(
        competing,
        "REPLAY",
        result_id="RESULT::OP14-COMPETING-B",
        run_reference="RUN::OP14-COMPETING-B",
    )
    barrier = Barrier(2)
    _barrier_after_once(competing_a, "_durable_lane_index", barrier)
    _barrier_after_once(competing_b, "_durable_lane_index", barrier)
    results, errors = _threaded(
        lambda: competing_a.register_result(competing_request_a, packet_a),
        lambda: competing_b.register_result(competing_request_b, packet_b),
    )
    assert sum(type(row) is RegisteredLaneResultOutcomeV1 for row in results) == 1
    conflicts = tuple(row for row in errors if row is not None)
    assert len(conflicts) == 1
    assert type(conflicts[0]) is ContractValidationError
    assert conflicts[0].reason_code is ReasonCode.ST12F_RESULT_SLOT_CONFLICT
    competing_rows = tuple(
        row
        for row in _control_rows(
            competing.persistence,
            cutoff=_NOW + timedelta(hours=1),
        )
        if row.typed_payload.receipt_class
        is ST12FReceiptClassV1.REPLAY_REGISTRATION
    )
    assert len(competing_rows) == 1

    public = _runtime_harness(identity="OUTCOME-01")
    public_service = public.service
    facade = _facade(public, public_service)
    public_packets = {
        lane: _runtime_packet(
            public,
            lane,
            result_id=f"RESULT::OUTCOME-01::{lane}",
            run_reference=f"RUN::OUTCOME-01::{lane}",
        )
        for lane in ("REPLAY", "PAPER")
    }
    public_requests = {
        lane: replace(
            _register_request(public, lane, f"OUTCOME-01::{lane}"),
            result_packet=_typed_lane_packet_record(public_packets[lane]),
        )
        for lane in ("REPLAY", "PAPER")
    }
    barrier = Barrier(2)
    original_register = public_service.register_result

    def interleaved_register(
        request: RegisterReplayPaperResultRequestV1,
        packet: ReplayResultContractV1 | PaperResultContractV1 | None = None,
    ) -> RegisteredLaneResultOutcomeV1:
        outcome = original_register(request, packet)
        barrier.wait(timeout=10)
        return outcome

    public_service.register_result = interleaved_register
    results, errors = _threaded(
        lambda: facade.register_replay_paper_result(public_requests["REPLAY"]),
        lambda: facade.register_replay_paper_result(public_requests["PAPER"]),
    )
    assert errors == (None, None)
    for response, lane in zip(results, ("REPLAY", "PAPER"), strict=True):
        assert response.receipt_refs == response.registration.evidence_refs
        assert response.receipt_refs == (
            f"ST12F-RECEIPT::RESULT::OUTCOME-01::{lane}::{lane}_REGISTRATION",
        )
    assert observed == set(_CONCURRENCY_CASE_IDS_V1_7[:1]) | set(
        _CONCURRENCY_CASE_IDS_V1_7[2:4]
    )


def test_complete_durable_bundle_lifecycle_receipts_and_d_resolution() -> None:
    observed = {
        "OUTCOME-02",
        "OP15-ROOT-IDENTICAL",
        "OP15-ROOT-COMPETING",
        "OP15-SIBLING",
        "BITEMPORAL",
        "REVIEW",
        "EVIDENCE-48",
        "METRICS-38",
        "TRUTH",
        "STALE-5",
        "SUPERSEDED",
        "CACHE",
    }

    public = _runtime_harness(identity="OUTCOME-02")
    public_replay = public.service.register_result(
        _register_request(public, "REPLAY", "OUTCOME-02"),
        _runtime_packet(
            public,
            "REPLAY",
            result_id="RESULT::OUTCOME-02",
            run_reference="RUN::OUTCOME-02",
        ),
    ).registered_result
    assert type(public_replay) is ReplayResultContractV1
    public_requests: dict[str, BuildEvidenceBundleRequestV1] = {}
    public_candidates: dict[str, ComputationEvidenceBundleV1] = {}
    for suffix in ("A", "B"):
        candidate = _incomplete_candidate(
            public,
            public_replay,
            evidence_id=f"EVIDENCE::OUTCOME-02::{suffix}",
            version=f"BUNDLE::OUTCOME-02::{suffix}",
        )
        request = _bundle_request(
            public,
            identity=f"OUTCOME-02::{suffix}",
            source_refs=candidate.source_and_provenance_refs,
            requested_at=_NOW + timedelta(seconds=10),
        )
        public_requests[suffix] = request
        public_candidates[request.request_id] = candidate
    public_service = ComputationEvidenceServiceV1(
        public.compiler,
        public.persistence,
        bundle_candidate_resolver=_BundleCandidateResolverV1(
            public_candidates
        ),
    )
    public_facade = _facade(public, public_service)
    barrier = Barrier(2)
    original_build = public_service.build_bundle

    def interleaved_build(
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1 | None = None,
    ) -> BuiltEvidenceBundleOutcomeV1:
        outcome = original_build(request, candidate)
        barrier.wait(timeout=10)
        return outcome

    public_service.build_bundle = interleaved_build
    results, errors = _threaded(
        lambda: public_facade.build_evidence_bundle(public_requests["A"]),
        lambda: public_facade.build_evidence_bundle(public_requests["B"]),
    )
    assert errors == (None, None)
    for response, suffix in zip(results, ("A", "B"), strict=True):
        assert response.receipt_refs == response.evidence_bundle.evidence_refs
        assert response.receipt_refs == (
            f"ST12F-RECEIPT::BUNDLE::OUTCOME-02::{suffix}::EVIDENCE_BUNDLE_VERSION",
        )

    identical = _runtime_harness(identity="OP15-ROOT-IDENTICAL")
    identical_replay = identical.service.register_result(
        _register_request(identical, "REPLAY", "ROOT-IDENTICAL"),
        _runtime_packet(
            identical,
            "REPLAY",
            result_id="RESULT::ROOT-IDENTICAL",
            run_reference="RUN::ROOT-IDENTICAL",
        ),
    ).registered_result
    assert type(identical_replay) is ReplayResultContractV1
    identical_candidate = _incomplete_candidate(
        identical,
        identical_replay,
        evidence_id="EVIDENCE::ROOT-IDENTICAL",
        version="BUNDLE::ROOT-IDENTICAL",
    )
    identical_request_a = _bundle_request(
        identical,
        identity="ROOT-IDENTICAL-A",
        source_refs=identical_candidate.source_and_provenance_refs,
        requested_at=_NOW + timedelta(seconds=10),
    )
    identical_request_b = replace(
        identical_request_a,
        request_id="REQUEST::OP15::ROOT-IDENTICAL-B",
        idempotency_key="IDEMPOTENCY::OP15::ROOT-IDENTICAL-B",
    )
    identical_a = identical.service
    identical_b = ComputationEvidenceServiceV1(
        identical.compiler,
        identical.persistence,
    )
    barrier = Barrier(2)
    _barrier_after_once(identical_a, "_durable_current_bundle_ref", barrier)
    _barrier_after_once(identical_b, "_durable_current_bundle_ref", barrier)
    results, errors = _threaded(
        lambda: identical_a.build_bundle(
            identical_request_a,
            identical_candidate,
        ),
        lambda: identical_b.build_bundle(
            identical_request_b,
            identical_candidate,
        ),
    )
    assert errors == (None, None)
    assert results[0] == results[1]
    assert identical_a.build_bundle(
        identical_request_a,
        identical_candidate,
    ) == results[0]
    root_rows = tuple(
        row
        for row in _control_rows(
            identical.persistence,
            cutoff=_NOW + timedelta(hours=1),
        )
        if row.typed_payload.receipt_class
        is ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
    )
    assert len(root_rows) == 1

    competing = _runtime_harness(identity="OP15-ROOT-COMPETING")
    competing_replay = competing.service.register_result(
        _register_request(competing, "REPLAY", "ROOT-COMPETING"),
        _runtime_packet(
            competing,
            "REPLAY",
            result_id="RESULT::ROOT-COMPETING",
            run_reference="RUN::ROOT-COMPETING",
        ),
    ).registered_result
    assert type(competing_replay) is ReplayResultContractV1
    candidates = tuple(
        _incomplete_candidate(
            competing,
            competing_replay,
            evidence_id="EVIDENCE::ROOT-COMPETING",
            version=f"BUNDLE::ROOT-COMPETING::{suffix}",
        )
        for suffix in ("A", "B")
    )
    requests = tuple(
        _bundle_request(
            competing,
            identity=f"ROOT-COMPETING::{suffix}",
            source_refs=candidate.source_and_provenance_refs,
            requested_at=_NOW + timedelta(seconds=10),
        )
        for suffix, candidate in zip(("A", "B"), candidates, strict=True)
    )
    competing_a = competing.service
    competing_b = ComputationEvidenceServiceV1(
        competing.compiler,
        competing.persistence,
    )
    barrier = Barrier(2)
    _barrier_after_once(competing_a, "_durable_current_bundle_ref", barrier)
    _barrier_after_once(competing_b, "_durable_current_bundle_ref", barrier)
    results, errors = _threaded(
        lambda: competing_a.build_bundle(requests[0], candidates[0]),
        lambda: competing_b.build_bundle(requests[1], candidates[1]),
    )
    assert sum(type(row) is BuiltEvidenceBundleOutcomeV1 for row in results) == 1
    conflicts = tuple(row for row in errors if row is not None)
    assert len(conflicts) == 1
    assert type(conflicts[0]) is PersistenceContractError
    assert conflicts[0].reason_code is ReasonCode.PERSISTENCE_CONFLICT
    competing_bundle_rows = tuple(
        row
        for row in _control_rows(
            competing.persistence,
            cutoff=_NOW + timedelta(hours=1),
        )
        if row.typed_payload.receipt_class
        is ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
    )
    assert len(competing_bundle_rows) == 1

    harness = _runtime_harness(identity="OWNER-RECERTIFIED")
    custody = _prepare_complete_custody(
        harness,
        identity="OWNER-RECERTIFIED",
        time_offset=2,
    )
    ready_time = _NOW + timedelta(seconds=10)
    ready_model = _runtime_model_risk(
        custody.replay,
        custody.paper,
        assessment_id="MODEL-RISK::READY",
        evaluated_at=_NOW + timedelta(seconds=8),
    )
    ready_model_ref = _register_control(
        harness,
        ready_model,
        identity="READY::MODEL-RISK",
        requested_at=_NOW + timedelta(seconds=8),
    )
    ready = _complete_candidate(
        custody,
        evidence_id="EVIDENCE::OWNER-RECERTIFIED",
        version="BUNDLE::OWNER-RECERTIFIED::READY",
        state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        model_risk=ready_model,
        model_risk_ref=ready_model_ref,
    )
    ready_request = _bundle_request(
        harness,
        identity="OWNER-RECERTIFIED::READY",
        source_refs=ready.source_and_provenance_refs,
        requested_at=ready_time,
    )
    ready_outcome = harness.service.build_bundle(ready_request, ready)
    ready_ref = ready_outcome.receipt_refs[0]

    review_probe = _review_record(
        identity="AUTHORITY-PROBE",
        prior_ref=ready_ref,
        evidence_id=ready.evidence_id,
        candidate_version="BUNDLE::AUTHORITY-PROBE",
        input_lock_id=ready.input_lock_id,
        reviewed_at=_NOW + timedelta(seconds=11),
    )
    authority_probe = _review_authority(
        review_probe,
        context_ref=harness.context.context_id,
    )
    producer_probe = IndependentEvidenceReviewV1(
        harness.compiler,
        harness.persistence,
        _AgentOrchRowsV1(
            authority_probe,
            context_ref=harness.context.context_id,
        ),
    )
    _assert_reason(
        lambda: producer_probe.review_ready_bundle(
            review_probe,
            replace(
                authority_probe,
                current_agent_id="ComputationEvidenceServiceV1",
            ),
            principal_id=authority_probe.principal_id,
            context_ref=harness.context.context_id,
            component_or_template_ref="MATH-01",
            traceparent=_TRACEPARENT,
            tracestate="qtt=runtime",
        ),
        ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
        AuthorityDeniedError,
    )
    _assert_reason(
        lambda: replace(
            review_probe,
            reviewer_identity=review_probe.bundle_producer_identity,
        ),
        ReasonCode.ST12F_SELF_REVIEW_FORBIDDEN,
    )
    _assert_reason(
        lambda: harness.service.register_control(
            _control_request(
                harness,
                identity="REVIEW-INJECTION",
                requested_at=_NOW + timedelta(seconds=11),
            ),
            review_probe,
        ),
        ReasonCode.CONTRACT_OR_TYPE_INVALID,
    )

    closed_rows: list[
        tuple[
            ComputationEvidenceBundleV1,
            BuildEvidenceBundleRequestV1,
            IndependentReviewRecordV1,
            str,
            object,
        ]
    ] = []
    for index, suffix in enumerate(("A", "B")):
        closed_rows.append(
            _closed_candidate(
                custody,
                evidence_id=ready.evidence_id,
                version=f"BUNDLE::OWNER-RECERTIFIED::CLOSED::{suffix}",
                parent_ref=ready_ref,
                identity=f"OWNER-RECERTIFIED::CLOSED::{suffix}",
                reviewed_at=_NOW + timedelta(seconds=12 + index),
                model_time=_NOW + timedelta(seconds=15 + index),
                build_time=_NOW + timedelta(seconds=20),
            )
        )
    sibling_a = harness.service
    sibling_b = ComputationEvidenceServiceV1(
        harness.compiler,
        harness.persistence,
    )
    barrier = Barrier(2)
    _barrier_after_once(sibling_a, "_durable_current_bundle_ref", barrier)
    _barrier_after_once(sibling_b, "_durable_current_bundle_ref", barrier)
    results, errors = _threaded(
        lambda: sibling_a.build_bundle(
            closed_rows[0][1],
            closed_rows[0][0],
        ),
        lambda: sibling_b.build_bundle(
            closed_rows[1][1],
            closed_rows[1][0],
        ),
    )
    winner_indexes = tuple(
        index
        for index, row in enumerate(results)
        if type(row) is BuiltEvidenceBundleOutcomeV1
    )
    assert len(winner_indexes) == 1
    sibling_conflicts = tuple(row for row in errors if row is not None)
    assert len(sibling_conflicts) == 1
    assert type(sibling_conflicts[0]) is PersistenceContractError
    assert sibling_conflicts[0].reason_code is ReasonCode.PERSISTENCE_CONFLICT
    winner_index = winner_indexes[0]
    winner_outcome = results[winner_index]
    assert type(winner_outcome) is BuiltEvidenceBundleOutcomeV1
    winner = winner_outcome.evidence_bundle
    winner_request = closed_rows[winner_index][1]
    winner_review = closed_rows[winner_index][2]
    winner_model_ref = closed_rows[winner_index][3]
    winner_model = closed_rows[winner_index][4]
    winner_ref = winner_outcome.receipt_refs[0]
    winner_review_ref = (
        f"ST12F-RECEIPT::{winner_review.review_id}::INDEPENDENT_REVIEW_VERSION"
    )
    assert sibling_a.build_bundle(winner_request, winner) == winner_outcome

    transitions = harness.persistence.reconstruct_as_of(
        effective_cutoff=_NOW + timedelta(hours=1),
        recorded_cutoff=_NOW + timedelta(hours=1),
        aggregate_scope=(),
    )
    parent_aggregate = f"ST12F-BUNDLE-PARENT::{ready_ref}"
    child_edges = tuple(
        row
        for row in transitions
        if getattr(row, "aggregate_id", None) == parent_aggregate
    )
    assert len(child_edges) == 1
    same_identity_bundles = tuple(
        row
        for row in _control_rows(
            harness.persistence,
            cutoff=_NOW + timedelta(hours=1),
        )
        if row.typed_payload.receipt_class
        is ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
        and row.typed_payload.reconstruct(
            ComputationEvidenceBundleV1
        ).evidence_id == ready.evidence_id
        and row.typed_payload.reconstruct(
            ComputationEvidenceBundleV1
        ).input_lock_id == ready.input_lock_id
    )
    assert len(same_identity_bundles) == 2

    early = _NOW + timedelta(seconds=9)
    _assert_reason(
        lambda: harness.service.resolve_bundle(
            ready_ref,
            decision_cutoff=early,
        ),
        ReasonCode.OWNER_DATA_MISSING,
        PersistenceContractError,
    )
    _assert_reason(
        lambda: harness.service.resolve_review(
            winner_review_ref,
            decision_cutoff=early,
        ),
        ReasonCode.OWNER_DATA_MISSING,
        PersistenceContractError,
    )
    winner_d = winner.d_evidence_reference_projection
    assert type(winner_d) is ST12FEvidenceReferenceV1
    winner_d_ref = (
        f"ST12F-RECEIPT::{winner_d.reference_id}::D_EVIDENCE_REFERENCE"
    )
    context_at_early = replace(
        harness.context,
        as_of=early,
        observed_at=early,
    )
    unavailable = harness.service.read_evidence_reference(
        context_at_early,
        causation_id="CAUSE::BITEMPORAL",
        correlation_id="CORRELATION::BITEMPORAL",
        query=FToDEvidenceReferenceQueryV1(
            query_id="QUERY::BITEMPORAL",
            requested_evidence_id=winner.evidence_id,
            requested_component_or_template_ref="MATH-01",
            expected_input_lock_id=winner.input_lock_id,
            expected_source_epoch_refs=("SOURCE::1=EPOCH::1",),
            evaluated_at=early,
            request_read_lineage_refs=("READ::BITEMPORAL",),
        ),
    )
    assert (
        unavailable.evidence_state
        is ST12FEvidenceStateV1.EVIDENCE_INSUFFICIENT_FAIL_CLOSED
    )

    future_divergence = replace(
        custody.divergence,
        assessment_id="DIVERGENCE::FUTURE-EFFECTIVE",
    )
    future_request = _control_request(
        harness,
        identity="FUTURE-EFFECTIVE",
        requested_at=early,
    )
    lock = harness.compiler.resolve_input_lock(
        harness.compilation.input_lock_id,
        decision_cutoff=early,
    )
    future_spine = replace(
        harness.service._receipt(
            request=future_request,
            contract=future_divergence,
            input_lock=lock,
        ),
        effective_at=_NOW + timedelta(hours=1),
    )
    _insert_spines(harness.persistence, (future_spine,))
    _assert_reason(
            lambda: harness.service.resolve_control_receipt(
                future_spine.record_id,
                DivergenceAssessmentV1,
                decision_cutoff=early,
            ),
        ReasonCode.OWNER_DATA_MISSING,
        PersistenceContractError,
    )

    admission = harness.service._admit_bundle_evidence(
        request=ready_request,
        candidate=ready,
        lock=lock,
        replay=custody.replay,
        paper=custody.paper,
    )
    assert len(admission.component_versions) == 38
    all_dispositions = tuple(
        row
        for section_name in _SECTION_FIELDS
        for row in getattr(ready, section_name).identity_dispositions
    )
    assert len(all_dispositions) == 48
    assert sum(
        row.disposition
        is EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED
        for row in all_dispositions
    ) == 38
    assert sum(
        row.disposition
        is EvidenceIdentityDispositionStateV1.NOT_APPLICABLE_WITH_PROOF
        for row in all_dispositions
    ) == 10
    metric_ids = {
        f"MATH-{number:02d}"
        for number in (*range(8, 34), *range(37, 46))
    } | {
        "MATH-50",
        "MATH-51",
        "MATH-52",
    }
    assert not any(
        row.evidence_identity in metric_ids
        and row.disposition
        is EvidenceIdentityDispositionStateV1.NOT_APPLICABLE_WITH_PROOF
        for row in all_dispositions
    )


    binding_08 = next(
        row
        for row in ST12F_EVIDENCE_OUTPUT_BINDINGS_V1
        if row.math_spec_id == "MATH-08"
    )
    pass_ref = "ST12F-DURABLE::MUTATION::PASS"
    synthetic_ref = "ST12F-DURABLE::MUTATION::SYNTHETIC-ZERO"
    _insert_spines(
        harness.persistence,
        (
            _metric_spine(
                harness,
                binding=binding_08,
                record_ref=pass_ref,
                recorded_at=_NOW + timedelta(seconds=9),
                value_override="PASS",
            ),
            _metric_spine(
                harness,
                binding=binding_08,
                record_ref=synthetic_ref,
                recorded_at=_NOW + timedelta(seconds=9),
                value_override=0.0,
                failure_code="MISSING_DATA_SUBSTITUTED",
            ),
        ),
    )
    for mutation_id, ref, reason in (
        ("PASS", pass_ref, ReasonCode.ST12F_EVIDENCE_INCOMPLETE),
        (
            "FIXTURE",
            f"ST12F-RECEIPT::{custody.replay.result_id}::REPLAY_REGISTRATION",
            ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
        ),
        (
            "SYNTHETIC-ZERO",
            synthetic_ref,
            ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
        ),
    ):
        mutated = _replace_disposition_ref(
            ready,
            math_spec_id="MATH-08",
            new_ref=ref,
        )
        mutated_request = replace(
            ready_request,
            request_id=f"{ready_request.request_id}::MUTATION::{mutation_id}",
            idempotency_key=(
                f"{ready_request.idempotency_key}::MUTATION::{mutation_id}"
            ),
            evidence_record_refs=mutated.source_and_provenance_refs,
        )
        _assert_reason(
            lambda candidate=mutated, request=mutated_request: (
                harness.service._admit_bundle_evidence(
                    request=request,
                    candidate=candidate,
                    lock=lock,
                    replay=custody.replay,
                    paper=custody.paper,
                )
            ),
            reason,
        )

    missing_rows = list(all_dispositions)
    missing_index = next(
        index
        for index, row in enumerate(missing_rows)
        if row.evidence_identity == "MATH-08"
    )
    missing_ref = missing_rows[missing_index].evidence_record_refs[0]
    missing_rows[missing_index] = EvidenceIdentityDispositionV1(
        "MATH-08",
        EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON,
        (),
        (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),
        (),
    )
    missing_versions = dict(ready.actual_executed_component_versions)
    del missing_versions["MATH-08"]
    missing_provenance = tuple(
        ref for ref in ready.source_and_provenance_refs if ref != missing_ref
    )
    missing = replace(
        ready,
        actual_executed_component_versions=missing_versions,
        source_and_provenance_refs=missing_provenance,
        failure_and_negative_evidence_states=(
            "DISPOSITION::MATH-08::ST12F_EVIDENCE_INCOMPLETE",
            "NO_TRADE::INDEPENDENT_REVIEW_NOT_CLOSED",
        ),
        **_sections_from_rows(tuple(missing_rows)),
    )
    missing_request = replace(
        ready_request,
        request_id=f"{ready_request.request_id}::MISSING",
        idempotency_key=f"{ready_request.idempotency_key}::MISSING",
        evidence_record_refs=missing_provenance,
    )
    _assert_reason(
        lambda: harness.service._admit_bundle_evidence(
            request=missing_request,
            candidate=missing,
            lock=lock,
            replay=custody.replay,
            paper=custody.paper,
        ),
        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
    )

    for mutated in (
        replace(
            ready,
            actual_executed_component_versions={
                **dict(ready.actual_executed_component_versions),
                "MATH-08": "WRONG",
            },
        ),
        replace(
            ready,
            actual_executed_stack_versions={"STACK::WRONG": "1"},
        ),
        replace(
            ready,
            source_and_provenance_refs=(
                *ready.source_and_provenance_refs[:-1],
                "PROVENANCE::WRONG",
            ),
        ),
        replace(
            ready,
            failure_and_negative_evidence_states=("NEGATIVE::WRONG",),
        ),
    ):
        _assert_reason(
            lambda candidate=mutated: harness.service._admit_bundle_evidence(
                request=ready_request,
                candidate=candidate,
                lock=lock,
                replay=custody.replay,
                paper=custody.paper,
            ),
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
        )

    annotation_id = "ANNOTATION::OWNER-RECERTIFIED"
    annotation_ref = (
        f"ST12F-RECEIPT::{annotation_id}::LLM_ANNOTATION_VALIDATION"
    )
    citation = AnnotationCitationV1(
        "CITATION::OWNER-RECERTIFIED",
        winner_ref,
        ("CLAIM::OWNER-RECERTIFIED",),
    )
    claim = AnnotationClaimV1(
        "CLAIM::OWNER-RECERTIFIED",
        "The cited measured value is advisory evidence.",
        (citation.citation_id,),
        ("NUMERIC::OWNER-RECERTIFIED",),
    )
    fact = QuotedNumericFactV1(
        "NUMERIC::OWNER-RECERTIFIED",
        winner_ref,
        "probability|unitless",
        Decimal("0"),
        (claim.claim_id,),
    )
    numeric = CanonicalNumericEvidenceValueV1(
        numeric_fact_id=fact.numeric_fact_id,
        evidence_ref=winner_ref,
        evidence_bundle_ref=winner_ref,
        value=fact.quoted_value,
        unit_and_basis=fact.unit_and_basis,
        evidence_receipt_ref=winner_d_ref,
        numeric_recheck_receipt_ref=annotation_ref,
        input_lock_id=winner.input_lock_id,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        observed_at=winner_d.observed_at,
        valid_until=winner_d.valid_until,
    )
    annotation = DeterministicEvidenceAnnotationContractV1(
        annotation_id=annotation_id,
        schema_version="QTT_ST12F_DETERMINISTIC_EVIDENCE_ANNOTATION_V1_4",
        contract_version="1.4",
        evidence_bundle_refs=(winner_ref,),
        redacted_context_refs=("REDACTED::OWNER-RECERTIFIED",),
        untrusted_content_isolated=True,
        advisory_task=LLMAdvisoryTaskV1.SUMMARIZE_EVIDENCE,
        citations=(citation,),
        claims=(claim,),
        limitations=("LIMITATION::ADVISORY",),
        abstentions=(),
        quoted_numeric_facts=(fact,),
        canonical_numeric_evidence=(numeric,),
        deterministic_numeric_recheck_receipt_refs=(annotation_ref,),
        upstream_budget_metadata={
            "budget_source_ref": "BUDGET::OWNER-RECERTIFIED",
            "supplied_upstream": True,
            "token_budget": 64,
        },
        input_lock_id=winner.input_lock_id,
        source_epoch_refs=numeric.source_epoch_refs,
        observed_at=numeric.observed_at,
        valid_until=numeric.valid_until,
        numeric_recheck_passed=True,
    )
    _register_control(
        harness,
        annotation,
        identity="OWNER-RECERTIFIED::ANNOTATION",
        requested_at=_NOW + timedelta(seconds=25),
    )
    assert harness.service.resolve_numeric_evidence(
        numeric_fact_id=fact.numeric_fact_id,
        evidence_ref=winner_ref,
        evaluated_at=_NOW + timedelta(seconds=26),
    ) == numeric

    visible_reference = harness.service.read_evidence_reference(
        replace(
            harness.context,
            as_of=_NOW + timedelta(seconds=26),
            observed_at=_NOW + timedelta(seconds=26),
        ),
        causation_id="CAUSE::VISIBLE-D",
        correlation_id="CORRELATION::VISIBLE-D",
        query=FToDEvidenceReferenceQueryV1(
            query_id="QUERY::VISIBLE-D",
            requested_evidence_id=winner.evidence_id,
            requested_component_or_template_ref="MATH-01",
            expected_input_lock_id=winner.input_lock_id,
            expected_source_epoch_refs=("SOURCE::1=EPOCH::1",),
            evaluated_at=_NOW + timedelta(seconds=26),
            request_read_lineage_refs=("READ::VISIBLE-D",),
        ),
    )
    assert visible_reference == winner_d

    cache_service = ComputationEvidenceServiceV1(
        harness.compiler,
        harness.persistence,
    )
    old_snapshot = cache_service._cache_snapshot
    original_spines = cache_service._durable_receipt_spines

    def failed_refresh(**_kwargs: object) -> tuple[object, ...]:
        raise PersistenceContractError(
            ReasonCode.PERSISTENCE_UNAVAILABLE,
            "injected cache refresh failure",
        )

    cache_service._durable_receipt_spines = failed_refresh
    _assert_reason(
        lambda: cache_service._rebuild_caches_from_durable_receipts(
            effective_cutoff=_NOW + timedelta(seconds=30),
            recorded_cutoff=_NOW + timedelta(seconds=30),
        ),
        ReasonCode.PERSISTENCE_UNAVAILABLE,
        PersistenceContractError,
    )
    assert cache_service._cache_snapshot is old_snapshot
    cache_service._durable_receipt_spines = original_spines
    cache_barrier = Barrier(2)
    seen_snapshots: list[EvidenceCacheSnapshotV1] = []

    def read_snapshots() -> None:
        cache_barrier.wait(timeout=10)
        for _ in range(1000):
            seen_snapshots.append(cache_service._cache_snapshot)

    def publish_snapshot() -> EvidenceCacheSnapshotV1:
        cache_barrier.wait(timeout=10)
        return cache_service._rebuild_caches_from_durable_receipts(
            effective_cutoff=_NOW + timedelta(seconds=30),
            recorded_cutoff=_NOW + timedelta(seconds=30),
        )

    cache_results, cache_errors = _threaded(
        read_snapshots,
        publish_snapshot,
    )
    assert cache_errors == (None, None)
    new_snapshot = cache_results[1]
    assert type(new_snapshot) is EvidenceCacheSnapshotV1
    assert all(
        row is old_snapshot or row is new_snapshot for row in seen_snapshots
    )
    assert new_snapshot.generation == old_snapshot.generation + 1

    stale_candidate = replace(
        winner,
        evidence_bundle_version="BUNDLE::OWNER-RECERTIFIED::STALE",
        independent_review_state=EvidenceBundleTerminalStateV1.STALE.value,
        failure_and_negative_evidence_states=(
            "LIFECYCLE::ST12F_BUNDLE_STALE",
        ),
        d_evidence_reference_projection="UNAVAILABLE",
        g_handoff_projection="UNAVAILABLE",
        terminal_state=EvidenceBundleTerminalStateV1.STALE,
        blocker_codes=(ReasonCode.ST12F_BUNDLE_STALE,),
    )
    stable_time = _NOW + timedelta(seconds=30)
    stable_request = _bundle_request(
        harness,
        identity="STALE::BASELINE",
        source_refs=stale_candidate.source_and_provenance_refs,
        requested_at=stable_time,
    )
    for suffix in ("TTL", "SOURCE", "PARAMETER", "IMPLEMENTATION", "CONTEXT"):
        _assert_reason(
            lambda suffix=suffix: harness.service._validate_bundle_transition_guard(
                request=replace(
                    stable_request,
                    request_id=f"{stable_request.request_id}::{suffix}",
                    idempotency_key=f"{stable_request.idempotency_key}::{suffix}",
                ),
                previous_ref=winner_ref,
                previous=winner,
                candidate=replace(
                    stale_candidate,
                    evidence_bundle_version=f"{stale_candidate.evidence_bundle_version}::{suffix}",
                ),
                lock=lock,
            ),
            ReasonCode.ST12F_BUNDLE_STALE,
        )

    stale_positive_inputs = (
        (
            "TTL",
            harness.snapshot,
            winner_d.valid_until + timedelta(seconds=1),
        ),
        (
            "SOURCE",
            replace(
                harness.snapshot,
                source_epochs={"SOURCE::1": "EPOCH::2"},
            ),
            stable_time,
        ),
        (
            "PARAMETER",
            replace(
                harness.snapshot,
                parameter_policy_version="ST12F_PARAMETER_POLICY::CHANGED",
            ),
            stable_time,
        ),
        (
            "IMPLEMENTATION",
            replace(
                harness.snapshot,
                implementation_versions={
                    **dict(harness.snapshot.implementation_versions),
                    "MATH-08": "VERSION::MATH-08::CHANGED",
                },
            ),
            stable_time,
        ),
        (
            "CONTEXT",
            replace(
                harness.snapshot,
                scenario_set_id="SCENARIO::CHANGED",
            ),
            stable_time,
        ),
    )
    for suffix, snapshot, requested_at in stale_positive_inputs:
        stale_compiler = ReplayPaperCohortCompilerV1(
            snapshot,
            harness.persistence,
        )
        stale_service = ComputationEvidenceServiceV1(
            stale_compiler,
            harness.persistence,
        )
        stale_service._validate_bundle_transition_guard(
            request=replace(
                stable_request,
                request_id=f"{stable_request.request_id}::POSITIVE::{suffix}",
                idempotency_key=(
                    f"{stable_request.idempotency_key}::POSITIVE::{suffix}"
                ),
                requested_at=requested_at,
            ),
            previous_ref=winner_ref,
            previous=winner,
            candidate=replace(
                stale_candidate,
                evidence_bundle_version=(
                    f"{stale_candidate.evidence_bundle_version}::POSITIVE::{suffix}"
                ),
            ),
            lock=lock,
        )

    newer_harness = _runtime_harness(
        harness.persistence,
        identity="OWNER-RECERTIFIED-NEWER-LOCK",
    )
    newer_custody = _prepare_complete_custody(
        newer_harness,
        identity="OWNER-RECERTIFIED-NEWER",
        time_offset=50,
    )
    newer_ready_model = _runtime_model_risk(
        newer_custody.replay,
        newer_custody.paper,
        assessment_id="MODEL-RISK::NEWER::READY",
        evaluated_at=_NOW + timedelta(seconds=56),
    )
    newer_ready_model_ref = _register_control(
        newer_harness,
        newer_ready_model,
        identity="NEWER::READY::MODEL-RISK",
        requested_at=_NOW + timedelta(seconds=56),
    )
    newer_ready = _complete_candidate(
        newer_custody,
        evidence_id=winner.evidence_id,
        version="BUNDLE::OWNER-RECERTIFIED::NEWER::READY",
        state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        model_risk=newer_ready_model,
        model_risk_ref=newer_ready_model_ref,
    )
    newer_ready_request = _bundle_request(
        newer_harness,
        identity="NEWER::READY",
        source_refs=newer_ready.source_and_provenance_refs,
        requested_at=_NOW + timedelta(seconds=60),
    )
    newer_ready_outcome = newer_harness.service.build_bundle(
        newer_ready_request,
        newer_ready,
    )
    newer_closed, newer_closed_request, newer_review, _, _ = (
        _closed_candidate(
            newer_custody,
            evidence_id=winner.evidence_id,
            version="BUNDLE::OWNER-RECERTIFIED::NEWER::CLOSED",
            parent_ref=newer_ready_outcome.receipt_refs[0],
            identity="OWNER-RECERTIFIED::NEWER::CLOSED",
            reviewed_at=_NOW + timedelta(seconds=62),
            model_time=_NOW + timedelta(seconds=64),
            build_time=_NOW + timedelta(seconds=70),
        )
    )
    newer_closed_outcome = newer_harness.service.build_bundle(
        newer_closed_request,
        newer_closed,
    )
    newer_bundle_ref = newer_closed_outcome.receipt_refs[0]
    newer_d = newer_closed.d_evidence_reference_projection
    assert type(newer_d) is ST12FEvidenceReferenceV1
    newer_d_ref = (
        f"ST12F-RECEIPT::{newer_d.reference_id}::D_EVIDENCE_REFERENCE"
    )
    newer_review_ref = (
        f"ST12F-RECEIPT::{newer_review.review_id}::INDEPENDENT_REVIEW_VERSION"
    )
    supersession_proofs = (
        newer_bundle_ref,
        newer_d_ref,
    )
    superseded = _complete_candidate(
        custody,
        evidence_id=winner.evidence_id,
        version="BUNDLE::OWNER-RECERTIFIED::SUPERSEDED",
        state=EvidenceBundleTerminalStateV1.SUPERSEDED,
        model_risk=winner_model,
        model_risk_ref=winner_model_ref,
        review_ref=newer_review_ref,
        proof_refs=supersession_proofs,
    )
    superseded_request = _bundle_request(
        harness,
        identity="OWNER-RECERTIFIED::SUPERSEDED",
        source_refs=superseded.source_and_provenance_refs,
        requested_at=_NOW + timedelta(seconds=80),
    )
    for omitted in (
        newer_bundle_ref,
        newer_d_ref,
        newer_review_ref,
    ):
        _assert_reason(
            lambda omitted=omitted: harness.service._validate_bundle_transition_guard(
                request=replace(
                    superseded_request,
                    request_id=f"{superseded_request.request_id}::WITHOUT::{omitted}",
                    idempotency_key=(
                        f"{superseded_request.idempotency_key}::WITHOUT::{omitted}"
                    ),
                    evidence_record_refs=tuple(
                        ref
                        for ref in superseded_request.evidence_record_refs
                        if ref != omitted
                    ),
                ),
                previous_ref=winner_ref,
                previous=winner,
                candidate=superseded,
                lock=lock,
            ),
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
        )
    superseded_outcome = harness.service.build_bundle(
        superseded_request,
        superseded,
    )
    assert (
        superseded_outcome.evidence_bundle.terminal_state
        is EvidenceBundleTerminalStateV1.SUPERSEDED
    )

    receipt_classes = {
        row.typed_payload.receipt_class
        for row in _control_rows(
            harness.persistence,
            cutoff=_NOW + timedelta(hours=5),
        )
    }
    assert len(receipt_classes) == 12
    assert receipt_classes == set(ST12FReceiptClassV1)
    assert observed == set(_CONCURRENCY_CASE_IDS_V1_7[1:2]) | set(
        _CONCURRENCY_CASE_IDS_V1_7[4:]
    )
