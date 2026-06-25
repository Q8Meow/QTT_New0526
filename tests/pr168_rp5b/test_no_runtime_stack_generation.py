from tests.pr168_rp5b._helpers import final_summary


def test_no_runtime_stack_generation() -> None:
    assert final_summary()["runtime_stack_generation_count"] == 0
