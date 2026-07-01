from .test_support import read_jsonl


def test_failure_memory_is_condition_scoped_caution_only() -> None:
    for row in read_jsonl("failure_memory.jsonl"):
        assert row["market_context_key"]
        assert row["failure_reason_codes"]
        assert row["similar_context_only_flag"] is True
        assert row["global_formula_ban_flag"] is False
        assert row["global_qku_ban_flag"] is False
        assert row["formula_mutation_required_flag"] is False
