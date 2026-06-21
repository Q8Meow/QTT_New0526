#!/usr/bin/env python3
"""Full-universe computability classification for PR168-GFP2."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2_input_loader import GFP2Inputs, rp_gap_by_key, rp_negative_by_key


def all_qku_computability_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    negatives = rp_negative_by_key(inputs)
    gaps = rp_gap_by_key(inputs)
    rows: list[dict[str, Any]] = []
    for index, assignment in enumerate(inputs.assignments, start=1):
        key = str(assignment.get("canonical_row_key"))
        prior_negative = key in negatives
        gap_routed = key in gaps or not prior_negative
        formula_ids = list(assignment.get("formula_ids") or [])
        quantum_forward = any("QUBO" in fid or "BQM" in fid or "ISING" in fid or "CQM" in fid or "QUADPROGRAM" in fid for fid in formula_ids)
        classification = (
            "PRIOR_FAKE_NEGATIVE_REOPEN_REQUIRED"
            if prior_negative
            else "COMPUTABLE_AFTER_BINDING_REPAIR"
        )
        recovery_state = (
            "RECOVERY_ELIGIBLE_PENDING_REAL_DATA_RECOMPUTE"
            if prior_negative
            else "RECOVERY_ELIGIBLE_PENDING_FORMULA_BINDING_REPAIR"
        )
        row = {
            "qku_id": _qku_id(assignment),
            "qku_family": assignment.get("row_family"),
            "qku_type": "FORMULA_ASSIGNMENT_SURFACE",
            "candidate_packet_id": _candidate_packet_id(assignment),
            "atomic_row_id": _atomic_row_id(assignment),
            "formula_id": assignment.get("formula_id"),
            "formula_expression_ref": "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
            "formula_assignment_ref": assignment.get("source_row_pointer"),
            "formula_join_state": "FORMULA_ASSIGNED_FROM_PR168_GFP",
            "selection_state_before_gfp2": "SELECTED_35_FORMULA_LAYER_OR_PRIOR_RESULT_LAYER",
            "selection_state_after_gfp2": "FULL_UNIVERSE_REOPENED_PENDING_ACCEPTED_REAL_DATA",
            "selection_decision_reason_code": "SELECTED_35_ONLY_OR_PRIOR_RESULT_AUTHORITY_NOT_REAL_DATA_PROOF",
            "selection_decision_data_provenance_tier": "PROVENANCE_DOWNGRADED_PRIOR_RESULT"
            if prior_negative
            else "GAP_ROUTED",
            "previous_pr_ref": "PR168-RP" if prior_negative else "PR168-GFP",
            "previous_report_ref": "PR168_RP_ComputedNegativeEdgeCandidates.report.json"
            if prior_negative
            else "PR168_GFP_FormulaAssignmentMatrix.report.json",
            "previous_row_id": negatives.get(key, {}).get("result_ref") if prior_negative else key,
            "previous_artifact_path": "docs/master_plan/generated/PR168_RP_ComputedNegativeEdgeCandidates.report.json"
            if prior_negative
            else "docs/master_plan/generated/PR168_GFP_FormulaAssignmentMatrix.report.json",
            "previous_result_family": "computed_negative_edge" if prior_negative else "formula_assignment_gap",
            "old_classification": "COMPUTED_NEGATIVE_EDGE" if prior_negative else "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING",
            "old_authority_class": "INTERNAL_REPLAY_PAPER_COMPUTED_ONLY" if prior_negative else "FORMULA_ASSIGNMENT_ONLY",
            "old_evidence_tier": "REPO_LOCAL_GENERATED_EVIDENCE" if prior_negative else "GAP_ROUTED",
            "prior_result_supersession_state": "SUPERSEDED_BY_PR168_GFP2",
            "prior_result_authority_downgrade_reason": "ACCEPTED_REAL_MARKET_DATA_NOT_USED_FOR_PRIOR_NEGATIVE"
            if prior_negative
            else "REAL_DATA_PROOF_COMPONENTS_MISSING",
            "supersedes_previous_authority_flag": True,
            "historical_record_preserved_flag": True,
            "requires_real_market_recompute_flag": True,
            "prior_fake_positive_flag": False,
            "prior_fake_negative_flag": prior_negative,
            "prior_fake_neutral_zero_flag": False,
            "prior_metadata_only_noncomputable_flag": False,
            "prior_champion_authority_revoked_flag": False,
            "prior_no_trade_dominance_unproven_flag": False,
            "input_data_refs": [negatives.get(key, {}).get("input_ref")] if prior_negative else [],
            "input_data_tier": "REPO_LOCAL_GENERATED_EVIDENCE" if prior_negative else "GAP_ROUTED",
            "accepted_real_data_refs": [],
            "accepted_source_evidence_refs": [],
            "source_truth_accepted_flag": False,
            "source_candidate_flag": True,
            "official_source_flag": False,
            "non_official_source_flag": False,
            "web_research_source_flag": False,
            "social_research_source_flag": False,
            "owner_submitted_source_flag": False,
            "institutional_research_source_flag": False,
            "connector_semantic_binding_flag": False,
            "historical_trade_data_used_flag": False,
            "current_market_data_used_flag": False,
            "historical_orderbook_used_flag": False,
            "market_price_history_used_flag": False,
            "resolved_outcome_data_used_flag": False,
            "fee_model_used_flag": False,
            "slippage_model_used_flag": False,
            "fill_probability_model_used_flag": False,
            "latency_model_used_flag": False,
            "capacity_depth_model_used_flag": False,
            "settlement_payoff_semantics_used_flag": False,
            "synthetic_or_proxy_value_fields": [],
            "repo_local_generated_flag": prior_negative,
            "gap_filled_assumption_flag": gap_routed,
            "unverified_external_source_flag": False,
            "metadata_label_only_flag": False,
            "champion_wording_only_flag": False,
            "future_consumer_note_only_flag": False,
            "formula_plugin_ready_label_only_flag": False,
            "solver_or_quantum_compatible_label_only_flag": quantum_forward,
            "gap_fields": _gap_fields(prior_negative, quantum_forward),
            "gap_reason_codes": _gap_reasons(prior_negative, quantum_forward),
            "repair_queue_refs": [
                "PR168_GFP2_RealDataMissingProofComponentQueue.report.json",
                "PR168_GFP2_To_PR168_RP2_RealMarketReplayRecompute.report.json",
            ],
            "formula_executed_flag": prior_negative,
            "formula_execution_context": "PR168_RP_INTERNAL_REPLAY_PAPER" if prior_negative else "NOT_EXECUTED_INPUTS_MISSING",
            "formula_execution_receipt_ref": negatives.get(key, {}).get("result_ref") if prior_negative else None,
            "real_market_proof_state": "NOT_REAL_MARKET_PROOF",
            "numeric_evidence_refs": [negatives.get(key, {}).get("result_ref")] if prior_negative else [],
            "proof_eligible_flag": False,
            "proof_block_reason_codes": [
                "ACCEPTED_REAL_MARKET_DATA_ABSENT",
                "PRODUCTION_ACCEPTED_SOURCE_EVIDENCE_ABSENT",
                "NO_SYNTHETIC_PROXY_CANDIDATE_COMPONENT_RULE_NOT_SATISFIED",
            ],
            "real_positive_claim_allowed_flag": False,
            "real_negative_claim_allowed_flag": False,
            "champion_eligible": False,
            "live_candidate_worthy": False,
            "zero_positive_final_truth_allowed_flag": False,
            "classification_before_gfp2": "COMPUTED_NEGATIVE_EDGE" if prior_negative else "UNPROVEN_FORMULA_ASSIGNED",
            "classification_after_gfp2": classification,
            "downgrade_reason": "PRIOR_RESULT_LACKS_ACCEPTED_REAL_DATA_PROOF",
            "false_negative_risk_reason": "PRIOR_NEGATIVE_REOPENED_FOR_REAL_MARKET_RECOMPUTE"
            if prior_negative
            else "UNEXECUTED_GAP_COULD_HIDE_POSITIVE_OR_NEGATIVE",
            "recovery_eligibility_state": recovery_state,
            "recovery_diagnosis_refs": ["PR168_GFP2_RecoveryDimensionDiagnosis.report.json"],
            "recovery_action_refs": ["PR168_GFP2_NegativeCandidateRepairLadderQueue.report.json"],
            "downstream_repair_route": "PR168-RP2",
            "prior_result_downstream_recompute_route": "PR168-RP2",
            "prior_result_downstream_retest_route": "PR168-RANK2",
            "prior_result_agent_consumption_class": "historical_candidate_evidence;recompute_required_signal;not_live_authority",
            "optimizer_default_refs": ["PR168_GFP2_OptimizerDefaultAndParameterRangeSeed.report.json"],
            "parameter_range_candidate_refs": ["PR168_GFP2_OptimizerDefaultAndParameterRangeSeed.report.json"],
            "execution_adjusted_edge_seed": "GAP_ROUTED_TO_PR168_RP2",
            "fill_adjusted_expected_pnl_seed": "GAP_ROUTED_TO_PR168_RP2",
            "net_expected_pnl_candidate_seed": "GAP_ROUTED_TO_PR168_RP2",
            "lower_confidence_bound_edge_seed": "GAP_ROUTED_TO_PR168_RP2",
            "no_trade_margin_seed": "GAP_ROUTED_TO_PR168_RANK2",
            "tca_components_seed": "PR168_GFP2_TCADecompositionSeed.report.json",
            "capacity_crowding_status": "GAP_ROUTED_TO_PR168_RP2",
            "overfit_fdr_trial_family_id": "PR168_GFP2_TRIAL_FAMILY_PENDING",
            "portfolio_marginal_utility_cluster_id": "PR168_GFP2_PORTFOLIO_CLUSTER_PENDING",
            "regime_condition_id": "PR168_GFP2_REGIME_PENDING",
            "calibration_seed_ref": "PR168_GFP2_ProbabilityCalibrationSeed.report.json",
            "scenario_ladder_seed_ref": "PR168_GFP2_TradeOrderSimulationStackSpecQueue.report.json",
            "candidate_stack_spec_ref": "PR168_GFP2_CandidateStackSearchSpaceManifest.report.json",
            "order_policy_alternative_refs": ["PR168_GFP2_OrderPolicyAlternativeSeed.report.json"],
            "quantum_objective_state": "OBJECTIVE_EXPRESSION_PRESENT_COEFFICIENTS_GAP_ROUTED"
            if quantum_forward
            else "NOT_QUANTUM_OBJECTIVE_ROW",
            "quantum_variable_domain_state": "VARIABLE_DOMAINS_PENDING_BINDING" if quantum_forward else "NOT_APPLICABLE",
            "quantum_linear_coeff_state": "LINEAR_COEFFICIENTS_GAP_ROUTED" if quantum_forward else "NOT_APPLICABLE",
            "quantum_quadratic_coeff_state": "QUADRATIC_COEFFICIENTS_GAP_ROUTED" if quantum_forward else "NOT_APPLICABLE",
            "quantum_constraint_state": "CONSTRAINTS_GAP_ROUTED" if quantum_forward else "NOT_APPLICABLE",
            "quantum_penalty_scaling_state": "PENALTY_SCALING_GAP_ROUTED" if quantum_forward else "NOT_APPLICABLE",
            "quantum_qubo_bqm_cqm_ising_quadraticprogram_mapping_state": "GAP_ROUTED_NOT_BACKEND_EXECUTED"
            if quantum_forward
            else "NOT_APPLICABLE",
            "quantum_interpret_back_state": "INTERPRET_BACK_GAP_ROUTED" if quantum_forward else "NOT_APPLICABLE",
            "classical_fallback_state": "CLASSICAL_FALLBACK_REQUIRED_AND_AVAILABLE_AS_ROUTE",
            "classical_comparator_state": "CLASSICAL_COMPARATOR_REQUIRED_FOR_PR168_RANK2",
            "quantum_backend_execution_flag": False,
            "quantum_advantage_claim_flag": False,
            "agent_owner": assignment.get("owning_agent") or "Formula Materialization Agent",
            "agent_consumers": ["Replay Paper Recompute Agent", "Ranking Agent", "Governance Agent"],
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "validator_refs": ["tools/pr168_gfp2_validator.py"],
            "test_refs": ["tests/pr168_gfp2"],
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            "terminal_by_nature_flag": False,
            "terminal_reason_code": None,
            "authority_class": "PROVENANCE_DOWNGRADED_PRIOR_RESULT"
            if prior_negative
            else "FULL_UNIVERSE_GAP_ROUTED_PROOF_PENDING",
            "manual_edit_allowed_flag": False,
            "qtt_sha_or_atomicrows_hash_authority_flag": False,
            "row_index": index,
            "canonical_row_key": key,
            "formula_ids": formula_ids,
            "required_formula_set_id": assignment.get("required_formula_set_id"),
        }
        rows.append(row)
    return rows


def _qku_id(row: dict[str, Any]) -> str:
    key = str(row.get("canonical_row_key") or "")
    return key.removeprefix("QKU::") if key.startswith("QKU::") else key


def _candidate_packet_id(row: dict[str, Any]) -> str | None:
    if row.get("row_family") == "CandidatePacketV1":
        return str(row.get("source_row_pointer", "")).split(":", 1)[-1]
    return None


def _atomic_row_id(row: dict[str, Any]) -> str | None:
    qku_id = _qku_id(row)
    if qku_id.startswith("QKU-ATOMICROW-"):
        return qku_id.removeprefix("QKU-ATOMICROW-")
    return None


def _gap_fields(prior_negative: bool, quantum_forward: bool) -> list[str]:
    fields = [
        "accepted_historical_or_current_market_data",
        "accepted_orderbook_trade_resolution_fee_fill_slippage_latency_capacity_data",
        "replay_or_current_data_lock",
    ]
    if not prior_negative:
        fields.append("formula_input_bindings")
    if quantum_forward:
        fields.extend(["quantum_coefficients", "constraints", "penalty_scaling", "interpret_back_map"])
    return fields


def _gap_reasons(prior_negative: bool, quantum_forward: bool) -> list[str]:
    reasons = [
        "ACCEPTED_REAL_MARKET_DATA_ABSENT",
        "ACCEPTED_SOURCE_EVIDENCE_ABSENT_FOR_REAL_MARKET_PROOF",
    ]
    if prior_negative:
        reasons.append("PRIOR_INTERNAL_NEGATIVE_REOPEN_REQUIRED")
    else:
        reasons.append("FORMULA_INPUT_BINDING_REPAIR_REQUIRED")
    if quantum_forward:
        reasons.append("QUANTUM_STRUCTURAL_COEFFICIENT_OR_CONSTRAINT_GAP")
    return reasons
