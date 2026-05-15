#!/usr/bin/env python3
"""Generate AtomicRows Repair PR D exact-row source JSONL files.

This generator writes only the 15 exact-row source family files. It does not
write bundles, hashes, freeze artifacts, final readiness artifacts, runtime
outputs, or source-evidence acceptances.
"""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_atomicrows_exact_row_generator_dry_run_manifest as dry_run_gate
from tools import validate_atomicrows_owner_approved_exact_15_family_count_distribution as c0_gate
from tools import validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest as c1_gate


REPO_ROOT = _REPO_ROOT
EXACT_ROW_SOURCES_DIR = pathlib.Path("docs/master_plan/atomic_rows/exact_row_sources")
FUTURE_BUNDLE_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
FUTURE_BUNDLE_SHA_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")

RECORD_TYPE = "ATOMICROWS_EXACT_ROW_SOURCE_RECORD"
RECORD_VERSION = "v1"
AUTHORITY_CLASS = (
    "EXACT_ROW_SOURCE_RECORD_INTERNAL_QTT_ARCHITECTURE_NOT_BUNDLE_NOT_RUNTIME_AUTHORITY"
)
MATERIALIZATION_STATE = "EXACT_ROW_SOURCE_MATERIALIZED_BY_REPAIR_PR_D"
BUNDLE_STATE = "NOT_BUNDLED_REPAIR_PR_E_REQUIRED"
SHA_FREEZE_STATE = "NOT_SHA_FROZEN_REPAIR_PR_F_REQUIRED"
FINAL_READINESS_STATE = "NOT_FINAL_READY_ROADMAP_PR_101_REQUIRED"

EXPECTED_TOTAL_ROWS = 4183
EXPECTED_FAMILY_COUNT = 15
EXPECTED_QUANTUM_FORWARD_TOTAL_ROWS = 1103
AGENT_GOVERNANCE_FAMILY_ID = "009_lifecycle_agent_binding"
AGENT_GOVERNANCE_FAMILY_ROWS = 270
SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_SOURCE_GENERATION_OK"

FAMILY_DISTRIBUTION: tuple[tuple[int, str, int], ...] = c0_gate.FAMILY_DISTRIBUTION
QUANTUM_FORWARD_FAMILY_IDS = set(c0_gate.QUANTUM_FAMILY_SLUGS)

