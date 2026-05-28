from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_basis_audit_requires_artifact_refs_or_owner_choice():
    records = report(c.BASIS_AUDIT_PATH)["records"]
    assert all(item["basis_artifact_refs"] or item["owner_choice_packet_ref_or_null"] for item in records)
