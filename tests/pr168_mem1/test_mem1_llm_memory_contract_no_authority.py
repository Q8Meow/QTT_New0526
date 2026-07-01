from .test_support import read_jsonl


def test_llm_contracts_are_read_only_and_stable_named() -> None:
    for name in ("llm_memory_view_contract.jsonl", "llm_memory_critic_payload_contract.jsonl", "llm_agent_task_contract.jsonl"):
        row = read_jsonl(name)[0]
        assert row["contract_status"] == "PRODUCED_BY_MEM1_READY_FOR_DOWNSTREAM_CONSUMER_ADOPTION"
        assert row["current_pr_consumer_runtime_enabled_flag"] is False
        assert row["llm_runtime_created_flag"] is False
        assert row["llm_source_truth_authority_flag"] is False
        assert row["llm_order_authority_flag"] is False
        assert row["llm_risk_gate_override_flag"] is False