ROW_CLASSES_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "001_signal_features": (
        "SIGNAL_FEATURE_TEMPLATE",
        "SIGNAL_TIME_WINDOW_POLICY",
        "FEATURE_TRANSFORM_POLICY",
        "MARKET_MICROSTRUCTURE_FEATURE_POLICY",
        "RESEARCH_INPUT_FEATURE_CANDIDATE",
        "SOURCE_REQUIRED_FEATURE_FIELD",
        "FEATURE_VALIDATION_POLICY",
        "FEATURE_BLOCK_CODE_POLICY",
    ),
    "002_scoring_ranking": (
        "SCORING_COMPONENT",
        "RANKING_POLICY",
        "TIE_BREAK_POLICY",
        "SCORE_NORMALIZATION_INPUT",
        "OWNER_PRIORITY_SCORE",
        "QUANTUM_BOOST_SCORE",
        "RANKING_BLOCK_CODE_POLICY",
        "SELECTION_SCORE_AUDIT_POLICY",
    ),
    "003_normalization_calibration": (
        "NORMALIZATION_METHOD",
        "CALIBRATION_METHOD",
        "SCALE_BOUND_POLICY",
        "CLIPPING_POLICY",
        "DRIFT_MONITOR_POLICY",
        "CALIBRATION_VALIDATION_POLICY",
        "NORMALIZATION_BLOCK_CODE_POLICY",
    ),
    "004_risk_control": (
        "RISK_LIMIT_POLICY",
        "DRAWDOWN_POLICY",
        "EXPOSURE_CAP_POLICY",
        "KILL_SWITCH_POLICY",
        "POSITION_BOUNDARY_POLICY",
        "OWNER_RISK_OVERRIDE_POLICY",
        "RISK_FAIL_CLOSED_POLICY",
    ),
    "005_execution_connector_boundary": (
        "EXECUTION_BOUNDARY_POLICY",
        "CONNECTOR_SOURCE_REQUIRED_FIELD",
        "ORDER_INTENT_NON_AUTHORITY",
        "ROUTING_BOUNDARY_POLICY",
        "FILL_INTEGRITY_SOURCE_REQUIRED",
        "LATENCY_COMPONENT_SOURCE_REQUIRED",
        "EXECUTION_BLOCK_CODE_POLICY",
    ),
    "006_capital_sizing_cash": (
        "SIZING_POLICY",
        "CASH_COMPONENT_SOURCE_REQUIRED",
        "CAPITAL_ALLOCATION_POLICY",
        "RESERVE_POLICY",
        "MARGIN_POLICY",
        "CASHFLOW_PNL_COMPONENT_SOURCE_REQUIRED",
        "CAPITAL_BLOCK_CODE_POLICY",
    ),
    "007_latency_routing": (
        "LATENCY_BUDGET_POLICY",
        "ROUTING_SELECTOR_POLICY",
        "HOT_PATH_EXCLUSION_POLICY",
        "CONTROL_PLANE_SNAPSHOT_POLICY",
        "FAIL_CLOSED_LATENCY_POLICY",
        "LATENCY_EVIDENCE_REQUIRED_POLICY",
    ),
    "008_error_guard_fail_closed": (
        "FAIL_CLOSED_POLICY",
        "ERROR_STATE_POLICY",
        "QUARANTINE_POLICY",
        "RETRY_REROUTE_POLICY",
        "VALIDATION_FAILURE_POLICY",
        "SAFE_DEGRADE_POLICY",
        "BLOCK_CODE_ESCALATION_POLICY",
    ),
    "009_lifecycle_agent_binding": (
        "AGENT_ELIGIBILITY_PLACEHOLDER",
        "AGENT_DUTY_POLICY",
        "AGENT_PERMISSION_BOUNDARY",
        "AGENT_KPI_POLICY",
        "OWNER_APPROVAL_REQUIRED",
        "D2_E0_MATRIX_PENDING",
        "AGENT_LIVE_AUTHORITY_BLOCK_POLICY",
    ),
    "010_source_evidence_connector_semantic": (
        "SOURCE_TARGET_FIELD_REQUIRED",
        "ACCEPTED_PACKET_REQUIRED",
        "CONNECTOR_BINDING_BLOCKED",
        "REVALIDATION_POLICY",
        "MATERIALITY_POLICY",
        "CONFLICT_RESOLUTION_POLICY",
        "SOURCE_TO_CONNECTOR_BLOCK_CODE_POLICY",
    ),
    "011_replay_paper_validation": (
        "REPLAY_INPUT_POLICY",
        "PAPER_INPUT_POLICY",
        "DUAL_LANE_SEPARATION",
        "RESULT_IMMUTABILITY_POLICY",
        "REVIEW_REQUIRED_POLICY",
        "NO_PROFIT_EVIDENCE_POLICY",
        "REPLAY_PAPER_BLOCK_CODE_POLICY",
    ),
    "012_quantum_advisory_optimization": (
        "QUANTUM_ADVISORY_OBJECTIVE_METADATA",
        "QUANTUM_CANDIDATE_TRIGGER_POLICY",
        "HYBRID_COMPARISON_POLICY",
        "QUANTUM_PRIORITY_METADATA",
        "OPTIMIZER_EVIDENCE_REQUIRED",
        "NO_BACKEND_EXECUTION_POLICY",
        "QUANTUM_ADVISORY_BLOCK_CODE_POLICY",
        "OWNER_QUANTUM_PRIORITY_POLICY_PENDING",
    ),
    "013_quantum_qubo_ising_metadata": (
        "QUBO_VARIABLE_METADATA",
        "QUBO_OBJECTIVE_METADATA",
        "QUBO_CONSTRAINT_PENALTY_POLICY",
        "ISING_MAPPING_METADATA",
        "EMBEDDING_METADATA",
        "BACKEND_EVIDENCE_REQUIRED",
        "QUBO_ISING_BLOCK_CODE_POLICY",
        "SOLVER_PARAMETER_SOURCE_REQUIRED",
    ),
    "014_quantum_qaoa_vqe_annealing_metadata": (
        "QAOA_DEPTH_METADATA",
        "QAOA_MIXER_METADATA",
        "QAOA_PARAMETER_METADATA",
        "VQE_ANSATZ_METADATA",
        "VQE_OPTIMIZER_METADATA",
        "ANNEALING_SCHEDULE_METADATA",
        "BACKEND_EVIDENCE_REQUIRED",
        "QAOA_VQE_ANNEALING_BLOCK_CODE_POLICY",
        "CIRCUIT_OR_SCHEDULE_PARAMETER_SOURCE_REQUIRED",
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        "PORTFOLIO_OBJECTIVE_METADATA",
        "RISK_RETURN_TRADEOFF_METADATA",
        "CVAR_DRAWDOWN_METADATA",
        "CLASSICAL_BASELINE_REQUIRED",
        "HYBRID_COMPARATOR_METADATA",
        "QUANTUM_ADVANTAGE_EVIDENCE_REQUIRED",
        "QUANTUM_PORTFOLIO_BLOCK_CODE_POLICY",
        "OWNER_APPROVED_PORTFOLIO_POLICY_REQUIRED",
    ),
}

