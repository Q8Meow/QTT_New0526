from __future__ import annotations


def test_probability_edge_units_and_yes_no_symmetry(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json"]
    assert len(rows) == 3985
    first = rows[0]
    assert first["unit_ref"]["market_implied_probability"] == "PROBABILITY_POINT"
    assert first["yes_no_symmetric_price_check"] is True
    assert abs(first["yes_price_cents"] + first["no_price_cents"] - 100.0) < 0.00001
