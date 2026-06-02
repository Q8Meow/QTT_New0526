from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import constants as c
from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.validator import validate_artifacts

from .test_support import REPO_ROOT, report


def test_pr162c_preflight_consumes_required_artifacts():
    result = validate_artifacts(REPO_ROOT)
    receipt = report(c.PREFLIGHT_REPORT_FILENAME)

    assert result.ok, result.failures
    assert receipt["PR136_control_plane_consumed"] is True
    assert receipt["PR162B_handoff_consumed"] is True
    assert receipt["PR162B_registry_baseline_consumed"] is True
    assert receipt["PR162A_repaired_state_consumed"] is True
    assert receipt["ci_offline_required"] is True
    assert receipt["online_discovery_allowed"] is True
    assert "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json" in receipt["required_inputs_missing"]
    assert receipt["fallback_paths_used"]
