def test_transaction_cost_analysis_covers_universe(records, summary):
    rows = records("PR163_B_TransactionCostAnalysisCandidateRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["tca_status"] == "TCA_COMPLETE" for row in rows)
    assert all(row["cost_model_truth_status"] == "SYNTHETIC_FIXTURE_COST_MODEL" for row in rows)
