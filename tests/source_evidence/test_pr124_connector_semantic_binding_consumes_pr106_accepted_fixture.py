from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import (
    consumed,
    expected,
    report_and_failures,
)


def test_pr124_consumes_pr106_accepted_fixture_and_matches_expected_output():
    result = consumed()

    assert result["success_records"] == expected()["expected_success_records"]
    assert result["success_records"][0]["accepted_source_evidence_packet_id"] == (
        "PR123_ACCEPTED_PACKET_1B1209B53C6165BDCC7579DA"
    )
    assert result["success_records"][0]["venue_id"] == "KALSHI"
    assert result["success_records"][0]["target_field_path"] == (
        "stage1.kalshi.order_entry.fixture_field"
    )


def test_pr124_validation_report_has_no_failures_for_fixture_suite():
    report, failures = report_and_failures()

    assert failures == []
    assert report["pr106_acceptance_artifacts_consumed"] is True
    assert report["fixture_connector_binding_success_count"] == 1
    assert report["fixture_connector_binding_rejection_count"] == 5
