from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_candidate_value_imputation_has_provenance():
    for row in load_records("PR163_C_CandidateValueImputationLedger.report.json"):
        assert row["source_class"]
        assert row["source_locator_or_artifact_ref"]
        assert row["observed_at_utc"]
        assert row["candidate_not_truth_flag"] is True
        assert row["replay_paper_only_flag"] is True
        assert row["connector_semantic_use_allowed"] is False
        assert row["live_use_allowed"] is False
