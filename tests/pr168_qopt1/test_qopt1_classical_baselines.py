from ._helpers import rows


def test_classical_solver_cascade_and_best_are_deterministic() -> None:
    assert rows("greedy_baseline.jsonl")
    assert rows("beam_result.jsonl")
    best = rows("classic_best.jsonl")[0]
    assert best["deterministic_seed_or_no_random_flag"] == "NO_RANDOMNESS"
    assert best["selected_candidate_ids"]
    assert rows("solver_arb.jsonl")[0]["manual_override_flag"] is False
