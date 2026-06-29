from ._helpers import assert_rows_have_contract


def test_master_and_roadmap_traces_exist() -> None:
    assert_rows_have_contract("master_trace.jsonl")
    assert_rows_have_contract("roadmap_trace.jsonl")

