from ._helpers import read_jsonl


def test_portfolio_diversification_rows_contain_exposures_and_near_clone_cluster() -> None:
    rows = read_jsonl("port_div.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["formula_family_exposure"]
        assert row["qku_family_exposure"]
        assert row["role_family_exposure"]
        assert row["near_clone_cluster_id"]
        assert float(row["diversification_score"]) >= 0.0
