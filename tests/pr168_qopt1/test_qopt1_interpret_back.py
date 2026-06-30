from ._helpers import rows


def test_quantum_variables_interpret_back_to_trade_domain() -> None:
    interp = rows("qinterp.jsonl")
    candidate_rows = [row for row in interp if row["candidate_id"]]
    assert candidate_rows
    for row in candidate_rows:
        assert row["trade_plan_id"]
        assert row["rank4_rank_id"]
        assert row["formula_refs"]
        assert row["qku_refs"]
