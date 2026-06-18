from tests.pr162e.helpers import plugin_rows


def test_condition_memory_has_regime_fingerprint():
    fp = plugin_rows()[0]["condition_fingerprint"]
    assert fp["venue"] == "PREDICTION_MARKET"
    assert "prior_no_fill_stale_book_state" in fp
