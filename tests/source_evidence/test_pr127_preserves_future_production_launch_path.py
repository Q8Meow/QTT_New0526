from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    model_records,
)


def test_pr127_preserves_future_production_launch_path():
    report = main_report()

    assert report["future_production_launch_path_preserved"] is True
    assert report["future_official_source_production_path_recorded"] is True
    assert report["production_values_filled_by_later_official_source_prs"] is True
    assert "PR127 per-venue execution lifecycle model builder" in (
        report["future_official_source_production_path"]
    )
    for model in model_records():
        assert model["future_production_launch_path_preserved"] is True
