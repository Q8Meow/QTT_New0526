from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    main_report,
    rejections_by_state,
)


def test_pr128_rejects_missing_lifecycle_model():
    assert main_report()["missing_lifecycle_model_rejection_count"] == 1
    rejection = rejections_by_state()["REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL"][0]
    assert rejection["rejection_reason_code"] == (
        "ACTIVE_STAGE1_VENUE_LIFECYCLE_MODEL_SET_MISMATCH"
    )
