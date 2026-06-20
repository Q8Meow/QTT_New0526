#!/usr/bin/env python3
"""Shared validators for PR168-RANK generated artifacts."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rank_binary_prediction_market_pnl import BinaryPnLInput, compute_binary_prediction_market_pnl
from tools.pr168_rank_compute_kernel import EMPTY_ALLOWED_REPORTS, REQUIRED_RANK_REPORTS
from tools.pr168_rank_report_writer import GENERATED_DIR, read_records, read_report
from tools.validation_scope_registry import PR168_RANK_BRANCH, is_pr_scoped_changed_path_allowed


FORBIDDEN_TRUE_FLAGS = (
    "source_truth_authority",
    "connector_truth_authority",
    "connector_semantic_binding_created",
    "live_authority",
    "order_authority",
    "generated_digest_authority_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
)

FORBIDDEN_TEXT = (
    "submit_order = true",
    "cancel_order = true",
    "reduce_order = true",
    "close_order = true",
    "quantum_advantage_claim_flag\": true",
    "live_execution_allowed_flag\": true",
    "source_truth_status\": \"ACCEPTED",
    "connector_binding_status\": \"BOUND",
)


def assert_true(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{code}: {message}")


def load_root(filename: str) -> dict[str, Any]:
    return read_report(REPO_ROOT, filename)


def load(filename: str) -> list[dict[str, Any]]:
    return read_records(REPO_ROOT, filename)


def _walk(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)
    else:
        yield value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_reports_exist() -> None:
    missing = [filename for filename in REQUIRED_RANK_REPORTS if not (REPO_ROOT / GENERATED_DIR / filename).exists()]
    assert_true(not missing, "PR168_RANK_MISSING_REPORTS", f"missing reports: {missing[:10]}")
    for filename in REQUIRED_RANK_REPORTS:
        root = load_root(filename)
        assert_true(root.get("materialized_artifact") is True, "PR168_RANK_NOT_MATERIALIZED", filename)
        assert_true(root.get("no_orphan_status"), "PR168_RANK_ROOT_NO_ORPHAN_MISSING", filename)
        for flag in FORBIDDEN_TRUE_FLAGS:
            assert_true(root.get(flag) in (False, 0), "PR168_RANK_FORBIDDEN_ROOT_AUTHORITY", f"{filename} {flag}")
        if int(root.get("record_count", 0)) == 0:
            assert_true(filename in EMPTY_ALLOWED_REPORTS, "PR168_RANK_UNEXPECTED_EMPTY_REPORT", filename)
            assert_true(root.get("summary", {}).get("empty_reason"), "PR168_RANK_EMPTY_WITHOUT_REASON", filename)


def validate_input_consumption() -> None:
    summary = load("PR168_RANK_PR168RPInputResultSummary.report.json")[0]
    source_final = load("PR168_RP_FinalSummary.report.json")[0]
    assert_true(summary["decision"] == "PROCEED_TO_PR168_RANK", "PR168_RANK_INPUT_NOT_PROCEED", str(summary))
    assert_true(summary["computed_negative_count"] == 10515, "PR168_RANK_NEGATIVE_COUNT", str(summary["computed_negative_count"]))
    assert_true(summary["pretrade_candidate_count"] == source_final["pretrade_candidate_count"], "PR168_RANK_PRETRADE_COUNT", "mismatch")
    assert_true(summary["computed_positive_count"] == 0, "PR168_RANK_POSITIVE_COUNT", "upstream positives should be zero")
    assert_true(not summary["missing_required_reports"], "PR168_RANK_MISSING_INPUTS", str(summary["missing_required_reports"]))
    assert_true(not summary["malformed_required_reports"], "PR168_RANK_MALFORMED_INPUTS", str(summary["malformed_required_reports"]))


def validate_no_fake_ranking() -> None:
    ranking = load("PR168_RANK_EvidenceBackedRanking.report.json")
    champions = load("PR168_RANK_ChampionCandidates.report.json")
    assert_true(not champions, "PR168_RANK_FAKE_CHAMPION", "no upstream positive evidence exists")
    assert_true(ranking, "PR168_RANK_RANKING_EMPTY", "ranking rows required")
    for row in ranking[:200]:
        assert_true(row.get("computed_status") != "COMPUTED_POSITIVE_EDGE", "PR168_RANK_FAKE_POSITIVE", str(row.get("candidate_id")))
        assert_true(row.get("champion_eligible") is False, "PR168_RANK_CHAMPION_FROM_NEGATIVE", str(row.get("candidate_id")))
        assert_true(row.get("numeric_evidence_refs"), "PR168_RANK_RANK_WITHOUT_NUMERIC_REF", str(row.get("candidate_id")))


def validate_score_math() -> None:
    rows = load("PR168_RANK_ScoreComponentLedger.report.json")
    assert_true(rows, "PR168_RANK_SCORE_ROWS_EMPTY", "score ledger required")
    for row in rows[:200]:
        components = row.get("score_components", {})
        for key in (
            "fill_adjusted_expected_pnl",
            "lower_confidence_bound_edge",
            "no_trade_comparison_margin",
            "total_tca_cost",
            "overfit_fdr_penalty",
            "capacity_crowding_penalty",
        ):
            assert_true(_is_number(components.get(key)), "PR168_RANK_SCORE_COMPONENT_NOT_NUMERIC", f"{row.get('candidate_id')} {key}")
        assert_true(_is_number(row.get("rank_score")), "PR168_RANK_SCORE_NOT_NUMERIC", str(row.get("candidate_id")))


def validate_binary_prediction_market_pnl() -> None:
    yes = compute_binary_prediction_market_pnl(
        BinaryPnLInput(
            side="YES",
            calibrated_model_probability_yes=0.62,
            execution_price=0.52,
            order_quantity=10,
            explicit_fees_per_unit=0.01,
            fill_probability=0.8,
            lcb_win_probability=0.57,
        )
    )
    no = compute_binary_prediction_market_pnl(
        BinaryPnLInput(
            side="NO",
            calibrated_model_probability_yes=0.38,
            execution_price=0.52,
            order_quantity=10,
            explicit_fees_per_unit=0.01,
            fill_probability=0.8,
            lcb_win_probability=0.57,
        )
    )
    assert_true(yes["p_win"] == 0.62, "PR168_RANK_YES_PWIN", str(yes))
    assert_true(no["p_win"] == 0.62, "PR168_RANK_NO_PWIN", str(no))
    assert_true(yes["net_expected_pnl_per_unit"] == 0.09, "PR168_RANK_YES_NET_PNL", str(yes))
    assert_true(no["net_expected_pnl_per_unit"] == 0.09, "PR168_RANK_NO_NET_PNL", str(no))


def validate_candidate_stack_generation() -> None:
    rows = load("PR168_RANK_CandidateStackGenerationLedger.report.json")
    assert_true(rows, "PR168_RANK_STACKS_EMPTY", "candidate stacks required")
    for row in rows[:200]:
        assert_true(row.get("candidate_stack_id"), "PR168_RANK_STACK_ID_MISSING", str(row))
        assert_true(row.get("upstream_numeric_evidence_refs"), "PR168_RANK_STACK_NO_NUMERIC_REF", str(row.get("candidate_stack_id")))
        assert_true(row.get("role_completeness_status") == "COMPLETE_FOR_NONLIVE_RANKING", "PR168_RANK_STACK_INCOMPLETE", str(row.get("candidate_stack_id")))


def validate_pretrade_order_simulation() -> None:
    rows = load("PR168_RANK_PreTradeOrderSimulationLedger.report.json")
    summary = load("PR168_RANK_PR168RPInputResultSummary.report.json")[0]
    assert_true(len(rows) == summary["pretrade_candidate_count"], "PR168_RANK_SIM_COUNT", f"{len(rows)} != {summary['pretrade_candidate_count']}")
    for row in rows[:200]:
        for key in ("fill_adjusted_expected_pnl", "lower_confidence_bound_edge", "no_trade_comparison_margin", "expected_fill_probability"):
            assert_true(_is_number(row.get(key)), "PR168_RANK_SIM_NUMERIC_MISSING", f"{row.get('simulated_order_id')} {key}")
        flags = row.get("authority_boundary_flags", {})
        assert_true(flags.get("live_execution_allowed_flag") is False, "PR168_RANK_SIM_LIVE_FLAG", str(row.get("simulated_order_id")))


def validate_order_decision_tournament() -> None:
    rows = load("PR168_RANK_OrderDecisionTournament.report.json")
    assert_true(rows, "PR168_RANK_TOURNAMENT_EMPTY", "tournament rows required")
    for row in rows[:200]:
        assert_true(row.get("winning_action") == "NO_TRADE_CANDIDATE", "PR168_RANK_TOURNAMENT_NOT_NOTRADE", str(row.get("candidate_id")))
        assert_true(row.get("no_trade_dominates") is True, "PR168_RANK_NOTRADE_NOT_DOMINANT", str(row.get("candidate_id")))
        assert_true(row.get("champion_eligible") is False, "PR168_RANK_TOURNAMENT_FAKE_CHAMPION", str(row.get("candidate_id")))


def validate_no_trade_dominance() -> None:
    rows = load("PR168_RANK_NoTradeDominanceResults.report.json")
    assert_true(rows, "PR168_RANK_NO_TRADE_ROWS_EMPTY", "no-trade dominance rows required")
    assert_true(all(row.get("no_trade_dominates") is True for row in rows[:200]), "PR168_RANK_NO_TRADE_FALSE", "sample failed")


def validate_quantum_structural() -> None:
    rows = load("PR168_RANK_QuantumStructuralRanking.report.json")
    assert_true(rows, "PR168_RANK_QUANTUM_ROWS_EMPTY", "quantum rows required")
    for row in rows[:200]:
        assert_true(row.get("backend_execution_required_flag") is False, "PR168_RANK_QUANTUM_BACKEND", str(row.get("quantum_candidate_id")))
        assert_true(row.get("quantum_advantage_claim_flag") is False, "PR168_RANK_QUANTUM_ADVANTAGE", str(row.get("quantum_candidate_id")))
        assert_true("GAP_ROUTED" in str(row.get("qubo_map_status")) or row.get("objective_terms") is not None, "PR168_RANK_QUANTUM_MAP_STATUS", str(row.get("quantum_candidate_id")))


def validate_registry_rows() -> None:
    registry_files = [
        "PR168_RANK_MarketAdapterRegistrySeed.report.json",
        "PR168_RANK_VenueCostModelRegistrySeed.report.json",
        "PR168_RANK_ContractPayoffModelRegistrySeed.report.json",
        "PR168_RANK_FormulaPluginRegistrySeed.report.json",
        "PR168_RANK_AlgorithmPluginRegistrySeed.report.json",
        "PR168_RANK_QuantumObjectiveRegistrySeed.report.json",
        "PR168_RANK_OrderPolicyRegistry.report.json",
        "PR168_RANK_AgentCapabilityRegistrySeed.report.json",
        "PR168_RANK_ConnectorReadinessRegistrySeed.report.json",
        "PR168_RANK_RuntimeAllowlistSeedRegistry.report.json",
        "PR168_RANK_HotPathDecisionSurfaceRegistry.report.json",
    ]
    for filename in registry_files:
        rows = load(filename)
        assert_true(rows, "PR168_RANK_REGISTRY_EMPTY", filename)
        for row in rows:
            assert_true(row.get("registry_status") == "SEED_CONTRACT_ONLY", "PR168_RANK_REGISTRY_NOT_SEED", filename)
            assert_true(row.get("live_execution_allowed_flag") is False, "PR168_RANK_REGISTRY_LIVE", filename)
            assert_true(row.get("connector_binding_status") == "NOT_BOUND_IN_THIS_PR", "PR168_RANK_REGISTRY_BOUND", filename)
            assert_true(row.get("source_evidence_status") == "NOT_ACCEPTED_IN_THIS_PR", "PR168_RANK_REGISTRY_SOURCE_TRUTH", filename)
            assert_true(row.get("downstream_pr_refs"), "PR168_RANK_REGISTRY_NO_DOWNSTREAM_PR", filename)
            assert_true(row.get("owning_agent"), "PR168_RANK_REGISTRY_NO_AGENT", filename)


def validate_no_orphan() -> None:
    validate_reports_exist()
    for filename in REQUIRED_RANK_REPORTS:
        root = load_root(filename)
        for key in ("producer", "consumer", "upstream_source", "downstream_route", "owning_agent", "no_orphan_status"):
            assert_true(root.get(key) not in ("", None), "PR168_RANK_ROOT_NO_ORPHAN_FIELD_MISSING", f"{filename} {key}")
        for row in root.get("records", [])[:10]:
            for key in ("producer", "consumer", "upstream_source", "downstream_route", "owning_agent", "no_orphan_status"):
                assert_true(row.get(key) not in ("", None), "PR168_RANK_ROW_NO_ORPHAN_FIELD_MISSING", f"{filename} {key}")


def validate_authority_boundaries() -> None:
    for filename in REQUIRED_RANK_REPORTS:
        path = REPO_ROOT / GENERATED_DIR / filename
        root = load_root(filename)
        for flag in FORBIDDEN_TRUE_FLAGS:
            assert_true(root.get(flag) in (False, 0), "PR168_RANK_FORBIDDEN_AUTHORITY", f"{filename} {flag}")
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for forbidden in FORBIDDEN_TEXT:
            assert_true(forbidden.lower() not in lowered, "PR168_RANK_FORBIDDEN_TEXT", f"{filename}: {forbidden}")


def validate_materialized_artifacts() -> None:
    for filename in REQUIRED_RANK_REPORTS:
        root = load_root(filename)
        assert_true(root.get("materialized_artifact") is True, "PR168_RANK_BLUEPRINT_ONLY", filename)
        assert_true("blueprint" not in json.dumps(root).lower(), "PR168_RANK_BLUEPRINT_TEXT", filename)


def validate_scope_registry() -> None:
    allowed = [
        "tools/build_pr168_rank_evidence_backed_ranking.py",
        "tools/pr168_rank_compute_kernel.py",
        "tools/validate_pr168_rank_input_consumption.py",
        "docs/master_plan/generated/PR168_RANK_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_rank_shards/PR168_RANK_EvidenceBackedRanking.part_0001_of_0001.report.json",
        "tests/pr168_rank/test_input_consumption.py",
    ]
    rejected = [
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "src/qtt/live_order_router.py",
        "AtomicRows.bundle.sha256",
    ]
    for path in allowed:
        assert_true(is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path), "PR168_RANK_SCOPE_REJECTED_ALLOWED", path)
    for path in rejected:
        assert_true(not is_pr_scoped_changed_path_allowed(PR168_RANK_BRANCH, path), "PR168_RANK_SCOPE_ALLOWED_REJECTED", path)


def validate_final_summary() -> None:
    row = load("PR168_RANK_FinalSummary.report.json")[0]
    assert_true(row["ranking_proceeded"] is True, "PR168_RANK_FINAL_NOT_PROCEEDED", str(row))
    assert_true(row["champion_count"] == 0, "PR168_RANK_FINAL_CHAMPIONS", str(row["champion_count"]))
    assert_true(row["challenger_count"] == 10515, "PR168_RANK_FINAL_CHALLENGERS", str(row["challenger_count"]))
    assert_true(row["forbidden_authority_not_created"] is True, "PR168_RANK_FINAL_AUTHORITY", str(row))
    assert_true(row["central_future_expansion_registry_layer_status"] == "MATERIALIZED_SEED_CONTRACT_ONLY", "PR168_RANK_FINAL_REGISTRY", str(row))


def validate_terminal_lifecycle() -> None:
    rows = load("PR168_RANK_TerminalArtifactLifecycle.report.json")
    assert_true(rows, "PR168_RANK_TERMINAL_EMPTY", "terminal lifecycle required")
    for row in rows[:200]:
        assert_true(row.get("terminal_reason_code"), "PR168_RANK_TERMINAL_REASON_MISSING", str(row.get("candidate_id")))
        assert_true(row.get("terminal_governance_consumer"), "PR168_RANK_TERMINAL_CONSUMER_MISSING", str(row.get("candidate_id")))


def validate_connector_routing() -> None:
    rows = load("PR168_RANK_ConnectorCandidateRoutingLedger.report.json")
    assert_true(rows, "PR168_RANK_CONNECTOR_ROWS_EMPTY", "connector rows required")
    for row in rows[:200]:
        assert_true(row.get("source_truth_status") == "NOT_ACCEPTED_IN_THIS_PR", "PR168_RANK_CONNECTOR_SOURCE_TRUTH", str(row))
        assert_true(row.get("private_state_required_flag") is False, "PR168_RANK_CONNECTOR_PRIVATE", str(row))
        assert_true(row.get("cash_required_flag") is False, "PR168_RANK_CONNECTOR_CASH", str(row))
        assert_true(row.get("order_authority_required_flag") is False, "PR168_RANK_CONNECTOR_ORDER", str(row))


def validate_two_speed() -> None:
    rows = load("PR168_RANK_TwoSpeedDecisionSurfacePlan.report.json")
    assert_true(rows, "PR168_RANK_TWO_SPEED_EMPTY", "two-speed rows required")
    row = rows[0]
    assert_true(row["research_full_simulation_allowed"] is True, "PR168_RANK_RESEARCH_SIM", str(row))
    assert_true(row["future_hot_path_full_research_recompute_allowed"] is False, "PR168_RANK_HOT_PATH_RECOMPUTE", str(row))
    assert_true(row["future_hot_path_cache_keys_must_not_create_sha_authority"] is True, "PR168_RANK_HOT_PATH_SHA", str(row))


def validate_generic() -> None:
    validate_reports_exist()
    validate_input_consumption()
    validate_no_fake_ranking()
    validate_score_math()
    validate_pretrade_order_simulation()
    validate_order_decision_tournament()
    validate_no_trade_dominance()
    validate_quantum_structural()
    validate_registry_rows()
    validate_no_orphan()
    validate_authority_boundaries()
    validate_materialized_artifacts()
    validate_scope_registry()
    validate_final_summary()
    validate_connector_routing()
    validate_two_speed()


VALIDATORS: dict[str, Callable[[], None]] = {
    "input_consumption": validate_input_consumption,
    "no_fake_ranking": validate_no_fake_ranking,
    "score_math": validate_score_math,
    "binary_prediction_market_pnl": validate_binary_prediction_market_pnl,
    "candidate_stack_generation": validate_candidate_stack_generation,
    "mode_policy_matrix": lambda: assert_true(bool(load("PR168_RANK_ModeScopedDecisionPolicyMatrix.report.json")), "PR168_RANK_MODE_EMPTY", "mode policy rows required"),
    "pretrade_order_simulation": validate_pretrade_order_simulation,
    "order_decision_tournament": validate_order_decision_tournament,
    "tca_decomposition": lambda: assert_true(bool(load("PR168_RANK_TCADecompositionUsed.report.json")), "PR168_RANK_TCA_EMPTY", "TCA rows required"),
    "champion_challenger": validate_no_fake_ranking,
    "no_trade_dominance": validate_no_trade_dominance,
    "overfit_fdr": lambda: assert_true(bool(load("PR168_RANK_OverfitFDRRankingPenalty.report.json")), "PR168_RANK_OVERFIT_EMPTY", "overfit rows required"),
    "regime_ranking": lambda: assert_true(bool(load("PR168_RANK_RegimeConditionedRanking.report.json")), "PR168_RANK_REGIME_EMPTY", "regime rows required"),
    "portfolio_ranking": lambda: assert_true(bool(load("PR168_RANK_PortfolioAwareRanking.report.json")), "PR168_RANK_PORTFOLIO_EMPTY", "portfolio rows required"),
    "capacity_crowding": lambda: assert_true(bool(load("PR168_RANK_CapacityCrowdingRankingPenalty.report.json")), "PR168_RANK_CAPACITY_EMPTY", "capacity rows required"),
    "quantum_structural_ranking": validate_quantum_structural,
    "quantum_combinatorial_selection": validate_quantum_structural,
    "latency_hot_path_seed": validate_two_speed,
    "agent_work_orders": lambda: assert_true(bool(load("PR168_RANK_AgentWorkOrders.report.json")), "PR168_RANK_AGENT_EMPTY", "agent rows required"),
    "downstream_orchestration": validate_no_orphan,
    "dag_orchestration": validate_no_orphan,
    "no_orphan": validate_no_orphan,
    "authority_boundaries": validate_authority_boundaries,
    "validation_scope_registry_integration": validate_scope_registry,
    "centralized_systems_coverage": lambda: assert_true(bool(load("PR168_RANK_CentralizedSystemsCoverageAudit.report.json")), "PR168_RANK_CENTRAL_EMPTY", "coverage rows required"),
    "edge_capture_attribution": lambda: assert_true(bool(load("PR168_RANK_EdgeCaptureAttributionLedger.report.json")), "PR168_RANK_EDGE_CAPTURE_EMPTY", "edge rows required"),
    "negative_recovery_tournament": lambda: assert_true(bool(load("PR168_RANK_NegativeRecoveryTournament.report.json")), "PR168_RANK_NEG_RECOVERY_EMPTY", "negative recovery rows required"),
    "threshold_surfaces": lambda: assert_true(bool(load("PR168_RANK_OrderDecisionThresholdSurface.report.json")), "PR168_RANK_THRESHOLD_EMPTY", "threshold rows required"),
    "maker_taker_tradeoff": lambda: assert_true(bool(load("PR168_RANK_MakerTakerAdverseSelectionTradeoff.report.json")), "PR168_RANK_MAKER_TAKER_EMPTY", "maker/taker rows required"),
    "size_price_time_sensitivity": lambda: assert_true(bool(load("PR168_RANK_SizePriceTimeSensitivityLadder.report.json")), "PR168_RANK_SPT_EMPTY", "size/price/time rows required"),
    "scenario_stress_surface": lambda: assert_true(bool(load("PR168_RANK_ScenarioStressOrderSurface.report.json")), "PR168_RANK_SCENARIO_STRESS_EMPTY", "scenario stress rows required"),
    "materialized_artifacts_not_blueprints": validate_materialized_artifacts,
    "scalar_value_no_orphan": lambda: assert_true(bool(load("PR168_RANK_ScalarValueNoOrphanProof.report.json")), "PR168_RANK_SCALAR_EMPTY", "scalar rows required"),
    "terminal_artifact_lifecycle": validate_terminal_lifecycle,
    "connector_candidate_routing": validate_connector_routing,
    "two_speed_decision_surface": validate_two_speed,
    "future_expansion_registries": validate_registry_rows,
    "market_adapter_registry_seed": validate_registry_rows,
    "venue_cost_model_registry_seed": validate_registry_rows,
    "contract_payoff_model_registry_seed": validate_registry_rows,
    "formula_algorithm_plugin_registry_seed": validate_registry_rows,
    "quantum_objective_registry_seed": validate_registry_rows,
    "order_policy_registry_seed": validate_registry_rows,
    "agent_capability_registry_seed": validate_registry_rows,
    "connector_readiness_registry_seed": validate_registry_rows,
    "runtime_allowlist_seed_registry": validate_registry_rows,
    "hot_path_decision_surface_registry": validate_registry_rows,
    "registry_seed_no_orphan": validate_registry_rows,
    "registry_anti_scatter": lambda: assert_true(bool(load("PR168_RANK_RegistryAntiScatterAudit.report.json")), "PR168_RANK_ANTI_SCATTER_EMPTY", "anti-scatter rows required"),
}


def run_validation(mode: str) -> None:
    key = mode
    if key.startswith("validate_pr168_rank_"):
        key = key.removeprefix("validate_pr168_rank_")
    if key.endswith(".py"):
        key = key[:-3]
    validator = VALIDATORS.get(key, validate_generic)
    validator()
    print(f"PR168_RANK_VALIDATION_OK {key}")


def main(script_name: str | None = None) -> int:
    mode = script_name or Path(sys.argv[0]).stem
    run_validation(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
