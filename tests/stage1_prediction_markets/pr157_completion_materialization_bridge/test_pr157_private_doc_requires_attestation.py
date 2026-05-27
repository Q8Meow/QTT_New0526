from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_registry


def test_pr157_private_doc_requires_attestation():
    records = [
        record for record in pr154_registry()["records"]
        if record["source_population"] == c.SourcePopulation.PR154_PRIVATE_DOC_ATTESTATION.value
    ]
    assert len(records) == 6
    assert all(record["blocker_class"] == c.BlockerClass.PRIVATE_DOC_ATTESTATION_REQUIRED.value for record in records)
