from tests.pr169_dash1_ui1.r2r2_contract_assertions import assert_no_orphan_central_routes


def test_ui1r2r2_no_orphan_central_routes() -> None:
    assert_no_orphan_central_routes()
