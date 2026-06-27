from __future__ import annotations

from ._helpers import rows


def test_vs1_selected_bindings_are_computable_not_metadata_only():
    bindings = rows("selected_computable_qku_formula_bindings.jsonl")

    assert bindings
    assert all(row["metadata_only_flag"] is False for row in bindings)
    assert all(row["computable_for_vs1_fixture_flag"] is True for row in bindings)
    assert all(row["missing_input_count"] == 0 for row in bindings)
    assert all(row["input_fields"] and row["output_field"] for row in bindings)
