from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_builds_fixture_market_data_ingest_for_three_stage1_venues():
    report = support.main_report()
    venue_inputs = {
        record["venue_id"] for record in support.adapter_inputs() if record.get("venue_id")
    }
    venue_bindings = {
        record["venue_id"] for record in support.adapter_bindings() if record.get("venue_id")
    }

    assert venue_inputs == set(policy.STAGE1_VENUE_IDS)
    assert venue_bindings == set(policy.STAGE1_VENUE_IDS)
    assert report["venue_specific_adapter_input_count"] == 24
    assert report["adapter_binding_count_by_scope"]["KALSHI"] == 1
    assert report["adapter_binding_count_by_scope"]["POLYMARKET"] == 1
    assert report["adapter_binding_count_by_scope"]["FORECASTEX_IBKR"] == 1
