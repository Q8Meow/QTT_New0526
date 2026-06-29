from ._helpers import assert_rows_have_contract


def test_completion_routes_are_precise_and_exec_now_hints_do_not_promote() -> None:
    completion = assert_rows_have_contract("completion_route.jsonl")
    hints = assert_rows_have_contract("exec_now_delta_hint.jsonl")

    assert all(row["broad_global_blocker_flag"] is False for row in completion)
    assert all(row["completion_status"] in {"COMPLETE", "SOURCE_REQUIRED", "REVALIDATION_REQUIRED", "DOWNSTREAM_REQUIRED", "NOT_STAGE1_APPLICABLE"} for row in completion)
    assert all(row["blocker_code"] for row in completion)
    assert all(row["future_rp5g_exec_now_consumer_flag"] is True for row in hints)
    assert all(row["rp5f_promotes_executable_now_flag"] is False for row in hints)

