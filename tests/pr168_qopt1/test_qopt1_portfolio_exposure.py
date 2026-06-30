from ._helpers import rows


def test_portfolio_exposure_near_clone_and_capacity_surfaces_exist() -> None:
    assert rows("exposure_matrix.jsonl")
    assert rows("near_clone_pair.jsonl")
    assert rows("capacity_matrix.jsonl")
    primary = next(row for row in rows("batch_select.jsonl") if row["batch_class"] == "PRIMARY_ADVISORY")
    assert primary["capital_efficiency_score"] != ""
