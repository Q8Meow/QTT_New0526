from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_pr116_runtime_resolver_snapshot_path():
    handoff = support.handoff_report()["runtime_cash_downstream_handoff"]

    assert handoff["future_runtime_resolver_snapshot_pr"] == "PR116"
    assert support.main_report()["future_runtime_resolver_snapshot_path_preserved"] is True
    assert support.main_report()["runtime_resolver_snapshot_created_count"] == 0
