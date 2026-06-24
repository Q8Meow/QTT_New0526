from tests.pr168_rp5a._helpers import assert_rp5a_valid, load_report


def test_cross_graph_consistency() -> None:
    assert_rp5a_valid()
    report = load_report("PR168_RP5A_CrossGraphConsistency.report.json")
    assert report["consistent_flag"] is True
