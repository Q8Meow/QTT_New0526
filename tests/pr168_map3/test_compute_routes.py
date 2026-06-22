from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_every_formula_has_computability_route() -> None:
    rows = records("PR168_MAP3_ComputeRoutes.report.json")
    assert rows
    assert all(row["computability_route"] for row in rows)
