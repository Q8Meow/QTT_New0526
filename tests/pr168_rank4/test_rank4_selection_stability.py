from ._helpers import rows


def test_selection_stability_discloses_brittleness() -> None:
    for row in rows("rank_rank_stability.jsonl"):
        assert "brittle_winner_flag" in row
        assert "stability_score" in row

