from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    rejections_by_state,
)


def test_pr127_rejects_stale_or_superseded_source_support():
    report = main_report()

    assert report["stale_packet_rejection_count"] == 1
    assert report["superseded_packet_rejection_count"] == 1
    assert report["revalidation_required_rejection_count"] == 1
    assert rejections_by_state()["REJECTED_STALE_ACCEPTED_PACKET"][0][
        "rejection_reason_code"
    ] == "ACCEPTED_PACKET_STALE"
    assert rejections_by_state()["REJECTED_SUPERSEDED_ACCEPTED_PACKET"][0][
        "rejection_reason_code"
    ] == "ACCEPTED_PACKET_SUPERSEDED"
    assert rejections_by_state()["REJECTED_REVALIDATION_REQUIRED"][0][
        "rejection_reason_code"
    ] == "ACCEPTED_PACKET_REVALIDATION_REQUIRED"
