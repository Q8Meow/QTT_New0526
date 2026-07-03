from tests.pr169_dash1_ui1.r1_contract_assertions import assert_no_deferred_artifacts


def test_ui1_no_deferred_idea_repo_artifacts() -> None:
    assert_no_deferred_artifacts()
