from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_negative_memory_handoff():
    rows = load_records("PR163_C_PR165BNegativeMemoryHandoff.report.json")
    assert len(rows) == summary()["pr165b_negative_memory_handoff_rows"]
    assert all(row["negative_memory_candidate_flag"] is True for row in rows)
    assert all(row["retest_condition"] for row in rows)
