def test_pr166_sm_summary_records_pr152_and_pr208_validation_stance(pr166_sm_summary):
    assert pr166_sm_summary["pr152_currentization_required"] is True
    assert pr166_sm_summary["pr152_currentization_run"] is True
    assert pr166_sm_summary["pr208_reduced_mode_used"] is False
    assert pr166_sm_summary["full_validation_required"] is True
    assert pr166_sm_summary["timeout_ms_3600000_used"] is True


def test_pr166_sm_connectivity_declares_validation_wiring_files(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_PRFileConnectivityAudit.report.json"]
    paths = {row["file_path"] for row in rows}
    assert "tools/run_validation_gates.py" in paths
    assert "tools/ci_branch_context.py" in paths
    assert "tools/build_pr166_sm_score_memory_refresh_from_pr166_s_results.py" in paths
    assert "tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py" in paths
    assert all("C:/" not in path and not path.startswith("/") for path in paths)
