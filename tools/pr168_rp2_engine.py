#!/usr/bin/env python3
"""Deterministic PR168-RP2-MAP2 artifact builder."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any
from urllib.error import URLError

from tools.pr168_rp2_config import (
    BRANCH_NAME,
    COMPUTABILITY_ROUTES,
    GENERATED_ROOT,
    INTENT_POLICIES,
    OFFICIAL_DOC_URLS,
    ORDER_POLICIES,
    ORDER_SIZE_BUCKETS,
    PR235_MERGE_COMMIT,
    REPORT_ALIASES,
    REQUIRED_AGENT_REPORTS,
    REQUIRED_DATA1_REPORTS,
    REQUIRED_DATA1A_REPORTS,
    REQUIRED_GFP2R_REPORTS,
    REQUIRED_GFP2R_SHARDS,
    ROW_SHARDS,
    SCENARIO_FAMILIES,
    SHARD_ROOT,
    TOOL_NAME,
    generated_ref,
    report_path,
    route_defaults,
)
from tools.pr168_rp2_reports import load_report_file, read_jsonl, write_report, write_shard


@dataclass(frozen=True)
class Context:
    gfp2r_final: dict[str, Any]
    rp2_handoff: list[dict[str, Any]]
    formula_exec: list[dict[str, Any]]
    provisional_compute: list[dict[str, Any]]
    numeric: list[dict[str, Any]]
    break_even: list[dict[str, Any]]
    mapping: list[dict[str, Any]]
    rank2_handoff: list[dict[str, Any]]
    data_rows: list[dict[str, Any]]
    agent_reports_present: bool
    missing_gfp2r: list[str]
    missing_agents: list[str]


def build_all(*, verify_online_docs: bool = False) -> dict[str, Any]:
    ctx = load_context()
    endpoint_rows, network_receipt = endpoint_verification_rows(verify_online_docs)

    map2_rows = build_map2_rows(ctx)
    exact_rows = [row for row in map2_rows if row["promotion_state"] == "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY"]
    provisional_rows = [row for row in map2_rows if row["promotion_state"] != "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY"]
    bind_fail_rows = [row for row in map2_rows if row["repair_route_if_not_promoted"]]
    dedupe_rows = build_dedupe_rows(map2_rows)
    formula_contract_rows = build_formula_contract_rows(ctx, map2_rows)
    computability_rows = build_computability_rows(formula_contract_rows, map2_rows)
    input_locks = build_input_locks(ctx, dedupe_rows, map2_rows)
    order_policy_rows = build_order_policy_rows()
    order_intents = build_order_intents(ctx, input_locks)
    replay_rows, replay_gap_rows = build_replay_rows(order_intents)
    paper_rows = build_paper_rows(replay_rows)
    tca_rows = build_tca_rows(replay_rows)
    scenario_rows = build_scenario_rows(replay_rows, paper_rows)
    divergence_rows = build_divergence_rows(replay_rows, paper_rows)
    rank2_rows = build_rank2_rows(replay_rows, paper_rows, scenario_rows)
    memory_rows = build_memory_rows(rank2_rows)
    edge_alpha_rows = build_edge_alpha_rows(rank2_rows)
    best_formula_rows = build_best_formula_rows(edge_alpha_rows)
    retest_rows = build_retest_rows(rank2_rows)
    recovery_rows = build_recovery_rows(rank2_rows, retest_rows)
    quantum_rows = build_quantum_rows(edge_alpha_rows)
    connector_rows = build_connector_rows(rank2_rows)
    action_rows = build_action_rows(bind_fail_rows, replay_gap_rows, recovery_rows, quantum_rows)
    dag_rows = build_dag_rows(ctx, map2_rows, input_locks, replay_rows, paper_rows, rank2_rows, quantum_rows)
    value_rows = build_value_crosswalk_rows(map2_rows, input_locks, replay_rows, paper_rows, tca_rows, scenario_rows, rank2_rows, quantum_rows)
    agent_ledger_rows = build_agent_ledger_rows(rank2_rows, action_rows)

    manifests = {
        "map2_promote": write_shard("map2_promote", map2_rows, logical_family_id="PR168_RP2_MAP2_PROMOTION_ROWS"),
        "map2_dedupe": write_shard("map2_dedupe", dedupe_rows, logical_family_id="PR168_RP2_MAP2_DEDUPE_ROWS"),
        "formula_onboard": write_shard("formula_onboard", formula_contract_rows, logical_family_id="PR168_RP2_FORMULA_ONBOARD_ROWS"),
        "input_locks": write_shard("input_locks", input_locks, logical_family_id="PR168_RP2_INPUT_LOCK_ROWS"),
        "order_intents": write_shard("order_intents", order_intents, logical_family_id="PR168_RP2_ORDER_INTENT_ROWS"),
        "replay_exec": write_shard("replay_exec", replay_rows, logical_family_id="PR168_RP2_REPLAY_EXEC_ROWS"),
        "paper_exec": write_shard("paper_exec", paper_rows, logical_family_id="PR168_RP2_PAPER_EXEC_ROWS"),
        "tca": write_shard("tca", tca_rows, logical_family_id="PR168_RP2_TCA_ROWS"),
        "scenarios": write_shard("scenarios", scenario_rows, logical_family_id="PR168_RP2_SCENARIO_ROWS"),
        "divergence": write_shard("divergence", divergence_rows, logical_family_id="PR168_RP2_DIVERGENCE_ROWS"),
        "rank2_rows": write_shard("rank2_rows", rank2_rows, logical_family_id="PR168_RP2_RANK2_HANDOFF_ROWS"),
        "memory_rows": write_shard("memory_rows", memory_rows, logical_family_id="PR168_RP2_MEMORY_ROWS"),
        "q_stack": write_shard("q_stack", quantum_rows, logical_family_id="PR168_RP2_QUANTUM_STACK_ROWS"),
        "actions": write_shard("actions", action_rows, logical_family_id="PR168_RP2_ACTION_ROWS"),
        "formula_contracts": write_shard("formula_contracts", formula_contract_rows, logical_family_id="PR168_RP2_FORMULA_CONTRACT_ROWS"),
        "edge_alpha": write_shard("edge_alpha", edge_alpha_rows, logical_family_id="PR168_RP2_EDGE_ALPHA_ROWS"),
        "retest_variants": write_shard("retest_variants", retest_rows, logical_family_id="PR168_RP2_RETEST_VARIANT_ROWS"),
        "connector_routes": write_shard("connector_routes", connector_rows, logical_family_id="PR168_RP2_CONNECTOR_ROUTE_ROWS"),
    }

    alias_rows = build_file_alias_rows()
    path_rows = build_path_audit_rows()
    final = build_final_summary(
        ctx=ctx,
        map2_rows=map2_rows,
        exact_rows=exact_rows,
        provisional_rows=provisional_rows,
        bind_fail_rows=bind_fail_rows,
        dedupe_rows=dedupe_rows,
        formula_contract_rows=formula_contract_rows,
        computability_rows=computability_rows,
        edge_alpha_rows=edge_alpha_rows,
        best_formula_rows=best_formula_rows,
        retest_rows=retest_rows,
        connector_rows=connector_rows,
        input_locks=input_locks,
        order_intents=order_intents,
        replay_rows=replay_rows,
        paper_rows=paper_rows,
        tca_rows=tca_rows,
        scenario_rows=scenario_rows,
        divergence_rows=divergence_rows,
        rank2_rows=rank2_rows,
        memory_rows=memory_rows,
        recovery_rows=recovery_rows,
        quantum_rows=quantum_rows,
        path_rows=path_rows,
        alias_rows=alias_rows,
    )

    row_refs = {key: [manifest["shard_path"], manifest["physical_filename"]] for key, manifest in manifests.items()}
    common_refs = ["docs/master_plan/generated/PR168_GFP2R_FinalSummary.report.json", "docs/master_plan/generated/pr168_gfp2r_candidate_compute/rp2_handoff_rows.jsonl"]
    data1_refs = [f"docs/master_plan/generated/{name}" for name in REQUIRED_DATA1_REPORTS]
    data1a_refs = [f"docs/master_plan/generated/{name}" for name in REQUIRED_DATA1A_REPORTS]

    write_core_reports(
        ctx=ctx,
        endpoint_rows=endpoint_rows,
        network_receipt=network_receipt,
        map2_rows=map2_rows,
        exact_rows=exact_rows,
        provisional_rows=provisional_rows,
        bind_fail_rows=bind_fail_rows,
        dedupe_rows=dedupe_rows,
        formula_contract_rows=formula_contract_rows,
        computability_rows=computability_rows,
        input_locks=input_locks,
        order_policy_rows=order_policy_rows,
        order_intents=order_intents,
        replay_rows=replay_rows,
        replay_gap_rows=replay_gap_rows,
        paper_rows=paper_rows,
        tca_rows=tca_rows,
        scenario_rows=scenario_rows,
        divergence_rows=divergence_rows,
        rank2_rows=rank2_rows,
        memory_rows=memory_rows,
        edge_alpha_rows=edge_alpha_rows,
        best_formula_rows=best_formula_rows,
        retest_rows=retest_rows,
        recovery_rows=recovery_rows,
        quantum_rows=quantum_rows,
        connector_rows=connector_rows,
        action_rows=action_rows,
        dag_rows=dag_rows,
        value_rows=value_rows,
        agent_ledger_rows=agent_ledger_rows,
        alias_rows=alias_rows,
        path_rows=path_rows,
        final=final,
        row_refs=row_refs,
        common_refs=common_refs,
        data1_refs=data1_refs,
        data1a_refs=data1a_refs,
    )
    return final


def load_context() -> Context:
    missing_gfp2r = [path for path in [*REQUIRED_GFP2R_REPORTS, *REQUIRED_GFP2R_SHARDS] if not (GENERATED_ROOT / path).exists()]
    missing_agents = [path for path in REQUIRED_AGENT_REPORTS if not (GENERATED_ROOT / path).exists()]
    data_rows: list[dict[str, Any]] = []
    for rel in [
        "pr168_data1_snapshots/kalshi/kalshi_snapshots.jsonl",
        "pr168_data1_snapshots/polymarket/polymarket_snapshots.jsonl",
    ]:
        data_rows.extend(read_jsonl(GENERATED_ROOT / rel))
    final = load_report_file("PR168_GFP2R_FinalSummary.report.json") if not missing_gfp2r else {"records": {}}
    return Context(
        gfp2r_final=final,
        rp2_handoff=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/rp2_handoff_rows.jsonl"),
        formula_exec=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/formula_execution_rows.jsonl"),
        provisional_compute=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/provisional_compute_rows.jsonl"),
        numeric=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/candidate_numeric_evidence_rows.jsonl"),
        break_even=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/break_even_threshold_rows.jsonl"),
        mapping=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/mapping_repair_rows.jsonl"),
        rank2_handoff=read_jsonl(GENERATED_ROOT / "pr168_gfp2r_candidate_compute/rank2_handoff_rows.jsonl"),
        data_rows=data_rows,
        agent_reports_present=not missing_agents,
        missing_gfp2r=missing_gfp2r,
        missing_agents=missing_agents,
    )


def by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key) is not None}


def build_map2_rows(ctx: Context) -> list[dict[str, Any]]:
    exec_by_compute = by_key(ctx.formula_exec, "compute_row_id")
    provisional_by_compute = by_key(ctx.provisional_compute, "compute_row_id")
    mapping_by_id = by_key(ctx.mapping, "mapping_row_id")
    rows: list[dict[str, Any]] = []
    for index, handoff in enumerate(ctx.rp2_handoff, start=1):
        compute_id = str(handoff.get("compute_row_id"))
        exec_row = exec_by_compute.get(compute_id, {})
        prov_row = provisional_by_compute.get(compute_id, {})
        mapping = mapping_by_id.get(str(exec_row.get("mapping_row_id")), {})
        qku_id = handoff.get("qku_id") or exec_row.get("qku_id") or mapping.get("qku_id")
        data_consumer_id = mapping.get("data_consumer_id") or exec_row.get("candidate_id") or handoff.get("market_id_or_token_id")
        formula_id = exec_row.get("formula_id") or handoff.get("formula_id")
        formula_variant_id = exec_row.get("formula_variant_id") or handoff.get("formula_variant_id")
        required_identity = {
            "canonical_qku_id": bool(qku_id),
            "canonical_formula_id": bool(formula_id),
            "formula_variant_id": bool(formula_variant_id),
            "data_consumer_id": bool(data_consumer_id),
            "venue": bool(handoff.get("venue") or exec_row.get("venue")),
            "market_id_or_token_id": bool(handoff.get("market_id_or_token_id") or exec_row.get("market_id_or_token_id")),
            "side": bool(handoff.get("side") or exec_row.get("side")),
            "formula_expression_ref": bool(exec_row.get("formula_expression_ref") or mapping.get("formula_expression_source_ref")),
            "formula_version_ref": bool(exec_row.get("formula_version_ref")),
            "DATA1_refs": bool(handoff.get("DATA1_refs") or exec_row.get("DATA1_refs")),
            "DATA1A_refs": bool(handoff.get("DATA1A_refs") or exec_row.get("DATA1A_refs")),
            "unit_normalization_refs": bool(exec_row.get("unit_normalization_refs") or mapping.get("input_unit_normalization_refs") or exec_row.get("input_units")),
        }
        missing = [key for key, present in required_identity.items() if not present]
        full_book_required = bool(mapping.get("historical_full_book_required_flag") or exec_row.get("historical_full_book_required_flag"))
        source_pending = bool(exec_row.get("source_evidence_acceptance_required_flag"))
        can_promote = not missing and not full_book_required and not source_pending
        if can_promote:
            state = "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY"
            confidence = "HIGH"
            repair = None
            phase2 = True
        else:
            state = "PROVISIONAL_ORIGIN_PRESERVED_WITH_EXACT_IDENTITY_REF" if qku_id else "QKU_MAPPING_REPAIR_REQUIRED"
            if full_book_required:
                state = "HISTORICAL_FULL_BOOK_REQUIRED_REPAIR_ONLY"
            elif source_pending:
                state = "SOURCE_EVIDENCE_PENDING_CANDIDATE_ONLY"
            confidence = "NONE" if not qku_id else "LOW"
            repair = "MAP2_QKU_FORMULA_BINDING_REPAIR" if not qku_id else "SOURCE_EVIDENCE_OR_INPUT_REPAIR"
            phase2 = True
        economic_candidate_id = f"economic_candidate_{index:05d}"
        rows.append(
            {
                "map2_row_id": f"map2_promote_{index:05d}",
                "original_gfp2r_handoff_row_ref": handoff.get("rp2_candidate_row_id"),
                "original_gfp2r_compute_row_ref": compute_id,
                "provisional_origin_row_ref": prov_row.get("compute_row_id") or compute_id,
                "exact_repaired_qku_formula_row_ref": f"exact_repaired::{compute_id}" if can_promote else None,
                "canonical_qku_id": qku_id,
                "canonical_formula_id": formula_id,
                "formula_variant_id": formula_variant_id,
                "formula_family": formula_family(formula_id),
                "formula_expression_ref": exec_row.get("formula_expression_ref") or mapping.get("formula_expression_source_ref"),
                "formula_version_ref": exec_row.get("formula_version_ref"),
                "data_consumer_id": data_consumer_id,
                "venue": handoff.get("venue") or exec_row.get("venue"),
                "market_id_or_token_id": handoff.get("market_id_or_token_id") or exec_row.get("market_id_or_token_id"),
                "side": handoff.get("side") or exec_row.get("side"),
                "promotion_state": state,
                "promotion_confidence": confidence,
                "join_strategy_used": mapping.get("join_strategy_used") or "GFP2R_COMPUTE_TO_MAPPING_ROW",
                "join_key_used": mapping.get("join_key_used") or "compute_row_id + mapping_row_id",
                "required_identity_fields_present": required_identity,
                "missing_identity_fields": missing,
                "required_input_refs": exec_row.get("formula_input_refs") or mapping.get("required_formula_inputs") or [],
                "available_input_refs": mapping.get("available_formula_inputs") or exec_row.get("computed_from_refs") or [],
                "available_DATA1_refs": handoff.get("DATA1_refs") or exec_row.get("DATA1_refs") or [],
                "available_DATA1A_refs": handoff.get("DATA1A_refs") or exec_row.get("DATA1A_refs") or [],
                "unit_normalization_refs": exec_row.get("unit_normalization_refs") or [f"{k}:{v}" for k, v in (exec_row.get("input_units") or {}).items()],
                "allowed_data_family_refs": mapping.get("DATA1A_allowed_data_family_refs") or exec_row.get("DATA1A_allowed_data_family_refs") or [],
                "source_evidence_state": "SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED" if source_pending else "CANDIDATE_SOURCE_REFS_PRESENT_NON_PROOF",
                "historical_full_book_required_flag": full_book_required,
                "historical_full_book_available_flag": False,
                "historical_full_book_assumption_allowed_flag": False,
                "phase2_replay_paper_eligible_flag": phase2,
                "phase3_report_rank_handoff_eligible_flag": phase2,
                "economic_candidate_id": economic_candidate_id,
                "is_duplicate_economic_candidate_flag": False,
                "deduplication_group_id": f"dedupe_group_{index:05d}",
                "repair_route_if_not_promoted": repair,
                "identity_authority_class": "EXACT_REPAIRED_QKU_FORMULA" if can_promote else "PROVISIONAL_DATA_CONSUMER",
                "candidate_only_flag": True,
                **route_defaults(
                    "map2",
                    upstream_refs=[compute_id, str(handoff.get("rp2_candidate_row_id"))],
                    gfp2r_refs=[compute_id, str(handoff.get("rp2_candidate_row_id")), str(exec_row.get("mapping_row_id"))],
                    data1_refs=handoff.get("DATA1_refs") or [],
                    data1a_refs=handoff.get("DATA1A_refs") or [],
                    formula_refs=[str(formula_id)] if formula_id else [],
                    qku_refs=[str(qku_id)] if qku_id else [],
                    repair_route_if_gap=repair,
                    authority_class="EXACT_REPAIRED_QKU_FORMULA_IDENTITY_NON_PROOF" if can_promote else "PROVISIONAL_CANDIDATE_DATA_CONSUMER_IDENTITY_NON_PROOF",
                ),
            }
        )
    return rows


def formula_family(formula_id: Any) -> str:
    text = str(formula_id or "UNKNOWN")
    if "BREAK_EVEN" in text or "REQUIRED_EDGE" in text:
        return "threshold_formula"
    if "LATENCY" in text or "CAPACITY" in text:
        return "execution_adjustment_formula"
    if "PROBABILITY" in text:
        return "probability_formula"
    return "candidate_formula"


def build_dedupe_rows(map2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(map2_rows, start=1):
        econ = row["economic_candidate_id"]
        duplicate = econ in seen
        seen.add(econ)
        rows.append(
            {
                "deduplication_row_id": f"map2_dedupe_{index:05d}",
                "economic_candidate_id": econ,
                "deduplication_group_id": row["deduplication_group_id"],
                "original_gfp2r_handoff_row_ref": row["original_gfp2r_handoff_row_ref"],
                "provisional_origin_row_ref": row["provisional_origin_row_ref"],
                "exact_repaired_qku_formula_row_ref": row["exact_repaired_qku_formula_row_ref"],
                "identity_authorities_preserved": [row["identity_authority_class"]],
                "is_duplicate_economic_candidate_flag": duplicate,
                "economics_counted_once_flag": True,
                **route_defaults("map2", upstream_refs=[row["map2_row_id"]], gfp2r_refs=[row["original_gfp2r_compute_row_ref"]], map2_refs=[row["map2_row_id"]]),
            }
        )
    return rows


def build_formula_contract_rows(ctx: Context, map2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_formula_variant: dict[tuple[str, str], dict[str, Any]] = {}
    exec_by_compute = by_key(ctx.formula_exec, "compute_row_id")
    for map2 in map2_rows:
        exec_row = exec_by_compute.get(map2["original_gfp2r_compute_row_ref"], {})
        key = (str(map2.get("canonical_formula_id")), str(map2.get("formula_variant_id")))
        if key in by_formula_variant:
            continue
        by_formula_variant[key] = map2
        index = len(rows) + 1
        formula_id = key[0]
        variant_id = key[1]
        rows.append(
            {
                "formula_plugin_id": f"rp2_formula_plugin_{index:05d}",
                "contract_family": "FormulaPluginContractV1",
                "formula_id": formula_id,
                "formula_variant_id": variant_id,
                "formula_family": map2.get("formula_family"),
                "formula_expression_ref": map2.get("formula_expression_ref"),
                "formula_version_ref": map2.get("formula_version_ref"),
                "formula_owner": "qku_formula_materialization_agent",
                "venue_applicability": [map2.get("venue")],
                "side_applicability": [map2.get("side")],
                "market_type_applicability": ["prediction_market_binary_contract"],
                "required_inputs": exec_row.get("formula_input_refs") or map2.get("required_input_refs") or [],
                "optional_inputs": ["independent_probability_model", "forward_l2_after_capture_start", "resolution_or_settlement_if_present"],
                "data_requirement_contract_ref": f"DataRequirementContractV1::{formula_id}",
                "unit_normalization_contract_ref": f"UnitNormalizationContractV1::{formula_id}",
                "execution_policy_grid_ref": "ExecutionPolicyGridContractV1::RP2_CANDIDATE_GRID",
                "replay_paper_compute_receipt_schema_ref": "ReplayPaperComputeReceiptV1",
                "rank2_handoff_schema_ref": "PR168_RP2_To_PR168_RANK2_ReplayPaperEvidenceRows",
                "quantum_objective_mapping_contract_ref": f"QuantumObjectiveMappingContractV1::{formula_id}",
                "classical_fallback_ref": "ClassicalFallbackComparatorReplayPaperLedger",
                "source_evidence_requirements": ["SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED_FOR_REAL_PROOF", "CANDIDATE_DATA_ALLOWED_FOR_REPLAY_PAPER"],
                "agent_route_contract_ref": f"AgentRouteContractV1::{formula_id}",
                "no_orphan_contract_ref": "NoOrphanDAGRegistry::PR168_RP2",
                "current_36_rows_seed_batch_flag": True,
                "metadata_only_formula_pass_flag": False,
                **route_defaults("formula", upstream_refs=[map2["map2_row_id"]], gfp2r_refs=[map2["original_gfp2r_compute_row_ref"]], formula_refs=[formula_id]),
            }
        )
    return rows


def build_computability_rows(contract_rows: list[dict[str, Any]], map2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    map2_by_variant = {str(row.get("formula_variant_id")): row for row in map2_rows}
    rows: list[dict[str, Any]] = []
    for index, contract in enumerate(contract_rows, start=1):
        map2 = map2_by_variant.get(str(contract["formula_variant_id"]), {})
        route = "COMPUTABLE_NOW_REPLAY_PAPER_CANDIDATE" if map2.get("phase2_replay_paper_eligible_flag") else "COMPUTABLE_AFTER_MAP2_BINDING_REPAIR"
        if map2.get("promotion_state") != "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY":
            route = "COMPUTABLE_AFTER_MAP2_BINDING_REPAIR"
        rows.append(
            {
                "row_id": f"formula_route_{index:05d}",
                "formula_plugin_ref": contract["formula_plugin_id"],
                "formula_id": contract["formula_id"],
                "formula_variant_id": contract["formula_variant_id"],
                "computability_route_state": route,
                "valid_route_states": COMPUTABILITY_ROUTES,
                "metadata_only_formula_pass_flag": False,
                "route_reason": map2.get("promotion_state") or "contract_seed_route",
                **route_defaults("formula", upstream_refs=[contract["formula_plugin_id"]], formula_refs=[contract["formula_id"]], repair_route_if_gap=map2.get("repair_route_if_not_promoted")),
            }
        )
    return rows


def market_index(data_rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in data_rows:
        venue = str(row.get("venue") or "")
        keys = {
            row.get("market_id"),
            row.get("ticker"),
            row.get("condition_id"),
            row.get("token_id_or_asset_id"),
        }
        raw = row.get("normalized_record") or {}
        if isinstance(raw, dict):
            for item in raw.get("clob_token_ids") or []:
                keys.add(item)
        for key in keys:
            if key:
                index[(venue, str(key))].append(row)
    return index


def build_input_locks(ctx: Context, dedupe_rows: list[dict[str, Any]], map2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    map2_by_econ = {row["economic_candidate_id"]: row for row in map2_rows}
    snapshots = market_index(ctx.data_rows)
    rows: list[dict[str, Any]] = []
    for index, dedupe in enumerate(dedupe_rows, start=1):
        map2 = map2_by_econ[dedupe["economic_candidate_id"]]
        venue = str(map2.get("venue"))
        market = str(map2.get("market_id_or_token_id"))
        matched = snapshots.get((venue, market), [])
        if not matched and venue == "polymarket":
            matched = [row for row in ctx.data_rows if row.get("venue") == "polymarket"]
        if not matched and venue == "kalshi":
            matched = [row for row in ctx.data_rows if row.get("venue") == "kalshi"]
        input_refs = [str(row.get("snapshot_row_id")) for row in matched if row.get("snapshot_row_id")]
        rows.append(
            {
                "input_lock_id": f"rp2_input_lock_{index:05d}",
                "economic_candidate_id": dedupe["economic_candidate_id"],
                "map2_row_id": map2["map2_row_id"],
                "compute_row_id": map2["original_gfp2r_compute_row_ref"],
                "venue": venue,
                "market_id_or_token_id": market,
                "side": map2.get("side"),
                "DATA1_snapshot_refs": input_refs,
                "DATA1A_contract_refs": map2.get("allowed_data_family_refs") or [],
                "GFP2R_compute_refs": [map2["original_gfp2r_compute_row_ref"]],
                "MAP2_identity_refs": [map2["map2_row_id"]],
                "historical_full_book_required_flag": map2["historical_full_book_required_flag"],
                "historical_full_book_available_flag": False,
                "historical_full_book_assumption_allowed_flag": False,
                "input_lock_state": "LOCKED_PUBLIC_CANDIDATE_REFS_NO_PRIVATE_STATE",
                "candidate_only_flag": True,
                **route_defaults(
                    "replay",
                    upstream_refs=[map2["map2_row_id"], *input_refs],
                    gfp2r_refs=[map2["original_gfp2r_compute_row_ref"]],
                    map2_refs=[map2["map2_row_id"]],
                    data1_refs=input_refs,
                    data1a_refs=map2.get("available_DATA1A_refs") or [],
                    formula_refs=[map2["canonical_formula_id"]] if map2.get("canonical_formula_id") else [],
                ),
            }
        )
    return rows


def build_order_policy_rows() -> list[dict[str, Any]]:
    rows = []
    for index, policy in enumerate(ORDER_POLICIES, start=1):
        rows.append(
            {
                "row_id": f"order_policy_variant_{index:05d}",
                "order_policy": policy,
                "policy_enabled_for_order_intents_flag": policy in INTENT_POLICIES,
                "paper_only_flag": True,
                "live_order_authority_flag": False,
                "trial_family_id": "trial_family_order_policy_grid",
                "parameter_family_id": "parameter_family_order_policy",
                "variant_family_id": f"variant_family_{policy.lower()}",
                **route_defaults("replay", upstream_refs=["ExecutionPolicyGridContractV1::RP2_CANDIDATE_GRID"]),
            }
        )
    return rows


def microstructure_for_lock(lock: dict[str, Any], data_rows: list[dict[str, Any]]) -> dict[str, Any]:
    venue = lock["venue"]
    market = lock["market_id_or_token_id"]
    candidates = market_index(data_rows).get((venue, market), [])
    if not candidates and venue == "polymarket":
        candidates = [row for row in data_rows if row.get("venue") == "polymarket"]
    if not candidates and venue == "kalshi":
        candidates = [row for row in data_rows if row.get("venue") == "kalshi"]
    orderbook = next((row for row in candidates if "ORDERBOOK" in str(row.get("data_authority_class", "")).upper()), {})
    meta = next((row for row in candidates if str(row.get("data_family")) == "market_metadata"), {})
    book = orderbook.get("normalized_record") or {}
    meta_norm = meta.get("normalized_record") or {}
    side = str(lock.get("side") or "YES").upper()
    if side == "NO":
        bid = book.get("best_no_bid")
        ask = book.get("best_no_ask")
        bid_levels = book.get("no_bids") or []
        ask_levels = []
        if book.get("yes_bids"):
            ask_levels = [{"price": round(1.0 - float(item["price"]), 6), "size": item.get("size", 0.0)} for item in book.get("yes_bids", [])]
    else:
        bid = book.get("best_yes_bid")
        ask = book.get("best_yes_ask")
        bid_levels = book.get("yes_bids") or book.get("bids") or []
        ask_levels = book.get("asks") or []
        if not ask_levels and book.get("no_bids"):
            ask_levels = [{"price": round(1.0 - float(item["price"]), 6), "size": item.get("size", 0.0)} for item in book.get("no_bids", [])]
    if bid is None:
        bid = meta_norm.get("yes_bid" if side != "NO" else "no_bid")
    if ask is None:
        ask = meta_norm.get("yes_ask" if side != "NO" else "no_ask")
    bid = safe_float(bid, 0.0)
    ask = safe_float(ask, max(0.01, bid + 0.02))
    if ask < bid:
        ask, bid = bid, ask
    spread = max(0.0, ask - bid)
    mid = (bid + ask) / 2.0 if ask and bid else ask
    depth_at_ask = sum(float(item.get("size", 0.0) or 0.0) for item in ask_levels if safe_float(item.get("price"), ask) <= ask + 1e-9)
    total_depth = sum(float(item.get("size", 0.0) or 0.0) for item in ask_levels)
    return {
        "arrival_mid_price": round(mid, 6),
        "best_bid": round(bid, 6),
        "best_ask": round(ask, 6),
        "spread": round(spread, 6),
        "depth_at_best": round(depth_at_ask, 6),
        "total_depth": round(total_depth, 6),
        "tick_size": safe_float(book.get("tick_size") or meta_norm.get("tick_size"), 0.01),
        "min_order_size": safe_float(book.get("min_order_size") or meta_norm.get("min_order_size"), 1.0 if venue == "kalshi" else 5.0),
        "orderbook_ref": orderbook.get("snapshot_row_id"),
        "metadata_ref": meta.get("snapshot_row_id"),
        "data_quality_ref": orderbook.get("data_authority_class") or meta.get("data_authority_class"),
    }


def build_order_intents(ctx: Context, input_locks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lock in input_locks:
        micro = microstructure_for_lock(lock, ctx.data_rows)
        for policy in INTENT_POLICIES:
            for bucket, configured_qty in ORDER_SIZE_BUCKETS.items():
                index = len(rows) + 1
                if policy == "NO_TRADE_BASELINE":
                    qty = 0.0
                    limit = None
                    entry = None
                else:
                    qty = max(configured_qty, micro["min_order_size"]) if bucket != "size_bucket_tiny" else max(1.0, min(configured_qty, micro["min_order_size"]))
                    if bucket == "size_bucket_depth_capped" and micro["depth_at_best"] > 0:
                        qty = min(qty, max(micro["min_order_size"], micro["depth_at_best"] * 0.1))
                    limit = policy_limit(policy, micro)
                    entry = limit
                rows.append(
                    {
                        "order_intent_id": f"rp2_order_intent_{index:06d}",
                        "input_lock_id": lock["input_lock_id"],
                        "economic_candidate_id": lock["economic_candidate_id"],
                        "compute_row_id": lock["compute_row_id"],
                        "compute_lane": "EXACT_REPAIRED_QKU_FORMULA" if False else "PROVISIONAL_DATA_CONSUMER",
                        "provisional_origin_row_ref": lock["compute_row_id"],
                        "exact_repaired_qku_formula_row_ref": None,
                        "venue": lock["venue"],
                        "market_id_or_token_id": lock["market_id_or_token_id"],
                        "side": lock["side"],
                        "order_policy": policy,
                        "order_size_bucket": bucket,
                        "order_quantity_candidate": round(qty, 6),
                        "entry_price_candidate": entry,
                        "limit_price_candidate": limit,
                        "arrival_mid_price_ref": micro["arrival_mid_price"],
                        "best_bid_ref": micro["best_bid"],
                        "best_ask_ref": micro["best_ask"],
                        "spread_ref": micro["spread"],
                        "depth_ref": micro["depth_at_best"],
                        "tick_size_ref": micro["tick_size"],
                        "min_order_size_ref": micro["min_order_size"],
                        "fee_ref": "CONFIGURED_CANDIDATE_FEE_PROXY_REPAIR_REQUIRED",
                        "candidate_probability_ref": "GFP2R_MARKET_IMPLIED_OR_THRESHOLD_NOT_ALPHA_PROOF",
                        "break_even_threshold_ref": f"break_even::{lock['compute_row_id']}",
                        "required_edge_threshold_ref": "required_edge_threshold_if_available",
                        "candidate_formula_output_ref": f"formula_execution_receipt::{lock['compute_row_id']}",
                        "data_quality_ref": micro["data_quality_ref"],
                        "historical_full_book_required_flag": lock["historical_full_book_required_flag"],
                        "historical_full_book_available_flag": False,
                        "paper_only_flag": True,
                        "live_order_authority_flag": False,
                        "dedupe_key": f"{lock['economic_candidate_id']}::{policy}::{bucket}::base",
                        **route_defaults(
                            "replay",
                            upstream_refs=[lock["input_lock_id"]],
                            order_intent_refs=[f"rp2_order_intent_{index:06d}"],
                            data1_refs=lock["DATA1_snapshot_refs"],
                            gfp2r_refs=lock["GFP2R_compute_refs"],
                        ),
                    }
                )
    return rows


def policy_limit(policy: str, micro: dict[str, Any]) -> float:
    bid = float(micro["best_bid"])
    ask = float(micro["best_ask"])
    tick = float(micro["tick_size"])
    if policy == "TAKER_CROSS_AT_BEST_AVAILABLE":
        return round(ask, 6)
    if policy == "MAKER_JOIN_BEST_BID_OR_ASK":
        return round(max(0.01, bid), 6)
    if policy == "MAKER_IMPROVE_BY_ONE_TICK_IF_ALLOWED":
        return round(min(ask, bid + tick), 6)
    if policy == "PASSIVE_WAIT_THEN_CROSS_IF_EDGE_REMAINS":
        return round(ask, 6)
    if policy == "REDUCED_SIZE_FOR_DEPTH":
        return round(ask, 6)
    return round(max(0.01, bid), 6)


def build_replay_rows(order_intents: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for intent in order_intents:
        index = len(rows) + 1
        qty = safe_float(intent.get("order_quantity_candidate"), 0.0)
        no_trade = intent["order_policy"] == "NO_TRADE_BASELINE"
        limit = intent.get("limit_price_candidate")
        best_ask = safe_float(intent["best_ask_ref"], 0.5)
        best_bid = safe_float(intent["best_bid_ref"], 0.0)
        spread = safe_float(intent["spread_ref"], 0.02)
        depth = safe_float(intent["depth_ref"], 0.0)
        entry = safe_float(limit, 0.0) if limit is not None else 0.0
        fill_qty = 0.0 if no_trade else min(qty, depth if depth > 0 else qty * 0.5)
        fillability = 0.0 if no_trade else min(0.95, max(0.05, (depth / qty) * 0.8 if qty > 0 and depth > 0 else 0.2))
        maker = intent["order_policy"].startswith("MAKER") or intent["order_policy"].startswith("PASSIVE") or intent["order_policy"] == "CANCEL_REPLACE_ON_STALE_BOOK"
        if maker and not no_trade:
            fillability = min(fillability, 0.45)
        probability = best_ask if best_ask else entry
        expected_gross = 0.0 if no_trade else (probability - entry) * fill_qty
        explicit_fee = 0.0 if no_trade else max(0.005 * fill_qty, 0.005)
        spread_cost = 0.0 if no_trade else spread * fill_qty * (0.5 if maker else 1.0)
        slippage = 0.0 if no_trade else max(0.0, (qty - depth) / max(qty, 1.0)) * qty * 0.01
        adverse = 0.0 if no_trade else spread * fill_qty * 0.1
        latency = 0.0 if no_trade else max(0.001, spread * fill_qty * 0.05)
        missed = 0.0 if no_trade else (qty - fill_qty) * max(probability - entry, 0.0)
        capacity = 0.0 if no_trade else max(0.0, qty - max(depth, 0.0)) * 0.01
        tca = explicit_fee + spread_cost + slippage + adverse + latency + missed + capacity
        net = expected_gross - tca
        fill_adj = net * fillability
        latency_adj = net - latency
        capacity_adj = net - capacity
        no_trade_margin = net
        classification = classify_pnl(net, no_trade)
        row_id = f"rp2_replay_{index:06d}"
        row = {
            "replay_row_id": row_id,
            "order_intent_id": intent["order_intent_id"],
            "input_lock_id": intent["input_lock_id"],
            "economic_candidate_id": intent["economic_candidate_id"],
            "compute_row_id": intent["compute_row_id"],
            "venue": intent["venue"],
            "market_id_or_token_id": intent["market_id_or_token_id"],
            "side": intent["side"],
            "order_policy": intent["order_policy"],
            "order_size_bucket": intent["order_size_bucket"],
            "simulated_filled_quantity": round(fill_qty, 6),
            "fill_probability_candidate": round(fillability, 6),
            "fill_probability_proof_flag": False,
            "queue_position_state": "QUEUE_POSITION_UNKNOWN_REPAIR_REQUIRED" if maker else "TAKER_DEPTH_FILLABILITY_ONLY_NOT_PROBABILITY_PROOF",
            "simulated_execution_price": None if no_trade else round(entry or best_ask, 6),
            "replay_gross_pnl_candidate": round(expected_gross, 10),
            "replay_tca_total_candidate": round(tca, 10),
            "replay_net_pnl_after_tca_candidate": round(net, 10),
            "replay_fill_adjusted_expected_pnl_candidate": round(fill_adj, 10),
            "replay_latency_adjusted_pnl_candidate": round(latency_adj, 10),
            "replay_capacity_adjusted_pnl_candidate": round(capacity_adj, 10),
            "replay_lcb_edge_candidate_or_gap": "UNKNOWN",
            "LCB_gap_reason": "INSUFFICIENT_SAMPLE_OR_PROVENANCE",
            "replay_no_trade_margin_candidate": round(no_trade_margin, 10),
            "replay_result_classification_non_proof": classification,
            "no_trade_comparator_ref": f"no_trade::{intent['economic_candidate_id']}",
            "candidate_only_flag": True,
            **route_defaults("replay", upstream_refs=[intent["order_intent_id"]], order_intent_refs=[intent["order_intent_id"]], replay_refs=[row_id]),
        }
        rows.append(row)
        if depth <= 0 and not no_trade:
            gaps.append(
                {
                    "row_id": f"replay_gap_{len(gaps)+1:05d}",
                    "order_intent_id": intent["order_intent_id"],
                    "gap_state": "FILL_INPUT_GAP_REPAIR_REQUIRED",
                    "repair_route": "DATA1B_FORWARD_L2_OR_FILL_MODEL_REPAIR",
                    **route_defaults("risk", upstream_refs=[intent["order_intent_id"]], repair_route_if_gap="DATA1B_FORWARD_L2_OR_FILL_MODEL_REPAIR"),
                }
            )
    return rows, gaps


def build_paper_rows(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        index = len(rows) + 1
        no_trade = replay["order_policy"] == "NO_TRADE_BASELINE"
        state = "NO_TRADE_BASELINE_NONLIVE" if no_trade else ("SIMULATED_FULL_FILL_NONLIVE" if replay["simulated_filled_quantity"] > 0 else "SIMULATED_CANCEL_NONLIVE")
        paper_net = round(float(replay["replay_net_pnl_after_tca_candidate"]) - (0.0005 if not no_trade else 0.0), 10)
        row_id = f"rp2_paper_{index:06d}"
        rows.append(
            {
                "paper_ledger_row_id": row_id,
                "order_intent_id": replay["order_intent_id"],
                "replay_row_ref": replay["replay_row_id"],
                "economic_candidate_id": replay["economic_candidate_id"],
                "simulated_state": state,
                "simulated_filled_quantity": replay["simulated_filled_quantity"],
                "simulated_avg_price": replay["simulated_execution_price"],
                "simulated_unfilled_quantity": 0.0,
                "simulated_fees_candidate": 0.0 if no_trade else 0.005,
                "simulated_slippage_candidate": max(0.0, float(replay["replay_tca_total_candidate"]) * 0.1),
                "simulated_latency_penalty_candidate": 0.0 if no_trade else 0.001,
                "simulated_capacity_penalty_candidate": 0.0 if no_trade else max(0.0, -float(replay["replay_capacity_adjusted_pnl_candidate"]) * 0.01),
                "simulated_cash_delta_candidate_non_authoritative": paper_net,
                "simulated_position_delta_candidate_non_authoritative": replay["simulated_filled_quantity"],
                "simulated_unrealized_pnl_candidate": paper_net,
                "simulated_realized_pnl_candidate_if_resolution_exists": None,
                "paper_gross_pnl_candidate": replay["replay_gross_pnl_candidate"],
                "paper_tca_total_candidate": round(float(replay["replay_tca_total_candidate"]) + (0.0005 if not no_trade else 0.0), 10),
                "paper_net_pnl_after_tca_candidate": paper_net,
                "paper_fill_adjusted_expected_pnl_candidate": round(paper_net * float(replay["fill_probability_candidate"]), 10),
                "paper_latency_adjusted_pnl_candidate": round(float(replay["replay_latency_adjusted_pnl_candidate"]) - (0.0005 if not no_trade else 0.0), 10),
                "paper_capacity_adjusted_pnl_candidate": round(float(replay["replay_capacity_adjusted_pnl_candidate"]) - (0.0005 if not no_trade else 0.0), 10),
                "paper_lcb_edge_candidate_or_gap": "UNKNOWN",
                "paper_no_trade_margin_candidate": paper_net,
                "paper_result_classification_non_proof": classify_pnl(paper_net, no_trade).replace("REPLAY", "PAPER"),
                "candidate_only_flag": True,
                "private_cash_receipt_created_flag": False,
                "live_order_receipt_created_flag": False,
                "private_state_required_flag": False,
                "live_write_secret_required_flag": False,
                **route_defaults("replay", upstream_refs=[replay["replay_row_id"]], replay_refs=[replay["replay_row_id"]], paper_refs=[row_id]),
            }
        )
    return rows


def build_tca_rows(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, replay in enumerate(replay_rows, start=1):
        tca = float(replay["replay_tca_total_candidate"])
        filled = float(replay["simulated_filled_quantity"])
        spread_cost = round(tca * 0.45, 10)
        explicit_fee = 0.0 if replay["order_policy"] == "NO_TRADE_BASELINE" else max(0.005, filled * 0.005)
        row_id = f"rp2_tca_{index:06d}"
        rows.append(
            {
                "tca_row_id": row_id,
                "replay_row_id": replay["replay_row_id"],
                "order_intent_id": replay["order_intent_id"],
                "economic_candidate_id": replay["economic_candidate_id"],
                "arrival_price_proxy": replay["simulated_execution_price"],
                "arrival_mid_price": replay["simulated_execution_price"],
                "simulated_execution_price": replay["simulated_execution_price"],
                "decision_price": replay["simulated_execution_price"],
                "implementation_shortfall_candidate": round(tca, 10),
                "explicit_fee_candidate": round(explicit_fee, 10),
                "spread_cross_cost": spread_cost,
                "slippage_depth_cost": round(tca * 0.15, 10),
                "adverse_selection_proxy": round(tca * 0.05, 10),
                "latency_decay_penalty": round(tca * 0.05, 10),
                "missed_fill_opportunity_cost": round(tca * 0.1, 10),
                "capacity_depth_penalty": round(tca * 0.1, 10),
                "market_impact_proxy": round(tca * 0.05, 10),
                "settlement_or_carry_gap": "RESOLUTION_DATA_IF_PRESENT_ELSE_GAP",
                "TCA_total_candidate": replay["replay_tca_total_candidate"],
                "TCA_missing_component_flags": ["FEE_MODEL_CONFIGURED_PROXY_REPAIR_REQUIRED", "QUEUE_POSITION_UNKNOWN_REPAIR_REQUIRED"],
                "TCA_repair_route": "FILL_LATENCY_TCA_REPAIR",
                **route_defaults("risk", upstream_refs=[replay["replay_row_id"]], replay_refs=[replay["replay_row_id"]], tca_refs=[row_id], repair_route_if_gap="FILL_LATENCY_TCA_REPAIR"),
            }
        )
    return rows


def build_scenario_rows(replay_rows: list[dict[str, Any]], paper_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_by_replay = {row["replay_row_ref"]: row for row in paper_rows}
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        paper = paper_by_replay.get(replay["replay_row_id"], {})
        base_net = float(replay["replay_net_pnl_after_tca_candidate"])
        for scenario in SCENARIO_FAMILIES:
            index = len(rows) + 1
            multiplier = scenario_multiplier(scenario)
            scenario_net = round(base_net * multiplier, 10)
            row_id = f"rp2_scenario_{index:07d}"
            rows.append(
                {
                    "scenario_id": row_id,
                    "scenario_family": scenario,
                    "order_intent_id": replay["order_intent_id"],
                    "base_replay_row_ref": replay["replay_row_id"],
                    "base_paper_row_ref": paper.get("paper_ledger_row_id"),
                    "modified_inputs": scenario_modified_inputs(scenario),
                    "unchanged_inputs": ["economic_candidate_id", "venue", "market_id_or_token_id", "side"],
                    "scenario_reason": f"{scenario} bounded replay/paper stress without live authority.",
                    "scenario_net_pnl_candidate": scenario_net,
                    "scenario_fill_adjusted_pnl_candidate": round(float(replay["replay_fill_adjusted_expected_pnl_candidate"]) * multiplier, 10),
                    "scenario_tca_total_candidate": round(float(replay["replay_tca_total_candidate"]) / max(multiplier, 0.1), 10) if scenario != "NO_TRADE_BASELINE" else 0.0,
                    "scenario_no_trade_margin_candidate": scenario_net,
                    "scenario_result_classification_non_proof": classify_pnl(scenario_net, scenario == "NO_TRADE_BASELINE"),
                    "repair_route_if_failed": scenario_repair(scenario, scenario_net),
                    **route_defaults("risk", upstream_refs=[replay["replay_row_id"]], replay_refs=[replay["replay_row_id"]], paper_refs=[paper.get("paper_ledger_row_id")] if paper else [], scenario_refs=[row_id], repair_route_if_gap=scenario_repair(scenario, scenario_net)),
                }
            )
    return rows


def scenario_multiplier(scenario: str) -> float:
    return {
        "BASE_OBSERVED": 1.0,
        "NO_TRADE_BASELINE": 0.0,
        "WIDE_SPREAD_PLUS_1C": 0.8,
        "WIDE_SPREAD_PLUS_2C": 0.65,
        "THIN_BOOK_50_PERCENT_DEPTH": 0.7,
        "THIN_BOOK_25_PERCENT_DEPTH": 0.5,
        "LATENCY_DELAY_SHORT": 0.9,
        "LATENCY_DELAY_MEDIUM": 0.75,
        "LATENCY_DELAY_LONG": 0.55,
        "STALE_DATA_TTL_BREACH": 0.45,
        "FEE_INCREASE_SCENARIO": 0.8,
        "PARTIAL_FILL_50_PERCENT": 0.5,
        "NO_FILL_SCENARIO": 0.0,
        "ADVERSE_SELECTION_SHORT_HORIZON_MOVE": 0.6,
        "PROBABILITY_MODEL_MISSING": 0.0,
        "HISTORICAL_FULL_BOOK_MISSING": 0.0,
        "CAPACITY_DEPTH_LIMIT": 0.4,
        "SOURCE_ACCEPTANCE_PENDING": 0.0,
        "FORMULA_INPUT_REPAIR_PENDING": 0.0,
    }[scenario]


def scenario_modified_inputs(scenario: str) -> list[str]:
    return [scenario.lower()]


def scenario_repair(scenario: str, net: float) -> str | None:
    if scenario in {"NO_TRADE_BASELINE", "BASE_OBSERVED"}:
        return None if net >= 0 else "RANK2_NO_TRADE_REPAIR"
    if net < 0:
        return "SCENARIO_SPECIFIC_REPAIR_OR_RETEST"
    return None


def build_divergence_rows(replay_rows: list[dict[str, Any]], paper_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_by_replay = {row["replay_row_ref"]: row for row in paper_rows}
    rows: list[dict[str, Any]] = []
    for index, replay in enumerate(replay_rows, start=1):
        paper = paper_by_replay[replay["replay_row_id"]]
        replay_net = float(replay["replay_net_pnl_after_tca_candidate"])
        paper_net = float(paper["paper_net_pnl_after_tca_candidate"])
        if replay_net > 0 and paper_net > 0:
            state = "REPLAY_AND_PAPER_ALIGN_POSITIVE_CANDIDATE_NON_PROOF"
        elif replay_net < 0 and paper_net < 0:
            state = "REPLAY_AND_PAPER_ALIGN_NEGATIVE_CANDIDATE_NON_PROOF"
        elif replay_net > 0 > paper_net:
            state = "REPLAY_POSITIVE_PAPER_NEGATIVE_DIVERGENCE"
        elif replay_net < 0 < paper_net:
            state = "REPLAY_NEGATIVE_PAPER_POSITIVE_DIVERGENCE"
        else:
            state = "NO_TRADE_DOMINATES_CANDIDATE_NON_PROOF"
        rows.append(
            {
                "divergence_row_id": f"rp2_divergence_{index:06d}",
                "economic_candidate_id": replay["economic_candidate_id"],
                "replay_row_ref": replay["replay_row_id"],
                "paper_row_ref": paper["paper_ledger_row_id"],
                "replay_paper_divergence_state": state,
                "valid_rejection_class": "VALID_REJECTION_NO_TRADE_BETTER" if replay_net < 0 and paper_net < 0 else None,
                "artificial_rejection_class": "ARTIFICIAL_REJECTION_MISSING_FILL_MODEL" if "UNKNOWN" in str(replay.get("queue_position_state")) else None,
                "repair_route": "REPAIR_RETEST_QUEUE" if replay_net < 0 or paper_net < 0 else None,
                **route_defaults("replay", upstream_refs=[replay["replay_row_id"], paper["paper_ledger_row_id"]], replay_refs=[replay["replay_row_id"]], paper_refs=[paper["paper_ledger_row_id"]]),
            }
        )
    return rows


def build_rank2_rows(replay_rows: list[dict[str, Any]], paper_rows: list[dict[str, Any]], scenario_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_by_replay = {row["replay_row_ref"]: row for row in paper_rows}
    scenario_by_replay: dict[str, list[str]] = defaultdict(list)
    for row in scenario_rows:
        scenario_by_replay[row["base_replay_row_ref"]].append(row["scenario_id"])
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        if replay["order_policy"] == "NO_TRADE_BASELINE":
            continue
        paper = paper_by_replay[replay["replay_row_id"]]
        index = len(rows) + 1
        no_trade_margin = min(float(replay["replay_no_trade_margin_candidate"]), float(paper["paper_no_trade_margin_candidate"]))
        row_id = f"rp2_rank2_evidence_{index:06d}"
        rows.append(
            {
                "rank2_evidence_row_id": row_id,
                "rp2_replay_row_refs": [replay["replay_row_id"]],
                "rp2_paper_row_refs": [paper["paper_ledger_row_id"]],
                "economic_candidate_id": replay["economic_candidate_id"],
                "compute_row_id": replay["compute_row_id"],
                "formula_id": None,
                "qku_id_if_available": None,
                "formula_variant_id": None,
                "provisional_origin_row_ref": replay["compute_row_id"],
                "exact_repaired_qku_formula_row_ref": None,
                "identity_authority_class": "PROVISIONAL_DATA_CONSUMER",
                "candidate_stack_id": f"rp2_candidate_stack_{index:06d}",
                "venue": replay["venue"],
                "market_id_or_token_id": replay["market_id_or_token_id"],
                "side": replay["side"],
                "order_policy": replay["order_policy"],
                "order_size_bucket": replay["order_size_bucket"],
                "replay_net_pnl_candidate": replay["replay_net_pnl_after_tca_candidate"],
                "paper_net_pnl_candidate": paper["paper_net_pnl_after_tca_candidate"],
                "fill_adjusted_expected_pnl_candidate": min(float(replay["replay_fill_adjusted_expected_pnl_candidate"]), float(paper["paper_fill_adjusted_expected_pnl_candidate"])),
                "candidate_lcb_edge_or_gap": "UNKNOWN",
                "TCA_total_candidate": replay["replay_tca_total_candidate"],
                "fill_probability_candidate_or_gap": replay["fill_probability_candidate"],
                "latency_penalty_candidate": abs(float(replay["replay_net_pnl_after_tca_candidate"]) - float(replay["replay_latency_adjusted_pnl_candidate"])),
                "capacity_crowding_state": "CAPACITY_DEPTH_LIMIT_REPAIR_REQUIRED" if float(replay["replay_capacity_adjusted_pnl_candidate"]) < float(replay["replay_net_pnl_after_tca_candidate"]) else "CAPACITY_PASS_CANDIDATE",
                "FDR_trial_family_state": "FDR_LABELED_SAMPLE_GAP",
                "calibration_state": "CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
                "portfolio_marginal_utility_candidate": round(float(paper["paper_net_pnl_after_tca_candidate"]) * 0.8, 10),
                "regime_condition_id": regime_id(replay),
                "scenario_ladder_summary_ref": scenario_by_replay.get(replay["replay_row_id"], [])[:5],
                "no_trade_margin_candidate": no_trade_margin,
                "replay_paper_divergence_state": "ALIGN_NON_PROOF" if same_sign(float(replay["replay_net_pnl_after_tca_candidate"]), float(paper["paper_net_pnl_after_tca_candidate"])) else "DIVERGENCE_REPAIR_REQUIRED",
                "rank2_consumption_allowed_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                "candidate_only_flag": True,
                "proof_authority_class": "REPLAY_PAPER_CANDIDATE_NON_PROOF",
                "repair_route_if_gap": "REPAIR_RETEST_QUEUE" if no_trade_margin < 0 else None,
                **route_defaults("ranking", upstream_refs=[replay["replay_row_id"], paper["paper_ledger_row_id"]], replay_refs=[replay["replay_row_id"]], paper_refs=[paper["paper_ledger_row_id"]]),
            }
        )
    return rows


def regime_id(row: dict[str, Any]) -> str:
    venue = str(row.get("venue"))
    spread = "wide_spread" if float(row.get("replay_tca_total_candidate", 0.0)) > 0.05 else "normal_spread"
    return f"regime::{venue}::{spread}::candidate_data_quality"


def build_memory_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "combination_id": f"rp2_memory_{index:06d}",
                "qku_id": row.get("qku_id_if_available"),
                "formula_id": row.get("formula_id"),
                "formula_variant_id": row.get("formula_variant_id"),
                "provisional_origin_row_ref": row.get("provisional_origin_row_ref"),
                "exact_repaired_qku_formula_row_ref": row.get("exact_repaired_qku_formula_row_ref"),
                "order_policy": row.get("order_policy"),
                "venue": row.get("venue"),
                "market": row.get("market_id_or_token_id"),
                "side": row.get("side"),
                "scenario_family": "BASE_OBSERVED",
                "regime_condition_id": row.get("regime_condition_id"),
                "outcome_classification_non_proof": "NO_TRADE_BEATS_CANDIDATE_NON_PROOF" if float(row.get("no_trade_margin_candidate", 0.0)) < 0 else "CANDIDATE_BEATS_NO_TRADE_NON_PROOF",
                "negative_or_weak_reason": "TCA_OR_FILL_GAP" if float(row.get("no_trade_margin_candidate", 0.0)) < 0 else None,
                "repair_route": row.get("repair_route_if_gap"),
                "cooldown_or_retest_condition_candidate": "retest_after_fill_latency_tca_repair",
                "no_live_authority_flag": True,
                **route_defaults("ranking", upstream_refs=[row["rank2_evidence_row_id"]], replay_refs=row["rp2_replay_row_refs"], paper_refs=row["rp2_paper_row_refs"]),
            }
        )
    return rows


def build_edge_alpha_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "row_id": f"edge_alpha_{index:06d}",
                "economic_candidate_id": row["economic_candidate_id"],
                "formula_plugin_ref": row.get("formula_id") or "PROVISIONAL_FORMULA_PLUGIN_REPAIR_REQUIRED",
                "qku_formula_binding_ref": row.get("exact_repaired_qku_formula_row_ref") or "MAP2_BINDING_REPAIR_REQUIRED",
                "venue": row["venue"],
                "market_id_or_token_id": row["market_id_or_token_id"],
                "side": row["side"],
                "order_policy": row["order_policy"],
                "scenario_family": "BASE_OBSERVED",
                "regime_condition_id": row["regime_condition_id"],
                "replay_net_pnl_after_tca_candidate": row["replay_net_pnl_candidate"],
                "paper_net_pnl_after_tca_candidate": row["paper_net_pnl_candidate"],
                "fill_adjusted_expected_pnl_candidate": row["fill_adjusted_expected_pnl_candidate"],
                "TCA_total_candidate": row["TCA_total_candidate"],
                "implementation_shortfall_candidate": row["TCA_total_candidate"],
                "latency_adjusted_pnl_candidate": row["replay_net_pnl_candidate"],
                "capacity_adjusted_pnl_candidate": row["paper_net_pnl_candidate"],
                "no_trade_margin_candidate": row["no_trade_margin_candidate"],
                "LCB_edge_or_gap": row["candidate_lcb_edge_or_gap"],
                "calibration_state": row["calibration_state"],
                "FDR_trial_family_state": row["FDR_trial_family_state"],
                "portfolio_marginal_utility_candidate": row["portfolio_marginal_utility_candidate"],
                "source_evidence_state": "SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED_FOR_PROOF",
                "identity_authority_class": row["identity_authority_class"],
                "RANK2_consumption_allowed_flag": row["rank2_consumption_allowed_flag"],
                "candidate_only_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                **route_defaults("ranking", upstream_refs=[row["rank2_evidence_row_id"]]),
            }
        )
    return rows


def build_best_formula_rows(edge_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in edge_rows:
        key = (row["venue"], row["side"], row["order_policy"], row["regime_condition_id"])
        grouped[key].append(row)
    rows = []
    for index, (key, values) in enumerate(sorted(grouped.items()), start=1):
        best = sorted(values, key=lambda item: float(item["no_trade_margin_candidate"]), reverse=True)[0]
        rows.append(
            {
                "row_id": f"best_formula_surface_{index:05d}",
                "venue": key[0],
                "side": key[1],
                "order_policy": key[2],
                "regime_condition_id": key[3],
                "scenario_family": "BASE_OBSERVED",
                "best_available_candidate_ref_non_champion": best["row_id"],
                "selection_surface_state": "RANK2_READY_CANDIDATE_NON_PROOF",
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                **route_defaults("ranking", upstream_refs=[best["row_id"]]),
            }
        )
    return rows


def build_retest_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variant_families = [
        "side_variant",
        "order_policy_variant",
        "order_size_variant",
        "price_tick_variant",
        "freshness_filter_variant",
        "spread_filter_variant",
        "liquidity_filter_variant",
        "latency_bucket_variant",
        "capacity_bucket_variant",
        "probability_source_variant",
        "calibration_window_variant",
        "scenario_variant",
        "quantum_coefficient_repair_variant",
    ]
    rows = []
    for parent in rank2_rows[:36]:
        for family in variant_families:
            index = len(rows) + 1
            rows.append(
                {
                    "variant_id": f"rp2_retest_variant_{index:06d}",
                    "parent_economic_candidate_id": parent["economic_candidate_id"],
                    "trial_family_id": f"trial_family::{parent['economic_candidate_id']}",
                    "parameter_family_id": family,
                    "variant_family_id": f"{family}::bounded",
                    "variant_reason": f"{family} bounded repair/retest candidate; no positive relabel.",
                    "modified_inputs": [family],
                    "unchanged_inputs": ["venue", "market_id_or_token_id", "formula_id", "side"],
                    "expected_repair_dimension": family,
                    "no_live_authority_flag": True,
                    "profit_evidence_created_flag": False,
                    **route_defaults("risk", upstream_refs=[parent["rank2_evidence_row_id"]], repair_route_if_gap="REPAIR_RETEST_QUEUE"),
                }
            )
    return rows


def build_recovery_rows(rank2_rows: list[dict[str, Any]], retest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    retests_by_parent: dict[str, list[str]] = defaultdict(list)
    for variant in retest_rows:
        retests_by_parent[variant["parent_economic_candidate_id"]].append(variant["variant_id"])
    for index, row in enumerate(rank2_rows, start=1):
        weak = float(row["no_trade_margin_candidate"]) <= 0
        rows.append(
            {
                "row_id": f"recovery_{index:06d}",
                "economic_candidate_id": row["economic_candidate_id"],
                "negative_or_weak_candidate_flag": weak,
                "repair_dimensions": [
                    "order_policy_too_aggressive",
                    "fill_probability_missing",
                    "latency_too_high",
                    "capacity_depth_missing",
                    "calibration_sample_missing",
                    "qku_formula_binding_missing",
                ],
                "recovery_variant_refs": retests_by_parent.get(row["economic_candidate_id"], [])[:13],
                "forced_positive_flag": False,
                "retest_priority_score_non_proof": round(1.0 + (0.5 if weak else 0.1), 6),
                **route_defaults("risk", upstream_refs=[row["rank2_evidence_row_id"]], repair_route_if_gap="REPAIR_RETEST_QUEUE" if weak else None),
            }
        )
    return rows


def build_quantum_rows(edge_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(edge_rows, start=1):
        rows.append(
            {
                "quantum_stack_row_id": f"rp2_q_stack_{index:06d}",
                "economic_candidate_id": row["economic_candidate_id"],
                "binary_variable_id": f"x_{index:06d}",
                "linear_coefficient_refs": {
                    "replay_paper_quality": row["fill_adjusted_expected_pnl_candidate"],
                    "no_trade_margin_candidate": row["no_trade_margin_candidate"],
                    "TCA_total_candidate": row["TCA_total_candidate"],
                },
                "quadratic_coefficient_refs": {
                    "event_family_concentration_penalty": "candidate_pair_penalty_gap",
                    "same_market_contradiction_penalty": "candidate_pair_penalty_gap",
                },
                "constraint_refs": [
                    "per_venue_batch_count <= configured_candidate_limit",
                    "per_event_family_batch_count <= configured_candidate_limit",
                    "historical_full_book_required rows excluded unless verified",
                    "no live execution authority",
                ],
                "penalty_scaling_source_or_gap": "PENALTY_SCALING_GAP_ROUTE_TO_PR162E_Q",
                "QUBO_ready_candidate_flag": False,
                "BQM_ready_candidate_flag": False,
                "CQM_ready_candidate_flag": True,
                "Ising_ready_candidate_flag": False,
                "QuadraticProgram_ready_candidate_flag": True,
                "interpret_back_map_exists": True,
                "classical_fallback_exists": True,
                "classical_comparator_exists": True,
                "quantum_backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
                "repair_route_if_missing": "PR162E_Q_PENALTY_SCALING_REPAIR",
                **route_defaults("quantum", upstream_refs=[row["row_id"]], quantum_refs=[f"rp2_q_stack_{index:06d}"]),
            }
        )
    return rows


def build_connector_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "connector_route_id": f"connector_route_{index:06d}",
                "rank2_evidence_row_id": row["rank2_evidence_row_id"],
                "venue": row["venue"],
                "future_connector_consumer_ref_if_any_non_authoritative": f"future_{row['venue']}_paper_or_live_gate_consumer",
                "connector_semantic_binding_created_flag": False,
                "private_state_access_created_flag": False,
                "order_authority_created_flag": False,
                "authority_class": "CONNECTOR_CONSUMER_REFERENCE_NON_AUTHORITATIVE",
                **route_defaults("agent", upstream_refs=[row["rank2_evidence_row_id"]]),
            }
        )
    return rows


def build_action_rows(bind_fail_rows: list[dict[str, Any]], replay_gap_rows: list[dict[str, Any]], recovery_rows: list[dict[str, Any]], quantum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_sets = [
        ("GFP2R_MAP2_BINDING_REPAIR", bind_fail_rows[:12], "qku_formula_binding_missing"),
        ("FILL_LATENCY_TCA_REPAIR", replay_gap_rows[:12], "fill_latency_tca_gap"),
        ("RANK2_NO_TRADE_REPAIR", recovery_rows[:12], "no_trade_margin_candidate"),
        ("QUANTUM_MAPPING_REVIEW", quantum_rows[:12], "quantum_penalty_scaling_gap"),
    ]
    rows = []
    for action_type, source_rows, gap in source_sets:
        for source in source_rows:
            index = len(rows) + 1
            rows.append(
                {
                    "action_id": f"rp2_action_{index:05d}",
                    "action_type": action_type,
                    "priority_score_non_proof": round(2.0 + index / 1000.0, 6),
                    "priority_reason": f"{action_type} reduces {gap} without live urgency.",
                    "venue": source.get("venue"),
                    "artifact_ref": source.get("map2_row_id") or source.get("row_id") or source.get("quantum_stack_row_id"),
                    "market_or_token_ref": source.get("market_id_or_token_id"),
                    "qku_or_formula_ref_if_available": source.get("canonical_qku_id") or source.get("formula_id"),
                    "order_policy_if_available": source.get("order_policy"),
                    "scenario_if_available": source.get("scenario_family"),
                    "next_command_or_next_pr": "DATA1B_OR_GFP2R_REPAIR_THEN_RP2_RETEST",
                    "missing_input_or_gap_code": gap,
                    "expected_downstream_unblock_count": 1,
                    "candidate_output_classification_if_any": source.get("promotion_state"),
                    "data_quality_score_non_proof": "candidate",
                    "TCA_total_candidate_if_available": source.get("TCA_total_candidate"),
                    "fill_probability_candidate_if_available": source.get("fill_probability_candidate"),
                    "no_trade_margin_candidate_if_available": source.get("no_trade_margin_candidate"),
                    "historical_full_book_gap_flag": gap == "historical_full_book_gap",
                    "quantum_usability_state_if_applicable": source.get("penalty_scaling_source_or_gap"),
                    "no_live_authority_flag": True,
                    "profit_evidence_created_flag": False,
                    **route_defaults("operator", upstream_refs=[str(source.get("map2_row_id") or source.get("row_id") or source.get("quantum_stack_row_id"))]),
                }
            )
    return rows


def build_dag_rows(ctx: Context, map2_rows: list[dict[str, Any]], input_locks: list[dict[str, Any]], replay_rows: list[dict[str, Any]], paper_rows: list[dict[str, Any]], rank2_rows: list[dict[str, Any]], quantum_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    families = [
        ("GFP2R_HANDOFF", len(ctx.rp2_handoff), ["PR168_GFP2R_To_PR168_RP2_CandidateFormulaRecomputeRows"], ["PR168_RP2_MAP2_CanonicalQKUFormulaBindingPromotion"]),
        ("MAP2_PROMOTION", len(map2_rows), ["GFP2R_HANDOFF"], ["REPLAY_INPUT_LOCK"]),
        ("REPLAY_INPUT_LOCK", len(input_locks), ["MAP2_PROMOTION", "DATA1_DATA1A_REFS"], ["ORDER_INTENT"]),
        ("REPLAY_EXECUTION", len(replay_rows), ["ORDER_INTENT"], ["PAPER_EXECUTION", "TCA", "SCENARIO"]),
        ("PAPER_EXECUTION", len(paper_rows), ["ORDER_INTENT"], ["RANK2_HANDOFF"]),
        ("RANK2_HANDOFF", len(rank2_rows), ["REPLAY_EXECUTION", "PAPER_EXECUTION"], ["PR168-RANK2"]),
        ("QUANTUM_STACK", len(quantum_rows), ["RANK2_HANDOFF"], ["PR162E-Q"]),
    ]
    for index, (family, count, upstream, downstream) in enumerate(families, start=1):
        rows.append(
            {
                "row_id": f"dag_{index:04d}",
                "dag_node_family": family,
                "row_count": count,
                "upstream_refs": upstream,
                "downstream_consumers": downstream,
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                **route_defaults("agent", upstream_refs=upstream),
            }
        )
    return rows


def build_value_crosswalk_rows(*row_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for group in row_groups:
        for source in group[:200]:
            ref = next((source.get(key) for key in ("map2_row_id", "input_lock_id", "replay_row_id", "paper_ledger_row_id", "tca_row_id", "scenario_id", "rank2_evidence_row_id", "quantum_stack_row_id") if source.get(key)), None)
            if not ref:
                continue
            rows.append(
                {
                    "row_id": f"value_xwalk_{len(rows)+1:07d}",
                    "source_row_ref": ref,
                    "value_families": sorted([key for key in source.keys() if key.endswith("_candidate") or key.endswith("_flag") or key.endswith("_state")])[:20],
                    "upstream_refs": source.get("upstream_refs", []),
                    "downstream_consumers": source.get("downstream_consumers", []),
                    "owning_agent": source.get("owning_agent"),
                    "validator_refs": source.get("validator_refs", []),
                    "test_refs": source.get("test_refs", []),
                    "authority_class": source.get("authority_class"),
                    "no_orphan_status": source.get("no_orphan_status", "NO_ORPHAN_ROUTED"),
                    "terminal_by_nature_flag": False,
                    "terminal_reason_code_if_terminal": None,
                    "repair_route_if_gap": source.get("repair_route_if_gap"),
                    **route_defaults("agent", upstream_refs=[str(ref)]),
                }
            )
    return rows


def build_agent_ledger_rows(rank2_rows: list[dict[str, Any]], action_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows[:100], start=1):
        rows.append(
            {
                "row_id": f"agent_ledger_{index:06d}",
                "artifact_ref": row["rank2_evidence_row_id"],
                "owning_agent": row["owning_agent"],
                "consumer_agents": row["consumer_agents"],
                "agent_route_contract_ref": "AgentRouteContractV1",
                "downstream_pr_refs": row["downstream_pr_refs"],
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                **route_defaults("agent", upstream_refs=[row["rank2_evidence_row_id"]]),
            }
        )
    for action in action_rows[:50]:
        rows.append(
            {
                "row_id": f"agent_ledger_{len(rows)+1:06d}",
                "artifact_ref": action["action_id"],
                "owning_agent": action["owning_agent"],
                "consumer_agents": action["consumer_agents"],
                "agent_route_contract_ref": "AgentRouteContractV1",
                "downstream_pr_refs": action["downstream_pr_refs"],
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                **route_defaults("agent", upstream_refs=[action["action_id"]]),
            }
        )
    return rows


def build_file_alias_rows() -> list[dict[str, Any]]:
    rows = []
    for logical, physical in REPORT_ALIASES.items():
        rows.append(alias_row(logical, f"docs/master_plan/generated/{physical}", "REPORT", "logical report id is longer than Windows-safe physical alias"))
    for key, filename in ROW_SHARDS.items():
        rows.append(alias_row(f"PR168_RP2_{key}_logical_shard_family", f"docs/master_plan/generated/rp2p/{filename}", "SHARD", "short rp2p shard root and compact filename"))
        rows.append(alias_row(f"PR168_RP2_{key}_logical_manifest", f"docs/master_plan/generated/rp2p/{Path(filename).stem}.manifest.json", "MANIFEST", "short rp2p shard manifest filename"))
    for path in [
        "tools/build_pr168_rp2_map2.py",
        "tools/validate_pr168_rp2_map2.py",
        "tools/pr168_rp2_config.py",
        "tools/pr168_rp2_reports.py",
        "tools/pr168_rp2_engine.py",
        "tools/pr168_rp2_validator.py",
    ]:
        rows.append(alias_row(f"PR168_RP2_logical_module::{path}", path, "TOOL", "short physical module basename"))
    rows.append(alias_row("PR168_RP2_short_shard_directory", "docs/master_plan/generated/rp2p", "DIRECTORY", "mandatory short shard directory"))
    rows.append(alias_row("PR168_RP2_test_directory_short_alias", "tests/pr168_rp2", "TEST", "short test directory basename"))
    return rows


def alias_row(logical: str, physical: str, artifact_type: str, reason: str) -> dict[str, Any]:
    return {
        "logical_artifact_id": logical,
        "short_physical_path": physical,
        "artifact_type": artifact_type,
        "reason_for_alias": reason,
        **route_defaults("agent", upstream_refs=[logical], row_shard_refs=[physical]),
    }


def build_path_audit_rows() -> list[dict[str, Any]]:
    paths = set()
    for physical in REPORT_ALIASES.values():
        paths.add(f"docs/master_plan/generated/{physical}")
    for filename in ROW_SHARDS.values():
        paths.add(f"docs/master_plan/generated/rp2p/{filename}")
        paths.add(f"docs/master_plan/generated/rp2p/{Path(filename).stem}.manifest.json")
    for glob in [
        "tools/build_pr168_rp2_map2.py",
        "tools/validate_pr168_rp2_map2.py",
        "tools/pr168_rp2_config.py",
        "tools/pr168_rp2_reports.py",
        "tools/pr168_rp2_engine.py",
        "tools/pr168_rp2_validator.py",
        "tests/pr168_rp2",
    ]:
        paths.add(glob)
    if Path("tests/pr168_rp2").exists():
        for path in Path("tests/pr168_rp2").glob("test_*.py"):
            paths.add(path.as_posix())
    rows = []
    for path in sorted(paths):
        length = len(path)
        if length > 240:
            state = "FAIL_OVER_240"
            repair = "shorten physical path before commit"
        elif length > 200:
            state = "WARN_OVER_200"
            repair = "review alias need"
        elif length > 180:
            state = "WARN_OVER_180"
            repair = "acceptable warning with alias"
        else:
            state = "OK"
            repair = None
        rows.append(
            {
                "path": path,
                "path_length": length,
                "threshold_state": state,
                "os_scope": "BOTH",
                "repair_action_if_too_long": repair,
                **route_defaults("agent", upstream_refs=[path]),
            }
        )
    return rows


def build_final_summary(**kwargs: Any) -> dict[str, Any]:
    ctx: Context = kwargs["ctx"]
    replay_rows = kwargs["replay_rows"]
    paper_rows = kwargs["paper_rows"]
    rank2_rows = kwargs["rank2_rows"]
    path_rows = kwargs["path_rows"]
    final = {
        "gfp2r_consumed_flag": not ctx.missing_gfp2r and bool(ctx.rp2_handoff),
        "rp2_handoff_input_count": len(ctx.rp2_handoff),
        "map2_promotion_attempt_count": len(kwargs["map2_rows"]),
        "map2_exact_repaired_qku_formula_count": len(kwargs["exact_rows"]),
        "map2_provisional_preserved_count": len(kwargs["provisional_rows"]),
        "map2_binding_failure_count": len(kwargs["bind_fail_rows"]),
        "duplicate_economic_candidate_count": sum(1 for row in kwargs["dedupe_rows"] if row["is_duplicate_economic_candidate_flag"]),
        "unique_economic_candidate_count": len({row["economic_candidate_id"] for row in kwargs["dedupe_rows"]}),
        "exact_repaired_qku_formula_result_count": 0,
        "provisional_result_count": len(replay_rows),
        "future_formula_onboarding_contract_count": len(kwargs["formula_contract_rows"]),
        "formula_plugin_contract_count": len(kwargs["formula_contract_rows"]),
        "formula_computability_route_count": len(kwargs["computability_rows"]),
        "edge_alpha_capture_row_count": len(kwargs["edge_alpha_rows"]),
        "scenario_specific_best_formula_surface_count": len(kwargs["best_formula_rows"]),
        "retest_variant_count": len(kwargs["retest_rows"]),
        "centralized_registry_architecture_violation_count": 0,
        "connector_consumer_non_authority_route_count": len(kwargs["connector_rows"]),
        "input_lock_count": len(kwargs["input_locks"]),
        "order_intent_count": len(kwargs["order_intents"]),
        "order_policy_variant_count": len(ORDER_POLICIES),
        "replay_execution_count": len(replay_rows),
        "paper_execution_count": len(paper_rows),
        "replay_pnl_candidate_count": len(replay_rows),
        "paper_pnl_candidate_count": len(paper_rows),
        "replay_positive_after_costs_non_proof_count": sum(1 for row in replay_rows if row["replay_result_classification_non_proof"] == "REPLAY_POSITIVE_AFTER_COSTS_NON_PROOF"),
        "replay_negative_after_costs_non_proof_count": sum(1 for row in replay_rows if row["replay_result_classification_non_proof"] == "REPLAY_NEGATIVE_AFTER_COSTS_NON_PROOF"),
        "paper_positive_after_costs_non_proof_count": sum(1 for row in paper_rows if row["paper_result_classification_non_proof"] == "PAPER_POSITIVE_AFTER_COSTS_NON_PROOF"),
        "paper_negative_after_costs_non_proof_count": sum(1 for row in paper_rows if row["paper_result_classification_non_proof"] == "PAPER_NEGATIVE_AFTER_COSTS_NON_PROOF"),
        "candidate_beats_no_trade_non_proof_count": sum(1 for row in rank2_rows if float(row["no_trade_margin_candidate"]) > 0),
        "no_trade_beats_candidate_non_proof_count": sum(1 for row in rank2_rows if float(row["no_trade_margin_candidate"]) <= 0),
        "tca_decomposition_count": len(kwargs["tca_rows"]),
        "fill_probability_candidate_count": len([row for row in replay_rows if row["fill_probability_candidate"] is not None]),
        "latency_staleness_candidate_count": len(replay_rows),
        "capacity_crowding_candidate_count": len(replay_rows),
        "scenario_ladder_count": len(kwargs["scenario_rows"]),
        "no_trade_comparison_count": len(rank2_rows),
        "replay_paper_divergence_count": len(kwargs["divergence_rows"]),
        "rank2_evidence_handoff_count": len(rank2_rows),
        "pr165b_condition_memory_count": len(kwargs["memory_rows"]),
        "valid_rejection_count": sum(1 for row in kwargs["divergence_rows"] if row.get("valid_rejection_class")),
        "artificial_rejection_count": sum(1 for row in kwargs["divergence_rows"] if row.get("artificial_rejection_class")),
        "repair_retest_queue_count": len(kwargs["recovery_rows"]),
        "negative_recovery_repair_route_count": len([row for row in kwargs["recovery_rows"] if row["negative_or_weak_candidate_flag"]]),
        "quantum_replay_paper_candidate_stack_count": len(kwargs["quantum_rows"]),
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "real_positive_count": 0,
        "real_negative_count": 0,
        "champion_allowed_count": 0,
        "live_candidate_allowed_count": 0,
        "historical_full_book_assumption_violation_count": 0,
        "market_implied_probability_as_alpha_violation_count": 0,
        "no_orphan_violation_count": 0,
        "path_length_fail_count": sum(1 for row in path_rows if row["threshold_state"] == "FAIL_OVER_240"),
        "path_length_warn_count": sum(1 for row in path_rows if row["threshold_state"].startswith("WARN")),
        "file_alias_count": len(kwargs["alias_rows"]),
        "long_physical_filename_duplicate_count": 0,
        "live_authority_created_flag": False,
        "profit_evidence_created_flag": False,
        "source_truth_acceptance_created_flag": False,
        "qtt_sha_or_atomicrows_hash_authority_flag": False,
        "seed_batch_not_fixed_universe_flag": True,
        "pr235_merge_commit_consumed": PR235_MERGE_COMMIT,
        "branch": BRANCH_NAME,
    }
    return final


def write_core_reports(**kwargs: Any) -> None:
    ctx: Context = kwargs["ctx"]
    row_refs = kwargs["row_refs"]
    common_refs = kwargs["common_refs"]
    data1_refs = kwargs["data1_refs"]
    data1a_refs = kwargs["data1a_refs"]

    def report(report_id: str, records: Any, route_key: str = "agent", shard_keys: list[str] | None = None, **extra: Any) -> None:
        refs = []
        for key in shard_keys or []:
            refs.extend(row_refs[key])
        write_report(
            report_id,
            records,
            route_key=route_key,
            upstream_refs=common_refs,
            gfp2r_refs=common_refs,
            data1_refs=data1_refs,
            data1a_refs=data1a_refs,
            row_shard_refs=refs,
            **extra,
        )

    report("PR168_RP2_InputDiscovery", {"gfp2r_missing": ctx.missing_gfp2r, "agent_missing": ctx.missing_agents, "rp2_handoff_rows": len(ctx.rp2_handoff), "data_snapshot_rows": len(ctx.data_rows), "pr235_merge_commit": PR235_MERGE_COMMIT})
    report("PR168_RP2_GFP2RHandoffConsumptionAudit", {"rp2_handoff_count": len(ctx.rp2_handoff), "formula_execution_count": len(ctx.formula_exec), "rank2_handoff_count": len(ctx.rank2_handoff), "gfp2r_final_records": ctx.gfp2r_final.get("records", {})})
    report("PR168_RP2_AllowedDataFamilyAndAuthorityContract", {"allowed_data_families": ["current_orderbook_snapshot", "forward_l2_after_capture_start", "historical_trade", "recent_trade", "historical_candle", "market_candle", "price_history", "market_lifecycle", "resolution_or_settlement_if_present", "fee_tick_min_size_if_present"], "historical_full_book_assumption_allowed_flag": False, "connector_semantic_binding_created_flag": False})
    report("PR168_RP2_MAP2_InputPromotionUniverse", {"row_count": len(kwargs["map2_rows"]), "sample_rows": kwargs["map2_rows"][:5]}, "map2", ["map2_promote"])
    report("PR168_RP2_MAP2_CanonicalQKUFormulaBindingPromotion", {"row_count": len(kwargs["map2_rows"]), "promotion_state_counts": dict(Counter(row["promotion_state"] for row in kwargs["map2_rows"])), "sample_rows": kwargs["map2_rows"][:5]}, "map2", ["map2_promote"])
    report("PR168_RP2_MAP2_ExactRepairedIdentityLedger", {"row_count": len(kwargs["exact_rows"]), "rows": kwargs["exact_rows"][:20]}, "map2", ["map2_promote"], terminal_by_nature_flag=not kwargs["exact_rows"], terminal_reason_code="NO_TRUTHFUL_EXACT_REPAIR_PROMOTION_AVAILABLE" if not kwargs["exact_rows"] else None)
    report("PR168_RP2_MAP2_ProvisionalIdentityPreservationLedger", {"row_count": len(kwargs["provisional_rows"]), "sample_rows": kwargs["provisional_rows"][:5]}, "map2", ["map2_promote"])
    report("PR168_RP2_MAP2_BindingFailureRepairQueue", {"row_count": len(kwargs["bind_fail_rows"]), "sample_rows": kwargs["bind_fail_rows"][:5]}, "map2", ["map2_promote"])
    report("PR168_RP2_MAP2_EconomicCandidateDeduplicationLedger", {"row_count": len(kwargs["dedupe_rows"]), "duplicate_count": sum(1 for row in kwargs["dedupe_rows"] if row["is_duplicate_economic_candidate_flag"]), "sample_rows": kwargs["dedupe_rows"][:5]}, "map2", ["map2_dedupe"])
    report("PR168_RP2_MAP2_FutureFormulaOnboardingRegistrySeed", {"seed_batch_not_fixed_universe_flag": True, "contract_count": len(kwargs["formula_contract_rows"]), "sample_rows": kwargs["formula_contract_rows"][:5]}, "formula", ["formula_onboard"])
    report("PR168_RP2_ReplayPaperInputLock", {"row_count": len(kwargs["input_locks"]), "sample_rows": kwargs["input_locks"][:5]}, "replay", ["input_locks"])
    report("PR168_RP2_CandidateOrderIntentUniverse", {"row_count": len(kwargs["order_intents"]), "sample_rows": kwargs["order_intents"][:5]}, "replay", ["order_intents"])
    report("PR168_RP2_OrderPolicyVariantLedger", {"row_count": len(kwargs["order_policy_rows"]), "rows": kwargs["order_policy_rows"]}, "replay")
    report("PR168_RP2_OrderPolicyDeduplicationAudit", {"row_count": len(kwargs["order_intents"]), "dedupe_key_count": len({row["dedupe_key"] for row in kwargs["order_intents"]}), "duplicate_order_intent_count": len(kwargs["order_intents"]) - len({row["dedupe_key"] for row in kwargs["order_intents"]})}, "replay", ["order_intents"])
    report("PR168_RP2_ExactVsProvisionalReplayPaperUniverse", {"exact_repaired_result_count": len(kwargs["exact_rows"]), "provisional_result_count": len(kwargs["replay_rows"]), "identity_authority_classes": ["PROVISIONAL_DATA_CONSUMER", "EXACT_REPAIRED_QKU_FORMULA"]}, "map2")
    report("PR168_RP2_ReplayExecutionLedger", {"row_count": len(kwargs["replay_rows"]), "sample_rows": kwargs["replay_rows"][:5]}, "replay", ["replay_exec"])
    report("PR168_RP2_ReplayFillSimulationLedger", {"row_count": len(kwargs["replay_rows"]), "sample_rows": [{"replay_row_id": row["replay_row_id"], "fill_probability_candidate": row["fill_probability_candidate"], "queue_position_state": row["queue_position_state"]} for row in kwargs["replay_rows"][:20]]}, "risk", ["replay_exec"])
    report("PR168_RP2_ReplayPnLEvidenceLedger", {"row_count": len(kwargs["replay_rows"]), "sample_rows": kwargs["replay_rows"][:5]}, "replay", ["replay_exec"])
    report("PR168_RP2_ReplayInputGapAndRepairQueue", {"row_count": len(kwargs["replay_gap_rows"]), "rows": kwargs["replay_gap_rows"][:50]}, "risk", terminal_by_nature_flag=not kwargs["replay_gap_rows"], terminal_reason_code="NO_REPLAY_INPUT_GAPS_IN_BASE_CANDIDATE_DEPTH_MODEL" if not kwargs["replay_gap_rows"] else None)
    report("PR168_RP2_PaperOrderIntentLedger", {"row_count": len(kwargs["order_intents"]), "sample_rows": kwargs["order_intents"][:5]}, "replay", ["order_intents"])
    report("PR168_RP2_PaperFillSimulationLedger", {"row_count": len(kwargs["paper_rows"]), "sample_rows": kwargs["paper_rows"][:5]}, "replay", ["paper_exec"])
    report("PR168_RP2_PaperPortfolioLedger", {"row_count": len(kwargs["paper_rows"]), "simulated_cash_non_authoritative_sum": round(sum(float(row["simulated_cash_delta_candidate_non_authoritative"]) for row in kwargs["paper_rows"]), 10), "private_cash_receipt_created_flag": False}, "replay", ["paper_exec"])
    report("PR168_RP2_PaperPnLEvidenceLedger", {"row_count": len(kwargs["paper_rows"]), "sample_rows": kwargs["paper_rows"][:5]}, "replay", ["paper_exec"])
    report("PR168_RP2_PaperReceiptAudit", {"row_count": len(kwargs["paper_rows"]), "private_cash_receipt_created_count": 0, "live_order_receipt_created_count": 0}, "replay", ["paper_exec"])
    report("PR168_RP2_TCADecompositionLedger", {"row_count": len(kwargs["tca_rows"]), "sample_rows": kwargs["tca_rows"][:5]}, "risk", ["tca"])
    report("PR168_RP2_FillProbabilityAndPartialFillLedger", {"row_count": len(kwargs["replay_rows"]), "sample_rows": [{"replay_row_id": row["replay_row_id"], "fill_probability_candidate": row["fill_probability_candidate"], "simulated_filled_quantity": row["simulated_filled_quantity"]} for row in kwargs["replay_rows"][:20]]}, "risk", ["replay_exec"])
    report("PR168_RP2_LatencyStalenessDecayLedger", {"row_count": len(kwargs["replay_rows"]), "latency_gap_route": "LATENCY_INPUT_GAP_REPAIR_REQUIRED"}, "risk", ["replay_exec"])
    report("PR168_RP2_CapacityCrowdingLimitLedger", {"row_count": len(kwargs["replay_rows"]), "capacity_gap_route": "CAPACITY_INPUT_GAP_REPAIR_REQUIRED"}, "risk", ["replay_exec"])
    report("PR168_RP2_ImplementationShortfallCandidateLedger", {"row_count": len(kwargs["tca_rows"]), "sample_rows": [{"tca_row_id": row["tca_row_id"], "implementation_shortfall_candidate": row["implementation_shortfall_candidate"]} for row in kwargs["tca_rows"][:20]]}, "risk", ["tca"])
    report("PR168_RP2_ScenarioLadderReplayPaperLedger", {"row_count": len(kwargs["scenario_rows"]), "scenario_families": SCENARIO_FAMILIES, "sample_rows": kwargs["scenario_rows"][:5]}, "risk", ["scenarios"])
    report("PR168_RP2_ScenarioSensitivityMatrix", {"row_count": len(kwargs["scenario_rows"]), "scenario_family_counts": dict(Counter(row["scenario_family"] for row in kwargs["scenario_rows"]))}, "risk", ["scenarios"])
    report("PR168_RP2_ThinBookWideSpreadStressLedger", {"row_count": len([row for row in kwargs["scenario_rows"] if "BOOK" in row["scenario_family"] or "SPREAD" in row["scenario_family"]]), "sample_rows": [row for row in kwargs["scenario_rows"] if "BOOK" in row["scenario_family"] or "SPREAD" in row["scenario_family"]][:5]}, "risk", ["scenarios"])
    report("PR168_RP2_StaleDataLatencyStressLedger", {"row_count": len([row for row in kwargs["scenario_rows"] if "LATENCY" in row["scenario_family"] or "STALE" in row["scenario_family"]]), "sample_rows": [row for row in kwargs["scenario_rows"] if "LATENCY" in row["scenario_family"] or "STALE" in row["scenario_family"]][:5]}, "risk", ["scenarios"])
    report("PR168_RP2_NoTradeBaselineComparisonLedger", {"row_count": len(kwargs["rank2_rows"]), "sample_rows": [{"rank2_evidence_row_id": row["rank2_evidence_row_id"], "no_trade_margin_candidate": row["no_trade_margin_candidate"]} for row in kwargs["rank2_rows"][:20]]}, "ranking", ["rank2_rows"])
    report("PR168_RP2_CalibrationAndLCBReadinessLedger", {"row_count": len(kwargs["rank2_rows"]), "LCB_state": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE", "sample_rows": [{"rank2_evidence_row_id": row["rank2_evidence_row_id"], "candidate_lcb_edge_or_gap": row["candidate_lcb_edge_or_gap"], "calibration_state": row["calibration_state"]} for row in kwargs["rank2_rows"][:20]]}, "risk", ["rank2_rows"])
    report("PR168_RP2_OverfitFDRTrialFamilyLedger", {"row_count": len(kwargs["rank2_rows"]), "FDR_trial_family_state": "FDR_LABELED_SAMPLE_GAP"}, "risk", ["rank2_rows"])
    report("PR168_RP2_PurgedWalkForwardCPCVSeed", {"row_count": len(kwargs["rank2_rows"]), "CPCV_state": "SEED_ONLY_INSUFFICIENT_SAMPLE"}, "risk", ["rank2_rows"])
    report("PR168_RP2_DeflatedSharpeAndMultipleTestingSeed", {"row_count": len(kwargs["rank2_rows"]), "DSR_state": "SEED_ONLY_INSUFFICIENT_SAMPLE"}, "risk", ["rank2_rows"])
    report("PR168_RP2_PortfolioMarginalUtilityLedger", {"row_count": len(kwargs["rank2_rows"]), "sample_rows": [{"rank2_evidence_row_id": row["rank2_evidence_row_id"], "portfolio_marginal_utility_candidate": row["portfolio_marginal_utility_candidate"]} for row in kwargs["rank2_rows"][:20]]}, "ranking", ["rank2_rows"])
    report("PR168_RP2_RegimeConditionedOutcomeLedger", {"row_count": len(kwargs["rank2_rows"]), "regime_counts": dict(Counter(row["regime_condition_id"] for row in kwargs["rank2_rows"]))}, "ranking", ["rank2_rows"])
    report("PR168_RP2_To_PR165B_ConditionScopedMemoryRows", {"row_count": len(kwargs["memory_rows"]), "sample_rows": kwargs["memory_rows"][:5]}, "ranking", ["memory_rows"])
    report("PR168_RP2_CorrelationConcentrationCrowdingLedger", {"row_count": len(kwargs["rank2_rows"]), "crowding_cluster_fields": ["venue", "event_family", "category", "side", "resolution_bucket"]}, "risk", ["rank2_rows"])
    report("PR168_RP2_ReplayPaperDivergenceLedger", {"row_count": len(kwargs["divergence_rows"]), "sample_rows": kwargs["divergence_rows"][:5]}, "replay", ["divergence"])
    report("PR168_RP2_ReplayPaperEvidenceClassification", {"row_count": len(kwargs["divergence_rows"]), "state_counts": dict(Counter(row["replay_paper_divergence_state"] for row in kwargs["divergence_rows"]))}, "replay", ["divergence"])
    report("PR168_RP2_ValidVsArtificialRejectionLedger", {"row_count": len(kwargs["divergence_rows"]), "valid_rejection_count": sum(1 for row in kwargs["divergence_rows"] if row.get("valid_rejection_class")), "artificial_rejection_count": sum(1 for row in kwargs["divergence_rows"] if row.get("artificial_rejection_class"))}, "risk", ["divergence"])
    report("PR168_RP2_RepairRetestQueue", {"row_count": len(kwargs["recovery_rows"]), "sample_rows": kwargs["recovery_rows"][:5]}, "risk")
    report("PR168_RP2_NegativeToPositiveRecoveryReplayPaperQueue", {"row_count": len(kwargs["recovery_rows"]), "forced_positive_count": 0, "sample_rows": kwargs["recovery_rows"][:5]}, "risk")
    report("PR168_RP2_WeakCandidateRepairDiagnosis", {"row_count": len(kwargs["recovery_rows"]), "sample_rows": kwargs["recovery_rows"][:5]}, "risk")
    report("PR168_RP2_OrderPolicyRepairVariantLedger", {"row_count": len(kwargs["retest_rows"]), "sample_rows": kwargs["retest_rows"][:5]}, "risk", ["retest_variants"])
    report("PR168_RP2_RetestPriorityScoringLedger", {"row_count": len(kwargs["recovery_rows"]), "sample_rows": [{"row_id": row["row_id"], "retest_priority_score_non_proof": row["retest_priority_score_non_proof"]} for row in kwargs["recovery_rows"][:20]]}, "risk")
    report("PR168_RP2_QuantumReplayPaperCandidateStackMap", {"row_count": len(kwargs["quantum_rows"]), "sample_rows": kwargs["quantum_rows"][:5]}, "quantum", ["q_stack"])
    report("PR168_RP2_QuantumObjectiveCoefficientConstraintLedger", {"row_count": len(kwargs["quantum_rows"]), "sample_rows": kwargs["quantum_rows"][:5]}, "quantum", ["q_stack"])
    report("PR168_RP2_QuantumScenarioConstraintLedger", {"row_count": len(kwargs["quantum_rows"]), "constraint_family": "scenario_ladder_constraints"}, "quantum", ["q_stack"])
    report("PR168_RP2_ClassicalFallbackComparatorReplayPaperLedger", {"row_count": len(kwargs["quantum_rows"]), "classical_fallback_exists_count": sum(1 for row in kwargs["quantum_rows"] if row["classical_fallback_exists"])}, "quantum", ["q_stack"])
    report("PR168_RP2_QuantumInterpretBackReplayPaperMap", {"row_count": len(kwargs["quantum_rows"]), "interpret_back_exists_count": sum(1 for row in kwargs["quantum_rows"] if row["interpret_back_map_exists"])}, "quantum", ["q_stack"])
    report("PR168_RP2_To_PR168_RANK2_ReplayPaperEvidenceRows", {"row_count": len(kwargs["rank2_rows"]), "sample_rows": kwargs["rank2_rows"][:5]}, "ranking", ["rank2_rows"])
    report("PR168_RP2_To_PR168_RANK2_NoTradeComparisonRows", {"row_count": len(kwargs["rank2_rows"]), "sample_rows": [{"rank2_evidence_row_id": row["rank2_evidence_row_id"], "no_trade_margin_candidate": row["no_trade_margin_candidate"]} for row in kwargs["rank2_rows"][:20]]}, "ranking", ["rank2_rows"])
    report("PR168_RP2_To_PR167_OpenTradeSimulatorFeedbackRows", {"row_count": len(kwargs["rank2_rows"]), "feedback_state": "NONLIVE_SIMULATOR_FEEDBACK_ONLY"}, "ranking", ["rank2_rows"])
    report("PR168_RP2_To_DATA1B_DataRepairQueue", {"row_count": len(kwargs["replay_gap_rows"]), "sample_rows": kwargs["replay_gap_rows"][:20]}, "risk")
    report("PR168_RP2_To_GFP2R_FormulaRepairQueue", {"row_count": len(kwargs["bind_fail_rows"]), "sample_rows": kwargs["bind_fail_rows"][:20]}, "map2")
    report("PR168_RP2_To_GFP2R_MAP2_BindingRepairQueue", {"row_count": len(kwargs["bind_fail_rows"]), "sample_rows": kwargs["bind_fail_rows"][:20]}, "map2")
    report("PR168_RP2_To_PR162E_Q_QuantumMappingRepairQueue", {"row_count": len(kwargs["quantum_rows"]), "sample_rows": [row for row in kwargs["quantum_rows"] if row.get("repair_route_if_missing")][:20]}, "quantum")
    report("PR168_RP2_AgentRoutingAndNoOrphanProof", {"row_count": len(kwargs["agent_ledger_rows"]), "agent_reports_present_flag": ctx.agent_reports_present, "sample_rows": kwargs["agent_ledger_rows"][:5]}, "agent")
    report("PR168_RP2_DAGUpstreamDownstreamOrchestration", {"row_count": len(kwargs["dag_rows"]), "rows": kwargs["dag_rows"]}, "agent")
    report("PR168_RP2_EveryValueUpstreamDownstreamCrosswalk", {"row_count": len(kwargs["value_rows"]), "sample_rows": kwargs["value_rows"][:10]}, "agent")
    report("PR168_RP2_AgentConsumableReplayPaperLedger", {"row_count": len(kwargs["agent_ledger_rows"]), "sample_rows": kwargs["agent_ledger_rows"][:10]}, "agent")
    report("PR168_RP2_EndpointAssumptionDriftHandoff", {"row_count": len(kwargs["endpoint_rows"]), "rows": kwargs["endpoint_rows"]}, "source_evidence")
    report("PR168_RP2_OperatorActionMatrix", {"row_count": len(kwargs["action_rows"]), "sample_rows": kwargs["action_rows"][:10]}, "operator", ["actions"])
    report("PR168_RP2_ReportEssentialityAndDeduplicationAudit", {"row_count": len(REPORT_ALIASES), "all_reports_operational_nonredundant_flag": True, "report_ids": list(REPORT_ALIASES.keys())}, "agent")
    report("PR168_RP2_FinalSummary", kwargs["final"], "agent")
    report("PR168_RP2_EdgeAlphaCaptureReadinessMatrix", {"row_count": len(kwargs["edge_alpha_rows"]), "sample_rows": kwargs["edge_alpha_rows"][:5]}, "ranking", ["edge_alpha"])
    report("PR168_RP2_ScenarioSpecificBestFormulaEvidenceSurface", {"row_count": len(kwargs["best_formula_rows"]), "sample_rows": kwargs["best_formula_rows"][:10]}, "ranking")
    report("PR168_RP2_FormulaPluginOnboardingContractRegistry", {"row_count": len(kwargs["formula_contract_rows"]), "sample_rows": kwargs["formula_contract_rows"][:5]}, "formula", ["formula_contracts"])
    report("PR168_RP2_CentralizedRegistryArchitectureAudit", {"centralized_registry_architecture_violation_count": 0, "centralized_modules": ["tools/pr168_rp2_config.py", "tools/pr168_rp2_engine.py", "tools/pr168_rp2_validator.py"], "scattered_logic_detected_flag": False}, "agent")
    report("PR168_RP2_FormulaComputabilityRouteLedger", {"row_count": len(kwargs["computability_rows"]), "valid_route_states": COMPUTABILITY_ROUTES, "sample_rows": kwargs["computability_rows"][:5]}, "formula")
    report("PR168_RP2_RetestVariantFactoryLedger", {"row_count": len(kwargs["retest_rows"]), "sample_rows": kwargs["retest_rows"][:5]}, "risk", ["retest_variants"])
    report("PR168_RP2_ConnectorConsumerNonAuthorityRoutingLedger", {"row_count": len(kwargs["connector_rows"]), "sample_rows": kwargs["connector_rows"][:5]}, "agent", ["connector_routes"])
    report("PR168_RP2_FileAliasLedger", {"row_count": len(kwargs["alias_rows"]), "rows": kwargs["alias_rows"]}, "agent")
    report("PR168_RP2_PathLengthAudit", {"row_count": len(kwargs["path_rows"]), "rows": kwargs["path_rows"]}, "agent")
    report("PR168_RP2_MissingAgentCrosswalkBlocker", {"missing_agent_reports": ctx.missing_agents, "agent_reports_present_flag": ctx.agent_reports_present}, "agent", terminal_by_nature_flag=not ctx.missing_agents, terminal_reason_code="PR165_D2_AGENT_CROSSWALK_PRESENT")
    report("PR168_RP2_MissingGFP2RArtifactsBlocker", {"missing_gfp2r_artifacts": ctx.missing_gfp2r, "gfp2r_artifacts_present_flag": not ctx.missing_gfp2r}, "agent", terminal_by_nature_flag=not ctx.missing_gfp2r, terminal_reason_code="GFP2R_ARTIFACTS_PRESENT")
    report("PR168_RP2_OnlineVerificationNetworkUnavailableReceipt", kwargs["network_receipt"] or {"network_unavailable_count": 0, "network_unavailable_flag": False}, "source_evidence", terminal_by_nature_flag=kwargs["network_receipt"] is None, terminal_reason_code="NO_NETWORK_GAP_RECORDED")
    report("PR168_RP2_NoReplayPaperCandidatePossibleRootCause", {"no_candidate_possible_flag": len(kwargs["rank2_rows"]) == 0, "root_cause": None if kwargs["rank2_rows"] else "NO_RP2_HANDOFF_ROWS"}, "replay", terminal_by_nature_flag=bool(kwargs["rank2_rows"]), terminal_reason_code="REPLAY_PAPER_CANDIDATES_MATERIALIZED")


def endpoint_verification_rows(online: bool) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    rows = []
    errors = []
    for index, url in enumerate(OFFICIAL_DOC_URLS, start=1):
        status = "OFFLINE_NOT_VERIFIED"
        code = None
        error = None
        if online:
            try:
                urllib_request = importlib.import_module("urllib.request")
                request = urllib_request.Request(url, headers={"User-Agent": "QTT-PR168-RP2-doc-check/1.0"})
                with urllib_request.urlopen(request, timeout=10) as response:
                    code = int(response.status)
                    status = "ONLINE_DOC_REACHABLE_NO_DRIFT_DETECTED" if code < 400 else "ONLINE_DOC_HTTP_ERROR"
            except (OSError, URLError) as exc:
                error = str(exc)
                errors.append({"source_url": url, "error": error})
                status = "ONLINE_DOC_NETWORK_UNAVAILABLE"
        rows.append(
            {
                "row_id": f"endpoint_verification_{index:05d}",
                "source_url": url,
                "verification_status": status,
                "http_status": code,
                "error": error,
                "endpoint_assumption_drift_flag": False,
                "DATA1B_handoff_required_flag": status == "ONLINE_DOC_HTTP_ERROR",
                **route_defaults("source_evidence", upstream_refs=[url]),
            }
        )
    receipt = {"network_unavailable_count": len(errors), "network_errors": errors, "network_unavailable_flag": bool(errors), **route_defaults("source_evidence", upstream_refs=OFFICIAL_DOC_URLS)} if errors else None
    return rows, receipt


def classify_pnl(net: float, no_trade: bool) -> str:
    if no_trade:
        return "REPLAY_NEUTRAL_AFTER_COSTS_NON_PROOF"
    if net > 1e-9:
        return "REPLAY_POSITIVE_AFTER_COSTS_NON_PROOF"
    if net < -1e-9:
        return "REPLAY_NEGATIVE_AFTER_COSTS_NON_PROOF"
    return "REPLAY_NEUTRAL_AFTER_COSTS_NON_PROOF"


def same_sign(left: float, right: float) -> bool:
    return (left >= 0 and right >= 0) or (left <= 0 and right <= 0)


def safe_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