QUANTUM_FAMILY_METADATA: dict[str, dict[str, str]] = {
    "012_quantum_advisory_optimization": {
        "quantum_metadata_class": "QUANTUM_ADVISORY_OPTIMIZATION_METADATA_ONLY",
        "quantum_strategy_surface": "ADVISORY_OBJECTIVE_AND_CANDIDATE_TRIGGER_METADATA_ONLY",
        "quantum_parameter_surface": "OBJECTIVE_WEIGHT_AND_CONSTRAINT_CLASSIFICATION_ONLY_NO_NUMERIC_DEFAULTS",
    },
    "013_quantum_qubo_ising_metadata": {
        "quantum_metadata_class": "QUBO_ISING_METADATA_ONLY",
        "quantum_strategy_surface": "QUBO_ISING_MAPPING_METADATA_ONLY",
        "quantum_parameter_surface": "VARIABLE_CONSTRAINT_PENALTY_EMBEDDING_CLASSIFICATION_ONLY_NO_NUMERIC_DEFAULTS",
    },
    "014_quantum_qaoa_vqe_annealing_metadata": {
        "quantum_metadata_class": "QAOA_VQE_ANNEALING_METADATA_ONLY",
        "quantum_strategy_surface": "CIRCUIT_ANSATZ_MIXER_DEPTH_SCHEDULE_METADATA_ONLY",
        "quantum_parameter_surface": "DEPTH_ANSATZ_MIXER_SCHEDULE_CLASSIFICATION_ONLY_NO_NUMERIC_DEFAULTS",
    },
    "015_quantum_portfolio_hybrid_comparator": {
        "quantum_metadata_class": "QUANTUM_PORTFOLIO_HYBRID_COMPARATOR_METADATA_ONLY",
        "quantum_strategy_surface": "PORTFOLIO_OBJECTIVE_RISK_RETURN_HYBRID_COMPARISON_METADATA_ONLY",
        "quantum_parameter_surface": "PORTFOLIO_OBJECTIVE_AND_RISK_TERM_CLASSIFICATION_ONLY_NO_NUMERIC_DEFAULTS",
    },
}

