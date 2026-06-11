from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.report_writer import build_payloads

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_all_required_reports_and_schemas_exist(pr165_d2_summary):
    payloads = build_payloads(REPO_ROOT)
    assert set(payloads) == set(c.REPORT_FILENAMES)
    for filename in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / filename).exists()
    for filename in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / filename).exists()
    assert pr165_d2_summary["net_edge_adjusted_candidate_ranking_rows"] == 3985
    assert pr165_d2_summary["quantum_candidate_priority_v2_rows"] == 6502
