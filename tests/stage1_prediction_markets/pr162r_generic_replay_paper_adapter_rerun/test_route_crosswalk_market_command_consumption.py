def test_route_crosswalk_market_command_consumption(summary, records):
    route = records("PR162R_RouteTriageCrosswalkConsumptionAudit.report.json")
    market = records("PR162R_MarketSpecificQKUAdapterIndex.report.json")
    command = records("PR162R_CommandActionQKUBindingMatrix.report.json")
    assert summary["route_triage_crosswalk_consumption_audit_created"] is True
    assert summary["market_specific_qku_adapter_index_created"] is True
    assert summary["command_action_qku_binding_matrix_created"] is True
    assert route
    assert market
    assert command
    assert any(row["fallback_lineage_used"] for row in route)
