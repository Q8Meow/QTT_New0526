from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results import constants as c

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pr166_sm_required_reports_schemas_and_shards_exist(pr166_sm_payloads):
    for filename in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / filename).is_file()
        assert filename in pr166_sm_payloads
        assert pr166_sm_payloads[filename]["created_by_pr"] == c.PR_ID
        assert pr166_sm_payloads[filename]["schema_ref"] == c.REPORT_SCHEMA_REFS[filename]

    for schema_name in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / schema_name).is_file()

    shard_files = sorted((REPO_ROOT / c.SHARD_DIR).glob("*.json"))
    assert shard_files
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("*.sha256"))


def test_pr166_sm_summary_conserves_required_row_domains(pr166_sm_summary):
    assert pr166_sm_summary["roadmap_pr_id"] == "PR166-SM"
    assert pr166_sm_summary["score_refresh_row_count"] == 3985
    assert pr166_sm_summary["memory_refresh_row_count"] == 3985
    assert pr166_sm_summary["rank_delta_row_count"] == 3985
    assert pr166_sm_summary["condition_winner_count"] == 3985
    assert pr166_sm_summary["condition_loser_count"] == 3985
    assert pr166_sm_summary["repair_priority_count"] == 3985
    assert pr166_sm_summary["external_candidate_value_count"] == 11
    assert pr166_sm_summary["qku_computability_rows"] == 6502
    assert pr166_sm_summary["field_materialization_action_count"] == 6502
    assert pr166_sm_summary["agent_task_queue_rows"] == 7
    assert pr166_sm_summary["metadata_only_rows"] == 0
    assert pr166_sm_summary["placeholder_rows"] == 0
    assert pr166_sm_summary["unknown_status_rows"] == 0
    assert pr166_sm_summary["orphan_rows"] == 0
