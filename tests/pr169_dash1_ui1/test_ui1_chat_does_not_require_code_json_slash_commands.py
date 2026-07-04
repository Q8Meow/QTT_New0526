from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_chat_does_not_require_code_json_slash_commands() -> None:
    examples = ui_doc("ui1r1_chat_examples.generated.json")["examples"]
    assert examples
    assert all(not row["owner_example_text"].lstrip().startswith(("/", "{", "[")) for row in examples)
