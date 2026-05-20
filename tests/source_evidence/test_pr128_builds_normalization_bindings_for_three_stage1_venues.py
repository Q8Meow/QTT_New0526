from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    main_report,
    phase_bindings,
    stage1_venues,
    transition_bindings,
)


def test_pr128_builds_normalization_bindings_for_three_stage1_venues():
    report = main_report()

    assert report["repo_pr_label"] == "PR128"
    assert report["roadmap_pr_implemented"] == "PR110"
    assert report["fixture_stage1_venue_count"] == 3
    assert {record["venue_id"] for record in phase_bindings()} == stage1_venues()
    assert {record["venue_id"] for record in transition_bindings()} == stage1_venues()
    assert report["fixture_phase_binding_count"] == 30
    assert report["fixture_transition_binding_count"] == 24
    assert report["fixture_normalized_taxonomy_count"] == 11
