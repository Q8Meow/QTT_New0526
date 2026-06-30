from ._helpers import rows


def test_positive_edge_search_identifies_batch_or_gap() -> None:
    row = rows("pos_edge_search.jsonl")[0]
    assert row["positive_edge_found_flag"] is True or row["closest_to_positive_batch_id_if_none"]
    assert row["terminal_dead_end_flag"] is False
    assert row["paper_order_intent_created_flag"] is False
