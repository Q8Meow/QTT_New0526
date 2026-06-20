from tools.pr168_rank_validator import run_validation


def test_materialized_artifacts_not_blueprints() -> None:
    run_validation("materialized_artifacts_not_blueprints")
