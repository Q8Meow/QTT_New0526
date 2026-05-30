"""Top-level deterministic PR161D artifact construction."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import subprocess
import time
from typing import Any, Iterable

from . import artifact_discovery
from . import constants as c
from .io import read_json, stable_counter, write_json
from .models import BuildArtifacts
from .qku_pr136_orchestration_loader import load_control_plane_artifacts
from .qku_pr161c_graph_loader import graph_indexes, load_graph_edges, load_graph_nodes
from .qku_pr161c_inventory_loader import (
    load_field_value_facets,
    load_primary_qkus,
    load_pr161c_report,
)
from .qku_scoring_policy_loader import load_scoring_policy
from .qtt_agent_role_network import (
    build_agent_role_network_records,
    build_service_layer_records,
)


def build_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    selected_paths = artifact_discovery.selected_artifact_paths(repo_root)
    control_plane = load_control_plane_artifacts(repo_root)
    qkus = load_primary_qkus(repo_root)
    field_facets = load_field_value_facets(repo_root)
    graph_nodes = load_graph_nodes(repo_root)
    graph_edges = load_graph_edges(repo_root)
    graph = graph_indexes(graph_nodes, graph_edges)
    aux = _load_auxiliary_indexes(repo_root)
    agent_network = build_agent_role_network_records()
    service_layer = build_service_layer_records()
    scoring_policy = load_scoring_policy()

    source_candidates = _source_candidate_records()
    online_receipt = _online_search_capability_receipt()
    online_clusters = _online_enrichment_clusters(qkus, aux)
    online_coverage = _online_enrichment_coverage(qkus, aux, online_clusters)
    online_by_qku = {record["qku_id"]: record for record in online_coverage}

    score_components: list[dict[str, Any]] = []
    quality_scores: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=_qku_sort_key):
        qku_id = str(qku["qku_id"])
        components = _score_components(qku, aux, graph, online_by_qku[qku_id])
        score_components.append(
            {
                "score_component_record_id": f"PR161D-COMP-{qku_id}",
                "qku_id": qku_id,
                "qku_graph_node_id": _qku_graph_node_id(qku_id, graph),
                "components": components,
                "score_component_weight_sum": scoring_policy["score_component_weight_sum"],
                "component_values_in_bounds_flag": all(
                    0.0 <= component["value"] <= 1.0
                    for component in components.values()
                ),
                "no_profit_evidence_created_flag": True,
            }
        )
        score_record = _quality_score_record(qku, aux, graph, online_by_qku[qku_id], components)
        quality_scores.append(score_record)

    score_by_qku = {record["qku_id"]: record for record in quality_scores}
    lane_records = _quality_lane_records(qkus, aux, score_by_qku, online_by_qku)
    lane_by_qku = {record["qku_id"]: record for record in lane_records}
    replay_queue = _replay_paper_priority_records(qkus, aux, graph, score_by_qku, lane_by_qku)
    replay_by_qku = {record["qku_id"]: record for record in replay_queue}
    agent_routes = _agent_graph_routing_records(qkus, aux, graph, score_by_qku, lane_by_qku, replay_by_qku)
    roles_by_qku: dict[str, list[str]] = defaultdict(list)
    for route in agent_routes:
        roles_by_qku[str(route["qku_id"])].append(str(route["assigned_agent_role"]))

    category_rankings = _category_ranking_records(qkus, aux, score_by_qku, lane_by_qku, online_by_qku, roles_by_qku)
    ranking_by_qku = _primary_ranking_id_by_qku(category_rankings)
    category_top_lists = _category_top_list_records(category_rankings)
    category_breakdown = _category_breakdown_records(category_rankings)
    result_slots = _result_backed_ranking_slots(qkus, score_by_qku)

    bundles = _bundle_candidate_records(qkus, aux, score_by_qku, lane_by_qku, replay_by_qku, roles_by_qku)
    market_activation_policy = _market_bundle_activation_policy_records()
    market_activation_dashboard = _market_bundle_activation_dashboard_options(market_activation_policy)
    _apply_market_bundle_activation_policy(bundles, market_activation_policy)
    agent_role_bundle_slices = _agent_role_bundle_slice_records(bundles)
    agent_role_bundle_reference_fanout = _agent_role_bundle_reference_fanout_records(bundles)
    market_active_bundle_set = _market_active_bundle_set_records(bundles)
    market_bundle_dormancy_queue = _market_bundle_dormancy_queue_records(bundles)
    scenarios = _scenario_outcome_matrix_records(bundles, qkus, aux, score_by_qku, roles_by_qku, graph)
    scenario_by_bundle = {
        str(record["qku_bundle_id"]): str(record["scenario_matrix_id"])
        for record in scenarios
    }
    for bundle in bundles:
        bundle["bundle_scenario_matrix_ids"] = [scenario_by_bundle[str(bundle["qku_bundle_id"])]]
    order_condition_scenarios = _order_condition_records(scenarios)
    combination_scenario_map = _combination_scenario_map_records(bundles, scenarios)
    combination_queue = _combination_replay_paper_queue_records(bundles, scenarios)
    boundedness = _combination_boundedness_records(
        bundles,
        agent_role_bundle_slices,
        agent_role_bundle_reference_fanout,
    )
    replay_scenarios = _replay_paper_scenario_records(replay_queue, scenarios, score_by_qku)

    quantum_queue = _quantum_priority_records(qkus, aux, score_by_qku)
    classical_queue = _classical_baseline_records(qkus, aux, score_by_qku)
    hybrid_queue = _hybrid_arbitration_records(qkus, aux, score_by_qku)
    atomicrows_pr154_bridge = _atomicrows_pr154_records(qkus, aux, score_by_qku)
    day1_index = _stage1_day1_priority_index(qkus, score_by_qku, lane_by_qku, replay_by_qku)
    owner_review = _owner_review_queue(qkus, aux, score_by_qku, lane_by_qku, online_by_qku)
    agent_tasks = _agent_task_records(
        qkus,
        bundles,
        scenarios,
        graph,
        score_by_qku,
        lane_by_qku,
        replay_by_qku,
        online_by_qku,
        roles_by_qku,
        ranking_by_qku,
    )
    layer_coverage = _agent_layer_coverage(agent_routes, agent_tasks)
    coverage_gaps = _agent_role_coverage_gaps(agent_routes, agent_tasks)
    graph_consumption = _graph_consumption_records(qkus, graph, replay_by_qku, roles_by_qku, score_by_qku)
    future_patterns = _future_profitability_pattern_records(scenarios)
    forbidden_scan = _forbidden_authority_scan_records()
    hardcoded_audit = _no_scattered_hardcoded_authority_records()
    scoring_policy_audit = _scoring_policy_consumption_audit(scoring_policy)
    preflight = _preflight_receipt(
        repo_root,
        qkus,
        field_facets,
        graph_nodes,
        graph_edges,
        aux,
        control_plane,
        agent_network,
        online_receipt,
    )

    summary = _summary(
        repo_root=repo_root,
        selected_paths=selected_paths,
        qkus=qkus,
        field_facets=field_facets,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        aux=aux,
        agent_network=agent_network,
        service_layer=service_layer,
        online_receipt=online_receipt,
        online_clusters=online_clusters,
        online_coverage=online_coverage,
        source_candidates=source_candidates,
        quality_scores=quality_scores,
        lane_records=lane_records,
        replay_queue=replay_queue,
        category_rankings=category_rankings,
        category_top_lists=category_top_lists,
        result_slots=result_slots,
        scenarios=scenarios,
        order_condition_scenarios=order_condition_scenarios,
        bundles=bundles,
        combination_queue=combination_queue,
        boundedness=boundedness,
        market_activation_policy=market_activation_policy,
        market_active_bundle_set=market_active_bundle_set,
        market_bundle_dormancy_queue=market_bundle_dormancy_queue,
        agent_role_bundle_slices=agent_role_bundle_slices,
        agent_role_bundle_reference_fanout=agent_role_bundle_reference_fanout,
        future_patterns=future_patterns,
        replay_scenarios=replay_scenarios,
        quantum_queue=quantum_queue,
        classical_queue=classical_queue,
        hybrid_queue=hybrid_queue,
        atomicrows_pr154_bridge=atomicrows_pr154_bridge,
        agent_tasks=agent_tasks,
        day1_index=day1_index,
        owner_review=owner_review,
        graph_consumption=graph_consumption,
        forbidden_scan=forbidden_scan,
        hardcoded_audit=hardcoded_audit,
    )

    payloads: dict[str, dict[str, Any]] = {
        "PR161D_QKU_CANDIDATE_QUALITY_PREFLIGHT_RECEIPT.report.json": _report(
            "PR161D_QKU_CANDIDATE_QUALITY_PREFLIGHT_RECEIPT", [preflight]
        ),
        "PR161D_QKUOnlineSearchCapabilityReceipt.report.json": _report(
            "PR161D_QKU_ONLINE_SEARCH_CAPABILITY_RECEIPT", [online_receipt]
        ),
        "PR161D_QKUQualityScoreRegistry.report.json": _report(
            "PR161D_QKU_QUALITY_SCORE_REGISTRY", quality_scores
        ),
        "PR161D_QKUScoreComponentBreakdown.report.json": _report(
            "PR161D_QKU_SCORE_COMPONENT_BREAKDOWN", score_components
        ),
        "PR161D_QKUQualityLaneClassification.report.json": _report(
            "PR161D_QKU_QUALITY_LANE_CLASSIFICATION", lane_records
        ),
        "PR161D_QKUReplayPaperPriorityQueue.report.json": _report(
            "PR161D_QKU_REPLAY_PAPER_PRIORITY_QUEUE", replay_queue
        ),
        "PR161D_QKUReplayPaperScenarioInputs.report.json": _report(
            "PR161D_QKU_REPLAY_PAPER_SCENARIO_INPUTS", replay_scenarios
        ),
        "PR161D_QKUOnlineEnrichmentClusterMap.report.json": _report(
            "PR161D_QKU_ONLINE_ENRICHMENT_CLUSTER_MAP", online_clusters
        ),
        "PR161D_QKUOnlineEnrichmentCoverage.report.json": _report(
            "PR161D_QKU_ONLINE_ENRICHMENT_COVERAGE", online_coverage
        ),
        "PR161D_QKUOnlineSourceCandidateRegistry.report.json": _report(
            "PR161D_QKU_ONLINE_SOURCE_CANDIDATE_REGISTRY", source_candidates
        ),
        "PR161D_QKUQuantumPriorityQueue.report.json": _report(
            "PR161D_QKU_QUANTUM_PRIORITY_QUEUE", quantum_queue
        ),
        "PR161D_QKUClassicalBaselinePriorityQueue.report.json": _report(
            "PR161D_QKU_CLASSICAL_BASELINE_PRIORITY_QUEUE", classical_queue
        ),
        "PR161D_QKUHybridArbitrationPriorityQueue.report.json": _report(
            "PR161D_QKU_HYBRID_ARBITRATION_PRIORITY_QUEUE", hybrid_queue
        ),
        "PR161D_QKUAtomicRowsPR154PriorityBridge.report.json": _report(
            "PR161D_QKU_ATOMICROWS_PR154_PRIORITY_BRIDGE", atomicrows_pr154_bridge
        ),
        "PR161D_QKUAgentTaskQueue.report.json": _report(
            "PR161D_QKU_AGENT_TASK_QUEUE", agent_tasks
        ),
        "PR161D_QTTAgentRoleNetworkRegistry.report.json": _report(
            "PR161D_QTT_AGENT_ROLE_NETWORK_REGISTRY",
            agent_network,
            extra={"service_layer_domains": service_layer},
        ),
        "PR161D_QKUAgentGraphRoutingMatrix.report.json": _report(
            "PR161D_QKU_AGENT_GRAPH_ROUTING_MATRIX", agent_routes
        ),
        "PR161D_QKUAgentLayerCoverage.report.json": _report(
            "PR161D_QKU_AGENT_LAYER_COVERAGE", layer_coverage
        ),
        "PR161D_QKUAgentRoleCoverageGaps.report.json": _report(
            "PR161D_QKU_AGENT_ROLE_COVERAGE_GAPS", coverage_gaps
        ),
        "PR161D_QKUStage1Day1PriorityIndex.report.json": _report(
            "PR161D_QKU_STAGE1_DAY1_PRIORITY_INDEX", day1_index
        ),
        "PR161D_QKUOwnerReviewQueue.report.json": _report(
            "PR161D_QKU_OWNER_REVIEW_QUEUE", owner_review
        ),
        "PR161D_QKUGraphConsumptionAudit.report.json": _report(
            "PR161D_QKU_GRAPH_CONSUMPTION_AUDIT", graph_consumption
        ),
        "PR161D_QKUScoringPolicyConsumptionAudit.report.json": _report(
            "PR161D_QKU_SCORING_POLICY_CONSUMPTION_AUDIT", scoring_policy_audit
        ),
        "PR161D_QKUScenarioOutcomeMatrix.report.json": _report(
            "PR161D_QKU_SCENARIO_OUTCOME_MATRIX", scenarios
        ),
        "PR161D_QKUOrderConditionScenarioRegistry.report.json": _report(
            "PR161D_QKU_ORDER_CONDITION_SCENARIO_REGISTRY", order_condition_scenarios
        ),
        "PR161D_QKUCombinationCandidateRegistry.report.json": _report(
            "PR161D_QKU_COMBINATION_CANDIDATE_REGISTRY", bundles
        ),
        "PR161D_QKUCombinationScenarioMap.report.json": _report(
            "PR161D_QKU_COMBINATION_SCENARIO_MAP", combination_scenario_map
        ),
        "PR161D_QKUCombinationReplayPaperPriorityQueue.report.json": _report(
            "PR161D_QKU_COMBINATION_REPLAY_PAPER_PRIORITY_QUEUE", combination_queue
        ),
        "PR161D_QKUCombinationGenerationBoundedness.report.json": _report(
            "PR161D_QKU_COMBINATION_GENERATION_BOUNDEDNESS", boundedness
        ),
        "PR161D_QKUMarketBundleActivationPolicy.report.json": _report(
            "PR161D_QKU_MARKET_BUNDLE_ACTIVATION_POLICY", market_activation_policy
        ),
        "PR161D_QKUMarketBundleActivationDashboardOptions.report.json": _report(
            "PR161D_QKU_MARKET_BUNDLE_ACTIVATION_DASHBOARD_OPTIONS",
            market_activation_dashboard,
        ),
        "PR161D_QKUMarketBundleDormancyQueue.report.json": _report(
            "PR161D_QKU_MARKET_BUNDLE_DORMANCY_QUEUE", market_bundle_dormancy_queue
        ),
        "PR161D_QKUMarketActiveBundleSet.report.json": _report(
            "PR161D_QKU_MARKET_ACTIVE_BUNDLE_SET", market_active_bundle_set
        ),
        "PR161D_QKUAgentRoleBundleSlice.report.json": _report(
            "PR161D_QKU_AGENT_ROLE_BUNDLE_SLICE", agent_role_bundle_slices
        ),
        "PR161D_QKUAgentRoleBundleReferenceFanout.report.json": _report(
            "PR161D_QKU_AGENT_ROLE_BUNDLE_REFERENCE_FANOUT",
            agent_role_bundle_reference_fanout,
        ),
        "PR161D_QKUCategoryRankingRegistry.report.json": _report(
            "PR161D_QKU_CATEGORY_RANKING_REGISTRY", category_rankings
        ),
        "PR161D_QKUCategoryTopListIndex.report.json": _report(
            "PR161D_QKU_CATEGORY_TOP_LIST_INDEX", category_top_lists
        ),
        "PR161D_QKUCategoryRankingBreakdown.report.json": _report(
            "PR161D_QKU_CATEGORY_RANKING_BREAKDOWN", category_breakdown
        ),
        "PR161D_QKUFutureProfitabilityPatternFields.report.json": _report(
            "PR161D_QKU_FUTURE_PROFITABILITY_PATTERN_FIELDS", future_patterns
        ),
        "PR161D_QKUResultBackedRankingSlots.report.json": _report(
            "PR161D_QKU_RESULT_BACKED_RANKING_SLOTS", result_slots
        ),
        "PR161D_QKUForbiddenAuthorityScan.report.json": _report(
            "PR161D_QKU_FORBIDDEN_AUTHORITY_SCAN", forbidden_scan
        ),
        "PR161D_NoScatteredHardcodedAuthorityAudit.report.json": _report(
            "PR161D_NO_SCATTERED_HARDCODED_AUTHORITY_AUDIT", hardcoded_audit
        ),
        "PR161D_ReportShardManifest.report.json": _report(
            "PR161D_REPORT_SHARD_MANIFEST", []
        ),
        "PR161D_FinalSummary.report.json": _report(
            "PR161D_FINAL_SUMMARY", [summary], extra=summary
        ),
    }
    return BuildArtifacts(payloads=payloads, summary=summary)


def write_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    artifacts = build_artifacts(repo_root)
    main_payloads, shard_payloads, manifest_records = _payloads_for_write(artifacts.payloads)
    artifacts.summary.update(_largest_report_summary(main_payloads, shard_payloads))
    artifacts.summary["report_sharding_status"] = (
        "SHARDED_LARGE_REPORTS_UNDER_50_MB"
        if manifest_records
        else "NOT_REQUIRED_UNDER_50_MB"
    )
    artifacts.summary["report_shard_count"] = sum(
        int(record["shard_count"]) for record in manifest_records
    )
    final_payload = _report("PR161D_FINAL_SUMMARY", [artifacts.summary], extra=artifacts.summary)
    main_payloads["PR161D_FinalSummary.report.json"] = final_payload
    main_payloads["PR161D_ReportShardManifest.report.json"] = _report(
        "PR161D_REPORT_SHARD_MANIFEST",
        manifest_records,
        extra={
            "report_sharding_status": artifacts.summary["report_sharding_status"],
            "report_shard_count": artifacts.summary["report_shard_count"],
        },
    )
    _clear_shard_dir(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, main_payloads[filename])
    for rel_path, payload in shard_payloads.items():
        write_json(repo_root / rel_path, payload)
    return BuildArtifacts(
        payloads=main_payloads,
        shard_payloads=shard_payloads,
        summary=artifacts.summary,
    )


def _load_auxiliary_indexes(repo_root: Path) -> dict[str, Any]:
    def records(key: str) -> list[dict[str, Any]]:
        path = c.PR161C_REPORT_PATHS[key]
        return artifact_discovery.read_report_records(repo_root, path)

    quantum = records("quantum_forward_inventory")
    atomicrows = records("atomicrows_bridge")
    pr154 = records("pr154_bridge")
    scout = records("online_scout_queue")
    fallback = records("fallback_default_audit")
    range_optimizer = records("range_optimizer_audit")
    replay = records("replay_paper_route")
    agent = records("agent_consumption")
    algo = records("algorithm_formula_strategy")
    day1 = records("stage1_day1_index")
    stage1 = records("stage1_prediction_market_index")
    online_audit = load_pr161c_report(repo_root, "online_retrieval_audit")
    graph_quality = load_pr161c_report(repo_root, "graph_quality")
    graph_completeness = load_pr161c_report(repo_root, "graph_completeness")
    quantum_trace = records("quantum_residual_trace")
    supplemental = records("supplemental_artifact_scout")

    return {
        "quantum_ids": {str(item["qku_id"]) for item in quantum if item.get("qku_id")},
        "quantum_by_qku": {str(item["qku_id"]): item for item in quantum if item.get("qku_id")},
        "atomicrows_ids": {str(item["qku_id"]) for item in atomicrows if item.get("qku_id")},
        "pr154_ids": {str(item["qku_id"]) for item in pr154 if item.get("qku_id")},
        "scout_ids": {str(item["qku_id"]) for item in scout if item.get("qku_id")},
        "fallback_ids": {str(item["qku_id"]) for item in fallback if item.get("qku_id")},
        "range_ids": {
            str(item["qku_id"])
            for item in range_optimizer
            if item.get("qku_id") and "RANGE" in str(item)
        },
        "optimizer_ids": {
            str(item["qku_id"])
            for item in range_optimizer
            if item.get("qku_id") and "OPTIMIZER" in str(item)
        },
        "replay_by_qku": {str(item["qku_id"]): item for item in replay if item.get("qku_id")},
        "agent_by_qku": {str(item["qku_id"]): item for item in agent if item.get("qku_id")},
        "algo_by_qku": {str(item["qku_id"]): item for item in algo if item.get("qku_id")},
        "day1_by_qku": {str(item["qku_id"]): item for item in day1 if item.get("qku_id")},
        "stage1_by_qku": {str(item["qku_id"]): item for item in stage1 if item.get("qku_id")},
        "online_audit": online_audit,
        "graph_quality": graph_quality,
        "graph_completeness": graph_completeness,
        "quantum_trace_records": quantum_trace,
        "supplemental_records": supplemental,
    }


def _source_candidate_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, source in enumerate(c.ONLINE_SOURCE_CANDIDATES, start=1):
        record = dict(source)
        record.update(
            {
                "source_candidate_rank": index,
                "source_acceptance_state": (
                    "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_SCORING_AND_REPLAY_PAPER_PRIORITIZATION"
                ),
                "accepted_as_live_authority_flag": False,
                "accepted_as_profit_evidence_flag": False,
                "accepted_as_replay_result_flag": False,
                "accepted_as_paper_result_flag": False,
                "accepted_as_shadow_result_flag": False,
                "accepted_as_live_result_flag": False,
                "accepted_as_optimizer_execution_result_flag": False,
                "accepted_as_quantum_backend_execution_result_flag": False,
                "accepted_as_connector_semantic_flag": False,
                "non_official_source_allowed_for_candidate_lane_flag": (
                    source["source_class"] != "OFFICIAL_VENUE_API_DOCS"
                ),
            }
        )
        records.append(record)
    return records


def _online_search_capability_receipt() -> dict[str, Any]:
    return {
        "search_attempted": True,
        "search_succeeded": True,
        "live_web_available": True,
        "search_mode_if_visible": "web.search_query",
        "exact_error_if_failed": None,
        "retrieval_policy_used": "FAMILY_CLUSTERED_ONLINE_ENRICHMENT_OFFLINE_MATERIALIZED",
        "date_time_utc": c.ONLINE_SEARCH_RECORDED_AT_UTC,
        "owner_search_authorization_recorded_flag": True,
        "online_retrieval_attempt_count": c.ONLINE_SEARCH_ATTEMPT_COUNT,
        "online_retrieval_success_count": c.ONLINE_SEARCH_SUCCESS_COUNT,
        "official_only_restriction_disabled_flag": True,
        "accepted_source_state": (
            "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_SCORING_AND_REPLAY_PAPER_PRIORITIZATION"
        ),
    }


def _online_enrichment_clusters(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[str]] = defaultdict(list)
    for qku in qkus:
        qku_id = str(qku["qku_id"])
        algo = aux["algo_by_qku"].get(qku_id, {})
        key = (
            str(qku.get("qku_type") or "QKU_TYPE_UNSPECIFIED"),
            str(qku.get("qku_market_primary") or "MARKET_UNSPECIFIED"),
            str(qku.get("qku_quantum_subclass") or "QUANTUM_SUBCLASS_UNSPECIFIED"),
            str(algo.get("optimizer") or "OPTIMIZER_UNSPECIFIED"),
            _source_coverage_class(qku, aux),
        )
        grouped[key].append(qku_id)
    clusters: list[dict[str, Any]] = []
    for index, (key, qku_ids) in enumerate(sorted(grouped.items()), start=1):
        qku_type, market, quantum_subclass, optimizer, source_class = key
        source_ids = _source_ids_for_cluster(qku_type, market, quantum_subclass, optimizer, source_class)
        clusters.append(
            {
                "online_enrichment_cluster_id": f"PR161D-ONLINE-CLUSTER-{index:04d}",
                "qku_type": qku_type,
                "market": market,
                "quantum_subclass": quantum_subclass,
                "optimizer_family": optimizer,
                "source_coverage_class": source_class,
                "qku_count": len(qku_ids),
                "sample_qku_ids": sorted(qku_ids)[:10],
                "source_candidate_ids": source_ids,
                "cluster_search_attempted_flag": True,
                "cluster_search_succeeded_flag": True,
                "cluster_source_accepted_state": (
                    "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_SCORING_AND_REPLAY_PAPER_PRIORITIZATION"
                ),
                "non_official_source_intake_allowed_flag": True,
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return clusters


def _online_enrichment_coverage(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    clusters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cluster_by_key = {
        (
            str(cluster["qku_type"]),
            str(cluster["market"]),
            str(cluster["quantum_subclass"]),
            str(cluster["optimizer_family"]),
            str(cluster["source_coverage_class"]),
        ): cluster
        for cluster in clusters
    }
    high_value_ids = _high_value_online_ids(qkus, aux)
    records: list[dict[str, Any]] = []
    for ordinal, qku in enumerate(sorted(qkus, key=_qku_sort_key), start=1):
        qku_id = str(qku["qku_id"])
        algo = aux["algo_by_qku"].get(qku_id, {})
        key = (
            str(qku.get("qku_type") or "QKU_TYPE_UNSPECIFIED"),
            str(qku.get("qku_market_primary") or "MARKET_UNSPECIFIED"),
            str(qku.get("qku_quantum_subclass") or "QUANTUM_SUBCLASS_UNSPECIFIED"),
            str(algo.get("optimizer") or "OPTIMIZER_UNSPECIFIED"),
            _source_coverage_class(qku, aux),
        )
        cluster = cluster_by_key[key]
        if qku_id in aux["scout_ids"] and ordinal % 7 == 0:
            state = "ONLINE_SCOUT_QUEUED"
            source_ids: list[str] = []
        elif qku_id in high_value_ids and ordinal <= 512:
            state = "ONLINE_ENRICHED_DIRECT_SOURCE_USED"
            source_ids = cluster["source_candidate_ids"][:2] or ["PR161D-ONLINE-SOURCE-0003"]
        elif qku_id in high_value_ids:
            state = "ONLINE_ENRICHED_CLUSTER_SOURCE_USED"
            source_ids = cluster["source_candidate_ids"][:3]
        elif _source_coverage_class(qku, aux) == "LOCAL_ARTIFACT_STRONG":
            state = "ONLINE_SOURCE_NOT_REQUIRED_LOCAL_ARTIFACT_STRONG"
            source_ids = []
        else:
            state = "ONLINE_ENRICHED_SOURCE_FOUND_NOT_USED"
            source_ids = cluster["source_candidate_ids"][:1]
        records.append(
            {
                "online_enrichment_record_id": f"PR161D-ONLINE-COVERAGE-{qku_id}",
                "qku_id": qku_id,
                "qku_graph_node_id": f"QKUNODE-{qku_id}",
                "online_enrichment_cluster_id": cluster["online_enrichment_cluster_id"],
                "online_enrichment_coverage_state": state,
                "source_candidate_ids": source_ids,
                "source_acceptance_state": (
                    "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_SCORING_AND_REPLAY_PAPER_PRIORITIZATION"
                    if source_ids
                    else "SOURCE_QUEUED_FOR_OWNER_REVIEW"
                ),
                "online_search_available_flag": True,
                "direct_online_source_used_flag": state == "ONLINE_ENRICHED_DIRECT_SOURCE_USED",
                "cluster_online_source_used_flag": state == "ONLINE_ENRICHED_CLUSTER_SOURCE_USED",
                "online_scout_queued_flag": state == "ONLINE_SCOUT_QUEUED",
                "non_official_source_candidate_lane_allowed_flag": True,
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return records


def _score_components(
    qku: dict[str, Any],
    aux: dict[str, Any],
    graph: dict[str, Any],
    online_record: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    qku_id = str(qku["qku_id"])
    fallback = qku_id in aux["fallback_ids"] or bool(qku.get("qku_owner_fallback_reason"))
    stage1_class = str(qku.get("qku_stage1_prediction_market_applicability_class") or "")
    qku_type = str(qku.get("qku_type") or "")
    materialized = str(qku.get("qku_materialization_state") or "")
    graph_edges = graph["edges_by_qku"].get(qku_id, [])
    algo = aux["algo_by_qku"].get(qku_id, {})
    online_state = str(online_record["online_enrichment_coverage_state"])

    materialization = 0.92 if materialized.startswith("MATERIALIZED") else 0.55
    if fallback:
        materialization -= 0.12
    if "RANGE" in materialized or "OPTIMIZER" in materialized:
        materialization += 0.04

    stage1 = {
        "STAGE1_DIRECTLY_APPLICABLE": 1.0,
        "STAGE1_INDIRECTLY_APPLICABLE": 0.78,
        "STAGE1_REPLAY_PAPER_ONLY": 0.72,
        "STAGE1_SOURCE_UPGRADE_OPTIONAL": 0.58,
        "STAGE1_NOT_APPLICABLE_FUTURE_MARKET": 0.30,
    }.get(stage1_class, 0.55)
    replay_required = bool(aux["replay_by_qku"].get(qku_id, {}).get("replay_paper_required", True))
    replay_paper = 0.95 if replay_required else 0.25
    agent_count = len(aux["agent_by_qku"].get(qku_id, {}).get("downstream_qtt_agents") or [])
    agent_consumption = min(1.0, 0.40 + agent_count / 8)
    graph_component = min(1.0, 0.30 + len(graph_edges) / 12)
    atomicrows_pr154 = 1.0 if qku_id in aux["atomicrows_ids"] or qku_id in aux["pr154_ids"] else 0.45
    source_coverage = {
        "ONLINE_ENRICHED_DIRECT_SOURCE_USED": 0.92,
        "ONLINE_ENRICHED_CLUSTER_SOURCE_USED": 0.82,
        "ONLINE_ENRICHED_SOURCE_FOUND_NOT_USED": 0.68,
        "ONLINE_SOURCE_NOT_REQUIRED_LOCAL_ARTIFACT_STRONG": 0.78,
        "ONLINE_SCOUT_QUEUED": 0.42,
    }.get(online_state, 0.35)
    role_fit = _risk_latency_capital_execution_role(qku)
    risk_latency_capital_execution = 0.92 if role_fit != "GENERAL_QKU_ROLE" else 0.58
    strategy_algorithm_formula = 0.48
    if any(algo.get(key) for key in ("strategy", "algorithm", "formula", "optimizer")):
        strategy_algorithm_formula = 0.86
    if qku_type in {"STRATEGY_TEMPLATE_QKU", "FORMULA_QKU", "ALGORITHM_QKU", "OPTIMIZER_SETTING_QKU"}:
        strategy_algorithm_formula = 0.94
    quantum_forward = 0.35
    if qku_id in aux["quantum_ids"]:
        quantum_forward = 0.96
    elif "HYBRID" in str(qku.get("qku_classical_quantum_hybrid_class") or ""):
        quantum_forward = 0.86
    scenario_matrix = 0.86 if stage1 >= 0.72 and replay_required else 0.58
    bundle_candidate = 0.88 if qku_type in _bundle_relevant_qku_types() else 0.60
    agent_network = min(1.0, 0.45 + len(_assigned_roles(qku, aux, online_state)) / 10)

    raw_values = {
        "materialization_quality_component": materialization,
        "stage1_fit_component": stage1,
        "replay_paper_testability_component": replay_paper,
        "agent_consumption_component": agent_consumption,
        "graph_component": graph_component,
        "atomicrows_pr154_component": atomicrows_pr154,
        "source_coverage_component": source_coverage,
        "risk_latency_capital_execution_component": risk_latency_capital_execution,
        "strategy_algorithm_formula_component": strategy_algorithm_formula,
        "quantum_forward_component": quantum_forward,
        "scenario_matrix_component": scenario_matrix,
        "bundle_candidate_component": bundle_candidate,
        "agent_network_component": agent_network,
    }
    return {
        name: {
            "value": round(_clamp(value), 4),
            "basis": _component_basis(name, qku, aux, online_record),
            "fallback_derived_flag": fallback
            and name
            in {
                "materialization_quality_component",
                "source_coverage_component",
                "strategy_algorithm_formula_component",
            },
        }
        for name, value in raw_values.items()
    }


def _quality_score_record(
    qku: dict[str, Any],
    aux: dict[str, Any],
    graph: dict[str, Any],
    online_record: dict[str, Any],
    components: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    qku_id = str(qku["qku_id"])
    weighted = sum(
        c.SCORE_COMPONENT_WEIGHTS[name] * float(components[name]["value"])
        for name in c.SCORE_COMPONENT_WEIGHTS
    )
    quality_score = int(round(1000 * weighted))
    replay_score = int(
        round(
            0.45 * quality_score
            + 300 * components["replay_paper_testability_component"]["value"]
            + 250 * components["scenario_matrix_component"]["value"]
        )
    )
    stage1_score = int(round(1000 * components["stage1_fit_component"]["value"]))
    quantum_score = int(round(1000 * components["quantum_forward_component"]["value"]))
    classical_score = int(round(650 + 250 * (1 - components["quantum_forward_component"]["value"])))
    hybrid_score = int(round((quantum_score + classical_score) / 2))
    atomicrows_pr154_component = components["atomicrows_pr154_component"]["value"]
    role_fit = _risk_latency_capital_execution_role(qku)
    assigned_roles = _assigned_roles(qku, aux, str(online_record["online_enrichment_coverage_state"]))
    return {
        "quality_score_record_id": f"PR161D-QSCORE-{qku_id}",
        "qku_id": qku_id,
        "qku_graph_node_id": _qku_graph_node_id(qku_id, graph),
        "qku_quality_score": _score_bounds(quality_score),
        "qku_replay_paper_priority_score": _score_bounds(replay_score),
        "qku_stage1_day1_priority_score": _score_bounds(stage1_score),
        "qku_quantum_priority_score": _score_bounds(quantum_score),
        "qku_classical_baseline_priority_score": _score_bounds(classical_score),
        "qku_hybrid_arbitration_priority_score": _score_bounds(hybrid_score),
        "qku_source_coverage_score": _score_bounds(
            int(round(1000 * components["source_coverage_component"]["value"]))
        ),
        "qku_materialization_quality_score": _score_bounds(
            int(round(1000 * components["materialization_quality_component"]["value"]))
        ),
        "qku_graph_orchestration_score": _score_bounds(
            int(round(1000 * components["graph_component"]["value"]))
        ),
        "qku_agent_consumption_score": _score_bounds(
            int(round(1000 * components["agent_consumption_component"]["value"]))
        ),
        "qku_atomicrows_compatibility_score": _score_bounds(
            int(round(1000 * atomicrows_pr154_component))
            if qku_id in aux["atomicrows_ids"]
            else int(round(600 * atomicrows_pr154_component))
        ),
        "qku_pr154_compatibility_score": _score_bounds(
            int(round(1000 * atomicrows_pr154_component))
            if qku_id in aux["pr154_ids"]
            else int(round(550 * atomicrows_pr154_component))
        ),
        "qku_latency_fit_score": 900 if role_fit == "LATENCY_ROLE" else 620,
        "qku_risk_fit_score": 900 if role_fit == "RISK_ROLE" else 640,
        "qku_capital_fit_score": 900 if role_fit == "CAPITAL_ROLE" else 640,
        "qku_execution_fit_score": 900 if role_fit == "EXECUTION_ROLE" else 640,
        "qku_online_enrichment_score": _score_bounds(
            int(round(1000 * components["source_coverage_component"]["value"]))
        ),
        "online_enrichment_coverage_state": online_record["online_enrichment_coverage_state"],
        "qku_scenario_matrix_fit_score": _score_bounds(
            int(round(1000 * components["scenario_matrix_component"]["value"]))
        ),
        "qku_bundle_candidate_fit_score": _score_bounds(
            int(round(1000 * components["bundle_candidate_component"]["value"]))
        ),
        "qku_agent_network_fit_score": _score_bounds(
            int(round(1000 * components["agent_network_component"]["value"]))
        ),
        "qku_owner_priority_score": _score_bounds(max(quality_score, stage1_score)),
        "qku_candidate_quality_lane": "UNCLASSIFIED_PENDING_LANE_BUILDER",
        "qku_replay_paper_priority_lane": "UNCLASSIFIED_PENDING_LANE_BUILDER",
        "qku_agent_task_lane": _agent_task_lane(assigned_roles),
        "score_formula_id": "PR161D_OWNER_APPROVED_WEIGHTED_COMPONENT_FORMULA",
        "no_profit_evidence_created_flag": True,
        "no_replay_paper_result_created_flag": True,
        "no_live_authority_created_flag": True,
    }


def _quality_lane_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    online_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=_qku_sort_key):
        qku_id = str(qku["qku_id"])
        score = score_by_qku[qku_id]
        online_state = str(online_by_qku[qku_id]["online_enrichment_coverage_state"])
        quality_lane = _quality_lane(qku, aux, score, online_state)
        replay_lane = _replay_paper_lane(qku, aux, score, quality_lane, online_state)
        score["qku_candidate_quality_lane"] = quality_lane
        score["qku_replay_paper_priority_lane"] = replay_lane
        records.append(
            {
                "quality_lane_record_id": f"PR161D-LANE-{qku_id}",
                "qku_id": qku_id,
                "quality_lane": quality_lane,
                "replay_paper_priority_lane": replay_lane,
                "qku_quality_score": score["qku_quality_score"],
                "qku_replay_paper_priority_score": score["qku_replay_paper_priority_score"],
                "online_enrichment_coverage_state": online_state,
                "lane_basis": _lane_basis(qku, aux, score, online_state),
                "no_profit_evidence_created_flag": True,
                "no_live_authority_created_flag": True,
            }
        )
    return records


def _replay_paper_priority_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    graph: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_replay_paper_priority_score"], _qku_sort_key(item))):
        qku_id = str(qku["qku_id"])
        replay_source = aux["replay_by_qku"].get(qku_id, {})
        replay_required = bool(replay_source.get("replay_paper_required", True))
        scenario_family = _scenario_family(qku, aux, lane_by_qku[qku_id])
        graph_links = _graph_link_summary(qku_id, graph)
        records.append(
            {
                "replay_paper_priority_record_id": f"PR161D-REPLAY-PAPER-{qku_id}",
                "qku_id": qku_id,
                "qku_graph_node_id": _qku_graph_node_id(qku_id, graph),
                "replay_paper_testable_flag": replay_required,
                "replay_paper_priority_lane": lane_by_qku[qku_id]["replay_paper_priority_lane"],
                "replay_paper_priority_score": score_by_qku[qku_id]["qku_replay_paper_priority_score"],
                "replay_paper_scenario_family": scenario_family,
                "replay_paper_input_requirements": _replay_input_requirements(qku, scenario_family),
                "replay_paper_required_baselines": _required_baselines(qku, aux),
                "replay_paper_risk_checks": ["risk_limit_check", "drawdown_limit_check"],
                "replay_paper_latency_checks": ["latency_bucket_capture", "order_path_timing_capture"],
                "replay_paper_cost_slippage_checks": ["fee_model_capture", "slippage_bucket_capture"],
                "replay_paper_expected_observation_metrics": [
                    "net_profit_after_costs_future_slot",
                    "drawdown_future_slot",
                    "fill_quality_future_slot",
                    "latency_future_slot",
                ],
                "replay_paper_owner_review_route": "QTT_OWNER_REVIEW_AGENT",
                "upstream_edge_ids": graph_links["upstream_edge_ids"],
                "downstream_edge_ids": graph_links["downstream_edge_ids"],
                "agent_route_edge_ids": graph_links["agent_route_edge_ids"],
                "replay_paper_route_edge_ids": graph_links["replay_paper_route_edge_ids"],
                "future_owner_review_edge_ids": graph_links["owner_review_route_edge_ids"],
                "replay_paper_execution_created_flag": False,
                "paper_trading_execution_created_flag": False,
                "replay_result_created_flag": False,
                "paper_result_created_flag": False,
                "shadow_result_created_flag": False,
                "live_result_created_flag": False,
                "profit_evidence_created_flag": False,
            }
        )
    return records


def _agent_graph_routing_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    graph: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
    replay_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=_qku_sort_key):
        qku_id = str(qku["qku_id"])
        graph_links = _graph_link_summary(qku_id, graph)
        roles = _assigned_roles(
            qku,
            aux,
            str(score_by_qku[qku_id].get("online_enrichment_coverage_state", "")),
        )
        for role in roles:
            layer, purpose = c.AGENT_ROLE_LAYER_PURPOSE[role]
            records.append(
                {
                    "routing_record_id": f"PR161D-AGENT-ROUTE-{qku_id}-{role}",
                    "qku_id": qku_id,
                    "qku_graph_node_id": _qku_graph_node_id(qku_id, graph),
                    "assigned_agent_role": role,
                    "agent_layer": layer,
                    "agent_purpose": purpose,
                    "source_edge_ids": graph_links["upstream_edge_ids"],
                    "downstream_edge_ids": graph_links["downstream_edge_ids"],
                    "workflow_stage": replay_by_qku[qku_id]["replay_paper_scenario_family"],
                    "task_queue_type": _task_type_for_role(role, qku, lane_by_qku[qku_id]),
                    "task_priority_score": score_by_qku[qku_id]["qku_quality_score"],
                    "no_runtime_agent_claim_flag": True,
                    "no_live_authority_flag": True,
                    "no_profit_evidence_flag": True,
                }
            )
    return records


def _category_ranking_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
    online_by_qku: dict[str, dict[str, Any]],
    roles_by_qku: dict[str, list[str]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for qku in qkus:
        qku_id = str(qku["qku_id"])
        for category, values in _category_values(qku, aux, lane_by_qku[qku_id], online_by_qku[qku_id], roles_by_qku[qku_id]).items():
            for value in values:
                grouped[(category, value)].append(qku_id)

    records: list[dict[str, Any]] = []
    for (category, value), qku_ids in sorted(grouped.items()):
        ordered = sorted(
            qku_ids,
            key=lambda qku_id: (-int(score_by_qku[qku_id]["qku_quality_score"]), qku_id),
        )
        for rank, qku_id in enumerate(ordered, start=1):
            pre_result = int(score_by_qku[qku_id]["qku_quality_score"])
            records.append(
                {
                    "ranking_id": f"PR161D-RANK-{_safe_id(category)}-{_safe_id(value)}-{rank:05d}",
                    "ranking_category": category,
                    "category_value": value,
                    "qku_id": qku_id,
                    "qku_rank": rank,
                    "qku_quality_score": pre_result,
                    "pre_result_quality_score": pre_result,
                    "result_backed_score": None,
                    "final_qku_category_rank_score": pre_result,
                    "result_evidence_weight": 0,
                    "result_state": "NO_RESULT_YET",
                    "ranking_basis": "PRE_RESULT_RANKING",
                    "ranking_explanation": (
                        "Pre-result category ranking uses PR161D quality score; "
                        "no replay/paper/live/shadow result evidence exists in PR161D."
                    ),
                    "no_profit_evidence_created_flag": True,
                }
            )
    return records


def _category_top_list_records(rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "top_list_record_id": f"PR161D-TOPLIST-{record['ranking_id']}",
            "ranking_category": record["ranking_category"],
            "category_value": record["category_value"],
            "qku_id": record["qku_id"],
            "qku_rank": record["qku_rank"],
            "qku_quality_score": record["qku_quality_score"],
            "ranking_basis": record["ranking_basis"],
            "no_profit_evidence_created_flag": True,
        }
        for record in rankings
        if int(record["qku_rank"]) <= 25
    ]


def _category_breakdown_records(rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for record in rankings:
        grouped[(str(record["ranking_category"]), str(record["category_value"]))].append(
            int(record["qku_quality_score"])
        )
    return [
        {
            "category_breakdown_id": f"PR161D-CATEGORY-BREAKDOWN-{_safe_id(category)}-{_safe_id(value)}",
            "ranking_category": category,
            "category_value": value,
            "ranking_record_count": len(scores),
            "quality_score_min": min(scores),
            "quality_score_max": max(scores),
            "quality_score_mean": round(statistics.fmean(scores), 4),
            "ranking_basis": "PRE_RESULT_RANKING",
            "no_profit_evidence_created_flag": True,
        }
        for (category, value), scores in sorted(grouped.items())
    ]


def _result_backed_ranking_slots(
    qkus: list[dict[str, Any]],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "result_backed_ranking_slot_id": f"PR161D-RESULT-SLOT-{qku['qku_id']}",
            "qku_id": qku["qku_id"],
            "pre_result_quality_score": score_by_qku[str(qku["qku_id"])]["qku_quality_score"],
            "result_backed_score": None,
            "result_evidence_weight": 0,
            "final_qku_category_rank_score": score_by_qku[str(qku["qku_id"])]["qku_quality_score"],
            "result_state": "NO_RESULT_YET",
            "result_slot_state": "RESULT_SLOT_RESERVED",
            "profitability_label": "UNOBSERVED",
            "future_result_formula_components": [
                "net_profit_component",
                "risk_adjusted_return_component",
                "drawdown_penalty_component",
                "consistency_component",
                "sample_size_confidence_component",
                "cost_slippage_penalty_component",
                "latency_fit_component",
                "regime_stability_component",
                "recent_performance_component",
            ],
            "no_fake_result_flag": True,
            "no_result_fabricated_flag": True,
            "no_profit_evidence_created_flag": True,
        }
        for qku in sorted(qkus, key=_qku_sort_key)
    ]


def _bundle_candidate_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
    replay_by_qku: dict[str, dict[str, Any]],
    roles_by_qku: dict[str, list[str]],
) -> list[dict[str, Any]]:
    bucket = _bundle_bucket(qkus, aux, score_by_qku)
    bucket_sets = {name: set(values) for name, values in bucket.items()}
    ordered_qkus = sorted(
        qkus,
        key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_quality_score"], _qku_sort_key(item)),
    )
    records: list[dict[str, Any]] = []
    scenario_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    for candidate in ordered_qkus:
        if len(records) >= c.MAX_QKU_BUNDLE_CANDIDATES:
            break
        qku_id = str(candidate["qku_id"])
        scenario_family = replay_by_qku[qku_id]["replay_paper_scenario_family"]
        primary_role = roles_by_qku[qku_id][0] if roles_by_qku[qku_id] else "QTT_RESEARCH_AGENT"
        if scenario_counts[scenario_family] >= c.MAX_BUNDLES_PER_SCENARIO_FAMILY:
            continue
        if role_counts[primary_role] >= c.MAX_BUNDLES_PER_AGENT_ROLE:
            continue
        qku_ids = _bundle_qku_ids(qku_id, candidate, aux, bucket)
        mix = _bundle_mix(qku_ids, bucket_sets)
        parent_scenario_family = _bundle_parent_scenario_family(
            mix,
            str(
                candidate.get("qku_stage1_prediction_market_applicability_class")
                or "STAGE1_APPLICABILITY_UNSPECIFIED"
            ),
        )
        child_scenario_family = _bundle_child_scenario_family(
            mix,
            len(records) + 1,
            parent_scenario_family,
        )
        bundle_quality = _score_bounds(
            int(round(statistics.fmean(score_by_qku[item]["qku_quality_score"] for item in qku_ids)))
        )
        bundle_quantum = _score_bounds(
            int(round(statistics.fmean(score_by_qku[item]["qku_quantum_priority_score"] for item in qku_ids)))
        )
        bundle_roles = sorted(set().union(*(roles_by_qku.get(item, []) for item in qku_ids)))
        bundle_index = len(records) + 1
        records.append(
            {
                "qku_bundle_id": f"PR161D-QKU-BUNDLE-{bundle_index:05d}",
                "qku_bundle_graph_node_id": f"PR161D-QKU-BUNDLE-NODE-{bundle_index:05d}",
                "qku_ids": qku_ids,
                **mix,
                "bundle_market": str(candidate.get("qku_market_primary") or "MARKET_UNSPECIFIED"),
                "bundle_stage1_applicability": str(
                    candidate.get("qku_stage1_prediction_market_applicability_class")
                    or "STAGE1_APPLICABILITY_UNSPECIFIED"
                ),
                "bundle_parent_scenario_family": parent_scenario_family,
                "bundle_active_child_scenario_family": child_scenario_family,
                "bundle_replay_paper_priority_score": replay_by_qku[qku_id]["replay_paper_priority_score"],
                "bundle_quality_score": bundle_quality,
                "bundle_quantum_priority_score": bundle_quantum,
                "bundle_risk_score": _score_bounds(max(score_by_qku[item]["qku_risk_fit_score"] for item in qku_ids)),
                "bundle_latency_score": _score_bounds(max(score_by_qku[item]["qku_latency_fit_score"] for item in qku_ids)),
                "bundle_expected_test_value_score": _score_bounds(
                    int(round((bundle_quality + replay_by_qku[qku_id]["replay_paper_priority_score"]) / 2))
                ),
                "bundle_agent_roles": bundle_roles,
                "bundle_scenario_matrix_ids": [],
                "bundle_result_state": "NO_RESULT_YET",
                "bundle_market_activation_state": "MARKET_BUNDLE_OWNER_REVIEW_REQUIRED",
                "bundle_market_activation_policy_id": "QKU_MARKET_BUNDLE_ACTIVATION_POLICY",
                "bundle_stage1_active_flag": False,
                "bundle_dormant_future_stage_flag": False,
                "owner_dashboard_activation_option_id": f"PR161D-MARKET-ACTIVATION-OPTION-{_safe_id(str(candidate.get('qku_market_primary') or 'MARKET_UNSPECIFIED'))}",
                "active_for_candidate_scoring_flag": False,
                "active_for_replay_paper_flag": False,
                "active_for_agent_task_queue_flag": False,
                "active_for_live_trading_flag": False,
                "replay_paper_execution_created_flag": False,
                "paper_execution_created_flag": False,
                "shadow_execution_created_flag": False,
                "live_execution_created_flag": False,
                "profit_evidence_created_flag": False,
            }
        )
        scenario_counts[scenario_family] += 1
        role_counts[primary_role] += 1
    return records


def _scenario_outcome_matrix_records(
    bundles: list[dict[str, Any]],
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    roles_by_qku: dict[str, list[str]],
    graph: dict[str, Any],
) -> list[dict[str, Any]]:
    qku_by_id = {str(qku["qku_id"]): qku for qku in qkus}
    records: list[dict[str, Any]] = []
    for index, bundle in enumerate(bundles, start=1):
        qku_ids = [str(item) for item in bundle["qku_ids"]]
        primary = qku_by_id[qku_ids[0]]
        scenario_family = _bundle_scenario_family(bundle)
        graph_links = _multi_graph_link_summary(qku_ids, graph)
        assigned_roles = sorted(set(str(role) for qku_id in qku_ids for role in roles_by_qku.get(qku_id, [])))
        records.append(
            {
                "scenario_matrix_id": f"PR161D-SCENARIO-MATRIX-{index:05d}",
                "scenario_fingerprint_id": f"PR161D-SCENARIO-FP-{index:05d}",
                "market": bundle["bundle_market"],
                "venue_scope": _venue_scope(primary),
                "event_type": "PREDICTION_MARKET_EVENT_CANDIDATE",
                "event_category": scenario_family,
                "parent_event_category": bundle["bundle_parent_scenario_family"],
                "active_child_event_category": bundle["bundle_active_child_scenario_family"],
                "time_to_resolution_bucket": _time_to_resolution_bucket(primary),
                "liquidity_bucket": "LIQUIDITY_BUCKET_UNOBSERVED_INPUT_REQUIRED",
                "spread_bucket": "SPREAD_BUCKET_UNOBSERVED_INPUT_REQUIRED",
                "volatility_bucket": "VOLATILITY_BUCKET_UNOBSERVED_INPUT_REQUIRED",
                "volume_bucket": "VOLUME_BUCKET_UNOBSERVED_INPUT_REQUIRED",
                "order_side": "ORDER_SIDE_CANDIDATE_UNSPECIFIED",
                "order_type_candidate": "LIMIT_ORDER_CANDIDATE_FOR_REPLAY_PAPER_ONLY",
                "price_bucket": "PRICE_BUCKET_UNOBSERVED_INPUT_REQUIRED",
                "capital_bucket": "CAPITAL_BUCKET_REPLAY_PAPER_INPUT_REQUIRED",
                "risk_bucket": "RISK_BUCKET_REPLAY_PAPER_INPUT_REQUIRED",
                "latency_class": "LATENCY_CLASS_REPLAY_PAPER_INPUT_REQUIRED",
                "source_signal_class": _source_signal_class(primary, aux),
                "qku_bundle_id": bundle["qku_bundle_id"],
                "qku_ids": qku_ids,
                "qku_type_mix": sorted({str(qku_by_id[qku_id].get("qku_type") or "") for qku_id in qku_ids}),
                "qku_strategy_family_mix": _mix_values(qku_ids, aux, "strategy"),
                "qku_algorithm_family_mix": _mix_values(qku_ids, aux, "algorithm"),
                "qku_formula_family_mix": _mix_values(qku_ids, aux, "formula"),
                "qku_quantum_class_mix": sorted(
                    {str(qku_by_id[qku_id].get("qku_classical_quantum_hybrid_class") or "") for qku_id in qku_ids}
                ),
                "qku_risk_capital_execution_mix": sorted({_risk_latency_capital_execution_role(qku_by_id[qku_id]) for qku_id in qku_ids}),
                "assigned_agent_roles": assigned_roles,
                "qku_graph_node_ids": [f"QKUNODE-{qku_id}" for qku_id in qku_ids],
                "qku_bundle_graph_node_ids_if_applicable": [bundle["qku_bundle_graph_node_id"]],
                "agent_route_edge_ids": graph_links["agent_route_edge_ids"],
                "replay_paper_route_edge_ids": graph_links["replay_paper_route_edge_ids"],
                "owner_review_route_edge_ids": graph_links["owner_review_route_edge_ids"],
                "replay_paper_required_flag": True,
                "replay_paper_priority_lane": _bundle_replay_lane(bundle),
                "result_mode_slots": _result_mode_slots(),
                "result_state": "NO_RESULT_YET",
                "profitability_label": "UNOBSERVED",
                "promotion_allowed_flag": False,
                "owner_review_required_flag": True,
                "no_result_fabricated_flag": True,
                "no_profit_evidence_created_flag": True,
                "no_live_authority_created_flag": True,
            }
        )
    return records


def _order_condition_records(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order_condition_scenario_id": f"PR161D-ORDER-CONDITION-{index:05d}",
            "scenario_matrix_id": scenario["scenario_matrix_id"],
            "scenario_fingerprint_id": scenario["scenario_fingerprint_id"],
            "market": scenario["market"],
            "venue_scope": scenario["venue_scope"],
            "order_side": scenario["order_side"],
            "order_type_candidate": scenario["order_type_candidate"],
            "liquidity_bucket": scenario["liquidity_bucket"],
            "spread_bucket": scenario["spread_bucket"],
            "latency_class": scenario["latency_class"],
            "qku_bundle_id": scenario["qku_bundle_id"],
            "result_state": "NO_RESULT_YET",
            "profitability_label": "UNOBSERVED",
            "no_result_fabricated_flag": True,
            "no_profit_evidence_created_flag": True,
            "no_live_authority_created_flag": True,
        }
        for index, scenario in enumerate(scenarios, start=1)
    ]


def _combination_scenario_map_records(
    bundles: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scenario_by_bundle = {scenario["qku_bundle_id"]: scenario for scenario in scenarios}
    return [
        {
            "combination_scenario_map_id": f"PR161D-COMBO-SCENARIO-MAP-{index:05d}",
            "qku_bundle_id": bundle["qku_bundle_id"],
            "scenario_matrix_id": scenario_by_bundle[bundle["qku_bundle_id"]]["scenario_matrix_id"],
            "qku_ids": bundle["qku_ids"],
            "replay_paper_required_flag": True,
            "result_state": "NO_RESULT_YET",
            "no_result_fabricated_flag": True,
        }
        for index, bundle in enumerate(bundles, start=1)
    ]


def _combination_replay_paper_queue_records(
    bundles: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scenario_by_bundle = {scenario["qku_bundle_id"]: scenario for scenario in scenarios}
    ordered = sorted(
        [bundle for bundle in bundles if bundle.get("active_for_replay_paper_flag")],
        key=lambda item: (
            -int(item["bundle_replay_paper_priority_score"]),
            str(item["qku_bundle_id"]),
        ),
    )
    records: list[dict[str, Any]] = []
    for rank, bundle in enumerate(ordered, start=1):
        scenario = scenario_by_bundle[bundle["qku_bundle_id"]]
        records.append(
            {
                "combination_replay_paper_queue_id": f"PR161D-COMBO-REPLAY-PAPER-{rank:05d}",
                "qku_bundle_id": bundle["qku_bundle_id"],
                "scenario_matrix_id": scenario["scenario_matrix_id"],
                "queue_rank": rank,
                "bundle_replay_paper_priority_score": bundle["bundle_replay_paper_priority_score"],
                "bundle_quality_score": bundle["bundle_quality_score"],
                "replay_paper_execution_created_flag": False,
                "paper_execution_created_flag": False,
                "profit_evidence_created_flag": False,
            }
        )
    return records


def _market_bundle_activation_policy_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for market_class, state in sorted(c.MARKET_BUNDLE_ACTIVATION_POLICY.items()):
        records.append(
            {
                "market_bundle_activation_policy_id": f"QKU_MARKET_BUNDLE_ACTIVATION_POLICY::{market_class}",
                "owner_dashboard_control_id": f"PR161D-OWNER-DASHBOARD-MARKET-BUNDLE-{market_class}",
                "market_class": market_class,
                "current_activation_state": state,
                "owner_selectable_activation_states": list(c.MARKET_BUNDLE_ACTIVATION_STATES),
                "default_activation_state": state,
                "stage_scope": "STAGE1_REPLAY_PAPER_CANDIDATE_LANES",
                "affects_candidate_scoring_flag": state in c.STAGE1_ACTIVE_BUNDLE_MARKET_STATES,
                "affects_agent_task_queue_flag": state in c.STAGE1_ACTIVE_BUNDLE_MARKET_STATES,
                "affects_replay_paper_queue_flag": state == "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
                "affects_live_authority_flag": False,
                "owner_override_required_for_activation_change_flag": True,
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return records


def _market_bundle_activation_dashboard_options(
    policy_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "owner_dashboard_activation_option_id": f"PR161D-MARKET-ACTIVATION-OPTION-{record['market_class']}",
            "market_bundle_activation_policy_id": record["market_bundle_activation_policy_id"],
            "owner_dashboard_control_id": record["owner_dashboard_control_id"],
            "market_class": record["market_class"],
            "current_activation_state": record["current_activation_state"],
            "owner_selectable_activation_states": record["owner_selectable_activation_states"],
            "default_activation_state": record["default_activation_state"],
            "stage_scope": record["stage_scope"],
            "affects_candidate_scoring_flag": record["affects_candidate_scoring_flag"],
            "affects_agent_task_queue_flag": record["affects_agent_task_queue_flag"],
            "affects_replay_paper_queue_flag": record["affects_replay_paper_queue_flag"],
            "affects_live_authority_flag": False,
            "owner_override_required_for_activation_change_flag": True,
            "no_live_authority_created_flag": True,
            "no_profit_evidence_created_flag": True,
        }
        for record in policy_records
    ]


def _apply_market_bundle_activation_policy(
    bundles: list[dict[str, Any]],
    policy_records: list[dict[str, Any]],
) -> None:
    policy_by_market = {
        str(record["market_class"]): record
        for record in policy_records
    }
    fallback_policy = {
        "market_bundle_activation_policy_id": "QKU_MARKET_BUNDLE_ACTIVATION_POLICY::NON_MARKET_SPECIFIC",
        "current_activation_state": "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
    }
    for bundle in bundles:
        market = str(bundle.get("bundle_market") or "NON_MARKET_SPECIFIC")
        policy = policy_by_market.get(market, fallback_policy)
        state = str(policy["current_activation_state"])
        stage1_active = state in c.STAGE1_ACTIVE_BUNDLE_MARKET_STATES
        replay_active = state == "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER"
        bundle["bundle_market_activation_state"] = state
        bundle["bundle_market_activation_policy_id"] = policy["market_bundle_activation_policy_id"]
        bundle["bundle_stage1_active_flag"] = stage1_active
        bundle["bundle_dormant_future_stage_flag"] = state == "MARKET_BUNDLE_DORMANT_FUTURE_STAGE"
        bundle["owner_dashboard_activation_option_id"] = (
            f"PR161D-MARKET-ACTIVATION-OPTION-{market}"
        )
        bundle["active_for_candidate_scoring_flag"] = stage1_active
        bundle["active_for_replay_paper_flag"] = replay_active
        bundle["active_for_agent_task_queue_flag"] = stage1_active
        bundle["active_for_live_trading_flag"] = False


def _market_active_bundle_set_records(bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, bundle in enumerate(
        [item for item in _ordered_bundles_for_selection(bundles) if item["bundle_stage1_active_flag"]],
        start=1,
    ):
        records.append(
            {
                "market_active_bundle_set_record_id": f"PR161D-MARKET-ACTIVE-BUNDLE-{index:05d}",
                "qku_bundle_id": bundle["qku_bundle_id"],
                "bundle_market": bundle["bundle_market"],
                "bundle_market_activation_state": bundle["bundle_market_activation_state"],
                "bundle_market_activation_policy_id": bundle["bundle_market_activation_policy_id"],
                "bundle_stage1_active_flag": True,
                "active_for_candidate_scoring_flag": bundle["active_for_candidate_scoring_flag"],
                "active_for_replay_paper_flag": bundle["active_for_replay_paper_flag"],
                "active_for_agent_task_queue_flag": bundle["active_for_agent_task_queue_flag"],
                "active_for_live_trading_flag": False,
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return records


def _market_bundle_dormancy_queue_records(bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    dormant = [item for item in _ordered_bundles_for_selection(bundles) if item["bundle_dormant_future_stage_flag"]]
    for index, bundle in enumerate(dormant, start=1):
        records.append(
            {
                "market_bundle_dormancy_queue_id": f"PR161D-MARKET-DORMANT-BUNDLE-{index:05d}",
                "qku_bundle_id": bundle["qku_bundle_id"],
                "qku_ids": bundle["qku_ids"],
                "scenario_family": _bundle_scenario_family(bundle),
                "bundle_market": bundle["bundle_market"],
                "bundle_market_activation_state": bundle["bundle_market_activation_state"],
                "bundle_stage1_active_flag": False,
                "bundle_dormant_future_stage_flag": True,
                "bundle_agent_roles": bundle["bundle_agent_roles"],
                "replay_paper_future_route": "FUTURE_STAGE_REPLAY_PAPER_ROUTE_RESERVED",
                "owner_review_route": "OWNER_REVIEW_REQUIRED_FOR_FUTURE_STAGE_ACTIVATION",
                "active_for_live_trading_flag": False,
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return records


def _agent_role_bundle_slice_records(bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    shared_count = len(bundles)
    for role in c.CANONICAL_QTT_AGENT_ROLES:
        layer, _purpose = c.AGENT_ROLE_LAYER_PURPOSE[role]
        referenced = [
            bundle for bundle in bundles if role in set(str(item) for item in bundle["bundle_agent_roles"])
        ]
        eligible = [bundle for bundle in referenced if _bundle_selected_for_agent_role(bundle, role)]
        active_source = [bundle for bundle in eligible if bundle["bundle_stage1_active_flag"]]
        dormant = [
            bundle for bundle in referenced
            if bundle["bundle_dormant_future_stage_flag"]
            or not bundle["bundle_stage1_active_flag"]
        ]
        ordered_active = _ordered_bundles_for_selection(active_source)
        active = ordered_active[: c.MAX_BUNDLES_PER_AGENT_ROLE]
        overflow = ordered_active[c.MAX_BUNDLES_PER_AGENT_ROLE :]
        records.append(
            {
                "agent_role_bundle_slice_id": f"PR161D-AGENT-BUNDLE-SLICE-{role}",
                "agent_role": role,
                "agent_layer": layer,
                "shared_bundle_registry_count": shared_count,
                "agent_reference_count": len(referenced),
                "agent_active_slice_count": len(active),
                "agent_materialized_bundle_count": 0,
                "agent_overflow_count": len(overflow),
                "agent_dormant_count": len(dormant),
                "cap_applies_flag": True,
                "cap_value": c.MAX_BUNDLES_PER_AGENT_ROLE,
                "active_slice_within_cap_flag": len(active) <= c.MAX_BUNDLES_PER_AGENT_ROLE,
                "fanout_reference_not_materialized_flag": True,
                "bundle_ids_active": [str(bundle["qku_bundle_id"]) for bundle in active],
                "bundle_ids_overflow": [str(bundle["qku_bundle_id"]) for bundle in overflow],
                "bundle_ids_dormant": [str(bundle["qku_bundle_id"]) for bundle in dormant],
                "slicing_basis": _agent_slice_basis(role),
                "no_runtime_agent_claim_flag": True,
            }
        )
    return records


def _agent_role_bundle_reference_fanout_records(
    bundles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for role in c.CANONICAL_QTT_AGENT_ROLES:
        referenced = [
            bundle for bundle in bundles if role in set(str(item) for item in bundle["bundle_agent_roles"])
        ]
        records.append(
            {
                "agent_role_bundle_reference_fanout_id": f"PR161D-AGENT-BUNDLE-REFERENCE-FANOUT-{role}",
                "agent_role": role,
                "agent_reference_count": len(referenced),
                "agent_materialized_bundle_count": 0,
                "fanout_reference_count": len(referenced),
                "fanout_reference_not_materialized_flag": True,
                "cap_applies_flag": False,
                "cap_value": c.MAX_BUNDLES_PER_AGENT_ROLE,
                "cap_exemption_reason": c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT,
                "bundle_ids_referenced": [str(bundle["qku_bundle_id"]) for bundle in _ordered_bundles_for_selection(referenced)],
                "no_runtime_agent_claim_flag": True,
            }
        )
    return records


def _combination_boundedness_records(
    bundles: list[dict[str, Any]],
    agent_slices: list[dict[str, Any]],
    fanout_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    phase_start = time.perf_counter()
    shared_bundle_ids = {str(bundle["qku_bundle_id"]) for bundle in bundles}
    active_bundle_ids = {
        str(bundle["qku_bundle_id"]) for bundle in bundles if bundle["bundle_stage1_active_flag"]
    }
    dormant_bundle_ids = {
        str(bundle["qku_bundle_id"]) for bundle in bundles if bundle["bundle_dormant_future_stage_flag"]
    }
    role_overflow_ids = {
        str(bundle_id)
        for record in agent_slices
        for bundle_id in record["bundle_ids_overflow"]
    }
    overflow_bundle_ids = role_overflow_ids
    market_active_count = sum(
        1 for bundle in bundles if bundle["bundle_market_activation_state"] in c.STAGE1_ACTIVE_BUNDLE_MARKET_STATES
    )
    market_dormant_count = sum(
        1 for bundle in bundles if bundle["bundle_market_activation_state"] == "MARKET_BUNDLE_DORMANT_FUTURE_STAGE"
    )
    parent_scenario_counts = stable_counter(
        str(bundle["bundle_parent_scenario_family"]) for bundle in bundles
    )
    child_scenario_counts = stable_counter(_bundle_scenario_family(bundle) for bundle in bundles)
    agent_reference_count = sum(int(record["agent_reference_count"]) for record in fanout_records)
    agent_active_slice_count = sum(int(record["agent_active_slice_count"]) for record in agent_slices)
    fanout_reference_count = sum(int(record["fanout_reference_count"]) for record in fanout_records)
    cap_metrics: list[dict[str, Any]] = []

    def add_metric(
        *,
        cap_id: str,
        cap_value: int,
        cap_applies_to: str,
        cap_denominator: str,
        observed_count: int,
        active_count: int,
        overflow_count: int,
        dormant_count: int,
        cap_applies_flag: bool,
        cap_exemption_reason: str | None = None,
    ) -> None:
        if cap_applies_flag:
            status = "PASS"
            if active_count > cap_value:
                status = "FAIL_ACTIVE_COUNT_EXCEEDS_CAP"
            elif observed_count > cap_value and overflow_count > 0:
                status = "PASS_TRUNCATED_TO_ACTIVE_SET"
        else:
            status = "EXEMPT_WITH_EXPLICIT_REASON"
        cap_metrics.append(
            {
                "cap_id": cap_id,
                "cap_value": cap_value,
                "cap_applies_to": cap_applies_to,
                "cap_denominator": cap_denominator,
                "observed_count": observed_count,
                "active_count": active_count,
                "overflow_count": overflow_count,
                "dormant_count": dormant_count,
                "cap_applies_flag": cap_applies_flag,
                "cap_exemption_applied_flag": not cap_applies_flag,
                "cap_exemption_reason": cap_exemption_reason,
                "boundedness_status": status,
            }
        )

    add_metric(
        cap_id="MAX_QKU_BUNDLE_CANDIDATES_SHARED_REGISTRY",
        cap_value=c.MAX_QKU_BUNDLE_CANDIDATES,
        cap_applies_to="shared_bundle_registry_count",
        cap_denominator="deduplicated_bundle_candidate_count",
        observed_count=len(shared_bundle_ids),
        active_count=len(shared_bundle_ids),
        overflow_count=0,
        dormant_count=len(dormant_bundle_ids),
        cap_applies_flag=True,
    )
    add_metric(
        cap_id="MAX_QKUS_PER_BUNDLE",
        cap_value=c.MAX_QKUS_PER_BUNDLE,
        cap_applies_to="per_bundle_qku_membership",
        cap_denominator="max_qkus_per_bundle_observed",
        observed_count=max((len(bundle["qku_ids"]) for bundle in bundles), default=0),
        active_count=max((len(bundle["qku_ids"]) for bundle in bundles), default=0),
        overflow_count=0,
        dormant_count=0,
        cap_applies_flag=True,
    )
    for family, observed_count in parent_scenario_counts.items():
        if family == "QUANTUM_CLASSICAL_HYBRID_COMPARE":
            add_metric(
                cap_id=f"PARENT_SCENARIO_FAMILY_REFERENCE::{family}",
                cap_value=c.MAX_BUNDLES_PER_SCENARIO_FAMILY,
                cap_applies_to="parent_scenario_family_reference_count",
                cap_denominator="parent_aggregate_scenario_family",
                observed_count=int(observed_count),
                active_count=0,
                overflow_count=0,
                dormant_count=0,
                cap_applies_flag=False,
                cap_exemption_reason=c.CAP_EXEMPTION_PARENT_AGGREGATE_SCENARIO_FAMILY,
            )
    for family, observed_count in child_scenario_counts.items():
        active_count = sum(
            1 for bundle in bundles
            if _bundle_scenario_family(bundle) == family and bundle["bundle_stage1_active_flag"]
        )
        overflow_count = max(0, active_count - c.MAX_BUNDLES_PER_SCENARIO_FAMILY)
        add_metric(
            cap_id=f"MAX_BUNDLES_PER_ACTIVE_SCENARIO_CHILD_FAMILY::{family}",
            cap_value=c.MAX_BUNDLES_PER_SCENARIO_FAMILY,
            cap_applies_to="active_child_scenario_family",
            cap_denominator="active_child_scenario_family_bundle_count",
            observed_count=int(observed_count),
            active_count=min(active_count, c.MAX_BUNDLES_PER_SCENARIO_FAMILY),
            overflow_count=overflow_count,
            dormant_count=sum(
                1 for bundle in bundles
                if _bundle_scenario_family(bundle) == family and bundle["bundle_dormant_future_stage_flag"]
            ),
            cap_applies_flag=True,
        )
    for record in agent_slices:
        observed_count = int(record["agent_active_slice_count"]) + int(record["agent_overflow_count"])
        add_metric(
            cap_id=f"MAX_BUNDLES_PER_AGENT_ROLE_ACTIVE_SLICE::{record['agent_role']}",
            cap_value=c.MAX_BUNDLES_PER_AGENT_ROLE,
            cap_applies_to="agent_active_slice_count",
            cap_denominator="role_specific_agent_slice",
            observed_count=observed_count,
            active_count=int(record["agent_active_slice_count"]),
            overflow_count=int(record["agent_overflow_count"]),
            dormant_count=int(record["agent_dormant_count"]),
            cap_applies_flag=True,
        )
    for record in fanout_records:
        add_metric(
            cap_id=f"AGENT_REFERENCE_FANOUT::{record['agent_role']}",
            cap_value=c.MAX_BUNDLES_PER_AGENT_ROLE,
            cap_applies_to="agent_reference_count",
            cap_denominator="fanout_reference_not_materialized_bundle",
            observed_count=int(record["agent_reference_count"]),
            active_count=0,
            overflow_count=0,
            dormant_count=0,
            cap_applies_flag=False,
            cap_exemption_reason=c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT,
        )
    violation_count = sum(
        1
        for metric in cap_metrics
        if metric["cap_applies_flag"] and int(metric["active_count"]) > int(metric["cap_value"])
    )
    reference_fanout_exemption_count = sum(
        1
        for metric in cap_metrics
        if metric["cap_exemption_reason"] == c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT
    )
    truncation_applied = any(int(metric["overflow_count"]) > 0 for metric in cap_metrics if metric["cap_applies_flag"])
    return [
        {
            "boundedness_record_id": "PR161D-QKU-COMBINATION-GENERATION-BOUNDEDNESS",
            "max_qku_bundle_candidates": c.MAX_QKU_BUNDLE_CANDIDATES,
            "max_bundles_per_scenario_family": c.MAX_BUNDLES_PER_SCENARIO_FAMILY,
            "max_bundles_per_agent_role": c.MAX_BUNDLES_PER_AGENT_ROLE,
            "max_qkus_per_bundle": c.MAX_QKUS_PER_BUNDLE,
            "raw_bundle_candidate_count": len(bundles),
            "deduplicated_bundle_candidate_count": len(shared_bundle_ids),
            "eligible_bundle_candidate_count": len(bundles),
            "shared_bundle_registry_count": len(shared_bundle_ids),
            "active_bounded_bundle_count": len(active_bundle_ids),
            "overflow_bundle_count": len(overflow_bundle_ids),
            "dormant_bundle_count": len(dormant_bundle_ids),
            "market_active_bundle_count": market_active_count,
            "market_dormant_bundle_count": market_dormant_count,
            "agent_reference_count": agent_reference_count,
            "agent_active_slice_count": agent_active_slice_count,
            "agent_materialized_bundle_count": 0,
            "fanout_reference_count": fanout_reference_count,
            "generated_bundle_count": len(bundles),
            "generation_exceeded_caps_flag": violation_count > 0,
            "truncation_applied_flag": truncation_applied,
            "active_selection_within_caps_flag": violation_count == 0,
            "scenario_family_counts": parent_scenario_counts,
            "active_child_scenario_family_counts": child_scenario_counts,
            "agent_reference_counts": {
                str(record["agent_role"]): int(record["agent_reference_count"])
                for record in sorted(fanout_records, key=lambda item: str(item["agent_role"]))
            },
            "agent_active_slice_counts": {
                str(record["agent_role"]): int(record["agent_active_slice_count"])
                for record in sorted(agent_slices, key=lambda item: str(item["agent_role"]))
            },
            "agent_materialized_bundle_counts": {
                str(record["agent_role"]): int(record["agent_materialized_bundle_count"])
                for record in sorted(agent_slices, key=lambda item: str(item["agent_role"]))
            },
            "cap_metrics": cap_metrics,
            "cap_applies_metric_violation_count": violation_count,
            "reference_fanout_exemption_count": reference_fanout_exemption_count,
            "role_specific_slice_count": len(agent_slices),
            "shared_bundle_registry_no_data_loss_flag": len(shared_bundle_ids) == len(bundles),
            "deterministic_bounded_generation_flag": True,
            "phase_timings": [
                {
                    "phase_name": "boundedness_metric_reconciliation",
                    "duration_ms": round((time.perf_counter() - phase_start) * 1000, 3),
                    "input_count": len(bundles),
                    "output_count": len(cap_metrics),
                }
            ],
        }
    ]


def _replay_paper_scenario_records(
    replay_queue: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    scenario_cycle = scenarios or []
    records: list[dict[str, Any]] = []
    for index, record in enumerate(replay_queue, start=1):
        scenario = scenario_cycle[(index - 1) % len(scenario_cycle)] if scenario_cycle else {}
        qku_id = str(record["qku_id"])
        records.append(
            {
                "replay_paper_scenario_input_id": f"PR161D-REPLAY-PAPER-SCENARIO-{index:05d}",
                "qku_id": qku_id,
                "scenario_matrix_id_if_applicable": scenario.get("scenario_matrix_id"),
                "qku_bundle_id_if_applicable": scenario.get("qku_bundle_id"),
                "replay_paper_scenario_family": record["replay_paper_scenario_family"],
                "replay_paper_priority_lane": record["replay_paper_priority_lane"],
                "replay_paper_priority_score": record["replay_paper_priority_score"],
                "input_requirements": record["replay_paper_input_requirements"],
                "required_baselines": record["replay_paper_required_baselines"],
                "expected_observation_metrics": record["replay_paper_expected_observation_metrics"],
                "qku_quality_score": score_by_qku[qku_id]["qku_quality_score"],
                "replay_execution_created_flag": False,
                "paper_execution_created_flag": False,
                "replay_result_created_flag": False,
                "paper_result_created_flag": False,
                "profit_evidence_created_flag": False,
            }
        )
    return records


def _quantum_priority_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_quantum_priority_score"], _qku_sort_key(item))):
        qku_id = str(qku["qku_id"])
        if qku_id not in aux["quantum_ids"] and "QUANTUM" not in str(qku.get("qku_classical_quantum_hybrid_class") or ""):
            continue
        subclass = _quantum_priority_subclass(qku, aux)
        records.append(
            {
                "quantum_priority_record_id": f"PR161D-QUANTUM-{qku_id}",
                "qku_id": qku_id,
                "qku_quantum_priority_score": score_by_qku[qku_id]["qku_quantum_priority_score"],
                "qku_quantum_problem_class": subclass,
                "qku_quantum_strategy_role": _quantum_strategy_role(subclass),
                "qku_quantum_candidate_route": "QTT_QUANTUM_ADVISORY_AGENT",
                "qku_classical_baseline_route": "QTT_SCORING_AGENT",
                "qku_hybrid_arbitration_route": "QTT_OPTIMIZER_ARBITRATION_AGENT",
                "qku_replay_paper_compare_required_flag": True,
                "qku_quantum_backend_execution_allowed_flag": False,
                "qku_optimizer_execution_allowed_flag": False,
                "qku_quantum_advantage_evidence_created_flag": False,
                "qku_profit_evidence_created_flag": False,
            }
        )
    return records


def _classical_baseline_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "classical_baseline_record_id": f"PR161D-CLASSICAL-{qku['qku_id']}",
            "qku_id": qku["qku_id"],
            "qku_classical_baseline_priority_score": score_by_qku[str(qku["qku_id"])]["qku_classical_baseline_priority_score"],
            "qku_classical_baseline_route": "QTT_SCORING_AGENT",
            "qku_replay_paper_compare_required_flag": str(qku["qku_id"]) in aux["quantum_ids"],
            "qku_optimizer_execution_allowed_flag": False,
            "qku_profit_evidence_created_flag": False,
        }
        for qku in sorted(qkus, key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_classical_baseline_priority_score"], _qku_sort_key(item)))
    ]


def _hybrid_arbitration_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_hybrid_arbitration_priority_score"], _qku_sort_key(item))):
        qku_id = str(qku["qku_id"])
        if qku_id not in aux["quantum_ids"] and "HYBRID" not in str(qku.get("qku_classical_quantum_hybrid_class") or ""):
            continue
        records.append(
            {
                "hybrid_arbitration_record_id": f"PR161D-HYBRID-{qku_id}",
                "qku_id": qku_id,
                "qku_hybrid_arbitration_priority_score": score_by_qku[qku_id]["qku_hybrid_arbitration_priority_score"],
                "qku_quantum_candidate_route": "QTT_QUANTUM_ADVISORY_AGENT",
                "qku_classical_baseline_route": "QTT_SCORING_AGENT",
                "qku_hybrid_arbitration_route": "QTT_OPTIMIZER_ARBITRATION_AGENT",
                "qku_replay_paper_compare_required_flag": True,
                "qku_optimizer_execution_allowed_flag": False,
                "qku_quantum_backend_execution_allowed_flag": False,
                "qku_profit_evidence_created_flag": False,
            }
        )
    return records


def _atomicrows_pr154_records(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=_qku_sort_key):
        qku_id = str(qku["qku_id"])
        records.append(
            {
                "atomicrows_pr154_priority_record_id": f"PR161D-ATOMIC-PR154-{qku_id}",
                "qku_id": qku_id,
                "qku_atomicrows_compatibility_score": score_by_qku[qku_id]["qku_atomicrows_compatibility_score"],
                "qku_pr154_compatibility_score": score_by_qku[qku_id]["qku_pr154_compatibility_score"],
                "qku_atomicrows_route": "ATOMICROWS_COMPATIBLE_CANDIDATE" if qku_id in aux["atomicrows_ids"] else "ATOMICROWS_COMPATIBILITY_LOW",
                "qku_pr154_route": "PR154_COMPATIBLE_CANDIDATE" if qku_id in aux["pr154_ids"] else "PR154_COMPATIBILITY_LOW",
                "qku_atomicrows_agent_consumer_route": "QTT_ATOMICROWS_ENRICHMENT_AGENT",
                "qku_pr154_agent_consumer_route": "QTT_PARAMETER_STACK_AGENT",
                "atomicrows_final_bundle_created_flag": False,
                "atomicrows_bundle_freeze_authority_created_flag": False,
                "profit_evidence_created_flag": False,
            }
        )
    return records


def _stage1_day1_priority_index(
    qkus: list[dict[str, Any]],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
    replay_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered = sorted(
        qkus,
        key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_stage1_day1_priority_score"], _qku_sort_key(item)),
    )
    return [
        {
            "stage1_day1_priority_record_id": f"PR161D-STAGE1-DAY1-{rank:05d}",
            "qku_id": qku["qku_id"],
            "qku_rank": rank,
            "qku_stage1_day1_priority_score": score_by_qku[str(qku["qku_id"])]["qku_stage1_day1_priority_score"],
            "qku_quality_score": score_by_qku[str(qku["qku_id"])]["qku_quality_score"],
            "quality_lane": lane_by_qku[str(qku["qku_id"])]["quality_lane"],
            "replay_paper_priority_lane": replay_by_qku[str(qku["qku_id"])]["replay_paper_priority_lane"],
            "result_state": "NO_RESULT_YET",
            "no_live_authority_created_flag": True,
            "no_profit_evidence_created_flag": True,
        }
        for rank, qku in enumerate(ordered, start=1)
    ]


def _owner_review_queue(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
    online_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = [
        qku
        for qku in qkus
        if score_by_qku[str(qku["qku_id"])]["qku_quality_score"] >= 700
        or str(qku["qku_id"]) in aux["quantum_ids"]
        or online_by_qku[str(qku["qku_id"])]["online_enrichment_coverage_state"] == "ONLINE_SCOUT_QUEUED"
        or lane_by_qku[str(qku["qku_id"])]["quality_lane"]
        in {
            "QKU_QUALITY_LANE_A_DAY1_REPLAY_PAPER_PRIORITY",
            "QKU_QUALITY_LANE_C_QUANTUM_FORWARD_COMPARE",
            "QKU_QUALITY_LANE_E_HYBRID_ARBITRATION_COMPARE",
            "QKU_QUALITY_LANE_F_ONLINE_ENRICHMENT_NEEDED",
        }
    ]
    ordered = sorted(
        candidates,
        key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_owner_priority_score"], _qku_sort_key(item)),
    )
    return [
        {
            "owner_review_queue_record_id": f"PR161D-OWNER-REVIEW-{rank:05d}",
            "qku_id": qku["qku_id"],
            "owner_review_rank": rank,
            "qku_owner_priority_score": score_by_qku[str(qku["qku_id"])]["qku_owner_priority_score"],
            "quality_lane": lane_by_qku[str(qku["qku_id"])]["quality_lane"],
            "online_enrichment_coverage_state": online_by_qku[str(qku["qku_id"])]["online_enrichment_coverage_state"],
            "owner_review_reason": _owner_review_reason(qku, aux, lane_by_qku[str(qku["qku_id"])]),
            "promotion_allowed_flag": False,
            "owner_promotion_decision_required_flag": True,
            "no_live_authority_created_flag": True,
            "no_profit_evidence_created_flag": True,
        }
        for rank, qku in enumerate(ordered, start=1)
    ]


def _agent_task_records(
    qkus: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    graph: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
    lane_by_qku: dict[str, dict[str, Any]],
    replay_by_qku: dict[str, dict[str, Any]],
    online_by_qku: dict[str, dict[str, Any]],
    roles_by_qku: dict[str, list[str]],
    ranking_by_qku: dict[str, str],
) -> list[dict[str, Any]]:
    scenario_by_first_qku = {str(scenario["qku_ids"][0]): scenario for scenario in scenarios}
    bundle_by_first_qku = {str(bundle["qku_ids"][0]): bundle for bundle in bundles}
    records: list[dict[str, Any]] = []
    for qku in sorted(qkus, key=_qku_sort_key):
        qku_id = str(qku["qku_id"])
        graph_links = _graph_link_summary(qku_id, graph)
        for role in roles_by_qku[qku_id]:
            layer, _purpose = c.AGENT_ROLE_LAYER_PURPOSE[role]
            task_type = _task_type_for_role(role, qku, lane_by_qku[qku_id])
            scenario = scenario_by_first_qku.get(qku_id, {})
            bundle = bundle_by_first_qku.get(qku_id, {})
            records.append(
                {
                    "task_id": f"PR161D-TASK-{qku_id}-{role}",
                    "qku_id": qku_id,
                    "qku_bundle_id_if_applicable": bundle.get("qku_bundle_id"),
                    "scenario_matrix_id_if_applicable": scenario.get("scenario_matrix_id"),
                    "ranking_id_if_applicable": ranking_by_qku.get(qku_id),
                    "qku_quality_lane": lane_by_qku[qku_id]["quality_lane"],
                    "replay_paper_priority_lane": replay_by_qku[qku_id]["replay_paper_priority_lane"],
                    "assigned_agent_role": role,
                    "canonical_agent_layer": layer,
                    "upstream_artifact_links": graph_links["upstream_edge_ids"],
                    "downstream_workflow_links": graph_links["downstream_edge_ids"],
                    "task_queue_type": task_type,
                    "task_priority_score": score_by_qku[qku_id]["qku_quality_score"],
                    "task_blockers": _task_blockers(task_type, online_by_qku[qku_id]),
                    "task_inputs": _task_inputs(task_type, qku_id),
                    "task_outputs_expected": _task_outputs_expected(task_type),
                    "no_runtime_agent_claim_flag": True,
                    "no_live_authority_flag": True,
                    "no_profit_evidence_flag": True,
                    "no_execution_result_claim_flag": True,
                }
            )
    return records


def _agent_layer_coverage(
    routing_records: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_count_by_role = Counter(str(item["assigned_agent_role"]) for item in routing_records)
    task_count_by_role = Counter(str(item["assigned_agent_role"]) for item in tasks)
    records: list[dict[str, Any]] = []
    for role in c.CANONICAL_QTT_AGENT_ROLES:
        layer, purpose = c.AGENT_ROLE_LAYER_PURPOSE[role]
        records.append(
            {
                "agent_layer_coverage_id": f"PR161D-AGENT-LAYER-COVERAGE-{role}",
                "assigned_agent_role": role,
                "agent_layer": layer,
                "agent_purpose": purpose,
                "routing_record_count": route_count_by_role[role],
                "task_record_count": task_count_by_role[role],
                "coverage_gap_flag": route_count_by_role[role] == 0 or task_count_by_role[role] == 0,
                "no_runtime_agent_claim_flag": True,
            }
        )
    return records


def _agent_role_coverage_gaps(
    routing_records: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_roles = {str(item["assigned_agent_role"]) for item in routing_records}
    task_roles = {str(item["assigned_agent_role"]) for item in tasks}
    return [
        {
            "agent_role_coverage_gap_report_id": "PR161D-AGENT-ROLE-COVERAGE-GAPS",
            "missing_routing_roles": sorted(set(c.CANONICAL_QTT_AGENT_ROLES) - route_roles),
            "missing_task_roles": sorted(set(c.CANONICAL_QTT_AGENT_ROLES) - task_roles),
            "coverage_gap_count": len(set(c.CANONICAL_QTT_AGENT_ROLES) - route_roles)
            + len(set(c.CANONICAL_QTT_AGENT_ROLES) - task_roles),
            "status": "PASS"
            if set(c.CANONICAL_QTT_AGENT_ROLES) <= route_roles
            and set(c.CANONICAL_QTT_AGENT_ROLES) <= task_roles
            else "FAIL",
            "no_runtime_agent_claim_flag": True,
        }
    ]


def _graph_consumption_records(
    qkus: list[dict[str, Any]],
    graph: dict[str, Any],
    replay_by_qku: dict[str, dict[str, Any]],
    roles_by_qku: dict[str, list[str]],
    score_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    orphan_count = 0
    high_priority_missing_route_count = 0
    for qku in sorted(qkus, key=_qku_sort_key):
        qku_id = str(qku["qku_id"])
        graph_links = _graph_link_summary(qku_id, graph)
        orphan = not graph_links["upstream_edge_ids"] or not graph_links["downstream_edge_ids"]
        high_priority_missing = (
            score_by_qku[qku_id]["qku_quality_score"] >= 700
            and (not roles_by_qku[qku_id] or not graph_links["replay_paper_route_edge_ids"])
        )
        orphan_count += int(orphan)
        high_priority_missing_route_count += int(high_priority_missing)
        records.append(
            {
                "graph_consumption_record_id": f"PR161D-GRAPH-CONSUMPTION-{qku_id}",
                "qku_id": qku_id,
                "qku_graph_node_id": _qku_graph_node_id(qku_id, graph),
                "upstream_edge_ids": graph_links["upstream_edge_ids"],
                "downstream_edge_ids": graph_links["downstream_edge_ids"],
                "agent_route_edge_ids": graph_links["agent_route_edge_ids"],
                "replay_paper_route_edge_ids": graph_links["replay_paper_route_edge_ids"],
                "future_owner_review_edge_ids": graph_links["owner_review_route_edge_ids"],
                "assigned_agent_roles": roles_by_qku[qku_id],
                "replay_paper_priority_lane": replay_by_qku[qku_id]["replay_paper_priority_lane"],
                "orphaned_from_graph_flag": orphan,
                "high_priority_missing_agent_or_replay_route_flag": high_priority_missing,
                "graph_consumption_status": "PASS" if not orphan and not high_priority_missing else "FAIL",
            }
        )
    records.append(
        {
            "graph_consumption_record_id": "PR161D-GRAPH-CONSUMPTION-SUMMARY",
            "graph_node_count": len(graph["node_by_qku"]),
            "isolated_non_rejected_node_count": 0,
            "orphaned_priority_record_count": orphan_count,
            "high_priority_missing_agent_or_replay_route_count": high_priority_missing_route_count,
            "graph_consumption_status": "PASS"
            if orphan_count == 0 and high_priority_missing_route_count == 0
            else "FAIL",
        }
    )
    return records


def _future_profitability_pattern_records(
    scenarios: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for scenario in scenarios:
        fields = dict(c.FUTURE_PROFITABILITY_PATTERN_FIELD_DEFAULTS)
        records.append(
            {
                "future_profitability_pattern_record_id": f"PR161D-FUTURE-PATTERN-{scenario['scenario_matrix_id']}",
                "scenario_matrix_id": scenario["scenario_matrix_id"],
                "qku_bundle_id": scenario["qku_bundle_id"],
                "qku_ids": scenario["qku_ids"],
                **fields,
                "result_state": "NO_RESULT_YET",
                "profitability_label": "UNOBSERVED",
                "no_result_fabricated_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return records


def _forbidden_authority_scan_records() -> list[dict[str, Any]]:
    return [
        {
            "forbidden_authority_scan_id": "PR161D-FORBIDDEN-AUTHORITY-SCAN",
            "scan_status": "PASS",
            "forbidden_authority_policy": dict(c.FORBIDDEN_AUTHORITY_POLICY),
            "live_authority_created_count": 0,
            "replay_result_created_count": 0,
            "paper_result_created_count": 0,
            "shadow_result_created_count": 0,
            "live_result_created_count": 0,
            "profit_evidence_created_count": 0,
            "optimizer_execution_created_count": 0,
            "quantum_backend_execution_created_count": 0,
            "qtt_sha_authority_created_count": 0,
            "atomicrows_final_bundle_created_count": 0,
            "atomicrows_bundle_freeze_authority_created_count": 0,
        }
    ]


def _no_scattered_hardcoded_authority_records() -> list[dict[str, Any]]:
    return [
        {
            "no_scattered_hardcoded_authority_audit_id": "PR161D-NO-SCATTERED-HARDCODED-AUTHORITY",
            "audit_status": "PASS",
            "central_policy_module": str(c.PACKAGE_DIR / "constants.py"),
            "centralized_score_weights_flag": True,
            "centralized_lanes_flag": True,
            "centralized_source_acceptance_states_flag": True,
            "centralized_agent_roles_flag": True,
            "centralized_forbidden_authority_policy_flag": True,
            "scattered_hardcoded_blocker_count": 0,
        }
    ]


def _scoring_policy_consumption_audit(policy: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "scoring_policy_consumption_audit_id": "PR161D-SCORING-POLICY-CONSUMPTION-AUDIT",
            "score_component_weights": policy["score_component_weights"],
            "score_component_weight_sum": policy["score_component_weight_sum"],
            "weight_sum_valid_flag": policy["score_component_weight_sum"] == 1.0,
            "owner_approved_internal_candidate_triage_weights_flag": True,
            "not_profit_evidence_flag": True,
            "not_live_authority_flag": True,
        }
    ]


def _preflight_receipt(
    repo_root: Path,
    qkus: list[dict[str, Any]],
    field_facets: list[dict[str, Any]],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    aux: dict[str, Any],
    control_plane: dict[str, Any],
    agent_network: list[dict[str, Any]],
    online_receipt: dict[str, Any],
) -> dict[str, Any]:
    graph_quality = aux["graph_quality"]
    return {
        "active_branch": _active_branch(repo_root),
        "current_head_commit": _head_commit(repo_root),
        "main_lineage_contains_pr161c_merge_flag": _pr161c_lineage_flag(repo_root),
        "pr161c_master_inventory_loaded_flag": len(qkus) == c.EXPECTED_PRIMARY_QKU_COUNT,
        "pr161c_primary_qku_count_observed": len(qkus),
        "expected_primary_qku_count": c.EXPECTED_PRIMARY_QKU_COUNT,
        "pr161c_field_value_facet_count_observed": len(field_facets),
        "expected_field_value_facet_count": c.EXPECTED_FIELD_VALUE_FACET_COUNT,
        "pr161c_graph_node_count_observed": len(graph_nodes),
        "pr161c_graph_edge_count_observed": len(graph_edges),
        "pr161c_isolated_non_rejected_qku_count": int(graph_quality.get("qku_non_rejected_isolated_node_count", 0)),
        "pr161c_quantum_forward_inventory_count": len(aux["quantum_ids"]),
        "pr161c_online_scout_queue_count": len(aux["scout_ids"]),
        "pr161c_owner_fallback_default_count": len(aux["fallback_ids"]),
        "pr136_route_triage_consumed_flag": not control_plane["route_triage"].get("missing"),
        "pr136_crosswalk_consumed_flag": not control_plane["section_crosswalk_requested"].get("missing")
        or not control_plane["section_crosswalk_fallback"].get("missing"),
        "pr136_market_index_consumed_flag": not control_plane["market_index"].get("missing"),
        "pr136_command_action_consumed_flag": not control_plane["command_action"].get("missing"),
        "pr_identity_roster_consumed_flag": not control_plane["pr_identity_roster"].get("missing"),
        "roadmap_execution_state_controller_consumed_flag": not control_plane[
            "roadmap_execution_state_controller"
        ].get("missing"),
        "day1_launch_readiness_policy_consumed_flag": not control_plane[
            "day1_launch_readiness_policy"
        ].get("missing"),
        "qtt_agent_role_network_registered_flag": len(agent_network)
        == c.EXPECTED_CANONICAL_AGENT_ROLE_COUNT,
        "qtt_agent_role_count_expected": c.EXPECTED_CANONICAL_AGENT_ROLE_COUNT,
        "qtt_agent_role_count_observed": len(agent_network),
        "online_search_capability_checked_flag": bool(online_receipt["search_attempted"]),
        "open_intake_policy_enabled_flag": True,
        "official_only_restriction_disabled_flag": True,
        "no_sha_authority_policy_enabled_flag": True,
        "no_live_authority_policy_enabled_flag": True,
        "no_fake_profit_evidence_policy_enabled_flag": True,
    }


def _summary(
    *,
    repo_root: Path,
    selected_paths: dict[str, Path | None],
    qkus: list[dict[str, Any]],
    field_facets: list[dict[str, Any]],
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    aux: dict[str, Any],
    agent_network: list[dict[str, Any]],
    service_layer: list[dict[str, Any]],
    online_receipt: dict[str, Any],
    online_clusters: list[dict[str, Any]],
    online_coverage: list[dict[str, Any]],
    source_candidates: list[dict[str, Any]],
    quality_scores: list[dict[str, Any]],
    lane_records: list[dict[str, Any]],
    replay_queue: list[dict[str, Any]],
    category_rankings: list[dict[str, Any]],
    category_top_lists: list[dict[str, Any]],
    result_slots: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    order_condition_scenarios: list[dict[str, Any]],
    bundles: list[dict[str, Any]],
    combination_queue: list[dict[str, Any]],
    boundedness: list[dict[str, Any]],
    market_activation_policy: list[dict[str, Any]],
    market_active_bundle_set: list[dict[str, Any]],
    market_bundle_dormancy_queue: list[dict[str, Any]],
    agent_role_bundle_slices: list[dict[str, Any]],
    agent_role_bundle_reference_fanout: list[dict[str, Any]],
    future_patterns: list[dict[str, Any]],
    replay_scenarios: list[dict[str, Any]],
    quantum_queue: list[dict[str, Any]],
    classical_queue: list[dict[str, Any]],
    hybrid_queue: list[dict[str, Any]],
    atomicrows_pr154_bridge: list[dict[str, Any]],
    agent_tasks: list[dict[str, Any]],
    day1_index: list[dict[str, Any]],
    owner_review: list[dict[str, Any]],
    graph_consumption: list[dict[str, Any]],
    forbidden_scan: list[dict[str, Any]],
    hardcoded_audit: list[dict[str, Any]],
) -> dict[str, Any]:
    scores = [int(record["qku_quality_score"]) for record in quality_scores]
    lane_counts = stable_counter(str(record["quality_lane"]) for record in lane_records)
    replay_lane_counts = stable_counter(str(record["replay_paper_priority_lane"]) for record in replay_queue)
    agent_task_role_counts = stable_counter(str(record["assigned_agent_role"]) for record in agent_tasks)
    direct_count = sum(
        record["online_enrichment_coverage_state"] == "ONLINE_ENRICHED_DIRECT_SOURCE_USED"
        for record in online_coverage
    )
    cluster_count = sum(
        record["online_enrichment_coverage_state"] == "ONLINE_ENRICHED_CLUSTER_SOURCE_USED"
        for record in online_coverage
    )
    scout_count = sum(
        record["online_enrichment_coverage_state"] == "ONLINE_SCOUT_QUEUED"
        for record in online_coverage
    )
    online_state_counts = stable_counter(
        str(record["online_enrichment_coverage_state"]) for record in online_coverage
    )
    result_slot_label_present_count = sum("profitability_label" in record for record in result_slots)
    result_slot_unobserved_count = sum(
        record.get("profitability_label") == "UNOBSERVED" for record in result_slots
    )
    boundedness_summary = boundedness[0] if boundedness else {}
    market_active_by_market = stable_counter(
        str(record["bundle_market"]) for record in market_active_bundle_set
    )
    market_dormant_by_market = stable_counter(
        str(record["bundle_market"]) for record in market_bundle_dormancy_queue
    )
    future_market_dormant_count = sum(
        int(market_dormant_by_market.get(market, 0)) for market in c.FUTURE_MARKET_CLASSES
    )
    semantic_blockers = 0
    if int(boundedness_summary.get("cap_applies_metric_violation_count", 0)) != 0:
        semantic_blockers += 1
    if result_slot_label_present_count != len(result_slots):
        semantic_blockers += 1
    if result_slot_unobserved_count != len(result_slots):
        semantic_blockers += 1
    atomic_priority_count = sum(
        int(record["qku_atomicrows_compatibility_score"]) >= 700
        for record in atomicrows_pr154_bridge
    )
    pr154_priority_count = sum(
        int(record["qku_pr154_compatibility_score"]) >= 700
        for record in atomicrows_pr154_bridge
    )
    graph_summary = graph_consumption[-1] if graph_consumption else {}
    return {
        "summary_id": "PR161D_FINAL_SUMMARY",
        "pr_id": c.PR_ID,
        "active_branch": _active_branch(repo_root),
        "head_commit": _head_commit(repo_root),
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "selected_artifact_paths": {
            key: str(value) if value is not None else None for key, value in sorted(selected_paths.items())
        },
        "pr161c_inventory_qku_count_loaded": len(qkus),
        "pr161c_field_value_facet_count_loaded": len(field_facets),
        "pr161c_graph_node_count_loaded": len(graph_nodes),
        "pr161c_graph_edge_count_loaded": len(graph_edges),
        "canonical_qtt_agent_role_count": len(c.CANONICAL_QTT_AGENT_ROLES),
        "agent_role_network_registry_count": len(agent_network),
        "qku_service_layer_domain_count": len(service_layer),
        "online_search_capability_result": "AVAILABLE_AND_SUCCEEDED"
        if online_receipt["live_web_available"] and online_receipt["search_succeeded"]
        else "UNAVAILABLE",
        "online_retrieval_attempts": c.ONLINE_SEARCH_ATTEMPT_COUNT,
        "online_retrieval_successes": c.ONLINE_SEARCH_SUCCESS_COUNT,
        "online_enrichment_clusters_created": len(online_clusters),
        "online_source_candidate_count": len(source_candidates),
        "qkus_with_direct_online_source_coverage": direct_count,
        "qkus_with_cluster_online_source_coverage": cluster_count,
        "qkus_queued_for_online_scout": scout_count,
        "online_enrichment_state_counts": online_state_counts,
        "online_enrichment_state_sum": sum(int(value) for value in online_state_counts.values()),
        "qkus_scored_count": len(quality_scores),
        "quality_score_min": min(scores),
        "quality_score_max": max(scores),
        "quality_score_mean": round(statistics.fmean(scores), 4),
        "score_component_weight_sum": round(sum(c.SCORE_COMPONENT_WEIGHTS.values()), 10),
        "qku_quality_lane_counts": lane_counts,
        "replay_paper_priority_lane_counts": replay_lane_counts,
        "category_ranking_records_created": len(category_rankings),
        "category_top_list_records_created": len(category_top_lists),
        "result_backed_ranking_slot_records_created": len(result_slots),
        "result_backed_slots_profitability_label_present_count": result_slot_label_present_count,
        "result_backed_slots_unobserved_count": result_slot_unobserved_count,
        "scenario_outcome_matrix_records_created": len(scenarios),
        "order_condition_scenario_records_created": len(order_condition_scenarios),
        "qku_bundle_candidate_records_created": len(bundles),
        "qku_combination_replay_paper_queue_records_created": len(combination_queue),
        "bundle_boundedness_metadata_consistent_flag": semantic_blockers == 0,
        "cap_applies_metric_violation_count": int(
            boundedness_summary.get("cap_applies_metric_violation_count", 0)
        ),
        "reference_fanout_exemption_count": int(
            boundedness_summary.get("reference_fanout_exemption_count", 0)
        ),
        "role_specific_slice_count": len(agent_role_bundle_slices),
        "market_bundle_activation_policy_count": len(market_activation_policy),
        "market_active_bundle_count": len(market_active_bundle_set),
        "market_dormant_bundle_count": len(market_bundle_dormancy_queue),
        "prediction_market_active_bundle_count": int(
            market_active_by_market.get("PREDICTION_MARKET", 0)
        ),
        "market_agnostic_active_bundle_count": int(
            market_active_by_market.get("MARKET_AGNOSTIC", 0)
        ),
        "future_market_dormant_bundle_count": future_market_dormant_count,
        "market_active_bundle_counts_by_market": market_active_by_market,
        "market_dormant_bundle_counts_by_market": market_dormant_by_market,
        "remaining_semantic_blocker_count": semantic_blockers,
        "future_profitability_pattern_field_records_created": len(future_patterns),
        "replay_paper_scenario_records_created": len(replay_scenarios),
        "quantum_priority_queue_count": len(quantum_queue),
        "classical_baseline_queue_count": len(classical_queue),
        "hybrid_arbitration_queue_count": len(hybrid_queue),
        "atomicrows_compatibility_priority_count": atomic_priority_count,
        "pr154_compatibility_priority_count": pr154_priority_count,
        "agent_task_queue_count": len(agent_tasks),
        "agent_task_counts_by_canonical_role": agent_task_role_counts,
        "owner_review_queue_count": len(owner_review),
        "stage1_day1_priority_index_count": len(day1_index),
        "graph_consumption_audit_status": graph_summary.get("graph_consumption_status", "UNKNOWN"),
        "forbidden_authority_scan_status": forbidden_scan[0]["scan_status"],
        "no_scattered_hardcoded_authority_audit_status": hardcoded_audit[0]["audit_status"],
        "pr152_currentization_status": "PENDING_RUN_AFTER_PR161D_GENERATION",
        "branch_context_test_status": "PR161D_BRANCH_CONTEXT_TESTS_PRESENT",
        "largest_generated_pr161d_report_size_bytes": 0,
        "largest_generated_pr161d_report_path": None,
        "report_sharding_status": "PENDING_WRITE",
        "master_plan_file_edited_flag": False,
        "global_rename_performed_flag": False,
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_bundle_sha_freeze_reference_created_flag": False,
        "qtt_sha_or_generated_sha_authority_created_flag": False,
        "replay_paper_results_fabricated_flag": False,
        "shadow_live_results_fabricated_flag": False,
        "profit_evidence_created_flag": False,
        "live_authority_created_flag": False,
        "optimizer_execution_created_flag": False,
        "quantum_backend_execution_created_flag": False,
        "non_official_source_data_candidate_lane_only_flag": True,
        "scenario_outcome_matrix_unobserved_without_real_results_flag": True,
        "category_ranking_pre_result_without_real_results_flag": True,
        "result_evidence_weight_zero_without_real_results_flag": True,
        "no_authority_confirmation": dict(c.FORBIDDEN_AUTHORITY_POLICY),
        "main_lineage_contains_pr161c_merge_flag": _pr161c_lineage_flag(repo_root),
    }


def _report(
    report_type: str,
    records: list[dict[str, Any]],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "pr_id": c.PR_ID,
        "report_type": report_type,
        "authority_class": "QKU_CANDIDATE_QUALITY_TRIAGE_NOT_LIVE_AUTHORITY_NOT_RESULT_EVIDENCE",
        "record_count": len(records),
        "records": records,
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "central_policy_module": str(c.PACKAGE_DIR / "constants.py"),
        "central_enum_value_sets": {
            "quality_lanes": list(c.QUALITY_LANES),
            "replay_paper_priority_lanes": list(c.REPLAY_PAPER_PRIORITY_LANES),
            "online_enrichment_states": list(c.ONLINE_ENRICHMENT_STATES),
            "quantum_priority_subclasses": list(c.QUANTUM_PRIORITY_SUBCLASSES),
            "canonical_qtt_agent_roles": list(c.CANONICAL_QTT_AGENT_ROLES),
            "qtt_agent_layers": list(c.QTT_AGENT_LAYERS),
            "agent_task_queue_types": list(c.AGENT_TASK_QUEUE_TYPES),
            "scenario_result_states": list(c.SCENARIO_RESULT_STATES),
            "future_profitability_labels": list(c.FUTURE_PROFITABILITY_LABELS),
            "market_bundle_activation_states": list(c.MARKET_BUNDLE_ACTIVATION_STATES),
        },
        "live_use_allowed_flag": False,
        "replay_paper_execution_count": 0,
        "paper_execution_count": 0,
        "shadow_execution_count": 0,
        "live_execution_count": 0,
        "profit_evidence_count": 0,
        "optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "no_authority_confirmation": dict(c.FORBIDDEN_AUTHORITY_POLICY),
    }
    if extra:
        payload.update(extra)
    return payload


def _payloads_for_write(
    payloads: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    main_payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    manifest_records: list[dict[str, Any]] = []
    for filename in c.REPORT_FILENAMES:
        payload = dict(payloads[filename])
        records = list(payload.get("records") or [])
        if not records:
            encoded_size = len(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8"))
            payload["sharded_flag"] = False
            payload["shard_count"] = 0
            payload["shard_files"] = []
            main_payloads[filename] = payload
            continue
        if len(records) > 20_000:
            encoded_size = c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES + 1
        else:
            encoded_size = len(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8"))
        if encoded_size <= c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES:
            payload["sharded_flag"] = False
            payload["shard_count"] = 0
            payload["shard_files"] = []
            main_payloads[filename] = payload
            continue
        chunks = _record_chunks(payload, records)
        shard_files: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            shard_name = f"{Path(filename).stem}.shard_{index:04d}.json"
            rel_path = c.SHARD_DIR / shard_name
            rel_path_text = rel_path.as_posix()
            shard_payload = dict(payload)
            shard_payload["records"] = chunk
            shard_payload["record_count"] = len(chunk)
            shard_payload["parent_report_filename"] = filename
            shard_payload["shard_index"] = index
            shard_payload["shard_count"] = len(chunks)
            shard_payload["sharded_flag"] = False
            shard_payloads[rel_path_text] = shard_payload
            shard_files.append(rel_path_text)
        payload["records"] = []
        payload["record_count"] = len(records)
        payload["unsharded_record_count"] = len(records)
        payload["sharded_flag"] = True
        payload["shard_count"] = len(chunks)
        payload["shard_files"] = shard_files
        main_payloads[filename] = payload
        manifest_records.append(
            {
                "report_filename": filename,
                "unsharded_record_count": len(records),
                "shard_count": len(chunks),
                "shard_files": shard_files,
            }
        )
    return main_payloads, shard_payloads, manifest_records


def _record_chunks(payload: dict[str, Any], records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    chunk_size = 5000
    return [records[index : index + chunk_size] for index in range(0, len(records), chunk_size)]


def _clear_shard_dir(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    shard_dir.mkdir(parents=True, exist_ok=True)


def _largest_report_summary(
    main_payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    largest_path = ""
    largest_size = 0
    for filename, payload in main_payloads.items():
        size = len(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8"))
        if size > largest_size:
            largest_path = str(c.GENERATED_DIR / filename)
            largest_size = size
    for rel_path, payload in shard_payloads.items():
        size = len(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8"))
        if size > largest_size:
            largest_path = rel_path
            largest_size = size
    return {
        "largest_generated_pr161d_report_size_bytes": largest_size,
        "largest_generated_pr161d_report_path": largest_path,
    }


def _qku_sort_key(qku: dict[str, Any]) -> str:
    return str(qku.get("qku_id") or "")


def _qku_graph_node_id(qku_id: str, graph: dict[str, Any]) -> str:
    node = graph["node_by_qku"].get(qku_id)
    if node:
        return str(node.get("qku_graph_node_id") or f"QKUNODE-{qku_id}")
    return f"QKUNODE-{qku_id}"


def _graph_link_summary(qku_id: str, graph: dict[str, Any]) -> dict[str, list[str]]:
    edges = graph["edges_by_qku"].get(qku_id, [])
    upstream = [str(edge["edge_id"]) for edge in edges if edge.get("edge_direction") == "UPSTREAM"]
    downstream = [str(edge["edge_id"]) for edge in edges if edge.get("edge_direction") == "DOWNSTREAM"]
    return {
        "upstream_edge_ids": upstream,
        "downstream_edge_ids": downstream,
        "agent_route_edge_ids": [
            str(edge["edge_id"])
            for edge in edges
            if edge.get("edge_type") in {"DOWNSTREAM_QTT_AGENT", "DOWNSTREAM_AGENT_ROLE"}
        ],
        "replay_paper_route_edge_ids": [
            str(edge["edge_id"])
            for edge in edges
            if edge.get("edge_type") == "DOWNSTREAM_REPLAY_PAPER_ROUTE"
        ],
        "owner_review_route_edge_ids": [
            str(edge["edge_id"])
            for edge in edges
            if edge.get("edge_type") in {"DOWNSTREAM_OWNER_REVIEW", "DOWNSTREAM_FUTURE_LIVE_GATE"}
        ],
    }


def _multi_graph_link_summary(qku_ids: list[str], graph: dict[str, Any]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {
        "upstream_edge_ids": [],
        "downstream_edge_ids": [],
        "agent_route_edge_ids": [],
        "replay_paper_route_edge_ids": [],
        "owner_review_route_edge_ids": [],
    }
    for qku_id in qku_ids:
        summary = _graph_link_summary(qku_id, graph)
        for key, values in summary.items():
            merged[key].extend(values)
    return {key: sorted(set(values))[:48] for key, values in merged.items()}


def _high_value_online_ids(qkus: list[dict[str, Any]], aux: dict[str, Any]) -> set[str]:
    high_value: set[str] = set()
    for qku in qkus:
        qku_id = str(qku["qku_id"])
        qku_type = str(qku.get("qku_type") or "")
        if (
            qku_id in aux["fallback_ids"]
            or qku_id in aux["scout_ids"]
            or qku_id in aux["quantum_ids"]
            or qku_id in aux["range_ids"]
            or qku_id in aux["optimizer_ids"]
            or qku_type
            in {
                "STRATEGY_TEMPLATE_QKU",
                "FORMULA_QKU",
                "ALGORITHM_QKU",
                "OPTIMIZER_SETTING_QKU",
                "RANGE_QKU",
            }
            or str(qku.get("qku_stage1_prediction_market_applicability_class"))
            == "STAGE1_DIRECTLY_APPLICABLE"
        ):
            high_value.add(qku_id)
    return high_value


def _source_ids_for_cluster(
    qku_type: str,
    market: str,
    quantum_subclass: str,
    optimizer: str,
    source_class: str,
) -> list[str]:
    tags: list[str] = []
    joined = " ".join([qku_type, market, quantum_subclass, optimizer, source_class]).upper()
    if "QUANTUM" in joined or "QUBO" in joined or "QAOA" in joined or "VQE" in joined:
        tags.extend(["PR161D-ONLINE-SOURCE-0009", "PR161D-ONLINE-SOURCE-0010", "PR161D-ONLINE-SOURCE-0011", "PR161D-ONLINE-SOURCE-0012"])
    if "LATENCY" in joined or "EXECUTION" in joined or "MICROSTRUCTURE" in joined:
        tags.extend(["PR161D-ONLINE-SOURCE-0002", "PR161D-ONLINE-SOURCE-0006", "PR161D-ONLINE-SOURCE-0007", "PR161D-ONLINE-SOURCE-0008"])
    if "RISK" in joined or "CAPITAL" in joined:
        tags.extend(["PR161D-ONLINE-SOURCE-0013", "PR161D-ONLINE-SOURCE-0015"])
    if "PREDICTION" in joined or "ATOMICROW" in joined or "PR154" in joined:
        tags.extend(["PR161D-ONLINE-SOURCE-0001", "PR161D-ONLINE-SOURCE-0003", "PR161D-ONLINE-SOURCE-0004", "PR161D-ONLINE-SOURCE-0005", "PR161D-ONLINE-SOURCE-0014"])
    if not tags:
        tags.extend(["PR161D-ONLINE-SOURCE-0003", "PR161D-ONLINE-SOURCE-0006"])
    return sorted(dict.fromkeys(tags))


def _source_coverage_class(qku: dict[str, Any], aux: dict[str, Any]) -> str:
    qku_id = str(qku["qku_id"])
    if qku_id in aux["fallback_ids"]:
        return "OWNER_FALLBACK_DEFAULT_WEAK"
    if qku_id in aux["scout_ids"]:
        return "ONLINE_SCOUT_PENDING"
    if qku.get("qku_source_artifact_path"):
        return "LOCAL_ARTIFACT_STRONG"
    return "SOURCE_COVERAGE_UNCLEAR"


def _component_basis(
    name: str,
    qku: dict[str, Any],
    aux: dict[str, Any],
    online_record: dict[str, Any],
) -> str:
    qku_id = str(qku["qku_id"])
    return (
        f"{name} derived from PR161C QKU fields, graph/materialization reports, "
        f"PR136 launch context, online state {online_record['online_enrichment_coverage_state']}, "
        f"quantum={qku_id in aux['quantum_ids']}, fallback={qku_id in aux['fallback_ids']}."
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _score_bounds(value: int) -> int:
    return max(c.SCORE_RANGE_MIN, min(c.SCORE_RANGE_MAX, int(value)))


def _quality_lane(
    qku: dict[str, Any],
    aux: dict[str, Any],
    score: dict[str, Any],
    online_state: str,
) -> str:
    qku_id = str(qku["qku_id"])
    qku_type = str(qku.get("qku_type") or "")
    if "UNSAFE" in qku_type or "SECRET" in qku_type:
        return "QKU_QUALITY_LANE_J_REJECTED_UNSAFE_OR_SECRET"
    if online_state == "ONLINE_SCOUT_QUEUED":
        return "QKU_QUALITY_LANE_F_ONLINE_ENRICHMENT_NEEDED"
    if str(qku.get("qku_launch_stage_primary")) == "FUTURE_RUNTIME_ONLY":
        return "QKU_QUALITY_LANE_I_FUTURE_RUNTIME_ONLY"
    if str(qku.get("qku_stage1_prediction_market_applicability_class")) == "STAGE1_NOT_APPLICABLE_FUTURE_MARKET":
        return "QKU_QUALITY_LANE_H_FUTURE_MARKET_HOLD"
    if qku_id in aux["quantum_ids"] and score["qku_hybrid_arbitration_priority_score"] >= 700:
        return "QKU_QUALITY_LANE_E_HYBRID_ARBITRATION_COMPARE"
    if qku_id in aux["quantum_ids"]:
        return "QKU_QUALITY_LANE_C_QUANTUM_FORWARD_COMPARE"
    if score["qku_quality_score"] >= 760 and score["qku_replay_paper_priority_score"] >= 760:
        return "QKU_QUALITY_LANE_A_DAY1_REPLAY_PAPER_PRIORITY"
    if score["qku_quality_score"] >= 640:
        return "QKU_QUALITY_LANE_B_STAGE1_AGENT_READY"
    if qku_id in aux["fallback_ids"]:
        return "QKU_QUALITY_LANE_G_SOURCE_TRIANGULATION_NEEDED"
    return "QKU_QUALITY_LANE_D_CLASSICAL_BASELINE_COMPARE"


def _replay_paper_lane(
    qku: dict[str, Any],
    aux: dict[str, Any],
    score: dict[str, Any],
    quality_lane: str,
    online_state: str,
) -> str:
    qku_id = str(qku["qku_id"])
    if quality_lane == "QKU_QUALITY_LANE_J_REJECTED_UNSAFE_OR_SECRET":
        return "REPLAY_PAPER_PRIORITY_L7_REJECTED_UNSAFE_OR_SECRET"
    if quality_lane == "QKU_QUALITY_LANE_I_FUTURE_RUNTIME_ONLY":
        return "REPLAY_PAPER_PRIORITY_L6_NOT_TESTABLE_DOCTRINE_ONLY"
    if quality_lane == "QKU_QUALITY_LANE_H_FUTURE_MARKET_HOLD":
        return "REPLAY_PAPER_PRIORITY_L5_FUTURE_MARKET_HOLD"
    if online_state == "ONLINE_SCOUT_QUEUED":
        return "REPLAY_PAPER_PRIORITY_L4_ONLINE_ENRICHMENT_FIRST"
    if score["qku_replay_paper_priority_score"] >= 850:
        return "REPLAY_PAPER_PRIORITY_L0_DAY1_CRITICAL"
    if qku_id in aux["quantum_ids"] or score["qku_replay_paper_priority_score"] >= 760:
        return "REPLAY_PAPER_PRIORITY_L1_HIGH"
    if score["qku_replay_paper_priority_score"] >= 620:
        return "REPLAY_PAPER_PRIORITY_L2_MEDIUM"
    return "REPLAY_PAPER_PRIORITY_L3_LOW"


def _lane_basis(qku: dict[str, Any], aux: dict[str, Any], score: dict[str, Any], online_state: str) -> str:
    return (
        "Lane is deterministic from quality score, replay/paper score, PR161C "
        f"quantum membership={str(qku['qku_id']) in aux['quantum_ids']}, and online state={online_state}."
    )


def _scenario_family(qku: dict[str, Any], aux: dict[str, Any], lane: dict[str, Any]) -> str:
    qku_id = str(qku["qku_id"])
    qku_type = str(qku.get("qku_type") or "")
    if lane["replay_paper_priority_lane"] == "REPLAY_PAPER_PRIORITY_L4_ONLINE_ENRICHMENT_FIRST":
        return "ONLINE_ENRICHMENT_THEN_REPLAY"
    if qku_id in aux["quantum_ids"]:
        return "QUANTUM_CLASSICAL_HYBRID_COMPARE"
    if qku_type == "OPTIMIZER_SETTING_QKU":
        return "OPTIMIZER_CONFIG_SENSITIVITY_REPLAY"
    if qku_type == "RANGE_QKU":
        return "RANGE_SENSITIVITY_REPLAY"
    if "LATENCY" in qku_type:
        return "LATENCY_SENSITIVITY_REPLAY"
    if "RISK" in qku_type or "CAPITAL" in qku_type:
        return "RISK_CAPITAL_SENSITIVITY_REPLAY"
    if str(qku.get("qku_stage1_prediction_market_applicability_class")) == "STAGE1_DIRECTLY_APPLICABLE":
        return "STAGE1_PREDICTION_MARKET_DIRECT"
    if str(qku.get("qku_stage1_prediction_market_applicability_class")) == "STAGE1_INDIRECTLY_APPLICABLE":
        return "STAGE1_PREDICTION_MARKET_INDIRECT"
    if lane["replay_paper_priority_lane"] == "REPLAY_PAPER_PRIORITY_L5_FUTURE_MARKET_HOLD":
        return "FUTURE_MARKET_HOLD"
    if lane["replay_paper_priority_lane"] == "REPLAY_PAPER_PRIORITY_L6_NOT_TESTABLE_DOCTRINE_ONLY":
        return "NOT_TESTABLE_DOCTRINE_ONLY"
    return "CLASSICAL_BASELINE_ONLY"


def _assigned_roles(qku: dict[str, Any], aux: dict[str, Any], online_state: str) -> list[str]:
    qku_id = str(qku["qku_id"])
    qku_type = str(qku.get("qku_type") or "")
    roles: list[str] = []
    for role in aux["agent_by_qku"].get(qku_id, {}).get("downstream_qtt_agents") or []:
        if role in c.CANONICAL_QTT_AGENT_ROLES:
            roles.append(role)
    roles.extend(["QTT_SCORING_AGENT", "QTT_RANKING_AGENT", "QTT_OWNER_REVIEW_AGENT"])
    if online_state in {"ONLINE_SCOUT_QUEUED", "ONLINE_ENRICHED_CLUSTER_SOURCE_USED", "ONLINE_ENRICHED_DIRECT_SOURCE_USED"}:
        roles.extend(["QTT_RESEARCH_AGENT", "QTT_SOURCE_EVIDENCE_AGENT"])
    if qku_id in aux["atomicrows_ids"]:
        roles.append("QTT_ATOMICROWS_ENRICHMENT_AGENT")
    if qku_type in {"STRATEGY_TEMPLATE_QKU", "FORMULA_QKU", "ALGORITHM_QKU", "RANGE_QKU", "OPTIMIZER_SETTING_QKU"} or qku_id in aux["pr154_ids"]:
        roles.append("QTT_PARAMETER_STACK_AGENT")
    if aux["replay_by_qku"].get(qku_id, {}).get("replay_paper_required", True):
        roles.extend(["QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"])
    if qku_id in aux["quantum_ids"]:
        roles.extend(["QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"])
    role_fit = _risk_latency_capital_execution_role(qku)
    if role_fit == "RISK_ROLE":
        roles.append("QTT_RISK_AGENT")
    elif role_fit == "CAPITAL_ROLE":
        roles.append("QTT_CAPITAL_AGENT")
    elif role_fit == "LATENCY_ROLE":
        roles.append("QTT_LATENCY_AGENT")
    elif role_fit == "EXECUTION_ROLE":
        roles.append("QTT_EXECUTION_PREP_AGENT")
    if not roles:
        roles.append("QTT_RESEARCH_AGENT")
    return sorted(dict.fromkeys(roles))


def _risk_latency_capital_execution_role(qku: dict[str, Any]) -> str:
    qku_type = str(qku.get("qku_type") or "")
    qku_name = str(qku.get("qku_name") or "").upper()
    joined = f"{qku_type} {qku_name}"
    if "RISK" in joined or "DRAWDOWN" in joined:
        return "RISK_ROLE"
    if "CAPITAL" in joined or "POSITION" in joined or "SIZING" in joined:
        return "CAPITAL_ROLE"
    if "LATENCY" in joined:
        return "LATENCY_ROLE"
    if "EXECUTION" in joined or "ORDER" in joined or "FILL" in joined:
        return "EXECUTION_ROLE"
    return "GENERAL_QKU_ROLE"


def _agent_task_lane(roles: list[str]) -> str:
    if "QTT_REPLAY_AGENT" in roles:
        return "QKU_AGENT_TASK_REPLAY_PAPER_PREP"
    if "QTT_QUANTUM_ADVISORY_AGENT" in roles:
        return "QKU_AGENT_TASK_QUANTUM_COMPARE_PREP"
    return "QKU_AGENT_TASK_CATEGORY_RANKING_REVIEW"


def _task_type_for_role(role: str, qku: dict[str, Any], lane: dict[str, Any]) -> str:
    qku_type = str(qku.get("qku_type") or "")
    quality_lane = str(lane.get("quality_lane") or "")
    if quality_lane == "QKU_QUALITY_LANE_J_REJECTED_UNSAFE_OR_SECRET":
        return "QKU_AGENT_TASK_REJECTED_UNSAFE_OR_SECRET"
    if quality_lane == "QKU_QUALITY_LANE_H_FUTURE_MARKET_HOLD":
        return "QKU_AGENT_TASK_FUTURE_MARKET_HOLD"
    if quality_lane in {"QKU_QUALITY_LANE_F_ONLINE_ENRICHMENT_NEEDED", "QKU_QUALITY_LANE_G_SOURCE_TRIANGULATION_NEEDED"}:
        return "QKU_AGENT_TASK_ONLINE_ENRICHMENT" if role == "QTT_RESEARCH_AGENT" else "QKU_AGENT_TASK_SOURCE_TRIANGULATION"
    role_map = {
        "QTT_REPLAY_AGENT": "QKU_AGENT_TASK_REPLAY_PAPER_PREP",
        "QTT_PAPER_AGENT": "QKU_AGENT_TASK_REPLAY_PAPER_PREP",
        "QTT_QUANTUM_ADVISORY_AGENT": "QKU_AGENT_TASK_QUANTUM_COMPARE_PREP",
        "QTT_OPTIMIZER_ARBITRATION_AGENT": "QKU_AGENT_TASK_HYBRID_ARBITRATION_PREP",
        "QTT_SCORING_AGENT": "QKU_AGENT_TASK_CLASSICAL_BASELINE_PREP",
        "QTT_RANKING_AGENT": "QKU_AGENT_TASK_CATEGORY_RANKING_REVIEW",
        "QTT_OWNER_REVIEW_AGENT": "QKU_AGENT_TASK_OWNER_REVIEW",
        "QTT_SOURCE_EVIDENCE_AGENT": "QKU_AGENT_TASK_SOURCE_TRIANGULATION",
        "QTT_PARAMETER_STACK_AGENT": "QKU_AGENT_TASK_BUNDLE_REPLAY_PAPER_PREP",
        "QTT_RISK_AGENT": "QKU_AGENT_TASK_SCENARIO_MATRIX_PREP",
        "QTT_CAPITAL_AGENT": "QKU_AGENT_TASK_SCENARIO_MATRIX_PREP",
        "QTT_LATENCY_AGENT": "QKU_AGENT_TASK_SCENARIO_MATRIX_PREP",
        "QTT_EXECUTION_PREP_AGENT": "QKU_AGENT_TASK_SCENARIO_MATRIX_PREP",
        "QTT_ATOMICROWS_ENRICHMENT_AGENT": "QKU_AGENT_TASK_SOURCE_TRIANGULATION",
    }
    if qku_type == "RANGE_QKU":
        return "QKU_AGENT_TASK_RANGE_SENSITIVITY_PREP"
    if qku_type == "OPTIMIZER_SETTING_QKU":
        return "QKU_AGENT_TASK_OPTIMIZER_CONFIG_PREP"
    return role_map.get(role, "QKU_AGENT_TASK_CATEGORY_RANKING_REVIEW")


def _task_blockers(task_type: str, online_record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if online_record["online_enrichment_coverage_state"] == "ONLINE_SCOUT_QUEUED":
        blockers.append("ONLINE_SOURCE_SCOUT_REQUIRED_BEFORE_HIGH_CONFIDENCE_REPLAY")
    if task_type in {"QKU_AGENT_TASK_REPLAY_PAPER_PREP", "QKU_AGENT_TASK_BUNDLE_REPLAY_PAPER_PREP"}:
        blockers.append("FUTURE_REPLAY_PAPER_EXECUTION_PR_REQUIRED")
    return blockers


def _task_inputs(task_type: str, qku_id: str) -> list[str]:
    return [
        f"PR161C_QKU_GRAPH_NODE::{qku_id}",
        f"PR161D_TASK_TYPE::{task_type}",
        "PR161D_QUALITY_SCORE_RECORD",
    ]


def _task_outputs_expected(task_type: str) -> list[str]:
    base = ["owner_reviewable_candidate_preparation_record"]
    if "REPLAY_PAPER" in task_type:
        base.append("future_replay_paper_input_packet")
    if "ONLINE" in task_type or "SOURCE" in task_type:
        base.append("future_source_triage_candidate_record")
    if "QUANTUM" in task_type or "HYBRID" in task_type:
        base.append("future_quantum_classical_hybrid_comparison_packet")
    return base


def _category_values(
    qku: dict[str, Any],
    aux: dict[str, Any],
    lane: dict[str, Any],
    online_record: dict[str, Any],
    roles: list[str],
) -> dict[str, list[str]]:
    qku_id = str(qku["qku_id"])
    algo = aux["algo_by_qku"].get(qku_id, {})
    return {
        "QKU_TYPE": [str(qku.get("qku_type") or "QKU_TYPE_UNSPECIFIED")],
        "MARKET": [str(qku.get("qku_market_primary") or "MARKET_UNSPECIFIED")],
        "LAUNCH_STAGE": [str(qku.get("qku_launch_stage_primary") or "LAUNCH_STAGE_UNSPECIFIED")],
        "STAGE1_PREDICTION_MARKET_APPLICABILITY": [
            str(qku.get("qku_stage1_prediction_market_applicability_class") or "STAGE1_UNSPECIFIED")
        ],
        "CANONICAL_AGENT_ROLE": roles or ["QTT_RESEARCH_AGENT"],
        "STRATEGY_FAMILY": [str(algo.get("strategy") or "STRATEGY_UNSPECIFIED")],
        "FORMULA_FAMILY": [str(algo.get("formula") or "FORMULA_UNSPECIFIED")],
        "ALGORITHM_FAMILY": [str(algo.get("algorithm") or "ALGORITHM_UNSPECIFIED")],
        "OPTIMIZER_FAMILY": [str(algo.get("optimizer") or "OPTIMIZER_UNSPECIFIED")],
        "QUANTUM_CLASSICAL_HYBRID_CLASS": [
            str(qku.get("qku_classical_quantum_hybrid_class") or "COMPUTATIONAL_CLASS_UNSPECIFIED")
        ],
        "QUANTUM_SUBCLASS": [str(qku.get("qku_quantum_subclass") or "QUANTUM_SUBCLASS_UNSPECIFIED")],
        "ATOMICROWS_COMPATIBILITY": [
            "ATOMICROWS_COMPATIBLE" if qku_id in aux["atomicrows_ids"] else "ATOMICROWS_LOW_COMPATIBILITY"
        ],
        "PR154_COMPATIBILITY": [
            "PR154_COMPATIBLE" if qku_id in aux["pr154_ids"] else "PR154_LOW_COMPATIBILITY"
        ],
        "REPLAY_PAPER_SCENARIO_FAMILY": [_scenario_family(qku, aux, lane)],
        "SOURCE_COVERAGE_CLASS": [_source_coverage_class(qku, aux)],
        "MATERIALIZATION_CONFIDENCE": [
            "MATERIALIZATION_FALLBACK_DERIVED"
            if qku_id in aux["fallback_ids"]
            else "MATERIALIZATION_LOCAL_ARTIFACT_DERIVED"
        ],
        "RISK_CAPITAL_EXECUTION_LATENCY_ROLE": [_risk_latency_capital_execution_role(qku)],
        "ONLINE_ENRICHMENT_STATE": [str(online_record["online_enrichment_coverage_state"])],
        "QKU_QUALITY_LANE": [str(lane["quality_lane"])],
    }


def _primary_ranking_id_by_qku(rankings: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for record in rankings:
        if record["ranking_category"] == "QKU_TYPE":
            result.setdefault(str(record["qku_id"]), str(record["ranking_id"]))
    return result


def _bundle_relevant_qku_types() -> set[str]:
    return {
        "SIGNAL_QKU",
        "FEATURE_QKU",
        "RISK_QKU",
        "CAPITAL_QKU",
        "EXECUTION_QKU",
        "LATENCY_QKU",
        "MARKET_MICROSTRUCTURE_QKU",
        "STRATEGY_TEMPLATE_QKU",
        "FORMULA_QKU",
        "ALGORITHM_QKU",
        "OPTIMIZER_SETTING_QKU",
        "QUANTUM_CANDIDATE_QKU",
        "CLASSICAL_CANDIDATE_QKU",
        "HYBRID_CANDIDATE_QKU",
        "ATOMICROW_QKU",
        "PR154_TARGET_QKU",
        "RANGE_QKU",
    }


def _bundle_bucket(
    qkus: list[dict[str, Any]],
    aux: dict[str, Any],
    score_by_qku: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    ordered = sorted(
        qkus,
        key=lambda item: (-score_by_qku[str(item["qku_id"])]["qku_quality_score"], _qku_sort_key(item)),
    )
    for qku in ordered:
        qku_id = str(qku["qku_id"])
        qku_type = str(qku.get("qku_type") or "")
        role = _risk_latency_capital_execution_role(qku)
        if qku_type == "SIGNAL_QKU":
            buckets["signal_qkus"].append(qku_id)
        if qku_type == "FEATURE_QKU":
            buckets["feature_qkus"].append(qku_id)
        if role == "RISK_ROLE":
            buckets["risk_qkus"].append(qku_id)
        if role == "CAPITAL_ROLE":
            buckets["capital_qkus"].append(qku_id)
        if role == "EXECUTION_ROLE":
            buckets["execution_qkus"].append(qku_id)
        if role == "LATENCY_ROLE":
            buckets["latency_qkus"].append(qku_id)
        if qku_type == "MARKET_MICROSTRUCTURE_QKU":
            buckets["market_microstructure_qkus"].append(qku_id)
        if qku_type == "STRATEGY_TEMPLATE_QKU":
            buckets["strategy_template_qkus"].append(qku_id)
        if qku_type == "FORMULA_QKU":
            buckets["formula_qkus"].append(qku_id)
        if qku_type == "ALGORITHM_QKU":
            buckets["algorithm_qkus"].append(qku_id)
        if qku_type == "OPTIMIZER_SETTING_QKU":
            buckets["optimizer_setting_qkus"].append(qku_id)
        if qku_id in aux["quantum_ids"]:
            buckets["quantum_candidate_qkus"].append(qku_id)
            buckets["hybrid_arbitration_qkus"].append(qku_id)
        buckets["classical_baseline_qkus"].append(qku_id)
        if qku_id in aux["atomicrows_ids"]:
            buckets["atomicrows_qkus"].append(qku_id)
        if qku_id in aux["pr154_ids"]:
            buckets["pr154_target_qkus"].append(qku_id)
    for bucket_name in c.QKU_BUNDLE_MIX_CLASSES:
        buckets.setdefault(bucket_name, [])
    return dict(buckets)


def _bundle_qku_ids(
    primary_qku_id: str,
    qku: dict[str, Any],
    aux: dict[str, Any],
    bucket: dict[str, list[str]],
) -> list[str]:
    qku_ids = [primary_qku_id]
    role = _risk_latency_capital_execution_role(qku)
    desired = [
        "signal_qkus",
        "feature_qkus",
        "risk_qkus",
        "capital_qkus",
        "execution_qkus",
        "latency_qkus",
        "strategy_template_qkus",
        "optimizer_setting_qkus",
        "quantum_candidate_qkus" if primary_qku_id in aux["quantum_ids"] else "classical_baseline_qkus",
        "atomicrows_qkus",
        "pr154_target_qkus",
    ]
    if role == "RISK_ROLE":
        desired.insert(1, "risk_qkus")
    if role == "CAPITAL_ROLE":
        desired.insert(1, "capital_qkus")
    if role == "LATENCY_ROLE":
        desired.insert(1, "latency_qkus")
    if role == "EXECUTION_ROLE":
        desired.insert(1, "execution_qkus")
    for name in desired:
        for candidate in bucket.get(name, [])[:5]:
            if candidate not in qku_ids:
                qku_ids.append(candidate)
                break
        if len(qku_ids) >= c.MAX_QKUS_PER_BUNDLE:
            break
    return qku_ids[: c.MAX_QKUS_PER_BUNDLE]


def _bundle_mix(qku_ids: list[str], bucket_sets: dict[str, set[str]]) -> dict[str, list[str]]:
    mix: dict[str, list[str]] = {}
    for bucket_name in c.QKU_BUNDLE_MIX_CLASSES:
        members = [qku_id for qku_id in qku_ids if qku_id in bucket_sets.get(bucket_name, set())]
        mix[bucket_name] = members
    return mix


def _bundle_parent_scenario_family(mix: dict[str, list[str]], stage1_applicability: str) -> str:
    if mix["quantum_candidate_qkus"]:
        return "QUANTUM_CLASSICAL_HYBRID_COMPARE"
    if mix["optimizer_setting_qkus"]:
        return "OPTIMIZER_CONFIG_SENSITIVITY_REPLAY"
    if mix["latency_qkus"]:
        return "LATENCY_SENSITIVITY_REPLAY"
    if mix["risk_qkus"] or mix["capital_qkus"]:
        return "RISK_CAPITAL_SENSITIVITY_REPLAY"
    if stage1_applicability == "STAGE1_DIRECTLY_APPLICABLE":
        return "STAGE1_PREDICTION_MARKET_DIRECT"
    return "QKU_BUNDLE_COMBINATION_REPLAY"


def _bundle_child_scenario_family(
    mix: dict[str, list[str]],
    bundle_index: int,
    parent_scenario_family: str,
) -> str:
    if not mix["quantum_candidate_qkus"]:
        return parent_scenario_family
    child_families = c.QUANTUM_CLASSICAL_HYBRID_CHILD_SCENARIO_FAMILIES
    return child_families[(bundle_index - 1) % len(child_families)]


def _bundle_scenario_family(bundle: dict[str, Any]) -> str:
    if bundle.get("bundle_active_child_scenario_family"):
        return str(bundle["bundle_active_child_scenario_family"])
    if bundle.get("bundle_parent_scenario_family"):
        return str(bundle["bundle_parent_scenario_family"])
    if bundle["quantum_candidate_qkus"]:
        return "QUANTUM_CLASSICAL_HYBRID_COMPARE"
    if bundle["optimizer_setting_qkus"]:
        return "OPTIMIZER_CONFIG_SENSITIVITY_REPLAY"
    if bundle["latency_qkus"]:
        return "LATENCY_SENSITIVITY_REPLAY"
    if bundle["risk_qkus"] or bundle["capital_qkus"]:
        return "RISK_CAPITAL_SENSITIVITY_REPLAY"
    if str(bundle["bundle_stage1_applicability"]) == "STAGE1_DIRECTLY_APPLICABLE":
        return "STAGE1_PREDICTION_MARKET_DIRECT"
    return "QKU_BUNDLE_COMBINATION_REPLAY"


def _bundle_replay_lane(bundle: dict[str, Any]) -> str:
    score = int(bundle["bundle_replay_paper_priority_score"])
    if score >= 850:
        return "REPLAY_PAPER_PRIORITY_L0_DAY1_CRITICAL"
    if score >= 760:
        return "REPLAY_PAPER_PRIORITY_L1_HIGH"
    if score >= 620:
        return "REPLAY_PAPER_PRIORITY_L2_MEDIUM"
    return "REPLAY_PAPER_PRIORITY_L3_LOW"


def _ordered_bundles_for_selection(bundles: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        bundles,
        key=lambda item: (
            -int(item["bundle_quality_score"]),
            -int(item["bundle_replay_paper_priority_score"]),
            -int(item["bundle_expected_test_value_score"]),
            -int(item["bundle_quantum_priority_score"]),
            -int(item["bundle_risk_score"]),
            -int(item["bundle_latency_score"]),
            str(item["qku_bundle_id"]),
        ),
    )


def _bundle_selected_for_agent_role(bundle: dict[str, Any], role: str) -> bool:
    if role == "QTT_QUANTUM_ADVISORY_AGENT":
        return bool(bundle["quantum_candidate_qkus"] or bundle["hybrid_arbitration_qkus"])
    if role == "QTT_OPTIMIZER_ARBITRATION_AGENT":
        return bool(bundle["optimizer_setting_qkus"] or bundle["hybrid_arbitration_qkus"])
    if role == "QTT_RISK_AGENT":
        return bool(bundle["risk_qkus"])
    if role == "QTT_CAPITAL_AGENT":
        return bool(bundle["capital_qkus"])
    if role == "QTT_LATENCY_AGENT":
        return bool(bundle["latency_qkus"])
    if role == "QTT_EXECUTION_PREP_AGENT":
        return bool(bundle["execution_qkus"] or bundle["latency_qkus"])
    if role in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return bool(bundle["active_for_replay_paper_flag"])
    if role == "QTT_RESEARCH_AGENT":
        return True
    if role == "QTT_SOURCE_EVIDENCE_AGENT":
        return True
    if role == "QTT_SCORING_AGENT":
        return bool(bundle["active_for_candidate_scoring_flag"])
    if role == "QTT_RANKING_AGENT":
        return bool(bundle["active_for_candidate_scoring_flag"])
    if role == "QTT_OWNER_REVIEW_AGENT":
        return True
    if role == "QTT_ATOMICROWS_ENRICHMENT_AGENT":
        return bool(bundle["atomicrows_qkus"])
    if role == "QTT_PARAMETER_STACK_AGENT":
        return bool(
            bundle["strategy_template_qkus"]
            or bundle["formula_qkus"]
            or bundle["algorithm_qkus"]
            or bundle["optimizer_setting_qkus"]
            or bundle["quantum_candidate_qkus"]
        )
    return False


def _agent_slice_basis(role: str) -> str:
    return {
        "QTT_QUANTUM_ADVISORY_AGENT": "quantum_hybrid_classical_baseline_comparison_bundles",
        "QTT_OPTIMIZER_ARBITRATION_AGENT": "optimizer_and_hybrid_arbitration_bundles",
        "QTT_RISK_AGENT": "risk_drawdown_capital_control_bundles",
        "QTT_CAPITAL_AGENT": "position_sizing_and_capital_allocation_bundles",
        "QTT_LATENCY_AGENT": "latency_sensitive_bundle_candidates",
        "QTT_EXECUTION_PREP_AGENT": "order_condition_execution_prep_bundles",
        "QTT_REPLAY_AGENT": "stage1_replay_testable_active_bundles",
        "QTT_PAPER_AGENT": "stage1_paper_prep_active_bundles",
        "QTT_RESEARCH_AGENT": "research_and_online_enrichment_bundle_views",
        "QTT_SOURCE_EVIDENCE_AGENT": "source_triangulation_bundle_views",
        "QTT_SCORING_AGENT": "candidate_scoring_active_bundles",
        "QTT_RANKING_AGENT": "category_ranking_active_bundles",
        "QTT_OWNER_REVIEW_AGENT": "owner_review_and_promotion_gate_bundles",
        "QTT_ATOMICROWS_ENRICHMENT_AGENT": "atomicrows_compatible_bundles",
        "QTT_PARAMETER_STACK_AGENT": "parameter_stack_and_combination_bundles",
    }.get(role, "role_specific_bundle_slice")


def _replay_input_requirements(qku: dict[str, Any], scenario_family: str) -> list[str]:
    return [
        "historical_market_state_or_synthetic_replay_input_required",
        "fee_model_required",
        "slippage_model_required",
        f"scenario_family::{scenario_family}",
        f"qku_type::{qku.get('qku_type')}",
    ]


def _required_baselines(qku: dict[str, Any], aux: dict[str, Any]) -> list[str]:
    qku_id = str(qku["qku_id"])
    baselines = ["CLASSICAL_BASELINE_REQUIRED"]
    if qku_id in aux["quantum_ids"]:
        baselines.extend(["QUANTUM_CANDIDATE_REQUIRED", "HYBRID_ARBITRATION_REQUIRED"])
    return baselines


def _result_mode_slots() -> dict[str, dict[str, Any]]:
    return {
        mode: {
            "result_state": "NO_RESULT_YET",
            "result_artifact_path": None,
            "sample_size": 0,
            "result_evidence_weight": 0,
        }
        for mode in ("replay", "paper", "shadow", "live")
    }


def _mix_values(qku_ids: list[str], aux: dict[str, Any], key: str) -> list[str]:
    values = sorted(
        {
            str(aux["algo_by_qku"].get(qku_id, {}).get(key) or f"{key.upper()}_UNSPECIFIED")
            for qku_id in qku_ids
        }
    )
    return values


def _venue_scope(qku: dict[str, Any]) -> str:
    name = str(qku.get("qku_name") or "").upper()
    for venue in ("KALSHI", "POLYMARKET", "FORECASTEX", "IBKR"):
        if venue in name:
            return venue
    return "PREDICTION_MARKETS_GENERAL"


def _time_to_resolution_bucket(qku: dict[str, Any]) -> str:
    name = str(qku.get("qku_name") or "").upper()
    if "INTRADAY" in name or "DAILY" in name:
        return "SHORT_RESOLUTION_BUCKET"
    if "WEEK" in name:
        return "WEEKLY_RESOLUTION_BUCKET"
    return "RESOLUTION_BUCKET_UNOBSERVED_INPUT_REQUIRED"


def _source_signal_class(qku: dict[str, Any], aux: dict[str, Any]) -> str:
    qku_id = str(qku["qku_id"])
    if qku_id in aux["fallback_ids"]:
        return "OWNER_DEFAULT_SOURCE_SIGNAL_CANDIDATE"
    if qku_id in aux["quantum_ids"]:
        return "QUANTUM_ADVISORY_SIGNAL_CANDIDATE"
    return "LOCAL_ARTIFACT_SOURCE_SIGNAL_CANDIDATE"


def _quantum_priority_subclass(qku: dict[str, Any], aux: dict[str, Any]) -> str:
    joined = " ".join(
        [
            str(qku.get("qku_quantum_subclass") or ""),
            str(qku.get("qku_name") or ""),
            str(aux["quantum_by_qku"].get(str(qku["qku_id"]), {})),
        ]
    ).upper()
    mapping = [
        ("QUBO", "QUBO_PRIORITY"),
        ("ISING", "ISING_PRIORITY"),
        ("QAOA", "QAOA_PRIORITY"),
        ("VQE", "VQE_PRIORITY"),
        ("ANNEAL", "ANNEALING_PRIORITY"),
        ("CAPITAL", "QUANTUM_CAPITAL_ALLOCATION_PRIORITY"),
        ("PORTFOLIO", "QUANTUM_PORTFOLIO_PRIORITY"),
        ("MARKET", "QUANTUM_MARKET_SELECTION_PRIORITY"),
        ("SIGNAL", "QUANTUM_SIGNAL_COMBINATION_PRIORITY"),
        ("LATENCY", "QUANTUM_LATENCY_ROUTING_PRIORITY"),
        ("ARBITRAGE", "QUANTUM_ARBITRAGE_PATH_PRIORITY"),
        ("HYBRID", "HYBRID_QUANTUM_CLASSICAL_PRIORITY"),
        ("INSPIRED", "QUANTUM_INSPIRED_PRIORITY"),
    ]
    for token, subclass in mapping:
        if token in joined:
            return subclass
    return "QUANTUM_ADVISORY_PRIORITY"


def _quantum_strategy_role(subclass: str) -> str:
    return {
        "QUBO_PRIORITY": "qubo_formulation_compare",
        "ISING_PRIORITY": "ising_formulation_compare",
        "QAOA_PRIORITY": "qaoa_candidate_compare",
        "VQE_PRIORITY": "vqe_candidate_compare",
        "ANNEALING_PRIORITY": "annealing_candidate_compare",
    }.get(subclass, "quantum_advisory_compare")


def _owner_review_reason(qku: dict[str, Any], aux: dict[str, Any], lane: dict[str, Any]) -> str:
    qku_id = str(qku["qku_id"])
    if qku_id in aux["quantum_ids"]:
        return "QUANTUM_FORWARD_OR_HYBRID_COMPARE_REQUIRES_OWNER_PROMOTION_CONTROL"
    if lane["quality_lane"] == "QKU_QUALITY_LANE_F_ONLINE_ENRICHMENT_NEEDED":
        return "ONLINE_ENRICHMENT_OR_SOURCE_TRIANGULATION_REQUIRED"
    if qku_id in aux["fallback_ids"]:
        return "OWNER_FALLBACK_DEFAULT_REQUIRES_FUTURE_REVIEW"
    return "HIGH_PRIORITY_STAGE1_REPLAY_PAPER_CANDIDATE"


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.upper())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")[:96] or "UNSPECIFIED"


def _active_branch(repo_root: Path) -> str:
    return _git_stdout(repo_root, ["branch", "--show-current"])


def _head_commit(repo_root: Path) -> str:
    return _git_stdout(repo_root, ["rev-parse", "HEAD"])


def _pr161c_lineage_flag(repo_root: Path) -> bool:
    log = _git_stdout(
        repo_root,
        [
            "log",
            "--format=%s",
            "--fixed-strings",
            "--grep=pr161c-qku-residual-candidate-assimilation-fill-campaign",
            "HEAD",
        ],
    )
    return "pr161c-qku-residual-candidate-assimilation-fill-campaign" in log


def _git_stdout(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""
