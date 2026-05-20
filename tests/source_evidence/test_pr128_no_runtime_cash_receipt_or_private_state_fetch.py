from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    binding_report,
    main_report,
)


def test_pr128_no_runtime_cash_receipt_or_private_state_fetch():
    report = main_report()
    assert report["runtime_cash_receipts_created_count"] == 0
    assert report["private_state_fetch_created_count"] == 0

    for family in (
        "phase_binding_records",
        "transition_binding_records",
        "validation_receipts",
        "rejection_records",
    ):
        for record in binding_report()[family]:
            assert record["runtime_cash_receipt_allowed_flag"] is False
            assert record["private_state_fetch_allowed_flag"] is False
