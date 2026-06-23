from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_rank_score_lineage_traces_components_and_notrade() -> None:
    assert_rank3_valid()
    assert all(row["raw_component_refs"] and row["normalized_component_refs"] and row["no_trade_refs"] for row in rows("rank_score_lineage"))
