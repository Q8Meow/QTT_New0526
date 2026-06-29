from ._helpers import assert_rows_have_contract


def test_factual_gate_blocks_real_labels_for_proxy_data() -> None:
    rows = assert_rows_have_contract("factual_gate.jsonl")
    assert all(row["real_outcome_label_allowed_flag"] is False for row in rows)
    assert all(row["proxy_simulation_allowed_flag"] is True for row in rows)

