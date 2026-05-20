from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_no_credential_provider_private_state_runtime_cash():
    for field in ("credential_provider_called", "live_credential_resolution_performed", "private_state_fetch_created", "runtime_cash_authority_created"):
        assert all(record[field] is False for record in support.all_records() if field in record)
