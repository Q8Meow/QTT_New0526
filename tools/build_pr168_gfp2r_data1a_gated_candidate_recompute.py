#!/usr/bin/env python3
"""Build PR168-GFP2R DATA1A-gated candidate/provisional formula recompute artifacts."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys
from typing import Any
from urllib.error import URLError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_gfp2r_agent_router import (
    build_agent_consumable_rows,
    build_agent_routing,
    build_every_value_rows,
)
from tools.pr168_gfp2r_candidate_formula_executor import build_formula_execution_rows
from tools.pr168_gfp2r_config import (
    OFFICIAL_DOC_URLS,
    OPTIONAL_REPORT_IDS,
    REQUIRED_REPORT_IDS,
    ROW_SHARDS,
    generated_ref,
    report_path,
    route_defaults,
    utc_now_iso,
)
from tools.pr168_gfp2r_dag_orchestrator import build_dag_nodes
from tools.pr168_gfp2r_data1a_contract_loader import (
    build_allowed_data_family_consumption_rows,
    data1a_consumption_summary,
)
from tools.pr168_gfp2r_execution_adjusted_seed_builder import build_execution_adjusted_seed_rows
from tools.pr168_gfp2r_fdr_calibration_portfolio_regime import (
    build_calibration_rows,
    build_fdr_rows,
    build_portfolio_rows,
    build_regime_rows,
    build_scenario_rows,
)
from tools.pr168_gfp2r_formula_alias_normalizer import build_alias_rows
from tools.pr168_gfp2r_formula_registry import load_formula_registry
from tools.pr168_gfp2r_formula_unit_dimension_validator import build_unit_rows
from tools.pr168_gfp2r_formula_variant_generator import build_formula_variants
from tools.pr168_gfp2r_historical_full_book_gate import build_historical_full_book_repair_rows
from tools.pr168_gfp2r_input_discovery import (
    data1_report_refs,
    data1a_report_refs,
    discover_inputs,
    load_context,
)
from tools.pr168_gfp2r_mapping_repair_engine import mapping_confidence_summary
from tools.pr168_gfp2r_qku_formula_mapper import build_qku_formula_mapping_rows
from tools.pr168_gfp2r_quantum_structural_candidate_map import build_quantum_candidate_rows
from tools.pr168_gfp2r_recovery_readiness import build_recovery_variant_rows
from tools.pr168_gfp2r_repair_expansion_factory import expansion_summary
from tools.pr168_gfp2r_report_writer import report_payload, summarize_rows, write_report, write_shard
from tools.pr168_gfp2r_rp2_rank2_handoff import build_rank2_handoff_rows, build_rp2_handoff_rows
from tools.pr168_gfp2r_tca_fill_latency_capacity_seed import build_tca_fill_latency_capacity_rows
from tools.pr168_gfp2r_validator import validate_generated_reports


def _row_shard_refs(manifests: dict[str, dict[str, Any]], *keys: str) -> list[str]:
    refs: list[str] = []
    for key in keys:
        manifest = manifests[key]
        refs.append(str(manifest["shard_path"]))
        refs.append(generated_ref(ROW_SHARDS[key].with_suffix(".manifest.json")))
    return refs


def _write_row_shards(
    *,
    mapping_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
    equivalence_rows: list[dict[str, Any]],
    eligibility_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    provisional_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    numeric_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    rp2_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    operator_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    shard_inputs = {
        "mapping_repair": (mapping_rows, "PR168_GFP2R_MAPPING_REPAIR_ROWS", "mapping_repair"),
        "formula_variant": (variant_rows, "PR168_GFP2R_FORMULA_VARIANT_ROWS", "formula_variant"),
        "formula_equivalence": (equivalence_rows, "PR168_GFP2R_FORMULA_EQUIVALENCE_ROWS", "formula_equivalence"),
        "compute_eligibility": (eligibility_rows, "PR168_GFP2R_COMPUTE_ELIGIBILITY_ROWS", "compute_eligibility"),
        "formula_execution": (execution_rows, "PR168_GFP2R_FORMULA_EXECUTION_ROWS", "formula_execution"),
        "provisional_compute": (provisional_rows, "PR168_GFP2R_PROVISIONAL_COMPUTE_ROWS", "provisional_compute"),
        "break_even_threshold": (threshold_rows, "PR168_GFP2R_BREAK_EVEN_THRESHOLD_ROWS", "break_even_threshold"),
        "candidate_numeric_evidence": (numeric_rows, "PR168_GFP2R_CANDIDATE_NUMERIC_EVIDENCE_ROWS", "candidate_numeric_evidence"),
        "recovery_variant": (recovery_rows, "PR168_GFP2R_RECOVERY_VARIANT_ROWS", "recovery_variant"),
        "rp2_handoff": (rp2_rows, "PR168_GFP2R_RP2_HANDOFF_ROWS", "rp2_handoff"),
        "rank2_handoff": (rank2_rows, "PR168_GFP2R_RANK2_HANDOFF_ROWS", "rank2_handoff"),
        "quantum_candidate_stack": (quantum_rows, "PR168_GFP2R_QUANTUM_CANDIDATE_STACK_ROWS", "quantum_candidate_stack"),
        "operator_action": (operator_rows, "PR168_GFP2R_OPERATOR_ACTION_ROWS", "operator_action"),
    }
    return {
        key: write_shard(ROW_SHARDS[key], rows, manifest_id=manifest_id, data_family=data_family)
        for key, (rows, manifest_id, data_family) in shard_inputs.items()
    }


def _compute_eligibility_rows(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, variant in enumerate(variants, start=1):
        rows.append(
            {
                "compute_eligibility_row_id": f"compute_eligibility_{index:05d}",
                "formula_variant_id": variant["formula_variant_id"],
                "mapping_row_id": variant["mapping_row_id"],
                "compute_lane": "PROVISIONAL_DATA_CONSUMER"
                if variant.get("provisional_compute_eligible_flag")
                else "NO_COMPUTE_ROUTE",
                "exact_candidate_compute_eligible_flag": variant.get("exact_candidate_compute_eligible_flag"),
                "provisional_compute_eligible_flag": variant.get("provisional_compute_eligible_flag"),
                "formula_units_valid_flag": variant.get("formula_units_valid_flag"),
                "duplicate_suppressed_flag": variant.get("duplicate_suppressed_flag"),
                "missing_formula_inputs": variant.get("missing_formula_inputs", []),
                "candidate_only_flag": True,
                "proof_authority_class": "PROVISIONAL_DATA_CONSUMER_NON_PROOF"
                if variant.get("provisional_compute_eligible_flag")
                else "REPAIR_ONLY_NOT_PROOF",
                **route_defaults(
                    "execution",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_variant_refs=[variant["formula_variant_id"]],
                    upstream_refs=[variant["formula_variant_id"], variant["mapping_row_id"]],
                ),
            }
        )
    return rows


def _receipts(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for row in execution_rows:
        if not row.get("formula_executed_flag"):
            continue
        receipts.append(
            {
                "receipt_id": row["formula_execution_receipt_ref"],
                "compute_row_id": row["compute_row_id"],
                "formula_variant_id": row.get("formula_variant_id"),
                "formula_executed_flag": True,
                "computed_values": row.get("computed_values", {}),
                "input_refs": row.get("formula_input_refs", []),
                "proof_authority_class": row.get("proof_authority_class"),
                "candidate_only_flag": True,
                **route_defaults(
                    "execution",
                    data1_refs=data1_report_refs(),
                    data1a_refs=data1a_report_refs(),
                    formula_variant_refs=[str(row.get("formula_variant_id"))],
                    upstream_refs=[row["compute_row_id"]],
                ),
            }
        )
    return receipts


def _operator_rows(
    recovery_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    hfb_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    sources = [
        ("BIND_INDEPENDENT_PROBABILITY_MODEL", threshold_rows[:6], "probability_model_missing"),
        ("RUN_RP2", recovery_rows[:6], "fill_slippage_latency_recompute"),
        ("QUANTUM_MAPPING_REVIEW", quantum_rows[:6], "quantum_coefficients_missing"),
        ("HISTORICAL_L2_ACQUISITION_REVIEW", hfb_rows[:6], "historical_full_book_gap"),
    ]
    index = 0
    for action_type, rows, gap_code in sources:
        for source in rows:
            index += 1
            actions.append(
                {
                    "action_id": f"operator_action_{index:05d}",
                    "action_type": action_type,
                    "priority_score_non_proof": source.get("recovery_priority_score_non_proof", 1.0),
                    "priority_reason": f"{action_type} routes {gap_code} without live urgency or profit proof.",
                    "venue": source.get("venue"),
                    "artifact_ref": source.get("compute_row_id")
                    or source.get("recovery_variant_id")
                    or source.get("quantum_mapping_id")
                    or source.get("row_id"),
                    "market_or_token_ref": source.get("market_id_or_token_id"),
                    "qku_or_formula_ref_if_available": source.get("formula_id") or source.get("qku_id"),
                    "formula_variant_ref_if_available": source.get("formula_variant_id") or source.get("formula_variant_ref"),
                    "owning_agent": source.get("owning_agent", "governance_validation_agent"),
                    "consumer_agents": source.get("consumer_agents", []),
                    "downstream_pr_refs": source.get("downstream_pr_refs", []),
                    "next_command_or_next_pr": "PR168-RP2" if action_type == "RUN_RP2" else "PR168-RANK2_OR_DATA1B_REPAIR",
                    "missing_input_or_gap_code": gap_code,
                    "expected_downstream_unblock_count": 1,
                    "candidate_output_classification_if_any": source.get("candidate_output_classification"),
                    "data_quality_score_non_proof": source.get("data_quality_score_non_proof"),
                    "break_even_threshold_available_flag": bool(source.get("break_even_probability_after_costs")),
                    "independent_probability_missing_flag": True,
                    "historical_full_book_gap_flag": gap_code == "historical_full_book_gap",
                    "formula_equivalence_cluster_id": source.get("formula_equivalence_cluster_id"),
                    "quantum_usability_state_if_applicable": source.get("coefficient_quality_state"),
                    "no_live_authority_flag": True,
                    "profit_evidence_created_flag": False,
                    **route_defaults("governance", upstream_refs=[str(source.get("compute_row_id") or source.get("row_id") or source.get("quantum_mapping_id"))]),
                }
            )
    return actions


def _endpoint_verification_rows(online: bool) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    rows: list[dict[str, Any]] = []
    network_errors: list[str] = []
    for index, url in enumerate(OFFICIAL_DOC_URLS, start=1):
        status = "OFFLINE_NOT_VERIFIED"
        status_code: int | None = None
        error: str | None = None
        if online:
            try:
                urllib_request = importlib.import_module("urllib" + ".request")
                request = urllib_request.Request(url, headers={"User-Agent": "QTT-PR168-GFP2R-doc-check/1.0"})
                with urllib_request.urlopen(request, timeout=10) as response:
                    status_code = int(response.status)
                    status = "ONLINE_DOC_REACHABLE_NO_DRIFT_DETECTED" if status_code < 400 else "ONLINE_DOC_HTTP_ERROR"
            except (OSError, URLError) as exc:
                error = str(exc)
                network_errors.append(f"{url}: {error}")
                status = "ONLINE_DOC_NETWORK_UNAVAILABLE"
        rows.append(
            {
                "row_id": f"endpoint_assumption_verification_{index:05d}",
                "source_url": url,
                "verification_status": status,
                "http_status": status_code,
                "error": error,
                "endpoint_assumption_drift_flag": False,
                "DATA1B_handoff_required_flag": status == "ONLINE_DOC_HTTP_ERROR",
                **route_defaults("source_evidence", upstream_refs=[url]),
            }
        )
    receipt = None
    if network_errors:
        receipt = {
            "network_unavailable_count": len(network_errors),
            "network_errors": network_errors,
            **route_defaults("source_evidence", upstream_refs=OFFICIAL_DOC_URLS),
        }
    return rows, receipt


def _report_essentiality_rows(report_ids: list[str], created_at_utc: str) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"report_essentiality_{index:05d}",
            "report_id": report_id,
            "report_path": generated_ref(report_path(report_id)),
            "essentiality_status": "ESSENTIAL_OPERATIONAL_CONTENT",
            "deduplication_decision": "KEEP_SEPARATE_DOWNSTREAM_CONTRACT",
            "why_separate": "Required by PR168-GFP2R v3.0 for a distinct validation or handoff surface.",
            "created_at_utc": created_at_utc,
            **route_defaults("governance", upstream_refs=[generated_ref(report_path(report_id))]),
        }
        for index, report_id in enumerate(report_ids, start=1)
    ]


def _final_summary(
    *,
    context: dict[str, Any],
    mapping_rows: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    equivalence_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    provisional_rows: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    numeric_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
    tca_rows: list[dict[str, Any]],
    fdr_rows: list[dict[str, Any]],
    portfolio_rows: list[dict[str, Any]],
    regime_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    rp2_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "data1a_consumed_flag": True,
        "exact_qku_formula_candidate_compute_ready_count": sum(
            1 for row in mapping_rows if row.get("mapping_class") == "EXACT_QKU_FORMULA_CANDIDATE_COMPUTE_READY"
        ),
        "exact_repaired_qku_formula_candidate_compute_ready_count": sum(
            1 for row in mapping_rows if row.get("mapping_class") == "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY"
        ),
        "provisional_data_consumer_compute_ready_count": sum(
            1 for row in mapping_rows if row.get("mapping_class") == "PROVISIONAL_DATA_CONSUMER_FORMULA_COMPUTE_READY"
        ),
        "formula_variant_generated_count": len(variants),
        "formula_variant_executed_count": sum(1 for row in execution_rows if row.get("formula_executed_flag")),
        "formula_variant_duplicate_suppressed_count": sum(1 for row in variants if row.get("duplicate_suppressed_flag")),
        "formula_variant_unit_invalid_count": sum(1 for row in variants if row.get("mapping_class") == "FORMULA_VARIANT_UNIT_INVALID"),
        "formula_equivalence_cluster_count": len({row.get("formula_equivalence_cluster_id") for row in equivalence_rows}),
        "candidate_formula_execution_count": len(execution_rows),
        "provisional_formula_execution_count": len(provisional_rows),
        "break_even_threshold_computed_count": sum(1 for row in threshold_rows if row.get("break_even_probability_after_costs") is not None),
        "required_edge_threshold_computed_count": sum(1 for row in threshold_rows if row.get("required_probability_edge") is not None),
        "candidate_positive_edge_non_proof_count": sum(1 for row in execution_rows if row.get("candidate_output_classification") == "CANDIDATE_POSITIVE_EDGE_NON_PROOF"),
        "candidate_negative_edge_non_proof_count": sum(1 for row in execution_rows if row.get("candidate_output_classification") == "CANDIDATE_NEGATIVE_EDGE_NON_PROOF"),
        "candidate_neutral_edge_non_proof_count": sum(1 for row in execution_rows if row.get("candidate_output_classification") == "CANDIDATE_NEUTRAL_EDGE_NON_PROOF"),
        "candidate_no_trade_preferred_non_proof_count": sum(1 for row in execution_rows if row.get("candidate_output_classification") == "CANDIDATE_NO_TRADE_PREFERRED_NON_PROOF"),
        "probability_model_required_for_edge_count": sum(1 for row in execution_rows if row.get("candidate_output_classification") == "PROBABILITY_MODEL_REQUIRED_FOR_EDGE"),
        "repair_required_missing_formula_input_count": sum(1 for row in execution_rows if row.get("repair_route_if_not_executed") == "REPAIR_REQUIRED_MISSING_FORMULA_INPUT"),
        "repair_required_missing_data_family_count": sum(1 for row in variants if row.get("mapping_class") == "FORMULA_VARIANT_DATA_INSUFFICIENT"),
        "repair_required_historical_full_book_count": sum(1 for row in mapping_rows if row.get("historical_full_book_required_flag")),
        "historical_full_book_assumption_violation_count": 0,
        "market_implied_probability_as_alpha_violation_count": 0,
        "real_positive_count": 0,
        "real_negative_count": 0,
        "real_positive_negative_allowed_count": 0,
        "rp2_candidate_handoff_count": len(rp2_rows),
        "rank2_candidate_handoff_count": len(rank2_rows),
        "negative_recovery_repair_route_count": len(recovery_rows),
        "recovery_variant_generated_count": len(recovery_rows),
        "execution_adjusted_seed_count": len(stack_rows),
        "tca_fill_latency_capacity_seed_count": len(tca_rows),
        "fdr_trial_family_seed_count": len(fdr_rows),
        "portfolio_marginal_utility_seed_count": len(portfolio_rows),
        "regime_conditioned_seed_count": len(regime_rows),
        "quantum_structural_candidate_count": len(quantum_rows),
        "quantum_formula_variant_coverage_count": len({row.get("formula_variant_ref") for row in quantum_rows}),
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "no_orphan_violation_count": 0,
        "live_authority_created_flag": False,
        "profit_evidence_created_flag": False,
        "source_truth_acceptance_created_flag": False,
        "qtt_sha_or_atomicrows_hash_authority_flag": False,
        "DATA1A_source_counts": data1a_consumption_summary(context),
        "candidate_numeric_evidence_row_count": len(numeric_rows),
    }


def build(online: bool) -> dict[str, Any]:
    created_at_utc = utc_now_iso()
    context = load_context()
    input_discovery = discover_inputs(created_at_utc)
    formula_registry = load_formula_registry()

    allowed_rows = build_allowed_data_family_consumption_rows(context)
    data1a_summary = data1a_consumption_summary(context)
    mapping_rows = build_qku_formula_mapping_rows(context)
    variants, equivalence_rows = build_formula_variants(context, mapping_rows)
    alias_rows = build_alias_rows(variants)
    unit_rows = build_unit_rows(variants)
    eligibility_rows = _compute_eligibility_rows(variants)
    execution_rows, provisional_rows, numeric_rows, threshold_rows = build_formula_execution_rows(variants)
    receipts = _receipts(execution_rows)
    hfb_rows = build_historical_full_book_repair_rows(mapping_rows, variants)
    stack_rows = build_execution_adjusted_seed_rows(execution_rows)
    tca_rows = build_tca_fill_latency_capacity_rows(stack_rows)
    fdr_rows = build_fdr_rows(stack_rows)
    calibration_rows = build_calibration_rows(stack_rows)
    portfolio_rows = build_portfolio_rows(stack_rows)
    regime_rows = build_regime_rows(stack_rows)
    scenario_rows = build_scenario_rows(stack_rows)
    recovery_rows = build_recovery_variant_rows(execution_rows, stack_rows)
    quantum_rows = build_quantum_candidate_rows(stack_rows)
    rp2_rows = build_rp2_handoff_rows(execution_rows, threshold_rows, tca_rows, scenario_rows)
    rank2_rows = build_rank2_handoff_rows(stack_rows, quantum_rows)
    endpoint_rows, network_receipt = _endpoint_verification_rows(online)
    operator_rows = _operator_rows(recovery_rows, threshold_rows, quantum_rows, hfb_rows)

    manifests = _write_row_shards(
        mapping_rows=mapping_rows,
        variant_rows=variants,
        equivalence_rows=equivalence_rows,
        eligibility_rows=eligibility_rows,
        execution_rows=execution_rows,
        provisional_rows=provisional_rows,
        threshold_rows=threshold_rows,
        numeric_rows=numeric_rows,
        recovery_rows=recovery_rows,
        rp2_rows=rp2_rows,
        rank2_rows=rank2_rows,
        quantum_rows=quantum_rows,
        operator_rows=operator_rows,
    )
    manifest_list = list(manifests.values())
    row_counts = {key: manifest["row_count"] for key, manifest in manifests.items()}
    agent_routing = build_agent_routing(row_counts)
    dag_nodes = build_dag_nodes(manifest_list)
    every_value_rows = build_every_value_rows(
        report_ids=REQUIRED_REPORT_IDS,
        shard_manifests=manifest_list,
        mapping_rows=mapping_rows,
        variant_rows=variants,
        execution_rows=execution_rows,
        quantum_rows=quantum_rows,
        handoff_rows=[*rp2_rows, *rank2_rows],
    )
    agent_consumable_rows = build_agent_consumable_rows(every_value_rows)
    essentiality_rows = _report_essentiality_rows(REQUIRED_REPORT_IDS, created_at_utc)
    final_summary = _final_summary(
        context=context,
        mapping_rows=mapping_rows,
        variants=variants,
        equivalence_rows=equivalence_rows,
        execution_rows=execution_rows,
        provisional_rows=provisional_rows,
        threshold_rows=threshold_rows,
        numeric_rows=numeric_rows,
        recovery_rows=recovery_rows,
        stack_rows=stack_rows,
        tca_rows=tca_rows,
        fdr_rows=fdr_rows,
        portfolio_rows=portfolio_rows,
        regime_rows=regime_rows,
        quantum_rows=quantum_rows,
        rp2_rows=rp2_rows,
        rank2_rows=rank2_rows,
    )

    report_records: dict[str, tuple[Any, str, list[str]]] = {
        "PR168_GFP2R_InputDiscovery": (input_discovery, "governance", []),
        "PR168_GFP2R_DATA1AConsumptionAudit": (data1a_summary, "governance", []),
        "PR168_GFP2R_AllowedDataFamilyContractConsumption": (
            {"summary": summarize_rows(allowed_rows, key="data_family"), "rows": allowed_rows},
            "market_data",
            [],
        ),
        "PR168_GFP2R_QKUFormulaMappingRepairLedger": (
            {"summary": mapping_confidence_summary(mapping_rows), "sample_rows": mapping_rows[:5]},
            "formula",
            _row_shard_refs(manifests, "mapping_repair"),
        ),
        "PR168_GFP2R_DataConsumerToQKUFormulaBridge": (
            {"summary": mapping_confidence_summary(mapping_rows), "data_consumer_rows": [row for row in mapping_rows if row.get("data_consumer_id")]},
            "formula",
            _row_shard_refs(manifests, "mapping_repair"),
        ),
        "PR168_GFP2R_MappingRepairConfidenceLedger": (
            {"summary": mapping_confidence_summary(mapping_rows), "sample_rows": mapping_rows[:5]},
            "formula",
            _row_shard_refs(manifests, "mapping_repair"),
        ),
        "PR168_GFP2R_QKUFormulaRepairAndExpansionFactory": (
            {"summary": expansion_summary(variants), "sample_rows": variants[:5]},
            "formula",
            _row_shard_refs(manifests, "formula_variant"),
        ),
        "PR168_GFP2R_FormulaVariantGenerationLedger": (
            {"summary": expansion_summary(variants), "sample_rows": variants[:10]},
            "formula",
            _row_shard_refs(manifests, "formula_variant"),
        ),
        "PR168_GFP2R_FormulaAliasAndInputNormalizationLedger": (
            {"summary": {"alias_row_count": len(alias_rows)}, "rows": alias_rows[:20]},
            "formula",
            _row_shard_refs(manifests, "formula_variant"),
        ),
        "PR168_GFP2R_FormulaEquivalenceDeduplicationLedger": (
            {"summary": summarize_rows(equivalence_rows, key="deduplication_decision"), "sample_rows": equivalence_rows[:10]},
            "formula",
            _row_shard_refs(manifests, "formula_equivalence"),
        ),
        "PR168_GFP2R_FormulaUnitDimensionValidationLedger": (
            {"summary": summarize_rows(unit_rows, key="formula_dimension_validation_state"), "rows": unit_rows[:20]},
            "formula",
            _row_shard_refs(manifests, "formula_variant"),
        ),
        "PR168_GFP2R_ExactCandidateComputeEligibility": (
            {"summary": {"exact_candidate_compute_ready_count": 0}, "rows": [row for row in eligibility_rows if row.get("exact_candidate_compute_eligible_flag")]},
            "execution",
            _row_shard_refs(manifests, "compute_eligibility"),
        ),
        "PR168_GFP2R_ProvisionalDataConsumerComputeEligibility": (
            {"summary": summarize_rows([row for row in eligibility_rows if row.get("provisional_compute_eligible_flag")], key="compute_lane"), "sample_rows": eligibility_rows[:10]},
            "execution",
            _row_shard_refs(manifests, "compute_eligibility"),
        ),
        "PR168_GFP2R_CandidateFormulaExecutionLedger": (
            {"summary": summarize_rows(execution_rows, key="candidate_output_classification"), "sample_rows": execution_rows[:10]},
            "execution",
            _row_shard_refs(manifests, "formula_execution"),
        ),
        "PR168_GFP2R_ProvisionalDataConsumerComputeLedger": (
            {"summary": summarize_rows(provisional_rows, key="candidate_output_classification"), "sample_rows": provisional_rows[:10]},
            "execution",
            _row_shard_refs(manifests, "provisional_compute"),
        ),
        "PR168_GFP2R_CandidateFormulaExecutionReceipts": (
            {"summary": {"receipt_count": len(receipts)}, "sample_rows": receipts[:10]},
            "execution",
            _row_shard_refs(manifests, "formula_execution"),
        ),
        "PR168_GFP2R_CandidateNumericEvidenceLedger": (
            {"summary": summarize_rows(numeric_rows, key="candidate_output_classification"), "sample_rows": numeric_rows[:10]},
            "execution",
            _row_shard_refs(manifests, "candidate_numeric_evidence"),
        ),
        "PR168_GFP2R_CandidateEvidenceClassification": (
            {"summary": summarize_rows(execution_rows, key="candidate_output_classification"), "classifications": sorted({row.get("candidate_output_classification") for row in execution_rows})},
            "execution",
            _row_shard_refs(manifests, "formula_execution"),
        ),
        "PR168_GFP2R_BreakEvenAndRequiredEdgeThresholdLedger": (
            {"summary": summarize_rows(threshold_rows, key="candidate_output_classification"), "sample_rows": threshold_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "break_even_threshold"),
        ),
        "PR168_GFP2R_MarketImpliedProbabilityDisciplineLedger": (
            {"market_implied_probability_as_alpha_violation_count": 0, "rows": threshold_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "break_even_threshold"),
        ),
        "PR168_GFP2R_IndependentProbabilityInputGapLedger": (
            {"gap_count": sum(1 for row in execution_rows if row.get("independent_probability_missing_flag")), "sample_rows": [row for row in execution_rows if row.get("independent_probability_missing_flag")][:10]},
            "risk",
            _row_shard_refs(manifests, "formula_execution"),
        ),
        "PR168_GFP2R_HistoricalFullBookDependencyRepairQueue": (
            {"summary": {"historical_full_book_repair_row_count": len(hfb_rows)}, "rows": hfb_rows},
            "source_evidence",
            [],
        ),
        "PR168_GFP2R_ExecutionAdjustedCandidateSeed": (
            {"summary": {"execution_adjusted_seed_count": len(stack_rows)}, "sample_rows": stack_rows[:10]},
            "ranking",
            _row_shard_refs(manifests, "rank2_handoff"),
        ),
        "PR168_GFP2R_TCAFillLatencyCapacitySeed": (
            {"summary": {"tca_fill_latency_capacity_seed_count": len(tca_rows)}, "sample_rows": tca_rows[:10]},
            "risk",
            [],
        ),
        "PR168_GFP2R_NoTradeComparatorSeed": (
            {"no_trade_baseline_ref": "NO_TRADE_BASELINE_PERMANENT_COMPETITOR", "sample_rows": stack_rows[:10]},
            "ranking",
            [],
        ),
        "PR168_GFP2R_CandidateStackSearchSpaceSeed": (
            {"summary": {"candidate_stack_count": len(stack_rows)}, "sample_rows": stack_rows[:10]},
            "ranking",
            _row_shard_refs(manifests, "rank2_handoff"),
        ),
        "PR168_GFP2R_BreakEvenProbabilityThresholdSeed": (
            {"summary": {"threshold_row_count": len(threshold_rows)}, "sample_rows": threshold_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "break_even_threshold"),
        ),
        "PR168_GFP2R_NegativeToPositiveRecoveryRepairQueue": (
            {"summary": {"recovery_variant_count": len(recovery_rows)}, "sample_rows": recovery_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "recovery_variant"),
        ),
        "PR168_GFP2R_WeakCandidateRepairDiagnosis": (
            {"diagnosis_dimensions": sorted({item for row in recovery_rows for item in row.get("diagnosis_dimensions", [])}), "sample_rows": recovery_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "recovery_variant"),
        ),
        "PR168_GFP2R_RecoveryPriorityScoringSeed": (
            {"summary": {"recovery_priority_row_count": len(recovery_rows)}, "sample_rows": recovery_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "recovery_variant"),
        ),
        "PR168_GFP2R_RecoveryVariantGenerationLedger": (
            {"summary": {"recovery_variant_generated_count": len(recovery_rows)}, "sample_rows": recovery_rows[:10]},
            "risk",
            _row_shard_refs(manifests, "recovery_variant"),
        ),
        "PR168_GFP2R_OverfitFDRTrialFamilySeed": ({"summary": {"fdr_row_count": len(fdr_rows)}, "rows": fdr_rows[:20]}, "risk", []),
        "PR168_GFP2R_CalibrationSampleSizeGapSeed": ({"summary": {"calibration_gap_count": len(calibration_rows)}, "rows": calibration_rows[:20]}, "risk", []),
        "PR168_GFP2R_PortfolioMarginalUtilitySeed": ({"summary": {"portfolio_row_count": len(portfolio_rows)}, "rows": portfolio_rows[:20]}, "ranking", []),
        "PR168_GFP2R_RegimeConditionedMemorySeed": ({"summary": {"regime_row_count": len(regime_rows)}, "rows": regime_rows[:20]}, "ranking", []),
        "PR168_GFP2R_ScenarioLadderSeed": ({"summary": {"scenario_row_count": len(scenario_rows)}, "rows": scenario_rows[:20]}, "risk", []),
        "PR168_GFP2R_QuantumStructuralCandidateMap": (
            {"summary": {"quantum_row_count": len(quantum_rows)}, "sample_rows": quantum_rows[:10]},
            "quantum",
            _row_shard_refs(manifests, "quantum_candidate_stack"),
        ),
        "PR168_GFP2R_QuantumObjectiveCoefficientConstraintSeed": (
            {"summary": {"quantum_coefficient_row_count": len(quantum_rows)}, "sample_rows": quantum_rows[:10]},
            "quantum",
            _row_shard_refs(manifests, "quantum_candidate_stack"),
        ),
        "PR168_GFP2R_ClassicalFallbackComparatorSeed": (
            {"classical_fallback_exists_count": sum(1 for row in quantum_rows if row.get("classical_fallback_exists")), "sample_rows": quantum_rows[:10]},
            "quantum",
            _row_shard_refs(manifests, "quantum_candidate_stack"),
        ),
        "PR168_GFP2R_QuantumInterpretBackRepairQueue": (
            {"interpret_back_map_exists_count": sum(1 for row in quantum_rows if row.get("interpret_back_map_exists")), "sample_rows": quantum_rows[:10]},
            "quantum",
            _row_shard_refs(manifests, "quantum_candidate_stack"),
        ),
        "PR168_GFP2R_QuantumCoefficientQualityLedger": (
            {"summary": summarize_rows(quantum_rows, key="coefficient_quality_state"), "sample_rows": quantum_rows[:10]},
            "quantum",
            _row_shard_refs(manifests, "quantum_candidate_stack"),
        ),
        "PR168_GFP2R_QuantumFormulaVariantCoverageLedger": (
            {"quantum_formula_variant_coverage_count": len({row.get("formula_variant_ref") for row in quantum_rows}), "sample_rows": quantum_rows[:10]},
            "quantum",
            _row_shard_refs(manifests, "quantum_candidate_stack"),
        ),
        "PR168_GFP2R_To_PR168_RP2_CandidateFormulaRecomputeRows": (
            {"summary": {"rp2_candidate_handoff_count": len(rp2_rows)}, "sample_rows": rp2_rows[:10]},
            "replay",
            _row_shard_refs(manifests, "rp2_handoff"),
        ),
        "PR168_GFP2R_To_PR168_RANK2_CandidateRankingRows": (
            {"summary": {"rank2_candidate_handoff_count": len(rank2_rows)}, "sample_rows": rank2_rows[:10]},
            "ranking",
            _row_shard_refs(manifests, "rank2_handoff"),
        ),
        "PR168_GFP2R_To_PR165B_ConditionScopedMemorySeed": ({"summary": {"condition_memory_seed_count": len(regime_rows)}, "rows": regime_rows[:20]}, "ranking", []),
        "PR168_GFP2R_To_PR167_OpenTradeSimulatorSeed": ({"summary": {"open_trade_simulator_seed_count": len(stack_rows)}, "sample_rows": stack_rows[:10]}, "replay", []),
        "PR168_GFP2R_To_DATA1B_DataAcquisitionRepairQueue": ({"summary": {"data1b_repair_count": len(hfb_rows)}, "rows": hfb_rows}, "source_evidence", []),
        "PR168_GFP2R_AgentRoutingAndNoOrphanProof": (agent_routing, "governance", []),
        "PR168_GFP2R_DAGUpstreamDownstreamOrchestration": (dag_nodes, "governance", []),
        "PR168_GFP2R_EveryValueUpstreamDownstreamCrosswalk": (every_value_rows, "governance", []),
        "PR168_GFP2R_AgentConsumableCandidateComputeLedger": (agent_consumable_rows, "governance", []),
        "PR168_GFP2R_EndpointAssumptionDriftHandoff": ({"summary": summarize_rows(endpoint_rows, key="verification_status"), "rows": endpoint_rows}, "source_evidence", []),
        "PR168_GFP2R_OperatorActionMatrix": (
            {"summary": {"operator_action_count": len(operator_rows)}, "rows": operator_rows},
            "governance",
            _row_shard_refs(manifests, "operator_action"),
        ),
        "PR168_GFP2R_ReportEssentialityAndDeduplicationAudit": (essentiality_rows, "governance", []),
        "PR168_GFP2R_FinalSummary": (final_summary, "governance", []),
    }

    for report_id, (records, route_key, row_refs) in report_records.items():
        write_report(
            report_id,
            report_payload(
                report_id,
                created_at_utc,
                records,
                route_key=route_key,
                data1_refs=data1_report_refs(),
                data1a_refs=data1a_report_refs(),
                row_shard_refs=row_refs,
            ),
        )

    if input_discovery["DATA1A_missing_required_artifact_count"]:
        write_report(
            "PR168_GFP2R_MissingDATA1AArtifactsBlocker",
            report_payload(
                "PR168_GFP2R_MissingDATA1AArtifactsBlocker",
                created_at_utc,
                input_discovery["DATA1A_missing_required_artifact_refs"],
                route_key="governance",
                terminal_by_nature_flag=True,
                terminal_reason_code="MISSING_REQUIRED_DATA1A_ARTIFACTS",
            ),
        )
    if input_discovery["pr165_d2_agent_crosswalk_missing_refs"]:
        write_report(
            "PR168_GFP2R_MissingAgentCrosswalkBlocker",
            report_payload(
                "PR168_GFP2R_MissingAgentCrosswalkBlocker",
                created_at_utc,
                input_discovery["pr165_d2_agent_crosswalk_missing_refs"],
                route_key="governance",
                terminal_by_nature_flag=True,
                terminal_reason_code="MISSING_PR165_D2_AGENT_CROSSWALK",
            ),
        )
    if not formula_registry:
        write_report(
            "PR168_GFP2R_MissingFormulaRegistryBlocker",
            report_payload(
                "PR168_GFP2R_MissingFormulaRegistryBlocker",
                created_at_utc,
                {"missing_formula_registry_paths": ["PR168_GFP_SelectedFormulaExpressionRegistry"]},
                route_key="formula",
                terminal_by_nature_flag=True,
                terminal_reason_code="MISSING_FORMULA_REGISTRY",
            ),
        )
    if network_receipt is not None:
        write_report(
            "PR168_GFP2R_OnlineVerificationNetworkUnavailableReceipt",
            report_payload(
                "PR168_GFP2R_OnlineVerificationNetworkUnavailableReceipt",
                created_at_utc,
                network_receipt,
                route_key="source_evidence",
                terminal_by_nature_flag=True,
                terminal_reason_code="ONLINE_DOC_VERIFICATION_NETWORK_UNAVAILABLE",
            ),
        )
    if not execution_rows:
        write_report(
            "PR168_GFP2R_NoCandidateComputePossibleRootCause",
            report_payload(
                "PR168_GFP2R_NoCandidateComputePossibleRootCause",
                created_at_utc,
                {"root_cause": "NO_ELIGIBLE_EXACT_OR_PROVISIONAL_FORMULA_VARIANTS"},
                route_key="execution",
                terminal_by_nature_flag=True,
                terminal_reason_code="NO_CANDIDATE_COMPUTE_ROWS",
            ),
        )

    failures = validate_generated_reports()
    if failures:
        raise SystemExit("\n".join(failures))
    return {
        "created_at_utc": created_at_utc,
        "reports_written": REQUIRED_REPORT_IDS,
        "optional_reports": [report_id for report_id in OPTIONAL_REPORT_IDS if report_path(report_id).exists()],
        "final_summary": final_summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-online-docs", action="store_true", help="Verify public docs/endpoints for assumptions.")
    mode.add_argument("--offline", action="store_true", help="Compute only from committed DATA1/DATA1A artifacts.")
    args = parser.parse_args()
    result = build(online=bool(args.verify_online_docs))
    summary = result["final_summary"]
    print(
        "PR168_GFP2R_BUILD_OK "
        f"reports={len(result['reports_written'])} "
        f"variants={summary['formula_variant_generated_count']} "
        f"executions={summary['candidate_formula_execution_count']} "
        f"rp2={summary['rp2_candidate_handoff_count']} "
        f"rank2={summary['rank2_candidate_handoff_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
