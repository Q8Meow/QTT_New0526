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


def test_report_manifest_lists_root_reports_and_shards(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_ReportManifest.report.json"]
    root_rows = [row for row in rows if row["manifest_entry_class"] == "ROOT_REPORT"]
    shard_rows = [row for row in rows if row["manifest_entry_class"] == "SHARD_REPORT"]
    assert {row["report_name"] + ".report.json" for row in root_rows} == set(c.REPORT_FILENAMES)
    expected_shards = 0
    for row in root_rows:
        expected_shards += row["shard_count"]
    assert len(shard_rows) == expected_shards
    assert all(row["parent_report_name"] for row in shard_rows)
