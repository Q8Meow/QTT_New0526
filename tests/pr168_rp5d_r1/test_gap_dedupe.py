from ._helpers import read_jsonl


def test_gap_dedupe_groups_gap_families() -> None:
    rows = read_jsonl("gap_dedupe.jsonl")
    assert rows
    assert all(row["deduped_for_execution_contract_completion_only_flag"] for row in rows)