BASE_BLOCK_CODES: tuple[str, ...] = (
    "EXACT_ROW_SOURCE_MATERIALIZED_NOT_BUNDLE",
    "BUNDLE_NOT_CREATED",
    "BUNDLE_SHA_NOT_CREATED",
    "FREEZE_NOT_CREATED",
    "FINAL_READINESS_NOT_CREATED",
    "RUNTIME_AUTHORITY_NOT_CREATED",
    "LIVE_AUTHORITY_NOT_CREATED",
    "ORDER_AUTHORITY_NOT_CREATED",
    "AGENT_ELIGIBILITY_MATRIX_PENDING",
    "SOURCE_FACT_ACCEPTANCE_PENDING_WHEN_APPLICABLE",
    "CONNECTOR_SEMANTIC_BINDING_PENDING_WHEN_APPLICABLE",
    "REPLAY_PAPER_VALIDATION_PENDING_WHEN_APPLICABLE",
    "OPTIMIZER_EXECUTION_PENDING_WHEN_APPLICABLE",
    "OWNER_REVIEW_REQUIRED_BEFORE_LIVE_USE",
    "LOW_LATENCY_HOT_PATH_NOT_CREATED",
)

QUANTUM_BLOCK_CODES: tuple[str, ...] = (
    "QUANTUM_METADATA_ONLY_NOT_BACKEND_OUTPUT",
    "QUANTUM_BACKEND_EVIDENCE_PENDING_WHEN_APPLICABLE",
    "QUANTUM_ADVANTAGE_EVIDENCE_NOT_CREATED",
    "QUANTUM_LATENCY_SUPERIORITY_EVIDENCE_NOT_CREATED",
    "QUANTUM_EXECUTION_SUPERIORITY_EVIDENCE_NOT_CREATED",
    "QUANTUM_PROFIT_EVIDENCE_NOT_CREATED",
)


@dataclass(frozen=True)
class FamilyPlan:
    family_number: int
    family_id: str
    family_label: str
    row_count: int
    start_row_index: int
    end_row_index: int
    exact_rows_file_path: str
    quantum_forward_family_flag: bool
    agent_governance_family_flag: bool
    first_row_id: str
    last_row_id: str


def family_label(family_id: str) -> str:
    return family_id.split("_", 1)[1].upper()


def generate_row_id(family_id: str, family_row_ordinal: int) -> str:
    return dry_run_gate.generate_row_id_preview(family_id, family_row_ordinal)


def build_family_plans() -> tuple[FamilyPlan, ...]:
    plans: list[FamilyPlan] = []
    start = 1
    for family_number, family_id, row_count in FAMILY_DISTRIBUTION:
        end = start + row_count - 1
        file_path = f"{EXACT_ROW_SOURCES_DIR.as_posix()}/{family_id}.exact_rows.jsonl"
        plans.append(
            FamilyPlan(
                family_number=family_number,
                family_id=family_id,
                family_label=family_label(family_id),
                row_count=row_count,
                start_row_index=start,
                end_row_index=end,
                exact_rows_file_path=file_path,
                quantum_forward_family_flag=family_id in QUANTUM_FORWARD_FAMILY_IDS,
                agent_governance_family_flag=family_id == AGENT_GOVERNANCE_FAMILY_ID,
                first_row_id=generate_row_id(family_id, 1),
                last_row_id=generate_row_id(family_id, row_count),
            )
        )
        start = end + 1
    return tuple(plans)


def expected_file_names() -> tuple[str, ...]:
    return tuple(f"{family_id}.exact_rows.jsonl" for _, family_id, _ in FAMILY_DISTRIBUTION)


def authority_field_policy() -> dict[str, bool]:
    return {
        "row_is_exact_source_record": True,
        "row_is_bundle_record": False,
        "row_is_runtime_authority": False,
        "row_is_live_authority": False,
        "row_is_order_authority": False,
        "row_is_profit_authority": False,
        "row_is_connector_semantic_authority": False,
        "row_is_source_fact_authority": False,
        "row_is_sha_freeze_authority": False,
        "row_is_final_readiness_authority": False,
        "row_is_agent_assignment_authority": False,
        "row_is_optimizer_output_authority": False,
        "row_is_quantum_backend_output_authority": False,
    }


