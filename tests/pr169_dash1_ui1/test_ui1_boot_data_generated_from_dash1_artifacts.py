from tests.pr169_dash1_ui1.conftest import boot_data, jsonl


def test_ui1_boot_data_generated_from_dash1_artifacts() -> None:
    data = boot_data()
    assert data["meta"]["data_source"] == "GENERATED_ARTIFACTS"
    assert data["decision_queue"] == jsonl("owner_decision_queue.generated.jsonl")
    assert data["actionable_cards"] == jsonl("owner_actionable_card.generated.jsonl")
    assert data["action_registry"] == jsonl("owner_action_registry.generated.jsonl")
    assert data["meta"]["ui1_renderer_layer"] is True
    assert data["meta"]["manual_edit_allowed"] is False
