from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report, rows


def test_candidate_usability_gains_cover_formula_source_and_data_repairs():
    assert_recovery1_valid()
    audit = report("PR168_RECOVERY1_ProductivityAudit.report.json")["records"]
    gains = rows("candidate_usability_gain")
    families = {row["gain_family"] for row in gains if row.get("candidate_usable_flag")}

    assert audit["actual_usability_improvement_flag"] is True
    assert "EXPRESSION_FORMULA" in families
    assert "SOURCE_PROVENANCE" in families
    assert "DATA_PRECISION" in families
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in gains)


def test_source_formula_data_results_remain_candidate_only():
    assert_recovery1_valid()
    result_rows = rows("source_formula_data_repair_result")

    assert result_rows
    assert all(row["candidate_only_flag"] is True for row in result_rows)
    assert all(row["accepted_truth_flag"] is False for row in result_rows)
    assert all(row["operational_use"] for row in result_rows)
