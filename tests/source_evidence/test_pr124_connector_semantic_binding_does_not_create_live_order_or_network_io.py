from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import consumed, report_and_failures


def test_pr124_binding_outputs_do_not_create_live_order_or_network_io():
    record = consumed()["success_records"][0]
    report, failures = report_and_failures()

    assert failures == []
    assert record["live_client_import_allowed_flag"] is False
    assert record["network_io_allowed_flag"] is False
    assert record["order_execution_allowed_flag"] is False
    assert record["live_reachability_allowed_flag"] is False
    assert report["forbidden_live_client_import_count"] == 0
    assert report["network_io_violation_count"] == 0
    assert report["order_execution_violation_count"] == 0
    assert report["live_reachability_violation_count"] == 0
    assert report["runtime_resolver_snapshot_created_count"] == 0
    assert report["order_authority_created"] is False
