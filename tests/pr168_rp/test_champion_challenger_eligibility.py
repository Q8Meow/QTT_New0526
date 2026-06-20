from tools.pr168_rp_validator import run_validation


def test_champion_challenger_eligibility() -> None:
    run_validation("champion_challenger")
