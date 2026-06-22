from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_dryruns_are_candidate_only_nonproof() -> None:
    rows = records("PR168_MAP3_FormulaDryRun.report.json")
    assert rows
    assert all(row["synthetic_unit_test_only_non_proof_flag"] is True for row in rows)
    assert all(row["accepted_truth_flag"] is False for row in rows)
