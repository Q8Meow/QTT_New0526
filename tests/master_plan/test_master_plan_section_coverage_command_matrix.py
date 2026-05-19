from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools import build_master_plan_section_coverage_report as builder
from tools import validate_qtt_master_plan_section_coverage_command_matrix as matrix_gate


REPO_ROOT = Path(".")
MASTER_PLAN = Path("docs/master_plan/QTT_MasterPlan_Current.md")
REGISTRY = Path("docs/master_plan/completion/QTTSectionCoverageRegistry.yaml")


def _report() -> dict:
    return builder.build_report(
        repo_root=REPO_ROOT,
        master_plan=MASTER_PLAN,
        registry_path=REGISTRY,
    )


def test_command_matrix_is_compact_normalized_and_covers_crosswalk_once():
    report = _report()
    crosswalk_rows = report["roadmap_crosswalk"]["rows"]
    command_rows = report["command_matrix"]["rows"]
    summary = report["command_matrix_summary"]

    assert report["command_matrix"]["compact_normalized_command_matrix_flag"] is True
    assert len(command_rows) == len(crosswalk_rows)
    assert summary["command_matrix_row_count"] == len(command_rows)
    assert summary["pr120_crosswalk_row_count"] == len(crosswalk_rows)
    assert summary["missing_section_count"] == 0
    assert summary["duplicate_section_count"] == 0
    assert [row["section_id"] for row in command_rows] == [
        row["section_id"] for row in crosswalk_rows
    ]
    assert all("normalized_section_title" not in row for row in command_rows)


def test_command_matrix_preserves_static_no_authority_boundaries():
    report = _report()

    assert report["pr121_scope_summary"]["repo_canonical_pr_label"] == "PR121"
    assert report["pr121_scope_summary"]["roadmap_pr_label"] == "PR #104"
    assert report["pr121_scope_summary"]["blueprint_pr_label"] == "PR #104"
    assert (
        report["pr121_scope_summary"]["semantic_task_id"]
        == "ROADMAP-MASTER-PLAN-SECTION-COVERAGE-COMMAND-MATRIX"
    )
    assert report["pr121_scope_summary"]["roadmap_pr105_source_retrieval_executor_implemented"] is False

    for row in report["command_matrix"]["rows"]:
        assert row["no_command_execution_flag"] is True
        assert row["no_runtime_live_order_profit_authority_created_flag"] is True
        assert row["no_source_connector_replay_paper_authority_created_flag"] is True
        assert row["no_quantum_backend_or_simulator_execution_created_flag"] is True
        assert row["no_market_launch_authority_created_flag"] is True
        assert row["no_open_ended_future_market_taxonomy_flag"] is True
        assert row["no_master_plan_text_mutation_flag"] is True
        assert row["no_old_coverage_ledger_flag"] is True


def test_stage1_market_scope_and_future_market_deferral_stay_gated():
    report = _report()
    summary = report["command_matrix_summary"]
    central = report["central_config"]["stage1_prediction_market_only_rules"]

    assert central["stage1_launch_scope_locked_to_prediction_markets_flag"] is True
    assert central["stage1_active_market_ids"] == [
        "PREDICTION_MARKETS_GENERAL",
        "KALSHI",
        "POLYMARKET",
        "FORECASTEX_IBKR",
    ]
    assert central["stage2_market_selection_created_flag"] is False
    assert central["future_market_launch_authority_created_flag"] is False
    assert summary["forbidden_market_taxonomy_value_count"] == 0
    assert summary["market_launch_authority_created"] is False
    assert summary["stage2_market_selection_created"] is False

    future_market_rows = [
        row
        for row in report["command_matrix"]["rows"]
        if row["future_market_relevance"] == "FUTURE_MARKET_PLANNING_DEFERRED"
    ]
    assert all(
        row["command_family"]
        in {
            "FUTURE_MARKET_DEFERRED_COMMAND",
            "MARKET_INDEX_COMMAND",
            "UNRESOLVED_RESEARCH_COMMAND",
            "OWNER_REVIEW_COMMAND",
        }
        for row in future_market_rows
    )


def test_quantum_latency_source_runtime_rows_remain_future_gated_or_metadata_only():
    report = _report()

    for row in report["command_matrix"]["rows"]:
        quantum = row["quantum_forward_command_metadata"]
        assert quantum["no_backend_execution_flag"] is True
        assert quantum["no_simulator_execution_flag"] is True
        assert quantum["no_optimizer_runtime_execution_flag"] is True
        assert quantum["no_quantum_advantage_claim_flag"] is True
        assert quantum["no_profit_or_latency_superiority_claim_flag"] is True

        latency = row["latency_command_metadata"]
        assert latency["no_latency_superiority_claim_flag"] is True
        assert latency["no_profit_or_latency_superiority_claim_flag"] is True

        runtime = row["source_connector_runtime_command_metadata"]
        assert runtime["no_source_retrieval_flag"] is True
        assert runtime["no_source_fact_acceptance_flag"] is True
        assert runtime["no_connector_semantic_binding_flag"] is True
        assert runtime["no_runtime_authority_flag"] is True
        assert runtime["no_replay_paper_result_flag"] is True
        assert runtime["no_live_or_order_authority_flag"] is True


def test_command_matrix_validator_prints_success_marker():
    completed = subprocess.run(
        [sys.executable, "tools/validate_qtt_master_plan_section_coverage_command_matrix.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == matrix_gate.SUCCESS_MARKER
