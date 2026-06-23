from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_normalized_scores_use_unit_groups_and_lcb_gap_penalty() -> None:
    assert_rank3_valid()
    feature = rows("feature_matrix")
    normalized = rows("normalized_score")
    assert all(row["unit_normalization_group"] for row in feature)
    assert all(row["normalized_lcb_edge_or_conservative_gap"] < 0 for row in normalized)
