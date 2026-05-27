from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_registry


def test_pr157_retry_records_do_not_execute_future_source_retry_scope():
    retry = [
        record for record in pr154_registry()["records"]
        if record["source_population"] == c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value
    ]
    assert len(retry) == 34
    assert all(record["blocker_class"] == c.BlockerClass.PUBLIC_EXTERNAL_RETRY_REQUIRED.value for record in retry)
    assert all(record["no_authority_confirmation"]["source_retrieval_execution_created"] is False for record in retry)
