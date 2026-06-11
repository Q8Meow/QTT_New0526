from __future__ import annotations


def test_false_discovery_controls_include_trial_counts(pr165_d2_records):
    row = pr165_d2_records["PR165_D2_FalseDiscoveryOverfitSelectionControl.report.json"][0]
    assert row["num_related_trials"] >= row["effective_independent_trial_count"] >= 1
    assert row["reason_codes"]
