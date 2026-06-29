from ._helpers import assert_rows_have_contract


def test_queue_fill_and_adverse_selection_inputs_are_surfaces_only() -> None:
    queue = assert_rows_have_contract("queue_fill_inputs.jsonl")
    adverse = assert_rows_have_contract("adverse_select.jsonl")

    assert all(row["future_rp5g_fill_model_required_flag"] is True for row in queue)
    assert all(row["queue_position_proxy"] == "SOURCE_REQUIRED" for row in queue)
    assert all(row["adverse_selection_risk_score"] for row in adverse)
    assert all(row["source_update_risk_proxy"] == "HIGH_SOURCE_REQUIRED" for row in adverse)
    assert all(row["future_rank4_penalty_consumer_flag"] is True for row in adverse)
