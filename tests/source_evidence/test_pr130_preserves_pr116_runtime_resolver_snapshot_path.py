from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_preserves_pr116_runtime_resolver_snapshot_path():
    handoff = support.handoff_report()["private_state_downstream_handoff"]

    assert support.main_report()["future_runtime_resolver_snapshot_path_preserved"] is True
    assert support.main_report()["runtime_resolver_snapshot_created_count"] == 0
    assert handoff["future_runtime_resolver_snapshot_pr"] == "PR116"
