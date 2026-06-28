from ._helpers import read_jsonl


def test_unit_adapter_rows_exist() -> None:
    assert read_jsonl("unit_adapt.jsonl")
