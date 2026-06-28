"""RP5E non-authority execution boundary."""

from __future__ import annotations

from .models import BLOCKER_POLICY_REF, EXECUTION_AUTHORITY_REF, generated_ref, with_common


def build_execution_authority_report() -> dict[str, object]:
    payload = {
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "execution_mode": "STACK_GENERATION_AND_STACK_PREVIEW_ONLY",
        "self_audit_v4_boundary": {
            "paper_mode": "simulated orders/fills/portfolio only; no real exchange order state; no live submit",
            "live_dry_run": "future PR170 connector/risk/order-intent pipeline with submit disabled; no order write",
            "shadow_mode": "future triggered live-concurrent comparison lane after reliable live execution surface/live receipts; not paper; not pre-live gate; not authority",
            "limited_live_canary": "future owner-approved tiny real-order execution after paper loop and live dry-run gates",
            "rp5e": "stack preview, features, and handoffs only",
        },
        "rp5e_scope": "STACK_PREVIEW_FEATURE_HANDOFF_ONLY",
        "stack_preview_authorized": True,
        "feature_generation_authorized": True,
        "downstream_handoff_authorized": True,
        "trade_plan_simulation_authorized": False,
        "final_trade_ranking_authorized": False,
        "champion_selection_authorized": False,
        "order_variable_optimization_authorized": False,
        "paper_order_authority_authorized": False,
        "live_dryrun_execution_authorized": False,
        "shadow_execution_authorized": False,
        "limited_live_canary_execution_authorized": False,
        "limited_live_canary_authorized": False,
        "order_submit_cancel_replace_reduce_close_authorized": False,
        "connector_runtime_authorized": False,
        "connector_write_authorized": False,
        "private_state_fetch_authorized": False,
        "cash_runtime_authorized": False,
        "venue_api_call_authorized": False,
        "source_fact_acceptance_authorized": False,
        "qopt_execution_authorized": False,
        "quantum_backend_execution_authorized": False,
        "quantum_advantage_claim_authorized": False,
        "real_positive_negative_authorized": False,
        "qtt_sha_authority_authorized": False,
        "atomicrows_bundle_hash_reference_authorized": False,
        "execution_authority_statement": "RP5E enables stack computation and feature generation; it does not adjust order variables, select final trade scenarios, or create paper/live-dry-run/shadow/live order authority.",
        "blocker_policy_ref": BLOCKER_POLICY_REF,
    }
    return with_common(
        payload,
        row_id="RP5E_EXEC_AUTH_REPORT",
        owner_agent="GovernanceAgent",
        consumer_agents=["RP5EValidator", "CommanderAgent", "RiskAgent"],
        upstream_refs=[generated_ref("mode_boundary.jsonl")],
        downstream_refs=[generated_ref("run_receipt.report.json"), generated_ref("downstream.jsonl")],
    )
