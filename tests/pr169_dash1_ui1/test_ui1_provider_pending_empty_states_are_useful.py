from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_provider_pending_empty_states_are_useful() -> None:
    manifest = ui_doc("owner_dashboard_useful_empty_state_manifest.generated.json")
    required = {
        "panel_id",
        "widget_id",
        "missing_data_family",
        "why_missing",
        "source_artifact_attempted",
        "provider_stage",
        "activation_route",
        "owner_action_refs",
        "agent_role_refs_from_PR165_D2",
        "blocked_authority_refs",
        "what_owner_can_do_next",
        "what_later_PR_will_materialize",
    }
    for row in manifest["empty_states"]:
        assert required.issubset(row)
