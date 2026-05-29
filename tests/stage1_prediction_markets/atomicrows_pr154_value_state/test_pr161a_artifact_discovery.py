from src.qtt.stage1_prediction_markets.atomicrows_pr154_value_state.pr161a_materialization_bridge import artifact_discovery
from .pr161a_test_support import REPO_ROOT


def test_pr161a_artifact_discovery_consumes_required_maps():
    selected = artifact_discovery.selected_artifact_paths(REPO_ROOT)
    assert selected["fallback_crosswalk_path_used"] == "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
    assert selected["pr159s_report_map"]
    assert selected["pr82_pr86_quantum_scoring_optimizer_artifact_map"]

