from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_report, atomic_records


def test_pr157_atomicrows_4183_universe_reconciles():
    report = atomic_report()
    assert report["atomicrows_total_universe_count"] == 4183
    assert report["processed_count"] == 4183
    assert report["sharded_count"] == 4183
    assert len(atomic_records()) == 4183
    assert report["count_reconciliation_passed_flag"] is True
