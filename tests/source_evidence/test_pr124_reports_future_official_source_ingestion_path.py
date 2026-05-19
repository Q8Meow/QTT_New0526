from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import (
    FUTURE_OFFICIAL_SOURCE_INGESTION_PATH,
    report_and_failures,
)


def test_pr124_report_records_future_official_source_ingestion_path():
    report, failures = report_and_failures()

    assert failures == []
    assert report["future_official_source_ingestion_path_recorded"] is True
    assert report["future_official_source_ingestion_path"] == list(
        FUTURE_OFFICIAL_SOURCE_INGESTION_PATH
    )
    assert report["production_values_filled_by_later_official_source_prs"] is True
    assert report["production_connector_semantic_binding_count"] == 0
    assert report["master_plan_modified"] is False
    assert report["atomicrows_bundle_created"] is False
    assert report["atomicrows_sha_created"] is False
