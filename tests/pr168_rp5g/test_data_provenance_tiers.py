from ._helpers import assert_rows_have_contract


def test_proxy_labels_do_not_claim_real_market_profit() -> None:
    rows = assert_rows_have_contract("sim_result.jsonl")
    assert all(row["outcome_label"].startswith("PROXY_SIMULATED_") for row in rows)
    assert all(row["real_market_profit_proof_flag"] is False for row in rows)

