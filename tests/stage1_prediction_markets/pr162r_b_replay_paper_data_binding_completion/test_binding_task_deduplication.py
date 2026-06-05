def test_binding_task_deduplication(summary, records):
    rows = records("PR162R_B_BindingTaskDeduplicationAudit.report.json")
    tasks = [row for row in rows if row.get("binding_task_id")]
    assert summary["binding_task_deduplication_created"] is True
    assert len(tasks) == summary["unique_binding_tasks_count"]
    assert summary["deduplication_ratio"] >= 10
    assert all(task["impacted_missing_action_refs"] for task in tasks)
