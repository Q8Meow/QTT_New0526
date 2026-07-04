from tests.pr169_dash1_ui1.r2_contract_assertions import assert_next_step_router


def test_ui1r2_next_step_router_no_orphan_refs() -> None:
    assert_next_step_router()
