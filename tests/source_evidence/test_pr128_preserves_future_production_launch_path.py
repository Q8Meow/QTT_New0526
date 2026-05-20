from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    binding_report,
    main_report,
)


def test_pr128_preserves_future_production_launch_path():
    report = main_report()

    assert report["future_production_launch_path_preserved"] is True
    assert report["production_values_filled_by_later_official_source_prs"] is True
    assert report["future_official_source_production_path_recorded"] is True
    assert "PR113 credential alias and secret no-capture readiness gate" in report[
        "future_official_source_production_path"
    ]
    for record in binding_report()["phase_binding_records"]:
        assert record["future_production_launch_path_preserved"] is True
