from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_pretrade_repair_lattice_complete():
    rows = load_records("PR163_C_PretradeRepairLattice.report.json")
    assert len(rows) == summary()["pr164_pr163c_trigger_rows_consumed"]
    assert all(row["repair_action_ids"] and row["consumer_routes"] for row in rows)
    assert all(row["after_readiness_route"] for row in rows)
