from ._helpers import assert_rows_have_contract


ALLOWED_USE_CLASSES = {
    "TARGET_ELIGIBLE_REPLAY_PAPER_EXEC_NOW",
    "TARGET_ELIGIBLE_AVAILABLE_ON_DEMAND",
    "TARGET_ELIGIBLE_SOURCE_REQUIRED",
    "TARGET_ELIGIBLE_EXECUTION_CONTRACT_INCOMPLETE",
    "NOT_STAGE1_APPLICABLE",
    "AGENT_DUTY_NOT_ALLOWED",
}


def test_qku_compute_route_and_target_use_are_classified() -> None:
    compute = assert_rows_have_contract("qku_compute_route.jsonl")
    target_use = assert_rows_have_contract("qku_target_use.jsonl")

    assert {row["use_class"] for row in compute} <= ALLOWED_USE_CLASSES
    assert {row["use_class"] for row in target_use} <= ALLOWED_USE_CLASSES
    assert all(row["full_library_scan_flag"] is False for row in compute)
    assert all(row["metadata_only_flag"] is False for row in compute)
    assert all(row["centralized_resolver_ref"] for row in compute)
    assert all(row["agent_duty_ref"] for row in compute)

