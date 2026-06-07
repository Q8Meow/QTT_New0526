from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.authority_policy import BOUNDARY_COUNT_FIELDS
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import summary


def test_pr164_no_live_profit_source_connector_private_state_authority():
    record = summary()
    for field in (
        "live_order_authority_count",
        "profit_evidence_count",
        "source_acceptance_count",
        "connector_binding_count",
        "private_state_fetch_count",
    ):
        assert record[field] == BOUNDARY_COUNT_FIELDS[field]
