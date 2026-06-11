"""Fail-closed validator for PR166-S generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import ZERO_AUTHORITY_KEYS, validate_record_authority
from .central_vocab import AUTHORITY_CLASS, FORBIDDEN_ORDER_STATES, NO_ORPHAN_STATUSES
from .json_io import read_json, records_from_payload
from .report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, load_report_records


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    _validate_serialized_repo_refs(reports, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    _validate_manifest(reports, records, failures)
    _validate_counts(repo_root, records, failures)
    _validate_execution_contracts(records, failures)
    _validate_repair_separation(records, failures)
    _validate_authority(records, failures)
    _validate_connectivity(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-S report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-S report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR166-S schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for rel_path in p.REQUIRED_INPUTS:
        normalized = p.normalize_repo_ref(rel_path)
        if not p.resolve_repo_relative(repo_root, normalized).exists():
            failures.append(f"missing required PR166-S upstream artifact: {normalized}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR166-S", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(payload.get("artifact_path"), failures, f"{filename} missing artifact path")
        _expect(payload.get("upstream_pr_refs"), failures, f"{filename} missing upstream refs")
        _expect(payload.get("downstream_pr_refs"), failures, f"{filename} missing downstream refs")
        if filename in p.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root must not duplicate row records")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} sharded row count mismatch")
        else:
            _expect(payload.get("record_count") == len(records_from_payload(payload)), failures, f"{filename} record_count mismatch")
        path = repo_root / p.GENERATED_DIR / filename
        _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds root report limit")
        for shard_path in payload.get("shard_files") or []:
            resolved = p.resolve_repo_relative(repo_root, shard_path)
            _expect(resolved.exists(), failures, f"{filename} missing shard: {shard_path}")
            if resolved.exists():
                _expect(resolved.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_path} exceeds shard limit")
        for record in records[filename]:
            for field in (
                "upstream_pr_refs",
                "downstream_pr_refs",
                "owning_agent",
                "consuming_agent",
                "downstream_action_type",
                "authority_boundary_ref",
                "validator_ref",
                "manifest_ref",
                "no_orphan_status",
            ):
                _expect(record.get(field) not in (None, "", []), failures, f"{filename} row missing {field}")
            _expect(record.get("no_orphan_status") in NO_ORPHAN_STATUSES, failures, f"{filename} row has invalid no_orphan_status")
            failures.extend(f"{filename} {failure}" for failure in validate_record_authority(record).failures)
            if record.get("terminal_status_flag") is True:
                _expect(record.get("terminal_status_reason"), failures, f"{filename} terminal row missing reason")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR166_S_ReportManifest.report.json"]
    listed = {row.get("report_filename") for row in manifest}
    _expect(listed == set(p.REPORT_FILENAMES), failures, "manifest does not list exactly the PR166-S reports")
    for row in manifest:
        filename = row["report_filename"]
        _expect(row.get("row_count") == reports[filename].get("record_count"), failures, f"manifest row count mismatch: {filename}")
        for shard_path in row.get("shard_paths") or []:
            _expect(shard_path in reports[filename].get("shard_files", []), failures, f"manifest shard mismatch: {shard_path}")


def _validate_counts(repo_root: Path, records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_S_FinalSummary.report.json"][0]
    pr165_d_summary = read_json(repo_root / p.GENERATED_DIR / "PR165_D_FinalSummary.report.json")["records"][0]
    selected_batch_count = int(pr165_d_summary["selected_batch_count"])
    ready_count = int(pr165_d_summary["selected_ready_retest_count"])
    repair_count = int(pr165_d_summary["selected_repair_before_retest_count"])
    quantum_count = int(pr165_d_summary["quantum_selection_route_rows"])
    equality = {
        "selected_batch_consumption_rows": len(records["PR166_S_SelectedBatchConsumptionRegistry.report.json"]),
        "replay_episode_rows": len(records["PR166_S_ReplayEpisodeRegistry.report.json"]),
        "paper_episode_rows": len(records["PR166_S_PaperEpisodeRegistry.report.json"]),
        "event_stream_rows": len(records["PR166_S_EventStreamRegistry.report.json"]),
        "execution_model_assumption_rows": len(records["PR166_S_ExecutionModelAssumptionLedger.report.json"]),
        "execution_sensitivity_scenario_rows": len(records["PR166_S_ExecutionSensitivityScenarioGrid.report.json"]),
        "order_intent_rows": len(records["PR166_S_OrderIntentRegistry.report.json"]),
        "order_state_transition_rows": len(records["PR166_S_OrderStateTransitionLedger.report.json"]),
        "simulated_fill_rows": len(records["PR166_S_SimulatedFillLedger.report.json"]),
        "fee_model_rows": len(records["PR166_S_FeeModelLedger.report.json"]),
        "spread_model_rows": len(records["PR166_S_SpreadModelLedger.report.json"]),
        "slippage_model_rows": len(records["PR166_S_SlippageModelLedger.report.json"]),
        "latency_model_rows": len(records["PR166_S_LatencyModelLedger.report.json"]),
        "liquidity_model_rows": len(records["PR166_S_LiquidityModelLedger.report.json"]),
        "market_impact_model_rows": len(records["PR166_S_MarketImpactModelLedger.report.json"]),
        "execution_cost_rows": len(records["PR166_S_ExecutionCostLedger.report.json"]),
        "replay_run_result_rows": len(records["PR166_S_ReplayRunResultRegistry.report.json"]),
        "paper_run_result_rows": len(records["PR166_S_PaperRunResultRegistry.report.json"]),
        "result_attribution_rows": len(records["PR166_S_ResultAttributionLedger.report.json"]),
        "result_confidence_rows": len(records["PR166_S_ResultConfidenceRegistry.report.json"]),
        "score_refresh_candidate_rows": len(records["PR166_S_ScoreRefreshCandidateRegistry.report.json"]),
        "memory_refresh_candidate_rows": len(records["PR166_S_MemoryRefreshCandidateRegistry.report.json"]),
        "repair_feedback_route_rows": len(records["PR166_S_RepairFeedbackRouter.report.json"]),
        "quantum_advisory_passthrough_rows": len(records["PR166_S_QuantumAdvisoryPassthrough.report.json"]),
        "agent_execution_contract_rows": len(records["PR166_S_AgentExecutionContract.report.json"]),
        "agent_execution_handoff_rows": len(records["PR166_S_AgentExecutionHandoff.report.json"]),
        "dashboard_execution_handoff_rows": len(records["PR166_S_DashboardExecutionHandoff.report.json"]),
        "governance_execution_handoff_rows": len(records["PR166_S_GovernanceExecutionHandoff.report.json"]),
        "commander_execution_handoff_rows": len(records["PR166_S_CommanderExecutionHandoff.report.json"]),
        "lineage_graph_rows": len(records["PR166_S_LineageGraph.report.json"]),
        "point_in_time_audit_rows": len(records["PR166_S_PointInTimeExecutionAudit.report.json"]),
        "no_lookahead_audit_rows": len(records["PR166_S_NoLookaheadAudit.report.json"]),
    }
    for field, actual in equality.items():
        _expect(summary.get(field) == actual, failures, f"summary {field} mismatch")
    _expect(equality["selected_batch_consumption_rows"] >= selected_batch_count, failures, "selected batch consumption undercounts PR165-D batches")
    _expect(equality["replay_episode_rows"] >= selected_batch_count, failures, "replay episodes undercount selected batches")
    _expect(equality["paper_episode_rows"] >= selected_batch_count, failures, "paper episodes undercount selected batches")
    _expect(equality["order_intent_rows"] >= ready_count, failures, "order intents undercount ready retest candidates")
    for report in (
        "PR166_S_FeeModelLedger.report.json",
        "PR166_S_SpreadModelLedger.report.json",
        "PR166_S_SlippageModelLedger.report.json",
        "PR166_S_LatencyModelLedger.report.json",
        "PR166_S_LiquidityModelLedger.report.json",
        "PR166_S_MarketImpactModelLedger.report.json",
        "PR166_S_ExecutionCostLedger.report.json",
    ):
        _expect(len(records[report]) >= ready_count, failures, f"{report} undercounts order intents")
    _expect(equality["repair_feedback_route_rows"] >= repair_count, failures, "repair feedback undercounts repair-before-retest rows")
    _expect(equality["quantum_advisory_passthrough_rows"] >= quantum_count, failures, "quantum passthrough undercounts PR165-D quantum rows")
    _expect(equality["commander_execution_handoff_rows"] >= equality["replay_run_result_rows"] + equality["paper_run_result_rows"], failures, "commander handoff undercounts run results")
    for field in (
        "metadata_only_rows",
        "placeholder_rows",
        "unknown_status_rows",
        "generic_blocked_rows",
        "live_authority_rows",
        "fake_live_result_count",
        "source_truth_acceptance_count",
        "profit_evidence_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
    ):
        _expect(summary.get(field) == 0, failures, f"summary {field} must be 0")
    _expect(summary.get("orphan_counts_all_zero") is True, failures, "orphan counts not all zero")
    _expect(summary.get("authority_counts_all_zero") is True, failures, "authority counts not all zero")


def _validate_execution_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    orders = records["PR166_S_OrderIntentRegistry.report.json"]
    transitions = records["PR166_S_OrderStateTransitionLedger.report.json"]
    fills = records["PR166_S_SimulatedFillLedger.report.json"]
    costs = records["PR166_S_ExecutionCostLedger.report.json"]
    transition_by_order = {row["order_intent_id"] for row in transitions}
    fill_by_order = {row["order_intent_id"] for row in fills}
    cost_by_order = {row["order_intent_id"] for row in costs}
    for order in orders:
        _expect(order["order_intent_id"] in transition_by_order, failures, "order intent lacks state transitions")
        _expect(order["order_intent_id"] in fill_by_order, failures, "order intent lacks fill record")
        _expect(order["order_intent_id"] in cost_by_order, failures, "order intent lacks cost record")
        _expect(order.get("no_live_authority") is True, failures, "order intent missing no_live_authority")
    for transition in transitions:
        _expect(transition.get("to_state") not in FORBIDDEN_ORDER_STATES, failures, f"forbidden order state {transition.get('to_state')}")
    for cost in costs:
        for field in (
            "gross_edge",
            "spread_cost",
            "maker_taker_fees",
            "slippage_cost",
            "market_impact_cost",
            "latency_drag",
            "liquidity_drag",
            "adverse_selection_drag",
            "settlement_payoff_adjustment",
            "net_edge_after_costs",
        ):
            _expect(field in cost, failures, f"cost row missing {field}")


def _validate_repair_separation(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    repair_candidates = {
        row["candidate_packet_id"]
        for row in records["PR166_S_RepairFeedbackRouter.report.json"]
        if row.get("executed_as_ready_retest_in_pr166_s") is False
    }
    order_candidates = {row["candidate_packet_id"] for row in records["PR166_S_OrderIntentRegistry.report.json"]}
    overlap = repair_candidates & order_candidates
    _expect(not overlap, failures, f"repair-before-retest candidates executed as ready: {sorted(overlap)[:5]}")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key in ZERO_AUTHORITY_KEYS:
                if int(row.get(key, 0) or 0) != 0:
                    failures.append(f"{filename} row has nonzero authority count {key}")
            if row.get("no_live_authority") is False:
                failures.append(f"{filename} row allows live authority")
            if row.get("no_profit_evidence") is False:
                failures.append(f"{filename} row allows profit evidence")
            if row.get("no_backend_execution") is False:
                failures.append(f"{filename} row allows quantum backend execution")


def _validate_connectivity(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    _expect(records["PR166_S_PRFileConnectivityAudit.report.json"], failures, "missing PR file connectivity rows")
    _expect(records["PR166_S_RowValueConnectivityAudit.report.json"], failures, "missing row value connectivity rows")
    _expect(records["PR166_S_TerminalArtifactReceiptRegistry.report.json"], failures, "missing terminal receipt rows")
    for row in records["PR166_S_RowValueConnectivityAudit.report.json"]:
        total = int(row.get("total_rows", 0) or 0)
        for field in (
            "rows_with_upstream_refs",
            "rows_with_downstream_refs",
            "rows_with_owning_agent",
            "rows_with_consuming_agent",
            "rows_with_authority_boundary",
            "rows_with_validator_coverage",
            "rows_with_no_orphan_status",
        ):
            _expect(int(row.get(field, 0) or 0) == total, failures, f"connectivity coverage mismatch {row.get('report_filename')} {field}")


def _validate_serialized_repo_refs(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    forbidden_values = {"UNKNOWN", "PLACEHOLDER", "METADATA_ONLY", "BLOCKED", "FUTURE_WORK_ONLY", "UNROUTED", "ORPHAN", "NONE"}
    for filename, payload in reports.items():
        for value in _flatten_values(payload):
            if "\\" in value:
                failures.append(f"{filename} serialized repo ref contains backslash: {value}")
            if value in forbidden_values:
                failures.append(f"{filename} contains forbidden generic value: {value}")


def _flatten_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return []


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
