from __future__ import annotations

from collections import Counter
from copy import deepcopy

from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import constants as c
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration.validator import (
    validate_artifacts,
)

from .helpers import REPO_ROOT, assert_report_contract, records, summary


def test_pr167_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr167_inputs_counts_and_required_reports():
    final = summary()
    assert final["consumed_pr167_handoff_rows"] == 559
    assert final["input_record_counts"]["PR162E_Q_To_PR167.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_To_PR167.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_OpenTradeSimHandoff.report.json"] == 559
    assert final["pr166_qc_open_trade_sim_handoff_count"] == 61
    assert final["actual_sim_subset_count"] == c.SIM_CAPS["max_actual_sim_rows_default_ci"]
    assert final["forbidden_authority_counts_all_zero_flag"] is True

    for filename in c.REPORT_FILENAMES:
        expected = 559 if filename in c.ROW_REPORTS else None
        assert_report_contract(filename, expected)

    from copy import deepcopy
    from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import validator as sim_validator

    name = "PR167_FinalSummary.report.json"
    base = {"roadmap_pr_id":c.PR_ID, "created_by_pr":c.PR_ID, "record_count":1}
    for count in (True, 1.0, "1", 1.9, None, -1):
        changed = deepcopy(base)
        changed["record_count"] = count
        failures = []
        sim_validator._validate_payload_contracts({name:changed}, {name:[{}]}, failures)
        assert failures == [f"BAD_RECORD_COUNT::{name}"]
    missing = deepcopy(base)
    del missing["record_count"]
    failures = []
    sim_validator._validate_payload_contracts({name:missing}, {name:[{}]}, failures)
    assert failures == [f"BAD_RECORD_COUNT::{name}"]
    failures = []
    sim_validator._validate_payload_contracts({name:base}, {name:[{}]}, failures)
    assert failures == []

    # Companion association is checked on existing semantic fields, not row order.
    from copy import deepcopy
    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration.report_writer import build_candidate_contexts
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError

    companion_names = (
        'PR162E_Q_OpenTradeSimMap.report.json',
        'PR162E_Q_QUBORecipe.report.json',
        'PR162E_Q_BQMRecipe.report.json',
        'PR162E_Q_IsingRecipe.report.json',
        'PR162E_Q_CQMRecipe.report.json',
        'PR162E_Q_DQMRecipe.report.json',
        'PR162E_Q_QuadProgramRecipe.report.json',
        'PR162E_Q_HybridRecipe.report.json',
        'PR162E_Q_SolutionInterpretBack.report.json',
        'PR162E_Q_TestVectors.report.json',
        'PR162E_Q_MapProof.report.json',
        'PR162E_Q_FeasibilityChecks.report.json',
        'PR162E_Q_TCAMapImpact.report.json',
        'PR162E_Q_OverfitFDRMapRisk.report.json',
        'PR162E_Q_PortfolioUtilityMap.report.json',
        'PR162E_Q_RegimeMapMemory.report.json',
        'PR166_QC_OpenTradeSimHandoff.report.json',
        'PR166_QC_To_PR167.report.json',
        'PR166_QC_TCAEvidence.report.json',
        'PR166_QC_FillNoFillEvidence.report.json',
        'PR166_QC_LatencyEvidence.report.json',
        'PR166_QC_QueueRiskEvidence.report.json',
        'PR166_QC_CapacityCrowdingEvidence.report.json',
        'PR166_QC_OverfitFDRRetest.report.json',
        'PR166_QC_PortfolioUtility.report.json',
        'PR166_QC_ChampChallengerPaper.report.json',
        'PR166_QC_StillNegativeAfterCosts.report.json',
        'PR166_QC_ReplayPaperRepairLab.report.json',
        'PR166_QC_OwnerDashboardReview.report.json',
        'PR166_QC_ConnectorRouteReadiness.report.json',
    )
    primary_name = 'PR162E_Q_To_PR167.report.json'
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


def test_pr167_source_and_upstream_report_use_ledgers():
    sources = assert_report_contract("PR167_SourceSimParams.report.json")
    assert len(sources) >= 8
    assert any(row["official_flag"] for row in sources)
    assert any(row["non_official_flag"] for row in sources)
    assert all(row["source_locator_or_query"] for row in sources)
    assert all(row["candidate_values_extracted_count"] > 0 for row in sources)
    assert all(row["no_source_truth_acceptance_flag"] for row in sources)
    assert all(row["no_connector_binding_flag"] for row in sources)

    upstream = assert_report_contract("PR167_UpstreamReportUse.report.json")
    assert len(upstream) == len(c.STRICT_INPUT_REPORTS)
    assert all(row["consumed_by_pr167_flag"] for row in upstream)
    assert {row["source_pr"] for row in upstream} >= {"PR166-QC", "PR162E-Q", "PR165-D2"}


