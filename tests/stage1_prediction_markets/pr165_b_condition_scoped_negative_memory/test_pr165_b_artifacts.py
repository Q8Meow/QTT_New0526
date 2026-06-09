from __future__ import annotations

from collections import Counter
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory import paths as p
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.json_io import read_json
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.negative_memory_action_policy import (
    AGENT_SELECTION_OVERLAY_ACTIONS,
    FORBIDDEN_OVERLAY_ACTIONS,
    MEMORY_ACTION_POLICIES,
    requires_repair,
    requires_retest,
)
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.negative_memory_status_vocab import (
    MEMORY_CLASSIFICATIONS,
    is_non_positive_memory,
)
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.report_sharding import load_report_records
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.validators import validate_artifacts


REPO_ROOT = Path(__file__).resolve().parents[3]


def _records(filename: str) -> list[dict]:
    payload = read_json(REPO_ROOT / p.GENERATED_DIR / filename)
    return load_report_records(REPO_ROOT, payload)


def test_pr165_b_generated_artifacts_validate():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:10]


def test_pr165_b_row_conservation_and_required_memory_classes():
    summary = _records("PR165_B_FinalSummary.report.json")[0]
    assert summary["memory_candidate_rows"] == 6502
    assert summary["condition_scoped_memory_rows"] == summary["memory_candidate_rows"]
    assert summary["condition_fingerprint_rows"] == 6502
    assert summary["combination_fingerprint_rows"] == 6502
    assert summary["scenario_outcome_rows"] == 6502
    assert summary["positive_memory_rows"] > 0
    assert summary["fragile_memory_rows"] > 0
    assert summary["global_ban_rows"] == 0
    assert summary["structural_invalidity_rows"] == 0
    assert summary["qku_untradable_rows"] == 0
    assert summary["permanent_rejection_rows"] == 0
    assert summary["authority_counts_all_0"] is True
    assert summary["orphan_counts_all_0"] is True
    assert summary["metadata_only_rows"] == 0
    assert summary["placeholder_only_rows"] == 0
    assert summary["unknown_status_rows"] == 0


def test_pr165_b_final_summary_splits_condition_caution_from_hard_negative():
    summary = _records("PR165_B_FinalSummary.report.json")[0]
    memory_rows = _records("PR165_B_CandidateVersionMemoryRegistry.report.json")
    class_counts = Counter(row["memory_classification"] for row in memory_rows)
    action_counts = Counter(row["memory_action_policy"] for row in memory_rows)
    reason_counts = Counter(reason for row in memory_rows for reason in row["reason_codes"])
    broad_non_positive_rows = sum(
        1 for row in memory_rows if is_non_positive_memory(row["memory_classification"])
    )

    assert len(memory_rows) == 6502
    assert summary["memory_candidate_rows"] == 6502
    assert summary["negative_memory_rows"] == broad_non_positive_rows
    assert summary["broad_non_positive_memory_rows"] == broad_non_positive_rows
    assert summary["condition_memory_caution_rows"] == broad_non_positive_rows
    assert summary["negative_memory_rows_are_qku_untradable_rows"] is False
    assert (
        summary["negative_memory_rows_semantics"]
        == "BACKWARD_COMPATIBILITY_ALIAS_FOR_BROAD_NON_POSITIVE_CONDITION_MEMORY_CAUTION_ROWS"
    )
    assert summary["hard_negative_memory_rows"] == 0
    assert summary["neutral_insufficient_evidence_rows"] == class_counts["NEUTRAL_INSUFFICIENT_EVIDENCE"]
    assert summary["neutral_insufficient_evidence_rows"] > 0
    assert summary["sparse_regime_watch_rows"] == reason_counts["PR165_B_SPARSE_REGIME_EVIDENCE"]
    assert summary["false_discovery_watch_rows"] == class_counts["FALSE_DISCOVERY_RISK_WATCH"]
    assert summary["repair_required_rows"] == sum(
        1 for row in memory_rows if requires_repair(row["memory_action_policy"])
    )
    assert summary["action_policy_retest_required_rows"] == sum(
        1 for row in memory_rows if requires_retest(row["memory_action_policy"])
    )
    assert summary["condition_scoped_cooldown_action_rows"] == action_counts["CONDITION_SCOPED_COOLDOWN"]
    assert summary["condition_scoped_avoid_action_rows"] == action_counts["AVOID_ONLY_WITHIN_MATCHING_CONDITION"]
    assert summary["condition_scoped_avoid_rows"] == summary["condition_memory_caution_rows"]
    assert summary["cooldown_rows"] == summary["condition_memory_caution_rows"]
    assert summary["retest_required_rows"] == summary["retest_queue_rows"]
    assert summary["replay_paper_retest_rows"] == summary["retest_queue_rows"]
    assert summary["top_negative_memory_categories"] == {}
    assert summary["global_ban_rows"] == 0
    assert summary["structural_invalidity_rows"] == 0
    assert summary["qku_untradable_rows"] == 0
    assert summary["permanent_rejection_rows"] == 0


def test_pr165_b_nonpositive_rows_have_policy_and_attribution_refs():
    memory_rows = _records("PR165_B_CandidateVersionMemoryRegistry.report.json")
    attribution_ids = {
        row["candidate_packet_id"]
        for row in _records("PR165_B_OutcomeAttributionLedger.report.json")
    }
    retest_ids = {
        row["candidate_packet_id"]
        for row in _records("PR165_B_ReplayPaperRetestQueue.report.json")
    }
    for row in memory_rows:
        assert row["memory_classification"] in MEMORY_CLASSIFICATIONS
        assert row["memory_action_policy"] in MEMORY_ACTION_POLICIES
        if not row["memory_classification"].startswith("POSITIVE"):
            assert row["candidate_packet_id"] in attribution_ids
            assert row["candidate_packet_id"] in retest_ids
            assert row["live_selection_allowed"] is False
            assert row["source_truth_conversion_by_PR165_B"] is False


def test_pr165_b_quantum_rows_have_no_backend_or_advantage_claims():
    quantum_rows = _records("PR165_B_QuantumNegativeMemoryRegistry.report.json")
    assert quantum_rows
    for row in quantum_rows:
        assert row["quantum_backend_execution_count"] == 0
        assert row["quantum_advantage_claim_count"] == 0
        assert row["quantum_failure_attribution"]


def test_pr165_b_agent_overlay_is_replay_paper_only():
    overlay_rows = _records("PR165_B_AgentSelectionOverlayHandoff.report.json")
    assert len(overlay_rows) == 6502
    for row in overlay_rows:
        assert row["overlay_action"] in AGENT_SELECTION_OVERLAY_ACTIONS
        assert row["overlay_action"] not in FORBIDDEN_OVERLAY_ACTIONS
        assert row["live_execution_allowed"] is False
        assert row["source_truth_accepted"] is False
        assert row["connector_bound"] is False
        assert row["private_state_used"] is False
        assert row["profit_evidence_created"] is False


def test_pr165_b_manifest_lists_all_reports_and_shards():
    manifest = _records("PR165_B_ReportManifest.report.json")
    assert {row["report_filename"] for row in manifest} == set(p.REPORT_FILENAMES)
    for row in manifest:
        root = read_json(REPO_ROOT / p.GENERATED_DIR / row["report_filename"])
        assert row["row_count"] == root["record_count"]
        assert row["shard_count"] == root["shard_count"]
