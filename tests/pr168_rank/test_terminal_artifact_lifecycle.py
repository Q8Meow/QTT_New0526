from tools.pr168_rank_validator import run_validation


def test_terminal_artifact_lifecycle() -> None:
    run_validation("terminal_artifact_lifecycle")
