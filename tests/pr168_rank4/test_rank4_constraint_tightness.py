from ._helpers import rows


def test_constraint_tightness_includes_margins() -> None:
    tight = rows("rank_constraint_tightness.jsonl")
    assert tight
    assert all("margin_to_threshold" in row for row in tight)
    assert any(row["barely_passed_flag"] is True for row in tight)

