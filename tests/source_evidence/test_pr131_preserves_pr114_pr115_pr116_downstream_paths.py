from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_preserves_pr114_pr115_pr116_downstream_paths():
    handoff = support.downstream_handoff()

    assert handoff["downstream_prs"] == ["PR114", "PR115", "PR116"]
    assert all("PR114" in record["downstream_pr114_market_data_ingest_ref"] for record in support.readiness_receipts())
    assert all("PR115" in record["downstream_pr115_orderbook_snapshot_ref"] for record in support.readiness_receipts())
    assert all("PR116" in record["downstream_pr116_runtime_resolver_snapshot_ref"] for record in support.readiness_receipts())
