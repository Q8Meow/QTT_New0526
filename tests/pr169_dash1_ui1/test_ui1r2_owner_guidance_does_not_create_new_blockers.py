from tests.pr169_dash1_ui1.r2_contract_assertions import assert_guidance_coverage


def test_ui1r2_owner_guidance_does_not_create_new_blockers() -> None:
    assert_guidance_coverage()
