from ._helpers import read_jsonl


def test_promoted_rows_have_fixture_only_proof_tier() -> None:
    promoted_ids = {row["unlock_candidate_id"] for row in read_jsonl("promote.jsonl")}
    proof = {row["unlock_candidate_id"]: row for row in read_jsonl("proof_tier.jsonl")}
    assert promoted_ids
    assert all(proof[cid]["executable_proof_provenance_tier"] == "EXEC_NOW_PROOF_FIXTURE_ONLY" for cid in promoted_ids)
    assert all(proof[cid]["real_market_profit_proof_flag"] is False for cid in promoted_ids)
