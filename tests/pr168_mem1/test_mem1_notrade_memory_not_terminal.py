from .test_support import read_jsonl


def test_notrade_memory_routes_work_without_dead_end_or_global_ban() -> None:
    assert read_jsonl("notrade_context_memory.jsonl")
    for row in read_jsonl("notrade_context_memory.jsonl"):
        assert row["terminal_dead_end_flag"] is False
        assert row["condition_scoped_only_flag"] is True
        assert row["reoptimization_route_required_flag"] is True
        assert row["global_formula_ban_flag"] is False
        assert row["global_qku_ban_flag"] is False
    assert all(row["terminal_dead_end_flag"] is False for row in read_jsonl("notrade_not_terminal.jsonl"))
