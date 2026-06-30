from ._helpers import rows


def test_future_mem1_contract_is_hint_only() -> None:
    for row in rows("rank_mem1_contract_hint.jsonl"):
        assert row["future_MEM1_contract_hint_only_flag"] is True
        assert row["durable_MEM1_storage_created_flag"] is False