def source_pointer_policy() -> dict[str, Any]:
    return {
        "source_pointer_state": (
            "INTERNAL_ARCHITECTURE_ROW_OR_SOURCE_REQUIRED_WHEN_EXTERNAL_FACT_FIELD_USED"
        ),
        "source_fact_acceptance_state": "NOT_ACCEPTED",
        "accepted_source_packet_id": None,
        "external_fact_value_created": False,
        "connector_semantic_value_created": False,
        "runtime_cash_value_created": False,
        "source_required_for_external_fact_fields": True,
        "retrieval_receipt_created_by_this_row": False,
        "accepted_packet_created_by_this_row": False,
        "accepted_packet_required_before_connector_binding": True,
    }


def block_code_policy() -> dict[str, bool]:
    return {
        "fail_closed_default": True,
        "required_block_codes_present": True,
        "bundle_required_before_bundle_authority": True,
        "sha_freeze_required_before_freeze_authority": True,
        "final_readiness_required_before_final_authority": True,
        "source_acceptance_required_when_external_fact_needed": True,
        "replay_paper_required_when_validation_needed": True,
        "optimizer_execution_required_when_optimizer_output_needed": True,
        "quantum_backend_evidence_required_when_backend_claim_needed": True,
        "owner_approval_required_before_live_use": True,
        "agent_eligibility_matrix_required_before_agent_use": True,
    }


def agent_eligibility() -> dict[str, Any]:
    return {
        "agent_eligibility_required": True,
        "default_agent_eligibility_state": (
            "DENY_BY_DEFAULT_PENDING_REPAIR_PR_D2_E0_ELIGIBILITY_MATRIX"
        ),
        "specific_agent_family_assignments_created": False,
        "specific_agent_row_assignments_created": False,
        "live_order_agent_authority_created": False,
        "quantum_backend_agent_authority_created": False,
        "allowed_agent_ids": [],
        "blocked_by_default": True,
        "future_matrix_required": True,
        "future_matrix_pr": "REPAIR_PR_D2_E0_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX",
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "replay_execution_created": False,
        "paper_execution_created": False,
        "optimizer_execution_created": False,
        "classical_optimizer_execution_created": False,
        "quantum_inspired_optimizer_execution_created": False,
        "true_quantum_optimizer_execution_created": False,
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "quantum_provider_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_solver_execution_created": False,
        "ising_solver_execution_created": False,
        "live_order_execution_created": False,
        "runtime_cash_receipt_created": False,
        "private_state_fetch_created": False,
        "live_hot_path_dependency_created": False,
    }


def external_fact_boundary() -> dict[str, bool]:
    return {
        "external_fact_value_created": False,
        "accepted_source_packet_created": False,
        "connector_semantic_binding_created": False,
        "venue_api_semantics_created": False,
        "order_field_semantics_created": False,
        "fee_rule_semantics_created": False,
        "tick_rule_semantics_created": False,
        "payout_rule_semantics_created": False,
        "settlement_rule_semantics_created": False,
        "sdk_behavior_created": False,
        "rate_limit_semantics_created": False,
        "backend_option_fact_created": False,
        "provider_primitive_fact_created": False,
        "market_data_semantics_created": False,
        "historical_data_availability_created": False,
        "account_balance_semantics_created": False,
        "private_state_cash_semantics_created": False,
        "execution_lifecycle_semantics_created": False,
        "fill_integrity_semantics_created": False,
        "cashflow_pnl_semantics_created": False,
        "latency_component_semantics_created": False,
        "settlement_finality_semantics_created": False,
        "reconciliation_semantics_created": False,
        "cross_venue_normalization_semantics_created": False,
    }


def selection_and_scoring_boundary() -> dict[str, bool]:
    return {
        "selection_score_created": False,
        "ranking_created": False,
        "selected_stack_created": False,
        "optimizer_arbitration_created": False,
        "owner_override_receipt_created": False,
        "replay_paper_competition_created": False,
        "live_promotion_created": False,
        "future_scoring_prs_may_consume": True,
        "future_selection_prs_may_consume": True,
        "future_optimizer_arbitration_prs_may_consume": True,
        "current_row_is_static_source_inventory_only": True,
    }


