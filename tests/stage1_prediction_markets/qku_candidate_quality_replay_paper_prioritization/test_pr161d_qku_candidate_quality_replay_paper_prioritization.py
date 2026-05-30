from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_candidate_quality_replay_paper_prioritization import constants as c
from src.qtt.stage1_prediction_markets.qku_candidate_quality_replay_paper_prioritization.validator import (
    _load_records,
    _validate_boundedness,
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED = REPO_ROOT / "docs/master_plan/generated"


def _payload(filename: str) -> dict[str, object]:
    return json.loads((GENERATED / filename).read_text(encoding="utf-8"))


def _records(filename: str) -> list[dict[str, object]]:
    return _load_records(REPO_ROOT, _payload(filename))


@pytest.fixture(scope="module")
def summary() -> dict[str, object]:
    return _payload("PR161D_FinalSummary.report.json")


def test_pr161d_consumes_pr161c_and_registers_agent_network(summary):
    assert summary["pr161c_inventory_qku_count_loaded"] == 9360
    assert summary["pr161c_field_value_facet_count_loaded"] == 22625
    assert summary["pr161c_graph_node_count_loaded"] == 9360
    assert summary["pr161c_graph_edge_count_loaded"] == 60375
    assert summary["canonical_qtt_agent_role_count"] == 15
    assert summary["agent_role_network_registry_count"] == 15
    assert summary["qku_service_layer_domain_count"] == 10

    network = _payload("PR161D_QTTAgentRoleNetworkRegistry.report.json")
    records = _records("PR161D_QTTAgentRoleNetworkRegistry.report.json")
    assert {record["assigned_agent_role"] for record in records} == set(c.CANONICAL_QTT_AGENT_ROLES)
    assert all(record["no_runtime_agent_claim_flag"] for record in records)
    assert all(
        service["no_runtime_agent_claim_flag"]
        for service in network["service_layer_domains"]
    )


def test_pr161d_online_search_and_coverage(summary):
    receipt = _records("PR161D_QKUOnlineSearchCapabilityReceipt.report.json")[0]
    coverage = _records("PR161D_QKUOnlineEnrichmentCoverage.report.json")
    sources = _records("PR161D_QKUOnlineSourceCandidateRegistry.report.json")

    assert receipt["search_attempted"] is True
    assert receipt["search_succeeded"] is True
    assert receipt["live_web_available"] is True
    assert len(coverage) == 9360
    assert summary["qkus_with_direct_online_source_coverage"] > 0
    assert summary["qkus_with_cluster_online_source_coverage"] > 0
    assert summary["qkus_queued_for_online_scout"] > 0
    assert all(record["online_enrichment_coverage_state"] in c.ONLINE_ENRICHMENT_STATES for record in coverage)
    assert any(source["source_class"] == "PUBLIC_GITHUB_REPOSITORY" for source in sources)
    assert all(
        source["source_acceptance_state"]
        == "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_SCORING_AND_REPLAY_PAPER_PRIORITIZATION"
        for source in sources
    )


def test_pr161d_score_components_scores_and_lanes(summary):
    quality = _records("PR161D_QKUQualityScoreRegistry.report.json")
    components = _records("PR161D_QKUScoreComponentBreakdown.report.json")
    lanes = _records("PR161D_QKUQualityLaneClassification.report.json")
    replay = _records("PR161D_QKUReplayPaperPriorityQueue.report.json")

    assert len(quality) == 9360
    assert len(components) == 9360
    assert len(lanes) == 9360
    assert len(replay) == 9360
    assert summary["score_component_weight_sum"] == 1.0
    assert min(record["qku_quality_score"] for record in quality) >= 0
    assert max(record["qku_quality_score"] for record in quality) <= 1000
    for record in components:
        for component in record["components"].values():
            assert 0.0 <= component["value"] <= 1.0
            assert component["basis"]
    assert all(record["quality_lane"] in c.QUALITY_LANES for record in lanes)
    assert all(record["replay_paper_priority_lane"] in c.REPLAY_PAPER_PRIORITY_LANES for record in replay)
    assert all(record["replay_result_created_flag"] is False for record in replay)
    assert all(record["paper_result_created_flag"] is False for record in replay)
    assert all(record["profit_evidence_created_flag"] is False for record in replay)


def test_pr161d_rankings_are_pre_result_and_contiguous(summary):
    rankings = _records("PR161D_QKUCategoryRankingRegistry.report.json")
    top_lists = _records("PR161D_QKUCategoryTopListIndex.report.json")
    slots = _records("PR161D_QKUResultBackedRankingSlots.report.json")

    assert len(rankings) == summary["category_ranking_records_created"]
    assert len(top_lists) == summary["category_top_list_records_created"]
    assert len(slots) == 9360
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for record in rankings:
        assert record["ranking_basis"] == "PRE_RESULT_RANKING"
        assert record["result_evidence_weight"] == 0
        assert record["final_qku_category_rank_score"] == record["pre_result_quality_score"]
        grouped[(record["ranking_category"], record["category_value"])].append(record["qku_rank"])
    for ranks in grouped.values():
        assert sorted(ranks) == list(range(1, len(ranks) + 1))
    assert all(slot["result_state"] == "NO_RESULT_YET" for slot in slots)
    assert all(slot["profitability_label"] == "UNOBSERVED" for slot in slots)
    assert all(slot["result_evidence_weight"] == 0 for slot in slots)
    assert all(slot["result_backed_score"] is None for slot in slots)
    assert all(slot["no_result_fabricated_flag"] is True for slot in slots)
    assert all(slot["no_profit_evidence_created_flag"] is True for slot in slots)


def test_pr161d_scenarios_bundles_and_future_patterns_do_not_fabricate_results(summary):
    scenarios = _records("PR161D_QKUScenarioOutcomeMatrix.report.json")
    orders = _records("PR161D_QKUOrderConditionScenarioRegistry.report.json")
    bundles = _records("PR161D_QKUCombinationCandidateRegistry.report.json")
    combo_queue = _records("PR161D_QKUCombinationReplayPaperPriorityQueue.report.json")
    patterns = _records("PR161D_QKUFutureProfitabilityPatternFields.report.json")
    replay_scenarios = _records("PR161D_QKUReplayPaperScenarioInputs.report.json")

    assert scenarios
    assert orders
    assert bundles
    assert combo_queue
    assert patterns
    assert len(replay_scenarios) == 9360
    assert len(bundles) <= c.MAX_QKU_BUNDLE_CANDIDATES
    assert all(len(bundle["qku_ids"]) <= c.MAX_QKUS_PER_BUNDLE for bundle in bundles)
    assert all(bundle["active_for_live_trading_flag"] is False for bundle in bundles)
    assert all(scenario["result_state"] == "NO_RESULT_YET" for scenario in scenarios)
    assert all(scenario["profitability_label"] == "UNOBSERVED" for scenario in scenarios)
    assert all(scenario["no_result_fabricated_flag"] for scenario in scenarios)
    assert all(bundle["profit_evidence_created_flag"] is False for bundle in bundles)
    assert all(bundle["live_execution_created_flag"] is False for bundle in bundles)
    assert all(record["future_confidence_class"] == "UNOBSERVED" for record in patterns)
    assert all(record["future_sample_size"] == 0 for record in patterns)


def test_pr161d_bundle_boundedness_uses_shared_registry_and_slices(summary):
    boundedness = _records("PR161D_QKUCombinationGenerationBoundedness.report.json")[0]
    bundles = _records("PR161D_QKUCombinationCandidateRegistry.report.json")
    slices = _records("PR161D_QKUAgentRoleBundleSlice.report.json")
    fanout = _records("PR161D_QKUAgentRoleBundleReferenceFanout.report.json")

    assert boundedness["raw_bundle_candidate_count"] == len(bundles)
    assert boundedness["deduplicated_bundle_candidate_count"] == len(bundles)
    assert boundedness["shared_bundle_registry_count"] == len(bundles)
    assert boundedness["agent_materialized_bundle_count"] == 0
    assert boundedness["cap_applies_metric_violation_count"] == 0
    assert boundedness["active_selection_within_caps_flag"] is True
    assert boundedness["shared_bundle_registry_no_data_loss_flag"] is True
    assert boundedness["reference_fanout_exemption_count"] == len(c.CANONICAL_QTT_AGENT_ROLES)
    assert len(slices) == len(c.CANONICAL_QTT_AGENT_ROLES)
    assert len(fanout) == len(c.CANONICAL_QTT_AGENT_ROLES)
    assert all(record["agent_materialized_bundle_count"] == 0 for record in slices)
    assert all(record["agent_active_slice_count"] <= c.MAX_BUNDLES_PER_AGENT_ROLE for record in slices)
    assert all(record["fanout_reference_not_materialized_flag"] for record in slices)
    assert all(record["cap_applies_flag"] is False for record in fanout)
    assert all(
        record["cap_exemption_reason"] == c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT
        for record in fanout
    )
    for metric in boundedness["cap_metrics"]:
        if metric["cap_applies_flag"]:
            assert metric["active_count"] <= metric["cap_value"]
        else:
            assert metric["cap_exemption_reason"] in {
                c.CAP_EXEMPTION_AGENT_REFERENCE_FANOUT,
                c.CAP_EXEMPTION_PARENT_AGGREGATE_SCENARIO_FAMILY,
            }
    child_metrics = [
        metric
        for metric in boundedness["cap_metrics"]
        if metric["cap_id"].startswith("MAX_BUNDLES_PER_ACTIVE_SCENARIO_CHILD_FAMILY::")
    ]
    assert child_metrics
    assert all(metric["active_count"] <= c.MAX_BUNDLES_PER_SCENARIO_FAMILY for metric in child_metrics)
    assert sum(record["agent_overflow_count"] for record in slices) > 0


def test_pr161d_boundedness_validator_rejects_unexplained_cap_overflow():
    boundedness = _records("PR161D_QKUCombinationGenerationBoundedness.report.json")
    bundles = _records("PR161D_QKUCombinationCandidateRegistry.report.json")
    slices = _records("PR161D_QKUAgentRoleBundleSlice.report.json")
    fanout = _records("PR161D_QKUAgentRoleBundleReferenceFanout.report.json")
    bad = dict(boundedness[0])
    bad["cap_metrics"] = [
        {
            "cap_id": "BAD_CAP",
            "cap_value": 5,
            "cap_applies_to": "test",
            "cap_denominator": "test",
            "observed_count": 10,
            "active_count": 10,
            "overflow_count": 0,
            "dormant_count": 0,
            "cap_applies_flag": True,
            "cap_exemption_applied_flag": False,
            "cap_exemption_reason": None,
            "boundedness_status": "PASS",
        }
    ]
    failures: list[str] = []
    _validate_boundedness([bad], bundles, slices, fanout, failures)
    assert any("active count exceeds cap" in failure for failure in failures)


def test_pr161d_market_bundle_activation_policy_is_owner_dashboard_only(summary):
    policy = _records("PR161D_QKUMarketBundleActivationPolicy.report.json")
    dashboard = _records("PR161D_QKUMarketBundleActivationDashboardOptions.report.json")
    active = _records("PR161D_QKUMarketActiveBundleSet.report.json")
    dormant = _records("PR161D_QKUMarketBundleDormancyQueue.report.json")
    bundles = _records("PR161D_QKUCombinationCandidateRegistry.report.json")

    policy_by_market = {record["market_class"]: record for record in policy}
    assert len(policy) == len(c.MARKET_BUNDLE_ACTIVATION_POLICY)
    assert len(dashboard) == len(c.MARKET_BUNDLE_ACTIVATION_POLICY)
    assert policy_by_market["PREDICTION_MARKET"]["default_activation_state"] == "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER"
    assert policy_by_market["MARKET_AGNOSTIC"]["default_activation_state"] == "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER"
    assert policy_by_market["NON_MARKET_SPECIFIC"]["default_activation_state"] == "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER"
    for market in c.FUTURE_MARKET_CLASSES:
        assert policy_by_market[market]["default_activation_state"] == "MARKET_BUNDLE_DORMANT_FUTURE_STAGE"
    assert all(record["affects_live_authority_flag"] is False for record in policy)
    assert all(record["no_live_authority_created_flag"] is True for record in policy)
    assert all(bundle["active_for_live_trading_flag"] is False for bundle in bundles)
    assert len(active) == summary["market_active_bundle_count"]
    assert len(dormant) == summary["market_dormant_bundle_count"]
    active_by_market = Counter(record["bundle_market"] for record in active)
    assert active_by_market["PREDICTION_MARKET"] == summary["prediction_market_active_bundle_count"]
    assert active_by_market["MARKET_AGNOSTIC"] == summary["market_agnostic_active_bundle_count"]


def test_pr161d_quantum_classical_hybrid_and_atomicrows_pr154(summary):
    quantum = _records("PR161D_QKUQuantumPriorityQueue.report.json")
    classical = _records("PR161D_QKUClassicalBaselinePriorityQueue.report.json")
    hybrid = _records("PR161D_QKUHybridArbitrationPriorityQueue.report.json")
    bridge = _records("PR161D_QKUAtomicRowsPR154PriorityBridge.report.json")

    assert len(quantum) == summary["quantum_priority_queue_count"]
    assert len(classical) == 9360
    assert len(hybrid) == summary["hybrid_arbitration_queue_count"]
    assert summary["quantum_priority_queue_count"] > 0
    assert summary["hybrid_arbitration_queue_count"] > 0
    assert len(bridge) == 9360
    assert summary["atomicrows_compatibility_priority_count"] == 4183
    assert summary["pr154_compatibility_priority_count"] == 342
    assert all(record["qku_quantum_backend_execution_allowed_flag"] is False for record in quantum)
    assert all(record["qku_optimizer_execution_allowed_flag"] is False for record in quantum)


def test_pr161d_agent_tasks_and_graph_consumption(summary):
    tasks = _records("PR161D_QKUAgentTaskQueue.report.json")
    routes = _records("PR161D_QKUAgentGraphRoutingMatrix.report.json")
    graph_audit = _records("PR161D_QKUGraphConsumptionAudit.report.json")

    assert len(tasks) == summary["agent_task_queue_count"]
    assert {record["assigned_agent_role"] for record in tasks} == set(c.CANONICAL_QTT_AGENT_ROLES)
    assert {record["assigned_agent_role"] for record in routes} == set(c.CANONICAL_QTT_AGENT_ROLES)
    assert all(record["no_runtime_agent_claim_flag"] for record in tasks)
    assert all(record["no_live_authority_flag"] for record in tasks)
    assert all(record["no_profit_evidence_flag"] for record in tasks)
    assert graph_audit[-1]["graph_consumption_status"] == "PASS"


def test_pr161d_guardrails_schemas_and_validator(summary):
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures
    assert summary["forbidden_authority_scan_status"] == "PASS"
    assert summary["no_scattered_hardcoded_authority_audit_status"] == "PASS"
    assert summary["bundle_boundedness_metadata_consistent_flag"] is True
    assert summary["cap_applies_metric_violation_count"] == 0
    assert summary["result_backed_slots_profitability_label_present_count"] == 9360
    assert summary["result_backed_slots_unobserved_count"] == 9360
    assert summary["remaining_semantic_blocker_count"] == 0
    assert summary["largest_generated_pr161d_report_size_bytes"] < c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES
    assert summary["master_plan_file_edited_flag"] is False
    assert summary["global_rename_performed_flag"] is False
    assert summary["atomicrows_final_bundle_created_flag"] is False
    assert summary["atomicrows_bundle_sha_freeze_reference_created_flag"] is False
    assert summary["qtt_sha_or_generated_sha_authority_created_flag"] is False
    assert summary["replay_paper_results_fabricated_flag"] is False
    assert summary["shadow_live_results_fabricated_flag"] is False
    assert summary["profit_evidence_created_flag"] is False
    assert summary["live_authority_created_flag"] is False
    assert summary["optimizer_execution_created_flag"] is False
    assert summary["quantum_backend_execution_created_flag"] is False

    for schema_path in (REPO_ROOT / c.SCHEMA_DIR).glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for field, enum_values in c.SCHEMA_ENUM_FIELDS.items():
            properties = schema.get("properties", {})
            if field in properties and "enum" in properties[field]:
                assert properties[field]["enum"] == list(enum_values)

    generated_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in GENERATED.glob("PR161D_*.report.json")
    )
    assert "AtomicRows.bundle.sha256" not in generated_text
    assert "SOURCE_ACCEPTED_AS_PROFIT_EVIDENCE" not in generated_text
    assert "SOURCE_ACCEPTED_AS_LIVE_AUTHORITY" not in generated_text
