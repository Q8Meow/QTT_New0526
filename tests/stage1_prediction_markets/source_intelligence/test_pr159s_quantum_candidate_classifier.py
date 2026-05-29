from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_quantum_candidate_classifier_metadata_only():
    payload = load(c.QUANTUM_CANDIDATE_READINESS_DELTA_PATH)
    assert payload["record_count"] == 868
    assert payload["quantum_relevant_candidate_count"] > 0
    assert all(record["quantum_backend_execution_performed_in_pr159s"] is False for record in payload["records"])
    assert all(record["quantum_simulator_execution_performed_in_pr159s"] is False for record in payload["records"])

