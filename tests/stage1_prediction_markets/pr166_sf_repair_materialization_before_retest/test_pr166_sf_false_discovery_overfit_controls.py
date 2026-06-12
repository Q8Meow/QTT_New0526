from .conftest import assert_rows


def test_pr166_sf_false_discovery_controls_are_carried_forward(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairOverfitControl.report.json")
    for row in rows[:100]:
        assert row["num_related_trials"] >= 1
        assert row["effective_independent_trial_count"] >= 1
        assert "repair_allowed_after_penalty" in row
