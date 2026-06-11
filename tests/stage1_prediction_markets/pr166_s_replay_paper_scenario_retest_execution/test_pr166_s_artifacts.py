from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution.report_builder import build_payloads
from src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution.tests_support import summary_record
from src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution.validators import validate_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pr166_s_payloads_conserve_pr165_d_selected_universe():
    payloads = build_payloads(REPO_ROOT)
    summary = summary_record(payloads)

    assert summary["selected_batch_consumption_rows"] == 131
    assert summary["replay_episode_rows"] == 131
    assert summary["paper_episode_rows"] == 131
    assert summary["order_intent_rows"] == 3985
    assert summary["simulated_fill_rows"] == 3985
    assert summary["execution_cost_rows"] == 3985
    assert summary["result_attribution_rows"] == 3985
    assert summary["score_refresh_candidate_rows"] == 3985
    assert summary["memory_refresh_candidate_rows"] == 3985
    assert summary["repair_feedback_route_rows"] >= 2512
    assert summary["quantum_advisory_passthrough_rows"] == 6502
    assert summary["metadata_only_rows"] == 0
    assert summary["placeholder_rows"] == 0
    assert summary["unknown_status_rows"] == 0
    assert summary["orphan_counts_all_zero"] is True
    assert summary["authority_counts_all_zero"] is True


def test_pr166_s_build_never_executes_repair_before_retest_as_ready():
    payloads = build_payloads(REPO_ROOT)
    orders = set()
    for shard in payloads["PR166_S_OrderIntentRegistry.report.json"]["shard_files"]:
        # Validator coverage checks the persisted shard reader; this test only
        # checks the in-memory compact summary contract.
        assert shard.startswith("docs/master_plan/generated/pr166_s_shards/")
    summary = summary_record(payloads)
    assert summary["order_intent_rows"] == summary["pr165_d_selected_ready_retest_count"]
    assert summary["pr165_d_repair_before_retest_rows"] == 2512


def test_pr166_s_generated_artifacts_validate_after_build():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:10]
