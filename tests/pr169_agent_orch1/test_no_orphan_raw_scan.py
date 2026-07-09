from __future__ import annotations

from pathlib import Path

from tools import build_pr169_agent_orch1 as builder

from .conftest import REPO_ROOT, json_report, jsonl


def test_svc1_owner_actions_all_route_to_agent_tasks():
    upstream_path = REPO_ROOT / "docs/master_plan/generated/pr169_svc1/owner_action_requests.generated.jsonl"
    upstream_actions = {
        row.get("action_code") or row.get("action_id")
        for row in _jsonl_from(upstream_path)
        if row.get("action_code") or row.get("action_id")
    }
    owner_cmd_actions = {row["owner_action_ref_or_gap"] for row in jsonl("owner_cmd_tasks.jsonl")}
    assert upstream_actions <= owner_cmd_actions
    for row in jsonl("owner_cmd_tasks.jsonl"):
        assert row["owner_request_authority"] is True
        assert row["direct_venue_submit_authority"] is False
        assert row["execution_router_release_authority"] is False


def test_no_trade_tasks_are_reoptimization_not_dead_end():
    for file_name in ("notrade_tasks.jsonl", "var_tune_tasks.jsonl", "stack_tasks.jsonl", "venue_side_tasks.jsonl", "source_refresh_tasks.jsonl", "retest_tasks.jsonl"):
        for row in jsonl(file_name):
            routes = row["no_trade_recovery_route_refs"]
            assert row["terminal_no_trade"] is False
            assert any("variable" in route for route in routes)
            assert any("stack" in route for route in routes)
            assert any("venue" in route for route in routes)
            assert any("source" in route for route in routes)
            assert any("retest" in route for route in routes)
            assert row["safe_reoptimization_routes"]


def test_tournament_tasks_cover_required_roles_or_pr165_d2_gaps():
    for row in jsonl("tournament_tasks.jsonl"):
        assert set(builder.TOURNAMENT_ROLES) <= set(row["tournament_roles"])
        assert row["single_agent_self_authorization_allowed"] is False
        assert row["tournament_role_ref_or_gap"]
        assert all(ref.startswith("PR165_D2_GAP::") for ref in row["tournament_role_ref_or_gap"])
        assert row["disagreement_receipt_ref_or_gap"]


def test_no_orphan_raw_scan_and_quality_reports_pass():
    assert json_report("no_orphan.report.json")["pass"] is True
    raw = json_report("no_raw_scan.report.json")
    assert raw["runtime_raw_upstream_jsonl_scan_count"] == 0
    assert raw["resolver_reads_owned_prefix_only"] is True
    quality = json_report("quality.report.json")
    assert quality["superseded_content_check"]["superseded_uploaded_text_preserved"] is False
    assert quality["superseded_content_check"]["superseded_uploaded_text_reference_count"] == 0
    assert quality["filename_contains_future_or_hint_count"] == 0


def test_resolver_source_does_not_scan_raw_upstream_generated_files():
    text = (REPO_ROOT / "src/qtt/agents/pr169_agent_orch1_resolvers.py").read_text(encoding="utf-8")
    assert ".rglob(" not in text
    assert "pr169_svc1" not in text
    assert "pr169_pretrade1" not in text
    assert "pr169_readiness1" not in text
    assert "pr168_mem1" not in text


def _jsonl_from(path: Path) -> list[dict]:
    import json

    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
