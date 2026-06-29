from ._helpers import assert_rows_have_contract


def test_quantum_constraints_and_interpret_back_exist() -> None:
    assert_rows_have_contract("q_constraints.jsonl")
    interp = assert_rows_have_contract("q_interp.jsonl")
    assert all(row["trade_seed_id"].startswith("RP5F_SEED_") for row in interp)

