from tests.pr169_dash1.conftest import jsonl


def test_qku_formula_candidate_routes_have_refs_and_no_formula_mutation() -> None:
    rows = jsonl("owner_qku_formula_candidate_route_view.generated.jsonl")
    assert rows
    for row in rows:
        assert row["computability_state"] == "COMPUTABLE_AFTER_PROVIDER_CONTRACT"
        assert row["upstream_evidence_refs"]
        assert row["activation_route"]
        assert row["qku_refs"] and row["formula_refs"] and row["trade_plan_candidate_refs"]
