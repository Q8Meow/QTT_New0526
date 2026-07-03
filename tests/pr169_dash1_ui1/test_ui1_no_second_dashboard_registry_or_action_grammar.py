from tests.pr169_dash1_ui1.conftest import UI, boot_data, ui_doc


def test_ui1_no_second_dashboard_registry_or_action_grammar() -> None:
    boundary = ui_doc("owner_dashboard_dash1_ui1_renderer_boundary.generated.json")
    assert boundary["second_registry"] is False
    assert boundary["new_action_semantics"] is False
    assert boundary["parallel_dashboard"] is False
    assert boot_data()["chat_action_catalog"]["meta"]["manual_edit_allowed"] is False
    assert not any(path.name.endswith("_registry.generated.json") for path in UI.glob("*registry*.json"))
