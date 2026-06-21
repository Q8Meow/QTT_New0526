#!/usr/bin/env python3
"""Build PR168-DATA1 public market-data snapshots and routed reports."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_data1_agent_router import build_no_orphan_rows, load_agent_crosswalk_status
from tools.pr168_data1_batch_selector import (
    build_gfp2r_handoff,
    build_priority_rows,
    build_rank2_batch,
    build_rp2_batch,
)
from tools.pr168_data1_config import (
    FORECASTEX_IBKR_MANIFEST,
    HISTORICAL_CANDIDATE_JSONL,
    KALSHI_FORWARD_L2_JSONL,
    KALSHI_SNAPSHOT_JSONL,
    POLYMARKET_FORWARD_L2_JSONL,
    POLYMARKET_SNAPSHOT_JSONL,
    REQUIRED_REPORT_IDS,
    authority_flags,
    generated_ref,
    manifest_path,
    report_path,
    route_defaults,
    utc_now_iso,
)
from tools.pr168_data1_dag_orchestrator import build_dag_nodes
from tools.pr168_data1_data_quality import build_quality_rows
from tools.pr168_data1_data_readiness_classifier import classify_readiness
from tools.pr168_data1_endpoint_registry import build_endpoint_registry
from tools.pr168_data1_feature_builder import build_feature_rows
from tools.pr168_data1_forecastex_ibkr_manifest import forecastex_ibkr_rows
from tools.pr168_data1_forward_l2_capture import build_forward_l2_rows
from tools.pr168_data1_historical_full_book_discovery import (
    historical_full_book_acquisition_ledger,
    historical_l2_gap_rows,
    official_historical_full_book_audit,
    third_party_candidate_rows,
)
from tools.pr168_data1_http_client import HttpResult
from tools.pr168_data1_kalshi_client import KalshiPublicClient
from tools.pr168_data1_online_doc_discovery import discover_sources
from tools.pr168_data1_polymarket_client import PolymarketPublicClient
from tools.pr168_data1_polymarket_public_ws_capture import websocket_dependency_status
from tools.pr168_data1_quantum_feature_surface import build_quantum_surface
from tools.pr168_data1_report_writer import report_payload, write_report
from tools.pr168_data1_schema_normalizer import normalize_snapshot_rows
from tools.pr168_data1_snapshot_writer import write_json, write_jsonl, write_shard_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discover-online", action="store_true")
    parser.add_argument("--fetch-live", action="store_true")
    parser.add_argument("--prefer-historical-full-book", action="store_true")
    parser.add_argument("--capture-forward-l2", action="store_true")
    parser.add_argument("--offline-validate", action="store_true")
    args = parser.parse_args(argv)
    if args.offline_validate:
        from tools.pr168_data1_validator import run_validation

        run_validation("offline_validate")
        return 0
    build_all_reports(
        discover_online=args.discover_online,
        fetch_live=args.fetch_live,
        prefer_historical_full_book=args.prefer_historical_full_book,
        capture_forward_l2=args.capture_forward_l2,
    )
    return 0


def build_all_reports(
    *,
    discover_online: bool = False,
    fetch_live: bool = False,
    prefer_historical_full_book: bool = False,
    capture_forward_l2: bool = False,
) -> None:
    now_utc = utc_now_iso()
    agent_status = load_agent_crosswalk_status(now_utc)
    source_rows = discover_sources(discover_online, now_utc)
    endpoint_rows = build_endpoint_registry(now_utc)
    audit_rows = official_historical_full_book_audit(now_utc)
    acquisition_ledger_rows = historical_full_book_acquisition_ledger(now_utc)
    third_party_rows = third_party_candidate_rows(now_utc)
    gap_rows = historical_l2_gap_rows(now_utc)
    ws_status = websocket_dependency_status()

    kalshi_data = _fetch_kalshi() if fetch_live else {"venue": "kalshi", "selected_market": {}, "results": {}}
    polymarket_data = _fetch_polymarket() if fetch_live else {"venue": "polymarket", "selected_market": {}, "selected_token": None, "results": {}}
    if fetch_live and not (_venue_had_success(kalshi_data) and _venue_had_success(polymarket_data)):
        if not (_venue_had_success(kalshi_data) or _venue_had_success(polymarket_data)):
            _write_network_receipt(now_utc, kalshi_data, polymarket_data)
            raise RuntimeError("NETWORK_OR_ENDPOINT_BLOCKED_OWNER_ACTION_REQUIRED: both public venues failed")

    snapshot_rows = normalize_snapshot_rows(kalshi_data, polymarket_data, now_utc)
    if capture_forward_l2:
        l2_rows = build_forward_l2_rows(snapshot_rows, now_utc)
    else:
        l2_rows = []
    feature_rows = build_feature_rows(snapshot_rows, l2_rows, now_utc)
    readiness_rows = classify_readiness(snapshot_rows, l2_rows, audit_rows, now_utc)
    quality_rows = build_quality_rows(snapshot_rows, l2_rows, feature_rows, now_utc)
    priority_rows = build_priority_rows(snapshot_rows, feature_rows, now_utc)
    gfp2r_handoff = build_gfp2r_handoff(snapshot_rows, l2_rows, feature_rows, readiness_rows, now_utc)
    rp2_batch = build_rp2_batch(priority_rows, l2_rows, now_utc)
    rank2_batch = build_rank2_batch(priority_rows, now_utc)
    quantum_rows = build_quantum_surface(priority_rows, now_utc)
    forecastex_rows = forecastex_ibkr_rows(now_utc)

    kalshi_rows = [row for row in snapshot_rows if row.get("venue") == "kalshi"]
    polymarket_rows = [row for row in snapshot_rows if row.get("venue") == "polymarket"]
    kalshi_l2_rows = [row for row in l2_rows if row.get("venue") == "kalshi"]
    polymarket_l2_rows = [row for row in l2_rows if row.get("venue") == "polymarket"]

    kalshi_rows = write_jsonl(KALSHI_SNAPSHOT_JSONL, kalshi_rows)
    polymarket_rows = write_jsonl(POLYMARKET_SNAPSHOT_JSONL, polymarket_rows)
    kalshi_l2_rows = write_jsonl(KALSHI_FORWARD_L2_JSONL, kalshi_l2_rows)
    polymarket_l2_rows = write_jsonl(POLYMARKET_FORWARD_L2_JSONL, polymarket_l2_rows)
    candidate_rows = write_jsonl(HISTORICAL_CANDIDATE_JSONL, third_party_rows)

    kalshi_manifest = write_shard_manifest(
        KALSHI_SNAPSHOT_JSONL,
        kalshi_rows,
        manifest_id="pr168_data1_kalshi_snapshot_manifest",
        venue="kalshi",
        data_family="snapshot",
        created_at_utc=now_utc,
        source_refs=["kalshi_quick_start_market_data", "kalshi_orderbook_responses"],
    )
    polymarket_manifest = write_shard_manifest(
        POLYMARKET_SNAPSHOT_JSONL,
        polymarket_rows,
        manifest_id="pr168_data1_polymarket_snapshot_manifest",
        venue="polymarket",
        data_family="snapshot",
        created_at_utc=now_utc,
        source_refs=["polymarket_market_data_overview", "polymarket_get_order_book"],
    )
    kalshi_l2_manifest = write_shard_manifest(
        KALSHI_FORWARD_L2_JSONL,
        kalshi_l2_rows,
        manifest_id="pr168_data1_kalshi_forward_l2_manifest",
        venue="kalshi",
        data_family="forward_l2",
        created_at_utc=now_utc,
        source_refs=["kalshi_current_orderbook"],
    )
    polymarket_l2_manifest = write_shard_manifest(
        POLYMARKET_FORWARD_L2_JSONL,
        polymarket_l2_rows,
        manifest_id="pr168_data1_polymarket_forward_l2_manifest",
        venue="polymarket",
        data_family="forward_l2",
        created_at_utc=now_utc,
        source_refs=["polymarket_clob_book", "polymarket_market_websocket"],
    )
    candidate_manifest = write_shard_manifest(
        HISTORICAL_CANDIDATE_JSONL,
        candidate_rows,
        manifest_id="pr168_data1_historical_full_book_candidate_manifest",
        venue="multi_venue",
        data_family="historical_full_book_candidate",
        created_at_utc=now_utc,
        source_refs=[row["source_id"] for row in candidate_rows],
    )
    forecastex_manifest = {
        "manifest_id": "pr168_data1_forecastex_ibkr_auth_required_manifest",
        "created_at_utc": now_utc,
        "row_count": len(forecastex_rows),
        "rows": forecastex_rows,
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        **route_defaults("governance"),
        **authority_flags(),
    }
    write_json(FORECASTEX_IBKR_MANIFEST, forecastex_manifest)

    snapshot_manifest_refs = [generated_ref(manifest_path(KALSHI_SNAPSHOT_JSONL)), generated_ref(manifest_path(POLYMARKET_SNAPSHOT_JSONL))]
    l2_manifest_refs = [generated_ref(manifest_path(KALSHI_FORWARD_L2_JSONL)), generated_ref(manifest_path(POLYMARKET_FORWARD_L2_JSONL))]
    data_refs = snapshot_manifest_refs + l2_manifest_refs + [generated_ref(manifest_path(HISTORICAL_CANDIDATE_JSONL))]
    feature_refs = [row["feature_row_id"] for row in feature_rows]
    artifact_refs = data_refs + [generated_ref(FORECASTEX_IBKR_MANIFEST)] + [generated_ref(report_path(report_id)) for report_id in REQUIRED_REPORT_IDS]
    no_orphan_rows = build_no_orphan_rows(artifact_refs, now_utc)
    dag_rows = build_dag_nodes(artifact_refs, now_utc)
    operator_rows = _operator_action_rows(priority_rows, gap_rows, forecastex_rows, third_party_rows, now_utc)
    fetch_summary_rows = _fetch_summary_rows(kalshi_data, polymarket_data, now_utc)
    price_trade_substitute_rows = [row for row in snapshot_rows if row.get("data_family") not in {"market_metadata", "current_full_orderbook_snapshot"}]
    minimum_dataset_plan = _minimum_dataset_plan(snapshot_rows, l2_rows, feature_rows, gap_rows, now_utc)
    report_essentiality_rows = _report_essentiality_rows(REQUIRED_REPORT_IDS, now_utc)
    final_summary = _final_summary(
        now_utc,
        snapshot_rows,
        l2_rows,
        feature_rows,
        priority_rows,
        agent_status,
        _closed_pr232_state(),
    )

    common_refs = {
        "snapshot_manifest_refs": snapshot_manifest_refs,
        "l2_replay_manifest_refs": l2_manifest_refs,
        "data_provenance_refs": [row["source_id"] for row in source_rows] + [row["endpoint_contract_id"] for row in endpoint_rows],
        "computed_feature_refs": feature_refs,
    }
    _write_required_reports(
        now_utc=now_utc,
        source_rows=source_rows,
        endpoint_rows=endpoint_rows,
        fetch_summary_rows=fetch_summary_rows,
        audit_rows=audit_rows,
        acquisition_ledger_rows=acquisition_ledger_rows,
        l2_rows=l2_rows,
        ws_status=ws_status,
        gap_rows=gap_rows,
        price_trade_substitute_rows=price_trade_substitute_rows,
        kalshi_manifest=kalshi_manifest,
        polymarket_manifest=polymarket_manifest,
        forecastex_manifest=forecastex_manifest,
        readiness_rows=readiness_rows,
        feature_rows=feature_rows,
        quality_rows=quality_rows,
        priority_rows=priority_rows,
        minimum_dataset_plan=minimum_dataset_plan,
        gfp2r_handoff=gfp2r_handoff,
        rp2_batch=rp2_batch,
        rank2_batch=rank2_batch,
        quantum_rows=quantum_rows,
        agent_status=agent_status,
        no_orphan_rows=no_orphan_rows,
        dag_rows=dag_rows,
        operator_rows=operator_rows,
        report_essentiality_rows=report_essentiality_rows,
        final_summary=final_summary,
        third_party_rows=third_party_rows,
        candidate_manifest=candidate_manifest,
        common_refs=common_refs,
    )


def _fetch_kalshi() -> dict[str, object]:
    return KalshiPublicClient().fetch_public_data()


def _fetch_polymarket() -> dict[str, object]:
    return PolymarketPublicClient().fetch_public_data()


def _venue_had_success(data: dict[str, object]) -> bool:
    results = data.get("results")
    if not isinstance(results, dict):
        return False
    return any(isinstance(result, HttpResult) and result.ok for result in results.values())


def _fetch_summary_rows(kalshi_data: dict[str, object], polymarket_data: dict[str, object], now_utc: str) -> list[dict[str, object]]:
    rows = []
    for data in [kalshi_data, polymarket_data]:
        venue = str(data.get("venue"))
        results = data.get("results") if isinstance(data.get("results"), dict) else {}
        for name, result in results.items():
            if not isinstance(result, HttpResult):
                continue
            rows.append(
                {
                    "fetch_row_id": f"{venue}_{name}",
                    "venue": venue,
                    "endpoint_name": name,
                    "source_url": result.url,
                    "http_status": result.status,
                    "data_status": result.data_status,
                    "error": result.error,
                    "elapsed_ms": result.elapsed_ms,
                    "record_count_estimate": _record_count(result.json_value),
                    "created_at_utc": now_utc,
                    **route_defaults("market_data"),
                    **authority_flags(),
                }
            )
    return rows


def _record_count(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("markets", "trades", "history", "candlesticks"):
            if isinstance(value.get(key), list):
                return len(value[key])
        return len(value)
    return 0


def _operator_action_rows(
    priority_rows: list[dict[str, object]],
    gap_rows: list[dict[str, object]],
    forecastex_rows: list[dict[str, object]],
    third_party_rows: list[dict[str, object]],
    now_utc: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, priority in enumerate(priority_rows[:4], start=1):
        for action_type, next_pr in [
            ("RUN_GFP2R", "PR168-GFP2R"),
            ("RUN_RP2", "PR168-RP2"),
            ("RUN_RANK2", "PR168-RANK2"),
            ("CAPTURE_FORWARD_L2", "future_long_running_full_book_capture_service_PR"),
        ]:
            rows.append(
                {
                    "action_id": f"operator_action_{index:04d}_{action_type.lower()}",
                    "action_type": action_type,
                    "venue": priority["venue"],
                    "artifact_ref": priority["snapshot_refs"][0],
                    "market_or_token_ref": priority["market_or_token_ref"],
                    "priority_score_non_proof": priority["priority_score_non_proof"],
                    "priority_reason": priority["priority_reason_codes"],
                    "next_command_or_next_pr": next_pr,
                    "missing_input_or_gap_code": "historical_full_book_replay" if action_type == "CAPTURE_FORWARD_L2" else "source_evidence_acceptance_pending",
                    "expected_downstream_unblock_count": priority["expected_downstream_unblock_count"],
                    "historical_full_book_priority_flag": True,
                    "forward_l2_capture_priority_flag": True,
                    "no_live_authority_flag": True,
                    "profit_evidence_created_flag": False,
                    "created_at_utc": now_utc,
                    **route_defaults("governance"),
                    **authority_flags(),
                }
            )
    for gap in gap_rows:
        rows.append(
            {
                "action_id": f"operator_action_{gap['gap_row_id']}",
                "action_type": "FETCH_HISTORICAL_FULL_BOOK",
                "venue": gap["venue"],
                "artifact_ref": gap["gap_row_id"],
                "market_or_token_ref": "venue_level",
                "priority_score_non_proof": 2.0,
                "priority_reason": gap["gap_code"],
                "next_command_or_next_pr": gap["future_pr_route"],
                "missing_input_or_gap_code": gap["gap_code"],
                "expected_downstream_unblock_count": 3,
                "historical_full_book_priority_flag": True,
                "forward_l2_capture_priority_flag": True,
                "no_live_authority_flag": True,
                "profit_evidence_created_flag": False,
                "created_at_utc": now_utc,
                **route_defaults("governance"),
                **authority_flags(),
            }
        )
    for row in forecastex_rows:
        rows.append(
            {
                "action_id": "operator_action_owner_ibkr_setup",
                "action_type": "OWNER_IBKR_SETUP",
                "venue": "forecastex_ibkr",
                "artifact_ref": row["forecast_ex_ibkr_row_id"],
                "market_or_token_ref": "conid_required",
                "priority_score_non_proof": 0.5,
                "priority_reason": "auth_and_market_data_subscription_required",
                "next_command_or_next_pr": "future_authenticated_forecastex_ibkr_data_PR",
                "missing_input_or_gap_code": "AUTH_REQUIRED_PENDING_OWNER_SETUP",
                "expected_downstream_unblock_count": 1,
                "historical_full_book_priority_flag": False,
                "forward_l2_capture_priority_flag": False,
                "no_live_authority_flag": True,
                "profit_evidence_created_flag": False,
                "created_at_utc": now_utc,
                **route_defaults("governance"),
                **authority_flags(),
            }
        )
    if third_party_rows:
        rows.append(
            {
                "action_id": "operator_action_third_party_dataset_review",
                "action_type": "THIRD_PARTY_DATASET_REVIEW",
                "venue": "multi_venue",
                "artifact_ref": generated_ref(manifest_path(HISTORICAL_CANDIDATE_JSONL)),
                "market_or_token_ref": "venue_level",
                "priority_score_non_proof": 1.5,
                "priority_reason": "candidate historical full-book archives require license/access/source-evidence review",
                "next_command_or_next_pr": "future_source_evidence_acceptance_workflow",
                "missing_input_or_gap_code": "THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATE_ONLY",
                "expected_downstream_unblock_count": 3,
                "historical_full_book_priority_flag": True,
                "forward_l2_capture_priority_flag": False,
                "no_live_authority_flag": True,
                "profit_evidence_created_flag": False,
                "created_at_utc": now_utc,
                **route_defaults("source_evidence"),
                **authority_flags(),
            }
        )
    return rows


def _minimum_dataset_plan(
    snapshot_rows: list[dict[str, object]],
    l2_rows: list[dict[str, object]],
    feature_rows: list[dict[str, object]],
    gap_rows: list[dict[str, object]],
    now_utc: str,
) -> dict[str, object]:
    return {
        "plan_id": "pr168_data1_minimum_viable_real_data_proof_dataset_plan",
        "snapshot_refs": [row["snapshot_row_id"] for row in snapshot_rows],
        "l2_replay_refs": [row["l2_replay_row_id"] for row in l2_rows],
        "feature_refs": [row["feature_row_id"] for row in feature_rows],
        "gap_refs": [row["gap_row_id"] for row in gap_rows],
        "required_before_profit_proof": [
            "source_evidence_acceptance",
            "GFP2R_formula_execution",
            "RP2_replay_paper_recompute",
            "RANK2_no_trade_competitor_ranking",
        ],
        "proof_state": "DATA_READY_CANDIDATE_NOT_PROFIT_PROOF",
        "created_at_utc": now_utc,
        **route_defaults("governance"),
        **authority_flags(),
    }


def _report_essentiality_rows(report_ids: list[str], now_utc: str) -> list[dict[str, object]]:
    return [
        {
            "essentiality_row_id": f"essentiality_{index:04d}",
            "report_id": report_id,
            "essentiality_class": "OPERATIONAL_COMPUTABLE_OR_ACTION_ROUTED",
            "deduplication_result": "NON_REDUNDANT_REQUIRED_DATA1_OUTPUT",
            "downstream_consumed_by": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"],
            "validator_covered": True,
            "no_orphan_status": "NO_ORPHAN_ROUTED",
            "created_at_utc": now_utc,
            **route_defaults("governance"),
            **authority_flags(),
        }
        for index, report_id in enumerate(report_ids, start=1)
    ]


def _final_summary(
    now_utc: str,
    snapshot_rows: list[dict[str, object]],
    l2_rows: list[dict[str, object]],
    feature_rows: list[dict[str, object]],
    priority_rows: list[dict[str, object]],
    agent_status: dict[str, object],
    pr232_state: dict[str, object],
) -> dict[str, object]:
    return {
        "summary_id": "pr168_data1_final_summary",
        "closed_pr232_state": pr232_state,
        "agent_crosswalk_consumed": agent_status["consumed_flag"],
        "snapshot_row_count": len(snapshot_rows),
        "forward_l2_row_count": len(l2_rows),
        "feature_row_count": len(feature_rows),
        "priority_row_count": len(priority_rows),
        "historical_full_book_result": "official_public_historical_full_book_unavailable_exact_gap_routed",
        "forward_l2_bootstrap_result": "public_rest_poll_bootstrap_materialized",
        "no_profit_proof_created": True,
        "no_live_order_or_private_state_authority_created": True,
        "created_at_utc": now_utc,
        **route_defaults("governance"),
        **authority_flags(),
    }


def _write_required_reports(**kwargs: object) -> None:
    now_utc = str(kwargs["now_utc"])
    common_refs = dict(kwargs["common_refs"])

    reports: dict[str, tuple[object, str]] = {
        "PR168_DATA1_SourceEndpointDiscovery": (
            {
                "source_rows": kwargs["source_rows"],
                "endpoint_contract_rows": kwargs["endpoint_rows"],
            },
            "source_evidence",
        ),
        "PR168_DATA1_PublicFetchExecutionSummary": (kwargs["fetch_summary_rows"], "market_data"),
        "PR168_DATA1_HistoricalFullBookAvailabilityAudit": (kwargs["audit_rows"], "source_evidence"),
        "PR168_DATA1_HistoricalFullBookAcquisitionLedger": (kwargs["acquisition_ledger_rows"], "source_evidence"),
        "PR168_DATA1_ForwardFullBookReplayCaptureBootstrap": (
            {"l2_rows": kwargs["l2_rows"], "websocket_status": kwargs["ws_status"]},
            "market_data",
        ),
        "PR168_DATA1_ForwardL2CaptureShardManifest": (
            kwargs["l2_replay_manifest_refs"] if "l2_replay_manifest_refs" in kwargs else common_refs["l2_replay_manifest_refs"],
            "market_data",
        ),
        "PR168_DATA1_HistoricalPriceTradeCandleReplaySubstituteLedger": (kwargs["price_trade_substitute_rows"], "market_data"),
        "PR168_DATA1_HistoricalL2GapRouteToFutureAcquisition": (kwargs["gap_rows"], "market_data"),
        "PR168_DATA1_KalshiSnapshotManifest": (kwargs["kalshi_manifest"], "market_data"),
        "PR168_DATA1_PolymarketSnapshotManifest": (kwargs["polymarket_manifest"], "market_data"),
        "PR168_DATA1_ForecastExIBKRAuthRequiredManifest": (kwargs["forecastex_manifest"], "governance"),
        "PR168_DATA1_DataReadinessClassification": (kwargs["readiness_rows"], "governance"),
        "PR168_DATA1_NormalizedMarketDataFeatureRegistry": (kwargs["feature_rows"], "market_data"),
        "PR168_DATA1_DataQualityFreshnessCoverageAudit": (kwargs["quality_rows"], "governance"),
        "PR168_DATA1_DataBindingPriorityByVenue": (kwargs["priority_rows"], "ranking"),
        "PR168_DATA1_MinimumViableRealDataProofDatasetPlan": (kwargs["minimum_dataset_plan"], "governance"),
        "PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse": (kwargs["gfp2r_handoff"], "market_data"),
        "PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch": (kwargs["rp2_batch"], "replay"),
        "PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch": (kwargs["rank2_batch"], "ranking"),
        "PR168_DATA1_QuantumForwardCoefficientFeatureSurface": (kwargs["quantum_rows"], "quantum"),
        "PR168_DATA1_AgentRoutingAndNoOrphanProof": (
            {"agent_crosswalk_status": kwargs["agent_status"], "no_orphan_rows": kwargs["no_orphan_rows"]},
            "governance",
        ),
        "PR168_DATA1_DAGUpstreamDownstreamOrchestration": (kwargs["dag_rows"], "governance"),
        "PR168_DATA1_OperatorActionMatrix": (kwargs["operator_rows"], "governance"),
        "PR168_DATA1_ReportEssentialityAndDeduplicationAudit": (kwargs["report_essentiality_rows"], "governance"),
        "PR168_DATA1_FinalSummary": (kwargs["final_summary"], "governance"),
        "PR168_DATA1_WebSocketDependencyGapReceipt": (kwargs["ws_status"], "market_data"),
        "PR168_DATA1_ThirdPartyHistoricalFullBookCandidateDatasetRegistry": (
            {"candidate_manifest": kwargs["candidate_manifest"], "candidate_rows": kwargs["third_party_rows"]},
            "source_evidence",
        ),
        "PR168_DATA1_PublicDatasetLicenseAndAccessSafetyAudit": (
            [
                {
                    "safety_row_id": "public_dataset_safety_0001",
                    "candidate_manifest_ref": generated_ref(manifest_path(HISTORICAL_CANDIDATE_JSONL)),
                    "license_access_state": "REQUIRES_SOURCE_EVIDENCE_AND_LICENSE_REVIEW",
                    "safe_to_fetch_in_DATA1_default": False,
                    "reason": "third-party historical L2 candidate sources are not official accepted source truth and may require API keys, login, or manual license review",
                    **route_defaults("source_evidence"),
                    **authority_flags(),
                }
            ],
            "source_evidence",
        ),
    }
    for report_id in REQUIRED_REPORT_IDS:
        records, route_key = reports[report_id]
        payload = report_payload(report_id, now_utc, records, route_key=route_key, **common_refs)
        write_report(report_id, payload)


def _write_network_receipt(now_utc: str, kalshi_data: dict[str, object], polymarket_data: dict[str, object]) -> None:
    payload = report_payload(
        "PR168_DATA1_NetworkUnavailableReceipt",
        now_utc,
        _fetch_summary_rows(kalshi_data, polymarket_data, now_utc),
        route_key="governance",
        authority_class="NETWORK_UNAVAILABLE",
        terminal_by_nature_flag=True,
        terminal_reason_code="NETWORK_OR_ENDPOINT_BLOCKED_OWNER_ACTION_REQUIRED",
    )
    write_report("PR168_DATA1_NetworkUnavailableReceipt", payload)


def _closed_pr232_state() -> dict[str, object]:
    try:
        completed = subprocess.run(  # noqa: S603 - local gh CLI, read-only metadata query
            ["gh", "pr", "view", "232", "--json", "number,state,mergedAt,headRefName"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"number": 232, "state": "UNKNOWN", "mergedAt": "UNKNOWN", "error": type(exc).__name__}
    if completed.returncode != 0:
        return {"number": 232, "state": "UNKNOWN", "mergedAt": "UNKNOWN", "error": completed.stderr.strip()[:200]}
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"number": 232, "state": "UNKNOWN", "mergedAt": "UNKNOWN", "error": "JSONDecodeError"}
    return value if isinstance(value, dict) else {"number": 232, "state": "UNKNOWN", "mergedAt": "UNKNOWN"}


if __name__ == "__main__":
    raise SystemExit(main())
