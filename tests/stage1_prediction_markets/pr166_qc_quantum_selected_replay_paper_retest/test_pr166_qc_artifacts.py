from __future__ import annotations

from copy import deepcopy

from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.validator import validate_artifacts

from .helpers import REPO_ROOT, assert_report_contract, records, summary


def test_pr166_qc_validator_passes_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr166_qc_consumes_pr166_qb_handoffs_and_counts():
    final = summary()
    assert final["consumed_pr166_qc_handoff_rows"] == 559
    assert final["input_record_counts"]["PR166_QB_To_PR166_QC.report.json"] == 559
    assert final["input_record_counts"]["PR166_QB_ClassicalReceipt.report.json"] == 559
    assert final["input_record_counts"]["PR166_QB_QuantumRepairLab.report.json"] == 559
    assert final["input_record_counts"]["PR166_QB_ArtifactMap.report.json"] == 157
    assert_report_contract("PR166_QC_RetestEligibility.report.json", 559)
    assert_report_contract("PR166_QC_ReplayEvidence.report.json", 559)


def test_pr166_qc_source_replay_params_are_route_only_no_truth():
    rows = assert_report_contract("PR166_QC_SourceReplayParams.report.json", 12)
    assert any(row["official_flag"] for row in rows)
    assert any(row["non_official_flag"] for row in rows)
    assert all(row["source_locator_or_query"] for row in rows)
    assert all(row["candidate_values_extracted_count"] > 0 for row in rows)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in rows)
    assert all(row["no_connector_binding_flag"] is True for row in rows)
    assert all(row["no_profit_evidence_flag"] is True for row in rows)


def test_pr166_qc_retest_budget_subset_is_capped_and_deterministic():
    final = summary()
    budget = records("PR166_QC_RetestBudget.report.json")[0]
    subset = [row for row in records("PR166_QC_SubsetSelection.report.json") if row["actual_retest_subset_flag"]]
    assert len(subset) == 64
    assert final["replay_paper_retest_subset_count"] == 64
    assert budget["max_actual_replay_paper_rows_default_ci"] == 64
    assert budget["max_walk_forward_slices_default_ci"] == 4
    assert budget["max_scenario_states_default_ci"] == 16
    assert budget["max_market_book_states_default_ci"] == 16
    assert budget["max_random_seeds_default_ci"] == 3
    assert [row["deterministic_sort_key"] for row in subset] == sorted(row["deterministic_sort_key"] for row in subset)

    # Type-safe selection and budgets must hold even outside the large fixture.
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import validator as qc_validator
    from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark import validator as qb_validator
    budget_name = "PR166_QC_RetestBudget.report.json"
    selection_name = "PR166_QC_SubsetSelection.report.json"
    baseline = {budget_name: [{**c.RETEST_CAPS, "actual_replay_paper_subset_size": 0}], selection_name: []}
    failures = []
    qc_validator._validate_retest_budget(deepcopy(baseline), failures)
    assert not failures
    for key in ("actual_replay_paper_subset_size", *c.RETEST_CAPS):
        for value in (False, True, float(baseline[budget_name][0][key]), "0", None, -1):
            bad = deepcopy(baseline)
            bad[budget_name][0][key] = value
            failures = []
            qc_validator._validate_retest_budget(bad, failures)
            assert failures, (key, value)
    for value in (0, 1, 0.0, 1.0, "false", "true", None, [], {}):
        bad = deepcopy(baseline)
        bad[selection_name] = [{"row_id": "invalid-flag", "actual_retest_subset_flag": value}]
        failures = []
        qc_validator._validate_retest_budget(bad, failures)
        assert failures == ["RETEST_SUBSET_FLAG_INVALID::invalid-flag"]
    for validator, family, subset_key in (
        (qb_validator, "PR166_QB", "benchmark_subset_count"),
        (qc_validator, "PR166_QC", "replay_paper_retest_subset_count"),
    ):
        report_name = family + "_FinalSummary.report.json"
        handoff_key = "consumed_" + family.lower() + "_handoff_rows"
        good = {handoff_key: 559, subset_key: 0,
                "forbidden_authority_counts_all_zero_flag": True,
                "cloud_switchboard_default_mode": "OFF", "owner_dashboard_default_mode": "OFF",
                "dashboard_ui_implemented_flag": False}
        failures = []
        validator._validate_summary({report_name: [good]}, failures)
        assert not failures
        for key, value in ((handoff_key, 559.0), (subset_key, False),
                           (subset_key, -1), (subset_key, 0.0), (subset_key, "0")):
            bad = deepcopy(good)
            bad[key] = value
            failures = []
            validator._validate_summary({report_name: [bad]}, failures)
            assert failures, (family, key, value)
        absent_optional = deepcopy(good)
        del absent_optional[subset_key]
        failures = []
        validator._validate_summary({report_name: [absent_optional]}, failures)
        assert not failures

    # Fallback selection must preserve the same per-role cap as priority selection.
    from collections import Counter
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.report_writer import select_retest_subset
    role_cap = c.RETEST_CAPS["max_rows_per_role_default_ci"]
    total_cap = c.RETEST_CAPS["max_actual_replay_paper_rows_default_ci"]
    for role in ("benchmark watch", "synthetic-unlisted-role"):
        for size in (0, 1, role_cap - 1, role_cap, role_cap + 1, total_cap + 1):
            contexts = [{"handoff": {}, "benchmark_role": role,
                         "upstream_pr166_qb_row_ref": f"synthetic-{i:04d}"} for i in range(size)]
            expected = {f"synthetic-{i:04d}" for i in range(min(size, role_cap, total_cap))}
            assert select_retest_subset(contexts) == expected
            assert select_retest_subset(list(reversed(contexts))) == expected
            assert select_retest_subset(contexts + contexts) == expected
    mixed = [{"handoff": {}, "benchmark_role": role,
              "upstream_pr166_qb_row_ref": f"synthetic-{group}-{i:04d}"}
             for group, role in enumerate(("benchmark champion", "benchmark challenger",
                 "benchmark watch", "replay/paper retest", "synthetic-unlisted-role"))
             for i in range(role_cap + 1)]
    selected_ids = select_retest_subset(mixed)
    selected_counts = Counter(row["benchmark_role"] for row in mixed
                              if row["upstream_pr166_qb_row_ref"] in selected_ids)
    assert len(selected_ids) == total_cap
    assert all(value <= role_cap for value in selected_counts.values())
    assert select_retest_subset(list(reversed(mixed))) == selected_ids


