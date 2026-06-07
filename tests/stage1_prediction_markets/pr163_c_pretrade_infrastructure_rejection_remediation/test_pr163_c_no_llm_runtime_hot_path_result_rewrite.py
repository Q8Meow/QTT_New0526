from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_no_llm_runtime_hot_path_result_rewrite():
    audit = load_records("PR163_C_NoLLMRuntimeHotPathResultRewriteAudit.report.json")[0]
    assert audit["llm_runtime_inference_count"] == 0
    assert audit["llm_result_rewrite_count"] == 0
    assert summary()["llm_runtime_rewrite_count"] == 0
