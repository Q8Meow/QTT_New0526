from tests.pr169_dash1.conftest import registry


def test_agent_routes_reference_pr165_d2_roles_and_validation_artifact() -> None:
    allowed_roles = {"dashboard_agent", "governance_agent", "commander_agent", "risk_manager_agent", "quantum_optimizer_agent", "parameter_selector_agent"}
    for row in registry():
        assert set(row["agent_role_refs_from_PR165_D2"]).issubset(allowed_roles)
        assert row["responsible_agent_role"] in allowed_roles
        assert row["agent_route_validation_ref"] == "PR165_D2_CommandActionMatrix.report.json"
