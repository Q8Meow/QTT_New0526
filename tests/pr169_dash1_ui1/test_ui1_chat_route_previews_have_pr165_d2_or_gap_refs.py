from tests.pr169_dash1_ui1.r1_contract_assertions import assert_chat_routes


def test_ui1_chat_route_previews_have_pr165_d2_or_gap_refs() -> None:
    assert_chat_routes()
