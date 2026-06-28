from ._helpers import all_rows


def test_no_rows_claim_profit_proof() -> None:
    assert all(row.get("profit_proof_flag") is False for row in all_rows())
