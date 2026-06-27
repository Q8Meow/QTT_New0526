from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import (
    ADAPTER_FAMILIES,
    QUEUE_FILE_BY_BLOCKER,
)

from ._helpers import rows


def test_adapter_queue_rows_map_to_central_families_and_create_no_authority() -> None:
    queue_files = sorted(set(QUEUE_FILE_BY_BLOCKER.values()))
    total = 0
    for filename in queue_files:
        for row in rows(filename):
            total += 1
            assert row["adapter_family_ref"] in ADAPTER_FAMILIES
            assert row["agent_owner_ref"]
            assert row["downstream_pr_refs"]
            assert row["live_authority_created_flag"] is False
            assert row["source_fact_acceptance_created_flag"] is False
            assert row["connector_binding_created_flag"] is False
    assert total > 0
