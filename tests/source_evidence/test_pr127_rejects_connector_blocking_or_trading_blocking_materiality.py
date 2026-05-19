from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    rejections_by_state,
)


def test_pr127_rejects_connector_blocking_or_trading_blocking_materiality():
    report = main_report()

    assert report["connector_blocking_materiality_rejection_count"] == 1
    assert report["trading_blocking_materiality_rejection_count"] == 1
    assert rejections_by_state()["REJECTED_CONNECTOR_BLOCKING_MATERIALITY"][0][
        "rejection_reason_code"
    ] == "CONNECTOR_BLOCKING_MATERIALITY"
    assert rejections_by_state()["REJECTED_TRADING_BLOCKING_MATERIALITY"][0][
        "rejection_reason_code"
    ] == "TRADING_BLOCKING_MATERIALITY"
