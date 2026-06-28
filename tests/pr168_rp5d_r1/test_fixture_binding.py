from ._helpers import read_jsonl


def test_fixture_bindings_are_non_authority() -> None:
    rows = read_jsonl("fixture_bind.jsonl")
    assert rows
    assert all(row["contract_source"] in {"FIXTURE_NON_AUTHORITY", "SOURCE_REQUIRED_NOT_FILLED"} for row in rows)
