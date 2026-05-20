from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    binding_report,
    main_report,
)


def test_pr128_no_order_execution_or_order_authority():
    report = main_report()
    assert report["production_order_authority_count"] == 0
    assert report["order_authority_created"] is False

    for family in (
        "phase_binding_records",
        "transition_binding_records",
        "validation_receipts",
        "rejection_records",
    ):
        for record in binding_report()[family]:
            assert record["order_execution_allowed_flag"] is False
            assert record["order_routing_authority_allowed_flag"] is False
