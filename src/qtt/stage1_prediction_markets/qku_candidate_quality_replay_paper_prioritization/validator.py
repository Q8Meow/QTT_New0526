"""PR161D artifact validator."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from . import constants as c
from .io import records_from_payload
from .models import ValidationResult


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR161D report: {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            failures.append(f"PR161D report is not an object: {path}")
            continue
        reports[filename] = payload

    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))

    quality = _load_records(repo_root, reports["PR161D_QKUQualityScoreRegistry.report.json"])
    components = _load_records(repo_root, reports["PR161D_QKUScoreComponentBreakdown.report.json"])
    lanes = _load_records(repo_root, reports["PR161D_QKUQualityLaneClassification.report.json"])
    replay = _load_records(repo_root, reports["PR161D_QKUReplayPaperPriorityQueue.report.json"])
    online = _load_records(repo_root, reports["PR161D_QKUOnlineEnrichmentCoverage.report.json"])
    agent_network = _load_records(repo_root, reports["PR161D_QTTAgentRoleNetworkRegistry.report.json"])
    agent_routes = _load_records(repo_root, reports["PR161D_QKUAgentGraphRoutingMatrix.report.json"])
    tasks = _load_records(repo_root, reports["PR161D_QKUAgentTaskQueue.report.json"])
    rankings = _load_records(repo_root, reports["PR161D_QKUCategoryRankingRegistry.report.json"])
    result_slots = _load_records(repo_root, reports["PR161D_QKUResultBackedRankingSlots.report.json"])
    scenarios = _load_records(repo_root, reports["PR161D_QKUScenarioOutcomeMatrix.report.json"])
    bundles = _load_records(repo_root, reports["PR161D_QKUCombinationCandidateRegistry.report.json"])
    boundedness = _load_records(repo_root, reports["PR161D_QKUCombinationGenerationBoundedness.report.json"])
    market_policy = _load_records(repo_root, reports["PR161D_QKUMarketBundleActivationPolicy.report.json"])
    market_dashboard = _load_records(repo_root, reports["PR161D_QKUMarketBundleActivationDashboardOptions.report.json"])
    market_active = _load_records(repo_root, reports["PR161D_QKUMarketActiveBundleSet.report.json"])
    market_dormant = _load_records(repo_root, reports["PR161D_QKUMarketBundleDormancyQueue.report.json"])
    agent_slices = _load_records(repo_root, reports["PR161D_QKUAgentRoleBundleSlice.report.json"])
    reference_fanout = _load_records(repo_root, reports["PR161D_QKUAgentRoleBundleReferenceFanout.report.json"])
    patterns = _load_records(repo_root, reports["PR161D_QKUFutureProfitabilityPatternFields.report.json"])
    quantum = _load_records(repo_root, reports["PR161D_QKUQuantumPriorityQueue.report.json"])
    classical = _load_records(repo_root, reports["PR161D_QKUClassicalBaselinePriorityQueue.report.json"])
    hybrid = _load_records(repo_root, reports["PR161D_QKUHybridArbitrationPriorityQueue.report.json"])
    graph_audit = _load_records(repo_root, reports["PR161D_QKUGraphConsumptionAudit.report.json"])
    final_summary = reports["PR161D_FinalSummary.report.json"]

    _expect(len(quality) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "quality score count must be 9360")
    _expect(len(components) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "component count must be 9360")
    _expect(len(lanes) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "lane count must be 9360")
    _expect(len(replay) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "replay/paper queue count must be 9360")
    _expect(len(online) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "online coverage count must be 9360")
    _expect(len(classical) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "classical baseline count must be 9360")
    _expect(len(agent_network) == c.EXPECTED_CANONICAL_AGENT_ROLE_COUNT, failures, "canonical agent role count must be 15")
    _expect({record["assigned_agent_role"] for record in agent_network} == set(c.CANONICAL_QTT_AGENT_ROLES), failures, "agent network roles must match constants")
    _expect(sum(c.SCORE_COMPONENT_WEIGHTS.values()) == 1.0, failures, "score component weights must sum to 1.0")
    _expect(bundles, failures, "bundle candidates must exist")
    _expect(scenarios, failures, "scenario outcome matrix must exist")
    _expect(patterns, failures, "future profitability pattern fields must exist")
    _expect(quantum, failures, "quantum priority queue must exist")
    _expect(hybrid, failures, "hybrid arbitration queue must exist")

    quality_ids = {record["qku_id"] for record in quality}
    _expect(quality_ids == {record["qku_id"] for record in lanes}, failures, "every scored QKU must have a lane")
    _expect(quality_ids == {record["qku_id"] for record in online}, failures, "every scored QKU must have online coverage")
    _expect(quality_ids <= {record["qku_id"] for record in agent_routes}, failures, "every QKU must have an agent route")
    _expect(quality_ids <= {record["qku_id"] for record in tasks}, failures, "every QKU must have an agent task")

    for record in quality:
        _expect(0 <= int(record["qku_quality_score"]) <= 1000, failures, f"quality score out of bounds: {record['qku_id']}")
        _expect(record["no_profit_evidence_created_flag"] is True, failures, f"quality score claimed profit evidence: {record['qku_id']}")
    for record in components:
        for name, component in record["components"].items():
            _expect(0.0 <= float(component["value"]) <= 1.0, failures, f"component out of bounds: {record['qku_id']} {name}")
            _expect(bool(component["basis"]), failures, f"component missing basis: {record['qku_id']} {name}")
    for record in lanes:
        _expect(record["quality_lane"] in c.QUALITY_LANES, failures, f"invalid quality lane: {record['qku_id']}")
        _expect(record["replay_paper_priority_lane"] in c.REPLAY_PAPER_PRIORITY_LANES, failures, f"invalid replay lane: {record['qku_id']}")
    for record in online:
        _expect(record["online_enrichment_coverage_state"] in c.ONLINE_ENRICHMENT_STATES, failures, f"invalid online state: {record['qku_id']}")
    for record in replay:
        _expect(record["replay_result_created_flag"] is False, failures, f"replay result created: {record['qku_id']}")
        _expect(record["paper_result_created_flag"] is False, failures, f"paper result created: {record['qku_id']}")
        _expect(record["profit_evidence_created_flag"] is False, failures, f"profit evidence created: {record['qku_id']}")

    _validate_rankings(rankings, failures)
    _validate_result_slots(result_slots, failures)
    _validate_scenarios(scenarios, failures)
    _validate_bundles(bundles, failures)
    _validate_boundedness(boundedness, bundles, agent_slices, reference_fanout, failures)
    _validate_market_activation(market_policy, market_dashboard, market_active, market_dormant, bundles, failures)
    _validate_patterns(patterns, failures)
    _validate_schemas(repo_root, failures)

    _expect(graph_audit[-1]["graph_consumption_status"] == "PASS", failures, "graph consumption audit must pass")
    _expect(final_summary["forbidden_authority_scan_status"] == "PASS", failures, "forbidden authority scan must pass")
    _expect(final_summary["no_scattered_hardcoded_authority_audit_status"] == "PASS", failures, "no-scattered audit must pass")
    _expect(final_summary["largest_generated_pr161d_report_size_bytes"] < c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES, failures, "largest PR161D report must be below 50 MiB after sharding")
    _expect(final_summary["master_plan_file_edited_flag"] is False, failures, "master plan edit flag must be false")
    _expect(final_summary["atomicrows_final_bundle_created_flag"] is False, failures, "AtomicRows final bundle flag must be false")
    _expect(final_summary["profit_evidence_created_flag"] is False, failures, "profit evidence flag must be false")
    _expect(final_summary["live_authority_created_flag"] is False, failures, "live authority flag must be false")
    _expect(final_summary["bundle_boundedness_metadata_consistent_flag"] is True, failures, "bundle boundedness metadata must be consistent")
    _expect(final_summary["cap_applies_metric_violation_count"] == 0, failures, "cap-applicable metric violations must be zero")
    _expect(final_summary["result_backed_slots_profitability_label_present_count"] == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "result slot profitability labels must be present")
    _expect(final_summary["result_backed_slots_unobserved_count"] == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "result slot profitability labels must be unobserved")
    _expect(final_summary["remaining_semantic_blocker_count"] == 0, failures, "remaining semantic blocker count must be zero")

    return ValidationResult(ok=not failures, failures=tuple(failures))


def _load_records(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = records_from_payload(payload)
    if records or not payload.get("sharded_flag"):
        return records
    merged: list[dict[str, Any]] = []
    for shard_file in payload.get("shard_files") or []:
        shard_payload = json.loads(_resolve_shard_path(repo_root, shard_file).read_text(encoding="utf-8"))
        merged.extend(records_from_payload(shard_payload))
    return merged


def _resolve_shard_path(repo_root: Path, shard_file: Any) -> Path:
    raw_path = str(shard_file)
    normalized = raw_path.replace("\\", "/")
    windows_path = PureWindowsPath(normalized)
    posix_path = PurePosixPath(normalized)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"PR161D shard path must be relative: {raw_path}")
    if any(part == ".." for part in posix_path.parts):
        raise ValueError(f"PR161D shard path must not contain '..': {raw_path}")
    candidate = repo_root.joinpath(*posix_path.parts)
    resolved_root = repo_root.resolve(strict=False)
    try:
        candidate.resolve(strict=False).relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"PR161D shard path escapes repo root: {raw_path}") from exc
    return candidate


def _validate_rankings(records: list[dict[str, Any]], failures: list[str]) -> None:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for record in records:
        _expect(record["ranking_basis"] == "PRE_RESULT_RANKING", failures, f"ranking used non-pre-result basis: {record['ranking_id']}")
        _expect(record["result_evidence_weight"] == 0, failures, f"ranking evidence weight nonzero: {record['ranking_id']}")
        _expect(record["final_qku_category_rank_score"] == record["pre_result_quality_score"], failures, f"ranking final score differs without result: {record['ranking_id']}")
        grouped[(record["ranking_category"], record["category_value"])].append(int(record["qku_rank"]))
    for key, ranks in grouped.items():
        expected = list(range(1, len(ranks) + 1))
        _expect(sorted(ranks) == expected, failures, f"ranking ranks are not contiguous for {key}")


def _validate_result_slots(records: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(len(records) == c.EXPECTED_PRIMARY_QKU_COUNT, failures, "result slot count must be 9360")
    for record in records:
        _expect(record["result_state"] == "NO_RESULT_YET", failures, f"result slot has result state: {record['qku_id']}")
        _expect(record["profitability_label"] == "UNOBSERVED", failures, f"result slot profitability observed: {record['qku_id']}")
        _expect(record["result_evidence_weight"] == 0, failures, f"result slot evidence nonzero: {record['qku_id']}")
        _expect(record["result_backed_score"] is None, failures, f"result-backed score populated: {record['qku_id']}")
        _expect(record["no_result_fabricated_flag"] is True, failures, f"result slot fabricated result flag false: {record['qku_id']}")
        _expect(record["no_profit_evidence_created_flag"] is True, failures, f"result slot created profit evidence: {record['qku_id']}")


def _validate_scenarios(records: list[dict[str, Any]], failures: list[str]) -> None:
    for record in records:
        _expect(record["result_state"] == "NO_RESULT_YET", failures, f"scenario has result state: {record['scenario_matrix_id']}")
        _expect(record["profitability_label"] == "UNOBSERVED", failures, f"scenario has observed profitability: {record['scenario_matrix_id']}")
        _expect(record["no_result_fabricated_flag"] is True, failures, f"scenario fabricated result flag false: {record['scenario_matrix_id']}")
        _expect(record["no_profit_evidence_created_flag"] is True, failures, f"scenario created profit evidence: {record['scenario_matrix_id']}")
        _expect(record["promotion_allowed_flag"] is False, failures, f"scenario allows promotion: {record['scenario_matrix_id']}")


def _validate_bundles(records: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(len(records) <= c.MAX_QKU_BUNDLE_CANDIDATES, failures, "bundle count exceeds cap")
    for record in records:
        _expect(len(record["qku_ids"]) <= c.MAX_QKUS_PER_BUNDLE, failures, f"bundle exceeds qku cap: {record['qku_bundle_id']}")
        _expect(record["bundle_result_state"] == "NO_RESULT_YET", failures, f"bundle has result: {record['qku_bundle_id']}")
        _expect(record["bundle_market_activation_state"] in c.MARKET_BUNDLE_ACTIVATION_STATES, failures, f"invalid bundle activation state: {record['qku_bundle_id']}")
        _expect(record["active_for_live_trading_flag"] is False, failures, f"bundle active for live trading: {record['qku_bundle_id']}")
        _expect(record["profit_evidence_created_flag"] is False, failures, f"bundle created profit evidence: {record['qku_bundle_id']}")
        _expect(record["live_execution_created_flag"] is False, failures, f"bundle created live execution: {record['qku_bundle_id']}")


def _validate_boundedness(
    records: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    agent_slices: list[dict[str, Any]],
    reference_fanout: list[dict[str, Any]],
    failures: list[str],
) -> None:
    _expect(len(records) == 1, failures, "boundedness report must have one summary record")
    if not records:
        return
    record = records[0]
    _expect(record["shared_bundle_registry_count"] == len(bundles), failures, "shared registry count must match bundles")
    _expect(record["deduplicated_bundle_candidate_count"] == len({bundle["qku_bundle_id"] for bundle in bundles}), failures, "deduplicated bundle count mismatch")
    _expect(record["agent_materialized_bundle_count"] == 0, failures, "agent materialized bundle count must be zero")
    _expect(record["cap_applies_metric_violation_count"] == 0, failures, "boundedness cap violations must be zero")
    _expect(record["active_selection_within_caps_flag"] is True, failures, "active bounded selections must be within caps")
    _expect(record["shared_bundle_registry_no_data_loss_flag"] is True, failures, "shared registry must preserve all bundles")
    allowed_exemptions = {
        c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT,
        c.CAP_EXEMPTION_PARENT_AGGREGATE_SCENARIO_FAMILY,
    }
    for metric in record["cap_metrics"]:
        if metric["cap_applies_flag"]:
            _expect(
                int(metric["active_count"]) <= int(metric["cap_value"]),
                failures,
                f"cap metric active count exceeds cap: {metric['cap_id']}",
            )
            if int(metric["observed_count"]) > int(metric["cap_value"]):
                _expect(
                    int(metric["overflow_count"]) > 0 or int(metric["dormant_count"]) > 0,
                    failures,
                    f"cap metric observed count exceeds cap without overflow/dormant: {metric['cap_id']}",
                )
        else:
            _expect(
                metric["cap_exemption_reason"] in allowed_exemptions,
                failures,
                f"cap exemption reason invalid: {metric['cap_id']}",
            )
    _expect(len(agent_slices) == c.EXPECTED_CANONICAL_AGENT_ROLE_COUNT, failures, "agent slice count must be 15")
    _expect(len(reference_fanout) == c.EXPECTED_CANONICAL_AGENT_ROLE_COUNT, failures, "fanout count must be 15")
    bundle_ids = {str(bundle["qku_bundle_id"]) for bundle in bundles}
    for slice_record in agent_slices:
        _expect(slice_record["agent_materialized_bundle_count"] == 0, failures, f"slice materialized bundles: {slice_record['agent_role']}")
        _expect(slice_record["fanout_reference_not_materialized_flag"] is True, failures, f"slice fanout materialized: {slice_record['agent_role']}")
        _expect(slice_record["agent_active_slice_count"] <= c.MAX_BUNDLES_PER_AGENT_ROLE, failures, f"agent active slice exceeds cap: {slice_record['agent_role']}")
        preserved = set(slice_record["bundle_ids_active"]) | set(slice_record["bundle_ids_overflow"]) | set(slice_record["bundle_ids_dormant"])
        _expect(preserved <= bundle_ids, failures, f"slice references unknown bundles: {slice_record['agent_role']}")
    for fanout in reference_fanout:
        _expect(fanout["cap_applies_flag"] is False, failures, f"fanout cap applies: {fanout['agent_role']}")
        _expect(fanout["cap_exemption_reason"] == c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT, failures, f"fanout exemption invalid: {fanout['agent_role']}")
        _expect(fanout["agent_materialized_bundle_count"] == 0, failures, f"fanout materialized bundles: {fanout['agent_role']}")


def _validate_market_activation(
    policy: list[dict[str, Any]],
    dashboard: list[dict[str, Any]],
    active: list[dict[str, Any]],
    dormant: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    failures: list[str],
) -> None:
    policy_by_market = {record["market_class"]: record for record in policy}
    _expect(len(policy_by_market) == len(c.MARKET_BUNDLE_ACTIVATION_POLICY), failures, "market activation policy count mismatch")
    _expect(len(dashboard) == len(c.MARKET_BUNDLE_ACTIVATION_POLICY), failures, "dashboard activation option count mismatch")
    for market, expected_state in c.MARKET_BUNDLE_ACTIVATION_POLICY.items():
        market_policy = policy_by_market.get(market)
        _expect(market_policy is not None, failures, f"missing market policy: {market}")
        if market_policy is None:
            continue
        _expect(market_policy["default_activation_state"] == expected_state, failures, f"market default state mismatch: {market}")
        _expect(market_policy["affects_live_authority_flag"] is False, failures, f"market policy creates live authority: {market}")
        _expect(market_policy["no_live_authority_created_flag"] is True, failures, f"market policy live flag false: {market}")
    for bundle in bundles:
        market = bundle["bundle_market"]
        if market in {"PREDICTION_MARKET", "MARKET_AGNOSTIC", "NON_MARKET_SPECIFIC"}:
            _expect(bundle["bundle_market_activation_state"] == "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER", failures, f"stage1 market bundle not active: {bundle['qku_bundle_id']}")
        if market in c.FUTURE_MARKET_CLASSES:
            _expect(bundle["bundle_market_activation_state"] == "MARKET_BUNDLE_DORMANT_FUTURE_STAGE", failures, f"future market bundle not dormant: {bundle['qku_bundle_id']}")
        _expect(bundle["active_for_live_trading_flag"] is False, failures, f"market activation created live trading: {bundle['qku_bundle_id']}")
    _expect({record["qku_bundle_id"] for record in active} <= {bundle["qku_bundle_id"] for bundle in bundles}, failures, "active set references unknown bundle")
    _expect({record["qku_bundle_id"] for record in dormant} <= {bundle["qku_bundle_id"] for bundle in bundles}, failures, "dormancy queue references unknown bundle")


def _validate_patterns(records: list[dict[str, Any]], failures: list[str]) -> None:
    for record in records:
        _expect(record["future_confidence_class"] == "UNOBSERVED", failures, f"future confidence observed: {record['future_profitability_pattern_record_id']}")
        _expect(record["future_sample_size"] == 0, failures, f"future sample size nonzero: {record['future_profitability_pattern_record_id']}")
        _expect(record["no_result_fabricated_flag"] is True, failures, f"future pattern fabricated result: {record['future_profitability_pattern_record_id']}")


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    schema_dir = repo_root / c.SCHEMA_DIR
    for schema_path in schema_dir.glob("*.schema.json"):
        payload = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = payload.get("properties", {})
        for field, enum_values in c.SCHEMA_ENUM_FIELDS.items():
            if field in properties and "enum" in properties[field]:
                _expect(properties[field]["enum"] == list(enum_values), failures, f"schema enum parity failed: {schema_path.name} {field}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
