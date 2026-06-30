from decimal import Decimal

from ._helpers import rows


def test_scores_have_numeric_components() -> None:
    scores = rows("rank_score.jsonl")
    components = rows("score_comp.jsonl")
    assert scores
    assert all(Decimal(row["rank4_execution_adjusted_score"]) == Decimal(row["rank4_execution_adjusted_score"]) for row in scores)
    assert min(sum(1 for comp in components if comp["candidate_id"] == row["candidate_id"]) for row in scores) >= 10

