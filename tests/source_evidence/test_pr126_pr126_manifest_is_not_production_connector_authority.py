from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    artifacts,
    manifest_records,
)


def test_pr126_pr126_manifest_is_not_production_connector_authority():
    report = artifacts()["main_report"]

    assert report["production_connector_semantic_implementation_count"] == 0
    assert report["production_connector_semantic_implementation_authority_count"] == 0
    assert report["fixture_outputs_marked_not_production_connector_semantic_implementation"]

    for record in manifest_records():
        assert record["production_connector_semantic_implementation_authority"] is False
        assert record["production_connector_use_allowed_flag"] is False