def test_pr166_qc_dispositions_and_lanes_are_complete_and_fail_closed():
    rows = assert_report_contract("PR166_QC_RetestEligibility.report.json", 559)
    assert all(row["evidence_disposition"] in c.EVIDENCE_DISPOSITIONS for row in rows)
    assert all(row["evidence_disposition"] not in c.FORBIDDEN_EVIDENCE_DISPOSITIONS for row in rows)
    assert all(row["primary_evidence_lane"] in c.EVIDENCE_LANES for row in rows)
    assert all(row["primary_evidence_lane"] in row["evidence_lanes"] for row in rows)
    bad = deepcopy(rows[0])
    bad["evidence_disposition"] = "METADATA_ONLY_EVIDENCED"
    assert bad["evidence_disposition"] in c.FORBIDDEN_EVIDENCE_DISPOSITIONS
    bad["evidence_disposition"] = "UNBOUNDED_REPLAY_EXECUTED"
    assert bad["evidence_disposition"] in c.FORBIDDEN_EVIDENCE_DISPOSITIONS
    bad["evidence_disposition"] = "LIVE_ORDER_EXECUTED"
    assert bad["evidence_disposition"] in c.FORBIDDEN_EVIDENCE_DISPOSITIONS


def test_pr166_qc_evidence_quality_replay_paper_scores_are_present():
    rows = assert_report_contract("PR166_QC_EvidenceQuality.report.json", 559)
    assert all(row["evidence_quality_grade"] in c.EVIDENCE_QUALITY_GRADES for row in rows)
    assert all(0 <= row["evidence_quality_score"] <= 1 for row in rows)
    assert all(0 <= row["replay_evidence_score"] <= 1 for row in rows)
    assert all(0 <= row["paper_evidence_score"] <= 1 for row in rows)
    assert all(0 <= row["calibration_score"] <= 1 for row in rows)
    assert all(row["probability_reliability_bucket"] for row in rows)
    assert any(row["paper_promotion_candidate_flag"] for row in rows)
    assert all(not row["live_promotion_claim_flag"] for row in rows)

    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.validator import _validate_payload_contracts
    count_name = "PR166_QC_InputConsumption.report.json"
    count_payload = {count_name: {"roadmap_pr_id": c.PR_ID, "created_by_pr": c.PR_ID, "record_count": 1}}
    count_rows = {count_name: [{}]}
    failures = []
    _validate_payload_contracts(count_payload, count_rows, failures)
    assert failures == []
    for value in (True, False, 1.0, 1.9, "1", None, -1, float("nan"), float("inf")):
        candidate_count = dict(count_payload[count_name])
        candidate_count["record_count"] = value
        failures = []
        _validate_payload_contracts({count_name: candidate_count}, count_rows, failures)
        assert failures == [f"BAD_RECORD_COUNT::{count_name}"]

    from copy import deepcopy
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.validator import (
        _validate_evidence_quality, _validate_replay_paper_and_execution,
    )
    quality_name = "PR166_QC_EvidenceQuality.report.json"
    quality = {quality_name: [{"row_id": "quality", "evidence_quality_score": 0.5,
        "sample_sufficiency_score": 0.5, "scenario_coverage_score": 0.5,
        "paper_champion_flag": False, "evidence_lanes": []}]}
    for field in ("evidence_quality_score", "sample_sufficiency_score", "scenario_coverage_score"):
        for value in (True, False, float("nan"), float("inf"), float("-inf"), "0.5", None):
            case = deepcopy(quality)
            case[quality_name][0][field] = value
            failures = []
            _validate_evidence_quality(case, failures)
            expected = ("EVIDENCE_QUALITY_SCORE_BAD::quality" if field == "evidence_quality_score"
                else f"SCORE_FIELD_MISSING::{quality_name}::quality::{field}")
            assert failures == [expected]
        case = deepcopy(quality)
        del case[quality_name][0][field]
        failures = []
        _validate_evidence_quality(case, failures)
        assert failures
    for field in ("sample_sufficiency_score", "scenario_coverage_score"):
        case = deepcopy(quality)
        case[quality_name][0][field] = 0.49
        failures = []
        _validate_evidence_quality(case, failures)
        assert failures == ["WEAK_SAMPLE_NOT_ROUTED::quality"]
        case[quality_name][0]["evidence_lanes"] = ["REPLAY_RETEST_REQUIRED"]
        failures = []
        _validate_evidence_quality(case, failures)
        assert failures == []

    report_names = ('PR166_QC_ReplayEvidence.report.json', 'PR166_QC_PaperEvidence.report.json', 'PR166_QC_TCAEvidence.report.json', 'PR166_QC_OverfitFDRRetest.report.json', 'PR166_QC_PortfolioUtility.report.json', 'PR166_QC_RegimeEvidence.report.json')
    score_fields = ('replay_evidence_score', 'paper_evidence_score', 'calibration_score', 'brier_score_proxy', 'sample_sufficiency_score', 'scenario_coverage_score', 'replay_paper_confidence_score')
    cost_fields = ('explicit_fee_component', 'bid_ask_spread_component', 'slippage_component', 'impact_component', 'latency_component', 'no_fill_opportunity_cost_component', 'settlement_finality_component', 'market_state_mismatch_component', 'model_vs_execution_gap_component', 'benchmark_to_replay_translation_penalty', 'replay_to_paper_translation_penalty', 'total_tca_estimate')
    required_label_fields = ('trial_family_id', 'near_duplicate_cluster_id', 'effective_independent_trial_count', 'family_wise_selection_pressure', 'false_discovery_penalty', 'deflated_score_proxy', 'probability_of_backtest_overfitting_proxy', 'replay_instability_penalty', 'paper_instability_penalty', 'replay_paper_divergence_penalty', 'seed_instability_penalty', 'rank_stability_score', 'repeated_test_inflation_penalty', 'event_cluster', 'question_market_cluster', 'formula_family_cluster', 'qku_family_cluster', 'algorithm_family_cluster', 'quantum_model_family_cluster', 'regime_cluster', 'time_to_resolution_bucket', 'liquidity_bucket', 'correlation_proxy_bucket', 'diversification_contribution', 'concentration_penalty', 'final_marginal_utility_evidence_score')
    baseline_row = {"row_id": "synthetic", "tca_reason_codes": ["SYNTHETIC"],
        "quantum_backend_execution_flag": False, **dict.fromkeys(score_fields + cost_fields, 0.5),
        **dict.fromkeys(required_label_fields, "synthetic")}
    packets = {name: [deepcopy(baseline_row)] for name in report_names}
    for name in report_names:
        for field in score_fields + cost_fields:
            for value in (True, float("nan"), float("inf"), "0.5", None):
                case = deepcopy(packets)
                case[name][0][field] = value
                failures = []
                _validate_replay_paper_and_execution(case, failures)
                prefix = "SCORE_FIELD_MISSING" if field in score_fields else "TCA_COMPONENT_MISSING"
                assert failures == [f"{prefix}::{name}::synthetic::{field}"]

    # Companion association is checked on existing semantic fields, not row order.
    from copy import deepcopy
    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.report_writer import build_candidate_contexts
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError

    companion_names = (
        'PR166_QB_SubsetSelection.report.json',
        'PR166_QB_ClassicalReceipt.report.json',
        'PR166_QB_QInspiredReceipt.report.json',
        'PR166_QB_AnnealTabuReceipt.report.json',
        'PR166_QB_ObjectiveQuality.report.json',
        'PR166_QB_RuntimeLatency.report.json',
        'PR166_QB_SeedStability.report.json',
        'PR166_QB_TCARanking.report.json',
        'PR166_QB_OverfitPenalty.report.json',
        'PR166_QB_PortfolioUtility.report.json',
        'PR166_QB_ChampChallenger.report.json',
        'PR166_QB_RegimeMemory.report.json',
        'PR166_QB_RaceArb.report.json',
        'PR166_QB_MarketPortability.report.json',
        'PR166_QB_QuantumRepairLab.report.json',
        'PR166_QB_AgentWorkOrders.report.json',
        'PR166_QB_AgentDAG.report.json',
        'PR166_QB_NoOrphanProof.report.json',
        'PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json',
    )
    primary_name = 'PR166_QB_To_PR166_QC.report.json'
    base = {"row_id": "fixture-A", "qku_id": "fixture-QKU", "formula_id": "fixture-formula",
            "algorithm_id": "fixture-algorithm", "parameter_stack_id": "fixture-parameters-A",
            "execution_route_id": "fixture-route", "market_scope": "fixture-market",
            "qku_family": "fixture-family", "model_family": "QUBO", "deterministic_sort_key": "A"}
    other = {**base, "row_id": "fixture-B", "parameter_stack_id": "fixture-parameters-B", "deterministic_sort_key": "B"}
    base["candidate_packet_id"] = "fixture-packet-A"
    other["candidate_packet_id"] = "fixture-packet-B"
    source_rows = {primary_name: [base, other]}
    for name in companion_names:
        source_rows[name] = [{**base, "row_id": name + "::A", "association_value": -7},
                             {**other, "row_id": name + "::B", "association_value": 11}]
    source = SimpleNamespace(records=source_rows)
    clean = build_candidate_contexts(source)
    assert len(clean) == 2
    expected = [-7, 11]
    for name in companion_names:
        assert [item["companions"][name]["association_value"] for item in clean] == expected
    name = companion_names[0]
    source_rows[name][0]["deterministic_sort_key"] = "Z"
    source_rows[name][1]["deterministic_sort_key"] = "0"
    source_rows[name].reverse()
    snapshot = deepcopy(source_rows)
    aligned = build_candidate_contexts(source)
    assert [item["companions"][name]["association_value"] for item in aligned] == expected
    assert source_rows == snapshot
    for mutation in ("missing", "extra", "duplicate-key", "wrong-key", "duplicate-row-id", "null-key"):
        changed = deepcopy(source_rows)
        if mutation == "missing":
            changed[name].pop()
        elif mutation == "extra":
            changed[name].append({**changed[name][0], "row_id": "fixture-extra", "parameter_stack_id": "fixture-extra"})
        elif mutation == "duplicate-key":
            changed[name].append({**changed[name][0], "row_id": "fixture-duplicate"})
        elif mutation == "wrong-key":
            changed[name][0]["execution_route_id"] = "fixture-unmatched-route"
        elif mutation == "duplicate-row-id":
            changed[name][1]["row_id"] = changed[name][0]["row_id"]
        else:
            changed[name][0]["qku_id"] = None
        with pytest.raises(SerializationSafetyError):
            build_candidate_contexts(SimpleNamespace(records=changed))

    # Existing packet identity must agree even when all context fields agree.
    for invalid_packet in (None, True, 0, 1.0, "", " ", "foreign-packet"):
        changed = deepcopy(source_rows)
        changed[name][0]["candidate_packet_id"] = invalid_packet
        with pytest.raises(SerializationSafetyError):
            build_candidate_contexts(SimpleNamespace(records=changed))
    changed = deepcopy(source_rows)
    del changed[name][0]["candidate_packet_id"]
    with pytest.raises(SerializationSafetyError):
        build_candidate_contexts(SimpleNamespace(records=changed))
    # Distinct packet identities resolve a legitimately shared six-field context.
    changed = deepcopy(source_rows)
    for values in changed.values():
        for value in values:
            value["parameter_stack_id"] = "shared-fixture-parameters"
    aligned = build_candidate_contexts(SimpleNamespace(records=changed))
    assert [item["companions"][name]["candidate_packet_id"] for item in aligned] == ["fixture-packet-A", "fixture-packet-B"]


