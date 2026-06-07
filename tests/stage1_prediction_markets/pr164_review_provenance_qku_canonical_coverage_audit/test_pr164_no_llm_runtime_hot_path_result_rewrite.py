from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import summary


def test_pr164_no_llm_runtime_hot_path_result_rewrite():
    record = summary()
    assert record["llm_runtime_inference_count"] == 0
    assert record["llm_model_loading_count"] == 0
    assert record["llm_api_call_count"] == 0
    assert record["llm_result_rewrite_count"] == 0
