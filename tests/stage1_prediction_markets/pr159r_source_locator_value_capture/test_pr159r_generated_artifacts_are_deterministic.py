def test_pr159r_generated_artifacts_are_deterministic(pr159r_validation_result):
    assert not pr159r_validation_result.failures

