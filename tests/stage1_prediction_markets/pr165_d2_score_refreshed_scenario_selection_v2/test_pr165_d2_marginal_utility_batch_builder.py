from __future__ import annotations


def test_marginal_utility_rows_have_learning_value(pr165_d2_records):
    row = pr165_d2_records["PR165_D2_MarginalUtilityBatchBuilderLedger.report.json"][0]
    assert 0 <= row["expected_information_gain_score"] <= 1
    assert 0 <= row["repair_aware_learning_value"] <= 1
