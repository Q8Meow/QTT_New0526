from ._helpers import read_jsonl


def test_selected_qkus_have_computability_or_repair_route() -> None:
    rows = read_jsonl("qku_guard.jsonl")
    selected = [row for row in rows if row["selected_for_context_flag"]]
    assert selected
    for row in selected:
        assert row["metadata_only_flag"] is False
        assert row["computability_class"] in {
            "COMPUTABLE_READY",
            "COMPUTABLE_AFTER_ADAPTER",
            "STRUCTURAL_READY_NOT_EXECUTABLE",
            "REPAIR_NEEDED",
        }
        if row["included_in_stack_flag"]:
            assert row["rp5d_computability_ref"]
