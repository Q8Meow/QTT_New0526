from tests.pr168_rp5a._helpers import assert_rp5a_valid, load_report, _original_rp5a_read_context


def test_cross_graph_consistency() -> None:
    context = _original_rp5a_read_context()
    assert_rp5a_valid(builder_read_context=context)
    report = load_report("PR168_RP5A_CrossGraphConsistency.report.json")
    assert report["consistent_flag"] is True
