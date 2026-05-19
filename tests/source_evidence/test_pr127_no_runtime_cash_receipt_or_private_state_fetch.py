from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    model_records,
)


def test_pr127_no_runtime_cash_receipt_or_private_state_fetch():
    report = main_report()

    assert report["runtime_cash_receipts_created_count"] == 0
    assert report["private_state_fetch_created_count"] == 0
    for model in model_records():
        assert model["runtime_cash_receipt_allowed_flag"] is False
        assert model["private_state_fetch_allowed_flag"] is False
