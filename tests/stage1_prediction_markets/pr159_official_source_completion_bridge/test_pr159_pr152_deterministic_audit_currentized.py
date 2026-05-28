from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge.io import read_json
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import ROOT


def test_pr159_pr152_deterministic_audit_currentized():
    audit_path = c.GENERATED_DIR / "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    audit = read_json(ROOT / audit_path)
    assert audit["validation_summary"]["critical_finding_count"] == 0
    assert audit["validation_summary"]["build_report_byte_stable"] is True
    assert audit["validator_tool_registry_audit"]["default_validation_mutation_status"] == "PASS"
    assert (
        audit["validator_tool_registry_audit"]["validator_tool_count"]
        == audit["whole_repo_inventory_audit"]["category_counts"]["VALIDATOR_TOOL"]
    )
