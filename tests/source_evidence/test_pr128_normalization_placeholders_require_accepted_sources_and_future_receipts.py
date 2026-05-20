from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    main_report,
    placeholder_records,
)


def test_pr128_normalization_placeholders_require_accepted_sources_and_future_receipts():
    assert main_report()["fixture_placeholder_normalization_count"] == 5
    runtime_required = {
        "cashflow_pnl_taxonomy",
        "reconciliation_taxonomy",
    }

    for record in placeholder_records():
        assert record["accepted_source_evidence_required_flag"] is True
        assert record["production_value_populated"] is False
        assert record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        assert record["production_cross_venue_normalization_authority"] is False
        assert record["future_pr_required_for_production_population"]
        assert record["runtime_receipt_required_flag"] is (
            record["normalization_dimension"] in runtime_required
        )
