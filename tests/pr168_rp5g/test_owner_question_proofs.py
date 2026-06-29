from ._helpers import assert_rows_have_contract


def test_owner_question_ledgers_exist() -> None:
    assert_rows_have_contract("owner_q1_edge.jsonl")
    assert_rows_have_contract("owner_q2_route.jsonl")
    assert_rows_have_contract("owner_q3_auto_path.jsonl")

