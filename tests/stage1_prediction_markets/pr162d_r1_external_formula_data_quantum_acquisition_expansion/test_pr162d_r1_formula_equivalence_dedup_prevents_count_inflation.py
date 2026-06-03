from __future__ import annotations


def test_pr162d_r1_formula_equivalence_dedup_prevents_count_inflation(records):
    dedup = records("PR162D_R1_FormulaEquivalenceAndDedupLedger.report.json")
    keys = [record["dedupe_key"] for record in dedup]
    assert len(keys) == len(set(keys))
    assert all(record["duplicate_count_inflation_flag"] is False for record in dedup)
