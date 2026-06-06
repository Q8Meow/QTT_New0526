def test_llm_runtime_model_api_prompt_are_excluded(records):
    rows = records("PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json")
    for row in rows[:250]:
        assert row["no_llm_runtime_inference"] is True
        assert row["no_llm_model_loading"] is True
        assert row["no_llm_api_call"] is True
        assert row["no_llm_prompt_execution"] is True
