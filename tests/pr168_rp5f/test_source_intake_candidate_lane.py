from ._helpers import assert_rows_have_contract


def test_source_intake_and_value_candidates_remain_candidate_only() -> None:
    for filename in ("source_intake.jsonl", "source_value_cand.jsonl"):
        rows = assert_rows_have_contract(filename)
        assert rows
        for row in rows:
            assert row["candidate_only_flag"] is True
            assert row["accepted_source_fact_flag"] is False
            assert row["connector_semantic_binding_flag"] is False
            assert row["live_default_flag"] is False
            assert row["profit_proof_flag"] is False
            assert row["replay_paper_verification_required"] is True

