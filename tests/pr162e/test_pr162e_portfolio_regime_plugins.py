from tests.pr162e.helpers import plugin_rows


def test_portfolio_and_regime_fields_are_materialized():
    row = plugin_rows()[0]
    assert row["portfolio_diversification"]["risk_budget"]
    assert row["condition_fingerprint"]["event_lifecycle_stage"] is not None
