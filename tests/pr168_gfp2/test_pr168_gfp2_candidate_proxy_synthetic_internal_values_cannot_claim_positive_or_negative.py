from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_candidate_proxy_synthetic_internal_values_cannot_claim_positive_or_negative() -> None:
    for row in load("PR168_GFP2_ProxySyntheticGeneratedEvidenceAudit.report.json")[:1000]:
        assert row["real_positive_claim_allowed_flag"] is False
        assert row["real_negative_claim_allowed_flag"] is False
        assert row["repo_local_generated_flag"] is True
