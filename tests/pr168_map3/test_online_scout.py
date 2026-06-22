from __future__ import annotations

from tests.pr168_map3._helpers import assert_minimum_counts, records


def test_online_scout_report_has_deep_structured_rows() -> None:
    rows = records("PR168_MAP3_OnlineScout.report.json")
    assert_minimum_counts()
    families = {row["query_family"] for row in rows}
    assert {
        "kalshi_venue_mechanics",
        "polymarket_venue_mechanics",
        "prediction_market_formulas",
        "execution_tca_fill_latency_capacity",
        "calibration_fdr_overfit",
        "portfolio_marginal_regime",
        "quantum_hybrid_optimization",
        "forecast_event_contracts",
    }.issubset(families)


def test_every_online_source_has_required_candidate_fields() -> None:
    required = {
        "scout_row_id",
        "source_url",
        "source_title",
        "source_tier",
        "retrieved_at_utc",
        "query_family",
        "useful_formula_or_input_found_flag",
        "formula_family_candidate",
        "candidate_expression_or_semantic_definition",
        "required_inputs_candidate",
        "data_family_requirements",
        "unit_requirements",
        "candidate_only_flag",
        "accepted_truth_flag",
        "source_evidence_review_route",
        "RP2_or_RANK2_route_if_computable",
        "rejected_flag",
        "reject_reason_if_any",
    }
    for row in records("PR168_MAP3_OnlineScout.report.json"):
        assert not (required - set(row)), row["scout_row_id"]
        assert row["candidate_only_flag"] is True
        assert row["accepted_truth_flag"] is False
        assert row["no_orphan_status"] == "NO_ORPHAN_LINKED"
