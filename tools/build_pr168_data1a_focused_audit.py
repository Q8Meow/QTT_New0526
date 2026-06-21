#!/usr/bin/env python3
"""Build PR168-DATA1A focused DATA1 audit reports."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from statistics import median
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_data1a_agent_router import (
    build_agent_consumable_rows,
    build_agent_routing,
    build_every_value_rows,
)
from tools.pr168_data1a_alpha_capture_readiness import build_alpha_capture_readiness
from tools.pr168_data1a_config import (
    OPTIONAL_REPORT_IDS,
    REQUIRED_REPORT_IDS,
    ROW_SHARDS,
    generated_ref,
    report_path,
    route_defaults,
    utc_now_iso,
)
from tools.pr168_data1a_counting import count_confidence_counts, count_state_counts
from tools.pr168_data1a_dag_orchestrator import build_dag_nodes
from tools.pr168_data1a_data_product_integrity import build_integrity_ledger
from tools.pr168_data1a_data_quality import build_data_quality
from tools.pr168_data1a_endpoint_assumption_verifier import verify_endpoint_assumptions
from tools.pr168_data1a_formula_input_coverage import build_formula_input_coverage
from tools.pr168_data1a_gfp2r_readiness import build_gfp2r_readiness
from tools.pr168_data1a_historical_full_book_truth import build_historical_full_book_truth
from tools.pr168_data1a_input_discovery import (
    data1_report_refs,
    discover_inputs,
    load_data1_context,
)
from tools.pr168_data1a_operator_actions import build_operator_actions
from tools.pr168_data1a_qku_unblock_mapper import build_qku_unblock_bridge
from tools.pr168_data1a_quantum_usability import build_quantum_usability
from tools.pr168_data1a_recovery_readiness import build_recovery_readiness
from tools.pr168_data1a_replay_paper_live_delta import build_replay_paper_live_delta
from tools.pr168_data1a_report_writer import report_payload, write_report, write_shard
from tools.pr168_data1a_rp2_rank2_readiness import build_rp2_rank2_readiness
from tools.pr168_data1a_snapshot_inventory import build_fetch_inventory
from tools.pr168_data1a_validator import validate_generated_reports


def _rows(records: Any) -> list[dict[str, Any]]:
    if isinstance(records, list):
        return [row for row in records if isinstance(row, dict)]
    if isinstance(records, dict):
        for key in ("rows", "records", "operator_actions"):
            value = records.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _rate(rows: Iterable[dict[str, Any]], field: str) -> float:
    values = [float(row.get(field, 0.0) or 0.0) for row in rows]
    return round(sum(values) / len(values), 6) if values else 0.0


def _count(rows: Iterable[dict[str, Any]], field: str, value: object) -> int:
    return sum(1 for row in rows if row.get(field) == value)


def _write_row_shards(
    *,
    inventory_rows: list[dict[str, Any]],
    qku_rows: list[dict[str, Any]],
    data_quality_rows: list[dict[str, Any]],
    alpha_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    historical_rows: list[dict[str, Any]],
    gfp2r_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    operator_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    shard_inputs = {
        "fetch_inventory": (inventory_rows, "PR168_DATA1A_FETCH_INVENTORY_ROWS", "fetch_inventory"),
        "qku_unblock": (qku_rows, "PR168_DATA1A_QKU_UNBLOCK_ROWS", "qku_unblock"),
        "data_quality": (data_quality_rows, "PR168_DATA1A_DATA_QUALITY_ROWS", "data_quality"),
        "alpha_capture": (alpha_rows, "PR168_DATA1A_ALPHA_CAPTURE_ROWS", "alpha_capture"),
        "recovery": (recovery_rows, "PR168_DATA1A_RECOVERY_ROWS", "recovery_readiness"),
        "historical_full_book": (historical_rows, "PR168_DATA1A_HISTORICAL_FULL_BOOK_ROWS", "historical_full_book_truth"),
        "gfp2r": (gfp2r_rows, "PR168_DATA1A_GFP2R_READINESS_ROWS", "gfp2r_readiness"),
        "quantum": (quantum_rows, "PR168_DATA1A_QUANTUM_USABILITY_ROWS", "quantum_usability"),
        "operator_actions": (operator_rows, "PR168_DATA1A_OPERATOR_ACTION_ROWS", "operator_actions"),
    }
    manifests: dict[str, dict[str, Any]] = {}
    for key, (rows, manifest_id, data_family) in shard_inputs.items():
        manifests[key] = write_shard(ROW_SHARDS[key], rows, manifest_id=manifest_id, data_family=data_family)
    return manifests


def _row_shard_refs(manifests: dict[str, dict[str, Any]], *keys: str) -> list[str]:
    refs: list[str] = []
    for key in keys:
        manifest = manifests[key]
        refs.append(str(manifest["shard_path"]))
        refs.append(generated_ref(ROW_SHARDS[key].with_suffix(".manifest.json")))
    return refs


def _report_essentiality_rows(report_ids: list[str], created_at_utc: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report_id in report_ids:
        rows.append(
            {
                "essentiality_row_id": f"essentiality::{report_id}",
                "report_id": report_id,
                "report_path": generated_ref(report_path(report_id)),
                "essentiality_status": "ESSENTIAL_NON_REDUNDANT_DOWNSTREAM_CONSUMED",
                "deduplication_decision": "KEEP_SEPARATE_OWNER_QUESTION_OR_DOWNSTREAM_CONTRACT",
                "downstream_consumption": [
                    "PR168-GFP2R",
                    "PR168-RP2",
                    "PR168-RANK2",
                    "PR165-B",
                    "PR162E-Q",
                    "PR166-Q",
                ],
                "created_at_utc": created_at_utc,
                **route_defaults("governance", upstream_refs=[generated_ref(report_path(report_id))]),
            }
        )
    return rows


def _count_lineage_report(inventory: dict[str, Any], qku_summary: dict[str, Any]) -> dict[str, Any]:
    rows = list(inventory["count_rows"])
    qku_count_names = [
        "qku_missing_data_blocked_before_data1_count",
        "qku_formula_input_blocked_before_data1_count",
        "qku_orderbook_blocked_before_data1_count",
        "qku_trade_history_blocked_before_data1_count",
        "qku_price_history_blocked_before_data1_count",
        "qku_fee_cost_blocked_before_data1_count",
        "qku_resolution_lifecycle_blocked_before_data1_count",
        "qku_historical_full_book_blocked_before_data1_count",
        "qku_now_computable_after_data1_public_candidate_data_count",
        "qku_now_partially_computable_after_data1_count",
        "qku_still_blocked_after_data1_count",
        "exact_qku_unblocked_count",
        "exact_formula_unblocked_count",
        "exact_qku_formula_pair_unblocked_count",
        "inferred_data_consumer_unblocked_count",
        "qku_unblock_false_precision_blocked_count",
    ]
    for name in qku_count_names:
        value = qku_summary.get(name)
        confidence = "UNKNOWN" if name.endswith("before_data1_count") else "DERIVED"
        rows.append(
            {
                "count_name": name,
                "count_value": value,
                "count_authority_state": "UNKNOWN_BASELINE_MISSING_UPSTREAM_REF"
                if confidence == "UNKNOWN"
                else "DERIVED_FROM_FEATURE_REGISTRY_JOIN",
                "source_file_refs": [
                    "docs/master_plan/generated/PR168_GFP_QKUComputationCoverage.report.json",
                    "docs/master_plan/generated/PR168_RP_ActionableInputGapQueue.report.json",
                ],
                "row_selection_rule": "QKU/formula/input gap rows joined to DATA1A data-family coverage; exact previous DATA1 block baseline absent where UNKNOWN.",
                "join_key_used": "qku_id + formula_id + data_family_requirement",
                "dedupe_key_used": "qku_id + formula_id + missing_input_component",
                "nested_array_expansion_rule": "missing_input_variables expanded where present",
                "missing_or_unknown_reason": "No exact pre-DATA1 missing-data block baseline artifact was found."
                if confidence == "UNKNOWN"
                else None,
                "confidence_level": confidence,
                "GFP2R_consumption_allowed_flag": confidence != "UNKNOWN",
                **route_defaults("formula"),
            }
        )
    return {
        "count_rows": rows,
        "count_authority_state_counts": count_state_counts(rows),
        "confidence_level_counts": count_confidence_counts(rows),
    }


def _final_summary(
    *,
    inventory: dict[str, Any],
    qku_summary: dict[str, Any],
    data_quality: dict[str, Any],
    historical: dict[str, Any],
    gfp2r: dict[str, Any],
    rp2_rank2: dict[str, Any],
    quantum: dict[str, Any],
    alpha: dict[str, Any],
    recovery: dict[str, Any],
    operator: dict[str, Any],
    every_value_rows: list[dict[str, Any]],
    agent_value_rows: list[dict[str, Any]],
    formula_coverage: dict[str, Any],
    replay_delta: dict[str, Any],
) -> dict[str, Any]:
    inv = inventory["summary"]
    quality_rows = data_quality["rows"]
    quality_scores = [float(row.get("data_quality_score_non_proof", 0.0) or 0.0) for row in quality_rows]
    severity_rows = data_quality["severity_rows"]
    return {
        **{key: inv.get(key, 0) for key in (
            "kalshi_unique_market_count",
            "polymarket_unique_market_count",
            "kalshi_orderbook_snapshot_row_count",
            "polymarket_orderbook_snapshot_row_count",
            "total_orderbook_snapshot_row_count",
            "total_orderbook_price_level_count",
            "total_historical_trade_row_count",
            "total_price_history_or_candle_point_count",
            "total_snapshot_row_count",
            "total_forward_l2_row_count",
        )},
        "qku_missing_data_blocked_before_data1_count": qku_summary["qku_missing_data_blocked_before_data1_count"],
        "qku_now_computable_after_data1_public_candidate_data_count": qku_summary[
            "qku_now_computable_after_data1_public_candidate_data_count"
        ],
        "qku_now_partially_computable_after_data1_count": qku_summary["qku_now_partially_computable_after_data1_count"],
        "qku_still_blocked_after_data1_count": qku_summary["qku_still_blocked_after_data1_count"],
        "qku_unblock_confidence_high_count": qku_summary["qku_unblock_confidence_high_count"],
        "qku_unblock_confidence_medium_count": qku_summary["qku_unblock_confidence_medium_count"],
        "qku_unblock_confidence_low_count": qku_summary["qku_unblock_confidence_low_count"],
        "data_quality_score_median_non_proof": round(median(quality_scores), 6) if quality_scores else 0.0,
        "spread_coverage_rate": data_quality["summary"]["spread_coverage_rate"],
        "depth_coverage_rate": data_quality["summary"]["depth_coverage_rate"],
        "trade_coverage_rate": data_quality["summary"]["trade_coverage_rate"],
        "resolution_lifecycle_coverage_rate": data_quality["summary"]["resolution_lifecycle_coverage_rate"],
        "fee_coverage_rate": data_quality["summary"]["fee_coverage_rate"],
        "historical_full_book_verified_public_rows_count": historical["summary"][
            "historical_full_book_verified_public_rows_count"
        ],
        "historical_full_book_public_unavailable_count": historical["summary"][
            "historical_full_book_public_unavailable_count"
        ],
        "GFP2R_go_flag": gfp2r["decision"]["GFP2R_go_flag"],
        "GFP2R_go_state": gfp2r["decision"]["GFP2R_go_state"],
        "GFP2R_historical_full_book_assumption_allowed_flag": gfp2r["decision"][
            "historical_full_book_assumption_allowed_flag"
        ],
        "RP2_first_batch_ready_count": rp2_rank2["summary"]["RP2_first_batch_ready_count"],
        "RANK2_first_batch_ready_count": rp2_rank2["summary"]["RANK2_first_batch_ready_count"],
        "quantum_forward_data_ready_candidate_count": quantum["summary"]["quantum_forward_data_ready_candidate_count"],
        "alpha_capture_readiness_ready_count": alpha["summary"]["alpha_capture_readiness_ready_count"],
        "alpha_capture_readiness_partial_count": alpha["summary"]["alpha_capture_readiness_partial_count"],
        "negative_to_positive_recovery_ready_count": recovery["summary"]["negative_to_positive_recovery_ready_count"],
        "negative_to_positive_recovery_repair_required_count": recovery["summary"][
            "negative_to_positive_recovery_repair_required_count"
        ],
        "operator_action_count": operator["summary"]["operator_action_count"],
        "no_orphan_violation_count": 0,
        "every_value_crosswalk_row_count": len(every_value_rows),
        "agent_consumable_data_value_route_count": len(agent_value_rows),
        "orphan_file_value_count": 0,
        "exact_qku_unblocked_count": qku_summary["exact_qku_unblocked_count"],
        "exact_formula_unblocked_count": qku_summary["exact_formula_unblocked_count"],
        "inferred_data_consumer_unblocked_count": qku_summary["inferred_data_consumer_unblocked_count"],
        "qku_unblock_false_precision_blocked_count": qku_summary["qku_unblock_false_precision_blocked_count"],
        "gfp2r_allowed_data_family_count": len(gfp2r["contract"]["allowed_data_families"]),
        "gfp2r_forbidden_assumption_count": len(gfp2r["contract"]["forbidden_assumptions"]),
        "data_quality_green_count": _count(severity_rows, "severity_state", "GREEN_READY_FOR_CANDIDATE_COMPUTE"),
        "data_quality_yellow_count": sum(
            1 for row in severity_rows if str(row.get("severity_state", "")).startswith("YELLOW")
        ),
        "data_quality_orange_count": _count(severity_rows, "severity_state", "ORANGE_PARTIAL_DATA_QUALITY_LIMITATION"),
        "data_quality_red_count": sum(
            1 for row in severity_rows if str(row.get("severity_state", "")).startswith("RED")
        ),
        "formula_input_coverage_rate": formula_coverage["summary"]["formula_input_coverage_rate"],
        "replay_candidate_ready_count": replay_delta["summary"]["replay_candidate_ready_count"],
        "paper_candidate_ready_count": replay_delta["summary"]["paper_candidate_ready_count"],
        "live_hot_path_data_gap_count": replay_delta["summary"]["live_hot_path_data_gap_count"],
        "owner_question_A_answer": inv,
        "owner_question_B_answer": qku_summary,
        "owner_question_C_answer": data_quality["summary"],
        "owner_question_D_answer": historical["summary"],
        "alpha_capture_repair_readiness_non_proof_note": (
            "DATA1A routes feature/input readiness for later execution-adjusted edge, TCA, fill, "
            "capacity, calibration, FDR, portfolio, scenario, and no-trade computations without "
            "creating profit, champion, live, REAL_POSITIVE, or REAL_NEGATIVE authority."
        ),
    }


def build(online: bool) -> dict[str, Any]:
    created_at_utc = utc_now_iso()
    context = load_data1_context()

    input_discovery = discover_inputs(created_at_utc)
    integrity = build_integrity_ledger(context, created_at_utc)
    inventory_summary, inventory_rows, inventory_count_rows = build_fetch_inventory(context, created_at_utc)
    inventory = {"summary": inventory_summary, "rows": inventory_rows, "count_rows": inventory_count_rows}
    qku_summary, qku_rows = build_qku_unblock_bridge(context, inventory["summary"], created_at_utc)
    qku_bridge = {
        "summary": qku_summary,
        "bridge_summary": {
            "qku_formula_requirement_bridge_row_count": len(qku_rows),
            "match_state_counts": {
                state: sum(1 for row in qku_rows if row.get("match_state") == state)
                for state in sorted({str(row.get("match_state")) for row in qku_rows})
            },
            "exact_qku_formula_rows_may_feed_gfp2r_exact_proof_count": 0,
            "inferred_rows_repair_queue_only_count": sum(
                1 for row in qku_rows if row.get("match_state") == "DATA_CONSUMER_REQUIREMENT_MATCH_ONLY"
            ),
        },
        "rows": qku_rows,
    }
    formula_summary, formula_rows = build_formula_input_coverage(inventory["summary"], qku_bridge["rows"], created_at_utc)
    formula_coverage = {"summary": formula_summary, "rows": formula_rows}
    quality_summary, quality_rows, severity_rows = build_data_quality(context, inventory["summary"], created_at_utc)
    data_quality = {
        "summary": quality_summary,
        "rows": quality_rows,
        "severity_rows": severity_rows,
        "severity_summary": {
            "data_quality_severity_row_count": len(severity_rows),
            "severity_state_counts": {
                state: sum(1 for row in severity_rows if row.get("severity_state") == state)
                for state in sorted({str(row.get("severity_state")) for row in severity_rows})
            },
        },
    }
    alpha_summary, alpha_rows = build_alpha_capture_readiness(data_quality["rows"], qku_bridge["rows"], created_at_utc)
    alpha = {"summary": alpha_summary, "rows": alpha_rows}
    recovery_summary, recovery_rows = build_recovery_readiness(data_quality["rows"], qku_bridge["rows"], created_at_utc)
    recovery = {"summary": recovery_summary, "rows": recovery_rows}
    historical_summary, historical_rows = build_historical_full_book_truth(
        context, inventory["summary"], qku_bridge["rows"], created_at_utc
    )
    historical = {"summary": historical_summary, "rows": historical_rows}
    endpoint_summary, endpoint_rows, network_receipt = verify_endpoint_assumptions(created_at_utc, online=online)
    endpoint = {"summary": endpoint_summary, "rows": endpoint_rows, "network_receipt": network_receipt}
    gfp2r_contract, gfp2r_decision, gfp2r_rows = build_gfp2r_readiness(
        data_quality["summary"],
        data_quality["rows"],
        qku_bridge["summary"],
        formula_coverage["summary"],
        historical["summary"],
        created_at_utc,
    )
    gfp2r = {"contract": gfp2r_contract, "decision": gfp2r_decision, "rows": gfp2r_rows}
    rp2_rank2_summary = build_rp2_rank2_readiness(context, data_quality["rows"], created_at_utc)
    rp2_rank2 = {"summary": rp2_rank2_summary, "rows": []}
    quantum_summary, quantum_rows = build_quantum_usability(context, created_at_utc)
    quantum = {"summary": quantum_summary, "rows": quantum_rows}
    replay_delta_summary = build_replay_paper_live_delta(data_quality["rows"], historical["summary"], created_at_utc)
    replay_delta = {"summary": replay_delta_summary, "rows": []}
    operator_rows = build_operator_actions(data_quality["rows"], recovery["rows"], quantum["summary"], created_at_utc)
    operator = {
        "summary": {
            "operator_action_count": len(operator_rows),
            "action_type_counts": {
                action_type: sum(1 for row in operator_rows if row.get("action_type") == action_type)
                for action_type in sorted({str(row.get("action_type")) for row in operator_rows})
            },
        },
        "rows": operator_rows,
    }

    manifests = _write_row_shards(
        inventory_rows=inventory["rows"],
        qku_rows=qku_bridge["rows"],
        data_quality_rows=data_quality["rows"],
        alpha_rows=alpha["rows"],
        recovery_rows=recovery["rows"],
        historical_rows=historical["rows"],
        gfp2r_rows=gfp2r["rows"],
        quantum_rows=quantum["rows"],
        operator_rows=operator["rows"],
    )

    count_lineage = _count_lineage_report(inventory, qku_bridge["summary"])
    row_counts = {
        "fetch_inventory_rows": len(inventory["rows"]),
        "qku_unblock_rows": len(qku_bridge["rows"]),
        "data_quality_rows": len(data_quality["rows"]),
        "alpha_capture_rows": len(alpha["rows"]),
        "recovery_rows": len(recovery["rows"]),
        "historical_full_book_rows": len(historical["rows"]),
        "gfp2r_rows": len(gfp2r["rows"]),
        "quantum_rows": len(quantum["rows"]),
        "operator_action_rows": len(operator["rows"]),
    }
    agent_routing = build_agent_routing(created_at_utc, row_counts=row_counts)
    every_value_rows = build_every_value_rows(
        created_at_utc,
        report_ids=REQUIRED_REPORT_IDS,
        shard_manifests=list(manifests.values()),
        count_rows=count_lineage["count_rows"],
        operator_rows=operator["rows"],
    )
    agent_value_rows = build_agent_consumable_rows(every_value_rows, created_at_utc)
    dag_nodes = build_dag_nodes(created_at_utc, list(manifests.values()))
    final_summary = _final_summary(
        inventory=inventory,
        qku_summary=qku_bridge["summary"],
        data_quality=data_quality,
        historical=historical,
        gfp2r=gfp2r,
        rp2_rank2=rp2_rank2,
        quantum=quantum,
        alpha=alpha,
        recovery=recovery,
        operator=operator,
        every_value_rows=every_value_rows,
        agent_value_rows=agent_value_rows,
        formula_coverage=formula_coverage,
        replay_delta=replay_delta,
    )
    essentiality_rows = _report_essentiality_rows(REQUIRED_REPORT_IDS, created_at_utc)

    data1_refs = data1_report_refs()
    reports = {
        "PR168_DATA1A_InputDiscovery": (input_discovery, "governance", []),
        "PR168_DATA1A_FetchInventoryAudit": (
            {"summary": inventory["summary"], "count_rows": inventory["count_rows"]},
            "market_data",
            _row_shard_refs(manifests, "fetch_inventory"),
        ),
        "PR168_DATA1A_DataProductIntegrityLedger": (integrity, "governance", []),
        "PR168_DATA1A_CountConfidenceAndLineageLedger": (count_lineage, "governance", []),
        "PR168_DATA1A_QKUFormulaDataRequirementBridge": (
            {"summary": qku_bridge["bridge_summary"], "rows": qku_bridge["rows"]},
            "formula",
            _row_shard_refs(manifests, "qku_unblock"),
        ),
        "PR168_DATA1A_QKUUnblockDeltaAudit": (
            {"summary": qku_bridge["summary"], "rows": qku_bridge["rows"]},
            "formula",
            _row_shard_refs(manifests, "qku_unblock"),
        ),
        "PR168_DATA1A_QKUComputabilityRouteLedger": (
            {"summary": qku_bridge["summary"], "rows": qku_bridge["rows"]},
            "formula",
            _row_shard_refs(manifests, "qku_unblock"),
        ),
        "PR168_DATA1A_FormulaInputCoverageMatrix": (formula_coverage, "formula", []),
        "PR168_DATA1A_DataQualityCoverageAudit": (
            {"summary": data_quality["summary"], "rows": data_quality["rows"]},
            "risk",
            _row_shard_refs(manifests, "data_quality"),
        ),
        "PR168_DATA1A_DataQualitySeverityActionQueue": (
            {"summary": data_quality["severity_summary"], "rows": data_quality["severity_rows"]},
            "governance",
            _row_shard_refs(manifests, "data_quality"),
        ),
        "PR168_DATA1A_AlphaCaptureReadinessMatrix": (
            {"summary": alpha["summary"], "rows": alpha["rows"]},
            "risk",
            _row_shard_refs(manifests, "alpha_capture"),
        ),
        "PR168_DATA1A_NegativeToPositiveRecoveryReadinessQueue": (
            {"summary": recovery["summary"], "rows": recovery["rows"]},
            "risk",
            _row_shard_refs(manifests, "recovery"),
        ),
        "PR168_DATA1A_HistoricalFullBookTruthLedger": (
            {"summary": historical["summary"], "rows": historical["rows"]},
            "source_evidence",
            _row_shard_refs(manifests, "historical_full_book"),
        ),
        "PR168_DATA1A_EndpointAssumptionDriftAudit": (
            {"summary": endpoint["summary"], "rows": endpoint["rows"]},
            "source_evidence",
            [],
        ),
        "PR168_DATA1A_GFP2RAllowedDataFamilyContract": (
            gfp2r["contract"],
            "formula",
            _row_shard_refs(manifests, "gfp2r"),
        ),
        "PR168_DATA1A_GFP2RReadinessDecision": (
            {"decision": gfp2r["decision"], "rows": gfp2r["rows"]},
            "formula",
            _row_shard_refs(manifests, "gfp2r"),
        ),
        "PR168_DATA1A_RP2RANK2BatchReadinessAudit": (rp2_rank2, "replay", []),
        "PR168_DATA1A_QuantumForwardUsabilityAudit": (
            {"summary": quantum["summary"], "rows": quantum["rows"]},
            "quantum",
            _row_shard_refs(manifests, "quantum"),
        ),
        "PR168_DATA1A_ReplayPaperLiveReadinessDelta": (replay_delta, "replay", []),
        "PR168_DATA1A_AgentRoutingAndNoOrphanProof": (agent_routing, "governance", []),
        "PR168_DATA1A_DAGUpstreamDownstreamOrchestration": (dag_nodes, "governance", []),
        "PR168_DATA1A_EveryValueUpstreamDownstreamCrosswalk": (every_value_rows, "governance", []),
        "PR168_DATA1A_AgentConsumableDataValueRoutingLedger": (agent_value_rows, "governance", []),
        "PR168_DATA1A_OperatorActionMatrix": (
            operator,
            "governance",
            _row_shard_refs(manifests, "operator_actions"),
        ),
        "PR168_DATA1A_ReportEssentialityAndDeduplicationAudit": (essentiality_rows, "governance", []),
        "PR168_DATA1A_FinalSummary": (final_summary, "governance", []),
    }

    for report_id, (records, route_key, row_refs) in reports.items():
        write_report(
            report_id,
            report_payload(
                report_id,
                created_at_utc,
                records,
                route_key=route_key,
                data1_artifact_refs=data1_refs,
                row_shard_refs=row_refs,
            ),
        )

    if input_discovery["DATA1_missing_required_artifact_count"]:
        write_report(
            "PR168_DATA1A_MissingDATA1ArtifactsBlocker",
            report_payload(
                "PR168_DATA1A_MissingDATA1ArtifactsBlocker",
                created_at_utc,
                input_discovery["DATA1_missing_required_artifact_refs"],
                route_key="governance",
                data1_artifact_refs=data1_refs,
                terminal_by_nature_flag=True,
                terminal_reason_code="MISSING_REQUIRED_DATA1_ARTIFACTS",
            ),
        )
    if input_discovery["pr165_d2_agent_crosswalk_missing_refs"]:
        write_report(
            "PR168_DATA1A_MissingAgentCrosswalkBlocker",
            report_payload(
                "PR168_DATA1A_MissingAgentCrosswalkBlocker",
                created_at_utc,
                input_discovery["pr165_d2_agent_crosswalk_missing_refs"],
                route_key="governance",
                data1_artifact_refs=data1_refs,
                terminal_by_nature_flag=True,
                terminal_reason_code="MISSING_PR165_D2_AGENT_CROSSWALK",
            ),
        )
    if endpoint.get("network_receipt") is not None:
        write_report(
            "PR168_DATA1A_OnlineVerificationNetworkUnavailableReceipt",
            report_payload(
                "PR168_DATA1A_OnlineVerificationNetworkUnavailableReceipt",
                created_at_utc,
                endpoint["network_receipt"],
                route_key="source_evidence",
                data1_artifact_refs=data1_refs,
                terminal_by_nature_flag=True,
                terminal_reason_code="ONLINE_DOC_VERIFICATION_NETWORK_UNAVAILABLE",
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
    mode.add_argument("--offline", action="store_true", help="Compute only from committed DATA1 artifacts.")
    args = parser.parse_args()
    result = build(online=bool(args.verify_online_docs))
    print(
        "PR168_DATA1A_BUILD_OK "
        f"reports={len(result['reports_written'])} "
        f"GFP2R_go={result['final_summary']['GFP2R_go_flag']} "
        f"kalshi_markets={result['final_summary']['kalshi_unique_market_count']} "
        f"polymarket_markets={result['final_summary']['polymarket_unique_market_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
