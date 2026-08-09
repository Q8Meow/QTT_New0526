"""Compact ST12-F REPLAY/PAPER/evidence semantic matrix."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence import (
    ComputationEvidenceBundleV1,
    DivergenceAssessmentV1,
    DivergenceTerminalStateV1,
    EvidenceBundleTerminalStateV1,
    EvidenceIdentityDispositionStateV1,
    EvidenceIdentityDispositionV1,
    EvidenceSectionV1,
    IndependentReviewDecisionV1,
    IndependentReviewRecordV1,
    PaperResultContractV1,
    ReplayResultContractV1,
    ST12F_EVIDENCE_IDENTITIES_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_lock import (
    CanonicalReplayPaperInputSnapshotV1,
    ST12F_TEMPLATE_IDS_V1,
    build_immutable_replay_paper_input_lock_v1,
    canonical_st12f_parameter_value_refs_v1,
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
