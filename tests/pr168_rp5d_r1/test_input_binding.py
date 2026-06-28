from ._helpers import read_jsonl


def test_input_binding_rows_exist() -> None:
    assert read_jsonl("input_bind.jsonl")
