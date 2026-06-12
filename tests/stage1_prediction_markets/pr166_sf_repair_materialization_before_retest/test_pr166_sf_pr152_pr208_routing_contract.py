def test_pr166_sf_summary_records_pr152_pr208_discipline(pr166_sf_summary):
    assert pr166_sf_summary["pr152_currentization_required"] is True
    assert pr166_sf_summary["pr152_currentization_run"] is True
    assert pr166_sf_summary["pr208_routing_mode"] == "FULL_VALIDATION_REQUIRED"
    assert pr166_sf_summary["timeout_ms_3600000_usage"] is True
