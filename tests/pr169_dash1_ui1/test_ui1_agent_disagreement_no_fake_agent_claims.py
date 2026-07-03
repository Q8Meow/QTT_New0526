from tests.pr169_dash1_ui1.r1_contract_assertions import assert_agent_disagreement


def test_ui1_agent_disagreement_no_fake_agent_claims() -> None:
    assert_agent_disagreement()
