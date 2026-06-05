from src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun.authority_policy import (
    FILL_ACTION_FAMILIES,
)


def test_missing_data_binding_action_queue(summary, records):
    rows = records("PR162R_MissingDataBindingActionQueue.report.json")
    assert len(rows) == summary["missing_data_binding_action_count"]
    assert rows
    for row in rows[:50]:
        assert row["fill_action_family"] in FILL_ACTION_FAMILIES
        assert row["missing_field"]
        assert row["responsible_agent"]
        assert row["suggested_source_classes"]
        assert row["downstream_consumer"]
        assert row["priority_score"] > 0
        assert row["owner_override_cannot_fabricate_external_fact"] is True
