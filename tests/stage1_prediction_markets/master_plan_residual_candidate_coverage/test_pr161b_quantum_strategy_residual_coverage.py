from .pr161b_test_support import records, summary


def test_pr161b_quantum_strategy_residuals_map_to_future_flow():
    assert summary()["quantum_strategy_residual_count"] > 0
    assert all(record["downstream_pr87_pr92_route"] for record in records("quantum_strategy")[:25])
