from __future__ import annotations

from tools import build_pr169_agent_orch1 as builder

from .conftest import json_report, jsonl


def test_no_forbidden_authority_fields_are_widened():
    rows = jsonl("registry.jsonl")
    for row in rows:
        for field in builder.AUTHORITY_FALSE_FIELDS + builder.LIVE_PATH_FALSE_FIELDS:
            if field in row:
                assert row[field] is False, f"{field} widened in {row['row_id']}"
        assert row["runtime_side_effect_allowed"] is False
        assert row["control_plane_only"] is True


def test_authority_proof_reports_have_zero_true_counts():
    for file_name in (
        "no_direct_submit.report.json",
        "no_llm_runtime.report.json",
        "no_paper_exec.report.json",
        "no_live_exec.report.json",
        "no_fake_receipts.report.json",
        "no_source_truth.report.json",
        "no_private_cash.report.json",
        "no_qbackend.report.json",
        "no_qtt_sha.report.json",
        "no_pr_collapse.report.json",
    ):
        report = json_report(file_name)
        assert report["pass"] is True
        assert report["fail_closed_reasons"] == []
        for count in report["authority_true_counts"].values():
            assert count == 0


def test_prep_routes_do_not_create_downstream_runtime_systems():
    for row in jsonl("paper_prep.jsonl"):
        assert row["paper_loop_owner_pr"] == "PR169-PAPER-LOOP"
        assert row["required_downstream_receipts"]
        assert row["paper_execution_created"] is False
    for row in jsonl("hotpath_prep.jsonl"):
        assert row["fresh_snapshot_required"] is True
        assert row["runtime_recompute_required"] is False
        assert row["runtime_cache_created"] is False
    for row in jsonl("shadow_prep.jsonl"):
        assert row["shadow_candidate_ref_or_gap"]
        assert row["paper_comparison_route_ref_or_gap"]
        assert row["live_dryrun_route_ref_or_gap_for_shadow"]
        assert row["shadow_execution_created"] is False
        assert row["live_execution_created"] is False
    for row in jsonl("live_prep.jsonl"):
        assert row["execution_router_final_check_ref_or_gap"]
        assert row["live_execution_created"] is False
        assert row["execution_router_release_created"] is False
