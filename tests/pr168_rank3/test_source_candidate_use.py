from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_source_candidate_use_rows_are_traceable_and_penalized() -> None:
    assert_rank3_valid()
    uses = rows("source_candidate_use")
    assert len(uses) == 5
    assert all(row["source_url_or_owner_ref"] for row in uses)
    assert all(row["formula_input_mapping"] for row in uses)
    assert all(row["reliability_penalty_or_gap"] > 0 for row in uses)
