from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    model_records,
    stage1_venues,
)


def test_pr127_builds_fixture_lifecycle_models_for_three_stage1_venues():
    report = main_report()
    models = model_records()

    assert report["roadmap_pr_implemented"] == "PR109"
    assert report["fixture_stage1_venue_count"] == 3
    assert report["fixture_lifecycle_model_count"] == 3
    assert {record["venue_id"] for record in models} == stage1_venues()
    assert report["fixture_lifecycle_phase_count"] == 30
    assert report["fixture_lifecycle_transition_count"] == 24

    for model in models:
        assert len(model["lifecycle_phase_records"]) == 10
        assert len(model["lifecycle_transition_records"]) == 8
        assert model["lifecycle_model_state"] == "READY_FOR_PR127_FIXTURE_SCOPE_MODEL"
