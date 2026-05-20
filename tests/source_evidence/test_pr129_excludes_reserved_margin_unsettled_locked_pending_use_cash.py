from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_excludes_reserved_margin_unsettled_locked_pending_use_cash():
    report = support.reconciliation_report()["reconciliation_reports"][0]

    assert report["excluded_reserved_cash_component_count"] == 3
    assert report["excluded_margin_lock_component_count"] == 3
    assert report["excluded_unsettled_funds_component_count"] == 3
    assert report["excluded_locked_or_withdrawal_restricted_component_count"] == 3
    assert report["excluded_pending_use_component_count"] == 3
    assert len(report["excluded_component_ids"]) == 12
