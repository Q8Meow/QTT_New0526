from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_formula_family_matrix_covers_or_gap_routes_minimum_families() -> None:
    rows = records("PR168_MAP3_FamilyMatrix.report.json")
    assert len(rows) >= 12
    assert all(row["coverage_state"] in {"COVERED", "EXACT_GAP_ROUTED"} for row in rows)
    data = summary()
    assert data["mandatory_formula_family_covered_count"] + data[
        "mandatory_formula_family_gap_routed_count"
    ] >= 12
