from tests.pr169_dash1_ui1.conftest import boot_data, jsonl


def test_ui1_existing_dash1_action_codes_preserved() -> None:
    canonical = {row["action_code"] for row in jsonl("owner_action_registry.generated.jsonl")}
    rendered = {row["action_code"] for row in boot_data()["action_registry"]}
    assert rendered == canonical
    chat_codes = boot_data()["chat_action_catalog"]["actions"]
    assert all(row["linked_existing_owner_action_code"] in canonical for row in chat_codes)
