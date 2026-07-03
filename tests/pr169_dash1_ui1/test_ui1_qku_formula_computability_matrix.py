from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_qku_formula_computability_matrix() -> None:
    matrix = ui_doc("owner_dashboard_qku_formula_computability_matrix.generated.json")
    rows = matrix["rows"]
    assert rows
    allowed = {
        "COMPUTABLE_WITH_CURRENT_CONTRACT",
        "COMPUTABLE_AFTER_PROVIDER_ROUTE",
        "SCHEDULABLE_AFTER_ADAPTER",
        "REPLAY_PAPER_READY_PROVIDER_PENDING",
        "QMAP_REQUIRED",
        "PLUGIN_INTAKE_REQUIRED",
        "ALLOWLIST_PROVIDER_PENDING",
        "BLOCKED_BY_AUTHORITY_BOUNDARY",
        "ACTIONABLE_GAP_ROUTE",
    }
    assert all(row["computability_state"] in allowed for row in rows)
    assert all(row["no_orphan_status"] == "PASS" for row in rows)
