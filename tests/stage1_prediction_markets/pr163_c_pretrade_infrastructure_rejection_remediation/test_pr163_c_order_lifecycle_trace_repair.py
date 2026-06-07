from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_order_lifecycle_trace_repair():
    for row in load_records("PR163_C_OrderLifecycleTraceRepairRegistry.report.json"):
        assert row["no_live_order_flag"] is True
        assert row["simulated_rejected"] is False
        assert row["simulated_submitted"]
