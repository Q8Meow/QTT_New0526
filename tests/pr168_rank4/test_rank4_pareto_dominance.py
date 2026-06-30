from ._helpers import rows


def test_pareto_and_dominance_rows_cover_candidates() -> None:
    candidates = {row["candidate_id"] for row in rows("rank_feat.jsonl")}
    assert candidates <= {row["candidate_id"] for row in rows("pareto_frontier.jsonl")}
    assert candidates <= {row["candidate_id"] for row in rows("dominance.jsonl")}

