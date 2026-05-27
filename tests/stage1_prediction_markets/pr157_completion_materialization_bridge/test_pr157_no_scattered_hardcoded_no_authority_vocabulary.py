from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records, pr154_registry


def test_pr157_no_scattered_hardcoded_no_authority_vocabulary():
    for record in [*pr154_registry()["records"][:20], *atomic_records()[:20]]:
        assert set(record["no_authority_confirmation"].values()) == {False}
        assert record["authority_profile_ids"]
