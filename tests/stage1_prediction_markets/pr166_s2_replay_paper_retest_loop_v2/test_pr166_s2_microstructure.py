from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_microstructure_records_prediction_market_fields():
    row = assert_report_rows("PR166_S2_MicrostructureLedger.report.json", 3215)[0]
    assert row["side"] in {"YES", "NO"}
    assert row["top_of_book_spread"] >= 0
    assert "binary_price_symmetry_check" in row
