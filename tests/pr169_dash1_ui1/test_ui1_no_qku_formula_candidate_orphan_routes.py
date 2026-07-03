from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_no_qku_formula_candidate_orphan_routes() -> None:
    report = ui_doc("owner_dashboard_qku_formula_no_orphan_closure.report.json")
    assert report["status"] == "PASS"
    assert report["orphan_count"] == 0
    assert report["matrix_ref"] == "owner_dashboard_qku_formula_computability_matrix.generated.json"
