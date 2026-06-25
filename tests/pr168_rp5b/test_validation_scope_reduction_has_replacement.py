from tests.pr168_rp5b._helpers import final_summary, load_rows


def test_validation_scope_reduction_has_replacement() -> None:
    rows = load_rows("validation_scope_reduction_rows")
    assert rows
    assert final_summary()["validation_replacement_rule_count"] == len(rows)
    assert all(row["replacement_validator_refs"] for row in rows)
