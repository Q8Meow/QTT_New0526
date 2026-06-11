from __future__ import annotations


def test_capacity_crowding_correlation_controls_are_bounded(pr165_d2_records):
    row = pr165_d2_records["PR165_D2_CapacityCrowdingCorrelationSelectionLedger.report.json"][0]
    assert 0 <= row["capacity_score"] <= 1
    assert 0 <= row["crowding_penalty"] <= 1
    assert row["correlation_cluster_id"]
