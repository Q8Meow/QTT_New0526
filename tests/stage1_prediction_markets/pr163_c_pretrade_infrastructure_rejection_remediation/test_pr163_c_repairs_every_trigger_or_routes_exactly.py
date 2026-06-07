from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.central_pretrade_repair_reason_codes import ALLOWED_DISPOSITIONS, PROHIBITED_DISPOSITIONS
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_repairs_every_trigger_or_routes_exactly():
    rows = load_records("PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json")
    assert summary()["repaired_or_exactly_routed_count"] == len(rows)
    assert all(row["final_disposition"] in ALLOWED_DISPOSITIONS for row in rows)
    assert not any(row["final_disposition"] in PROHIBITED_DISPOSITIONS for row in rows)
    assert all(row["repair_action_ids"] for row in rows)
