"""PnL formulas and replay/paper receipt helpers for PR168-GFP."""

from __future__ import annotations


def net_expected_pnl_candidate(position_size: float, execution_adjusted_edge: float) -> float:
    return float(position_size) * float(execution_adjusted_edge)


def compute_replay_candidate_pnl(input_packet: dict[str, float]) -> dict[str, float | str]:
    pnl = net_expected_pnl_candidate(input_packet["position_size"], input_packet["execution_adjusted_edge"])
    return {"mode": "replay", "net_expected_pnl_candidate": pnl}


def compute_paper_candidate_pnl(input_packet: dict[str, float]) -> dict[str, float | str]:
    pnl = net_expected_pnl_candidate(input_packet["position_size"], input_packet["execution_adjusted_edge"])
    return {"mode": "paper", "net_expected_pnl_candidate": pnl}


def compare_replay_paper_pnl(replay_result: dict[str, float], paper_result: dict[str, float]) -> dict[str, float]:
    replay_pnl = float(replay_result["net_expected_pnl_candidate"])
    paper_pnl = float(paper_result["net_expected_pnl_candidate"])
    return {"replay_minus_paper": replay_pnl - paper_pnl}


def compute_before_after_delta(baseline_result: dict[str, float], recomputed_result: dict[str, float]) -> dict[str, float]:
    baseline = float(baseline_result["net_expected_pnl_candidate"])
    recomputed = float(recomputed_result["net_expected_pnl_candidate"])
    return {"before_after_delta": recomputed - baseline}


def compute_formula_retest_receipt(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_ref": candidate.get("canonical_row_key") or candidate.get("qku_id") or candidate.get("row_id"),
        "receipt_status": "FORMULA_RETEST_RECEIPT_CREATED_FROM_NUMERIC_INPUTS",
    }
