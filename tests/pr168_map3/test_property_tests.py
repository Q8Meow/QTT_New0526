from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_property_test_receipts_exist() -> None:
    rows = records("PR168_MAP3_PropertyTests.report.json")
    assert len(rows) == summary()["formula_property_test_row_count"]
    assert all(row["invariant_status"] for row in rows)
