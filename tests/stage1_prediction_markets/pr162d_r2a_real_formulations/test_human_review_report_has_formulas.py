from __future__ import annotations


def test_human_review_report_has_visible_real_formulations(records, repo_root):
    row = records("PR162D_R2A_HumanReviewTopFormulations.report.json")[0]
    assert row["formula_count"] >= 50
    assert row["algorithm_count"] >= 25
    assert row["quantum_count"] >= 25
    assert row["comparator_count"] >= 25
    text = (
        repo_root
        / "docs"
        / "master_plan"
        / "generated"
        / "PR162D_R2A_HumanReviewTopFormulations.report.md"
    ).read_text(encoding="utf-8")
    for token in ("YES_EV", "NO_EV", "IMPLIED_PROBABILITY", "KELLY", "BRIER", "RSI", "MACD", "VWAP", "QUBO", "CQM"):
        assert token in text
