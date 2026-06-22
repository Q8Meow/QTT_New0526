from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_negative_to_candidate_repair_routes_without_relabeling_profit() -> None:
    rows = records("PR168_MAP3_NegativeToCandidateRepair.report.json")
    assert rows
    assert all(row["not_profit_proof_flag"] is True for row in rows)
