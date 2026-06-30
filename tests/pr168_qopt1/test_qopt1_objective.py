from ._helpers import rows


def test_objective_terms_are_numeric_and_not_metadata_only() -> None:
    terms = rows("obj_terms.jsonl")
    assert terms
    assert any(row["term_name"] == "net_expected_pnl_cash" for row in terms)
    for row in terms:
        assert row["metadata_only_flag"] is False
        assert row["numeric_evidence_refs"]
