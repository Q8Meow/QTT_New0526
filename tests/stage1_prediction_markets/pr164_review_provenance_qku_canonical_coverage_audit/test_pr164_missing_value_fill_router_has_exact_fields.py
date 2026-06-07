from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_missing_value_fill_router_has_exact_fields():
    rows = load_records("PR164_QKUMissingValueFillRouter.report.json")
    assert len(rows) == summary()["missing_value_fill_tasks_created"]
    for row in rows:
        assert row["exact_missing_field"] == "candidate_packet_v1_record"
        assert row["expected_type"]
        assert row["valid_range_or_domain"]
        assert row["candidate_source_targets"]
        assert row["route_to_pr162d_r3_or_pr162b_r_or_pr163c"]
