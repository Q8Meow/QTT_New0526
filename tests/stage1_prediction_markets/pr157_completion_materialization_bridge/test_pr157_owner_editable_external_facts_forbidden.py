from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records, pr154_registry


def test_pr157_owner_editable_external_facts_forbidden():
    records = [*pr154_registry()["records"], *atomic_records()]
    external = [record for record in records if record["factual_external_value_flag"] is True]
    assert external
    assert all(record["external_fact_override_forbidden_flag"] is True for record in external)
