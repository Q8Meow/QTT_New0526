from src.qtt.stage1_prediction_markets.master_plan_residual_candidate_coverage.pr161a_coverage_index import build_pr161a_coverage_index

from .pr161b_test_support import REPO_ROOT


def test_pr161b_pr161a_coverage_index_consumes_pr161a_reports():
    index = build_pr161a_coverage_index(REPO_ROOT)
    assert len(index["field_records"]) == 22625
    assert len(index["atomicrow_ids"]) == 4183
    assert len(index["pr154_target_ids"]) == 342
    assert len(index["quantum_profiles"]) == 41
