from __future__ import annotations

import importlib

import pytest

from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import formula_by_id


def _call(callable_ref: str, inputs: dict):
    module_name, attr = callable_ref.split(":", 1)
    return getattr(importlib.import_module(module_name), attr)(inputs)


def test_formula_compute_functions_match_vectors(records):
    vectors = {
        row["test_vector_id"]: row
        for row in records("PR162D_R2A_TestVectorRegistry.report.json")
    }
    formulas = [
        row for row in records("PR162D_R2A_FormulationRecordRegistry.report.json")
        if row["formulation_type"] in {"FORMULA", "FEATURE"}
    ]
    for row in formulas:
        vector = vectors[row["test_vector_refs"][0]]
        assert _call(row["callable_ref"], dict(vector["inputs"])) == vector["expected_outputs"]


def test_mandatory_formula_examples_have_expected_values():
    formulas = formula_by_id()
    assert formulas["YES_EV"].compute(formulas["YES_EV"].test_inputs)["yes_ev"] == pytest.approx(0.075)
    assert formulas["NO_EV"].compute(formulas["NO_EV"].test_inputs)["no_ev"] == pytest.approx(-0.025)
    assert formulas["IMPLIED_PROBABILITY"].compute({"price": 0.43, "payout": 1.0})["implied_probability"] == 0.43
    assert round(formulas["KELLY_CAPPED"].compute(formulas["KELLY_CAPPED"].test_inputs)["kelly_capped"], 10) == 0.1
    assert formulas["BRIER_SCORE"].compute(formulas["BRIER_SCORE"].test_inputs)["brier_score"] == pytest.approx(0.0375)
