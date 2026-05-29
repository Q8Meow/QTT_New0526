from .pr161a_test_support import records, summary


def test_pr161a_quantum_strategy_candidates_exist():
    strategies = records("quantum_strategies")
    assert len(strategies) == summary()["quantum_strategy_candidate_count"] == 8
    assert {strategy["strategy_class"] for strategy in strategies}
    assert all(strategy["downstream PR route"] for strategy in strategies)

