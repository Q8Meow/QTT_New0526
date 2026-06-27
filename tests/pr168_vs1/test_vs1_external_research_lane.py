from __future__ import annotations

from ._helpers import rows


def test_vs1_external_research_lane_records_offline_skip_without_source_fact_authority():
    receipts = rows("external_research_candidate_receipts.jsonl")

    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["external_research_used_flag"] is False
    assert receipt["accepted_source_fact_flag"] is False
    assert receipt["connector_semantic_binding_flag"] is False
    assert receipt["fixture_constant_binding_flag"] is False
    assert receipt["runtime_dependency_flag"] is False
