from ._helpers import all_jsonl_rows, read_json


def test_every_generated_row_has_no_execution_authority() -> None:
    for name, row in all_jsonl_rows():
        for key, value in row.items():
            if key.endswith("_authority_flag") or key in {
                "connector_write_flag",
                "private_state_fetch_flag",
                "cash_account_read_flag",
                "profit_proof_flag",
                "qopt_execution_flag",
                "quantum_backend_execution_flag",
                "quantum_advantage_claim_flag",
            }:
                assert value is False, (name, row.get("row_id"), key, value)

    report = read_json("exec_auth.report.json")
    assert report["order_authority_flag"] is False
    assert report["live_authority_flag"] is False
    assert report["live_order_authorized"] is False
    assert report["order_submit_cancel_replace_reduce_close_authorized"] is False
