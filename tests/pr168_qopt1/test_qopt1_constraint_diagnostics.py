from ._helpers import rows


def test_constraint_diagnostics_include_binding_shadow_and_lagrangian() -> None:
    assert rows("constraint_bind.jsonl")
    assert rows("shadow_price.jsonl")
    assert rows("lagrangian_term.jsonl")
    assert any(row["binding_flag"] is True for row in rows("constraint_bind.jsonl"))
