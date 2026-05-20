from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    binding_report,
    main_report,
    stage1_venues,
    taxonomy_record,
)


def test_pr128_prediction_markets_general_is_shared_scope_not_fourth_venue():
    report = main_report()
    taxonomy = taxonomy_record()

    assert report["prediction_markets_general_treated_as_shared_scope"] is True
    assert report["fixture_stage1_venue_count"] == 3
    assert set(taxonomy["venue_ids_in_scope"]) == stage1_venues()
    assert taxonomy["shared_scope_metadata_ids"] == ["PREDICTION_MARKETS_GENERAL"]
    assert "PREDICTION_MARKETS_GENERAL" not in {
        record["venue_id"] for record in binding_report()["phase_binding_records"]
    }
