from ._helpers import assert_rows_have_contract


def test_trade_candidate_required_fields() -> None:
    row = assert_rows_have_contract("trade_candidate.jsonl")[0]
    for key in ("side", "entry_price_candidate", "order_size_candidate", "maker_taker_split_candidate", "pre_submit_revalidation_ref"):
        assert row[key] not in ("", None, [])

