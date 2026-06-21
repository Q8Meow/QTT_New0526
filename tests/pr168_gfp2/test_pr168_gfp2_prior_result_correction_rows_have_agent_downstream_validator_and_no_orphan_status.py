from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_prior_result_correction_rows_have_agent_downstream_validator_and_no_orphan_status() -> None:
    for row in load("PR168_GFP2_PriorResultSupersessionLedger.report.json")[:1000]:
        assert row["downstream_agent_owner"]
        assert row["downstream_pr_refs"]
        assert row["validator_refs"]
        assert row["test_refs"]
        assert row["no_orphan_status"]
