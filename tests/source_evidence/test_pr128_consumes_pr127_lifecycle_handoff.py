from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    binding_report,
    main_report,
)


def test_pr128_consumes_pr127_lifecycle_handoff():
    report = main_report()
    binding = binding_report()

    assert report["pr127_execution_lifecycle_artifacts_consumed"] is True
    assert binding["source_pr127_handoff_id"] == (
        "PR127_CROSS_VENUE_NORMALIZATION_HANDOFF_FIXTURE_V1"
    )
    assert binding["source_pr127_lifecycle_model_ids"] == [
        "PR127_LIFECYCLE_MODEL_FORECASTEX_IBKR_FIXTURE",
        "PR127_LIFECYCLE_MODEL_KALSHI_FIXTURE",
        "PR127_LIFECYCLE_MODEL_POLYMARKET_FIXTURE",
    ]
