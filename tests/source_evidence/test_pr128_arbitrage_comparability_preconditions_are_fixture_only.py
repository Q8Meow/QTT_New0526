from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    arbitrage_preconditions,
    main_report,
)


def test_pr128_arbitrage_comparability_preconditions_are_fixture_only():
    assert main_report()["fixture_arbitrage_precondition_count"] == 3
    assert main_report()["production_arbitrage_comparability_authority_count"] == 0

    for record in arbitrage_preconditions():
        assert record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        assert record["precondition_authority_class"] == "NOT_ARBITRAGE_AUTHORITY"
        assert record["production_arbitrage_comparability_authority"] is False
        assert record["apparent_price_gap_arbitrage_claim_allowed"] is False
        assert record["production_order_authority_allowed"] is False
