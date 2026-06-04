from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.critical_missing_info_classifier import critical_missing_info


def test_pr162r_a_quantum_candidates_require_objective_variables_coefficients_for_quantum_eligibility(records):
    quantum = records("PR162R_A_QuantumReplayPaperEligibilityMatrix.report.json")
    assert quantum
    assert all(row["quantum_specific_mapping_ready_flag"] for row in quantum)
    bad = {
        "candidate_id": "SYNTHETIC_QUANTUM_BAD",
        "quantum_candidate_id": "SYNTHETIC_QUANTUM_BAD",
        "source_locator": "source://synthetic",
        "qku_refs": ["QKU_SYNTH"],
        "agent_refs": ["QUANTUM_ADVISORY_AGENT"],
        "replay_paper_route_refs": ["REPLAY_ENGINE_INPUT_PREP", "PAPER_ENGINE_INPUT_PREP"],
        "input_fields": ["x"],
        "output_fields": ["energy"],
        "units": "objective_energy",
        "mathematical_objective": "minimize x",
        "variable_definitions": {"x": "binary"},
    }
    assert "QUANTUM_MAPPING_MISSING" in critical_missing_info(bad)
