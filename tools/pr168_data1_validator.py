#!/usr/bin/env python3
"""Offline validator for committed PR168-DATA1 artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.pr168_data1_agent_router import AGENT_DUTY_PATH, AGENT_ROSTER_PATH
from tools.pr168_data1_config import (
    FORECASTEX_IBKR_MANIFEST,
    HISTORICAL_CANDIDATE_JSONL,
    KALSHI_FORWARD_L2_JSONL,
    KALSHI_SNAPSHOT_JSONL,
    POLYMARKET_FORWARD_L2_JSONL,
    POLYMARKET_SNAPSHOT_JSONL,
    REQUIRED_REPORT_IDS,
    VALID_READINESS_STATES,
    manifest_path,
    report_path,
)


FORBIDDEN_TRUE_FLAGS = [
    "live_authority_created_flag",
    "profit_evidence_created_flag",
    "source_truth_acceptance_created_flag",
    "connector_semantic_binding_created_flag",
    "private_state_access_created_flag",
    "order_authority_created_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "qtt_sha_or_atomicrows_hash_authority_flag",
]

SNAPSHOT_REQUIRED_FIELDS = [
    "snapshot_row_id",
    "venue",
    "data_family",
    "as_of_utc",
    "source_url",
    "endpoint_name",
    "http_status",
    "data_status",
    "source_tier",
    "historical_full_book_state",
    "forward_l2_capture_state",
    "data_authority_class",
    "accepted_truth_flag",
    "candidate_only_flag",
    "normalized_record",
    "qtt_capture_timestamp_utc",
    "downstream_consumers",
    "downstream_pr_refs",
    "owning_agent",
    "consumer_agents",
    "validator_refs",
    "test_refs",
    "no_orphan_status",
]

L2_REQUIRED_FIELDS = [
    "l2_replay_row_id",
    "venue",
    "capture_session_id",
    "capture_mode",
    "event_type",
    "bids",
    "asks",
    "yes_bids",
    "no_bids",
    "source_url",
    "endpoint_or_ws_channel",
    "accepted_truth_flag",
    "candidate_only_flag",
    "venue_raw_hash_authority_flag",
    "no_orphan_status",
]


def run_validation(mode: str = "all") -> None:
    artifacts = _load_artifacts()
    _validate_required_reports(artifacts["reports"])
    _validate_no_hard_cap_and_no_useless_outputs(artifacts["reports"])
    _validate_manifests_and_rows(artifacts)
    _validate_historical_full_book_audit(artifacts["reports"])
    _validate_authority_boundaries(artifacts)
    _validate_readiness_states(artifacts["reports"])
    _validate_features(artifacts["reports"])
    _validate_downstream_handoffs(artifacts["reports"])
    _validate_agent_crosswalk(artifacts["reports"])
    _validate_no_orphan(artifacts)
    _validate_operator_actions(artifacts["reports"])
    _validate_ci_offline(mode)


def _load_artifacts() -> dict[str, Any]:
    reports = {report_id: _load_json(report_path(report_id)) for report_id in REQUIRED_REPORT_IDS}
    return {
        "reports": reports,
        "kalshi_rows": _load_jsonl(KALSHI_SNAPSHOT_JSONL),
        "polymarket_rows": _load_jsonl(POLYMARKET_SNAPSHOT_JSONL),
        "kalshi_l2_rows": _load_jsonl(KALSHI_FORWARD_L2_JSONL),
        "polymarket_l2_rows": _load_jsonl(POLYMARKET_FORWARD_L2_JSONL),
        "candidate_rows": _load_jsonl(HISTORICAL_CANDIDATE_JSONL),
        "manifests": [
            _load_json(manifest_path(KALSHI_SNAPSHOT_JSONL)),
            _load_json(manifest_path(POLYMARKET_SNAPSHOT_JSONL)),
            _load_json(manifest_path(KALSHI_FORWARD_L2_JSONL)),
            _load_json(manifest_path(POLYMARKET_FORWARD_L2_JSONL)),
            _load_json(manifest_path(HISTORICAL_CANDIDATE_JSONL)),
            _load_json(FORECASTEX_IBKR_MANIFEST),
        ],
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"missing json artifact: {path}")
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"json artifact is not object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise AssertionError(f"missing jsonl artifact: {path}")
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise AssertionError(f"jsonl row is not object: {path}:{line_number}")
            rows.append(value)
    if not rows:
        raise AssertionError(f"jsonl artifact has no rows: {path}")
    return rows


def _validate_required_reports(reports: dict[str, dict[str, Any]]) -> None:
    for report_id, report in reports.items():
        assert report["report_id"] == report_id
        for key in [
            "report_version",
            "created_by_tool",
            "created_at_utc",
            "upstream_input_refs",
            "snapshot_manifest_refs",
            "l2_replay_manifest_refs",
            "data_provenance_refs",
            "computed_feature_refs",
            "owning_agent",
            "downstream_consumers",
            "downstream_pr_refs",
            "validator_refs",
            "test_refs",
            "no_orphan_status",
            "authority_class",
            "records",
        ]:
            if key not in report:
                raise AssertionError(f"{report_id} missing {key}")
        _assert_false_flags(report, report_id)
        if report["records"] in (None, [], {}, ""):
            raise AssertionError(f"{report_id} has empty records")


def _validate_no_hard_cap_and_no_useless_outputs(reports: dict[str, dict[str, Any]]) -> None:
    if len(reports) < 25:
        raise AssertionError("report family unexpectedly small; no hard report cap proof missing")
    essentiality = reports["PR168_DATA1_ReportEssentialityAndDeduplicationAudit"]["records"]
    if not isinstance(essentiality, list) or len(essentiality) < len(REQUIRED_REPORT_IDS):
        raise AssertionError("report essentiality audit does not cover required reports")
    for row in essentiality:
        if row.get("essentiality_class") != "OPERATIONAL_COMPUTABLE_OR_ACTION_ROUTED":
            raise AssertionError(f"non-operational essentiality row: {row}")


def _validate_manifests_and_rows(artifacts: dict[str, Any]) -> None:
    rows = artifacts["kalshi_rows"] + artifacts["polymarket_rows"]
    l2_rows = artifacts["kalshi_l2_rows"] + artifacts["polymarket_l2_rows"]
    if not artifacts["kalshi_rows"]:
        raise AssertionError("Kalshi snapshot rows missing")
    if not artifacts["polymarket_rows"]:
        raise AssertionError("Polymarket snapshot rows missing")
    for manifest in artifacts["manifests"]:
        if int(manifest.get("row_count", 0)) <= 0:
            raise AssertionError(f"manifest has no rows and no terminal route: {manifest.get('manifest_id')}")
        if not manifest.get("downstream_consumers"):
            raise AssertionError(f"manifest missing downstream consumers: {manifest.get('manifest_id')}")
        _assert_false_flags(manifest, str(manifest.get("manifest_id")))
    for row in rows:
        for field in SNAPSHOT_REQUIRED_FIELDS:
            if field not in row:
                raise AssertionError(f"snapshot row missing {field}: {row.get('snapshot_row_id')}")
        if not row["source_url"] or not row["endpoint_name"]:
            raise AssertionError(f"snapshot row missing source endpoint: {row.get('snapshot_row_id')}")
        if row.get("accepted_truth_flag") is not False:
            raise AssertionError(f"snapshot row accepted truth: {row.get('snapshot_row_id')}")
        _assert_false_flags(row, str(row.get("snapshot_row_id")))
    for row in l2_rows:
        for field in L2_REQUIRED_FIELDS:
            if field not in row:
                raise AssertionError(f"l2 row missing {field}: {row.get('l2_replay_row_id')}")
        if row.get("venue_raw_hash_authority_flag") is not False:
            raise AssertionError(f"l2 row creates venue hash authority: {row.get('l2_replay_row_id')}")
        _assert_false_flags(row, str(row.get("l2_replay_row_id")))


def _validate_historical_full_book_audit(reports: dict[str, dict[str, Any]]) -> None:
    records = reports["PR168_DATA1_HistoricalFullBookAvailabilityAudit"]["records"]
    venues = {row["venue"]: row for row in records}
    for venue in ("kalshi", "polymarket"):
        row = venues.get(venue)
        if not row:
            raise AssertionError(f"missing historical full-book audit for {venue}")
        if row.get("availability_classification") != "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON":
            raise AssertionError(f"{venue} historical full-book audit lacks exact gap")
        if "full-book" not in str(row.get("exact_reason")).lower() and "full book" not in str(row.get("exact_reason")).lower():
            raise AssertionError(f"{venue} exact reason is not specific")
    gaps = reports["PR168_DATA1_HistoricalL2GapRouteToFutureAcquisition"]["records"]
    if len(gaps) < 2:
        raise AssertionError("historical L2 gap routes missing")


def _validate_authority_boundaries(artifacts: dict[str, Any]) -> None:
    used_rows = artifacts["kalshi_rows"] + artifacts["polymarket_rows"] + artifacts["kalshi_l2_rows"] + artifacts["polymarket_l2_rows"]
    forbidden_endpoint_tokens = ["/orders", "/portfolio", "/positions", "/balance", "/balances", "/order/"]
    for row in used_rows:
        haystack = f"{row.get('source_url')} {row.get('endpoint_name')} {row.get('endpoint_or_ws_channel')}".lower()
        for token in forbidden_endpoint_tokens:
            if token in haystack:
                raise AssertionError(f"private/order endpoint used in fetched row: {row}")
        forbidden_words = ["real_positive", "real_negative", "champion_eligible", "quantum advantage"]
        if any(word in json.dumps(row, sort_keys=True).lower() for word in forbidden_words):
            raise AssertionError(f"forbidden proof/live wording in row: {row}")


def _validate_readiness_states(reports: dict[str, dict[str, Any]]) -> None:
    records = reports["PR168_DATA1_DataReadinessClassification"]["records"]
    states = {row.get("data_readiness_state") for row in records}
    allowed = VALID_READINESS_STATES | {
        "DATA_READY_PUBLIC_REAL_ORDERBOOK_CANDIDATE",
        "DATA_READY_PUBLIC_REAL_SNAPSHOT_CANDIDATE",
        "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON",
    }
    bad = states - allowed
    if bad:
        raise AssertionError(f"invalid readiness states: {sorted(bad)}")
    if "DATA_READY_PUBLIC_REAL_ORDERBOOK_CANDIDATE" not in states:
        raise AssertionError("orderbook readiness state missing")


def _validate_features(reports: dict[str, dict[str, Any]]) -> None:
    features = reports["PR168_DATA1_NormalizedMarketDataFeatureRegistry"]["records"]
    if not isinstance(features, list) or len(features) < 10:
        raise AssertionError("not enough computable feature rows")
    names = {row.get("feature_name") for row in features}
    required = {"best_yes_bid", "best_yes_ask", "spread_yes", "depth_within_1c", "historical_full_book_gap_flag", "forward_l2_capture_available_flag"}
    if not required <= names:
        raise AssertionError(f"missing required features: {sorted(required - names)}")
    for row in features:
        if not row.get("snapshot_row_refs"):
            raise AssertionError(f"feature row missing snapshot refs: {row.get('feature_row_id')}")
        if row.get("profit_evidence_created_flag") is not False or row.get("live_authority_created_flag") is not False:
            raise AssertionError(f"feature row creates proof/live authority: {row.get('feature_row_id')}")
        if "profit" in str(row.get("feature_name")).lower():
            raise AssertionError(f"profit feature not allowed: {row.get('feature_row_id')}")


def _validate_downstream_handoffs(reports: dict[str, dict[str, Any]]) -> None:
    gfp = reports["PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse"]["records"]
    if gfp.get("proof_state") != "DATA_READY_CANDIDATE_NOT_PROFIT_PROOF":
        raise AssertionError("GFP2R handoff proof state invalid")
    if int(gfp.get("data_ready_orderbook_snapshot_count", 0)) < 2:
        raise AssertionError("GFP2R handoff lacks both venue orderbook rows")
    if not reports["PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch"]["records"]:
        raise AssertionError("RP2 batch missing")
    rank = reports["PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch"]["records"]
    if not rank or any(row.get("champion_challenger_seed_only_flag") is not True for row in rank):
        raise AssertionError("RANK2 seed-only handoff missing")
    quantum = reports["PR168_DATA1_QuantumForwardCoefficientFeatureSurface"]["records"]
    if not quantum or any(row.get("quantum_backend_execution_flag") or row.get("quantum_advantage_claim_flag") for row in quantum):
        raise AssertionError("quantum surface violated no-backend/no-advantage boundary")
    if any(not row.get("classical_fallback_required_flag") for row in quantum):
        raise AssertionError("quantum surface missing classical fallback")


def _validate_agent_crosswalk(reports: dict[str, dict[str, Any]]) -> None:
    if not AGENT_ROSTER_PATH.exists() or not AGENT_DUTY_PATH.exists():
        blocker = report_path("PR168_DATA1_MissingAgentCrosswalkBlocker")
        if not blocker.exists():
            raise AssertionError("PR165-D2 crosswalk missing and blocker report absent")
        raise AssertionError("PR165-D2 agent crosswalk missing")
    status = reports["PR168_DATA1_AgentRoutingAndNoOrphanProof"]["records"]["agent_crosswalk_status"]
    if status.get("consumed_flag") is not True:
        raise AssertionError("PR165-D2 agent crosswalk not consumed")


def _validate_no_orphan(artifacts: dict[str, Any]) -> None:
    reports = artifacts["reports"]
    no_orphan = reports["PR168_DATA1_AgentRoutingAndNoOrphanProof"]["records"]["no_orphan_rows"]
    if not no_orphan:
        raise AssertionError("no-orphan proof rows missing")
    for row in artifacts["kalshi_rows"] + artifacts["polymarket_rows"] + artifacts["kalshi_l2_rows"] + artifacts["polymarket_l2_rows"]:
        if row.get("no_orphan_status") != "NO_ORPHAN_ROUTED":
            raise AssertionError(f"orphan row: {row}")
        if not row.get("downstream_pr_refs") or not row.get("validator_refs") or not row.get("test_refs"):
            raise AssertionError(f"row missing downstream/test refs: {row}")
    dag = reports["PR168_DATA1_DAGUpstreamDownstreamOrchestration"]["records"]
    if len(dag) < 8 or any(row.get("no_orphan_status") != "NO_ORPHAN_ROUTED" for row in dag):
        raise AssertionError("DAG no-orphan proof incomplete")


def _validate_operator_actions(reports: dict[str, dict[str, Any]]) -> None:
    actions = reports["PR168_DATA1_OperatorActionMatrix"]["records"]
    action_types = {row.get("action_type") for row in actions}
    required = {"RUN_GFP2R", "RUN_RP2", "RUN_RANK2", "CAPTURE_FORWARD_L2", "OWNER_IBKR_SETUP", "THIRD_PARTY_DATASET_REVIEW", "FETCH_HISTORICAL_FULL_BOOK"}
    if not required <= action_types:
        raise AssertionError(f"operator matrix missing actions: {sorted(required - action_types)}")
    for row in actions:
        if not row.get("next_command_or_next_pr") or row.get("no_live_authority_flag") is not True:
            raise AssertionError(f"operator row is not actionable/no-live: {row}")


def _validate_ci_offline(mode: str) -> None:
    gate_text = Path("tools/run_validation_gates.py").read_text(encoding="utf-8")
    if "build_pr168_data1_public_market_data_snapshots.py\", \"--fetch-live" in gate_text:
        raise AssertionError("CI gate must not run DATA1 live fetch")
    if mode == "closed_pr232_not_merged_guard":
        final = _load_json(report_path("PR168_DATA1_FinalSummary"))["records"]["closed_pr232_state"]
        if final.get("state") != "CLOSED" or final.get("mergedAt") is not None:
            raise AssertionError(f"PR232 guard failed: {final}")


def _assert_false_flags(row: dict[str, Any], label: str) -> None:
    for flag in FORBIDDEN_TRUE_FLAGS:
        if row.get(flag) is True:
            raise AssertionError(f"{label} has forbidden true flag {flag}")


if __name__ == "__main__":
    run_validation("cli")
