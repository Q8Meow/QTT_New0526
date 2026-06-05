def test_polymarket_capability_has_clob_order_type_semantics(records):
    row = next(row for row in records("PR163_PaperVenueAdapterCapabilityMatrix.report.json") if row["venue_scope"] == "POLYMARKET_CLOB")
    assert "GTC_GTD_FOK_FAK_post_only_semantics" in row["supported_features"]
    assert "no_wallet_signature_private_key" in row["supported_features"]
