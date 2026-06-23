from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_rp3_item_accounting_counts_match() -> None:
    assert_rank3_valid()
    row = rows("rp3_item_accounting")[0]
    assert row["rp3_computable_map3_formula_tested_count_observed"] == 35
    assert row["rp3_canonical_formula_id_universe_observed"] == 47
    assert row["rp3_expression_repair_formula_count_observed"] == 7
    assert row["rp3_source_review_formula_count_observed"] == 5
    assert row["rp3_data_repair_formula_count_observed"] == 0
