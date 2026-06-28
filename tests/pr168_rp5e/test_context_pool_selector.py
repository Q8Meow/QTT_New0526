from ._helpers import read_jsonl


def test_context_formula_pools_have_required_role_and_readiness_surfaces() -> None:
    rows = read_jsonl("ctx_pools.jsonl")
    assert rows
    for row in rows:
        assert float(row["role_coverage_score"]) >= 0.8
        assert row["missing_required_roles"] == []
        assert row["rp5d_readiness_refs"]
        assert row["vs1_evidence_refs"]
