from pathlib import Path

from src.qtt.stage1_prediction_markets.pr165_d_scenario_qku_combination_selection.report_builder import build_payloads
from src.qtt.stage1_prediction_markets.pr165_d_scenario_qku_combination_selection.validators import validate_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pr165_d_payloads_conserve_pr165_c_candidate_universe():
    payloads = build_payloads(REPO_ROOT)
    summary = payloads["PR165_D_FinalSummary.report.json"]["records"][0]

    assert summary["selection_coverage_rows"] == 6502
    assert summary["candidate_feature_vector_rows"] == 6502
    assert summary["scenario_combination_candidate_rows"] == 6502
    assert summary["retest_batch_selection_rows"] == 6497
    assert summary["repair_before_retest_selection_rows"] == 2512
    assert summary["selected_excluded_reason_rows"] == 6502
    assert summary["false_discovery_control_rows"] == 6502
    assert summary["point_in_time_selection_audit_rows"] == 6502
    assert summary["quantum_selection_route_rows"] == 6502
    assert summary["metadata_only_rows"] == 0
    assert summary["placeholder_rows"] == 0
    assert summary["unknown_status_rows"] == 0
    assert summary["orphan_counts_all_zero"] is True
    assert summary["authority_counts_all_zero"] is True


def test_pr165_d_generated_artifacts_validate_after_build():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:10]
