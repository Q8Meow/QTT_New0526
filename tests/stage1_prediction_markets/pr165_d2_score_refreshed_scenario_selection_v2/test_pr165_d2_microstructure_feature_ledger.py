from __future__ import annotations


def test_microstructure_rows_have_execution_realism_fields(pr165_d2_records):
    row = pr165_d2_records["PR165_D2_MicrostructureFeatureLedger.report.json"][0]
    assert row["spread_cents"] > 0
    assert row["order_book_depth_top_10"] >= row["order_book_depth_top_1"]
    assert 0 <= row["expected_fill_probability_proxy"] <= 1
