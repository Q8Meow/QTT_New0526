from ._helpers import rows


def test_source_rights_reject_source_fact_authority() -> None:
    for row in rows("rank_source_rights.jsonl"):
        assert row["accepted_source_fact_flag"] is False
        assert row["replay_paper_verification_required"] is True
        assert row["confidential_or_restricted_flag"] is False

