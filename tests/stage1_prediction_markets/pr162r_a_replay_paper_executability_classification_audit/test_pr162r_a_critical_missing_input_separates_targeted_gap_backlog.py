from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.executability_classifier import classify_executability
from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.targeted_gap_backlog import critical_gap_records


def test_pr162r_a_critical_missing_input_separates_targeted_gap_backlog(summary):
    bad = {
        "candidate_id": "SYNTHETIC_FORMULA_MISSING",
        "source_locator": "source://synthetic",
        "qku_refs": ["QKU_SYNTH"],
        "agent_refs": ["REPLAY_ENGINE_INPUT_PREP"],
        "replay_paper_route_refs": ["REPLAY_ENGINE_INPUT_PREP", "PAPER_ENGINE_INPUT_PREP"],
        "input_fields": ["x"],
        "output_fields": ["y"],
        "units": "unitless",
        "metadata_only_flag": False,
    }
    classification = classify_executability(bad)
    backlog = critical_gap_records([classification])
    assert summary["targeted_pr162d_r2_critical_gap_backlog_count"] == 0
    assert classification["primary_executability_state"] == "NON_EXECUTABLE_FORMULA_OR_ALGORITHM_MISSING"
    assert backlog[0]["target_pr"] == "PR162D_R2"
