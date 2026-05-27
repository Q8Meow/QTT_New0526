from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records, pr154_registry


def test_pr157_owner_editability_classification_for_all_targets_and_rows():
    assert all(record["owner_editability_class"] for record in pr154_registry()["records"])
    assert all(record["owner_editability_class"] for record in atomic_records())
