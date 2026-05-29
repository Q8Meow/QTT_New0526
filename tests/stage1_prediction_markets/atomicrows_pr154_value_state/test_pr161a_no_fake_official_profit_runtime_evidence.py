from .pr161a_test_support import report


def test_pr161a_no_fake_official_profit_runtime_evidence():
    for key in ("final_summary", "field_inventory", "quantum_profiles"):
        payload = report(key)
        assert payload["profit_evidence_count"] == 0
        assert payload["replay_paper_execution_count"] == 0
        assert payload["runtime_live_order_profit_authority_count"] == 0
        assert payload["optimizer_execution_count"] == 0
        assert payload["quantum_backend_execution_count"] == 0

