from tools.pr168_rank_validator import run_validation


def test_latency_hot_path_seed() -> None:
    run_validation("latency_hot_path_seed")
