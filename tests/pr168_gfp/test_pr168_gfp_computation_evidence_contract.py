from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.evidence import (
    build_computation_gap,
    classify_computation_evidence,
    missing_computed_evidence_fields,
)


def test_computed_status_requires_numeric_evidence_fields():
    row = {"new_truth_status": "COMPUTED_POSITIVE_EDGE", "canonical_row_key": "QKU::X"}

    assert classify_computation_evidence(row) == "INVALID_COMPUTED_STATUS_MISSING_NUMERIC_EVIDENCE"
    assert "input_values" in missing_computed_evidence_fields(row)


def test_formula_assigned_row_without_numeric_values_is_pending_not_computed():
    row = {
        "canonical_row_key": "QKU::X",
        "formula_id": "PR168_GFP_FORMULA_GROSS_EDGE",
        "new_truth_status": "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING",
    }

    assert classify_computation_evidence(row) == "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING"


def test_computation_gap_has_actionable_routes():
    gap = build_computation_gap(
        canonical_row_key="QKU::X",
        formula_id="PR168_GFP_FORMULA_GROSS_EDGE",
        missing_fields=["predicted_probability"],
        owning_agent="Formula Materialization Agent",
        downstream_route="PR168-RP",
    )

    assert gap["truth_status"] == "ACTIONABLE_COMPUTATION_GAP"
    assert gap["missing_fields"] == ["predicted_probability"]
    assert gap["input_materialization_route"] == "PR168-FM"
    assert gap["replay_paper_recompute_route"] == "PR168-RP"
