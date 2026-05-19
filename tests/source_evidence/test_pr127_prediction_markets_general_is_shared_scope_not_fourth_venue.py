from tests.source_evidence.pr127_execution_lifecycle_support import (
    artifacts,
    main_report,
    model_records,
)


def test_pr127_prediction_markets_general_is_shared_scope_not_fourth_venue():
    shared = artifacts()["builder_report"]["shared_scope_metadata_records"]

    assert main_report()["shared_scope_metadata_count"] == 1
    assert shared[0]["platform_scope"] == "PREDICTION_MARKETS_GENERAL"
    assert shared[0]["venue_specific_lifecycle_model_allowed"] is False
    assert "PREDICTION_MARKETS_GENERAL" not in {
        record["venue_id"] for record in model_records()
    }