def test_pr167_budget_dispositions_and_structural_receipts_are_bounded():
    budget = records("PR167_SimBudget.report.json")[0]
    rows = assert_report_contract("PR167_SimEligibility.report.json", 559)
    actual = [row for row in rows if row["actual_sim_subset_flag"]]
    open_trade = [row for row in rows if row["open_trade_sim_route_flag"]]

    assert len(actual) == 96
    assert len(open_trade) == 61
    assert all(row["actual_sim_subset_flag"] for row in open_trade)
    assert budget["max_actual_sim_rows_default_ci"] == 96
    assert budget["max_route_variants_default_ci"] == 5
    assert budget["max_cancel_replace_attempts_default_ci"] == 4
    assert budget["no_unbounded_simulation_execution_flag"] is True
    assert all(row["simulator_disposition"] in c.SIMULATOR_DISPOSITIONS for row in rows)
    assert not (set(row["simulator_disposition"] for row in rows) & set(c.FORBIDDEN_SIMULATOR_DISPOSITIONS))
    assert all(row["simulator_quality_grade"] in c.SIMULATOR_QUALITY_GRADES for row in rows)
    assert all(row["classical_fallback_ref"] for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)

    bad = deepcopy(rows[0])
    bad["simulator_disposition"] = "METADATA_ONLY_SIMULATED"
    assert bad["simulator_disposition"] in c.FORBIDDEN_SIMULATOR_DISPOSITIONS


def test_pr167_order_intent_shadow_book_price_and_lifecycle_contracts():
    intents = assert_report_contract("PR167_OrderIntent.report.json", 559)
    assert all(row["order_intent_id"] for row in intents)
    assert all(row["YES_NO_side"] in {"YES", "NO"} for row in intents)
    assert all(0 <= row["normalized_price"] <= 1 for row in intents)
    assert all(row["no_live_authority_flag"] for row in intents)

    shadows = assert_report_contract("PR167_ShadowOrderAudit.report.json", 559)
    assert all(row["simulator_only_flag"] for row in shadows)
    assert all(row["real_order_id"] is None for row in shadows)
    assert all(row["real_fill_flag"] is False and row["real_pnl_flag"] is False for row in shadows)
    assert all(row["live_order_execution_flag"] is False for row in shadows)

    books = assert_report_contract("PR167_OrderBookState.report.json", 559)
    assert all(row["book_state_provenance"] in {"generated_structural", "structural_unavailable"} for row in books)
    assert all(row["no_live_market_call_flag"] for row in books)

    norms = assert_report_contract("PR167_PriceSideNorm.report.json", 559)
    assert all(row["probability_unit"] == "PROBABILITY_0_TO_1" for row in norms)
    assert all(row["TCA_unit"] == "NORMALIZED_PRICE_POINTS" for row in norms)

    lifecycle = assert_report_contract("PR167_OrderLifecycle.report.json", 559)
    assert all(row["lifecycle_states"] for row in lifecycle)
    assert all(row["simulated_not_real_flag"] for row in lifecycle)


