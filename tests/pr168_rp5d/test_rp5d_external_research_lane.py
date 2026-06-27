from __future__ import annotations

from ._helpers import rows


def test_external_research_lane_is_skip_or_candidate_only() -> None:
    research = rows("rp5d_external_research.jsonl")
    candidates = rows("rp5d_external_candidates.jsonl")

    assert research
    assert candidates
    for row in [*research, *candidates]:
        assert row["accepted_source_fact_flag"] is False
        assert row["connector_semantic_binding_flag"] is False
        assert row["fixture_constant_binding_flag"] is False
        assert row["live_order_authority_flag"] is False
