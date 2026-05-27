from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_registry


def test_pr157_split_reclassification_requires_basis():
    records = [
        record for record in pr154_registry()["records"]
        if record["source_population"] == c.SourcePopulation.PR154_SPLIT_RECLASSIFICATION.value
    ]
    assert len(records) == 33
    assert all(record["blocker_class"] == c.BlockerClass.SPLIT_RECLASSIFICATION_REQUIRED.value for record in records)