def test_pr167_execution_models_are_materialized_not_label_only():
    for filename in (
        "PR167_OrderAggressionLadder.report.json",
        "PR167_CounterfactualRouteSim.report.json",
        "PR167_FillNoFillSim.report.json",
        "PR167_PartialFillSim.report.json",
        "PR167_QueuePositionSim.report.json",
        "PR167_QueueSurvivalSim.report.json",
        "PR167_LatencySim.report.json",
        "PR167_TCASim.report.json",
        "PR167_ImplementationShortfallSim.report.json",
        "PR167_AdverseSelectionSim.report.json",
        "PR167_CancelReplaceSim.report.json",
        "PR167_CapacityCrowdingSim.report.json",
        "PR167_SettlementFinalitySim.report.json",
        "PR167_ModelExecutionGap.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["counterfactual_route_ref"] for row in rows)
        assert all(row["total_TCA_candidate"] >= 0 for row in rows)
        assert all(row["fill_probability_score"] >= 0 for row in rows)
        assert all(row["not_profit_evidence_flag"] for row in rows)


def test_pr167_classical_quantum_hybrid_and_firewall_boundaries():
    classical = assert_report_contract("PR167_ClassicalFallbackSim.report.json", 559)
    assert all(row["classical_fallback_available"] for row in classical)
    quantum = assert_report_contract("PR167_QuantumHybridSim.report.json", 559)
    assert all(row["quantum_precompute_available"] for row in quantum)
    assert all(row["hybrid_selects_classical_executes_flag"] for row in quantum)
    assert all(row["quantum_backend_execution_flag"] is False for row in quantum)
    assert all(row["cloud_backend_execution_flag"] is False for row in quantum)

    firewall = assert_report_contract("PR167_SimPromotionFirewall.report.json", 559)
    assert all(row["live_ready_flag"] is False for row in firewall)
    assert all(row["future_live_authority_pr_required_flag"] for row in firewall)
    assert all(row["live_promotion_claim_flag"] is False for row in firewall)


def test_pr167_survivors_failures_champions_repair_and_coverage():
    survivors = assert_report_contract("PR167_SimSurvivorRegistry.report.json", 559)
    survivor_rows = [row for row in survivors if row["simulator_survival_flag"]]
    assert survivor_rows
    assert all("SURVIVED" in row["survival_reason"] for row in survivor_rows)
    assert all(row["downstream_retest_route_ref"] for row in survivor_rows)

    failures = assert_report_contract("PR167_SimFailureRegistry.report.json", 559)
    failure_rows = [row for row in failures if row["simulator_failure_reason"]]
    assert failure_rows
    assert all(row["primary_failure_reason"] != "NOT_FAILED_SIMULATOR_ROUTE" for row in failure_rows)
    assert all(row["repair_route_ref"] for row in failure_rows)

    champ = assert_report_contract("PR167_SimChampChallenger.report.json", 559)
    assert sum(1 for row in champ if row["simulator_champion"]) == summary()["simulator_champion_count"]
    assert sum(1 for row in champ if row["simulator_challenger"]) == summary()["simulator_challenger_count"]
    assert all(row["downstream_pr166_qc_retest_route_ref"] for row in champ if row["simulator_champion"] or row["simulator_challenger"])

    repairs = assert_report_contract("PR167_SimRetestRepair.report.json", 559)
    assert all(row["repair_family"] for row in repairs)
    assert all(row["not_profit_evidence_flag"] for row in repairs)
    coverage = assert_report_contract("PR167_SimCalibrationCoverage.report.json", 559)
    assert all(row["coverage_score"] >= 0 for row in coverage)


def test_pr167_dashboard_plugin_intake_connector_market_routes_are_safe():
    for filename in (
        "PR167_OwnerDashboardReview.report.json",
        "PR167_PluginNeeds.report.json",
        "PR167_OwnerAgentIntakeNeeds.report.json",
        "PR167_ConnectorRouteReady.report.json",
        "PR167_MarketPortability.report.json",
        "PR167_To_PR166_QC_Retest.report.json",
        "PR167_To_PR162E.report.json",
        "PR167_To_PR162F.report.json",
        "PR167_To_OwnerDashboard.report.json",
        "PR167_To_CloudSwitchboard.report.json",
        "PR167_To_FutureConnectors.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["no_live_authority_flag"] for row in rows)
        assert all(row["connector_semantic_binding_flag"] is False for row in rows)
        assert all(row["source_truth_acceptance_flag"] is False for row in rows)

    dashboard = records("PR167_OwnerDashboardReview.report.json")
    assert all(row["dashboard_ui_implemented_flag"] is False for row in dashboard)
    connector = records("PR167_ConnectorRouteReady.report.json")
    assert all(row["no_current_connector_binding_flag"] for row in connector)
    assert all(row["no_private_state_fetch_flag"] for row in connector)


def test_pr167_crosswalk_artifact_agents_and_summary_counts_match():
    crosswalk = assert_report_contract("PR167_ReportConsumerCrosswalk.report.json")
    mapped = {row["report_path"] for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        assert f"docs/master_plan/generated/{filename}" in mapped
    assert all(row["consuming_agent_ids"] or row["consuming_downstream_reports"] or row["terminal_flag"] for row in crosswalk)

    artifacts = assert_report_contract("PR167_ArtifactMap.report.json")
    assert any(row["artifact_type"] == "generated_schema" for row in artifacts)
    assert any(row["artifact_type"] == "generated_shard_report" for row in artifacts)
    assert all(row["consumed_by_agent"] or row["consumed_by_report"] or row["terminal_flag"] for row in artifacts)

    assert_report_contract("PR167_AgentWorkOrders.report.json", 559)
    dag = assert_report_contract("PR167_AgentDAG.report.json", 559)
    assert all(row["downstream_agent_refs"] for row in dag)
    no_orphan = assert_report_contract("PR167_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in no_orphan)

    final = summary()
    eligibility = records("PR167_SimEligibility.report.json")
    assert final["simulator_disposition_counts"] == dict(sorted(Counter(row["simulator_disposition"] for row in eligibility).items()))
    assert final["simulator_quality_grade_counts"] == dict(sorted(Counter(row["simulator_quality_grade"] for row in eligibility).items()))
