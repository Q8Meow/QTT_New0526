from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_quantum_provider_docs_metadata_only():
    payload = report(c.QUANTUM_METADATA_PATH)
    assert payload["record_count"] >= 1
    assert all(item["metadata_only_no_backend_execution"] is True for item in payload["records"])

