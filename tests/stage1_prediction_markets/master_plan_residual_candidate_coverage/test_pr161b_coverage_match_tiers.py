from .pr161b_test_support import candidate_records


def test_pr161b_coverage_match_tiers_do_not_treat_weak_text_as_full_coverage():
    for record in candidate_records():
        if record["coverage_match_tier"] == "TIER_4_WEAK_TEXT_MATCH_POSSIBLE_ONLY":
            assert record["residual_gap_flag"] is True
        assert record.get("coverage_proof", {}).get("weak_text_match_counted_as_full_coverage_flag") is False
