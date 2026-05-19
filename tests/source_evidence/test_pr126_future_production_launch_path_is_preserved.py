from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    artifacts,
    manifest_records,
)


def test_pr126_future_production_launch_path_is_preserved():
    report = artifacts()["main_report"]

    assert report["future_official_source_production_path_recorded"] is True
    assert report["future_production_launch_path_preserved"] is True
    assert report["production_values_filled_by_later_official_source_prs"] is True
    assert "PR126 connector semantic implementation gate" in (
        report["future_official_source_production_path"]
    )

    for record in manifest_records():
        assert record["future_production_launch_path_preserved"] is True
        assert record["production_values_filled_by_later_official_source_prs"] is True