def test_pr166_qc_tca_fill_latency_queue_components_exist():
    rows = assert_report_contract("PR166_QC_TCAEvidence.report.json", 559)
    component_keys = (
        "explicit_fee_component",
        "bid_ask_spread_component",
        "slippage_component",
        "impact_component",
        "latency_component",
        "no_fill_opportunity_cost_component",
        "settlement_finality_component",
        "market_state_mismatch_component",
        "model_vs_execution_gap_component",
        "benchmark_to_replay_translation_penalty",
        "replay_to_paper_translation_penalty",
        "total_tca_estimate",
    )
    assert all(all(isinstance(row[key], (int, float)) for key in component_keys) for row in rows)
    assert all(row["tca_reason_codes"] for row in rows)
    assert all(row["profit_evidence_flag"] is False for row in rows)


def test_pr166_qc_overfit_portfolio_regime_and_race_fields_exist():
    rows = assert_report_contract("PR166_QC_OverfitFDRRetest.report.json", 559)
    assert all(row["trial_family_id"] for row in rows)
    assert all(row["near_duplicate_cluster_id"] for row in rows)
    assert all(row["effective_independent_trial_count"] > 0 for row in rows)
    assert all(row["probability_of_backtest_overfitting_proxy"] >= 0 for row in rows)
    assert all(row["classical_fallback_available"] is True for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)
    portfolio_rows = assert_report_contract("PR166_QC_PortfolioUtility.report.json", 559)
    assert all(row["event_cluster"] for row in portfolio_rows)
    assert all(row["final_marginal_utility_evidence_score"] >= 0 for row in portfolio_rows)
    regime_rows = assert_report_contract("PR166_QC_RegimeEvidence.report.json", 559)
    assert all(row["scenario_similarity_key"] for row in regime_rows)


