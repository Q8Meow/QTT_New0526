def test_paper_execution_result_candidates(records, summary):
    rows = records("PR163_B_PaperExecutionResultCandidateRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert {row["lane"] for row in rows} == {"PAPER"}
