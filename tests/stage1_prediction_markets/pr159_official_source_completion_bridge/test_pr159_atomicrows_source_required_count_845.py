from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import atomicrows_records, master_report


def test_pr159_atomicrows_source_required_count_845():
    assert master_report()["atomicrows_source_required_target_count"] == 845
    assert len(atomicrows_records()) == 845

