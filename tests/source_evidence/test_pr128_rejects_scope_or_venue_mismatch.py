from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    main_report,
    rejections_by_state,
)


def test_pr128_rejects_scope_or_venue_mismatch():
    assert main_report()["scope_or_venue_mismatch_rejection_count"] == 1
    rejection = rejections_by_state()["REJECTED_SCOPE_OR_VENUE_MISMATCH"][0]
    assert rejection["rejection_reason_code"] == "HANDOFF_NORMALIZATION_DIMENSION_MISMATCH"
