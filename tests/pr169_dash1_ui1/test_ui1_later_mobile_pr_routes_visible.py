from tests.pr169_dash1_ui1.conftest import PROVIDER_STAGES, boot_data


def test_ui1_later_mobile_pr_routes_visible() -> None:
    routes = {row["provider_stage"] for row in boot_data()["provider_stage_routes"]["routes"]}
    for stage in ("UI2", "SVC1", "MOBILE1", "MOBILE2", "TG1"):
        assert stage in routes
    assert set(PROVIDER_STAGES).issubset(routes)
