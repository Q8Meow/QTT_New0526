from __future__ import annotations

from ._helpers import d, rows


def test_vs1_capacity_and_crowding_penalize_thin_and_crowded_books():
    receipts = rows("capacity_crowding_receipts.jsonl")
    thin = [row for row in receipts if row["fixture_id"].startswith("VS1_FIXTURE_0003")]
    crowded = [row for row in receipts if row["fixture_id"].startswith("VS1_FIXTURE_0004")]

    assert thin and crowded
    assert any(row["thin_book_flag"] is True for row in thin)
    assert any(d(row["capacity_penalty_cash"]) > 0 for row in crowded)
    assert any(d(row["crowding_penalty_cash"]) > 0 for row in crowded)
