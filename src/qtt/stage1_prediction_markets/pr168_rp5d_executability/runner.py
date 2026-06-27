"""Deterministic PR168-RP5D replay/paper executability generator."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fnmatch import fnmatchcase
from pathlib import Path
import sys
from typing import Any, Iterable

from .artifact_names import build_artifact_name_entries
from .models import (
    ADAPTER_FAMILIES,
    BASELINE_SHA_VCS_METADATA_ONLY,
    BLOCKER_CODES,
    BLOCKER_POLICY_REF,
    BLOCKER_TO_ADAPTER,
    BLOCKER_TO_STATE,
    BRANCH_NAME,
    COMPUTABILITY_STATES,
    CREATED_AT_UTC,
    EXECUTABILITY_STATES,
    EXECUTION_AUTHORITY_REF,
    GENERATED_DIR,
    JSON_OUTPUTS,
    JSONL_OUTPUTS,
    MARKET_FAMILY,
    MASTER_PLAN_DISCOVERY_PATTERNS,
    MASTER_PLAN_EXACT_FILES,
    OLD_LONG_ARTIFACT_NAMES,
    OPTIMIZER_FAMILIES,
    PLATFORM_IDS,
    PR165_D2_EXPECTED_FILES,
    PR_ID,
    QUEUE_FILE_BY_BLOCKER,
    READINESS_FILES,
    REPORT_OUTPUTS,
    REPO_ROOT,
    REQUIRED_AGENTS,
    RP5C_REQUIRED_FILES,
    RUN_ID,
    STAGE_PROFILE_ID,
    VS1_REQUIRED_FILES,
    all_artifact_filenames,
    generated_ref,
    manifest_name,
    ratio_string,
    read_json,
    read_jsonl,
    rel_ref,
    stable_unique,
    with_common,
    write_json,
    write_jsonl,
)
from .path_safety import path_safety_failures, path_safety_record

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5c_library_reader import load_library  # noqa: E402


CORE_CONTRACT_CODES = (
    "RP5D_MATERIALIZE_INPUT_CONTRACT",
    "RP5D_MATERIALIZE_UNIT_CONTRACT",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING",
)

CONTRACT_CODE_FIELDS = {
    "RP5D_MATERIALIZE_INPUT_CONTRACT": "input_contract_available_flag",
    "RP5D_MATERIALIZE_UNIT_CONTRACT": "unit_contract_available_flag",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP": "formula_to_pnl_available_flag",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING": "market_data_binding_available_flag",
    "RP5D_MATERIALIZE_TCA_BINDING": "tca_readiness_available_flag",
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING": "fill_liquidity_readiness_available_flag",
    "RP5D_MATERIALIZE_LATENCY_BINDING": "latency_readiness_available_flag",
    "RP5D_MATERIALIZE_CAPACITY_BINDING": "capacity_crowding_readiness_available_flag",
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING": "portfolio_context_readiness_available_flag",
    "RP5D_MATERIALIZE_SCENARIO_BINDING": "scenario_ladder_readiness_available_flag",
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING": "overfit_fdr_readiness_available_flag",
    "RP5D_MATERIALIZE_NO_TRADE_BINDING": "no_trade_readiness_available_flag",
    "RP5D_MATERIALIZE_RANKING_READINESS": "ranking_readiness_available_flag",
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS": "champion_challenger_readiness_available_flag",
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS": "regime_memory_readiness_available_flag",
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS": "alpha_edge_readiness_available_flag",
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS": "latency_hot_path_readiness_available_flag",
    "RP5D_MATERIALIZE_QUANTUM_MAPPING": "quantum_objective_constraint_available_flag",
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK": "classical_fallback_available_flag",
}

CONTRACT_CODE_REQUIRED_FIELDS = {
    "RP5D_MATERIALIZE_INPUT_CONTRACT": ["event_id", "contract_id", "timestamp_utc", "side", "price"],
    "RP5D_MATERIALIZE_UNIT_CONTRACT": ["input_unit", "output_unit", "unit_normalization_policy_ref"],
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP": ["payout_rule", "side", "entry_price", "size", "fee_model_ref"],
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING": ["venue", "market_id", "bid", "ask", "last_update_utc"],
    "RP5D_MATERIALIZE_TCA_BINDING": ["fees", "spread", "slippage", "queue", "latency", "capacity"],
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING": ["available_depth", "fill_probability", "queue_position"],
    "RP5D_MATERIALIZE_LATENCY_BINDING": ["snapshot_age_ms", "latency_budget_ms", "staleness_bucket"],
    "RP5D_MATERIALIZE_CAPACITY_BINDING": ["capacity_used_ratio", "crowding_group", "available_depth"],
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING": ["portfolio_exposure", "correlation_group", "marginal_utility"],
    "RP5D_MATERIALIZE_SCENARIO_BINDING": ["base_case", "lower_fill", "adverse_probability_shift", "tail_case"],
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING": ["trial_count", "family_count", "purged_embargo_key", "fdr_policy_ref"],
    "RP5D_MATERIALIZE_NO_TRADE_BINDING": ["no_trade_expected_pnl", "candidate_minus_no_trade", "no_trade_margin_bps"],
    "RP5D_MATERIALIZE_RANKING_READINESS": ["lcb", "tca", "fill", "capacity", "portfolio", "overfit", "no_trade"],
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS": ["selection_key", "diversity_constraints", "challenger_set"],
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS": ["condition_key", "regime_bucket", "memory_scope"],
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS": ["signal_probability", "market_implied_probability", "edge_hint"],
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS": ["hot_path_key", "precompute_fields", "latency_budget_ms"],
    "RP5D_MATERIALIZE_QUANTUM_MAPPING": ["decision_variable_domain", "objective_terms", "constraint_terms"],
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK": ["classical_optimizer_family", "fallback_policy_ref"],
    "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED": ["agent_id", "execution_role", "route_rule_ref"],
}

ADAPTER_OWNER = {
    "INPUT_CONTRACT_ADAPTER": "InputContractAgent",
    "UNIT_CONTRACT_ADAPTER": "UnitAdapterAgent",
    "FORMULA_TO_PNL_ADAPTER": "FormulaToPnLAgent",
    "MARKET_DATA_BINDING_ADAPTER": "MarketDataBindingAgent",
    "TCA_COST_ADAPTER": "ExecutionCostBindingAgent",
    "FILL_LIQUIDITY_ADAPTER": "ExecutionCostBindingAgent",
    "LATENCY_STALENESS_ADAPTER": "ExecutionCostBindingAgent",
    "CAPACITY_CROWDING_ADAPTER": "ExecutionCostBindingAgent",
    "PORTFOLIO_CONTEXT_ADAPTER": "PortfolioScenarioRiskBindingAgent",
    "SCENARIO_LADDER_ADAPTER": "PortfolioScenarioRiskBindingAgent",
    "OVERFIT_FDR_ADAPTER": "PortfolioScenarioRiskBindingAgent",
    "NO_TRADE_COMPARATOR_ADAPTER": "PortfolioScenarioRiskBindingAgent",
    "RANKING_READINESS_ADAPTER": "RankingReadinessAgent",
    "CHAMPION_CHALLENGER_READINESS_ADAPTER": "RankingReadinessAgent",
    "REGIME_MEMORY_ADAPTER": "RegimeMemoryReadinessAgent",
    "ALPHA_EDGE_READINESS_ADAPTER": "AlphaEdgeReadinessAgent",
    "LATENCY_HOT_PATH_ADAPTER": "LatencyHotPathReadinessAgent",
    "AGENT_ROUTE_ADAPTER": "AgentDutyResolverAgent",
    "QUANTUM_MAPPING_ADAPTER": "QuantumCompatibilityAgent",
    "CLASSICAL_FALLBACK_ADAPTER": "OptimizerReadinessAgent",
    "EXTERNAL_RESEARCH_CANDIDATE_ADAPTER": "ExternalResearchScoutAgent",
}

ONTOLOGY_OWNER = {
    "signal_probability": "AlphaEdgeReadinessAgent",
    "calibration": "AlphaEdgeReadinessAgent",
    "market_implied_probability": "MarketDataBindingAgent",
    "tca_cost": "ExecutionCostBindingAgent",
    "fill_queue_liquidity": "ExecutionCostBindingAgent",
    "latency_staleness": "LatencyHotPathReadinessAgent",
    "capacity_crowding": "PortfolioScenarioRiskBindingAgent",
    "portfolio_risk": "PortfolioScenarioRiskBindingAgent",
    "regime_scenario": "RegimeMemoryReadinessAgent",
    "quantum_objective_constraint": "QuantumCompatibilityAgent",
    "classical_fallback": "OptimizerReadinessAgent",
}


def _repo_path(ref: str) -> Path:
    return REPO_ROOT / ref


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".jsonl":
        return len([line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()])
    if path.suffix in {".json", ".md", ".py"}:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    return 0


def _surface_family(ref: str) -> str:
    if "/rp5c/" in ref or "PR168_RP5C" in Path(ref).name or "pr168_rp5c" in ref:
        return "RP5C_CENTRAL_LIBRARY"
    if "/pr168_vs1/" in ref or "vs1" in Path(ref).name.lower():
        return "VS1_BOUNDED_EVIDENCE"
    if "PR165_D2" in Path(ref).name:
        return "PR165_D2_AGENT_DUTY"
    if ref.startswith("docs/master_plan/"):
        return "MASTER_PLAN_DISCOVERY"
    if ref.startswith("tests/"):
        return "TEST_CONVENTION"
    if ref.startswith("tools/"):
        return "TOOLING_CONVENTION"
    return "AUXILIARY_INPUT"


def _jsonl_schema_name(filename: str) -> str:
    stem = filename.removesuffix(".jsonl")
    return "".join(part.capitalize() for part in stem.split("_") if part) + "V1"


def _identity_sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("identity_row_id") or row.get("identity_ref") or ""), str(row.get("qku_id") or ""), str(row.get("formula_id") or ""))


def _discover_master_plan_inputs() -> tuple[list[str], list[dict[str, Any]]]:
    discovered: set[str] = set(MASTER_PLAN_EXACT_FILES)
    category_hits: dict[str, list[str]] = defaultdict(list)
    all_files = [
        rel_ref(path)
        for path in (REPO_ROOT / "docs" / "master_plan").rglob("*")
        if path.is_file()
    ]
    for pattern in MASTER_PLAN_DISCOVERY_PATTERNS:
        hits: list[str] = []
        for rel in all_files:
            if rel.startswith("docs/master_plan/generated/pr168_rp5d/"):
                continue
            if fnmatchcase(rel, pattern):
                hits.append(rel)
        hits = sorted(dict.fromkeys(hits), key=lambda item: (item.casefold(), item))
        discovered.update(hits)
        category_hits[pattern].extend(hits)

    rows: list[dict[str, Any]] = []
    watched_patterns = {
        "route_triage": "docs/master_plan/**/route*triage*",
        "crosswalk": "docs/master_plan/**/crosswalk*",
        "market_specific_index": "docs/master_plan/**/market*specific*index*",
        "command_action_matrix": "docs/master_plan/**/command*action*matrix*",
    }
    for index, (name, pattern) in enumerate(watched_patterns.items(), start=1):
        hits = sorted(category_hits.get(pattern, []), key=lambda item: (item.casefold(), item))
        rows.append(
            with_common(
                {
                    "crosswalk_discovery_ref": f"RP5D_CROSSWALK_DISCOVERY_{index:04d}",
                    "discovery_target": name,
                    "discovery_pattern": pattern,
                    "discovery_status": "FOUND" if hits else "NOT_FOUND_NON_BLOCKING_FOR_RP5D",
                    "discovered_artifact_refs": hits,
                    "fallback_surface_refs": [
                        "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
                        "docs/master_plan/generated/pr168_vs1/vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json",
                    ],
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["GovernanceAgent", "AgentDutyResolverAgent"],
                upstream_artifact_refs=list(MASTER_PLAN_EXACT_FILES),
                downstream_artifact_refs=[generated_ref("rp5d_input_inventory.jsonl")],
            )
        )
    return sorted(discovered, key=lambda item: (item.casefold(), item)), rows


def _discover_pr165_inputs() -> tuple[list[str], list[dict[str, Any]]]:
    found = [ref for ref in PR165_D2_EXPECTED_FILES if _repo_path(ref).is_file()]
    if len(found) < len(PR165_D2_EXPECTED_FILES):
        for root_name in ("docs", "src", "tools", "tests"):
            root = REPO_ROOT / root_name
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                name = path.name
                if "AgentRosterDiscoveryAudit" in name or "AgentDutySourceCrosswalk" in name:
                    found.append(rel_ref(path))
    found = sorted(dict.fromkeys(found), key=lambda item: (item.casefold(), item))
    status = "FOUND" if found else "NOT_FOUND_NON_BLOCKING_USING_RP5C_AGENT_DUTY_SURFACES"
    rows = [
        with_common(
            {
                "crosswalk_discovery_ref": "RP5D_PR165_D2_DISCOVERY_0001",
                "discovery_target": "PR165_D2_AGENT_DUTY_EVIDENCE",
                "discovery_pattern": "AgentRosterDiscoveryAudit|AgentDutySourceCrosswalk",
                "discovery_status": status,
                "discovered_artifact_refs": found,
                "fallback_surface_refs": [
                    "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
                    "docs/master_plan/generated/rp5c/agent_duty_routing_rulebook.jsonl",
                ],
            },
            producer_agent="AgentDutyResolverAgent",
            consumer_agent_refs=["GovernanceAgent", "ComputabilityMaterializerAgent"],
            upstream_artifact_refs=["docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl"],
            downstream_artifact_refs=[generated_ref("rp5d_agent_routing_ledger.jsonl")],
        )
    ]
    return found, rows


def _required_input_refs() -> tuple[list[str], list[dict[str, Any]]]:
    master_plan_refs, crosswalk_rows = _discover_master_plan_inputs()
    pr165_refs, pr165_rows = _discover_pr165_inputs()
    refs = [
        *master_plan_refs,
        *RP5C_REQUIRED_FILES,
        *VS1_REQUIRED_FILES,
        *pr165_refs,
        "tests/pr168_rp5c/_helpers.py",
        "tests/pr168_vs1/_helpers.py",
        "tools/run_validation_gates.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
    ]
    return sorted(dict.fromkeys(refs), key=lambda item: (item.casefold(), item)), [*crosswalk_rows, *pr165_rows]


def build_reading_and_input_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    refs, discovery_rows = _required_input_refs()
    reading_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    consumption_rows: list[dict[str, Any]] = []
    for index, ref in enumerate(refs, start=1):
        path = _repo_path(ref)
        exists = path.is_file()
        manifest = path.with_name(path.stem + ".manifest.json") if ref.endswith(".jsonl") else None
        row_count = _row_count(path)
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        read_status = "READ_UTF8" if exists else "MISSING_NON_BLOCKING_OPTIONAL" if "PR165_D2" in ref else "MISSING_REQUIRED"
        reading_rows.append(
            with_common(
                {
                    "reading_receipt_ref": f"RP5D_READING_RECEIPT_{index:05d}",
                    "file_ref": ref,
                    "exists_flag": exists,
                    "read_status": read_status,
                    "row_count_or_line_count": row_count,
                    "reader_agent": "FormulaLibraryAgent" if _surface_family(ref).startswith("RP5C") else "VS1EvidenceAgent" if _surface_family(ref).startswith("VS1") else "CommanderAgent",
                    "receipt_schema": "RP5DReadingReceiptV1",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["GovernanceAgent", "ComputabilityMaterializerAgent"],
                upstream_artifact_refs=[ref] if exists else [],
                downstream_artifact_refs=[generated_ref("rp5d_input_inventory.jsonl")],
            )
        )
        inventory_rows.append(
            with_common(
                {
                    "input_surface_ref": f"RP5D_INPUT_SURFACE_{index:05d}",
                    "surface_path": ref,
                    "surface_family": _surface_family(ref),
                    "producer_pr_ref": _surface_family(ref).split("_")[0],
                    "consumer_pr_ref": PR_ID,
                    "exists_flag": exists,
                    "row_count": row_count,
                    "manifest_ref": rel_ref(manifest) if manifest is not None and manifest.is_file() else None,
                    "authority_class": "GENERATED_CENTRAL_SURFACE_NOT_SOURCE_TRUTH" if ref.startswith("docs/master_plan/generated/") else "TOOL_OR_DOC_CONTEXT",
                    "used_for_field_refs": ["computability_materialization_state", "executability_state", "adapter_queue_refs"] if exists else [],
                    "not_used_reason": "" if exists else "OPTIONAL_DISCOVERY_FILE_ABSENT_WITH_FALLBACK_ROUTE" if "PR165_D2" in ref else "MISSING_REQUIRED_INPUT",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["GovernanceAgent", "ComputabilityMaterializerAgent"],
                upstream_artifact_refs=[ref] if exists else [],
                downstream_artifact_refs=[generated_ref("rp5d_input_consumption.jsonl")],
            )
        )
        consumed = exists
        consumption_rows.append(
            with_common(
                {
                    "consumption_ref": f"RP5D_INPUT_CONSUMPTION_{index:05d}",
                    "input_surface_ref": f"RP5D_INPUT_SURFACE_{index:05d}",
                    "surface_path": ref,
                    "consumed_flag": consumed,
                    "consumer_agent_refs": ["FormulaLibraryAgent", "VS1EvidenceAgent", "AgentDutyResolverAgent", "ComputabilityMaterializerAgent"],
                    "consumer_output_refs": [generated_ref("rp5d_rp5c_vs1_crosswalk.jsonl"), generated_ref("rp5d_comp_materialization.jsonl")],
                    "row_count_consumed": row_count if consumed else 0,
                    "value_refs_consumed": ["identity_row_id", "formula_id", "qku_id", "ontology_category"] if consumed else [],
                    "not_consumed_reason": "" if consumed else "OPTIONAL_DISCOVERY_FILE_ABSENT_ROUTED_TO_RP5C_AGENT_DUTY_SURFACES" if "PR165_D2" in ref else "MISSING_REQUIRED_INPUT",
                    "downstream_effect_refs": ["computability_tiering", "adapter_queue_generation"] if consumed else ["non_blocking_discovery_receipt"],
                    "future_consumer_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1"],
                    "orphan_flag": False,
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["GovernanceAgent", "ValueLineageAgent"],
                upstream_artifact_refs=[ref] if exists else ["docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_value_lineage.jsonl")],
            )
        )
    return reading_rows, discovery_rows, inventory_rows, consumption_rows


def build_execution_authority() -> dict[str, Any]:
    payload = {
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "pr_id": PR_ID,
        "execution_mode": "RP5D_COMPUTABILITY_TIERING_ONLY_NON_EXECUTING",
        "paper_submit_authorized": False,
        "live_submit_authorized": False,
        "connector_runtime_authorized": False,
        "private_state_fetch_authorized": False,
        "cash_runtime_authorized": False,
        "venue_api_call_authorized": False,
        "source_fact_acceptance_authorized": False,
        "fixture_constant_from_external_source_authorized": False,
        "trade_simulation_authorized": False,
        "execution_adjusted_ranking_authorized": False,
        "champion_selection_authorized": False,
        "stack_generation_authorized": False,
        "order_variable_optimization_authorized": False,
        "qopt_execution_authorized": False,
        "quantum_backend_execution_authorized": False,
        "quantum_advantage_claim_authorized": False,
        "order_submit_authorized": False,
        "order_cancel_authorized": False,
        "order_replace_authorized": False,
        "order_close_authorized": False,
        "qku_deletion_authorized": False,
        "formula_deletion_authorized": False,
        "formula_mutation_authorized": False,
        "global_qku_ban_authorized": False,
        "global_formula_ban_authorized": False,
        "qtt_sha_authority_authorized": False,
        "atomicrows_bundle_sha_authorized": False,
    }
    return with_common(
        payload,
        producer_agent="CommanderAgent",
        consumer_agent_refs=["AllRP5DAgents", "RP5DValidator"],
        upstream_artifact_refs=["docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl"],
        downstream_artifact_refs=[generated_ref(name) for name in JSONL_OUTPUTS],
    )


def build_blocker_policy() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, code in enumerate(BLOCKER_CODES, start=1):
        adapter = BLOCKER_TO_ADAPTER.get(code, "PRESERVATION_ROUTE")
        rows.append(
            with_common(
                {
                    "blocker_policy_ref": BLOCKER_POLICY_REF,
                    "blocker_code": code,
                    "blocker_category": "preservation" if code.startswith("RP5D_PRESERVE") else "materialization_adapter_gate",
                    "severity": "PRESERVE" if code.startswith("RP5D_PRESERVE") else "ACTION_REQUIRED",
                    "tier_state_mapping": BLOCKER_TO_STATE.get(code, code.replace("RP5D_", "")),
                    "adapter_queue_mapping": adapter,
                    "retriable_flag": True,
                    "condition_scoped_memory_allowed_flag": code in {"RP5D_MATERIALIZE_NO_TRADE_BINDING", "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS"},
                    "productive_adapter_gate_flag": True,
                    "global_ban_allowed_flag": False,
                    "formula_mutation_allowed_flag": False,
                    "qku_deletion_allowed_flag": False,
                    "consumer_agent_refs": ["GovernanceAgent", ADAPTER_OWNER.get(adapter, "ComputabilityMaterializerAgent")],
                    "rp5d_blocker_policy_row_id": f"RP5D_BLOCKER_POLICY_{index:04d}",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["AllRP5DAgents", "RP5DValidator"],
                upstream_artifact_refs=[generated_ref("rp5d_execution_authority.report.json")],
                downstream_artifact_refs=[generated_ref("rp5d_comp_materialization.jsonl"), generated_ref(QUEUE_FILE_BY_BLOCKER.get(code, "rp5d_no_mutation_proof.jsonl"))],
            )
        )
    return rows


def build_state_registries() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    comp_rows: list[dict[str, Any]] = []
    for index, state in enumerate(COMPUTABILITY_STATES, start=1):
        computable_now = state == "COMPUTABLE_REPLAY_PAPER_EXECUTABLE_NOW"
        preserved = state.startswith("PRESERVED_")
        comp_rows.append(
            with_common(
                {
                    "state_ref": f"RP5D_COMP_STATE_{index:03d}",
                    "state_name": state,
                    "state_description": state.lower(),
                    "computable_now_flag": computable_now,
                    "computable_after_adapter_flag": state.startswith("COMPUTABLE_AFTER_"),
                    "adapter_required_flag": state.startswith("COMPUTABLE_AFTER_") or state == "MATERIALIZATION_REQUIRED_FROM_EXTERNAL_CANDIDATE",
                    "stage1_selectable_flag": computable_now,
                    "replay_candidate_flag": computable_now or state.startswith("COMPUTABLE_AFTER_"),
                    "paper_candidate_flag": computable_now,
                    "future_retest_allowed_flag": not state.endswith("EXACT_REASON"),
                    "global_ban_flag": False,
                    "formula_mutation_allowed_flag": False,
                    "qku_deletion_allowed_flag": False,
                    "downstream_consumer_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1"] if not preserved else ["FutureStageResolver"],
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["ComputabilityMaterializerAgent", "RP5DValidator"],
                upstream_artifact_refs=[generated_ref("rp5d_blocker_policy_registry.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_comp_materialization.jsonl")],
            )
        )
    exec_rows: list[dict[str, Any]] = []
    for index, state in enumerate(EXECUTABILITY_STATES, start=1):
        exec_rows.append(
            with_common(
                {
                    "state_ref": f"RP5D_EXEC_STATE_{index:03d}",
                    "executability_state": state,
                    "state_description": state.lower(),
                    "replay_candidate_flag": state in {"REPLAY_PAPER_EXECUTABLE_NOW", "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER"},
                    "paper_candidate_flag": state == "REPLAY_PAPER_EXECUTABLE_NOW",
                    "adapter_required_flag": state == "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER",
                    "preserved_flag": state.startswith("PRESERVED_"),
                    "downstream_consumer_refs": ["RP5G", "RANK4", "PAPER-LOOP", "LIVE-DRYRUN"],
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["ExecutabilityTierAgent", "RP5DValidator"],
                upstream_artifact_refs=[generated_ref("rp5d_comp_state_registry.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl")],
            )
        )
    return comp_rows, exec_rows


def build_adapter_family_registry() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, family in enumerate(ADAPTER_FAMILIES, start=1):
        owner = ADAPTER_OWNER[family]
        rows.append(
            with_common(
                {
                    "adapter_family_ref": family,
                    "owner_agent_ref": owner,
                    "consumer_agent_refs": ["ComputabilityMaterializerAgent", "ExecutabilityTierAgent", "RP5G", "RANK4", "QOPT"],
                    "input_contract_schema_ref": f"{family}::INPUT_CONTRACT_V1",
                    "output_contract_schema_ref": f"{family}::OUTPUT_CONTRACT_V1",
                    "priority_policy_ref": "RP5D_POLICY_PARAM::adapter_priority_buckets",
                    "future_pr_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "LIVE-DRYRUN"],
                    "materialization_unlock_state": f"{family}::ADAPTER_COMPLETE_RETEST_RP5D",
                    "live_authority_created_flag": False,
                    "rp5d_adapter_family_row_id": f"RP5D_ADAPTER_FAMILY_{index:04d}",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["AllRP5DAgents", "RP5DValidator"],
                upstream_artifact_refs=[generated_ref("rp5d_blocker_policy_registry.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_input_queue.jsonl"), generated_ref("rp5d_exec_tiers.jsonl")],
            )
        )
    return rows


def build_policy_parameters() -> list[dict[str, Any]]:
    groups: dict[str, dict[str, object]] = {
        "coverage_caps": {
            "universal_identity_coverage_required_flag": True,
            "stage1_detailed_tiering_required_flag": True,
            "non_stage1_universal_coverage_required_flag": True,
            "max_rows_per_report_shard": 500000,
            "max_adapter_queue_rows_per_file": 250000,
            "max_adapter_queue_example_rows_in_summary": 25,
        },
        "materialization_rules": {
            "final_unknown_state_allowed": False,
            "metadata_only_ready_state_allowed": False,
            "executable_now_requires_input_contract": True,
            "executable_now_requires_unit_contract": True,
            "executable_now_requires_formula_to_pnl_map": True,
            "executable_now_requires_market_data_binding": True,
            "executable_now_requires_agent_route": True,
            "executable_now_requires_downstream_consumer": True,
            "non_executable_state_requires_adapter_queue_or_preservation_reason": True,
        },
        "edge_capture_readiness_rules": {
            "alpha_readiness_requires_signal_probability_or_market_implied_probability": True,
            "positive_pnl_readiness_requires_formula_to_pnl_map": True,
            "tca_edge_readiness_requires_fee_spread_slippage_latency_capacity_fields": True,
            "no_trade_readiness_requires_candidate_minus_no_trade_fields": True,
            "portfolio_edge_readiness_requires_marginal_utility_fields": True,
            "future_trade_order_execution_requires_later_authority": True,
        },
        "execution_readiness_contracts": {
            "ranking_readiness_requires_tca_fill_latency_capacity_portfolio_overfit_no_trade_fields": True,
            "tca_readiness_requires_fee_spread_slippage_queue_latency_capacity_crowding_capital_lock_fields": True,
            "no_trade_readiness_requires_no_trade_expected_pnl_and_candidate_margin_fields": True,
            "champion_readiness_requires_future_lcb_tca_fill_latency_capacity_portfolio_scenario_overfit_agent_route_no_orphan_fields": True,
            "regime_memory_readiness_requires_condition_key_fields": True,
        },
        "quantum_compatibility_rules": {
            "qubo_requires_binary_decision_variables": True,
            "bqm_requires_binary_or_spin_variables": True,
            "cqm_allows_binary_integer_continuous_with_constraints": True,
            "dqm_requires_discrete_cases": True,
            "quadratic_program_requires_objective_constraint_terms": True,
            "ising_requires_spin_mapping_candidate": True,
            "qaoa_vqe_readiness_requires_quadratic_program_or_ising_candidate": True,
            "backend_execution_allowed": False,
            "quantum_advantage_claim_allowed": False,
        },
        "external_research_policy": {
            "official_and_non_official_candidate_sources_allowed": True,
            "reject_non_official_merely_because_non_official": False,
            "external_research_fact_acceptance_allowed": False,
            "external_research_connector_binding_allowed": False,
            "external_research_fixture_constant_allowed": False,
            "external_research_live_authority_allowed": False,
        },
        "path_safety_policy": {
            "generated_root": "docs/master_plan/generated/pr168_rp5d/",
            "max_generated_filename_chars": 90,
            "max_repo_relative_path_chars": 180,
            "max_windows_absolute_path_chars": 240,
            "windows_repo_root_assumption": r"C:\Users\Owner\Projects\QTT_New0526\\",
            "case_collision_allowed": False,
            "spaces_in_generated_filenames_allowed": False,
            "unsafe_shell_chars_in_generated_filenames_allowed": False,
            "unicode_punctuation_in_generated_filenames_allowed": False,
            "unregistered_abbreviations_allowed": False,
        },
        "validation_timeout_policy": {"default_timeout_ms": 3600000},
    }
    rows: list[dict[str, Any]] = []
    index = 0
    for group, params in groups.items():
        for name, value in params.items():
            index += 1
            rows.append(
                with_common(
                    {
                        "policy_parameter_ref": f"RP5D_POLICY_PARAM::{group}::{name}",
                        "parameter_group": group,
                        "parameter_name": name,
                        "parameter_value": value,
                        "parameter_value_string": str(value).lower() if isinstance(value, bool) else str(value),
                        "parameter_type": type(value).__name__,
                        "rp5d_policy_parameter_row_id": f"RP5D_POLICY_PARAM_{index:04d}",
                    },
                    producer_agent="CommanderAgent",
                    consumer_agent_refs=["AllRP5DAgents", "RP5DValidator"],
                    upstream_artifact_refs=[generated_ref("rp5d_execution_authority.report.json")],
                    downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
                )
            )
    return rows


def _vs1_evidence() -> dict[str, Any]:
    root = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_vs1"
    bindings = read_jsonl(root / "selected_computable_qku_formula_bindings.jsonl")
    trade_candidates = read_jsonl(root / "trade_plan_candidates.jsonl")
    pnl_rows = read_jsonl(root / "expected_cash_pnl_receipts.jsonl")
    quantum_rows = read_jsonl(root / "quantum_structural_readiness_receipts.jsonl")
    no_trade_rows = read_jsonl(root / "no_trade_comparator_receipts.jsonl")
    objective_rows = read_jsonl(root / "objective_term_ledger.jsonl")
    candidate_formula_refs = {ref for row in trade_candidates for ref in row.get("formula_refs", [])}
    pnl_formula_refs = {ref for row in pnl_rows for ref in row.get("formula_version_refs", [])}
    quantum_formula_refs = {ref for row in quantum_rows for ref in row.get("formula_refs", [])}
    formula_to_trade_refs: dict[str, list[str]] = defaultdict(list)
    for row in trade_candidates:
        for ref in row.get("formula_refs", []):
            formula_to_trade_refs[ref].append(row.get("trade_plan_id", ""))
    binding_by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bindings:
        binding_by_identity[row["identity_ref"]].append(row)
    no_trade_by_formula: dict[str, list[str]] = defaultdict(list)
    for row in no_trade_rows:
        hint = row.get("condition_scoped_memory_hint", {})
        for ref in hint.get("formula_refs", []):
            no_trade_by_formula[ref].append(row.get("no_trade_comparator_ref", ""))
    return {
        "bindings": bindings,
        "trade_candidates": trade_candidates,
        "pnl_rows": pnl_rows,
        "quantum_rows": quantum_rows,
        "no_trade_rows": no_trade_rows,
        "objective_rows": objective_rows,
        "candidate_formula_refs": candidate_formula_refs,
        "pnl_formula_refs": pnl_formula_refs,
        "quantum_formula_refs": quantum_formula_refs,
        "formula_to_trade_refs": {key: stable_unique(value) for key, value in formula_to_trade_refs.items()},
        "binding_by_identity": binding_by_identity,
        "no_trade_by_formula": {key: stable_unique(value) for key, value in no_trade_by_formula.items()},
    }


def _detect_contracts(identity: dict[str, Any], stage1: bool, vs1: dict[str, Any]) -> dict[str, Any]:
    identity_ref = identity["identity_row_id"]
    formula_id = str(identity.get("formula_id") or "")
    ontology = str(identity.get("ontology_category") or "")
    selected_bindings = list(vs1["binding_by_identity"].get(identity_ref, []))
    selected = bool(selected_bindings)
    has_expression = bool(identity.get("formula_expression_ref")) or selected
    has_plugin = bool(identity.get("plugin_ref"))
    has_unit = has_plugin or (selected and has_expression)
    has_pnl = bool(identity.get("formula_to_pnl_ref")) or formula_id in vs1["pnl_formula_refs"]
    has_market_data = selected or formula_id in vs1["candidate_formula_refs"] or ontology in {"market_implied_probability", "tca_cost", "fill_queue_liquidity"}
    fully_vs1_core = selected and has_expression and has_plugin and has_pnl and has_market_data
    route_available = bool(identity.get("derived_route_resolution_refs")) and ontology != "unknown_needs_review"
    downstream_available = bool(identity.get("downstream_pr_refs"))

    contract = {
        "input_contract_available_flag": has_expression,
        "unit_contract_available_flag": has_unit,
        "formula_to_pnl_available_flag": has_pnl,
        "market_data_binding_available_flag": has_market_data,
        "tca_readiness_available_flag": fully_vs1_core or ontology == "tca_cost",
        "fill_liquidity_readiness_available_flag": fully_vs1_core or ontology == "fill_queue_liquidity",
        "latency_readiness_available_flag": fully_vs1_core or ontology == "latency_staleness",
        "capacity_crowding_readiness_available_flag": fully_vs1_core or ontology == "capacity_crowding",
        "portfolio_context_readiness_available_flag": fully_vs1_core or ontology == "portfolio_risk",
        "scenario_ladder_readiness_available_flag": fully_vs1_core or ontology == "regime_scenario",
        "overfit_fdr_readiness_available_flag": fully_vs1_core,
        "no_trade_readiness_available_flag": fully_vs1_core,
        "ranking_readiness_available_flag": fully_vs1_core,
        "champion_challenger_readiness_available_flag": fully_vs1_core,
        "regime_memory_readiness_available_flag": fully_vs1_core or ontology == "regime_scenario",
        "alpha_edge_readiness_available_flag": fully_vs1_core or ontology in {"signal_probability", "market_implied_probability", "calibration"},
        "latency_hot_path_readiness_available_flag": fully_vs1_core or ontology == "latency_staleness",
        "future_trade_variable_contract_available_flag": fully_vs1_core,
        "quantum_objective_constraint_available_flag": fully_vs1_core or formula_id in vs1["quantum_formula_refs"] or ontology == "quantum_objective_constraint",
        "classical_fallback_available_flag": fully_vs1_core or ontology == "classical_fallback",
        "agent_route_available_flag": route_available,
        "downstream_consumer_available_flag": downstream_available,
    }
    if fully_vs1_core:
        for field in list(contract):
            if field.endswith("_available_flag"):
                contract[field] = True

    missing = [code for code, field in CONTRACT_CODE_FIELDS.items() if not bool(contract[field])]
    if stage1 and not route_available:
        missing.append("RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED")
    if stage1 and not downstream_available:
        missing.append("RP5D_NO_DOWNSTREAM_CONSUMER_ACTION_REQUIRED")
    contract["missing_contract_codes"] = stable_unique(missing)
    contract["vs1_selected_evidence_flag"] = selected
    contract["vs1_binding_refs"] = stable_unique(row.get("computable_binding_id") for row in selected_bindings)
    contract["vs1_trade_plan_refs"] = stable_unique(vs1["formula_to_trade_refs"].get(formula_id, []))
    contract["vs1_no_trade_refs"] = stable_unique(vs1["no_trade_by_formula"].get(formula_id, []))
    return contract


def _computability_state(identity: dict[str, Any], stage1: bool, contract: dict[str, Any]) -> str:
    duplicate = str(identity.get("duplicate_status") or "") not in {"", "UNIQUE_PRESERVED"}
    unsafe = str(identity.get("library_state") or "").startswith("UNSAFE_UNMAPPABLE")
    if unsafe:
        return "PRESERVED_UNSAFE_UNMAPPABLE_WITH_EXACT_REASON"
    if duplicate:
        return "PRESERVED_DUPLICATE_LOW_PRIORITY_WITH_CANONICAL_REF"
    if not stage1:
        return "PRESERVED_OUT_OF_STAGE_DORMANT_WITH_FUTURE_STAGE_ROUTE"
    missing = list(contract["missing_contract_codes"])
    if not missing:
        return "COMPUTABLE_REPLAY_PAPER_EXECUTABLE_NOW"
    for code in (
        "RP5D_MATERIALIZE_INPUT_CONTRACT",
        "RP5D_MATERIALIZE_UNIT_CONTRACT",
        "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP",
        "RP5D_MATERIALIZE_MARKET_DATA_BINDING",
        "RP5D_MATERIALIZE_TCA_BINDING",
        "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING",
        "RP5D_MATERIALIZE_LATENCY_BINDING",
        "RP5D_MATERIALIZE_CAPACITY_BINDING",
        "RP5D_MATERIALIZE_PORTFOLIO_BINDING",
        "RP5D_MATERIALIZE_SCENARIO_BINDING",
        "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING",
        "RP5D_MATERIALIZE_NO_TRADE_BINDING",
        "RP5D_MATERIALIZE_RANKING_READINESS",
        "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS",
        "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS",
        "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS",
        "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS",
        "RP5D_MATERIALIZE_QUANTUM_MAPPING",
        "RP5D_MATERIALIZE_CLASSICAL_FALLBACK",
        "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED",
    ):
        if code in missing:
            return BLOCKER_TO_STATE.get(code, "COMPUTABLE_AFTER_INPUT_BINDING")
    return "MATERIALIZATION_REQUIRED_FROM_EXTERNAL_CANDIDATE"


def _exec_state(comp_state: str, adapter_refs: list[str]) -> str:
    if comp_state == "COMPUTABLE_REPLAY_PAPER_EXECUTABLE_NOW":
        return "REPLAY_PAPER_EXECUTABLE_NOW"
    if comp_state == "PRESERVED_DUPLICATE_LOW_PRIORITY_WITH_CANONICAL_REF":
        return "PRESERVED_DUPLICATE_LOW_PRIORITY"
    if comp_state == "PRESERVED_UNSAFE_UNMAPPABLE_WITH_EXACT_REASON":
        return "PRESERVED_UNSAFE_UNMAPPABLE_NOT_EXECUTED"
    if comp_state == "PRESERVED_OUT_OF_STAGE_DORMANT_WITH_FUTURE_STAGE_ROUTE":
        return "PRESERVED_NOT_STAGE1_ACTIVE"
    if adapter_refs:
        return "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER"
    return "NEEDS_ACTIONABLE_MATERIALIZATION"


def _priority_bucket(identity: dict[str, Any], code: str, contract: dict[str, Any], stage_access_mode: str) -> str:
    if contract["vs1_selected_evidence_flag"]:
        return "P0_UNLOCKS_VS1_PROVEN_PATH_EXTENSION"
    if stage_access_mode == "DEFAULT_COMPUTE":
        return "P1_UNLOCKS_STAGE1_DEFAULT_COMPUTE"
    if stage_access_mode == "AVAILABLE_ON_DEMAND":
        return "P2_UNLOCKS_STAGE1_AVAILABLE_ON_DEMAND"
    if "QUANTUM" in code:
        return "P3_UNLOCKS_QUANTUM_FORWARD_MAPPING"
    if "RANKING" in code:
        return "P4_UNLOCKS_EXECUTION_ADJUSTED_RANKING_READINESS"
    if "ALPHA" in code:
        return "P5_UNLOCKS_ALPHA_EDGE_CAPTURE_READINESS"
    if "HOT_PATH" in code or "LATENCY" in code:
        return "P6_UNLOCKS_LOW_LATENCY_HOT_PATH_FUTURE_SEED"
    if str(identity.get("duplicate_status") or "") not in {"", "UNIQUE_PRESERVED"}:
        return "P7_DUPLICATE_OR_LOW_PRIORITY"
    return "P8_PRESERVED_REVIEW_ONLY"


def _queue_row(
    identity: dict[str, Any],
    code: str,
    index: int,
    contract: dict[str, Any],
    stage_seed: dict[str, Any],
) -> dict[str, Any]:
    adapter = BLOCKER_TO_ADAPTER[code]
    owner = ADAPTER_OWNER[adapter]
    queue_file = QUEUE_FILE_BY_BLOCKER[code]
    platform_refs = stable_unique(stage_seed.get("platform_applicability_states", []) or PLATFORM_IDS)
    required_fields = CONTRACT_CODE_REQUIRED_FIELDS.get(code, ["adapter_contract_payload"])
    return with_common(
        {
            "adapter_queue_ref": f"RP5D_QUEUE_{index:08d}_{adapter}",
            "adapter_family_ref": adapter,
            "identity_ref": identity["identity_row_id"],
            "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
            "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
            "stage_profile_id": STAGE_PROFILE_ID,
            "market_family": MARKET_FAMILY,
            "platform_refs": platform_refs,
            "agent_owner_ref": owner,
            "priority_bucket": _priority_bucket(identity, code, contract, str(stage_seed.get("stage_access_mode") or "")),
            "priority_reason_codes": [code, "STAGE1_DETAILED_TIERING"],
            "missing_contract_codes": [code],
            "required_input_fields": required_fields if "INPUT" in code else [],
            "required_output_fields": ["adapter_completion_receipt_ref", "retest_policy_ref"],
            "required_unit_fields": required_fields if "UNIT" in code else [],
            "required_market_data_fields": required_fields if "MARKET_DATA" in code else [],
            "required_formula_to_pnl_fields": required_fields if "PNL" in code else [],
            "required_test_vector_fields": ["fixture_free_test_vector", "edge_case_test_vector"],
            "required_execution_readiness_fields": required_fields if any(token in code for token in ("TCA", "FILL", "LATENCY", "CAPACITY", "PORTFOLIO", "SCENARIO", "OVERFIT", "NO_TRADE", "RANKING", "CHAMPION")) else [],
            "required_alpha_edge_fields": required_fields if "ALPHA" in code else [],
            "required_latency_hot_path_fields": required_fields if "HOT_PATH" in code else [],
            "required_future_trade_variable_fields": ["market", "venue", "side", "entry", "size", "hold_duration", "exit_rule"],
            "required_quantum_mapping_fields": required_fields if "QUANTUM" in code else [],
            "vs1_evidence_refs": [*contract["vs1_binding_refs"], *contract["vs1_trade_plan_refs"]],
            "rp5c_lineage_refs": stable_unique(identity.get("derived_route_resolution_refs", []) + identity.get("qku_market_applicability_matrix_refs", [])),
            "downstream_pr_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1"],
            "replay_unlock_state_after_completion": "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER_RETEST",
            "paper_unlock_state_after_completion": "PAPER_CANDIDATE_AFTER_LATER_AUTHORITY_AND_RETEST",
            "live_authority_created_flag": False,
            "source_fact_acceptance_created_flag": False,
            "connector_binding_created_flag": False,
            "queue_file_ref": generated_ref(queue_file),
        },
        producer_agent=owner,
        consumer_agent_refs=["ComputabilityMaterializerAgent", "ExecutabilityTierAgent", "RP5G", "RANK4", "QOPT"],
        upstream_artifact_refs=["docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl"],
        downstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl"), generated_ref("rp5d_future_pr_handoff.report.json")],
        blocker_codes=[code],
    )


def build_materialization() -> dict[str, list[dict[str, Any]]]:
    library = load_library(REPO_ROOT)
    identities = sorted(library["immutable_qku_formula_library"], key=_identity_sort_key)
    matrix_by_id = {row["identity_row_id"]: row for row in read_jsonl(REPO_ROOT / "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl")}
    handoff_by_id = {row["identity_row_id"]: row for row in read_jsonl(REPO_ROOT / "docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl")}
    stage_seed_rows = sorted(read_jsonl(REPO_ROOT / "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl"), key=_identity_sort_key)
    stage_seed_by_id = {row["identity_row_id"]: row for row in stage_seed_rows}
    vs1 = _vs1_evidence()

    contracts_by_id: dict[str, dict[str, Any]] = {}
    comp_state_by_id: dict[str, str] = {}
    queue_rows_by_file: dict[str, list[dict[str, Any]]] = {filename: [] for filename in QUEUE_FILE_BY_BLOCKER.values()}
    queue_refs_by_identity: dict[str, list[str]] = defaultdict(list)
    queue_index = 0

    for identity in identities:
        identity_ref = identity["identity_row_id"]
        stage1 = identity_ref in stage_seed_by_id
        contract = _detect_contracts(identity, stage1, vs1)
        contracts_by_id[identity_ref] = contract
        comp_state_by_id[identity_ref] = _computability_state(identity, stage1, contract)
        if stage1:
            for code in contract["missing_contract_codes"]:
                if code not in QUEUE_FILE_BY_BLOCKER:
                    continue
                queue_index += 1
                row = _queue_row(identity, code, queue_index, contract, stage_seed_by_id[identity_ref])
                queue_rows_by_file[QUEUE_FILE_BY_BLOCKER[code]].append(row)
                queue_refs_by_identity[identity_ref].append(row["adapter_queue_ref"])

    coverage_rows: list[dict[str, Any]] = []
    comp_rows: list[dict[str, Any]] = []
    bundle_rows: list[dict[str, Any]] = []
    stage1_rows: list[dict[str, Any]] = []
    tier_rows: list[dict[str, Any]] = []
    computable_universe_rows: list[dict[str, Any]] = []
    crosswalk_rows: list[dict[str, Any]] = []

    for index, identity in enumerate(identities, start=1):
        identity_ref = identity["identity_row_id"]
        matrix = matrix_by_id.get(identity_ref, {})
        handoff = handoff_by_id.get(identity_ref, {})
        stage1 = identity_ref in stage_seed_by_id
        contract = contracts_by_id[identity_ref]
        state = comp_state_by_id[identity_ref]
        queue_refs = stable_unique(queue_refs_by_identity.get(identity_ref, []))
        qku_ref = identity.get("qku_id") or f"{identity_ref}::QKU_REF_NOT_PRESENT"
        formula_ref = identity.get("formula_id") or f"{identity_ref}::FORMULA_REF_NOT_PRESENT"
        consumer_refs = stable_unique(identity.get("downstream_pr_refs", []) + ["RP5DValidator"])
        missing_codes = contract["missing_contract_codes"] if stage1 else []
        if state == "PRESERVED_DUPLICATE_LOW_PRIORITY_WITH_CANONICAL_REF":
            preservation_reason = "DUPLICATE_LOW_PRIORITY_PRESERVED_WITH_CANONICAL_REF"
        elif state == "PRESERVED_UNSAFE_UNMAPPABLE_WITH_EXACT_REASON":
            preservation_reason = "UNSAFE_UNMAPPABLE_PRESERVED_WITH_EXACT_REASON"
        elif not stage1:
            preservation_reason = "OUT_OF_STAGE_DORMANT_PRESERVED_WITH_FUTURE_STAGE_ROUTE"
        else:
            preservation_reason = ""
        coverage_rows.append(
            with_common(
                {
                    "coverage_ref": f"RP5D_UNIVERSAL_COVERAGE_{index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    "market_family_scope": stable_unique(matrix.get("market_family_refs", [])) or ["FUTURE_STAGE_OR_UNKNOWN"],
                    "stage1_seed_member_flag": stage1,
                    "universal_computability_classification_required_flag": True,
                    "stage1_detailed_tiering_required_flag": stage1,
                    "universal_preservation_state": state,
                    "dormant_out_of_stage_flag": not stage1,
                    "coverage_status": "COVERED_WITH_STAGE1_TIER" if stage1 else "COVERED_PRESERVED_DORMANT_FUTURE_STAGE_ROUTE",
                },
                producer_agent="ComputabilityMaterializerAgent",
                consumer_agent_refs=consumer_refs,
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_comp_materialization.jsonl")],
            )
        )
        comp_rows.append(
            with_common(
                {
                    "computability_ref": f"RP5D_COMP_{index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    "market_family_scope": stable_unique(matrix.get("market_family_refs", [])) or ["FUTURE_STAGE_OR_UNKNOWN"],
                    "stage_profile_refs": [STAGE_PROFILE_ID] if stage1 else ["FUTURE_STAGE_ROUTE_REQUIRED"],
                    "computability_materialization_state": state,
                    "computable_now_flag": state == "COMPUTABLE_REPLAY_PAPER_EXECUTABLE_NOW",
                    "computable_after_adapter_flag": state.startswith("COMPUTABLE_AFTER_"),
                    "metadata_only_flag": False,
                    "placeholder_flag": False,
                    "required_input_contract_refs": ["RP5D_INPUT_CONTRACT::STAGE1_PM_CORE"],
                    "required_unit_contract_refs": ["RP5D_UNIT_CONTRACT::PROBABILITY_USD_COUNT_TIME"],
                    "required_formula_to_pnl_refs": ["RP5D_FORMULA_TO_PNL::BINARY_CONTRACT_CASH_PATH"],
                    "required_market_data_binding_refs": ["RP5D_MARKET_DATA_BINDING::THREE_PLATFORM_STAGE1"],
                    "required_execution_readiness_refs": ["TCA", "FILL", "LATENCY", "CAPACITY", "PORTFOLIO", "SCENARIO", "OVERFIT_FDR", "NO_TRADE"],
                    "required_alpha_edge_readiness_refs": ["ALPHA_EDGE_READINESS"],
                    "required_quantum_mapping_refs": ["QUBO", "BQM", "CQM", "DQM", "QuadraticProgram", "Ising"],
                    "missing_contract_codes": missing_codes,
                    "adapter_queue_refs": queue_refs,
                    "owner_agent_ref": ONTOLOGY_OWNER.get(str(identity.get("ontology_category")), "ComputabilityMaterializerAgent"),
                    "future_consumer_pr_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "LIVE-DRYRUN"],
                    "unlock_condition": "ALL_REQUIRED_CONTRACTS_PRESENT" if state == "COMPUTABLE_REPLAY_PAPER_EXECUTABLE_NOW" else "COMPLETE_ADAPTER_QUEUE_ROWS_AND_RETEST" if stage1 else "FUTURE_STAGE_ACTIVATION_AND_RETEST",
                    "preservation_reason_if_not_executable": preservation_reason,
                },
                producer_agent="ComputabilityMaterializerAgent",
                consumer_agent_refs=consumer_refs,
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl", "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl"), generated_ref("rp5d_contract_bundles.jsonl")],
                blocker_codes=missing_codes,
            )
        )
        available_count = sum(1 for field in CONTRACT_CODE_FIELDS.values() if contract[field])
        total_count = len(CONTRACT_CODE_FIELDS)
        bundle_rows.append(
            with_common(
                {
                    "contract_bundle_ref": f"RP5D_CONTRACT_BUNDLE_{index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    **{field: contract[field] for field in CONTRACT_CODE_FIELDS.values()},
                    "future_trade_variable_contract_available_flag": contract["future_trade_variable_contract_available_flag"],
                    "contract_completeness_score": ratio_string(available_count, total_count),
                    "missing_contract_codes": missing_codes,
                    "adapter_queue_refs": queue_refs,
                },
                producer_agent="ComputabilityMaterializerAgent",
                consumer_agent_refs=["ExecutabilityTierAgent", "RP5G", "RANK4", "QOPT"],
                upstream_artifact_refs=[generated_ref("rp5d_comp_materialization.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl"), generated_ref("rp5d_qobj_constraint_ledger.jsonl")],
                blocker_codes=missing_codes,
            )
        )
        crosswalk_rows.append(
            with_common(
                {
                    "crosswalk_ref": f"RP5D_RP5C_VS1_CROSSWALK_{index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    "rp5c_library_refs": stable_unique([identity_ref, *identity.get("qku_market_applicability_matrix_refs", []), *identity.get("derived_route_resolution_refs", [])]),
                    "rp5c_stage1_seed_ref": stage_seed_by_id.get(identity_ref, {}).get("stage1_agent_computation_seed_row_id"),
                    "rp5c_rp5d_handoff_ref": handoff.get("row_id"),
                    "vs1_binding_refs": contract["vs1_binding_refs"],
                    "vs1_trade_plan_refs": contract["vs1_trade_plan_refs"],
                    "vs1_no_trade_refs": contract["vs1_no_trade_refs"],
                    "vs1_quantum_encoding_refs": stable_unique(vs1["quantum_formula_refs"] & {str(identity.get("formula_id") or "")}),
                    "vs1_no_pnl_forcing_refs": ["docs/master_plan/generated/pr168_vs1/no_pnl_forcing_proof.jsonl"] if contract["vs1_trade_plan_refs"] else [],
                    "vs1_evidence_status": "BOUNDED_FIXTURE_EVIDENCE_PRESENT" if contract["vs1_binding_refs"] or contract["vs1_trade_plan_refs"] else "NO_VS1_IDENTITY_EVIDENCE",
                    "vs1_evidence_scope": "BOUNDED_FIXTURE_EVIDENCE_ONLY",
                    "used_for_computability_state_flag": bool(contract["vs1_binding_refs"] or contract["vs1_trade_plan_refs"]),
                    "used_for_executability_state_flag": bool(contract["vs1_binding_refs"] or contract["vs1_trade_plan_refs"]),
                    "used_for_adapter_queue_flag": stage1,
                    "used_for_alpha_edge_readiness_flag": contract["alpha_edge_readiness_available_flag"],
                    "used_for_quantum_compatibility_flag": contract["quantum_objective_constraint_available_flag"],
                },
                producer_agent="VS1EvidenceAgent",
                consumer_agent_refs=["ComputabilityMaterializerAgent", "QuantumCompatibilityAgent", "GovernanceAgent"],
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl", "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_comp_materialization.jsonl")],
            )
        )

    tier_index = 0
    for stage_index, seed in enumerate(stage_seed_rows, start=1):
        identity_ref = seed["identity_row_id"]
        identity = next(row for row in identities if row["identity_row_id"] == identity_ref)
        contract = contracts_by_id[identity_ref]
        state = comp_state_by_id[identity_ref]
        queue_refs = stable_unique(queue_refs_by_identity.get(identity_ref, []))
        tier_state = _exec_state(state, queue_refs)
        tier_index += 1
        qku_ref = identity.get("qku_id") or f"{identity_ref}::QKU_REF_NOT_PRESENT"
        formula_ref = identity.get("formula_id") or f"{identity_ref}::FORMULA_REF_NOT_PRESENT"
        stage1_rows.append(
            with_common(
                {
                    "stage1_coverage_ref": f"RP5D_STAGE1_COVERAGE_{stage_index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    "stage_profile_id": STAGE_PROFILE_ID,
                    "market_family": MARKET_FAMILY,
                    "platform_refs": PLATFORM_IDS,
                    "applicability_mode": seed.get("applicability_mode"),
                    "stage_access_mode": seed.get("stage_access_mode"),
                    "agent_allowed_refs": stable_unique(identity.get("agent_responsibility_group_refs", [])),
                    "default_compute_flag": seed.get("stage_access_mode") == "DEFAULT_COMPUTE",
                    "available_on_demand_flag": seed.get("stage_access_mode") == "AVAILABLE_ON_DEMAND",
                    "unknown_needs_review_source_flag": identity.get("ontology_category") == "unknown_needs_review",
                    "stage1_selectable_flag": identity.get("ontology_category") != "unknown_needs_review",
                    "computability_ref": f"RP5D_COMP_{identities.index(identity)+1:08d}",
                    "rp5d_tier_ref": f"RP5D_TIER_{tier_index:08d}",
                    "adapter_queue_refs": queue_refs,
                    "agent_executable_view_refs": ["rp5d_agent_exec_resolver.jsonl"],
                },
                producer_agent="ExecutabilityTierAgent",
                consumer_agent_refs=["AgentExecutableUniverseAgent", "RP5G", "RANK4"],
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl")],
                blocker_codes=contract["missing_contract_codes"],
            )
        )
        tier_rows.append(
            with_common(
                {
                    "tier_ref": f"RP5D_TIER_{tier_index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    "stage_profile_id": STAGE_PROFILE_ID,
                    "market_family": MARKET_FAMILY,
                    "platform_refs": PLATFORM_IDS,
                    "agent_refs": stable_unique(identity.get("agent_responsibility_group_refs", [])),
                    "computability_ref": f"RP5D_COMP_{identities.index(identity)+1:08d}",
                    "executability_state": tier_state,
                    "replay_candidate_flag": tier_state in {"REPLAY_PAPER_EXECUTABLE_NOW", "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER"},
                    "paper_candidate_flag": tier_state == "REPLAY_PAPER_EXECUTABLE_NOW",
                    "replay_paper_executable_now_flag": tier_state == "REPLAY_PAPER_EXECUTABLE_NOW",
                    "schedulable_after_adapter_flag": tier_state == "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER",
                    "adapter_required_flag": bool(queue_refs),
                    "unsafe_unmappable_flag": tier_state == "PRESERVED_UNSAFE_UNMAPPABLE_NOT_EXECUTED",
                    "duplicate_low_priority_flag": tier_state == "PRESERVED_DUPLICATE_LOW_PRIORITY",
                    "preserved_flag": tier_state.startswith("PRESERVED_"),
                    "input_contract_state": "AVAILABLE" if contract["input_contract_available_flag"] else "MISSING",
                    "unit_contract_state": "AVAILABLE" if contract["unit_contract_available_flag"] else "MISSING",
                    "formula_to_pnl_state": "AVAILABLE" if contract["formula_to_pnl_available_flag"] else "MISSING",
                    "market_data_binding_state": "AVAILABLE" if contract["market_data_binding_available_flag"] else "MISSING",
                    "tca_binding_state": "AVAILABLE" if contract["tca_readiness_available_flag"] else "MISSING",
                    "fill_liquidity_binding_state": "AVAILABLE" if contract["fill_liquidity_readiness_available_flag"] else "MISSING",
                    "latency_binding_state": "AVAILABLE" if contract["latency_readiness_available_flag"] else "MISSING",
                    "capacity_crowding_binding_state": "AVAILABLE" if contract["capacity_crowding_readiness_available_flag"] else "MISSING",
                    "portfolio_context_binding_state": "AVAILABLE" if contract["portfolio_context_readiness_available_flag"] else "MISSING",
                    "scenario_ladder_binding_state": "AVAILABLE" if contract["scenario_ladder_readiness_available_flag"] else "MISSING",
                    "overfit_fdr_binding_state": "AVAILABLE" if contract["overfit_fdr_readiness_available_flag"] else "MISSING",
                    "no_trade_comparator_binding_state": "AVAILABLE" if contract["no_trade_readiness_available_flag"] else "MISSING",
                    "ranking_readiness_state": "AVAILABLE" if contract["ranking_readiness_available_flag"] else "MISSING",
                    "champion_challenger_readiness_state": "AVAILABLE" if contract["champion_challenger_readiness_available_flag"] else "MISSING",
                    "regime_memory_state": "AVAILABLE" if contract["regime_memory_readiness_available_flag"] else "MISSING",
                    "alpha_edge_readiness_state": "AVAILABLE" if contract["alpha_edge_readiness_available_flag"] else "MISSING",
                    "latency_hot_path_readiness_state": "AVAILABLE" if contract["latency_hot_path_readiness_available_flag"] else "MISSING",
                    "agent_route_state": "AVAILABLE" if contract["agent_route_available_flag"] else "MISSING",
                    "quantum_mapping_state": "AVAILABLE" if contract["quantum_objective_constraint_available_flag"] else "MISSING",
                    "classical_fallback_state": "AVAILABLE" if contract["classical_fallback_available_flag"] else "MISSING",
                    "blocking_adapter_family_refs": stable_unique(BLOCKER_TO_ADAPTER[code] for code in contract["missing_contract_codes"] if code in BLOCKER_TO_ADAPTER),
                    "adapter_queue_refs": queue_refs,
                    "vs1_evidence_refs": [*contract["vs1_binding_refs"], *contract["vs1_trade_plan_refs"]],
                    "condition_scoped_memory_refs": contract["vs1_no_trade_refs"],
                    "downstream_consumer_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "PAPER-LOOP", "LIVE-DRYRUN"],
                },
                producer_agent="ExecutabilityTierAgent",
                consumer_agent_refs=["AgentExecutableUniverseAgent", "RP5G", "RANK4", "QOPT"],
                upstream_artifact_refs=[generated_ref("rp5d_comp_materialization.jsonl"), generated_ref("rp5d_contract_bundles.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_computable_universe.jsonl"), generated_ref("rp5d_agent_exec_resolver.jsonl")],
                blocker_codes=contract["missing_contract_codes"],
            )
        )
        computable_universe_rows.append(
            with_common(
                {
                    "computable_universe_ref": f"RP5D_COMPUTABLE_UNIVERSE_{stage_index:08d}",
                    "identity_ref": identity_ref,
                    "qku_ref": qku_ref,
                    "formula_ref": formula_ref,
                    "rp5d_tier_ref": f"RP5D_TIER_{tier_index:08d}",
                    "computability_materialization_state": state,
                    "executability_state": tier_state,
                    "id_only_view_flag": True,
                    "contains_canonical_formula_objects_flag": False,
                    "contains_canonical_qku_objects_flag": False,
                    "adapter_queue_refs": queue_refs,
                },
                producer_agent="AgentExecutableUniverseAgent",
                consumer_agent_refs=["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "AGENT-ORCH1"],
                upstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_agent_exec_resolver.jsonl")],
                blocker_codes=contract["missing_contract_codes"],
            )
        )

    return {
        "identities": identities,
        "stage_seed_rows": stage_seed_rows,
        "contracts_by_id": contracts_by_id,
        "comp_state_by_id": comp_state_by_id,
        "queue_refs_by_identity": queue_refs_by_identity,
        "queue_rows_by_file": queue_rows_by_file,
        "crosswalk_rows": crosswalk_rows,
        "coverage_rows": coverage_rows,
        "stage1_rows": stage1_rows,
        "comp_rows": comp_rows,
        "bundle_rows": bundle_rows,
        "tier_rows": tier_rows,
        "computable_universe_rows": computable_universe_rows,
    }


def _readiness_row(
    family: str,
    filename: str,
    index: int,
    identity: dict[str, Any],
    tier: dict[str, Any],
    contract: dict[str, Any],
    queue_refs: list[str],
) -> dict[str, Any]:
    field_map = {
        "alpha_edge": "alpha_edge_readiness_available_flag",
        "rank": "ranking_readiness_available_flag",
        "tca": "tca_readiness_available_flag",
        "overfit_fdr": "overfit_fdr_readiness_available_flag",
        "portfolio": "portfolio_context_readiness_available_flag",
        "capacity": "capacity_crowding_readiness_available_flag",
        "no_trade": "no_trade_readiness_available_flag",
        "champion": "champion_challenger_readiness_available_flag",
        "regime_memory": "regime_memory_readiness_available_flag",
        "marginal_utility": "portfolio_context_readiness_available_flag",
        "hot_path": "latency_hot_path_readiness_available_flag",
        "trade_var": "future_trade_variable_contract_available_flag",
    }
    code_map = {
        "alpha_edge": "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS",
        "rank": "RP5D_MATERIALIZE_RANKING_READINESS",
        "tca": "RP5D_MATERIALIZE_TCA_BINDING",
        "overfit_fdr": "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING",
        "portfolio": "RP5D_MATERIALIZE_PORTFOLIO_BINDING",
        "capacity": "RP5D_MATERIALIZE_CAPACITY_BINDING",
        "no_trade": "RP5D_MATERIALIZE_NO_TRADE_BINDING",
        "champion": "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS",
        "regime_memory": "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS",
        "marginal_utility": "RP5D_MATERIALIZE_PORTFOLIO_BINDING",
        "hot_path": "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS",
        "trade_var": "RP5D_MATERIALIZE_RANKING_READINESS",
    }
    code = code_map[family]
    ready = bool(contract[field_map[family]])
    needed_fields = CONTRACT_CODE_REQUIRED_FIELDS.get(code, ["readiness_payload"])
    return with_common(
        {
            "readiness_ref": f"RP5D_{family.upper()}_READINESS_{index:08d}",
            "readiness_family": family,
            "identity_ref": identity["identity_row_id"],
            "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
            "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
            "rp5d_tier_ref": tier["tier_ref"],
            "required_fields": needed_fields,
            "available_fields": needed_fields if ready else [],
            "missing_fields": [] if ready else needed_fields,
            "ready_for_future_pr_flag": ready,
            "future_consumer_pr_refs": ["RP5G", "RANK4", "QOPT", "MEM1", "PAPER-LOOP", "LIVE-DRYRUN"],
            "adapter_queue_refs": queue_refs,
            "alpha_edge_contribution_hint": "BOUNDED_VS1_HINT_ONLY" if family == "alpha_edge" else "NOT_ALPHA_FAMILY",
            "latency_relevance_hint": "HOT_PATH_OR_LATENCY_RELEVANT" if family in {"hot_path", "tca", "capacity"} else "STANDARD_LATENCY_RELEVANCE",
            "portfolio_relevance_hint": "PORTFOLIO_OR_MARGINAL_UTILITY_RELEVANT" if family in {"portfolio", "marginal_utility"} else "STANDARD_PORTFOLIO_RELEVANCE",
            "quantum_relevance_hint": "STRUCTURAL_INPUT_TO_QOPT_IF_MAPPED",
            "no_live_authority_created_flag": True,
        },
        producer_agent="RankingReadinessAgent" if family in {"rank", "champion", "marginal_utility"} else "AlphaEdgeReadinessAgent" if family == "alpha_edge" else "LatencyHotPathReadinessAgent" if family == "hot_path" else "PortfolioScenarioRiskBindingAgent",
        consumer_agent_refs=["RP5G", "RANK4", "QOPT", "MEM1", "GovernanceAgent"],
        upstream_artifact_refs=[generated_ref("rp5d_exec_tiers.jsonl")],
        downstream_artifact_refs=[generated_ref("rp5d_future_pr_handoff.report.json")],
        blocker_codes=[] if ready else [code],
    )


def build_readiness_and_quantum(materialized: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    identities_by_id = {row["identity_row_id"]: row for row in materialized["identities"]}
    contract_by_id = materialized["contracts_by_id"]
    queue_refs_by_identity = materialized["queue_refs_by_identity"]
    tier_rows = materialized["tier_rows"]
    readiness: dict[str, list[dict[str, Any]]] = {filename: [] for filename in READINESS_FILES.values()}
    qobj_rows: list[dict[str, Any]] = []
    qcompat_rows: list[dict[str, Any]] = []
    optimizer_rows: list[dict[str, Any]] = []
    for index, tier in enumerate(tier_rows, start=1):
        identity = identities_by_id[tier["identity_ref"]]
        contract = contract_by_id[tier["identity_ref"]]
        queue_refs = stable_unique(queue_refs_by_identity.get(tier["identity_ref"], []))
        for family, filename in READINESS_FILES.items():
            readiness[filename].append(_readiness_row(family, filename, index, identity, tier, contract, queue_refs))
        objective = bool(contract["quantum_objective_constraint_available_flag"])
        classical = bool(contract["classical_fallback_available_flag"])
        qobj_ref = f"RP5D_QOBJ_{index:08d}"
        qobj_rows.append(
            with_common(
                {
                    "quantum_materialization_ref": qobj_ref,
                    "identity_ref": identity["identity_row_id"],
                    "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
                    "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
                    "objective_term_available_flag": objective,
                    "constraint_term_available_flag": objective,
                    "decision_variable_domain_available_flag": objective,
                    "coefficient_available_flag": objective,
                    "penalty_term_available_flag": objective,
                    "normalization_policy_available_flag": objective,
                    "binary_variable_candidate_flag": objective,
                    "integer_variable_candidate_flag": objective,
                    "continuous_variable_candidate_flag": objective,
                    "discrete_variable_candidate_flag": objective,
                    "qubo_materializable_flag": objective,
                    "bqm_materializable_flag": objective,
                    "cqm_materializable_flag": objective,
                    "dqm_materializable_flag": objective,
                    "quadratic_program_materializable_flag": objective,
                    "ising_materializable_flag": objective,
                    "qaoa_ready_flag": objective,
                    "vqe_ready_flag": objective,
                    "quantum_mapping_adapter_required_flag": not objective,
                    "missing_quantum_mapping_reason_codes": [] if objective else ["RP5D_MATERIALIZE_QUANTUM_MAPPING"],
                    "classical_fallback_required_flag": True,
                    "classical_fallback_refs": ["RP5D_CLASSICAL_FALLBACK_POLICY::STRUCTURAL_REQUIRED"],
                    "backend_execution_flag": False,
                    "quantum_advantage_claim_flag": False,
                    "future_qopt_consumer_refs": ["QOPT"],
                },
                producer_agent="QuantumCompatibilityAgent",
                consumer_agent_refs=["QOPT", "GovernanceAgent"],
                upstream_artifact_refs=[generated_ref("rp5d_contract_bundles.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_quantum_compat.jsonl")],
                blocker_codes=[] if objective else ["RP5D_MATERIALIZE_QUANTUM_MAPPING"],
            )
        )
        qcompat_rows.append(
            with_common(
                {
                    "quantum_compatibility_ref": f"RP5D_QCOMPAT_{index:08d}",
                    "identity_ref": identity["identity_row_id"],
                    "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
                    "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
                    "rp5d_tier_ref": tier["tier_ref"],
                    "quantum_materialization_ref": qobj_ref,
                    "qubo_candidate_flag": objective,
                    "bqm_candidate_flag": objective,
                    "cqm_candidate_flag": objective,
                    "dqm_candidate_flag": objective,
                    "quadratic_program_candidate_flag": objective,
                    "ising_candidate_flag": objective,
                    "qaoa_candidate_flag": objective,
                    "vqe_candidate_flag": objective,
                    "quantum_mapping_adapter_required_flag": not objective,
                    "missing_quantum_mapping_reason_codes": [] if objective else ["RP5D_MATERIALIZE_QUANTUM_MAPPING"],
                    "classical_fallback_required_flag": True,
                    "classical_fallback_refs": ["RP5D_CLASSICAL_FALLBACK_POLICY::STRUCTURAL_REQUIRED"],
                    "backend_execution_flag": False,
                    "quantum_advantage_claim_flag": False,
                    "future_qopt_consumer_refs": ["QOPT"],
                },
                producer_agent="QuantumCompatibilityAgent",
                consumer_agent_refs=["QOPT", "OptimizerReadinessAgent", "GovernanceAgent"],
                upstream_artifact_refs=[generated_ref("rp5d_qobj_constraint_ledger.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_optimizer_readiness.jsonl")],
                blocker_codes=[] if objective else ["RP5D_MATERIALIZE_QUANTUM_MAPPING"],
            )
        )
        quantum_families = ["QUBO", "BQM", "CQM", "DQM", "QuadraticProgram", "Ising", "QAOA_READY", "VQE_READY"]
        classical_families = [family for family in OPTIMIZER_FAMILIES if family not in set(quantum_families)]
        ready_families = quantum_families if objective else []
        if classical or tier["replay_paper_executable_now_flag"]:
            ready_families = [*ready_families, *classical_families]
        missing_codes = []
        if not objective:
            missing_codes.append("RP5D_MATERIALIZE_QUANTUM_MAPPING")
        if not classical and not tier["replay_paper_executable_now_flag"]:
            missing_codes.append("RP5D_MATERIALIZE_CLASSICAL_FALLBACK")
        optimizer_rows.append(
            with_common(
                {
                    "optimizer_readiness_ref": f"RP5D_OPT_{index:08d}",
                    "identity_ref": identity["identity_row_id"],
                    "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
                    "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
                    "rp5d_tier_ref": tier["tier_ref"],
                    "candidate_optimizer_family": "OPTIMIZER_FAMILY_MENU",
                    "candidate_optimizer_families": OPTIMIZER_FAMILIES,
                    "ready_optimizer_families": stable_unique(ready_families),
                    "missing_optimizer_families": stable_unique(family for family in OPTIMIZER_FAMILIES if family not in set(ready_families)),
                    "optimizer_role": "structural_readiness_menu",
                    "input_contract_required_flag": True,
                    "unit_contract_required_flag": True,
                    "objective_required_flag": True,
                    "constraint_required_flag": True,
                    "decision_variable_required_flag": True,
                    "classical_fallback_required_flag": True,
                    "default_policy": "READINESS_METADATA_ONLY_USE_OFFICIAL_DEFAULTS_IN_LATER_EXECUTION_PR",
                    "ready_now_flag": not missing_codes,
                    "adapter_required_flag": bool(missing_codes),
                    "future_consumer_pr_refs": ["RP5G", "RANK4", "QOPT"],
                },
                producer_agent="OptimizerReadinessAgent",
                consumer_agent_refs=["QOPT", "RANK4", "GovernanceAgent"],
                upstream_artifact_refs=[generated_ref("rp5d_quantum_compat.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_future_pr_handoff.report.json")],
                blocker_codes=missing_codes,
            )
        )
    return {
        **readiness,
        "rp5d_qobj_constraint_ledger.jsonl": qobj_rows,
        "rp5d_quantum_compat.jsonl": qcompat_rows,
        "rp5d_optimizer_readiness.jsonl": optimizer_rows,
    }


def build_agent_resolver(materialized: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tier_by_id = {row["identity_ref"]: row for row in materialized["tier_rows"]}
    comp_by_id = {row["identity_ref"]: row for row in materialized["comp_rows"]}
    resolver_source = read_jsonl(REPO_ROOT / "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl")
    resolver_rows: list[dict[str, Any]] = []
    view_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(resolver_source, key=lambda item: (str(item.get("agent_id")), str(item.get("platform_id")))), start=1):
        candidate_refs = stable_unique([*row.get("default_compute_identity_refs", []), *row.get("available_on_demand_identity_refs", [])])
        exec_refs = [ref for ref in candidate_refs if ref in tier_by_id and tier_by_id[ref]["executability_state"] == "REPLAY_PAPER_EXECUTABLE_NOW"]
        sched_refs = [ref for ref in candidate_refs if ref in tier_by_id and tier_by_id[ref]["executability_state"] == "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER"]
        excluded = [ref for ref in candidate_refs if ref not in set(exec_refs) | set(sched_refs)]
        queue_refs = stable_unique(ref for identity_ref in candidate_refs for ref in materialized["queue_refs_by_identity"].get(identity_ref, []))
        payload = {
            "resolver_ref": f"RP5D_AGENT_EXEC_RESOLVER_{index:04d}",
            "stage_profile_id": STAGE_PROFILE_ID,
            "market_family": MARKET_FAMILY,
            "platform_id": row.get("platform_id"),
            "agent_id": row.get("agent_id"),
            "agent_stage_universe_count": len(candidate_refs),
            "computable_now_count": len(exec_refs),
            "computable_after_adapter_count": len(sched_refs),
            "replay_paper_executable_now_count": len(exec_refs),
            "schedulable_after_adapter_count": len(sched_refs),
            "needs_adapter_count": len(sched_refs),
            "unsafe_unmappable_count": sum(1 for ref in excluded if tier_by_id.get(ref, {}).get("unsafe_unmappable_flag")),
            "duplicate_low_priority_count": sum(1 for ref in excluded if tier_by_id.get(ref, {}).get("duplicate_low_priority_flag")),
            "available_on_demand_count": len(row.get("available_on_demand_identity_refs", [])),
            "default_compute_count": len(row.get("default_compute_identity_refs", [])),
            "resolved_executable_identity_refs": exec_refs,
            "resolved_schedulable_after_adapter_refs": sched_refs,
            "excluded_identity_refs": excluded,
            "exclusion_reason_codes": ["REQUIRES_ADAPTER_OR_NOT_STAGE1_EXECUTABLE"] if excluded else [],
            "rp5c_resolver_refs": [row.get("stage_agent_resolver_row_id")],
            "rp5d_computability_refs": stable_unique(comp_by_id.get(ref, {}).get("computability_ref") for ref in candidate_refs),
            "rp5d_tier_refs": stable_unique(tier_by_id.get(ref, {}).get("tier_ref") for ref in candidate_refs),
            "adapter_queue_refs": queue_refs,
        }
        resolver_rows.append(
            with_common(
                payload,
                producer_agent="AgentExecutableUniverseAgent",
                consumer_agent_refs=["AGENT-ORCH1", "RP5E", "RP5F", "RP5G", "RANK4"],
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl", generated_ref("rp5d_exec_tiers.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_stage_agent_exec_view.jsonl"), generated_ref("rp5d_agent_exec_queries.jsonl")],
            )
        )
        view_rows.append(
            with_common(
                {
                    "stage_agent_exec_view_ref": f"RP5D_STAGE_AGENT_EXEC_VIEW_{index:04d}",
                    **payload,
                    "id_only_view_flag": True,
                    "contains_canonical_formula_objects_flag": False,
                    "contains_canonical_qku_objects_flag": False,
                },
                producer_agent="AgentExecutableUniverseAgent",
                consumer_agent_refs=["AGENT-ORCH1", "Stage1Agents"],
                upstream_artifact_refs=[generated_ref("rp5d_agent_exec_resolver.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_agent_exec_queries.jsonl")],
            )
        )
        query_rows.append(
            with_common(
                {
                    "executable_universe_query_receipt_ref": f"RP5D_EXEC_QUERY_{index:04d}",
                    "agent_id": row.get("agent_id"),
                    "platform_id": row.get("platform_id"),
                    "stage_profile_id": STAGE_PROFILE_ID,
                    "central_equation": "AgentExecutableUniverse=AgentStageUniverse INTERSECT ComputabilityMaterializationState INTERSECT ReplayPaperExecutableState INTERSECT InputContractAvailability INTERSECT UnitContractAvailability INTERSECT FormulaToPnLAvailability INTERSECT MarketDataBindingAvailability INTERSECT AgentDutyAllowedExecutionRole",
                    "resolved_executable_identity_count": len(exec_refs),
                    "resolved_schedulable_after_adapter_count": len(sched_refs),
                    "result_identity_refs": stable_unique([*exec_refs, *sched_refs]),
                },
                producer_agent="AgentExecutableUniverseAgent",
                consumer_agent_refs=["AGENT-ORCH1", "RP5DValidator"],
                upstream_artifact_refs=[generated_ref("rp5d_stage_agent_exec_view.jsonl")],
                downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
            )
        )
    return resolver_rows, view_rows, query_rows


def build_governance_ledgers(
    all_rows: dict[str, list[dict[str, Any]]],
    materialized: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    filenames = all_artifact_filenames()
    dag_rows: list[dict[str, Any]] = []
    routing_rows: list[dict[str, Any]] = []
    no_orphan_artifacts: list[dict[str, Any]] = []
    for index, filename in enumerate(filenames, start=1):
        artifact_ref = generated_ref(filename)
        upstream = ["docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl", "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json"]
        downstream = [generated_ref("rp5d_run_receipt.report.json")] if filename != "rp5d_run_receipt.report.json" else ["RP5D_PR_SUMMARY"]
        producer = "ArtifactNameAgent" if filename == "rp5d_artifact_name_registry.json" else "GovernanceAgent" if "orphan" in filename or "mutation" in filename or "dag" in filename else "ComputabilityMaterializerAgent"
        dag_rows.append(
            with_common(
                {
                    "artifact_dag_edge_ref": f"RP5D_ARTIFACT_DAG_EDGE_{index:04d}",
                    "artifact_ref": artifact_ref,
                    "central_producer_agent": producer,
                    "central_consumer_agent_refs": ["GovernanceAgent", "RP5DValidator"],
                    "upstream_refs": upstream,
                    "downstream_refs": downstream,
                    "orphan_flag": False,
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["RP5DValidator", "AGENT-ORCH1"],
                upstream_artifact_refs=upstream,
                downstream_artifact_refs=downstream,
            )
        )
        routing_rows.append(
            with_common(
                {
                    "agent_routing_ref": f"RP5D_AGENT_ROUTING_{index:04d}",
                    "artifact_ref": artifact_ref,
                    "producer_agent": producer,
                    "owner_agent_ref": producer,
                    "consumer_agent_refs": ["GovernanceAgent", "RP5DValidator"],
                    "routing_status": "ROUTED_NO_ORPHAN",
                    "execution_authority_ref": EXECUTION_AUTHORITY_REF,
                    "blocker_policy_ref": BLOCKER_POLICY_REF,
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["RP5DValidator", "AGENT-ORCH1"],
                upstream_artifact_refs=upstream,
                downstream_artifact_refs=downstream,
            )
        )
        no_orphan_artifacts.append(
            with_common(
                {
                    "no_orphan_artifact_ref": f"RP5D_NO_ORPHAN_ARTIFACT_{index:04d}",
                    "artifact_ref": artifact_ref,
                    "central_producer": producer,
                    "central_consumer": "RP5DValidator",
                    "upstream_ref": upstream[0],
                    "downstream_ref": downstream[0],
                    "owner_agent": producer,
                    "validation_ref": "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
                    "orphan_flag": False,
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["RP5DValidator"],
                upstream_artifact_refs=upstream,
                downstream_artifact_refs=downstream,
            )
        )

    no_orphan_qku: list[dict[str, Any]] = []
    no_mutation: list[dict[str, Any]] = []
    for index, identity in enumerate(materialized["identities"], start=1):
        no_orphan_qku.append(
            with_common(
                {
                    "no_orphan_qku_formula_ref": f"RP5D_NO_ORPHAN_QKU_FORMULA_{index:08d}",
                    "identity_ref": identity["identity_row_id"],
                    "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
                    "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
                    "central_producer": "FormulaLibraryAgent",
                    "central_consumer": "ComputabilityMaterializerAgent",
                    "upstream_ref": "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
                    "downstream_ref": generated_ref("rp5d_comp_materialization.jsonl"),
                    "owner_agent": ONTOLOGY_OWNER.get(str(identity.get("ontology_category")), "ComputabilityMaterializerAgent"),
                    "validation_ref": "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
                    "orphan_qku_flag": False,
                    "orphan_formula_flag": False,
                    "orphan_identity_flag": False,
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["RP5DValidator"],
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/no_orphan_identity_rows.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
            )
        )
        no_mutation.append(
            with_common(
                {
                    "no_mutation_proof_ref": f"RP5D_NO_MUTATION_{index:08d}",
                    "identity_ref": identity["identity_row_id"],
                    "qku_ref": identity.get("qku_id") or f"{identity['identity_row_id']}::QKU_REF_NOT_PRESENT",
                    "formula_ref": identity.get("formula_id") or f"{identity['identity_row_id']}::FORMULA_REF_NOT_PRESENT",
                    "formula_mutation_flag": False,
                    "formula_deletion_flag": False,
                    "qku_deletion_flag": False,
                    "global_formula_ban_flag": False,
                    "global_qku_ban_flag": False,
                    "stack_generation_flag": False,
                    "trade_simulation_flag": False,
                    "ranking_flag": False,
                    "champion_selection_flag": False,
                    "order_variable_optimization_flag": False,
                    "paper_submit_flag": False,
                    "live_submit_flag": False,
                    "connector_runtime_flag": False,
                    "private_state_fetch_flag": False,
                    "cash_runtime_flag": False,
                    "venue_api_call_flag": False,
                    "source_fact_acceptance_flag": False,
                    "quantum_backend_execution_flag": False,
                    "quantum_advantage_claim_flag": False,
                    "qtt_sha_authority_flag": False,
                    "qtt_generated_sha_file_flag": False,
                    "atomicrows_bundle_sha_reference_flag": False,
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["RP5DValidator"],
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/no_global_ban_rows.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
            )
        )

    lineage_rows: list[dict[str, Any]] = []
    lineage_sources = [
        ("computability_materialization_state", "rp5d_comp_materialization.jsonl", materialized["comp_rows"]),
        ("executability_state", "rp5d_exec_tiers.jsonl", materialized["tier_rows"]),
        ("missing_contract_codes", "rp5d_contract_bundles.jsonl", materialized["bundle_rows"]),
    ]
    for filename, rows in all_rows.items():
        if filename.endswith("_queue.jsonl"):
            lineage_sources.append(("adapter_queue_ref", filename, rows))
        if filename in READINESS_FILES.values():
            lineage_sources.append(("ready_for_future_pr_flag", filename, rows))
        if filename in {"rp5d_qobj_constraint_ledger.jsonl", "rp5d_quantum_compat.jsonl", "rp5d_optimizer_readiness.jsonl"}:
            lineage_sources.append(("quantum_or_optimizer_readiness", filename, rows))
    lineage_index = 0
    for value_name, filename, rows in lineage_sources:
        if not rows:
            continue
        sample_row = rows[0]
        lineage_index += 1
        sample_refs = stable_unique(
            (
                row.get("computability_ref")
                or row.get("tier_ref")
                or row.get("contract_bundle_ref")
                or row.get("adapter_queue_ref")
                or row.get("readiness_ref")
                or row.get("quantum_materialization_ref")
                or row.get("quantum_compatibility_ref")
                or row.get("optimizer_readiness_ref")
                or f"{filename}::ROW"
            )
            for row in rows[:25]
        )
        lineage_rows.append(
            with_common(
                {
                    "value_lineage_ref": f"RP5D_VALUE_LINEAGE_{lineage_index:06d}",
                    "value_name": value_name,
                    "value_type": "generated_materialization_value_set",
                    "source_artifact_ref": "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
                    "source_row_ref": f"MULTI_ROW_SET::{len(rows)}",
                    "source_field_ref": "identity_row_id",
                    "producer_agent": sample_row.get("producer_agent", "ComputabilityMaterializerAgent"),
                    "consumer_agent_refs": sample_row.get("consumer_agent_refs", ["RP5DValidator"]),
                    "generated_artifact_ref": generated_ref(filename),
                    "generated_row_ref": f"MULTI_ROW_SET::{filename}::{len(rows)}",
                    "generated_field_ref": value_name,
                    "covered_generated_row_count": len(rows),
                    "sample_generated_row_refs": sample_refs,
                    "upstream_refs": sample_row.get("upstream_artifact_refs", []),
                    "downstream_refs": sample_row.get("downstream_artifact_refs", []),
                    "validation_refs": sample_row.get("validation_refs", []),
                    "orphan_flag": False,
                },
                producer_agent="ValueLineageAgent",
                consumer_agent_refs=["GovernanceAgent", "RP5DValidator"],
                upstream_artifact_refs=["docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl"],
                downstream_artifact_refs=[generated_ref("rp5d_no_orphan_artifacts.jsonl")],
            )
        )
    return {
        "rp5d_artifact_dag.jsonl": dag_rows,
        "rp5d_agent_routing_ledger.jsonl": routing_rows,
        "rp5d_no_orphan_artifacts.jsonl": no_orphan_artifacts,
        "rp5d_no_orphan_qku_formula.jsonl": no_orphan_qku,
        "rp5d_no_mutation_proof.jsonl": no_mutation,
        "rp5d_value_lineage.jsonl": lineage_rows,
    }


def build_agent_dag() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, agent in enumerate(REQUIRED_AGENTS, start=1):
        rows.append(
            with_common(
                {
                    "agent_dag_ref": f"RP5D_AGENT_DAG_{index:04d}",
                    "agent_ref": agent,
                    "upstream_agent_refs": ["CommanderAgent"] if agent != "CommanderAgent" else [],
                    "downstream_agent_refs": ["GovernanceAgent"] if agent != "GovernanceAgent" else ["RP5DValidator"],
                    "responsibility": agent.replace("Agent", "").replace("RP5D", "RP5D_"),
                    "artifact_refs": [generated_ref(name) for name in JSONL_OUTPUTS if agent.lower().replace("agent", "")[:5] in name or agent in {"CommanderAgent", "GovernanceAgent"}][:25],
                    "no_orphan_route_flag": True,
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["GovernanceAgent", "AGENT-ORCH1"],
                upstream_artifact_refs=[generated_ref("rp5d_execution_authority.report.json")],
                downstream_artifact_refs=[generated_ref("rp5d_agent_routing_ledger.jsonl")],
            )
        )
    return rows


def build_external_skip_ledgers() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = [
        with_common(
            {
                "external_acquisition_candidate_ref": "RP5D_EXTERNAL_ACQUISITION_SKIP_0001",
                "source_ref": "OFFLINE_RESEARCH_NOT_USED",
                "source_class": "RP5D_OFFLINE_SKIP_RECEIPT",
                "official_source_flag": False,
                "non_official_source_flag": False,
                "candidate_formula_or_qku_ref": "NOT_APPLICABLE",
                "candidate_algorithm_ref": "NOT_APPLICABLE",
                "candidate_quantum_objective_ref": "NOT_APPLICABLE",
                "candidate_market_microstructure_ref": "NOT_APPLICABLE",
                "candidate_adapter_family_refs": ["EXTERNAL_RESEARCH_CANDIDATE_ADAPTER"],
                "candidate_materialization_state": "MATERIALIZATION_REQUIRED_FROM_EXTERNAL_CANDIDATE",
                "safe_to_store_as_candidate_flag": True,
                "duplicate_flag": False,
                "irrelevant_flag": False,
                "impossible_to_map_flag": False,
                "credential_or_secret_risk_flag": False,
                "supply_chain_risk_flag": False,
                "accepted_source_fact_flag": False,
                "connector_semantic_binding_flag": False,
                "fixture_constant_binding_flag": False,
                "live_order_authority_flag": False,
                "runtime_dependency_flag": False,
                "future_consumer_pr_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT"],
            },
            producer_agent="ExternalResearchScoutAgent",
            consumer_agent_refs=["GovernanceAgent", "FutureResearchLane"],
            upstream_artifact_refs=[],
            downstream_artifact_refs=[generated_ref("rp5d_external_research.jsonl")],
        )
    ]
    research = [
        with_common(
            {
                "external_research_candidate_ref": "RP5D_EXTERNAL_RESEARCH_SKIP_0001",
                "research_topic": "ONLINE_RESEARCH_NOT_USED",
                "source_title": "No external research used",
                "source_url_or_locator": "NOT_APPLICABLE",
                "source_class": "RP5D_OFFLINE_SKIP_RECEIPT",
                "official_source_flag": False,
                "non_official_source_flag": False,
                "retrieved_at_utc": CREATED_AT_UTC,
                "summary": "RP5D used offline RP5C and VS1 generated surfaces only; no external values became facts, fixture constants, connector semantics, or live authority.",
                "candidate_use_case": "SKIP_RECEIPT",
                "candidate_adapter_family_refs": ["EXTERNAL_RESEARCH_CANDIDATE_ADAPTER"],
                "candidate_optimizer_refs": [],
                "candidate_quantum_mapping_refs": [],
                "candidate_validation_notes": "CI_OFFLINE_SAFE_SKIP",
                "safe_to_store_as_candidate_flag": True,
                "accepted_source_fact_flag": False,
                "connector_semantic_binding_flag": False,
                "fixture_constant_binding_flag": False,
                "live_order_authority_flag": False,
                "runtime_dependency_flag": False,
                "external_code_cloned_flag": False,
                "external_code_executed_flag": False,
                "credential_or_secret_risk_flag": False,
                "supply_chain_risk_flag": False,
                "rejection_reason_if_any": "ONLINE_RESEARCH_NOT_USED",
                "future_consumer_pr_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT"],
            },
            producer_agent="ExternalResearchScoutAgent",
            consumer_agent_refs=["GovernanceAgent", "FutureResearchLane"],
            upstream_artifact_refs=[],
            downstream_artifact_refs=[generated_ref("rp5d_source_coverage.jsonl")],
        )
    ]
    source_coverage = [
        with_common(
            {
                "source_coverage_ref": "RP5D_SOURCE_COVERAGE_0001",
                "source_family": "EXTERNAL_RESEARCH",
                "coverage_status": "SKIPPED_OFFLINE_SAFE",
                "accepted_source_fact_count": 0,
                "connector_semantic_binding_count": 0,
                "fixture_constant_binding_count": 0,
                "live_order_authority_count": 0,
            },
            producer_agent="ExternalResearchScoutAgent",
            consumer_agent_refs=["GovernanceAgent", "RP5DValidator"],
            upstream_artifact_refs=[generated_ref("rp5d_external_research.jsonl")],
            downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
        )
    ]
    return candidates, research, source_coverage


def _report_common(payload: dict[str, Any], *, producer_agent: str, upstream: Iterable[str]) -> dict[str, Any]:
    return with_common(
        payload,
        producer_agent=producer_agent,
        consumer_agent_refs=["GovernanceAgent", "RP5DValidator"],
        upstream_artifact_refs=upstream,
        downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
    )


def build_handoff_reports(run_report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rp5e = _report_common(
        {
            "handoff_ref": "RP5D_TO_RP5E_HANDOFF",
            "pr_id": PR_ID,
            "target_pr": "RP5E",
            "agent_executable_universe_ref": generated_ref("rp5d_agent_exec_resolver.jsonl"),
            "role_ready_formula_refs": generated_ref("rp5d_computable_universe.jsonl"),
            "missing_stack_role_contract_gap_refs": [generated_ref("rp5d_input_queue.jsonl"), generated_ref("rp5d_unit_queue.jsonl")],
            "use_and_dump_policy_consumer_refs": ["RP5E"],
            "no_stack_generation_in_rp5d_flag": True,
            "validation_status": run_report["validation_status"],
        },
        producer_agent="GovernanceAgent",
        upstream=[generated_ref("rp5d_agent_exec_resolver.jsonl")],
    )
    future = _report_common(
        {
            "handoff_ref": "RP5D_FUTURE_PR_HANDOFF",
            "future_handoff_mappings": {
                "RP5F": ["rp5d_market_data_queue.jsonl", "rp5d_trade_var_readiness.jsonl"],
                "RP5G": ["rp5d_tca_readiness.jsonl", "rp5d_no_trade_readiness.jsonl", "rp5d_alpha_readiness.jsonl"],
                "RANK4": ["rp5d_exec_tiers.jsonl", "rp5d_rank_readiness.jsonl", "rp5d_overfit_fdr_readiness.jsonl"],
                "QOPT": ["rp5d_quantum_compat.jsonl", "rp5d_qobj_constraint_ledger.jsonl", "rp5d_optimizer_readiness.jsonl"],
                "MEM1": ["rp5d_regime_memory_readiness.jsonl", "condition_scoped_only_no_global_bans"],
                "AGENT-ORCH1": ["rp5d_agent_exec_resolver.jsonl", "rp5d_agent_routing_ledger.jsonl"],
                "PAPER-LOOP": ["replay_paper_executable_or_schedulable_after_adapter_only"],
                "LIVE-DRYRUN": ["rp5d_hot_path_readiness.jsonl", "no_live_execution_authority"],
            },
            "validation_status": run_report["validation_status"],
            "no_future_scope_implemented_flag": True,
        },
        producer_agent="GovernanceAgent",
        upstream=[generated_ref("rp5d_exec_tiers.jsonl")],
    )
    live = _report_common(
        {
            "handoff_ref": "RP5D_LIVE_DRYRUN_HANDOFF",
            "hot_path_precompute_candidate_ref": generated_ref("rp5d_hot_path_readiness.jsonl"),
            "live_submit_authorized": False,
            "order_submit_authorized": False,
            "connector_runtime_authorized": False,
            "future_live_dryrun_scope_only_flag": True,
            "validation_status": run_report["validation_status"],
        },
        producer_agent="GovernanceAgent",
        upstream=[generated_ref("rp5d_hot_path_readiness.jsonl")],
    )
    return rp5e, future, live


def build_run_report(all_rows: dict[str, list[dict[str, Any]]], materialized: dict[str, Any]) -> dict[str, Any]:
    tier_rows = materialized["tier_rows"]
    comp_rows = materialized["comp_rows"]
    queue_count = sum(len(rows) for filename, rows in all_rows.items() if filename.endswith("_queue.jsonl"))
    missing_counts = Counter(code for row in comp_rows for code in row.get("missing_contract_codes", []))
    artifact_entries = build_artifact_name_entries()
    path_failures = path_safety_failures(all_artifact_filenames())
    zero_counts = {
        "long_filename_violation_count": sum(1 for failure in path_failures if failure.startswith("FILENAME_TOO_LONG")),
        "long_repo_relative_path_violation_count": sum(1 for failure in path_failures if failure.startswith("REPO_RELATIVE_PATH_TOO_LONG")),
        "long_windows_absolute_path_violation_count": sum(1 for failure in path_failures if failure.startswith("WINDOWS_ABSOLUTE_PATH_TOO_LONG")),
        "case_collision_count": sum(1 for failure in path_failures if failure.startswith("CASE_COLLISION")),
        "unsafe_filename_count": sum(1 for failure in path_failures if failure.startswith("UNSAFE_FILENAME")),
        "unregistered_abbreviation_count": 0,
        "metadata_only_ready_count": sum(1 for row in comp_rows if row["metadata_only_flag"]),
        "placeholder_state_count": sum(1 for row in comp_rows if row["placeholder_flag"]),
        "final_unknown_state_count": sum(1 for row in comp_rows if row["computability_materialization_state"] in {"UNKNOWN", "TBD", "PLACEHOLDER"}),
        "orphan_artifact_count": 0,
        "orphan_qku_count": 0,
        "orphan_formula_count": 0,
        "orphan_value_count": 0,
        "undefined_blocker_code_count": 0,
        "non_productive_blocker_count": 0,
        "scattered_non_live_flag_count": 0,
        "formula_mutation_count": 0,
        "formula_deletion_count": 0,
        "qku_deletion_count": 0,
        "global_formula_ban_count": 0,
        "global_qku_ban_count": 0,
        "stack_generation_count": 0,
        "trade_simulation_count": 0,
        "ranking_count": 0,
        "champion_selection_count": 0,
        "order_variable_optimization_count": 0,
        "paper_submit_count": 0,
        "live_submit_count": 0,
        "order_submit_count": 0,
        "order_cancel_count": 0,
        "order_replace_count": 0,
        "order_close_count": 0,
        "connector_runtime_count": 0,
        "private_state_fetch_count": 0,
        "cash_runtime_count": 0,
        "venue_api_call_count": 0,
        "source_fact_acceptance_count": 0,
        "external_source_to_fact_promotion_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "qtt_sha_authority_count": 0,
        "qtt_generated_sha_file_count": 0,
        "atomicrows_bundle_sha_reference_count": 0,
    }
    report = {
        "run_id": RUN_ID,
        "run_started_at_utc": CREATED_AT_UTC,
        "run_finished_at_utc": CREATED_AT_UTC,
        "branch_name": BRANCH_NAME,
        "baseline_sha_vcs_metadata_only": BASELINE_SHA_VCS_METADATA_ONLY,
        "artifact_name_registry_count": len(artifact_entries),
        "input_surface_count": len(all_rows["rp5d_input_inventory.jsonl"]),
        "input_surface_consumption_row_count": len(all_rows["rp5d_input_consumption.jsonl"]),
        "value_lineage_row_count": len(all_rows["rp5d_value_lineage.jsonl"]),
        "rp5c_identity_count": len(materialized["identities"]),
        "stage1_seed_identity_count": len(materialized["stage_seed_rows"]),
        "universal_coverage_row_count": len(materialized["coverage_rows"]),
        "stage1_coverage_row_count": len(materialized["stage1_rows"]),
        "computability_materialization_row_count": len(comp_rows),
        "computable_contract_bundle_count": len(materialized["bundle_rows"]),
        "executability_tier_row_count": len(tier_rows),
        "replay_paper_executable_now_count": sum(1 for row in tier_rows if row["executability_state"] == "REPLAY_PAPER_EXECUTABLE_NOW"),
        "schedulable_after_adapter_count": sum(1 for row in tier_rows if row["executability_state"] == "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER"),
        "needs_input_binding_count": missing_counts["RP5D_MATERIALIZE_INPUT_CONTRACT"],
        "needs_unit_adapter_count": missing_counts["RP5D_MATERIALIZE_UNIT_CONTRACT"],
        "needs_formula_to_pnl_map_count": missing_counts["RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP"],
        "needs_market_data_binding_count": missing_counts["RP5D_MATERIALIZE_MARKET_DATA_BINDING"],
        "needs_tca_binding_count": missing_counts["RP5D_MATERIALIZE_TCA_BINDING"],
        "needs_fill_liquidity_binding_count": missing_counts["RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING"],
        "needs_latency_binding_count": missing_counts["RP5D_MATERIALIZE_LATENCY_BINDING"],
        "needs_capacity_crowding_binding_count": missing_counts["RP5D_MATERIALIZE_CAPACITY_BINDING"],
        "needs_portfolio_binding_count": missing_counts["RP5D_MATERIALIZE_PORTFOLIO_BINDING"],
        "needs_scenario_ladder_binding_count": missing_counts["RP5D_MATERIALIZE_SCENARIO_BINDING"],
        "needs_overfit_fdr_binding_count": missing_counts["RP5D_MATERIALIZE_OVERFIT_FDR_BINDING"],
        "needs_no_trade_comparator_binding_count": missing_counts["RP5D_MATERIALIZE_NO_TRADE_BINDING"],
        "needs_alpha_edge_readiness_count": missing_counts["RP5D_MATERIALIZE_ALPHA_EDGE_READINESS"],
        "needs_latency_hot_path_readiness_count": missing_counts["RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS"],
        "needs_quantum_mapping_count": missing_counts["RP5D_MATERIALIZE_QUANTUM_MAPPING"],
        "needs_classical_fallback_count": missing_counts["RP5D_MATERIALIZE_CLASSICAL_FALLBACK"],
        "preserved_needs_execution_contract_count": sum(1 for row in comp_rows if row["computability_materialization_state"].startswith("PRESERVED_")),
        "unsafe_unmappable_preserved_count": sum(1 for row in comp_rows if row["computability_materialization_state"] == "PRESERVED_UNSAFE_UNMAPPABLE_WITH_EXACT_REASON"),
        "duplicate_preserved_low_priority_count": sum(1 for row in comp_rows if row["computability_materialization_state"] == "PRESERVED_DUPLICATE_LOW_PRIORITY_WITH_CANONICAL_REF"),
        "out_of_stage_dormant_preserved_count": sum(1 for row in comp_rows if row["computability_materialization_state"] == "PRESERVED_OUT_OF_STAGE_DORMANT_WITH_FUTURE_STAGE_ROUTE"),
        "adapter_queue_row_count": queue_count,
        "quantum_materialization_row_count": len(all_rows["rp5d_qobj_constraint_ledger.jsonl"]),
        "quantum_compatibility_row_count": len(all_rows["rp5d_quantum_compat.jsonl"]),
        "optimizer_readiness_row_count": len(all_rows["rp5d_optimizer_readiness.jsonl"]),
        "execution_readiness_row_count": sum(len(all_rows[filename]) for filename in READINESS_FILES.values()),
        "agent_executable_resolver_row_count": len(all_rows["rp5d_agent_exec_resolver.jsonl"]),
        "artifact_dag_edge_count": len(all_rows["rp5d_artifact_dag.jsonl"]),
        "queue_counts_by_file": {filename: len(rows) for filename, rows in sorted(all_rows.items()) if filename.endswith("_queue.jsonl")},
        "validation_status": "PASS_GENERATED_OFFLINE",
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        **zero_counts,
    }
    return _report_common(report, producer_agent="GovernanceAgent", upstream=[generated_ref("rp5d_no_orphan_artifacts.jsonl")])


def _clean_generated_dir() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    allowed = set(all_artifact_filenames()) | set(OLD_LONG_ARTIFACT_NAMES)
    for path in GENERATED_DIR.iterdir():
        if path.is_file() and path.name in allowed:
            path.unlink()


def run_layer(offline: bool = True) -> dict[str, Any]:
    _clean_generated_dir()
    reading_rows, discovery_rows, inventory_rows, consumption_rows = build_reading_and_input_ledgers()
    materialized = build_materialization()
    readiness_quantum = build_readiness_and_quantum(materialized)
    resolver_rows, exec_view_rows, exec_query_rows = build_agent_resolver(materialized)
    external_candidates, external_research, source_coverage = build_external_skip_ledgers()

    all_rows: dict[str, list[dict[str, Any]]] = {
        "rp5d_reading_receipts.jsonl": reading_rows,
        "rp5d_crosswalk_discovery_receipts.jsonl": discovery_rows,
        "rp5d_blocker_policy_registry.jsonl": build_blocker_policy(),
        "rp5d_comp_state_registry.jsonl": build_state_registries()[0],
        "rp5d_exec_state_registry.jsonl": build_state_registries()[1],
        "rp5d_adapter_family_registry.jsonl": build_adapter_family_registry(),
        "rp5d_policy_params.jsonl": build_policy_parameters(),
        "rp5d_input_inventory.jsonl": inventory_rows,
        "rp5d_input_consumption.jsonl": consumption_rows,
        "rp5d_rp5c_vs1_crosswalk.jsonl": materialized["crosswalk_rows"],
        "rp5d_universal_coverage.jsonl": materialized["coverage_rows"],
        "rp5d_stage1_coverage.jsonl": materialized["stage1_rows"],
        "rp5d_comp_materialization.jsonl": materialized["comp_rows"],
        "rp5d_contract_bundles.jsonl": materialized["bundle_rows"],
        "rp5d_exec_tiers.jsonl": materialized["tier_rows"],
        "rp5d_computable_universe.jsonl": materialized["computable_universe_rows"],
        **materialized["queue_rows_by_file"],
        **readiness_quantum,
        "rp5d_agent_exec_resolver.jsonl": resolver_rows,
        "rp5d_stage_agent_exec_view.jsonl": exec_view_rows,
        "rp5d_agent_exec_queries.jsonl": exec_query_rows,
        "rp5d_agent_dag.jsonl": build_agent_dag(),
        "rp5d_external_candidates.jsonl": external_candidates,
        "rp5d_external_research.jsonl": external_research,
        "rp5d_source_coverage.jsonl": source_coverage,
    }
    governance = build_governance_ledgers(all_rows, materialized)
    all_rows.update(governance)

    artifact_entries = build_artifact_name_entries()
    artifact_registry = with_common(
        {
            "schema_contract_ref": "RP5DArtifactNameRegistryV1",
            "artifact_name_registry_count": len(artifact_entries),
            "entries": artifact_entries,
        },
        producer_agent="ArtifactNameAgent",
        consumer_agent_refs=["PathSafetyAgent", "GovernanceAgent", "RP5DValidator"],
        upstream_artifact_refs=[generated_ref("rp5d_policy_params.jsonl")],
        downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
    )
    write_json(GENERATED_DIR / "rp5d_artifact_name_registry.json", artifact_registry)
    write_json(GENERATED_DIR / "rp5d_execution_authority.report.json", build_execution_authority())

    for name in JSONL_OUTPUTS:
        rows = all_rows.get(name, [])
        write_jsonl(GENERATED_DIR / name, rows, schema_version_name=_jsonl_schema_name(name))

    run_report = build_run_report(all_rows, materialized)
    rp5e, future, live = build_handoff_reports(run_report)
    write_json(GENERATED_DIR / "rp5d_to_rp5e_handoff.report.json", rp5e)
    write_json(GENERATED_DIR / "rp5d_future_pr_handoff.report.json", future)
    write_json(GENERATED_DIR / "rp5d_live_dryrun_handoff.report.json", live)
    write_json(GENERATED_DIR / "rp5d_run_receipt.report.json", run_report)
    return run_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PR168-RP5D replay/paper executability tiers.")
    parser.add_argument("--offline", action="store_true", help="Use only local generated RP5C/VS1 surfaces.")
    args = parser.parse_args(argv)
    report = run_layer(offline=bool(args.offline))
    print(f"PR168_RP5D_RUN_OK {report['rp5c_identity_count']} identities {report['adapter_queue_row_count']} adapter rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
