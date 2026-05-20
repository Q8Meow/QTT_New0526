from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    downstream_handoff,
    main_report,
)


def test_pr128_preserves_downstream_pr111_pr112_pr113_pr114_pr115_pr116_paths():
    handoff = downstream_handoff()

    assert main_report()["downstream_handoff_created"] is True
    assert handoff["future_runtime_cash_component_field_map_pr"] == "PR111"
    assert handoff["future_private_state_read_receipt_pr"] == "PR112"
    assert handoff["future_credential_alias_secret_no_capture_pr"] == "PR113"
    assert handoff["future_market_data_ingest_pr"] == "PR114"
    assert handoff["future_orderbook_event_snapshot_pr"] == "PR115"
    assert handoff["future_runtime_resolver_snapshot_pr"] == "PR116"
    assert handoff["production_downstream_authority"] is False
