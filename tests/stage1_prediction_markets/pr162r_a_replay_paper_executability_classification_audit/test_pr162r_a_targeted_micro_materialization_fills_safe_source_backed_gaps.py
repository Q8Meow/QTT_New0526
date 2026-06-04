from __future__ import annotations


def test_pr162r_a_targeted_micro_materialization_fills_safe_source_backed_gaps(summary, records):
    ledger = records("PR162R_A_TargetedMicroMaterializationLedger.report.json")
    assert summary["targeted_micro_materialization_count"] == len({row["candidate_id"] for row in ledger})
    assert summary["targeted_micro_materialized_field_count"] == len(ledger)
    assert ledger
    assert all(row["source_locator"] for row in ledger)
    assert all(row["no_live_order_authority"] is True for row in ledger)
