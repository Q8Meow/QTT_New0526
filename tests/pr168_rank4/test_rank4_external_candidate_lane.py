from ._helpers import rows


def test_external_candidates_are_candidate_only() -> None:
    for row in rows("rank_ext_cand_intake.jsonl"):
        assert row["candidate_only_flag"] is True
        assert row["accepted_source_fact_flag"] is False
        assert row["live_default_flag"] is False

