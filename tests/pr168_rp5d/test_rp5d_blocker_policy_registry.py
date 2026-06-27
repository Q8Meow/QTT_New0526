from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import BLOCKER_CODES

from ._helpers import rows


def test_blocker_policy_defines_every_required_productive_code() -> None:
    policies = rows("rp5d_blocker_policy_registry.jsonl")
    by_code = {str(row["blocker_code"]): row for row in policies}

    assert set(BLOCKER_CODES) == set(by_code)
    assert all(row["global_ban_allowed_flag"] is False for row in policies)
    assert all(row["formula_mutation_allowed_flag"] is False for row in policies)
    assert all(row["qku_deletion_allowed_flag"] is False for row in policies)
    assert all(row["adapter_queue_mapping"] or row["downstream_artifact_refs"] for row in policies)
