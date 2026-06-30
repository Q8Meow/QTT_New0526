from ._helpers import rows


def test_solver_cascade_frontiers_controls_exist() -> None:
    assert rows("solver_cascade.jsonl")
    assert rows("efficient_frontier.jsonl")
    assert rows("robust_batch.jsonl")
    assert rows("stress_batch.jsonl")
    assert rows("null_batch.jsonl")
    assert rows("anti_sel_bias.jsonl")
