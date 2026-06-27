from __future__ import annotations

from ._helpers import rows


def test_reading_receipts_include_corrected_rp5c_access_policy_path() -> None:
    receipts = rows("rp5d_reading_receipts.jsonl")
    paths = {str(row["file_ref"]) for row in receipts}

    assert "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl" in paths
    assert "docs/master_plan/generated/rp5c/agent_access_policy_registry.jsonl" not in paths


def test_pr165_discovery_is_recorded_without_mutating_pr165_artifacts() -> None:
    inventory = rows("rp5d_input_inventory.jsonl")
    pr165_rows = [row for row in inventory if row["surface_family"] == "PR165_D2_AGENT_DUTY"]

    assert pr165_rows
    assert all(row["consumer_pr_ref"] == "PR168_RP5D" for row in pr165_rows)
