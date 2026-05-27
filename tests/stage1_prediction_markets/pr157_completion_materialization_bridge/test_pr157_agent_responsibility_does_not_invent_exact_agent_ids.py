from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records, pr154_registry


def test_pr157_agent_responsibility_does_not_invent_exact_agent_ids():
    records = [*pr154_registry()["records"], *atomic_records()]
    assert all(record["exact_agent_id_or_null"] is None for record in records)