def latency_boundary() -> dict[str, bool]:
    return {
        "low_latency_runtime_path_created": False,
        "live_pretrade_dependency_created": False,
        "runtime_router_dependency_created": False,
        "latency_superiority_evidence_created": False,
        "latency_budget_value_created": False,
        "control_plane_static_inventory_only": True,
        "future_low_latency_consumers_must_use_precomputed_bundle_snapshot": True,
    }


def risk_boundary() -> dict[str, bool]:
    return {
        "risk_limit_value_created": False,
        "exposure_authority_created": False,
        "capital_authority_created": False,
        "cash_component_value_created": False,
        "kill_switch_runtime_created": False,
        "owner_risk_review_required_before_live_use": True,
    }


def future_extension_policy() -> dict[str, Any]:
    return {
        "extension_policy_version": "v1",
        "future_parameter_addition_supported": True,
        "future_algorithm_addition_supported": True,
        "future_quantum_parameter_addition_supported": True,
        "future_research_agent_findings_supported": True,
        "future_owner_findings_supported": True,
        "extension_requires_versioned_pr": True,
        "extension_requires_schema_or_manifest_update": True,
        "extension_requires_validation_gate_update": True,
        "extension_may_not_create_live_authority_by_default": True,
        "extension_may_not_create_external_fact_by_default": True,
        "extension_may_not_create_quantum_backend_claim_by_default": True,
        "extension_may_not_create_profit_claim_by_default": True,
        "extension_namespace": "ATOMICROWS_FUTURE_EXTENSION_SLOT",
        "extension_slots": {
            "owner_research_extension_refs": [],
            "research_agent_extension_refs": [],
            "algorithm_extension_refs": [],
            "quantum_extension_refs": [],
            "source_evidence_extension_refs": [],
            "replay_paper_extension_refs": [],
            "risk_extension_refs": [],
            "latency_extension_refs": [],
        },
    }


def future_work() -> dict[str, bool]:
    return {
        "repair_pr_d2_e0_agent_family_eligibility_matrix_required": True,
        "repair_pr_e_bundle_materialization_required": True,
        "repair_pr_f_sha_freeze_required": True,
        "roadmap_pr_101_final_readiness_required": True,
        "exact_row_source_record_ready_for_bundle_builder": True,
        "bundle_builder_may_consume_after_repair_pr_e_owner_scope": True,
        "future_parameter_algorithm_extension_prs_allowed_after_owner_approval": True,
        "future_quantum_optimizer_extension_prs_allowed_after_owner_approval": True,
    }


def quantum_metadata(family_id: str) -> dict[str, Any]:
    if family_id not in QUANTUM_FORWARD_FAMILY_IDS:
        return {
            "quantum_forward_family_flag": False,
            "quantum_metadata_authority": "NOT_QUANTUM_FORWARD_FAMILY",
            "quantum_applicability_state": "NOT_QUANTUM_FORWARD_FAMILY",
            "quantum_backend_execution_created": False,
            "quantum_simulator_execution_created": False,
            "quantum_provider_execution_created": False,
            "qaoa_execution_created": False,
            "vqe_execution_created": False,
            "annealing_execution_created": False,
            "qubo_solver_execution_created": False,
            "ising_solver_execution_created": False,
            "quantum_advantage_claim_created": False,
            "quantum_latency_superiority_claim_created": False,
            "quantum_execution_superiority_claim_created": False,
            "quantum_profit_evidence_created": False,
            "future_quantum_extension_supported": False,
            "quantum_metadata_class": "NOT_QUANTUM_FORWARD_FAMILY",
            "quantum_strategy_surface": "NOT_QUANTUM_FORWARD_FAMILY",
            "quantum_parameter_surface": "NOT_QUANTUM_FORWARD_FAMILY",
        }
    metadata = {
        "quantum_forward_family_flag": True,
        "quantum_metadata_authority": "METADATA_ONLY_NOT_BACKEND_OUTPUT",
        "quantum_applicability_state": "QUANTUM_FORWARD_METADATA_ONLY",
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "quantum_provider_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_solver_execution_created": False,
        "ising_solver_execution_created": False,
        "quantum_advantage_claim_created": False,
        "quantum_latency_superiority_claim_created": False,
        "quantum_execution_superiority_claim_created": False,
        "quantum_profit_evidence_created": False,
        "future_quantum_extension_supported": True,
        "future_quantum_scoring_supported": True,
        "future_quantum_optimizer_arbitration_supported": True,
        "future_replay_paper_quantum_comparison_supported": True,
        "future_owner_quantum_priority_policy_supported": True,
    }
    metadata.update(QUANTUM_FAMILY_METADATA[family_id])
    return metadata


