from ._helpers import read_jsonl


def test_contract_matrix_complete_for_promotions() -> None:
    promoted_ids = {row["unlock_candidate_id"] for row in read_jsonl("promote.jsonl")}
    matrix = {row["unlock_candidate_id"]: row for row in read_jsonl("contract_matrix.jsonl")}
    assert all(matrix[cid]["all_required_contracts_complete_flag"] is True for cid in promoted_ids)
    assert all(not matrix[cid]["missing_contracts"] for cid in promoted_ids)
