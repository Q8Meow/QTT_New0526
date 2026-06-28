from ._helpers import read_jsonl


def test_edge_profit_map_is_one_per_unlock_candidate_without_profit_proof() -> None:
    rows = read_jsonl("edge_profit_map.jsonl")
    assert len(rows) == 52
    assert all(row["rp5d_r1_profit_proof_flag"] is False for row in rows)
    assert all(row["rp5d_r1_order_authority_flag"] is False for row in rows)
