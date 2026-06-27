from __future__ import annotations

from ._helpers import rows


def test_vs1_fixtures_cover_required_cases_and_platforms():
    fixtures = rows("trade_target_fixtures.jsonl")
    snapshots = rows("market_condition_snapshots.jsonl")

    assert {row["fixture_case"] for row in fixtures} == {
        "positive_edge_fixture",
        "negative_edge_fixture",
        "thin_book_fixture",
        "crowded_capacity_fixture",
        "portfolio_conflict_fixture",
    }
    assert {row["platform_id"] for row in fixtures} == {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"}
    assert all(row["source_class"] == "VS1_SYNTHETIC_FIXTURE_ONLY" for row in fixtures)
    assert len(snapshots) == len(fixtures)
