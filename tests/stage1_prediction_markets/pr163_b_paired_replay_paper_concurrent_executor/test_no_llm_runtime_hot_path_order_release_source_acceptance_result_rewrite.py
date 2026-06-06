def test_no_llm_runtime_hot_path_order_release_source_acceptance_result_rewrite(summary):
    for field in ("llm_runtime_inference_count", "llm_model_loading_count", "llm_api_call_count", "llm_prompt_execution_count", "llm_order_release_count", "llm_source_acceptance_count", "llm_result_rewrite_count"):
        assert summary[field] == 0
