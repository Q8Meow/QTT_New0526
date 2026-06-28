from ._helpers import assert_rows_have_contract


def test_yes_no_parity_and_cross_venue_hints_are_non_authority() -> None:
    parity = assert_rows_have_contract("yes_no_parity.jsonl")
    cross = assert_rows_have_contract("cross_venue_hints.jsonl")

    assert all(row["fee_adjusted_yes_no_complement_parity_hint"] == "SOURCE_REQUIRED" for row in parity)
    assert all(row["accepted_source_fact_flag"] is False for row in parity)
    assert all(row["accepted_source_fact_flag"] is False for row in parity)
    assert all(row["cross_venue_price_dislocation_hint"] == "SOURCE_REQUIRED" for row in cross)
    assert all(row["cross_venue_latency_skew_hint"] == "SOURCE_REQUIRED" for row in cross)
    assert all(row["profit_proof_flag"] is False for row in cross)
