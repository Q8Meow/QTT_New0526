from ._helpers import assert_rows_have_contract


def test_owner_audit_materializes_three_owner_answers() -> None:
    rows = assert_rows_have_contract("owner_audit.jsonl")
    by_question = {row["question_id"]: row for row in rows}

    assert set(by_question) == {"Q1", "Q2", "Q3"}
    for row in rows:
        assert row["profit_proof_created_flag"] is False
        assert row["order_authority_created_flag"] is False
        assert row["implemented_by_artifacts"]
        assert row["validator_refs"]
