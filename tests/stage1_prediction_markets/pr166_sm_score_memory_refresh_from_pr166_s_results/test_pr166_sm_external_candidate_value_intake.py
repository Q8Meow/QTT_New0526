def test_pr166_sm_external_intake_is_candidate_provisional_only(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_ExternalCandidateValueIntakeRegistry.report.json"]
    assert len(rows) == 11
    assert {row["official_or_non_official"] for row in rows} >= {"OFFICIAL", "NON_OFFICIAL"}
    for row in rows:
        assert row["source_truth_acceptance"] is False
        assert row["connector_semantic_binding"] is False
        assert row["candidate_research_value"] is True
        assert row["replay_paper_route_required"] is True
        assert row["promotion_allowed_in_this_pr"] is False
        assert row["promotion_requires_downstream_review"] is True
        assert row["authority_class"] == "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH"
        assert row["source_url"].startswith("https://")
        assert row["downstream_route"] in row["downstream_pr_refs"]
