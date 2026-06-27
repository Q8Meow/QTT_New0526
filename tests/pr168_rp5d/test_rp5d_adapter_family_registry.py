from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import ADAPTER_FAMILIES

from ._helpers import rows


def test_adapter_family_registry_has_owner_consumers_and_no_live_authority() -> None:
    families = rows("rp5d_adapter_family_registry.jsonl")
    by_ref = {str(row["adapter_family_ref"]): row for row in families}

    assert set(ADAPTER_FAMILIES) == set(by_ref)
    assert all(row["owner_agent_ref"] for row in families)
    assert all(row["consumer_agent_refs"] for row in families)
    assert all(row["live_authority_created_flag"] is False for row in families)
