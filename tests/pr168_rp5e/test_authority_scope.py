from ._helpers import read_json


def test_rp5e_execution_authority_is_preview_handoff_only() -> None:
    report = read_json("exec_auth.report.json")
    assert report["rp5e_scope"] == "STACK_PREVIEW_FEATURE_HANDOFF_ONLY"
    for key in (
        "paper_order_authority_authorized",
        "live_dryrun_execution_authorized",
        "shadow_execution_authorized",
        "limited_live_canary_authorized",
        "connector_write_authorized",
        "private_state_fetch_authorized",
        "order_submit_cancel_replace_reduce_close_authorized",
        "qopt_execution_authorized",
        "quantum_backend_execution_authorized",
    ):
        assert report[key] is False


def test_run_receipt_keeps_forbidden_authority_counts_zero() -> None:
    receipt = read_json("run_receipt.report.json")
    for key in (
        "forbidden_authority_count",
        "paper_authority_count",
        "shadow_authority_count",
        "live_authority_count",
        "order_authority_count",
        "connector_write_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
    ):
        assert receipt[key] == 0
