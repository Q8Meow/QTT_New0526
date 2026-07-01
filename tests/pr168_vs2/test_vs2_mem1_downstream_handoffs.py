from .test_support import read_jsonl


def test_mem1_handoff_is_non_authority_storage_future_only() -> None:
    for row in read_jsonl("mem1_handoff.jsonl"):
        assert row["future_MEM1_storage_required_flag"] is True
        assert row["durable_MEM1_storage_created_flag"] is False
        assert row["MEM1_query_api_created_flag"] is False


def test_downstream_handoff_carries_future_only_llm_dash_tg_fields() -> None:
    for row in read_jsonl("downstream_handoff.jsonl"):
        assert row["future_LLM_review_possible_flag"] is True
        assert row["future_LLM_order_authority_flag"] is False
        assert row["future_dashboard_consumer_pr"] == "PR169-DASH1"
        assert row["future_telegram_consumer_pr"] == "PR169-TG1"
        assert row["future_dashboard_runtime_created_by_vs2_flag"] is False
        assert row["future_telegram_runtime_created_by_vs2_flag"] is False
