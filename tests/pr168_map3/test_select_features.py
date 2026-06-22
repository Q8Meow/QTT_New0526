from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_select_features_route_to_rank2_without_champion_status() -> None:
    rows = records("PR168_MAP3_SelectFeatures.report.json")
    assert rows
    assert all(row["rank2_consumption_route"] == "PR168_RANK2_EVIDENCE_RANKING" for row in rows)
    assert all(row["champion_allowed_flag"] is False for row in rows)
