from src.qtt.stage1_prediction_markets.pr162r_b_replay_paper_data_binding_completion.authority_policy import (
    validate_dedup_group_label,
)


def test_no_dedup_group_label_sha_hash_checksum(summary, records):
    tasks = [
        row
        for row in records("PR162R_B_BindingTaskDeduplicationAudit.report.json")
        if row.get("binding_task_id")
    ]
    assert summary["dedup_group_label_sha_hash_checksum_violation_count"] == 0
    assert all(validate_dedup_group_label(task["dedup_group_label"]).ok for task in tasks)
