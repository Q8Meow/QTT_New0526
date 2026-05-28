from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import overlay_records


def test_pr158_atomicrows_semantic_contract_compatibility_preserved():
    assert all(record["AtomicRows_semantic_contract_ref"] == "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json" for record in overlay_records())
    assert all(record["AtomicRows_reconciliation_ref"] == "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json" for record in overlay_records())

