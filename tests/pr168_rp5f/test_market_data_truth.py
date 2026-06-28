from ._helpers import assert_rows_have_contract


def test_market_data_truth_blocks_executable_authority_when_source_required() -> None:
    rows = assert_rows_have_contract("md_truth.jsonl")

    assert all(row["truth_state"] == "SOURCE_REQUIRED" for row in rows)
    assert all(row["executable_truth_allowed_flag"] is False for row in rows)
    assert all(row["risk_diagnostic_only_flag"] is True for row in rows)
    assert all(row["block_new_or_increased_exposure_flag"] is True for row in rows)