def test_pr166_qc_repair_dashboard_market_connector_routes_are_safe():
    repair_rows = assert_report_contract("PR166_QC_ReplayPaperRepairLab.report.json", 559)
    assert all(row["repair_row_id"] for row in repair_rows)
    assert all(row["not_profit_evidence_flag"] is True for row in repair_rows)
    assert all(row["no_live_authority_flag"] is True for row in repair_rows)
    dashboard_rows = assert_report_contract("PR166_QC_OwnerDashboardReview.report.json", 559)
    assert all(row["dashboard_review_id"] for row in dashboard_rows)
    assert all(row.get("dashboard_ui_implemented_flag") in {None, False} for row in dashboard_rows)
    market_rows = assert_report_contract("PR166_QC_MarketPortability.report.json", 559)
    assert all(row["stage1_prediction_market_flag"] is True for row in market_rows)
    assert all(row["no_current_connector_binding_flag"] is True for row in market_rows)
    connector_rows = assert_report_contract("PR166_QC_ConnectorRouteReadiness.report.json", 559)
    assert all(row["no_current_connector_binding_flag"] is True for row in connector_rows)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in connector_rows)
    assert all(row["no_private_state_fetch_flag"] is True for row in connector_rows)


def test_pr166_qc_crosswalk_artifact_map_agents_and_handoffs_have_no_orphans():
    crosswalk = assert_report_contract("PR166_QC_ReportConsumerCrosswalk.report.json")
    mapped = {row["report_path"] for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        assert f"docs/master_plan/generated/{filename}" in mapped
    artifact_rows = assert_report_contract("PR166_QC_ArtifactMap.report.json")
    assert artifact_rows
    assert all(row["artifact_path"] for row in artifact_rows)
    assert all(row["consumed_by_module"] for row in artifact_rows)
    assert_report_contract("PR166_QC_AgentWorkOrders.report.json", 559)
    assert_report_contract("PR166_QC_AgentDAG.report.json", 559)
    no_orphan = assert_report_contract("PR166_QC_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in no_orphan)
    for filename in (
        "PR166_QC_To_PR162E_Q.report.json",
        "PR166_QC_To_PR167.report.json",
        "PR166_QC_To_PR162E.report.json",
        "PR166_QC_To_PR162F.report.json",
        "PR166_QC_To_OwnerDashboard.report.json",
        "PR166_QC_To_CloudSwitchboard.report.json",
        "PR166_QC_To_FutureConnectors.report.json",
    ):
        assert_report_contract(filename, 559)


def test_pr166_qc_authority_boundary_forbidden_counts_are_zero():
    final = summary()
    assert final["forbidden_authority_counts_all_zero_flag"] is True
    for key in (
        "cloud_backend_execution_count",
        "credential_access_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "profit_evidence_count",
        "live_order_authority_count",
        "live_promotion_claim_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "qtt_sha_authority_count",
        "atomicrows_bundle_hash_authority_count",
    ):
        assert final[key] == 0
