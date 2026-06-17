from __future__ import annotations

from copy import deepcopy

from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark import constants as c
from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark.validator import validate_artifacts

from .helpers import REPO_ROOT, assert_report_contract, records, summary


def test_pr166_qb_validator_passes_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr166_qb_consumes_expected_upstream_handoffs_and_counts():
    final = summary()
    assert final["consumed_pr166_qb_handoff_rows"] == 559
    assert final["input_record_counts"]["PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json"] == 559
    assert final["input_record_counts"]["PR166_Q_UniversalArtifactConsumerMap.report.json"] == 685
    assert_report_contract("PR166_QB_Eligibility.report.json", 559)
    assert_report_contract("PR166_QB_RaceArb.report.json", 559)


def test_pr166_qb_budget_subset_is_capped_and_deterministic():
    final = summary()
    subset = [row for row in records("PR166_QB_SubsetSelection.report.json") if row["benchmark_subset_flag"]]
    assert len(subset) == 64
    assert final["benchmark_subset_count"] == 64
    assert all(row["iterations_used"] <= c.BENCHMARK_CAPS["max_optimizer_iterations_default_ci"] for row in subset)
    assert all(row["samples_or_reads_used"] <= c.BENCHMARK_CAPS["max_samples_or_reads_default_ci"] for row in subset)
    assert all(row["seed_count"] <= c.BENCHMARK_CAPS["max_random_seeds_default_ci"] for row in subset)
    by_family = {}
    for row in subset:
        by_family[row["model_family"]] = by_family.get(row["model_family"], 0) + 1
    assert all(count <= c.BENCHMARK_CAPS["max_rows_per_family_default_ci"] for count in by_family.values())
    assert [row["deterministic_sort_key"] for row in subset] == sorted(row["deterministic_sort_key"] for row in subset)


def test_pr166_qb_rejects_forbidden_benchmark_dispositions_and_modes():
    rows = deepcopy(records("PR166_QB_Eligibility.report.json"))
    rows[0]["benchmark_disposition"] = "METADATA_ONLY_BENCHMARKED"
    assert rows[0]["benchmark_disposition"] in c.FORBIDDEN_BENCHMARK_DISPOSITIONS
    rows[1]["benchmark_execution_mode"] = "CLOUD_BACKEND_EXECUTION"
    assert rows[1]["benchmark_execution_mode"] in c.FORBIDDEN_EXECUTION_MODES


def test_pr166_qb_fairness_normalizes_objective_direction_and_budget():
    rows = assert_report_contract("PR166_QB_FairnessNorm.report.json", 559)
    assert all(row["objective_direction_normalized"] == "MAXIMIZE_EXECUTION_ADJUSTED_EDGE" for row in rows)
    assert all(row["minmax_sign"] == 1 for row in rows)
    assert all(row["same_budget_comparison_flag"] is True for row in rows)
    assert all(row["energy_to_edge_translation"] for row in rows)
    assert all(row["paired_comparison_group_id"] for row in rows)


def test_pr166_qb_race_arbitration_keeps_classical_fallback_nonlive():
    rows = assert_report_contract("PR166_QB_RaceArb.report.json", 559)
    assert all(row["classical_fallback_required_flag"] is True for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)
    assert all(row["future_live_route_candidate_flag"] is False for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)
    assert all(row["winning_nonlive_route"] != "TRUE_QUANTUM_STRUCTURAL_PAPER_ONLY" for row in rows)


def test_pr166_qb_qaoa_and_sampling_vqe_are_dependency_unavailable_noexec():
    for filename in ("PR166_QB_QAOAReceipt.report.json", "PR166_QB_SamplingVQEReceipt.report.json"):
        rows = assert_report_contract(filename, 559)
        assert all(row["benchmark_disposition"] == "BENCHMARK_STRUCTURAL_ONLY_DEPENDENCY_UNAVAILABLE" for row in rows)
        assert all(row["benchmark_executed_flag"] is False for row in rows)
        assert all(row["credential_access_flag"] is False for row in rows)
        assert all(row["cloud_backend_execution_flag"] is False for row in rows)
        assert all(row["quantum_backend_execution_flag"] is False for row in rows)


def test_pr166_qb_repair_lab_routes_negative_candidates_without_profit_evidence():
    rows = assert_report_contract("PR166_QB_QuantumRepairLab.report.json", 559)
    assert all(row["repair_row_id"] for row in rows)
    assert all(row["not_profit_evidence_flag"] is True for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)
    assert all(row["downstream_pr166_qc_route_ref"] or row["downstream_pr162e_q_route_ref"] for row in rows)


def test_pr166_qb_cloud_switchboard_and_owner_controls_default_off():
    for filename in ("PR166_QB_CloudSwitchReady.report.json", "PR166_QB_OwnerQuantumControlReady.report.json"):
        rows = assert_report_contract(filename, 5)
        assert all(row["default_mode"] == "OFF" for row in rows)
        assert all(row["credential_access_allowed_flag"] is False for row in rows)
        assert all(row["backend_execution_allowed_flag"] is False for row in rows)
        assert all(row["live_order_authority_flag"] is False for row in rows)
        assert all(row["no_backend_execution_flag"] is True for row in rows)
    owner_rows = records("PR166_QB_OwnerQuantumControlReady.report.json")
    assert all(row["dashboard_implementation_required_flag"] is True for row in owner_rows)
    assert all(row["dashboard_ui_implemented_flag"] is False for row in owner_rows)


def test_pr166_qb_market_portability_is_route_only():
    rows = assert_report_contract("PR166_QB_MarketPortability.report.json", 559)
    assert all(row["stage1_prediction_market_flag"] is True for row in rows)
    assert all(row["future_market_portability_flag"] is True for row in rows)
    assert all(row["no_current_connector_binding_flag"] is True for row in rows)
    assert all(row["no_live_authority_flag"] is True for row in rows)


def test_pr166_qb_agent_dag_and_artifact_map_have_no_orphans():
    assert_report_contract("PR166_QB_AgentWorkOrders.report.json", 559)
    assert_report_contract("PR166_QB_AgentDAG.report.json", 559)
    proof_rows = assert_report_contract("PR166_QB_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in proof_rows)
    artifact_rows = assert_report_contract("PR166_QB_ArtifactMap.report.json")
    assert artifact_rows
    assert all(row["artifact_path"] for row in artifact_rows)
    assert all(row["consumed_by_module"] for row in artifact_rows)
