from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion import constants as c


def test_pr162d_r1_mines_master_plan_formula_algorithm_parameter_quantum_content(summary, records):
    assert summary["master_plan_formula_mentions_scanned_count"] >= c.THRESHOLDS["master_plan_formula_mentions_scanned_count"]
    assert summary["master_plan_algorithm_mentions_scanned_count"] >= c.THRESHOLDS["master_plan_algorithm_mentions_scanned_count"]
    assert summary["master_plan_parameter_pack_mentions_scanned_count"] >= c.THRESHOLDS["master_plan_parameter_pack_mentions_scanned_count"]
    assert summary["master_plan_extracted_formula_candidate_count"] >= c.THRESHOLDS["master_plan_extracted_formula_candidate_count"]
    assert summary["master_plan_extracted_algorithm_candidate_count"] >= c.THRESHOLDS["master_plan_extracted_algorithm_candidate_count"]
    assert summary["master_plan_extracted_quantum_candidate_count"] >= c.THRESHOLDS["master_plan_extracted_quantum_candidate_count"]
    assert records("PR162D_R1_MasterPlanParameterPackExtractionLedger.report.json")
    assert records("PR162D_R1_MasterPlanQuantumFormulaExtractionLedger.report.json")
