from ._helpers import read_jsonl


def test_search_trace_records_generated_retained_and_discarded_counts_by_mode() -> None:
    rows = read_jsonl("search_trace.jsonl")
    assert rows
    assert sum(row["candidate_count_generated"] for row in rows) == len(read_jsonl("tmp_previews.jsonl"))
    assert sum(row["candidate_count_retained"] for row in rows) == len(read_jsonl("topk.jsonl"))
    assert all(row["random_seed_used_flag"] is False for row in rows)
    assert all(row["full_cartesian_generation_flag"] is False for row in rows)
