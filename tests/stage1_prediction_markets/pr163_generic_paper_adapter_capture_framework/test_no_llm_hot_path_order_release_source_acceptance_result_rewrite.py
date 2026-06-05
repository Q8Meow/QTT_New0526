def test_no_llm_hot_path_order_release_source_acceptance_result_rewrite(summary, records):
    rows = records("PR163_NoLLMHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json")
    assert rows[0]["llm_runtime_inference_count"] == 0
    assert rows[0]["llm_order_release_count"] == 0
    assert rows[0]["llm_source_acceptance_count"] == 0
    assert rows[0]["llm_result_rewrite_count"] == 0
    assert summary["llm_hot_path_allowed_count"] == 0
