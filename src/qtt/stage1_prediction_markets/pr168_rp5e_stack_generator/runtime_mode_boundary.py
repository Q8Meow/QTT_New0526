"""Runtime-mode boundary rows for RP5E."""

from __future__ import annotations

from .models import generated_ref, with_common


def build_runtime_mode_boundaries() -> list[dict[str, object]]:
    rows = [
        {
            "mode_boundary_id": "RP5E_MODE_PAPER",
            "runtime_state": "PAPER_MODE",
            "stage1_required_flag": True,
            "stage1_enabled_in_rp5e_flag": False,
            "requires_live_execution_surface_flag": False,
            "requires_live_receipts_flag": False,
            "requires_owner_approval_flag": False,
            "requires_submit_disabled_flag": False,
            "simulated_orders": True,
            "simulated_fills": True,
            "real_exchange_order_state": False,
            "pre_live_gate_role_allowed_flag": True,
            "post_live_validation_role_flag": False,
            "allowed_trigger_family": ["future_paper_loop_request"],
            "future_pr_consumer": "PAPER-LOOP",
            "downstream_handoff_file": "to_paper.report.json",
        },
        {
            "mode_boundary_id": "RP5E_MODE_LIVE_DRYRUN",
            "runtime_state": "LIVE_DRYRUN_SUBMIT_DISABLED",
            "stage1_required_flag": True,
            "stage1_enabled_in_rp5e_flag": False,
            "requires_live_execution_surface_flag": True,
            "requires_live_receipts_flag": False,
            "requires_owner_approval_flag": True,
            "requires_submit_disabled_flag": True,
            "live_like_connector_risk_order_pipeline": True,
            "submit_disabled": True,
            "real_order_submission_allowed": False,
            "pre_live_gate_role_allowed_flag": True,
            "post_live_validation_role_flag": False,
            "allowed_trigger_family": ["future_pr170_live_dryrun"],
            "future_pr_consumer": "PR170-LIVE-DRYRUN",
            "downstream_handoff_file": "to_live_dry.report.json",
        },
        {
            "mode_boundary_id": "RP5E_MODE_SHADOW",
            "runtime_state": "SHADOW_LIVE_CONCURRENT_COMPARISON",
            "stage1_required_flag": False,
            "stage1_enabled_in_rp5e_flag": False,
            "requires_live_execution_surface_flag": True,
            "requires_live_receipts_flag": True,
            "requires_owner_approval_flag": True,
            "requires_submit_disabled_flag": False,
            "role": "LIVE_CONCURRENT_EXECUTION_COMPARISON_LANE",
            "required_before_limited_live_canary": False,
            "execution_enabled_in_rp5e_flag": False,
            "pre_live_gate_role_allowed_flag": False,
            "post_live_validation_role_flag": True,
            "may_replace_replay_or_paper_flag": False,
            "order_authority_source": "UNDERLYING_APPROVED_CANARY_OR_LIVE_SURFACE_ONLY",
            "allowed_trigger_family": [
                "owner_parameter_adjustment",
                "qtt_agent_parameter_adjustment",
                "candidate_value_adjustment",
                "risk_manager_escalation",
                "market_regime_drift",
                "venue_latency_fill_reject_throttle_drift",
                "canary_live_comparison_need",
            ],
            "future_pr_consumer": "TRIGGERED-SHADOW-COMPARISON",
            "downstream_handoff_file": "to_shadow.report.json",
        },
        {
            "mode_boundary_id": "RP5E_MODE_LIMITED_CANARY",
            "runtime_state": "LIMITED_LIVE_CANARY",
            "stage1_required_flag": False,
            "stage1_enabled_in_rp5e_flag": False,
            "requires_live_execution_surface_flag": True,
            "requires_live_receipts_flag": True,
            "requires_owner_approval_flag": True,
            "requires_submit_disabled_flag": False,
            "owner_approved_tiny_real_orders": True,
            "enabled_in_rp5e_flag": False,
            "pre_live_gate_role_allowed_flag": False,
            "post_live_validation_role_flag": False,
            "allowed_trigger_family": ["future_owner_approved_live_pilot"],
            "future_pr_consumer": "PR171-LIVE-PILOT",
            "downstream_handoff_file": "future.report.json",
        },
        {
            "mode_boundary_id": "RP5E_MODE_FULL_OR_SCALED_LIVE",
            "runtime_state": "FULL_OR_SCALED_LIVE",
            "stage1_required_flag": False,
            "stage1_enabled_in_rp5e_flag": False,
            "requires_live_execution_surface_flag": True,
            "requires_live_receipts_flag": True,
            "requires_owner_approval_flag": True,
            "requires_submit_disabled_flag": False,
            "pre_live_gate_role_allowed_flag": False,
            "post_live_validation_role_flag": False,
            "allowed_trigger_family": ["future_owner_approved_full_or_scaled_live"],
            "future_pr_consumer": "POST-RP5E-LIVE-SCOPE",
            "downstream_handoff_file": "future.report.json",
        },
    ]
    out = []
    for index, row in enumerate(rows, start=1):
        row.update(
            {
                "order_authority_allowed_in_rp5e_flag": False,
                "connector_write_allowed_in_rp5e_flag": False,
                "private_state_fetch_allowed_in_rp5e_flag": False,
                "runtime_cash_receipt_allowed_in_rp5e_flag": False,
                "may_replace_replay_or_paper_flag": row.get("may_replace_replay_or_paper_flag", False),
                "trigger_decision_receipt_required_flag": row["runtime_state"] == "SHADOW_LIVE_CONCURRENT_COMPARISON",
                "no_changed_scope_no_risk_escalation_result": "NO_SHADOW_RUN_REQUIRED",
            }
        )
        out.append(
            with_common(
                row,
                row_id=f"RP5E_MODE_BOUNDARY_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["CommanderAgent", "RiskAgent", "PaperExecutionAgent", "ShadowObservationAgent", "LiveDryRunAgent"],
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref(str(row["downstream_handoff_file"])), generated_ref("exec_auth.report.json")],
            )
        )
    return out
