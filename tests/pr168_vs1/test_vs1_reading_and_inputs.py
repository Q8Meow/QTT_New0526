from __future__ import annotations

from ._helpers import rows


def test_vs1_reading_receipts_include_required_rp5c_and_correct_access_policy():
    reading = rows("vs1_reading_receipts.jsonl")
    paths = {row["file_ref"]: row for row in reading}

    corrected = "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl"
    incorrect = "docs/master_plan/generated/rp5c/agent_access_policy_registry.jsonl"

    assert corrected in paths
    assert paths[corrected]["read_status"] == "READ"
    assert incorrect not in paths
    assert all(row["read_status"] != "MISSING_REQUIRED" for row in reading)
    assert rows("vs1_crosswalk_discovery_receipts.jsonl")
