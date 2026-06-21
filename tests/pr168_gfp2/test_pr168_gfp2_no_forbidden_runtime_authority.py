from tests.pr168_gfp2.pr168_gfp2_test_support import root
from tools.pr168_gfp2_constants import REQUIRED_REPORTS


def test_no_live_order_source_truth_connector_private_state_cash_or_quantum_backend_authority() -> None:
    for name in REQUIRED_REPORTS:
        report = root(name)
        assert report["live_authority_created_flag"] is False
        assert report["order_authority_created_flag"] is False
        assert report["source_truth_acceptance_created_flag"] is False
        assert report["connector_semantic_binding_created_flag"] is False
        assert report["private_state_accessed_flag"] is False
        assert report["cash_accessed_flag"] is False
        assert report["quantum_backend_execution_flag"] is False
