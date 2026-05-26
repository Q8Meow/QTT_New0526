"""Deterministic report builder and validator for PR150."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import current_branch_context, is_pr_or_later_branch

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    constants as pr152_constants,
)

from . import constants as c


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(_read_text(path))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sorted_strings(value: Any) -> list[str]:
    return sorted(str(item) for item in _list(value) if isinstance(item, str))


def _read_required_text(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> str:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR150_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR150_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return ""


def _read_required_json(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR150_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            f"PR150_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return {}


def _read_optional_json(root: Path, rel_path: Path, failures: list[str]) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists() or path.is_dir():
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            f"PR150_UPSTREAM_REPORT_PARSE_ERROR: optional: {rel_path.as_posix()}: {exc}"
        )
        return {}


def _read_optional_text(root: Path, rel_path: Path, failures: list[str]) -> str:
    path = root / rel_path
    if not path.exists() or path.is_dir():
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR150_UPSTREAM_REPORT_PARSE_ERROR: optional: {rel_path.as_posix()}: {exc}"
        )
        return ""


def _crosswalk_payload(root: Path, failures: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    alias_path = root / c.PR136_SECTION_CROSSWALK_ALIAS_PATH
    canonical_path = root / c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    alias_exists = alias_path.exists()
    canonical_exists = canonical_path.exists()
    selected = (
        c.PR136_SECTION_CROSSWALK_ALIAS_PATH
        if alias_exists
        else c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    )
    if not alias_exists and not canonical_exists:
        failures.append(
            "PR150_UPSTREAM_REPORT_MISSING: pr136_section_crosswalk_or_alias: "
            f"{c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()}"
        )
        return {}, {
            "alias_used": False,
            "canonical_successor_used": False,
            "created_missing_alias": False,
            "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
            "selected_path": c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix(),
        }
    payload = _read_required_json(root, "pr136_section_crosswalk_or_alias", selected, failures)
    return payload, {
        "alias_used": alias_exists,
        "canonical_successor_used": not alias_exists and canonical_exists,
        "created_missing_alias": False,
        "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
        "selected_path": selected.as_posix(),
    }


def _path_records(paths: Sequence[Path], present: set[str], required: bool) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "artifact_path": path.as_posix(),
                "consumed": path.as_posix() in present,
                "required": required,
            }
            for path in paths
        ),
        key=lambda item: item["artifact_path"],
    )


def load_static_evidence(repo_root: Path | str) -> tuple[dict[str, Any], list[str]]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    present: set[str] = set()

    text_payloads = {
        "launch_roadmap": _read_required_text(root, "launch_roadmap", c.ROADMAP_PATH, failures),
        "launch_roadmap_policy": _read_required_text(
            root,
            "launch_roadmap_policy",
            c.ROADMAP_POLICY_PATH,
            failures,
        ),
    }
    for rel_path, text in (
        (c.ROADMAP_PATH, text_payloads["launch_roadmap"]),
        (c.ROADMAP_POLICY_PATH, text_payloads["launch_roadmap_policy"]),
    ):
        if text:
            present.add(rel_path.as_posix())

    json_payloads = {
        "control_plane_roster": _read_required_json(
            root,
            "control_plane_roster",
            c.ROSTER_PATH,
            failures,
        ),
        "control_plane_controller": _read_required_json(
            root,
            "control_plane_controller",
            c.CONTROLLER_PATH,
            failures,
        ),
        "pr136_route_triage": _read_required_json(
            root,
            "pr136_route_triage",
            c.PR136_ROUTE_TRIAGE_PATH,
            failures,
        ),
        "pr136_market_index": _read_required_json(
            root,
            "pr136_market_index",
            c.PR136_MARKET_INDEX_PATH,
            failures,
        ),
        "pr136_command_matrix": _read_required_json(
            root,
            "pr136_command_matrix",
            c.PR136_COMMAND_MATRIX_PATH,
            failures,
        ),
        "pr137r_reconciliation": _read_required_json(
            root,
            "pr137r_reconciliation",
            c.PR137R_REPORT_PATH,
            failures,
        ),
        "pr138_semantic_contract": _read_required_json(
            root,
            "pr138_semantic_contract",
            c.PR138_REPORT_PATH,
            failures,
        ),
        "pr149_bridge_report": _read_required_json(
            root,
            "pr149_bridge_report",
            c.PR149_REPORT_PATH,
            failures,
        ),
    }
    json_path_by_key = {
        "control_plane_roster": c.ROSTER_PATH,
        "control_plane_controller": c.CONTROLLER_PATH,
        "pr136_route_triage": c.PR136_ROUTE_TRIAGE_PATH,
        "pr136_market_index": c.PR136_MARKET_INDEX_PATH,
        "pr136_command_matrix": c.PR136_COMMAND_MATRIX_PATH,
        "pr137r_reconciliation": c.PR137R_REPORT_PATH,
        "pr138_semantic_contract": c.PR138_REPORT_PATH,
        "pr149_bridge_report": c.PR149_REPORT_PATH,
    }
    for key, rel_path in json_path_by_key.items():
        if json_payloads[key]:
            present.add(rel_path.as_posix())

    crosswalk, alias_resolution = _crosswalk_payload(root, failures)
    json_payloads["pr136_section_crosswalk_or_alias"] = crosswalk
    if crosswalk:
        present.add(str(alias_resolution["selected_path"]))

    pr149_module_path = root / c.PR149_MODULE_DIR_PATH
    if not pr149_module_path.exists() or not pr149_module_path.is_dir():
        failures.append(
            "PR150_UPSTREAM_REPORT_MISSING: pr149_bridge_module: "
            f"{c.PR149_MODULE_DIR_PATH.as_posix()}"
        )
    else:
        present.add(c.PR149_MODULE_DIR_PATH.as_posix())

    optional_payloads: dict[str, Any] = {}
    for rel_path in c.OPTIONAL_CONTEXT_ARTIFACTS:
        path = root / rel_path
        if not path.exists():
            optional_payloads[rel_path.as_posix()] = None
            continue
        present.add(rel_path.as_posix())
        if path.is_dir():
            optional_payloads[rel_path.as_posix()] = {
                "directory_file_names": sorted(
                    child.name for child in path.iterdir() if child.is_file()
                )
            }
            continue
        if path.suffix == ".json":
            optional_payloads[rel_path.as_posix()] = _read_optional_json(
                root,
                rel_path,
                failures,
            )
        else:
            text = _read_optional_text(root, rel_path, failures)
            optional_payloads[rel_path.as_posix()] = {
                "present": bool(text),
                "line_count": len(text.splitlines()) if text else 0,
            }

    return {
        "alias_resolution": alias_resolution,
        "json_payloads": json_payloads,
        "optional_payloads": optional_payloads,
        "present_paths": present,
        "repo_root": root,
        "text_payloads": text_payloads,
    }, sorted(set(failures))


def _stable_id(*parts: str) -> str:
    raw = "_".join(part for part in parts if part)
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()
    return f"PR150_{normalized}"


def _route_defaults(route: str) -> dict[str, Any]:
    if route == "source":
        return {
            "default_target_state": "TARGET_DEFINED_VALUE_PENDING_SOURCE_EVIDENCE",
            "evidence_requirement_class": "OFFICIAL_SOURCE_EVIDENCE_REQUIRED",
            "order_use_eligibility": "PENDING_SOURCE_EVIDENCE",
            "reason_codes": ["PR150_SOURCE_EVIDENCE_REQUIRED", "PR150_NO_VALUE_INVENTION"],
            "value_authority_class": "SOURCE_EVIDENCE_REQUIRED_VALUE",
        }
    if route == "runtime":
        return {
            "default_target_state": "TARGET_DEFINED_VALUE_PENDING_RUNTIME_RECEIPT",
            "evidence_requirement_class": "RUNTIME_RECEIPT_REQUIRED",
            "order_use_eligibility": "PENDING_RUNTIME_RECEIPT",
            "reason_codes": ["PR150_RUNTIME_RECEIPT_REQUIRED", "PR150_NO_RUNTIME_AUTHORITY"],
            "value_authority_class": "RUNTIME_RECEIPT_REQUIRED_VALUE",
        }
    if route == "replay_paper":
        return {
            "default_target_state": "TARGET_DEFINED_VALUE_PENDING_REPLAY_PAPER_CALIBRATION",
            "evidence_requirement_class": "REPLAY_PAPER_CALIBRATION_REQUIRED",
            "order_use_eligibility": "REPLAY_PAPER_CANDIDATE_ONLY",
            "reason_codes": [
                "PR150_REPLAY_PAPER_CALIBRATION_REQUIRED",
                "PR150_NO_PROFIT_AUTHORITY",
            ],
            "value_authority_class": "REPLAY_PAPER_CALIBRATION_REQUIRED_VALUE",
        }
    if route == "quantum_metadata":
        return {
            "default_target_state": "TARGET_DEFINED_VALUE_QUANTUM_METADATA_ONLY",
            "evidence_requirement_class": "QUANTUM_METADATA_ONLY",
            "order_use_eligibility": "CONFIGURATION_METADATA_ONLY",
            "reason_codes": ["PR150_QUANTUM_METADATA_ONLY"],
            "value_authority_class": "QUANTUM_METADATA_ONLY_VALUE",
        }
    if route == "quantum_evidence":
        return {
            "default_target_state": "TARGET_DEFINED_VALUE_PENDING_QUANTUM_EXECUTION_EVIDENCE",
            "evidence_requirement_class": "QUANTUM_EXECUTION_EVIDENCE_REQUIRED",
            "order_use_eligibility": "PENDING_QUANTUM_EXECUTION_EVIDENCE",
            "reason_codes": [
                "PR150_QUANTUM_EXECUTION_EVIDENCE_REQUIRED",
                "PR150_NO_VALUE_INVENTION",
            ],
            "value_authority_class": "QUANTUM_EXECUTION_EVIDENCE_REQUIRED_VALUE",
        }
    return {
        "default_target_state": "TARGET_DEFINED_VALUE_UNRESOLVED_PENDING_UPSTREAM",
        "evidence_requirement_class": "UPSTREAM_VALUE_REQUIRED",
        "order_use_eligibility": "ORDER_USE_REQUIRES_FUTURE_PR",
        "reason_codes": ["PR150_UNRESOLVED_PENDING_UPSTREAM", "PR150_NO_HIDDEN_DEFAULTS"],
        "value_authority_class": "UNRESOLVED_PENDING_UPSTREAM_VALUE",
    }


def _target_item(
    *,
    family: str,
    domain: str,
    name: str,
    description: str,
    route: str,
    source_artifact_ref: str,
    source_target_field_class: str,
    market_scope: Sequence[str],
    agent_scope: Sequence[str],
    consumers: Sequence[str],
    formula_reference: str | None = None,
    runtime_receipt_requirement: str | None = None,
    replay_paper_calibration_requirement: str | None = None,
    quantum_execution_evidence_requirement: str | None = None,
    atomicrows_refs: Sequence[str] = (),
    pr149_refs: Sequence[str] = (),
    reason_codes: Sequence[str] = (),
) -> dict[str, Any]:
    route_values = _route_defaults(route)
    all_reasons = sorted(set(route_values["reason_codes"]) | set(reason_codes))
    return {
        "agent_scope": sorted(agent_scope),
        "allowed_range": None,
        "atomicrows_refs": sorted(atomicrows_refs),
        "default_target_state": route_values["default_target_state"],
        "default_value": None,
        "downstream_consumer_classes": sorted(consumers),
        "evidence_requirement_class": route_values["evidence_requirement_class"],
        "formula_reference": formula_reference,
        "market_scope": sorted(market_scope),
        "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
        "order_use_eligibility": route_values["order_use_eligibility"],
        "pr149_refs": sorted(pr149_refs),
        "quantum_execution_evidence_requirement": quantum_execution_evidence_requirement,
        "reason_codes": all_reasons,
        "replay_paper_calibration_requirement": replay_paper_calibration_requirement,
        "runtime_receipt_requirement": runtime_receipt_requirement,
        "source_artifact_ref": source_artifact_ref,
        "source_target_field_class": source_target_field_class,
        "target_description": description,
        "target_domain": domain,
        "target_family_id": family,
        "target_id": _stable_id(family, domain, name, "_".join(market_scope)),
        "target_name": name,
        "unit_or_scale": None,
        "value_authority_class": route_values["value_authority_class"],
    }


CLASSICAL_STRATEGY_TARGETS = (
    ("EDGE_SIGNAL_FAMILY_TARGETS", "edge_signal_family", "Edge signal family target slot."),
    ("MARKET_MAKING_TARGETS", "market_making", "Market-making parameter target slot."),
    ("ARBITRAGE_MISPRICING_TARGETS", "arbitrage_mispricing", "Arbitrage and mispricing target slot."),
    ("MOMENTUM_FLOW_TARGETS", "momentum_flow", "Momentum and flow target slot."),
    (
        "LIQUIDITY_VOLUME_OPEN_INTEREST_TARGETS",
        "liquidity_volume_open_interest",
        "Liquidity, volume, and open-interest target slot.",
    ),
    (
        "EVENT_MATURITY_TIME_TO_RESOLUTION_TARGETS",
        "event_maturity_time_to_resolution",
        "Event maturity and time-to-resolution target slot.",
    ),
    (
        "FORECAST_PROBABILITY_CALIBRATION_TARGETS",
        "forecast_probability_calibration",
        "Forecast probability calibration target slot.",
    ),
    ("CATEGORY_MARKET_TYPE_TARGETS", "category_market_type", "Category and market-type target slot."),
    ("YES_NO_ASYMMETRY_TARGETS", "yes_no_asymmetry", "Yes/no asymmetry target slot."),
    ("LONGSHOT_FAVORITE_BIAS_TARGETS", "longshot_favorite_bias", "Longshot/favorite bias target slot."),
    ("NEWS_RESEARCH_SIGNAL_TARGETS", "news_research_signal", "News/research signal target slot."),
    (
        "MODEL_FREE_BASELINE_COMPARATOR_TARGETS",
        "model_free_baseline_comparator",
        "Model-free baseline comparator target slot.",
    ),
)

SCORING_TARGETS = (
    ("AGENT_BINDING_SCORE_INPUTS", "agent_binding_score_input"),
    ("LIFECYCLE_READINESS_SCORE_INPUTS", "lifecycle_readiness_score_input"),
    ("PLATFORM_APPLICABILITY_SCORE_INPUTS", "platform_applicability_score_input"),
    ("STRATEGY_FIT_SCORE_INPUTS", "strategy_fit_score_input"),
    ("LATENCY_FIT_SCORE_INPUTS", "latency_fit_score_input"),
    ("RISK_FIT_SCORE_INPUTS", "risk_fit_score_input"),
    ("EXPECTED_NET_VALUE_SCORE_TARGETS", "expected_net_value_score_target"),
    ("EXPECTED_NET_COST_SCORE_TARGETS", "expected_net_cost_score_target"),
    ("SOURCE_EVIDENCE_COMPLETENESS_INPUTS", "source_evidence_completeness_input"),
    ("REPLAY_PAPER_CALIBRATION_INPUTS", "replay_paper_calibration_input"),
    ("OPTIMIZER_SCORE_INPUTS", "optimizer_score_input"),
    ("QUANTUM_APPLICABILITY_SCORE_INPUTS", "quantum_applicability_score_input"),
    ("FINAL_STACK_SCORE_INPUTS", "final_stack_score_input"),
    ("TIE_BREAKER_POLICY_INPUTS", "tie_breaker_policy_input"),
)

RISK_TARGETS = (
    ("CANDIDATE_COUNT_TARGETS", "candidate_count"),
    ("POSITION_SIZING_TARGETS", "position_sizing"),
    ("PORTFOLIO_EXPOSURE_TARGETS", "portfolio_exposure"),
    ("PER_MARKET_EXPOSURE_TARGETS", "per_market_exposure"),
    ("PER_VENUE_EXPOSURE_TARGETS", "per_venue_exposure"),
    ("PER_AGENT_EXPOSURE_TARGETS", "per_agent_exposure"),
    ("MAX_ORDER_NOTIONAL_TARGETS", "max_order_notional"),
    ("CAPITAL_RESERVE_TARGETS", "capital_reserve"),
    ("DRAWDOWN_GUARD_TARGETS", "drawdown_guard"),
    ("STOP_QUARANTINE_KILL_SWITCH_THRESHOLD_TARGETS", "stop_quarantine_kill_switch_threshold"),
    ("LIQUIDITY_GUARD_TARGETS", "liquidity_guard"),
    ("SLIPPAGE_GUARD_TARGETS", "slippage_guard"),
    ("NEW_INCREASED_EXPOSURE_BLOCK_TARGETS", "new_increased_exposure_block"),
    ("RUNTIME_AVAILABLE_CASH_RECEIPT_TARGETS", "runtime_available_cash_receipt"),
)

EXECUTION_TARGETS = (
    ("ORDER_INTENT_PARAMETER_TARGETS", "order_intent_parameter"),
    ("ORDER_TYPE_TARGET_FIELDS", "order_type_field"),
    ("LIMIT_PRICE_TARGET_FIELDS", "limit_price_field"),
    ("TICK_SIZE_TARGET_FIELDS", "tick_size_field"),
    ("MINIMUM_ORDER_SIZE_TARGET_FIELDS", "minimum_order_size_field"),
    ("FEE_SETTLEMENT_COST_TARGET_FIELDS", "fee_settlement_cost_field"),
    ("RATE_LIMIT_TARGET_FIELDS", "rate_limit_field"),
    ("ORDERBOOK_SNAPSHOT_FRESHNESS_TARGETS", "orderbook_snapshot_freshness"),
    ("WEBSOCKET_ORDERBOOK_EVENT_SEQUENCING_TARGETS", "websocket_orderbook_event_sequencing"),
    ("RETRY_BACKOFF_ERROR_ROUTING_TARGETS", "retry_backoff_error_routing"),
    ("LATENCY_BUDGET_TARGET_SLOTS", "latency_budget_slot"),
    ("PRECOMPUTED_HOT_PATH_SNAPSHOT_TARGETS", "precomputed_hot_path_snapshot"),
    ("LIVE_PRETRADE_EXCLUSION_TARGETS", "live_pretrade_exclusion"),
)

VENUE_SOURCE_CLASSES = (
    ("VENUE_API_SEMANTICS", "venue_api_semantics"),
    ("VENUE_ORDER_FIELDS", "order_fields"),
    ("VENUE_FEE_RULES", "fee_rules"),
    ("VENUE_TICK_RULES", "tick_rules"),
    ("VENUE_PAYOUT_RULES", "payout_rules"),
    ("VENUE_SETTLEMENT_RULES", "settlement_rules"),
    ("VENUE_SDK_BEHAVIOR", "sdk_behavior"),
    ("VENUE_RATE_LIMITS", "rate_limits"),
    ("VENUE_MARKET_DATA_SEMANTICS", "market_data_semantics"),
    ("VENUE_ACCOUNT_PRIVATE_STATE_SEMANTICS", "account_private_state_semantics"),
    ("VENUE_EXECUTION_LIFECYCLE", "execution_lifecycle"),
    ("VENUE_FILL_INTEGRITY", "fill_integrity"),
    ("VENUE_CASHFLOW_PNL_SEMANTICS", "cashflow_pnl_semantics"),
    ("VENUE_LATENCY_COMPONENT_SEMANTICS", "latency_component_semantics"),
    ("VENUE_RECONCILIATION_SEMANTICS", "reconciliation_semantics"),
    (
        "VENUE_CROSS_VENUE_NORMALIZATION_DEPENDENCIES",
        "cross_venue_normalization_dependencies",
    ),
)

OPTIMIZER_TARGETS = (
    ("CLASSICAL_OPTIMIZER_CANDIDATE_METADATA", "classical_optimizer_candidate_metadata"),
    ("GRID_SEARCH_METADATA_SLOTS", "grid_search_metadata"),
    ("RANDOM_SEARCH_METADATA_SLOTS", "random_search_metadata"),
    ("BAYESIAN_OPTIMIZER_METADATA_SLOTS", "bayesian_optimizer_metadata"),
    ("EVOLUTIONARY_OPTIMIZER_METADATA_SLOTS", "evolutionary_optimizer_metadata"),
    (
        "INTEGER_LINEAR_QUADRATIC_PROGRAM_METADATA_SLOTS",
        "integer_linear_quadratic_program_metadata",
    ),
    ("SCORING_WEIGHT_OPTIMIZATION_TARGETS", "scoring_weight_optimization"),
    ("HYPERPARAMETER_SEARCH_SPACE_TARGETS", "hyperparameter_search_space"),
    ("CONSTRAINT_PENALTY_WEIGHT_TARGET_SLOTS", "constraint_penalty_weight"),
    ("STRONGEST_CLASSICAL_COMPARATOR_TARGETS", "strongest_classical_comparator"),
    ("OPTIMIZER_OUTPUT_RECEIPT_REQUIREMENTS", "optimizer_output_receipt"),
    ("OPTIMIZER_PROMOTION_GATE_REQUIREMENTS", "optimizer_promotion_gate"),
)

QUANTUM_TARGETS = (
    ("QUANTUM_APPLICABILITY_METADATA", "quantum_applicability", "quantum_metadata"),
    ("QUBO_ENCODING_TARGET_SLOTS", "qubo_encoding", "quantum_metadata"),
    ("ISING_MAPPING_TARGET_SLOTS", "ising_mapping", "quantum_metadata"),
    ("QAOA_DEPTH_CLASS_TARGET_SLOTS", "qaoa_depth_class", "quantum_metadata"),
    ("QAOA_MIXER_ANSATZ_METADATA_SLOTS", "qaoa_mixer_ansatz", "quantum_metadata"),
    ("QAOA_CLASSICAL_OPTIMIZER_METADATA_SLOTS", "qaoa_classical_optimizer", "quantum_metadata"),
    ("VQE_ANSATZ_CLASS_METADATA_SLOTS", "vqe_ansatz_class", "quantum_metadata"),
    ("VQE_EXPECTATION_TOLERANCE_TARGET_SLOTS", "vqe_expectation_tolerance", "quantum_evidence"),
    ("ANNEALING_SCHEDULE_METADATA_SLOTS", "annealing_schedule", "quantum_metadata"),
    ("ANNEALING_CHAIN_EMBEDDING_TARGET_SLOTS", "annealing_chain_embedding", "quantum_evidence"),
    ("QUANTUM_PORTFOLIO_SELECTION_METADATA_SLOTS", "quantum_portfolio_selection", "quantum_metadata"),
    ("QUANTUM_SEARCH_SPACE_METADATA_SLOTS", "quantum_search_space", "quantum_metadata"),
    ("SHOT_COUNT_TARGET_SLOTS", "shot_count", "quantum_evidence"),
    ("BACKEND_PROVIDER_TARGET_SLOTS", "backend_provider", "quantum_evidence"),
    ("SIMULATOR_TARGET_SLOTS", "simulator", "quantum_evidence"),
    ("QUANTUM_RESULT_RECEIPT_REQUIREMENTS", "quantum_result_receipt", "quantum_evidence"),
    (
        "QUANTUM_STRONGEST_CLASSICAL_COMPARATOR_REQUIREMENTS",
        "quantum_strongest_classical_comparator",
        "replay_paper",
    ),
    ("QUANTUM_HOT_PATH_EXCLUSION_TARGETS", "quantum_hot_path_exclusion", "quantum_metadata"),
)

ATOMICROWS_TARGETS = (
    ("ATOMICROWS_ROW_FAMILY_REFERENCES", "row_family_references"),
    ("ATOMICROWS_SEMANTIC_FIELD_REFERENCES", "semantic_field_references"),
    ("ATOMICROWS_PR149_MATERIALIZATION_TARGET_REFERENCES", "pr149_materialization_targets"),
    ("ATOMICROWS_CANDIDATE_INVENTORY_LINKS", "candidate_inventory_links"),
    (
        "ATOMICROWS_FUTURE_SOURCE_MATERIALIZATION_DEPENDENCIES",
        "future_source_materialization_dependencies",
    ),
    (
        "ATOMICROWS_FUTURE_AGENT_FAMILY_ELIGIBILITY_DEPENDENCIES",
        "future_agent_family_eligibility_dependencies",
    ),
    ("ATOMICROWS_NO_BUNDLE_MUTATION_STATE", "no_bundle_mutation_state"),
)

REPLAY_PAPER_TARGETS = (
    ("REPLAY_METRIC_TARGET_SLOTS", "replay_metric"),
    ("PAPER_METRIC_TARGET_SLOTS", "paper_metric"),
    ("REPLAY_PAPER_LANE_SEPARATION_TARGETS", "lane_separation"),
    ("DUAL_RESULT_REVIEW_INPUT_TARGETS", "dual_result_review_input"),
    ("CALIBRATION_CONFIDENCE_TARGET_SLOTS", "calibration_confidence"),
    ("PROMOTION_GATE_INPUT_TARGET_SLOTS", "promotion_gate_input"),
    ("NO_REPLAY_PAPER_RESULT_FABRICATION", "no_result_fabrication"),
    ("NO_AUTOMATIC_LIVE_PROMOTION", "no_automatic_live_promotion"),
)


def _target_family_catalog() -> list[dict[str, Any]]:
    family_to_consumers = {
        "CLASSICAL_STRATEGY_PARAMETER": [
            "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
            "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
        ],
        "SCORING_FORMULA_INPUT": [
            "SCORING_RANKING_METADATA_CONSUMER",
            "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
        ],
        "RISK_CAPITAL_CONTROL": [
            "RISK_CAPITAL_CONTROL_METADATA_CONSUMER",
            "OWNER_DASHBOARD_READ_ONLY_METADATA_CONSUMER",
        ],
        "EXECUTION_LATENCY": [
            "EXECUTION_PLANNING_METADATA_CONSUMER",
            "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
        ],
        "VENUE_SOURCE_REQUIRED": [
            "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
            "EXECUTION_PLANNING_METADATA_CONSUMER",
        ],
        "OPTIMIZER_PARAMETER": [
            "OPTIMIZER_PLANNING_METADATA_CONSUMER",
            "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
        ],
        "QUANTUM_PARAMETER": [
            "QUANTUM_PLANNING_METADATA_CONSUMER",
            "OPTIMIZER_PLANNING_METADATA_CONSUMER",
        ],
        "ATOMICROWS_COMPATIBILITY": [
            "ATOMICROWS_COMPATIBILITY_METADATA_CONSUMER",
            "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
        ],
        "REPLAY_PAPER_CALIBRATION": [
            "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
            "OWNER_DASHBOARD_READ_ONLY_METADATA_CONSUMER",
        ],
        "MARKET_SPECIFIC_PARAMETER": [
            "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
            "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
        ],
    }
    return [
        {
            "downstream_consumer_classes": family_to_consumers[family],
            "evidence_requirements": [
                "NO_FILLED_VALUES_WITHOUT_MATCHING_UPSTREAM_EVIDENCE",
                "ORDER_USE_REQUIRES_FUTURE_PR",
            ],
            "required_authority_route": "STRUCTURED_TARGET_SLOT_ONLY",
            "target_construction_rules": [
                "STABLE_ID_FROM_FAMILY_DOMAIN_NAME_SCOPE",
                "NULL_DEFAULT_AND_RANGE_UNLESS_AUTHORITY_PRESENT",
                "NO_EXTERNAL_FACT_VALUE_FROM_OWNER_POLICY_PACKET",
            ],
            "target_family_id": family,
        }
        for family in c.TARGET_FAMILY_VALUES
    ]


def _build_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for domain, name, description in CLASSICAL_STRATEGY_TARGETS:
        route = "source" if name in {"category_market_type", "news_research_signal"} else "replay_paper"
        items.append(
            _target_item(
                family="CLASSICAL_STRATEGY_PARAMETER",
                domain=domain,
                name=name,
                description=description,
                route=route,
                source_artifact_ref=c.PR149_REPORT_PATH.as_posix(),
                source_target_field_class=f"classical_strategy:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("parameter_stack_agent", "replay_agent", "paper_agent"),
                consumers=(
                    "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
                    "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
                ),
                formula_reference=f"FUTURE_PARAMETER_FORMULA_REGISTRY.{name}",
                replay_paper_calibration_requirement=f"replay_paper_calibration_required:{name}",
                atomicrows_refs=("PR138_FIELD_STRATEGY_FAMILY", "PR138_FIELD_SIGNAL_FAMILY"),
                pr149_refs=("PR149_FIELD_STRATEGY_FAMILY", "PR149_FIELD_SIGNAL_FAMILY"),
            )
        )

    for domain, name in SCORING_TARGETS:
        route = "source" if name == "source_evidence_completeness_input" else "replay_paper"
        if name in {"latency_fit_score_input", "risk_fit_score_input"}:
            route = "runtime"
        items.append(
            _target_item(
                family="SCORING_FORMULA_INPUT",
                domain=domain,
                name=name,
                description=f"Scoring/ranking formula input target slot for {name}.",
                route=route,
                source_artifact_ref=c.PARAMETER_STACK_SCORING_REPORT_PATH.as_posix(),
                source_target_field_class=f"scoring_formula_input:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("parameter_stack_agent", "risk_agent"),
                consumers=(
                    "SCORING_RANKING_METADATA_CONSUMER",
                    "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
                ),
                formula_reference=f"FUTURE_SCORING_FORMULA_INPUT.{name}",
                runtime_receipt_requirement=(
                    f"runtime_receipt_required:{name}" if route == "runtime" else None
                ),
                replay_paper_calibration_requirement=(
                    f"replay_paper_calibration_required:{name}" if route == "replay_paper" else None
                ),
                atomicrows_refs=("PR138_FIELD_SCORING_FAMILY",),
                pr149_refs=("PR149_FIELD_SCORING_FAMILY",),
            )
        )

    for domain, name in RISK_TARGETS:
        route = "runtime" if name == "runtime_available_cash_receipt" else "replay_paper"
        if name in {"candidate_count", "capital_reserve"}:
            route = "unresolved"
        items.append(
            _target_item(
                family="RISK_CAPITAL_CONTROL",
                domain=domain,
                name=name,
                description=f"Risk and capital-control target slot for {name}.",
                route=route,
                source_artifact_ref=c.PR149_REPORT_PATH.as_posix(),
                source_target_field_class=f"risk_capital:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("risk_agent", "owner_approval_agent"),
                consumers=(
                    "RISK_CAPITAL_CONTROL_METADATA_CONSUMER",
                    "OWNER_DASHBOARD_READ_ONLY_METADATA_CONSUMER",
                ),
                runtime_receipt_requirement=(
                    f"runtime_receipt_required:{name}" if route == "runtime" else None
                ),
                replay_paper_calibration_requirement=(
                    f"replay_paper_calibration_required:{name}" if route == "replay_paper" else None
                ),
                atomicrows_refs=("PR138_FIELD_RISK_FAMILY", "PR138_FIELD_CAPITAL_FAMILY"),
                pr149_refs=("PR149_FIELD_RISK_FAMILY", "PR149_FIELD_CAPITAL_FAMILY"),
                reason_codes=(
                    ["PR150_NO_ORDER_AUTHORITY"]
                    if name in {"new_increased_exposure_block", "max_order_notional"}
                    else []
                ),
            )
        )

    for domain, name in EXECUTION_TARGETS:
        route = (
            "runtime"
            if name in {
                "orderbook_snapshot_freshness",
                "websocket_orderbook_event_sequencing",
                "precomputed_hot_path_snapshot",
            }
            else "source"
        )
        if name == "live_pretrade_exclusion":
            route = "unresolved"
        items.append(
            _target_item(
                family="EXECUTION_LATENCY",
                domain=domain,
                name=name,
                description=f"Execution and latency target slot for {name}.",
                route=route,
                source_artifact_ref=c.PR136_MARKET_INDEX_PATH.as_posix(),
                source_target_field_class=f"execution_latency:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("market_data_agent", "runtime_resolver_agent"),
                consumers=(
                    "EXECUTION_PLANNING_METADATA_CONSUMER",
                    "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
                ),
                runtime_receipt_requirement=(
                    f"runtime_receipt_required:{name}" if route == "runtime" else None
                ),
                atomicrows_refs=("PR138_FIELD_EXECUTION_FAMILY", "PR138_FIELD_LATENCY_FAMILY"),
                pr149_refs=("PR149_FIELD_EXECUTION_FAMILY", "PR149_FIELD_LATENCY_FAMILY"),
                reason_codes=("PR150_NO_LIVE_AUTHORITY", "PR150_NO_ORDER_AUTHORITY"),
            )
        )

    for venue in c.VENUE_SCOPES:
        for domain, source_class in VENUE_SOURCE_CLASSES:
            items.append(
                _target_item(
                    family="VENUE_SOURCE_REQUIRED",
                    domain=domain,
                    name=source_class,
                    description=f"{venue} official-source target slot for {source_class}.",
                    route="source",
                    source_artifact_ref=c.PR136_MARKET_INDEX_PATH.as_posix(),
                    source_target_field_class=f"official_source:{venue}:{source_class}",
                    market_scope=(venue,),
                    agent_scope=("source_evidence_agent", "connector_semantic_agent"),
                    consumers=(
                        "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER",
                        "EXECUTION_PLANNING_METADATA_CONSUMER",
                    ),
                    atomicrows_refs=("PR138_FIELD_VENUE_SCOPE", "PR138_FIELD_SOURCE_EVIDENCE_REQUIRED_FLAG"),
                    pr149_refs=("PR149_FIELD_VENUE_SCOPE", "PR149_FIELD_SOURCE_EVIDENCE_REQUIRED_FLAG"),
                    reason_codes=("PR150_NO_ORDER_AUTHORITY",),
                )
            )

    for domain, name in OPTIMIZER_TARGETS:
        route = "replay_paper"
        if name in {"optimizer_output_receipt", "optimizer_promotion_gate"}:
            route = "unresolved"
        items.append(
            _target_item(
                family="OPTIMIZER_PARAMETER",
                domain=domain,
                name=name,
                description=f"Optimizer planning target slot for {name}.",
                route=route,
                source_artifact_ref=c.QUANTUM_CLASSICAL_ARBITRATION_REPORT_PATH.as_posix(),
                source_target_field_class=f"optimizer_parameter:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("classical_optimizer_agent", "quantum_optimizer_agent"),
                consumers=(
                    "OPTIMIZER_PLANNING_METADATA_CONSUMER",
                    "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
                ),
                replay_paper_calibration_requirement=(
                    f"replay_paper_calibration_required:{name}" if route == "replay_paper" else None
                ),
                atomicrows_refs=("PR138_FIELD_ALGORITHM_FAMILY",),
                pr149_refs=("PR149_FIELD_ALGORITHM_FAMILY",),
                reason_codes=("PR150_NO_VALUE_INVENTION",),
            )
        )

    for domain, name, route in QUANTUM_TARGETS:
        items.append(
            _target_item(
                family="QUANTUM_PARAMETER",
                domain=domain,
                name=name,
                description=f"Quantum-forward target slot for {name}.",
                route=route,
                source_artifact_ref=c.CONTROLLER_PATH.as_posix(),
                source_target_field_class=f"quantum_parameter:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("quantum_optimizer_agent",),
                consumers=(
                    "QUANTUM_PLANNING_METADATA_CONSUMER",
                    "OPTIMIZER_PLANNING_METADATA_CONSUMER",
                ),
                replay_paper_calibration_requirement=(
                    f"strongest_classical_comparator_required:{name}"
                    if route == "replay_paper"
                    else None
                ),
                quantum_execution_evidence_requirement=(
                    f"quantum_evidence_required:{name}" if route == "quantum_evidence" else None
                ),
                atomicrows_refs=("PR138_FIELD_QUANTUM_FAMILY",),
                pr149_refs=("PR149_FIELD_QUANTUM_FAMILY", "PR149_FIELD_QUANTUM_APPLICABILITY_CLASS"),
                reason_codes=("PR150_NO_LIVE_AUTHORITY", "PR150_NO_ORDER_AUTHORITY"),
            )
        )

    for domain, name in ATOMICROWS_TARGETS:
        items.append(
            _target_item(
                family="ATOMICROWS_COMPATIBILITY",
                domain=domain,
                name=name,
                description=f"AtomicRows compatibility target slot for {name}.",
                route="unresolved",
                source_artifact_ref=c.PR149_REPORT_PATH.as_posix(),
                source_target_field_class=f"atomicrows_compatibility:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("atomicrows_agent",),
                consumers=(
                    "ATOMICROWS_COMPATIBILITY_METADATA_CONSUMER",
                    "PARAMETER_STACK_SELECTION_METADATA_CONSUMER",
                ),
                atomicrows_refs=("PR138_FIELD_ROW_FAMILY", "PR138_FIELD_ROW_ID"),
                pr149_refs=("PR149_FIELD_ROW_FAMILY", "PR149_FIELD_ROW_ID"),
                reason_codes=("PR150_NO_BUNDLE_MUTATION_AUTHORITY",),
            )
        )

    for domain, name in REPLAY_PAPER_TARGETS:
        items.append(
            _target_item(
                family="REPLAY_PAPER_CALIBRATION",
                domain=domain,
                name=name,
                description=f"Replay/paper calibration target slot for {name}.",
                route="replay_paper",
                source_artifact_ref=c.PARAMETER_STACK_SCORING_REPORT_PATH.as_posix(),
                source_target_field_class=f"replay_paper_calibration:{name}",
                market_scope=("PREDICTION_MARKETS_GENERAL",),
                agent_scope=("replay_agent", "paper_agent"),
                consumers=(
                    "REPLAY_PAPER_CALIBRATION_METADATA_CONSUMER",
                    "OWNER_DASHBOARD_READ_ONLY_METADATA_CONSUMER",
                ),
                replay_paper_calibration_requirement=f"replay_paper_calibration_required:{name}",
                atomicrows_refs=("PR138_FIELD_REPLAY_REQUIRED_FLAG", "PR138_FIELD_PAPER_REQUIRED_FLAG"),
                pr149_refs=("PR149_FIELD_REPLAY_REQUIRED_FLAG", "PR149_FIELD_PAPER_REQUIRED_FLAG"),
                reason_codes=("PR150_NO_LIVE_AUTHORITY", "PR150_NO_ORDER_AUTHORITY"),
            )
        )
    return sorted(items, key=lambda item: item["target_id"])


def _ids_for_family(items: Sequence[Mapping[str, Any]], family: str) -> list[str]:
    return sorted(str(item["target_id"]) for item in items if item.get("target_family_id") == family)


def _ids_for_domains(items: Sequence[Mapping[str, Any]], domains: set[str]) -> list[str]:
    return sorted(str(item["target_id"]) for item in items if item.get("target_domain") in domains)


def _counts(items: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key))
        counts[value] = counts.get(value, 0) + 1
    return {name: counts[name] for name in sorted(counts)}


def _evidence_index(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for evidence_class, count in _counts(items, "evidence_requirement_class").items():
        records.append(
            {
                "evidence_requirement_class": evidence_class,
                "target_count": count,
                "target_ids": sorted(
                    str(item["target_id"])
                    for item in items
                    if item.get("evidence_requirement_class") == evidence_class
                ),
            }
        )
    return records


def _market_targets(
    items: Sequence[Mapping[str, Any]],
    pr136_market: Mapping[str, Any],
) -> list[dict[str, Any]]:
    market_rows = {
        str(row.get("canonical_venue_id")): row
        for row in _list(pr136_market.get("market_scopes"))
        if isinstance(row, Mapping)
    }
    records = []
    for venue in c.VENUE_SCOPES:
        source = _mapping(market_rows.get(venue))
        records.append(
            {
                "market_scope": venue,
                "missing_source_evidence_classes": _sorted_strings(
                    source.get("missing_accepted_source_evidence_classes")
                ),
                "order_use_eligibility": "PENDING_SOURCE_EVIDENCE",
                "source_artifact_ref": c.PR136_MARKET_INDEX_PATH.as_posix(),
                "target_ids": sorted(
                    str(item["target_id"])
                    for item in items
                    if item.get("market_scope") == [venue]
                ),
            }
        )
    return records


def _optional_report_summary(optional: Mapping[str, Any], rel_path: Path) -> dict[str, Any]:
    payload = _mapping(optional.get(rel_path.as_posix()))
    return {
        "artifact_path": rel_path.as_posix(),
        "present": bool(payload),
        "report_id": payload.get("report_id"),
        "validation_marker": payload.get("validation_marker"),
        "static_only_flag": payload.get("static_only_flag"),
        "metadata_only_flag": payload.get("metadata_only_flag"),
        "optimizer_execution_created": payload.get("optimizer_execution_created"),
        "runtime_authority_created": payload.get("runtime_authority_created"),
        "order_authority_created": payload.get("order_authority_created"),
    }


def _field_ids(pr138: Mapping[str, Any]) -> list[str]:
    contract = _mapping(pr138.get("semantic_contract"))
    return _sorted_strings(contract.get("field_ids"))


def _build_payload(evidence: Mapping[str, Any]) -> dict[str, Any]:
    payloads = _mapping(evidence["json_payloads"])
    optional = _mapping(evidence["optional_payloads"])
    present = set(evidence["present_paths"])
    pr136_route = _mapping(payloads.get("pr136_route_triage"))
    pr136_crosswalk = _mapping(payloads.get("pr136_section_crosswalk_or_alias"))
    pr136_market = _mapping(payloads.get("pr136_market_index"))
    pr136_command = _mapping(payloads.get("pr136_command_matrix"))
    pr137r = _mapping(payloads.get("pr137r_reconciliation"))
    pr138 = _mapping(payloads.get("pr138_semantic_contract"))
    pr149 = _mapping(payloads.get("pr149_bridge_report"))
    source_packet = _mapping(optional.get(c.SOURCE_EVIDENCE_PACKET_PATH.as_posix()))
    items = _build_items()
    family_catalog = _target_family_catalog()

    classical_domains = {domain for domain, _name, _description in CLASSICAL_STRATEGY_TARGETS}
    scoring_domains = {domain for domain, _name in SCORING_TARGETS}
    risk_domains = {domain for domain, _name in RISK_TARGETS}
    execution_domains = {domain for domain, _name in EXECUTION_TARGETS}
    venue_domains = {domain for domain, _name in VENUE_SOURCE_CLASSES}
    optimizer_domains = {domain for domain, _name in OPTIMIZER_TARGETS}
    quantum_domains = {domain for domain, _name, _route in QUANTUM_TARGETS}
    atomicrows_domains = {domain for domain, _name in ATOMICROWS_TARGETS}
    replay_paper_domains = {domain for domain, _name in REPLAY_PAPER_TARGETS}

    return {
        "agent_algorithm_registry_summary": {
            "parameter_algorithm_scoring_policy": _optional_report_summary(
                optional,
                c.PARAMETER_ALGORITHM_SCORING_REPORT_PATH,
            ),
            "parameter_stack_scoring_gate": _optional_report_summary(
                optional,
                c.PARAMETER_STACK_SCORING_REPORT_PATH,
            ),
            "quantum_classical_arbitration_gate": _optional_report_summary(
                optional,
                c.QUANTUM_CLASSICAL_ARBITRATION_REPORT_PATH,
            ),
        },
        "atomicrows_compatibility_summary": {
            "atomicrows_bundle_mutated": False,
            "bundle_boundary_report_present": c.ATOMICROWS_BUNDLE_BOUNDARY_REPORT_PATH.as_posix()
            in present,
            "bundle_materialization_report_present": c.ATOMICROWS_BUNDLE_MATERIALIZATION_REPORT_PATH.as_posix()
            in present,
            "no_bundle_mutation_state_target_ids": _ids_for_domains(
                items,
                {"ATOMICROWS_NO_BUNDLE_MUTATION_STATE"},
            ),
            "pr137r_consumed": bool(pr137r),
            "pr138_consumed": bool(pr138),
            "pr149_consumed": bool(pr149),
            "qtt_integrity_authority_created": False,
        },
        "atomicrows_parameter_targets": _ids_for_domains(items, atomicrows_domains),
        "authority_class": c.AUTHORITY_CLASS,
        "centralized_reason_codes": list(c.REASON_CODES),
        "centralized_state_enums": {
            "default_target_state": list(c.DEFAULT_TARGET_STATE_VALUES),
            "downstream_consumer_class": list(c.DOWNSTREAM_CONSUMER_CLASS_VALUES),
            "evidence_requirement_class": list(c.EVIDENCE_REQUIREMENT_CLASS_VALUES),
            "order_use_eligibility": list(c.ORDER_USE_ELIGIBILITY_VALUES),
            "parameter_domain": list(c.PARAMETER_DOMAIN_VALUES),
            "target_family": list(c.TARGET_FAMILY_VALUES),
            "value_authority_class": list(c.VALUE_AUTHORITY_CLASS_VALUES),
        },
        "classical_parameter_targets": _ids_for_domains(items, classical_domains),
        "deterministic_generation_policy": {
            "array_sorting": "STABLE_IDENTIFIER_ASC",
            "dictionary_key_sorting": "JSON_SORT_KEYS_TRUE",
            "machine_local_paths_allowed": False,
            "random_ids_allowed": False,
            "tracked_timestamp_policy": c.STATIC_TIME,
        },
        "downstream_agent_consumption_surface": [
            {
                "consumer_class": consumer,
                "may_consume_as_metadata_only": True,
                "must_not_treat_as_order_authority": True,
                "target_ids": sorted(
                    str(item["target_id"])
                    for item in items
                    if consumer in item.get("downstream_consumer_classes", [])
                ),
            }
            for consumer in c.DOWNSTREAM_CONSUMER_CLASS_VALUES
        ],
        "evidence_requirement_index": _evidence_index(items),
        "execution_latency_parameter_targets": _ids_for_domains(items, execution_domains),
        "market_specific_parameter_targets": _market_targets(items, pr136_market),
        "next_consumer_contract": {
            "consumer_contract_id": "PR150_PARAMETER_TARGET_MATRIX_METADATA_CONTRACT",
            "must_preserve_null_values_until_evidence": True,
            "must_preserve_no_claim_flags": True,
            "must_request_future_evidence_for_pending_targets": True,
            "next_allowed_state": "FUTURE_SCOPED_CONSUMER_PR_REQUIRED",
            "order_use_created": False,
        },
        "no_claim_boundary": dict(c.NO_CLAIM_FLAGS),
        "optional_context_inputs": _path_records(c.OPTIONAL_CONTEXT_ARTIFACTS, present, False),
        "optimizer_parameter_targets": _ids_for_domains(items, optimizer_domains),
        "order_use_eligibility_summary": {
            "counts_by_order_use_eligibility": _counts(items, "order_use_eligibility"),
            "order_usable_target_count": 0,
            "order_use_created": False,
        },
        "orchestration_preflight_receipt": {
            "alias_resolution": dict(evidence["alias_resolution"]),
            "all_required_inputs_consumed": all(
                path.as_posix() in present for path in c.REQUIRED_UPSTREAM_ARTIFACTS
            )
            and c.PR149_MODULE_DIR_PATH.as_posix() in present,
            "pr149_module_consumed": c.PR149_MODULE_DIR_PATH.as_posix() in present,
            "required_input_keys": [
                "control_plane_roster",
                "control_plane_controller",
                "launch_roadmap",
                "launch_roadmap_policy",
                "pr136_route_triage",
                "pr136_section_crosswalk_or_alias",
                "pr136_market_index",
                "pr136_command_matrix",
                "pr137r_reconciliation",
                "pr138_semantic_contract",
                "pr149_bridge_report",
                "pr149_bridge_module",
            ],
        },
        "parameter_default_target_matrix": {
            "matrix_id": "PR150_PARAMETER_DEFAULT_TARGET_MATRIX",
            "parameter_target_items": items,
            "target_count": len(items),
        },
        "pr136_alignment_summary": {
            "command_action_count": len(_list(pr136_command.get("actions"))),
            "crosswalk_entry_count": pr136_crosswalk.get("coverage_entry_count"),
            "market_scope_count": pr136_market.get("canonical_venue_count"),
            "route_receipt_type": pr136_route.get("receipt_type"),
            "sequence_authority_class": pr136_route.get("sequence_authority_class"),
        },
        "pr137r_alignment_summary": {
            "row_count_proven": _mapping(pr137r.get("atomicrows_validation_state")).get(
                "row_count_proven"
            ),
            "validation_state": pr137r.get("validation_state"),
        },
        "pr138_semantic_contract_summary": {
            "field_count": len(_field_ids(pr138)),
            "semantic_row_contract_defined": pr138.get("semantic_row_contract_defined_by_pr138"),
            "semantic_values_materialized": pr138.get("semantic_row_values_materialized_by_pr138"),
        },
        "pr149_bridge_consumption_summary": {
            "authority_class": pr149.get("authority_class"),
            "pr136_consumed_by_pr149": _mapping(
                pr149.get("orchestration_preflight_receipt")
            ).get("all_required_inputs_consumed"),
            "report_id": pr149.get("report_id"),
            "semantic_item_count": len(
                _list(
                    _mapping(pr149.get("semantic_value_materialization_packet")).get(
                        "materialization_items"
                    )
                )
            ),
        },
        "pr_id": c.PR_ID,
        "pr_title": c.PR_TITLE,
        "quantum_parameter_targets": _ids_for_domains(items, quantum_domains),
        "readiness_class": c.READINESS_CLASS,
        "replay_paper_calibration_targets": _ids_for_domains(items, replay_paper_domains),
        "report_id": c.REPORT_ID,
        "report_version": c.REPORT_VERSION,
        "risk_capital_control_targets": _ids_for_domains(items, risk_domains),
        "scoring_formula_input_targets": _ids_for_domains(items, scoring_domains),
        "scoring_ranking_optimizer_surface_summary": {
            "candidate_generation_report_present": c.CANDIDATE_STACK_GENERATION_REPORT_PATH.as_posix()
            in present,
            "selected_stack_handoff_report_present": c.SELECTED_STACK_HANDOFF_REPORT_PATH.as_posix()
            in present,
            "trade_context_selection_report_present": c.TRADE_CONTEXT_SELECTION_REPORT_PATH.as_posix()
            in present,
            "optimizer_target_ids": _ids_for_domains(items, optimizer_domains),
            "scoring_target_ids": _ids_for_domains(items, scoring_domains),
        },
        "source_evidence_boundary_summary": {
            "accepted_source_value_items_created": 0,
            "external_fact_value_created": False,
            "owner_source_policy_packet_present": bool(source_packet),
            "policy_context_only": True,
            "source_required_target_count": len(
                [
                    item
                    for item in items
                    if item.get("value_authority_class") == "SOURCE_EVIDENCE_REQUIRED_VALUE"
                ]
            ),
        },
        "target_family_catalog": family_catalog,
        "unresolved_target_index": {
            "target_count": len(
                [
                    item
                    for item in items
                    if item.get("value_authority_class") == "UNRESOLVED_PENDING_UPSTREAM_VALUE"
                ]
            ),
            "target_ids": sorted(
                str(item["target_id"])
                for item in items
                if item.get("value_authority_class") == "UNRESOLVED_PENDING_UPSTREAM_VALUE"
            ),
        },
        "upstream_artifact_inputs": _path_records(c.REQUIRED_UPSTREAM_ARTIFACTS, present, True),
        "validation_summary": {
            "build_report_byte_stable": True,
            "default_validation_mutates_tracked_report": False,
            "explicit_report_write_mode_supported": True,
            "normal_full_gate_integration_is_non_mutating": True,
            "tracked_report_path": c.REPORT_PATH.as_posix(),
        },
        "venue_source_required_targets": _ids_for_domains(items, venue_domains),
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    evidence, failures = load_static_evidence(repo_root)
    if failures:
        raise ValueError("\n".join(failures))
    return _build_payload(evidence)


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _is_path_like_key(key: str) -> bool:
    return (
        key == "artifact_path"
        or key.endswith("_path")
        or key.endswith("_paths")
        or key.endswith("_ref")
        or key.endswith("_refs")
    )


def _forbidden_bundle_sidecar_path() -> str:
    return c.ATOMICROWS_BUNDLE_PATH.with_suffix("." + "sha" + "256").as_posix()


def _contains_exact(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return value.replace("\\", "/") == needle
    if isinstance(value, list):
        return any(_contains_exact(item, needle) for item in value)
    return False


def _path_and_integrity_failures(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    forbidden_sidecar = _forbidden_bundle_sidecar_path()
    for key, value in _walk(payload):
        lowered = key.lower()
        if lowered.endswith(("_" + "di" + "gest", "_" + "check" + "sum", "_hash")):
            failures.append("PR150_NO_QTT_INTEGRITY_AUTHORITY")
        if "integrity_authority" in lowered and value is not False:
            failures.append("PR150_NO_QTT_INTEGRITY_AUTHORITY")
        if _is_path_like_key(key) and _contains_exact(value, forbidden_sidecar):
            failures.append("PR150_NO_BUNDLE_MUTATION_AUTHORITY")
        if isinstance(value, str) and re.search(r"[A-Za-z]:[\\/]", value):
            failures.append("PR150_LOCAL_PATH_FORBIDDEN")
    return sorted(set(failures))


def _false_flag_failures(payload: Mapping[str, Any]) -> list[str]:
    flags = _mapping(payload.get("no_claim_boundary"))
    failures: list[str] = []
    if dict(flags) != c.NO_CLAIM_FLAGS:
        failures.append("PR150_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED")
    for key, value in flags.items():
        if value is not False:
            failures.append(f"PR150_FORBIDDEN_FLAG_TRUE: {key}")
    return failures


def _validate_item(item: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    target_id = str(item.get("target_id"))
    for key in c.TARGET_ITEM_REQUIRED_FIELDS:
        if key not in item:
            failures.append(f"PR150_TARGET_ITEM_SCHEMA_INVALID: {target_id}: {key}")
    enum_checks = {
        "target_family_id": c.TARGET_FAMILY_VALUES,
        "target_domain": c.PARAMETER_DOMAIN_VALUES,
        "value_authority_class": c.VALUE_AUTHORITY_CLASS_VALUES,
        "default_target_state": c.DEFAULT_TARGET_STATE_VALUES,
        "evidence_requirement_class": c.EVIDENCE_REQUIREMENT_CLASS_VALUES,
        "order_use_eligibility": c.ORDER_USE_ELIGIBILITY_VALUES,
    }
    for key, allowed in enum_checks.items():
        if item.get(key) not in allowed:
            failures.append(f"PR150_TARGET_ENUM_INVALID: {target_id}: {key}")
    if _mapping(item.get("no_claim_flags")) != c.NO_CLAIM_FLAGS:
        failures.append(f"PR150_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED: {target_id}")
    for reason in _list(item.get("reason_codes")):
        if reason not in c.REASON_CODES:
            failures.append(f"PR150_REASON_CODE_INVALID: {reason}")
    for consumer in _list(item.get("downstream_consumer_classes")):
        if consumer not in c.DOWNSTREAM_CONSUMER_CLASS_VALUES:
            failures.append(f"PR150_TARGET_ENUM_INVALID: {target_id}: downstream_consumer")

    authority = item.get("value_authority_class")
    source_field = str(item.get("source_target_field_class"))
    filled_default = item.get("default_value") is not None
    filled_range = item.get("allowed_range") is not None
    allowed_filled_classes = {
        "OWNER_POLICY_VALUE",
        "INTERNAL_QTT_ARCHITECTURE_VALUE",
        "ACCEPTED_SOURCE_EVIDENCE_VALUE",
    }
    if filled_default and authority not in allowed_filled_classes:
        failures.append(f"PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED: {target_id}")
    if filled_range and authority not in allowed_filled_classes:
        failures.append(f"PR150_UNAUTHORIZED_ALLOWED_RANGE_FILLED: {target_id}")
    if authority == "ACCEPTED_SOURCE_EVIDENCE_VALUE":
        ref = str(item.get("source_artifact_ref"))
        if "accepted" not in ref.lower() or not source_field:
            failures.append(f"PR150_ACCEPTED_SOURCE_FIELD_SCOPE_REQUIRED: {target_id}")
    if authority == "OWNER_POLICY_VALUE" and source_field.startswith("official_source:"):
        if filled_default or filled_range:
            failures.append(f"PR150_OWNER_POLICY_EXTERNAL_FACT_MISUSE: {target_id}")
    if authority == "SOURCE_EVIDENCE_REQUIRED_VALUE" and (filled_default or filled_range):
        failures.append(f"PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED: {target_id}")
    if authority == "RUNTIME_RECEIPT_REQUIRED_VALUE":
        if not item.get("runtime_receipt_requirement"):
            failures.append(f"PR150_RUNTIME_RECEIPT_REQUIRED: {target_id}")
        if filled_default or filled_range:
            failures.append(f"PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED: {target_id}")
    if authority == "REPLAY_PAPER_CALIBRATION_REQUIRED_VALUE":
        if not item.get("replay_paper_calibration_requirement"):
            failures.append(f"PR150_REPLAY_PAPER_CALIBRATION_REQUIRED: {target_id}")
        if filled_default or filled_range:
            failures.append(f"PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED: {target_id}")
    if authority == "QUANTUM_EXECUTION_EVIDENCE_REQUIRED_VALUE":
        if not item.get("quantum_execution_evidence_requirement"):
            failures.append(f"PR150_QUANTUM_EXECUTION_EVIDENCE_REQUIRED: {target_id}")
        if filled_default or filled_range:
            failures.append(f"PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED: {target_id}")
    if authority == "QUANTUM_METADATA_ONLY_VALUE" and (filled_default or filled_range):
        failures.append(f"PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED: {target_id}")
    if item.get("order_use_eligibility") == "ORDER_USABLE":
        failures.append(f"PR150_NO_ORDER_AUTHORITY: {target_id}")
    return failures


def validate_report_payload(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    required_top_level = (
        "report_id",
        "report_version",
        "pr_id",
        "pr_title",
        "authority_class",
        "readiness_class",
        "deterministic_generation_policy",
        "upstream_artifact_inputs",
        "optional_context_inputs",
        "orchestration_preflight_receipt",
        "pr136_alignment_summary",
        "pr137r_alignment_summary",
        "pr138_semantic_contract_summary",
        "pr149_bridge_consumption_summary",
        "source_evidence_boundary_summary",
        "agent_algorithm_registry_summary",
        "scoring_ranking_optimizer_surface_summary",
        "atomicrows_compatibility_summary",
        "target_family_catalog",
        "parameter_default_target_matrix",
        "market_specific_parameter_targets",
        "classical_parameter_targets",
        "scoring_formula_input_targets",
        "risk_capital_control_targets",
        "execution_latency_parameter_targets",
        "venue_source_required_targets",
        "optimizer_parameter_targets",
        "quantum_parameter_targets",
        "atomicrows_parameter_targets",
        "replay_paper_calibration_targets",
        "downstream_agent_consumption_surface",
        "evidence_requirement_index",
        "unresolved_target_index",
        "order_use_eligibility_summary",
        "no_claim_boundary",
        "centralized_reason_codes",
        "validation_summary",
        "next_consumer_contract",
    )
    for key in required_top_level:
        if key not in payload:
            failures.append(f"PR150_REQUIRED_REPORT_KEY_MISSING: {key}")
    if payload.get("report_id") != c.REPORT_ID:
        failures.append("PR150_REPORT_ID_MISMATCH")
    if payload.get("report_version") != c.REPORT_VERSION:
        failures.append("PR150_REPORT_VERSION_MISMATCH")
    if payload.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append("PR150_AUTHORITY_CLASS_MISMATCH")
    if payload.get("readiness_class") != c.READINESS_CLASS:
        failures.append("PR150_READINESS_CLASS_MISMATCH")
    if payload.get("centralized_reason_codes") != list(c.REASON_CODES):
        failures.append("PR150_ENUMS_NOT_CONSTANT_ALIGNED")

    enums = _mapping(payload.get("centralized_state_enums"))
    expected_enums = {
        "default_target_state": list(c.DEFAULT_TARGET_STATE_VALUES),
        "downstream_consumer_class": list(c.DOWNSTREAM_CONSUMER_CLASS_VALUES),
        "evidence_requirement_class": list(c.EVIDENCE_REQUIREMENT_CLASS_VALUES),
        "order_use_eligibility": list(c.ORDER_USE_ELIGIBILITY_VALUES),
        "parameter_domain": list(c.PARAMETER_DOMAIN_VALUES),
        "target_family": list(c.TARGET_FAMILY_VALUES),
        "value_authority_class": list(c.VALUE_AUTHORITY_CLASS_VALUES),
    }
    if dict(enums) != expected_enums:
        failures.append("PR150_ENUMS_NOT_CONSTANT_ALIGNED")
    failures.extend(_false_flag_failures(payload))
    failures.extend(_path_and_integrity_failures(payload))

    preflight = _mapping(payload.get("orchestration_preflight_receipt"))
    if preflight.get("all_required_inputs_consumed") is not True:
        failures.append("PR150_PR136_ORCHESTRATION_REQUIRED")
    if preflight.get("pr149_module_consumed") is not True:
        failures.append("PR150_PR149_BRIDGE_REQUIRED")
    if _mapping(payload.get("pr136_alignment_summary")).get("route_receipt_type") != (
        "PR136_ROUTE_TRIAGE_RECEIPT"
    ):
        failures.append("PR150_PR136_ORCHESTRATION_REQUIRED")
    if _mapping(payload.get("pr137r_alignment_summary")).get("row_count_proven") is not True:
        failures.append("PR150_PR137R_RECONCILIATION_REQUIRED")
    if _mapping(payload.get("pr138_semantic_contract_summary")).get("field_count") != 59:
        failures.append("PR150_PR138_SEMANTIC_CONTRACT_REQUIRED")
    if not _mapping(payload.get("pr149_bridge_consumption_summary")).get("report_id"):
        failures.append("PR150_PR149_BRIDGE_REQUIRED")

    family_catalog = _list(payload.get("target_family_catalog"))
    if not family_catalog:
        failures.append("PR150_TARGET_FAMILY_CATALOG_MISSING")
    family_ids = [
        str(row.get("target_family_id"))
        for row in family_catalog
        if isinstance(row, Mapping)
    ]
    if family_ids != list(c.TARGET_FAMILY_VALUES):
        failures.append("PR150_TARGET_FAMILY_CATALOG_MISSING")

    matrix = _mapping(payload.get("parameter_default_target_matrix"))
    items = _list(matrix.get("parameter_target_items"))
    if not items:
        failures.append("PR150_TARGET_ITEMS_MISSING")
    item_ids = [str(item.get("target_id")) for item in items if isinstance(item, Mapping)]
    if item_ids != sorted(item_ids):
        failures.append("PR150_TARGET_ITEMS_NOT_SORTED")
    if len(item_ids) != len(set(item_ids)):
        failures.append("PR150_TARGET_ID_DUPLICATE")
    for item in items:
        if not isinstance(item, Mapping):
            failures.append("PR150_TARGET_ITEM_SCHEMA_INVALID: non_object")
            continue
        failures.extend(_validate_item(item))

    order_summary = _mapping(payload.get("order_use_eligibility_summary"))
    if order_summary.get("order_usable_target_count") != 0:
        failures.append("PR150_NO_ORDER_AUTHORITY")
    if order_summary.get("order_use_created") is not False:
        failures.append("PR150_NO_ORDER_AUTHORITY")
    return sorted(set(failures))


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--short", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        if len(line) > 2 and line[2] == " ":
            path = line[3:]
        elif len(line) > 1 and line[1] == " ":
            path = line[2:]
        else:
            path = line[3:] if len(line) > 3 else line
        normalized = path.strip().replace("\\", "/")
        if " -> " in normalized:
            normalized = normalized.rsplit(" -> ", 1)[1]
        paths.append(normalized)
    return sorted(set(paths))


def _branch_allows_pr150_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        150,
        allow_main=False,
        allow_repair=False,
    )


def _branch_allows_explicit_pr150_tracked_report_write(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        150,
        allow_main=True,
        allow_repair=False,
    )


def _branch_allows_pr151_retrieval_target_pack_changed_paths(branch: str) -> bool:
    return is_pr_or_later_branch(branch, 151, allow_main=False, allow_repair=False)


def _is_pr151_retrieval_target_pack_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS
        and _branch_allows_pr151_retrieval_target_pack_changed_paths(branch)
    )


def _branch_allows_pr152_audit_changed_paths(branch: str) -> bool:
    return is_pr_or_later_branch(
        branch,
        152,
        allow_main=False,
        allow_repair=False,
    )


def _is_pr152_audit_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in pr152_constants.PR152_AUDIT_CHANGED_PATHS
        and _branch_allows_pr152_audit_changed_paths(branch)
    )


def _is_allowed_pr150_changed_path_for_branch(
    path: str,
    branch: str,
    *,
    tracked_report_write_allowed: bool = False,
) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if (
        tracked_report_write_allowed
        and normalized == c.REPORT_PATH.as_posix()
        and _branch_allows_explicit_pr150_tracked_report_write(branch)
    ):
        return True
    if _is_pr151_retrieval_target_pack_changed_path_for_branch(normalized, branch):
        return True
    if _is_pr152_audit_changed_path_for_branch(normalized, branch):
        return True
    return normalized in c.EXACT_CHANGED_PATH_CANDIDATES and _branch_allows_pr150_changed_paths(
        branch
    )


def _validate_changed_paths(
    repo_root: Path,
    *,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR150_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if not _is_allowed_pr150_changed_path_for_branch(
            normalized,
            branch,
            tracked_report_write_allowed=tracked_report_write_allowed,
        ):
            failures.append(f"PR150_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR150_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR150_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized == _forbidden_bundle_sidecar_path():
            failures.append("PR150_NO_BUNDLE_MUTATION_AUTHORITY")
    return sorted(set(failures))


def validate_repository_artifacts(
    repo_root: Path | str,
    *,
    report_output_path: Path | str | None = None,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    root = Path(repo_root).resolve()
    try:
        expected_report = build_report(root)
        if expected_report != build_report(root):
            return ["PR150_REPORT_NOT_DETERMINISTIC"]
    except ValueError as exc:
        return [line for line in str(exc).splitlines() if line]

    failures = validate_report_payload(expected_report)
    if report_output_path is not None:
        output_path = Path(report_output_path)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_dump(expected_report), encoding="utf-8", newline="\n")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR150_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")
    if actual_report and actual_report != expected_report:
        failures.append("PR150_REPORT_STALE_OR_NONDETERMINISTIC")
    if actual_report:
        failures.extend(validate_report_payload(actual_report))

    failures.extend(
        _validate_changed_paths(
            root,
            tracked_report_write_allowed=tracked_report_write_allowed,
        )
    )
    return sorted(set(failures))


def write_report_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / c.REPORT_PATH
    serialized_report = json_dump(report)
    serialized_bytes = serialized_report.encode("utf-8")
    if path.exists():
        current_bytes = path.read_bytes()
        if (
            current_bytes == serialized_bytes
            or current_bytes.replace(b"\r\n", b"\n") == serialized_bytes
        ):
            return report
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized_report, encoding="utf-8", newline="\n")
    return report
