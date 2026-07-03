from tests.pr169_dash1_ui1.conftest import boot_data, jsonl


def test_ui1_decision_queue_and_actionable_card_semantics_preserved() -> None:
    data = boot_data()
    assert data["decision_queue"] == jsonl("owner_decision_queue.generated.jsonl")
    assert data["actionable_cards"] == jsonl("owner_actionable_card.generated.jsonl")
    assert all(row["no_actionable_card_outside_decision_queue"] is True for row in data["decision_queue"])
