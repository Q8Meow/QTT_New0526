from tests.pr168_gfp2r._helpers import records


def test_pr168_gfp2r_consumes_data1a_allowed_data_family_contract() -> None:
    payload = records("PR168_GFP2R_AllowedDataFamilyContractConsumption")
    families = {row["data_family"] for row in payload["rows"]}
    assert "current_orderbook_snapshot" in families
    assert "historical_full_book_replay_exists" not in families
    assert all(row["allowed_for_real_positive_negative_proof_flag"] is False for row in payload["rows"])
