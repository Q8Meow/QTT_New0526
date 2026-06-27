from __future__ import annotations

from ._helpers import rows


def test_vs1_temporary_stacks_and_variable_search_are_bounded_ex_ante():
    stacks = rows("temporary_stack_candidate_receipts.jsonl")
    searches = rows("trade_plan_variable_search_receipts.jsonl")

    assert all(row["ephemeral_stack_flag"] is True for row in stacks)
    assert all(row["bulk_grid_retained_flag"] is False for row in stacks)
    assert all(row["bounded_search_flag"] is True for row in searches)
    assert all(row["ex_ante_search_flag"] is True for row in searches)
    assert all(row["hindsight_free_flag"] is True for row in searches)
    assert all(row["gate_relaxation_attempt_count"] == 0 for row in searches)
