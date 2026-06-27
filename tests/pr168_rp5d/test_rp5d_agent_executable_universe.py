from __future__ import annotations

from ._helpers import report, rows


def test_agent_executable_resolver_is_id_only_and_centralized() -> None:
    run = report("rp5d_run_receipt.report.json")
    resolver = rows("rp5d_agent_exec_resolver.jsonl")
    views = rows("rp5d_stage_agent_exec_view.jsonl")
    queries = rows("rp5d_agent_exec_queries.jsonl")

    assert len(resolver) == run["agent_executable_resolver_row_count"]
    assert views
    assert queries
    assert all("resolved_executable_identity_refs" in row for row in resolver)
    assert all("identity_objects" not in row for row in resolver)
