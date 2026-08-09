"""Compact ST12-F REPLAY/PAPER/evidence semantic matrix."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
    POLICY_VERSION,
)

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    PersistenceContractError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    ComputationEvidenceBundleV1,
    ComputationEvidenceServiceV1,
    DivergenceAssessmentV1,
    DivergenceTerminalStateV1,
    EvidenceBundleTerminalStateV1,
    EvidenceIdentityDispositionStateV1,
    EvidenceIdentityDispositionV1,
    EvidenceSectionV1,
    FToDEvidenceReferenceQueryV1,
    FToGHandoffReferencesV1,
    IndependentReviewDecisionV1,
    IndependentReviewRecordV1,
    PaperResultContractV1,
    ReplayResultContractV1,
    ST12F_EVIDENCE_IDENTITIES_V1,
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
    QuantumEconomicBasisV1,
    QuantumTraceValidationReceiptV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    EconomicReceiptEventSpineV1,
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
    replay = harness.service.register_result(
        _register_request(harness, "REPLAY", f"REPLAY{suffix}"),
        _runtime_packet(
            harness,
            "REPLAY",
            result_id=f"RESULT::REPLAY{suffix}",
            run_reference=f"RUN::REPLAY{suffix}",
            component=component,
        ),
    )
    paper = harness.service.register_result(
        _register_request(harness, "PAPER", f"PAPER{suffix}"),
        _runtime_packet(
            harness,
            "PAPER",
            result_id=f"RESULT::PAPER{suffix}",
            run_reference=f"RUN::PAPER{suffix}",
            component=component,
        ),
    )
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
    identity: str = "RUNTIME",
) -> object:
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
            False,
            (f"RECEIPT::{condition_id}",),
            (),
        )
        for condition_id in NO_TRADE_CONDITION_IDS_V1
    )
    expiry = _NOW + timedelta(hours=1)
    basis = ModelRiskAdjudicationBasisV1(
        expected_component_or_template_ref=replay.cohort_template_id,
        evaluated_at=_NOW,
        required_evidence_valid_until=expiry,
        required_evidence_receipt_refs=("RECEIPT::REQUIRED-EVIDENCE",),
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
        independent_review_state="READY_FOR_INDEPENDENT_REVIEW",
        independent_review_receipt_ref="RECEIPT::REVIEW-PENDING",
    )
    comparison = PermanentNoTradeEvidenceComparisonV1(
        comparison_id=f"NO-TRADE-COMPARISON::{identity}",
        input_lock_id=replay.input_lock_id,
        execution_adjusted_lcb=Decimal("0.1"),
        candidate_utility=Decimal("1"),
        strongest_classical_utility=Decimal("0.8"),
        no_trade_utility=Decimal("0"),
        strongest_comparator="CANDIDATE",
    )
    return ModelRiskEvidenceAdjudicatorV1().adjudicate(
        assessment_id=f"MODEL-RISK::{identity}",
        input_lock_id=replay.input_lock_id,
        controls=controls,
        conditions=conditions,
        comparison=comparison,
        adjudication_basis=basis,
        limitations=("LIMITATION::RUNTIME",),
        receipt_refs=("RECEIPT::MODEL-RISK-UPSTREAM",),
    )


def _runtime_quantum(input_lock_id: str) -> QuantumTraceValidationReceiptV1:
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
        version_epoch_pins=("SOURCE::1=EPOCH::1", "VERSION::RUNTIME"),
    )
    return QuantumTraceValidationReceiptV1(
        receipt_id="QUANTUM-TRACE::RUNTIME",
        schema_version="QTT_ST12F_QUANTUM_TRACE_VALIDATION_V1_4",
        contract_version="1.4",
        math_spec_id="MATH-50",
        trace_id="TRACE::RUNTIME",
        input_lock_id=input_lock_id,
        formulation_id="MATH-01",
        comparison_basis=basis,
        selected_candidate_id="CANDIDATE::RUNTIME",
        recomputed_objective=Decimal("1"),
        recomputed_variance_or_explicit_absence="EXPLICIT_ABSENCE",
        selected_original_model_feasible=True,
        selected_hard_veto=False,
        original_model_interpret_back_valid=True,
        strongest_classical_receipt_ref="RECEIPT::CLASSICAL",
        no_trade_receipt_ref="RECEIPT::NO-TRADE",
        original_economic_utility=Decimal("1"),
        resource_use=Decimal("1"),
        latency=Decimal("1"),
        deterministic_tie_break="CANDIDATE::RUNTIME",
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


def _runtime_llm(input_lock_id: str) -> DeterministicEvidenceAnnotationContractV1:
    citation = AnnotationCitationV1(
        "CITATION::RUNTIME", "UPSTREAM-BUNDLE::RUNTIME", ("CLAIM::RUNTIME",)
    )
    claim = AnnotationClaimV1(
        "CLAIM::RUNTIME",
        "The supplied evidence remains advisory.",
        (citation.citation_id,),
        ("NUMERIC::RUNTIME",),
    )
    fact = QuotedNumericFactV1(
        "NUMERIC::RUNTIME",
        citation.evidence_ref,
        "probability|unitless",
        Decimal("0.5"),
        (claim.claim_id,),
    )
    numeric = CanonicalNumericEvidenceValueV1(
        numeric_fact_id=fact.numeric_fact_id,
        evidence_ref=fact.evidence_ref,
        evidence_bundle_ref=fact.evidence_ref,
        value=fact.quoted_value,
        unit_and_basis=fact.unit_and_basis,
        evidence_receipt_ref="ST12F-RECEIPT::NUMERIC-EVIDENCE::D_EVIDENCE_REFERENCE",
        numeric_recheck_receipt_ref="ST12F-RECEIPT::NUMERIC-RECHECK::LLM_ANNOTATION_VALIDATION",
        input_lock_id=input_lock_id,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        observed_at=_NOW - timedelta(minutes=1),
        valid_until=_NOW + timedelta(hours=1),
    )
    return DeterministicEvidenceAnnotationContractV1(
        annotation_id="ANNOTATION::RUNTIME",
        schema_version="QTT_ST12F_DETERMINISTIC_EVIDENCE_ANNOTATION_V1_4",
        contract_version="1.4",
        evidence_bundle_refs=(citation.evidence_ref,),
        redacted_context_refs=("REDACTED::RUNTIME",),
        untrusted_content_isolated=True,
        advisory_task=LLMAdvisoryTaskV1.SUMMARIZE_EVIDENCE,
        citations=(citation,),
        claims=(claim,),
        limitations=("LIMITATION::ADVISORY",),
        abstentions=(),
        quoted_numeric_facts=(fact,),
        canonical_numeric_evidence=(numeric,),
        deterministic_numeric_recheck_receipt_refs=(
            numeric.numeric_recheck_receipt_ref,
        ),
        upstream_budget_metadata={
            "budget_source_ref": "BUDGET::RUNTIME",
            "supplied_upstream": True,
            "token_budget": 64,
        },
        input_lock_id=input_lock_id,
        source_epoch_refs=numeric.source_epoch_refs,
        observed_at=numeric.observed_at,
        valid_until=numeric.valid_until,
        numeric_recheck_passed=True,
    )


def _bundle_candidate(
    *,
    evidence_id: str,
    version: str,
    input_lock_id: str,
    state: EvidenceBundleTerminalStateV1,
    source_refs: tuple[str, ...],
    replay: ReplayResultContractV1 | None,
    paper: PaperResultContractV1 | None,
    divergence_ref: str,
    component: str = "MATH-01",
    blockers: tuple[ReasonCode, ...] = (),
    d_reference: ST12FEvidenceReferenceV1 | str = "UNAVAILABLE",
    g_handoff: FToGHandoffReferencesV1 | str = "UNAVAILABLE",
) -> ComputationEvidenceBundleV1:
    present = tuple(row for row in (replay, paper) if row is not None)
    lane_receipts = tuple(
        f"ST12F-RECEIPT::{row.result_id}::{('REPLAY' if type(row) is ReplayResultContractV1 else 'PAPER')}_REGISTRATION"
        for row in present
    )
    return ComputationEvidenceBundleV1(
        evidence_id=evidence_id,
        schema_version="QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4",
        contract_version="1.4",
        evidence_bundle_version=version,
        component_or_template_ref=component,
        input_lock_id=input_lock_id,
        actual_executed_component_versions={component: f"VERSION::{component}"},
        actual_executed_stack_versions={"STACK::RUNTIME": "VERSION::1"},
        replay_result_ref="EXPLICIT_ABSENCE" if replay is None else replay.result_id,
        paper_result_ref="EXPLICIT_ABSENCE" if paper is None else paper.result_id,
        divergence_assessment_ref=divergence_ref,
        lane_execution_receipt_refs=lane_receipts,
        **_sections(),
        independent_review_state=state.value,
        failure_and_negative_evidence_states=(state.value,) if blockers else (),
        source_and_provenance_refs=source_refs,
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
    component: str = "MATH-01",
    input_lock_id: str | None = None,
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
        component_id=component,
        input_lock_id=(
            harness.compilation.input_lock_id
            if input_lock_id is None
            else input_lock_id
        ),
        evidence_record_refs=source_refs,
        required_lanes=("REPLAY", "PAPER"),
    )


def _review_record(
    *,
    review_id: str,
    prior_ref: str,
    evidence_id: str,
    candidate_version: str,
    input_lock_id: str,
    decision: IndependentReviewDecisionV1,
    reviewed_at: datetime,
    valid_until: datetime | None = None,
) -> IndependentReviewRecordV1:
    blockers = () if decision is IndependentReviewDecisionV1.VALIDATED else (
        ReasonCode.ST12F_MODEL_RISK_VETO,
    )
    return IndependentReviewRecordV1(
        review_id=review_id,
        schema_version="QTT_ST12F_INDEPENDENT_REVIEW_RECORD_V1_4",
        contract_version="1.4",
        prior_bundle_ref=prior_ref,
        evidence_id=evidence_id,
        evidence_bundle_version=candidate_version,
        input_lock_id=input_lock_id,
        reviewer_identity="REVIEWER::INDEPENDENT",
        bundle_producer_identity="ComputationEvidenceServiceV1",
        authority_receipt_ref=f"AUTHORITY::{review_id}",
        reviewed_source_epoch_refs=("SOURCE::1=EPOCH::1",),
        decision=decision,
        blocker_codes=blockers,
        reviewed_at=reviewed_at,
        valid_until=(
            reviewed_at + timedelta(hours=1)
            if valid_until is None
            else valid_until
        ),
    )


def _closed_projections(
    *,
    identity: str,
    evidence_id: str,
    version: str,
    input_lock_id: str,
    component: str,
    observed_at: datetime,
    valid_until: datetime,
    model_receipt_ref: str,
) -> tuple[ST12FEvidenceReferenceV1, FToGHandoffReferencesV1, str]:
    bundle_ref = f"ST12F-RECEIPT::{version}::EVIDENCE_BUNDLE_VERSION"
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
        component_or_template_ref=component,
        evidence_bundle_version=version,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
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
        source_epoch_refs=reference.source_epoch_refs,
        observed_at=observed_at,
        valid_until=valid_until,
        terminal_state=reference.terminal_state,
        evidence_bundle_ref=bundle_ref,
        no_trade_blocker_refs=(),
        champion_challenger_evidence_refs=(model_receipt_ref,),
        portfolio_utility_refs=(f"RECEIPT::PORTFOLIO-UTILITY::{identity}",),
        quantum_classical_comparison_receipt_ref=(
            f"RECEIPT::QUANTUM-COMPARISON::{identity}"
        ),
    )
    return reference, handoff, bundle_ref


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


class _BundleCandidateResolverV1:
    def __init__(self, candidate: ComputationEvidenceBundleV1) -> None:
        self.candidate = candidate

    def resolve_bundle_candidate(
        self, _request: BuildEvidenceBundleRequestV1
    ) -> ComputationEvidenceBundleV1:
        return self.candidate

    @staticmethod
    def resolve_control_contracts(
        _request: BuildEvidenceBundleRequestV1,
    ) -> tuple[object, ...]:
        return ()


def _assert_public_op13_op14_op15_receipt_ids() -> None:
    snapshot = _runtime_snapshot()
    adapter = InMemoryPersistenceAdapterV1()
    compiler = ReplayPaperCohortCompilerV1(snapshot, adapter)
    context = ComputationContextKeyV1(
        context_id="MATH-01",
        as_of=_NOW,
        observed_at=_NOW,
        source_epoch_id="SOURCE::1=EPOCH::1",
        input_version="INPUT::PUBLIC-RECEIPTS",
        maximum_age=timedelta(hours=1),
    )
    evidence_service = ComputationEvidenceServiceV1(compiler, adapter)
    facade = QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=_NoEffectAdmissionV1(),
        persistence_adapter=adapter,
        replay_paper_cohort_compiler=compiler,
        computation_evidence_service=evidence_service,
    )
    compile_request = _compile_request(
        identity="PUBLIC-RECEIPTS", context=context
    )
    op13 = facade.compile_replay_paper_cohort(compile_request)
    compilation = compiler.resolve_compilation(
        "ST12F-COMPILATION::PUBLIC-RECEIPTS"
    )
    assert op13.receipt_refs == op13.cohort_compilation.evidence_refs
    assert len(op13.receipt_refs) == 2
    assert all(adapter.get_record(ref) is not None for ref in op13.receipt_refs)

    harness = _RuntimeHarnessV1(
        snapshot=snapshot,
        persistence=adapter,
        compiler=compiler,
        service=evidence_service,
        compilation=compilation,
        context=context,
    )
    replay = _runtime_packet(harness, "REPLAY", result_id="RESULT::PUBLIC")
    register_request = replace(
        _register_request(harness, "REPLAY", "PUBLIC-RECEIPTS"),
        result_packet=_typed_lane_packet_record(replay),
    )
    op14 = facade.register_replay_paper_result(register_request)
    assert op14.receipt_refs == op14.registration.evidence_refs
    assert op14.receipt_refs == (
        "ST12F-RECEIPT::RESULT::PUBLIC::REPLAY_REGISTRATION",
    )
    assert all(adapter.get_record(ref) is not None for ref in op14.receipt_refs)

    source_refs = ("UPSTREAM::PUBLIC-RECEIPTS",)
    candidate = _bundle_candidate(
        evidence_id="EVIDENCE::PUBLIC-RECEIPTS",
        version="BUNDLE::PUBLIC-RECEIPTS::1",
        input_lock_id=replay.input_lock_id,
        state=EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        source_refs=source_refs,
        replay=replay,
        paper=None,
        divergence_ref="EXPLICIT_ABSENCE",
        blockers=(ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),
    )
    op15_service = ComputationEvidenceServiceV1(
        compiler,
        adapter,
        bundle_candidate_resolver=_BundleCandidateResolverV1(candidate),
    )
    op15_facade = QKUComputationControlPlaneV1(
        CanonicalOwnerPacketRegistryV1(),
        agent_capability_resolver=_NoEffectAdmissionV1(),
        persistence_adapter=adapter,
        replay_paper_cohort_compiler=compiler,
        computation_evidence_service=op15_service,
    )
    op15 = op15_facade.build_evidence_bundle(
        _bundle_request(
            harness,
            identity="PUBLIC-RECEIPTS",
            source_refs=source_refs,
            requested_at=_NOW + timedelta(seconds=10),
        )
    )
    assert op15.receipt_refs == op15.evidence_bundle.evidence_refs
    assert op15.receipt_refs == (
        "ST12F-RECEIPT::BUNDLE::PUBLIC-RECEIPTS::1::EVIDENCE_BUNDLE_VERSION",
    )
    assert all(adapter.get_record(ref) is not None for ref in op15.receipt_refs)


def test_op14_atomic_restart_conflict_and_fixture_non_poisoning() -> None:
    failing_adapter = _CommitFailingAdapterV1()
    failing = _runtime_harness(failing_adapter, identity="ATOMIC")
    failing_adapter.fail_next_commit = True
    before = {
        name: dict(index)
        for name, index in failing.service.immutable_indexes.items()
    }
    try:
        failing.service.register_result(
            _register_request(failing, "REPLAY", "ATOMIC"),
            _runtime_packet(failing, "REPLAY"),
        )
    except PersistenceContractError as exc:
        assert exc.reason_code is ReasonCode.PERSISTENCE_UNAVAILABLE
    else:
        raise AssertionError("injected commit failure did not roll back")
    after = {
        name: dict(index)
        for name, index in failing.service.immutable_indexes.items()
    }
    assert after == before
    assert (
        failing.persistence.get_record(
            "ST12F-RECEIPT::RESULT::REPLAY::REPLAY_REGISTRATION"
        )
        is None
    )

    fixture_harness = _runtime_harness(identity="FIXTURE")
    fixture = _runtime_packet(fixture_harness, "REPLAY", fixture=True)
    fixture_harness.service.register_result(
        _register_request(fixture_harness, "REPLAY", "FIXTURE"), fixture
    )
    assert not fixture_harness.service.immutable_indexes["lane_results"]
    assert not fixture_harness.service.immutable_indexes["slot_results"]
    assert fixture_harness.service.last_committed_receipt_refs == ()
    real = _runtime_packet(fixture_harness, "REPLAY")
    fixture_harness.service.register_result(
        _register_request(fixture_harness, "REPLAY", "REAL-AFTER-FIXTURE"),
        real,
    )
    assert len(fixture_harness.service.immutable_indexes["slot_results"]) == 1

    restart_harness = _runtime_harness(identity="RESTART")
    committed = restart_harness.service.register_result(
        _register_request(restart_harness, "REPLAY", "FIRST"),
        _runtime_packet(restart_harness, "REPLAY"),
    )
    fresh_compiler = ReplayPaperCohortCompilerV1(
        restart_harness.snapshot, restart_harness.persistence
    )
    restarted = ComputationEvidenceServiceV1(
        fresh_compiler, restart_harness.persistence
    )
    replayed = restarted.register_result(
        _register_request(restart_harness, "REPLAY", "SAME-PAYLOAD-NEW-KEY"),
        committed,
    )
    assert replayed == committed
    assert len(restarted.immutable_indexes["slot_results"]) == 1
    competing = _runtime_packet(
        restart_harness,
        "REPLAY",
        result_id="RESULT::REPLAY::COMPETING",
        run_reference="RUN::REPLAY::COMPETING",
    )
    try:
        restarted.register_result(
            _register_request(restart_harness, "REPLAY", "COMPETING"),
            competing,
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_RESULT_SLOT_CONFLICT
    else:
        raise AssertionError("restart natural-slot conflict was accepted")
    _assert_public_op13_op14_op15_receipt_ids()


def test_complete_durable_bundle_lifecycle_receipts_and_d_resolution() -> None:
    harness = _runtime_harness(identity="LIFECYCLE")
    replay, paper = _register_dual_lanes(harness)
    divergence = _runtime_divergence(replay, paper)
    conflicting_divergence = _runtime_conflicting_divergence(replay, paper)
    model_risk = _runtime_model_risk(replay, paper)
    quantum = _runtime_quantum(replay.input_lock_id)
    annotation = _runtime_llm(replay.input_lock_id)
    initial_sources = ("UPSTREAM::RUNTIME",)
    ready = _bundle_candidate(
        evidence_id="EVIDENCE::READY-BASE",
        version="BUNDLE::READY-BASE::1",
        input_lock_id=replay.input_lock_id,
        state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        source_refs=initial_sources,
        replay=replay,
        paper=paper,
        divergence_ref=divergence.assessment_id,
    )
    ready_request = _bundle_request(
        harness,
        identity="READY-BASE",
        source_refs=initial_sources,
        requested_at=_NOW + timedelta(seconds=10),
    )
    persisted_ready = harness.service.build_bundle(
        ready_request,
        ready,
        control_contracts=(divergence, model_risk, quantum, annotation),
    )
    assert persisted_ready.terminal_state is EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
    assert len(harness.service.last_committed_receipt_refs) == 5

    divergence_receipt = (
        f"ST12F-RECEIPT::{divergence.assessment_id}::DIVERGENCE_ASSESSMENT"
    )
    model_receipt = (
        f"ST12F-RECEIPT::{model_risk.assessment_id}::MODEL_RISK_ASSESSMENT"
    )
    durable_sources = (divergence_receipt, model_receipt)

    incomplete_cases = (
        (
            "MISSING-REPLAY",
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            None,
            paper,
        ),
        (
            "MISSING-PAPER",
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
            replay,
            None,
        ),
        (
            "CONFLICT",
            EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT,
            replay,
            paper,
        ),
    )
    observed_states = {persisted_ready.terminal_state}
    incomplete_values: dict[
        EvidenceBundleTerminalStateV1, ComputationEvidenceBundleV1
    ] = {}
    for offset, (identity, state, replay_row, paper_row) in enumerate(
        incomplete_cases, start=11
    ):
        source_refs = (f"UPSTREAM::{identity}",)
        candidate = _bundle_candidate(
            evidence_id=f"EVIDENCE::{identity}",
            version=f"BUNDLE::{identity}::1",
            input_lock_id=replay.input_lock_id,
            state=state,
            source_refs=source_refs,
            replay=replay_row,
            paper=paper_row,
            divergence_ref=(
                "EXPLICIT_ABSENCE"
                if replay_row is None or paper_row is None
                else conflicting_divergence.assessment_id
            ),
            blockers=(ReasonCode.ST12F_EVIDENCE_INCOMPLETE,),
        )
        value = harness.service.build_bundle(
            _bundle_request(
                harness,
                identity=identity,
                source_refs=source_refs,
                requested_at=_NOW + timedelta(seconds=offset),
            ),
            candidate,
            control_contracts=(
                (conflicting_divergence,)
                if state is EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT
                else ()
            ),
        )
        incomplete_values[state] = value
        observed_states.add(value.terminal_state)

    missing_to_ready_values: list[ComputationEvidenceBundleV1] = []
    for offset, missing_state in enumerate(
        (
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        ),
        start=16,
    ):
        prior = incomplete_values[missing_state]
        transitioned = _bundle_candidate(
            evidence_id=prior.evidence_id,
            version=f"{prior.evidence_bundle_version}::READY",
            input_lock_id=replay.input_lock_id,
            state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            source_refs=durable_sources,
            replay=replay,
            paper=paper,
            divergence_ref=divergence.assessment_id,
        )
        missing_to_ready_values.append(
            harness.service.build_bundle(
                _bundle_request(
                    harness,
                    identity=f"{missing_state.value}-TO-READY",
                    source_refs=durable_sources,
                    requested_at=_NOW + timedelta(seconds=offset),
                ),
                transitioned,
            )
        )
    assert all(
        value.terminal_state
        is EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
        for value in missing_to_ready_values
    )

    missing_divergence_sources = ("UPSTREAM::MISSING-DIVERGENCE",)
    try:
        harness.service.build_bundle(
            _bundle_request(
                harness,
                identity="MISSING-DIVERGENCE",
                source_refs=missing_divergence_sources,
                requested_at=_NOW + timedelta(seconds=19),
            ),
            _bundle_candidate(
                evidence_id="EVIDENCE::MISSING-DIVERGENCE",
                version="BUNDLE::MISSING-DIVERGENCE::1",
                input_lock_id=replay.input_lock_id,
                state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
                source_refs=missing_divergence_sources,
                replay=replay,
                paper=paper,
                divergence_ref="EXPLICIT_ABSENCE",
            ),
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
    else:
        raise AssertionError("dual-lane bundle without divergence proof was accepted")

    def new_ready(identity: str, second: int) -> ComputationEvidenceBundleV1:
        candidate = _bundle_candidate(
            evidence_id=f"EVIDENCE::{identity}",
            version=f"BUNDLE::{identity}::1",
            input_lock_id=replay.input_lock_id,
            state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            source_refs=durable_sources,
            replay=replay,
            paper=paper,
            divergence_ref=divergence.assessment_id,
        )
        return harness.service.build_bundle(
            _bundle_request(
                harness,
                identity=f"{identity}-READY",
                source_refs=durable_sources,
                requested_at=_NOW + timedelta(seconds=second),
            ),
            candidate,
        )

    rejected_ready = new_ready("REJECT", 20)
    rejected_prior = (
        f"ST12F-RECEIPT::{rejected_ready.evidence_bundle_version}::EVIDENCE_BUNDLE_VERSION"
    )
    rejected_review = _review_record(
        review_id="REVIEW::REJECTED",
        prior_ref=rejected_prior,
        evidence_id=rejected_ready.evidence_id,
        candidate_version="BUNDLE::REJECT::2",
        input_lock_id=replay.input_lock_id,
        decision=IndependentReviewDecisionV1.REJECTED,
        reviewed_at=_NOW + timedelta(seconds=21),
    )
    rejected = _bundle_candidate(
        evidence_id=rejected_ready.evidence_id,
        version=rejected_review.evidence_bundle_version,
        input_lock_id=replay.input_lock_id,
        state=EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
        source_refs=durable_sources,
        replay=replay,
        paper=paper,
        divergence_ref=divergence.assessment_id,
        blockers=rejected_review.blocker_codes,
    )
    rejected_value = harness.service.build_bundle(
        _bundle_request(
            harness,
            identity="REJECTED",
            source_refs=durable_sources,
            requested_at=_NOW + timedelta(seconds=22),
        ),
        rejected,
        control_contracts=(rejected_review,),
    )
    observed_states.add(rejected_value.terminal_state)

    wrong_review = replace(
        rejected_review,
        review_id="REVIEW::WRONG-CANDIDATE",
        evidence_bundle_version="BUNDLE::WRONG",
    )
    try:
        harness.service.build_bundle(
            _bundle_request(
                harness,
                identity="WRONG-REVIEW",
                source_refs=durable_sources,
                requested_at=_NOW + timedelta(seconds=23),
            ),
            replace(
                rejected,
                evidence_id="EVIDENCE::WRONG-REVIEW",
                evidence_bundle_version="BUNDLE::WRONG-REVIEW::2",
            ),
            control_contracts=(wrong_review,),
        )
    except ContractValidationError as exc:
        assert exc.reason_code in {
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
            ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
        }
    else:
        raise AssertionError("wrong review prior/candidate version was accepted")

    closed_ready = new_ready("CLOSED", 30)
    closed_prior = (
        f"ST12F-RECEIPT::{closed_ready.evidence_bundle_version}::EVIDENCE_BUNDLE_VERSION"
    )
    closed_version = "BUNDLE::CLOSED::2"
    bundle_record_ref = (
        f"ST12F-RECEIPT::{closed_version}::EVIDENCE_BUNDLE_VERSION"
    )
    closed_review = _review_record(
        review_id="REVIEW::VALIDATED",
        prior_ref=closed_prior,
        evidence_id=closed_ready.evidence_id,
        candidate_version=closed_version,
        input_lock_id=replay.input_lock_id,
        decision=IndependentReviewDecisionV1.VALIDATED,
        reviewed_at=_NOW + timedelta(seconds=31),
    )
    d_reference = ST12FEvidenceReferenceV1(
        evidence_state=ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE,
        evidence_ref=bundle_record_ref,
        lane="REPLAY_PAPER",
        dataset_grade_ref="DATASET-GRADE::RUNTIME",
        venue_semantic_binding_ref="VENUE-SEMANTICS::RUNTIME",
        cross_venue_equivalence_ref="CROSS-VENUE::RUNTIME",
        observed_at=closed_review.reviewed_at,
        valid_until=closed_review.valid_until,
        policy_version="ST12F_EVIDENCE_POLICY_V1_4",
        causation_id="CAUSE::1",
        correlation_id="CORRELATION::1",
        input_lock_id=replay.input_lock_id,
        component_or_template_ref="MATH-01",
        evidence_bundle_version=closed_version,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        terminal_state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value,
        reference_id="D-REFERENCE::CLOSED",
        evidence_id=closed_ready.evidence_id,
    )
    g_handoff = FToGHandoffReferencesV1(
        handoff_id="G-HANDOFF::CLOSED",
        contract_version="1.4",
        input_lock_id=replay.input_lock_id,
        source_epoch_refs=("SOURCE::1=EPOCH::1",),
        observed_at=closed_review.reviewed_at,
        valid_until=closed_review.valid_until,
        terminal_state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value,
        evidence_bundle_ref=bundle_record_ref,
        no_trade_blocker_refs=(),
        champion_challenger_evidence_refs=(model_receipt,),
        portfolio_utility_refs=("RECEIPT::PORTFOLIO-UTILITY",),
        quantum_classical_comparison_receipt_ref="RECEIPT::QUANTUM-COMPARISON",
    )
    closed = _bundle_candidate(
        evidence_id=closed_ready.evidence_id,
        version=closed_version,
        input_lock_id=replay.input_lock_id,
        state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        source_refs=durable_sources,
        replay=replay,
        paper=paper,
        divergence_ref=divergence.assessment_id,
        d_reference=d_reference,
        g_handoff=g_handoff,
    )
    closed_value = harness.service.build_bundle(
        _bundle_request(
            harness,
            identity="CLOSED",
            source_refs=durable_sources,
            requested_at=_NOW + timedelta(seconds=32),
        ),
        closed,
        control_contracts=(closed_review,),
    )
    observed_states.add(closed_value.terminal_state)

    def close_ready(
        *,
        runtime: _RuntimeHarnessV1,
        identity: str,
        ready_value: ComputationEvidenceBundleV1,
        replay_value: ReplayResultContractV1,
        paper_value: PaperResultContractV1,
        divergence_value: DivergenceAssessmentV1,
        source_refs: tuple[str, ...],
        model_receipt_ref: str,
        requested_at: datetime,
        valid_until: datetime,
        component: str = "MATH-01",
    ) -> tuple[ComputationEvidenceBundleV1, ST12FEvidenceReferenceV1, str]:
        prior_ref = (
            f"ST12F-RECEIPT::{ready_value.evidence_bundle_version}::"
            "EVIDENCE_BUNDLE_VERSION"
        )
        version = f"{ready_value.evidence_bundle_version}::CLOSED"
        review = _review_record(
            review_id=f"REVIEW::{identity}",
            prior_ref=prior_ref,
            evidence_id=ready_value.evidence_id,
            candidate_version=version,
            input_lock_id=ready_value.input_lock_id,
            decision=IndependentReviewDecisionV1.VALIDATED,
            reviewed_at=requested_at - timedelta(seconds=1),
            valid_until=valid_until,
        )
        reference, handoff, record_ref = _closed_projections(
            identity=identity,
            evidence_id=ready_value.evidence_id,
            version=version,
            input_lock_id=ready_value.input_lock_id,
            component=component,
            observed_at=review.reviewed_at,
            valid_until=review.valid_until,
            model_receipt_ref=model_receipt_ref,
        )
        candidate = _bundle_candidate(
            evidence_id=ready_value.evidence_id,
            version=version,
            input_lock_id=ready_value.input_lock_id,
            component=component,
            state=EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            source_refs=source_refs,
            replay=replay_value,
            paper=paper_value,
            divergence_ref=divergence_value.assessment_id,
            d_reference=reference,
            g_handoff=handoff,
        )
        value = runtime.service.build_bundle(
            _bundle_request(
                runtime,
                identity=f"{identity}-CLOSED",
                source_refs=source_refs,
                requested_at=requested_at,
                component=component,
                input_lock_id=ready_value.input_lock_id,
            ),
            candidate,
            control_contracts=(review,),
        )
        return value, reference, record_ref

    for prohibited_state in (
        EvidenceBundleTerminalStateV1.STALE,
        EvidenceBundleTerminalStateV1.SUPERSEDED,
    ):
        prohibited = _bundle_candidate(
            evidence_id=persisted_ready.evidence_id,
            version=f"BUNDLE::READY-PROHIBITED::{prohibited_state.value}",
            input_lock_id=persisted_ready.input_lock_id,
            state=prohibited_state,
            source_refs=durable_sources,
            replay=replay,
            paper=paper,
            divergence_ref=divergence.assessment_id,
            blockers=(
                (ReasonCode.ST12F_BUNDLE_STALE,)
                if prohibited_state is EvidenceBundleTerminalStateV1.STALE
                else ()
            ),
        )
        try:
            ComputationEvidenceServiceV1._validate_bundle_transition(
                persisted_ready,
                prohibited,
            )
        except ContractValidationError as exc:
            assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
        else:
            raise AssertionError(
                f"READY to {prohibited_state.value} was accepted"
            )

    stale_ready = new_ready("STALE", 40)
    stale_closed, stale_reference, stale_closed_ref = close_ready(
        runtime=harness,
        identity="STALE",
        ready_value=stale_ready,
        replay_value=replay,
        paper_value=paper,
        divergence_value=divergence,
        source_refs=durable_sources,
        model_receipt_ref=model_receipt,
        requested_at=_NOW + timedelta(seconds=42),
        valid_until=_NOW + timedelta(seconds=44),
    )
    stale_candidate = _bundle_candidate(
        evidence_id=stale_closed.evidence_id,
        version="BUNDLE::STALE::3",
        input_lock_id=stale_closed.input_lock_id,
        state=EvidenceBundleTerminalStateV1.STALE,
        source_refs=durable_sources,
        replay=replay,
        paper=paper,
        divergence_ref=divergence.assessment_id,
        blockers=(ReasonCode.ST12F_BUNDLE_STALE,),
    )
    try:
        harness.service.build_bundle(
            _bundle_request(
                harness,
                identity="STALE-WITHOUT-GUARD",
                source_refs=durable_sources,
                requested_at=_NOW + timedelta(seconds=43),
            ),
            stale_candidate,
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_BUNDLE_STALE
    else:
        raise AssertionError("CLOSED to STALE without exact TTL proof was accepted")
    stale_value = harness.service.build_bundle(
        _bundle_request(
            harness,
            identity="STALE-WITH-TTL-GUARD",
            source_refs=durable_sources,
            requested_at=_NOW + timedelta(seconds=45),
        ),
        stale_candidate,
    )
    assert stale_reference.valid_until < _NOW + timedelta(seconds=45)
    observed_states.add(stale_value.terminal_state)

    superseded_ready = new_ready("SUPERSEDED", 50)
    superseded_closed, _superseded_reference, superseded_closed_ref = close_ready(
        runtime=harness,
        identity="SUPERSEDED-OLD",
        ready_value=superseded_ready,
        replay_value=replay,
        paper_value=paper,
        divergence_value=divergence,
        source_refs=durable_sources,
        model_receipt_ref=model_receipt,
        requested_at=_NOW + timedelta(seconds=52),
        valid_until=_NOW + timedelta(hours=1),
    )
    superseded_without_newer = _bundle_candidate(
        evidence_id=superseded_closed.evidence_id,
        version="BUNDLE::SUPERSEDED::WITHOUT-NEWER",
        input_lock_id=superseded_closed.input_lock_id,
        state=EvidenceBundleTerminalStateV1.SUPERSEDED,
        source_refs=durable_sources,
        replay=replay,
        paper=paper,
        divergence_ref=divergence.assessment_id,
    )
    try:
        harness.service.build_bundle(
            _bundle_request(
                harness,
                identity="SUPERSEDED-WITHOUT-NEWER-CLOSED",
                source_refs=durable_sources,
                requested_at=_NOW + timedelta(seconds=53),
            ),
            superseded_without_newer,
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
    else:
        raise AssertionError(
            "CLOSED to SUPERSEDED without a newer closed bundle was accepted"
        )

    newer_harness = _runtime_harness(
        harness.persistence,
        identity="SUPERSEDED-NEW-LOCK",
    )
    newer_replay, newer_paper = _register_dual_lanes(
        newer_harness,
        identity="SUPERSEDED-NEW-LOCK",
    )
    newer_divergence = _runtime_divergence(
        newer_replay,
        newer_paper,
        identity="SUPERSEDED-NEW-LOCK",
    )
    newer_model_risk = _runtime_model_risk(
        newer_replay,
        newer_paper,
        identity="SUPERSEDED-NEW-LOCK",
    )
    newer_sources = ("UPSTREAM::SUPERSEDED-NEW-LOCK",)
    newer_ready_candidate = _bundle_candidate(
        evidence_id=superseded_closed.evidence_id,
        version="BUNDLE::SUPERSEDED-NEW-LOCK::READY",
        input_lock_id=newer_replay.input_lock_id,
        state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        source_refs=newer_sources,
        replay=newer_replay,
        paper=newer_paper,
        divergence_ref=newer_divergence.assessment_id,
    )
    newer_ready = newer_harness.service.build_bundle(
        _bundle_request(
            newer_harness,
            identity="SUPERSEDED-NEW-LOCK-READY",
            source_refs=newer_sources,
            requested_at=_NOW + timedelta(seconds=54),
        ),
        newer_ready_candidate,
        control_contracts=(newer_divergence, newer_model_risk),
    )
    newer_divergence_receipt = (
        f"ST12F-RECEIPT::{newer_divergence.assessment_id}::"
        "DIVERGENCE_ASSESSMENT"
    )
    newer_model_receipt = (
        f"ST12F-RECEIPT::{newer_model_risk.assessment_id}::"
        "MODEL_RISK_ASSESSMENT"
    )
    newer_durable_sources = (newer_divergence_receipt, newer_model_receipt)
    newer_closed, _newer_reference, newer_closed_ref = close_ready(
        runtime=newer_harness,
        identity="SUPERSEDED-NEW-LOCK",
        ready_value=newer_ready,
        replay_value=newer_replay,
        paper_value=newer_paper,
        divergence_value=newer_divergence,
        source_refs=newer_durable_sources,
        model_receipt_ref=newer_model_receipt,
        requested_at=_NOW + timedelta(seconds=56),
        valid_until=_NOW + timedelta(hours=1),
    )
    superseded_sources = (newer_closed_ref,)
    superseded_candidate = _bundle_candidate(
        evidence_id=superseded_closed.evidence_id,
        version="BUNDLE::SUPERSEDED::WITH-NEWER",
        input_lock_id=superseded_closed.input_lock_id,
        state=EvidenceBundleTerminalStateV1.SUPERSEDED,
        source_refs=superseded_sources,
        replay=replay,
        paper=paper,
        divergence_ref=divergence.assessment_id,
    )
    superseded_value = newer_harness.service.build_bundle(
        _bundle_request(
            newer_harness,
            identity="SUPERSEDED-WITH-NEWER-CLOSED",
            source_refs=superseded_sources,
            requested_at=_NOW + timedelta(seconds=58),
            input_lock_id=superseded_closed.input_lock_id,
        ),
        superseded_candidate,
    )
    assert newer_closed.input_lock_id != superseded_value.input_lock_id
    observed_states.add(superseded_value.terminal_state)

    assert observed_states == set(EvidenceBundleTerminalStateV1)

    restarted = ComputationEvidenceServiceV1(
        ReplayPaperCohortCompilerV1(harness.snapshot, harness.persistence),
        harness.persistence,
    )
    assert restarted.resolve_bundle(bundle_record_ref) == closed_value
    assert divergence.assessment_id in restarted.immutable_indexes["divergence"]
    assert d_reference.reference_id in restarted.immutable_indexes["d_references"]
    assert g_handoff.handoff_id in restarted.immutable_indexes["g_handoffs"]

    def transition_contract(
        state: EvidenceBundleTerminalStateV1,
        *,
        version: str,
    ) -> ComputationEvidenceBundleV1:
        state_replay: ReplayResultContractV1 | None = replay
        state_paper: PaperResultContractV1 | None = paper
        state_divergence = divergence.assessment_id
        state_blockers: tuple[ReasonCode, ...] = ()
        state_reference: ST12FEvidenceReferenceV1 | str = "UNAVAILABLE"
        state_handoff: FToGHandoffReferencesV1 | str = "UNAVAILABLE"
        if state is EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY:
            state_replay = None
            state_divergence = "EXPLICIT_ABSENCE"
            state_blockers = (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,)
        elif state is EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER:
            state_paper = None
            state_divergence = "EXPLICIT_ABSENCE"
            state_blockers = (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,)
        elif state is EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT:
            state_divergence = conflicting_divergence.assessment_id
            state_blockers = (ReasonCode.ST12F_EVIDENCE_INCOMPLETE,)
        elif state is EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED:
            state_blockers = (ReasonCode.ST12F_MODEL_RISK_VETO,)
        elif state is EvidenceBundleTerminalStateV1.STALE:
            state_blockers = (ReasonCode.ST12F_BUNDLE_STALE,)
        elif state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
            state_reference, state_handoff, _record_ref = _closed_projections(
                identity=f"TRANSITION-MATRIX::{version}",
                evidence_id="EVIDENCE::TRANSITION-MATRIX",
                version=version,
                input_lock_id=replay.input_lock_id,
                component="MATH-01",
                observed_at=_NOW,
                valid_until=_NOW + timedelta(hours=1),
                model_receipt_ref=model_receipt,
            )
        return _bundle_candidate(
            evidence_id="EVIDENCE::TRANSITION-MATRIX",
            version=version,
            input_lock_id=replay.input_lock_id,
            state=state,
            source_refs=durable_sources,
            replay=state_replay,
            paper=state_paper,
            divergence_ref=state_divergence,
            blockers=state_blockers,
            d_reference=state_reference,
            g_handoff=state_handoff,
        )

    allowed_pairs = {
        (source, target) for source, target, _guard in _OWNER_TRANSITIONS
    }
    allowed_transition_positive_count = 0
    prohibited_transition_rejection_count = 0
    for source_state in EvidenceBundleTerminalStateV1:
        previous = transition_contract(
            source_state,
            version=f"BUNDLE::TRANSITION-MATRIX::{source_state.value}::PRIOR",
        )
        for target_state in EvidenceBundleTerminalStateV1:
            candidate = transition_contract(
                target_state,
                version=(
                    f"BUNDLE::TRANSITION-MATRIX::{source_state.value}::"
                    f"{target_state.value}"
                ),
            )
            assert (
                previous.evidence_id,
                previous.input_lock_id,
                previous.component_or_template_ref,
            ) == (
                candidate.evidence_id,
                candidate.input_lock_id,
                candidate.component_or_template_ref,
            )
            assert previous.evidence_bundle_version != candidate.evidence_bundle_version
            expected_allowed = (
                source_state.value,
                target_state.value,
            ) in allowed_pairs
            try:
                ComputationEvidenceServiceV1._validate_bundle_transition(
                    previous,
                    candidate,
                )
            except ContractValidationError as exc:
                assert not expected_allowed
                assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
                prohibited_transition_rejection_count += 1
            else:
                assert expected_allowed
                allowed_transition_positive_count += 1
    assert allowed_transition_positive_count == 6
    assert prohibited_transition_rejection_count == 58

    root_states = {
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT,
        EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
    }
    for state in EvidenceBundleTerminalStateV1:
        candidate = transition_contract(
            state,
            version=f"BUNDLE::TRANSITION-MATRIX::ROOT::{state.value}",
        )
        try:
            ComputationEvidenceServiceV1._validate_bundle_transition(
                None,
                candidate,
            )
        except ContractValidationError as exc:
            assert state not in root_states
            assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
        else:
            assert state in root_states

    identity_previous = transition_contract(
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
        version="BUNDLE::IDENTITY-CONTINUITY::PRIOR",
    )
    identity_candidate = transition_contract(
        EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        version="BUNDLE::IDENTITY-CONTINUITY::CANDIDATE",
    )
    ComputationEvidenceServiceV1._validate_bundle_transition(
        identity_previous,
        identity_candidate,
    )
    for field_name, changed_value in (
        ("evidence_id", "EVIDENCE::MIGRATED"),
        ("input_lock_id", "LOCK::MIGRATED"),
        ("component_or_template_ref", "MATH-02"),
    ):
        migrated = replace(identity_candidate, **{field_name: changed_value})
        assert migrated.evidence_bundle_version == identity_candidate.evidence_bundle_version
        try:
            ComputationEvidenceServiceV1._validate_bundle_transition(
                identity_previous,
                migrated,
            )
        except ContractValidationError as exc:
            assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID
        else:
            raise AssertionError(f"bundle identity migration accepted: {field_name}")
    same_version = replace(
        identity_candidate,
        evidence_bundle_version=identity_previous.evidence_bundle_version,
    )
    try:
        ComputationEvidenceServiceV1._validate_bundle_transition(
            identity_previous,
            same_version,
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
    else:
        raise AssertionError("same-version lifecycle transition was accepted")

    stale_ready_ref = (
        f"ST12F-RECEIPT::{stale_ready.evidence_bundle_version}::"
        "EVIDENCE_BUNDLE_VERSION"
    )
    stale_value_ref = (
        f"ST12F-RECEIPT::{stale_value.evidence_bundle_version}::"
        "EVIDENCE_BUNDLE_VERSION"
    )
    lineage_rows = (
        (stale_ready_ref, stale_ready, "EXPLICIT_ABSENCE"),
        (stale_closed_ref, stale_closed, stale_ready_ref),
        (stale_value_ref, stale_value, stale_closed_ref),
    )
    assert ComputationEvidenceServiceV1._bundle_leaf_ref(lineage_rows) == stale_value_ref
    stale_identity = (
        stale_value.evidence_id,
        stale_value.input_lock_id,
        stale_value.component_or_template_ref,
    )
    assert harness.service.immutable_indexes["current_bundles"][stale_identity] == stale_value_ref
    assert restarted.immutable_indexes["current_bundles"][stale_identity] == stale_value_ref
    for record_ref, _bundle_value, expected_parent in lineage_rows:
        spine = harness.persistence.get_record(record_ref)
        assert type(spine) is EconomicReceiptEventSpineV1
        assert (
            spine.typed_payload.parent_version_ref_or_explicit_absence
            == expected_parent
        )
        assert not hasattr(
            spine.typed_payload.reconstruct(ComputationEvidenceBundleV1),
            "prior_bundle_ref_or_explicit_absence",
        )

    branch_ref = "ST12F-RECEIPT::BUNDLE::LINEAGE-BRANCH::EVIDENCE_BUNDLE_VERSION"
    branch_value = replace(
        rejected_value,
        evidence_id=stale_ready.evidence_id,
        input_lock_id=stale_ready.input_lock_id,
        component_or_template_ref=stale_ready.component_or_template_ref,
        evidence_bundle_version="BUNDLE::LINEAGE-BRANCH",
    )
    lineage_negative_cases = (
        ("branched", (*lineage_rows, (branch_ref, branch_value, stale_ready_ref))),
        (
            "cyclic",
            (
                (stale_ready_ref, stale_ready, stale_value_ref),
                lineage_rows[1],
                lineage_rows[2],
            ),
        ),
        (
            "disconnected",
            (
                lineage_rows[0],
                (stale_closed_ref, stale_closed, "EXPLICIT_ABSENCE"),
                lineage_rows[2],
            ),
        ),
        (
            "missing-parent",
            (
                lineage_rows[0],
                (stale_closed_ref, stale_closed, "ST12F-RECEIPT::MISSING-PARENT"),
                lineage_rows[2],
            ),
        ),
    )
    lineage_rejections: dict[str, int] = {
        name: 0 for name, _rows in lineage_negative_cases
    }
    for name, mutated_rows in lineage_negative_cases:
        assert len(mutated_rows) >= len(lineage_rows)
        try:
            ComputationEvidenceServiceV1._bundle_leaf_ref(mutated_rows)
        except ContractValidationError as exc:
            assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
            lineage_rejections[name] += 1
        else:
            raise AssertionError(f"{name} durable bundle lineage was accepted")
    assert lineage_rejections == {
        "branched": 1,
        "cyclic": 1,
        "disconnected": 1,
        "missing-parent": 1,
    }

    read_context = replace(
        harness.context,
        as_of=_NOW + timedelta(seconds=33),
        observed_at=_NOW + timedelta(seconds=33),
    )
    query = FToDEvidenceReferenceQueryV1(
        query_id="D-QUERY::VALID",
        requested_evidence_id=closed_value.evidence_id,
        requested_component_or_template_ref="MATH-01",
        expected_input_lock_id=replay.input_lock_id,
        expected_source_epoch_refs=("SOURCE::1=EPOCH::1",),
        evaluated_at=_NOW + timedelta(seconds=33),
        request_read_lineage_refs=("READ-RECEIPT::1",),
    )
    resolved = restarted.read_evidence_reference(
        read_context,
        causation_id="READ-CAUSE::DIFFERENT",
        correlation_id="READ-CORRELATION::DIFFERENT",
        query=query,
    )
    assert resolved == d_reference
    mismatch_queries = (
        replace(query, requested_evidence_id="EVIDENCE::OTHER"),
        replace(query, requested_component_or_template_ref="MATH-02"),
        replace(query, expected_input_lock_id="ST12F-LOCK::OTHER"),
        replace(query, expected_source_epoch_refs=("SOURCE::1=EPOCH::OTHER",)),
        replace(query, evaluated_at=d_reference.valid_until + timedelta(seconds=1)),
    )
    for mismatched in mismatch_queries:
        unavailable = restarted.read_evidence_reference(
            read_context,
            causation_id="READ-CAUSE::DIFFERENT",
            correlation_id="READ-CORRELATION::DIFFERENT",
            query=mismatched,
        )
        assert unavailable.evidence_state is ST12FEvidenceStateV1.EVIDENCE_INSUFFICIENT_FAIL_CLOSED

    multi_component_references: dict[str, ST12FEvidenceReferenceV1] = {}
    for offset, component in enumerate(("MATH-02", "MATH-03"), start=70):
        identity = f"MULTI-{component}"
        component_replay, component_paper = _register_dual_lanes(
            newer_harness,
            identity=identity,
            component=component,
        )
        component_divergence = _runtime_divergence(
            component_replay,
            component_paper,
            identity=identity,
        )
        component_model_risk = _runtime_model_risk(
            component_replay,
            component_paper,
            identity=identity,
        )
        component_sources = (f"UPSTREAM::{identity}",)
        component_ready = newer_harness.service.build_bundle(
            _bundle_request(
                newer_harness,
                identity=f"{identity}-READY",
                source_refs=component_sources,
                requested_at=_NOW + timedelta(seconds=offset),
                component=component,
            ),
            _bundle_candidate(
                evidence_id="EVIDENCE::MULTI-COMPONENT",
                version=f"BUNDLE::{identity}::READY",
                input_lock_id=component_replay.input_lock_id,
                component=component,
                state=EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
                source_refs=component_sources,
                replay=component_replay,
                paper=component_paper,
                divergence_ref=component_divergence.assessment_id,
            ),
            control_contracts=(component_divergence, component_model_risk),
        )
        component_divergence_receipt = (
            f"ST12F-RECEIPT::{component_divergence.assessment_id}::"
            "DIVERGENCE_ASSESSMENT"
        )
        component_model_receipt = (
            f"ST12F-RECEIPT::{component_model_risk.assessment_id}::"
            "MODEL_RISK_ASSESSMENT"
        )
        component_closed, component_reference, _component_closed_ref = close_ready(
            runtime=newer_harness,
            identity=identity,
            ready_value=component_ready,
            replay_value=component_replay,
            paper_value=component_paper,
            divergence_value=component_divergence,
            source_refs=(
                component_divergence_receipt,
                component_model_receipt,
            ),
            model_receipt_ref=component_model_receipt,
            requested_at=_NOW + timedelta(seconds=offset + 1),
            valid_until=_NOW + timedelta(hours=1),
            component=component,
        )
        assert (
            component_closed.component_or_template_ref == component
            and component_closed.evidence_id == "EVIDENCE::MULTI-COMPONENT"
        )
        multi_component_references[component] = component_reference

    multi_read_at = _NOW + timedelta(seconds=90)
    multi_read_context = replace(
        newer_harness.context,
        as_of=multi_read_at,
        observed_at=multi_read_at,
    )
    multi_component_selection_count = 0
    for component in ("MATH-02", "MATH-03"):
        expected_reference = multi_component_references[component]
        actual_reference = newer_harness.service.read_evidence_reference(
            multi_read_context,
            causation_id=f"READ-CAUSE::{component}",
            correlation_id=f"READ-CORRELATION::{component}",
            query=FToDEvidenceReferenceQueryV1(
                query_id=f"D-QUERY::{component}",
                requested_evidence_id="EVIDENCE::MULTI-COMPONENT",
                requested_component_or_template_ref=component,
                expected_input_lock_id=expected_reference.input_lock_id,
                expected_source_epoch_refs=expected_reference.source_epoch_refs,
                evaluated_at=multi_read_at,
                request_read_lineage_refs=(f"READ-LINEAGE::{component}",),
            ),
        )
        assert actual_reference == expected_reference
        multi_component_selection_count += 1
    assert multi_component_selection_count == 2

    try:
        replace(d_reference, terminal_state="STALE")
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.EVIDENCE_REFERENCE_UNAVAILABLE_STALE_CONFLICTING_OR_SCOPE_MISMATCH
    else:
        raise AssertionError("D terminal-state mismatch was accepted")
    bad_no_effect = replace(d_reference)
    object.__setattr__(bad_no_effect, "no_effect_flags", object())
    try:
        ComputationEvidenceServiceV1._validate_closed_projections(
            replace(closed_value, d_evidence_reference_projection=bad_no_effect),
            bundle_record_ref=bundle_record_ref,
            lock=harness.compilation.input_lock,
        )
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.ST12F_EVIDENCE_INCOMPLETE
    else:
        raise AssertionError("D no-effect mismatch was accepted")

    spines = tuple(
        row
        for row in harness.service._durable_receipt_spines()
        if type(row.typed_payload) is ST12FEvidenceControlReceiptRecordV1
    )
    classes = {row.typed_payload.receipt_class for row in spines}
    assert classes == set(ST12FReceiptClassV1)
    expected_types: dict[ST12FReceiptClassV1, type[object]] = {
        ST12FReceiptClassV1.COHORT_COMPILATION: ReplayPaperCohortCompilationRecordV1,
        ST12FReceiptClassV1.INPUT_LOCK: ImmutableReplayPaperInputLockV1,
        ST12FReceiptClassV1.REPLAY_REGISTRATION: ReplayResultContractV1,
        ST12FReceiptClassV1.PAPER_REGISTRATION: PaperResultContractV1,
        ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT: DivergenceAssessmentV1,
        ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT: type(model_risk),
        ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION: QuantumTraceValidationReceiptV1,
        ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION: DeterministicEvidenceAnnotationContractV1,
        ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION: ComputationEvidenceBundleV1,
        ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION: IndependentReviewRecordV1,
        ST12FReceiptClassV1.D_EVIDENCE_REFERENCE: ST12FEvidenceReferenceV1,
        ST12FReceiptClassV1.G_HANDOFF_REFERENCE: FToGHandoffReferencesV1,
    }
    for spine in spines:
        payload = spine.typed_payload
        payload.reconstruct(expected_types[payload.receipt_class])

    replay_spine = harness.persistence.get_record(
        f"ST12F-RECEIPT::{replay.result_id}::REPLAY_REGISTRATION"
    )
    assert type(replay_spine) is EconomicReceiptEventSpineV1
    mismatched_metadata = replace(
        replay_spine.typed_payload,
        contract_id="RESULT::OTHER",
    )
    try:
        mismatched_metadata.reconstruct(ReplayResultContractV1)
    except ContractValidationError as exc:
        assert exc.reason_code is ReasonCode.SCHEMA_MISMATCH
    else:
        raise AssertionError("receipt metadata/contract mismatch was accepted")

    assert harness.persistence.get_record(
        f"ST12F-RECEIPT::{harness.compilation.compilation_id}::COHORT_COMPILATION"
    ) is not None
    assert harness.persistence.get_record(
        f"ST12F-RECEIPT::{harness.compilation.input_lock_id}::INPUT_LOCK"
    ) is not None
    assert all(
        ref.startswith("ST12F-RECEIPT::")
        for ref in harness.service.last_committed_receipt_refs
    )