def block_codes(family_id: str) -> list[str]:
    codes = list(BASE_BLOCK_CODES)
    if family_id in QUANTUM_FORWARD_FAMILY_IDS:
        codes.extend(QUANTUM_BLOCK_CODES)
    return codes


def build_row_record(plan: FamilyPlan, family_row_ordinal: int) -> dict[str, Any]:
    row_index = plan.start_row_index + family_row_ordinal - 1
    row_classes = ROW_CLASSES_BY_FAMILY[plan.family_id]
    row_class = row_classes[(family_row_ordinal - 1) % len(row_classes)]
    subfamily_ordinal = 1 + ((family_row_ordinal - 1) // 25)
    subfamily_padded = f"{subfamily_ordinal:02d}"
    return {
        "agent_eligibility": agent_eligibility(),
        "authority_class": AUTHORITY_CLASS,
        "authority_field_policy": authority_field_policy(),
        "block_code_policy": block_code_policy(),
        "block_codes": block_codes(plan.family_id),
        "bundle_state": BUNDLE_STATE,
        "execution_boundary": execution_boundary(),
        "external_fact_boundary": external_fact_boundary(),
        "family_end_row_index": plan.end_row_index,
        "family_id": plan.family_id,
        "family_label": plan.family_label,
        "family_row_count": plan.row_count,
        "family_row_ordinal": family_row_ordinal,
        "family_start_row_index": plan.start_row_index,
        "final_readiness_state": FINAL_READINESS_STATE,
        "future_extension_policy": future_extension_policy(),
        "future_work": future_work(),
        "latency_boundary": latency_boundary(),
        "materialization_state": MATERIALIZATION_STATE,
        "quantum_metadata": quantum_metadata(plan.family_id),
        "record_type": RECORD_TYPE,
        "record_version": RECORD_VERSION,
        "risk_boundary": risk_boundary(),
        "row_class": row_class,
        "row_id": generate_row_id(plan.family_id, family_row_ordinal),
        "row_index": row_index,
        "row_index_padded": f"{row_index:04d}",
        "row_purpose": (
            f"Static exact-row source inventory for {plan.family_id}; not bundle, "
            "runtime, live, source-fact, connector, profit, or quantum-backend authority."
        ),
        "row_semantic_class": "STATIC_EXACT_ROW_SOURCE_INVENTORY",
        "row_title": f"{plan.family_label} exact source row {family_row_ordinal:04d}",
        "selection_and_scoring_boundary": selection_and_scoring_boundary(),
        "sha_freeze_state": SHA_FREEZE_STATE,
        "source_file_family_id": plan.family_id,
        "source_file_path": plan.exact_rows_file_path,
        "source_pointer_policy": source_pointer_policy(),
        "subfamily_id": f"{plan.family_id}__sf_{subfamily_padded}",
        "subfamily_label": f"{plan.family_label} subfamily {subfamily_padded}",
        "subfamily_ordinal": subfamily_ordinal,
    }


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return dry_run_gate.load_yaml(path)


def ensure_required_inputs(repo_root: pathlib.Path) -> None:
    required = (
        c0_gate.DEFAULT_CONFIG,
        c0_gate.DEFAULT_REPORT,
        dry_run_gate.DEFAULT_CONFIG,
        dry_run_gate.DEFAULT_REPORT,
        c1_gate.DEFAULT_CONFIG,
        c1_gate.DEFAULT_REPORT,
    )
    missing = [path.as_posix() for path in required if not (repo_root / path).exists()]
    if missing:
        raise RuntimeError("missing required repair-chain input(s): " + ", ".join(missing))

    c0_report = load_json(repo_root / c0_gate.DEFAULT_REPORT)
    dry_run_report = load_json(repo_root / dry_run_gate.DEFAULT_REPORT)
    c1_report = load_json(repo_root / c1_gate.DEFAULT_REPORT)
    if c0_report.get("validation_result") != c0_gate.VALIDATION_RESULT:
        raise RuntimeError("Repair PR C0 report is not exact-distribution ready")
    if dry_run_report.get("validation_result") != dry_run_gate.VALIDATION_RESULT:
        raise RuntimeError("Repair PR C dry-run report is not passing")
    if c1_report.get("validation_result") != c1_gate.VALIDATION_RESULT:
        raise RuntimeError("Repair PR C1 audit report is not passing")
    if dry_run_report.get("actual_dry_run", {}).get("would_generate_total_rows") != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Repair PR C dry-run total rows mismatch")
    if dry_run_report.get("actual_dry_run", {}).get("final_row_index") != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("Repair PR C dry-run final row index mismatch")

    if (repo_root / FUTURE_BUNDLE_PATH).exists():
        raise RuntimeError("AtomicRows.bundle.jsonl exists; Repair PR D must not create a bundle")
    if (repo_root / FUTURE_BUNDLE_SHA_PATH).exists():
        raise RuntimeError("AtomicRows.bundle.sha256 exists; Repair PR D must not create a bundle SHA")


def render_family_file_bytes(plan: FamilyPlan) -> bytes:
    rows = (
        json.dumps(build_row_record(plan, family_row_ordinal), sort_keys=True, separators=(",", ":"))
        for family_row_ordinal in range(1, plan.row_count + 1)
    )
    return ("\n".join(rows) + "\n").encode("utf-8")


def _normalize_jsonl_newlines(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def write_family_file(repo_root: pathlib.Path, plan: FamilyPlan) -> None:
    path = repo_root / pathlib.Path(plan.exact_rows_file_path)
    desired = render_family_file_bytes(plan)
    if path.exists() and _normalize_jsonl_newlines(path.read_bytes()) == desired:
        return
    path.write_bytes(desired)


def generate_exact_row_sources(repo_root: pathlib.Path = REPO_ROOT) -> tuple[FamilyPlan, ...]:
    repo_root = repo_root.resolve()
    ensure_required_inputs(repo_root)
    plans = build_family_plans()
    if len(plans) != EXPECTED_FAMILY_COUNT:
        raise RuntimeError("family plan count mismatch")
    if sum(plan.row_count for plan in plans) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError("family plan total rows mismatch")
    if sum(plan.row_count for plan in plans if plan.quantum_forward_family_flag) != (
        EXPECTED_QUANTUM_FORWARD_TOTAL_ROWS
    ):
        raise RuntimeError("quantum-forward row total mismatch")
    agent_plan = next(plan for plan in plans if plan.family_id == AGENT_GOVERNANCE_FAMILY_ID)
    if agent_plan.row_count != AGENT_GOVERNANCE_FAMILY_ROWS:
        raise RuntimeError("agent-governance family row count mismatch")

    output_dir = repo_root / EXACT_ROW_SOURCES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_names = set(expected_file_names())
    unexpected = sorted(
        path.name for path in output_dir.glob("*.exact_rows.jsonl") if path.name not in expected_names
    )
    if unexpected:
        raise RuntimeError("unexpected exact-row source file(s): " + ", ".join(unexpected))

    for plan in plans:
        write_family_file(repo_root, plan)
    return plans


def main(argv: Sequence[str] | None = None) -> int:
    _ = argv
    try:
        generate_exact_row_sources()
    except Exception as exc:
        print(f"QTT_ATOMICROWS_EXACT_ROW_SOURCE_GENERATION_FAILED: {exc}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
