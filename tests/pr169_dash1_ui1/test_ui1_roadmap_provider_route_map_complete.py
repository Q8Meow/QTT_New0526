from tests.pr169_dash1_ui1.conftest import PROVIDER_STAGES, ui_doc


def test_ui1_roadmap_provider_route_map_complete() -> None:
    route_map = ui_doc("owner_dashboard_roadmap_provider_route_map.generated.json")
    routes = {row["provider_stage"]: row for row in route_map["routes"]}
    assert set(PROVIDER_STAGES).issubset(routes)
    for row in routes.values():
        assert row["runtime_side_effect_allowed_in_UI1"] is False
        assert row["activation_route"]
        assert row["authority_class"]
