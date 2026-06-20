#!/usr/bin/env python3
"""Shared validators for PR168-RP generated artifacts."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp_compute_kernel import BASELINE_COUNTS, REQUIRED_REPORTS
from tools.pr168_rp_evidence_state_machine import COMPUTED_STATUSES, EVIDENCE_TIERS
from tools.pr168_rp_order_candidate_factory import ORDER_POLICIES
from tools.pr168_rp_report_writer import GENERATED_DIR, read_records, read_report
from tools.qtt_authority_reason_code_registry import (
    get_gap_reason_code,
    get_negative_recovery_reason_code,
    validate_no_scattered_authority_wording,
)
from tools.validation_scope_registry import (
    PR168_RP_BRANCH,
    is_pr_scoped_changed_path_allowed,
)


NUMERIC_EVIDENCE_FIELDS = {
    "market_implied_probability",
    "predicted_probability",
    "gross_edge",
    "expected_value",
    "explicit_fee_cost",
    "spread_cost",
    "slippage_cost",
    "market_impact",
    "adverse_selection_penalty",
    "implementation_shortfall",
    "latency_decay",
    "queue_nonfill_penalty",
    "partial_fill_penalty",
    "stale_orderbook_penalty",
    "capacity_crowding_penalty",
    "overfit_fdr_penalty",
    "execution_adjusted_edge",
    "fill_adjusted_expected_pnl",
    "position_size",
    "net_expected_pnl_candidate",
    "lower_confidence_bound_edge",
}

FORBIDDEN_GENERATED_STRINGS = (
    "formula_" + "bundle",
    "formula_" + "bundle_id",
    "formula_" + "bundle_refs",
    "bundle" + "-only coverage",
    "AtomicRows.bundle" + ".sha256",
)


def load(filename: str) -> list[dict[str, Any]]:
    return read_records(REPO_ROOT, filename)


def load_root(filename: str) -> dict[str, Any]:
    return read_report(REPO_ROOT, filename)


def assert_true(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{code}: {message}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _walk_values(value: Any) -> Any:
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_values(child)
    else:
        yield value


def _metrics(row: dict[str, Any]) -> dict[str, Any]:
    nested = row.get("metrics")
    if isinstance(nested, dict):
        return nested
    return row


def validate_reports_exist() -> None:
    missing = [filename for filename in REQUIRED_REPORTS if not (REPO_ROOT / GENERATED_DIR / filename).exists()]
    assert_true(not missing, "PR168_RP_MISSING_REPORTS", f"missing required reports: {missing[:10]}")
    for filename in REQUIRED_REPORTS:
        root = load_root(filename)
        for key in (
            "producer",
            "consumer",
            "upstream_source",
            "downstream_route",
            "owning_agent",
            "no_orphan_status",
        ):
            assert_true(key in root, "PR168_RP_REPORT_METADATA_MISSING", f"{filename} missing top-level {key}")
        assert_true(root.get("live_authority") is False, "PR168_RP_LIVE_AUTHORITY_CREATED", filename)
        assert_true(root.get("connector_truth_authority") is False, "PR168_RP_CONNECTOR_AUTHORITY_CREATED", filename)
        assert_true(root.get("source_truth_authority") is False, "PR168_RP_SOURCE_AUTHORITY_CREATED", filename)
        assert_true(root.get("generated_digest_authority_created") is False, "PR168_RP_DIGEST_AUTHORITY_CREATED", filename)


def validate_universe() -> None:
    final_summary = load("PR168_RP_FinalSummary.report.json")
    assert_true(len(final_summary) == 1, "PR168_RP_FINAL_SUMMARY_COUNT", "final summary must have one row")
    row = final_summary[0]
    assert_true(
        row["baseline_counts"] == BASELINE_COUNTS,
        "PR168_RP_BASELINE_COUNTS",
        f"unexpected baseline counts: {row['baseline_counts']}",
    )
    assert_true(
        row["formula_assignment_rows_consumed"] == BASELINE_COUNTS["formula_assignment_rows"],
        "PR168_RP_ASSIGNMENT_COUNT",
        "formula assignment universe was not fully consumed",
    )
    availability = load("PR168_RP_InputAvailabilityMatrix.report.json")
    assert_true(
        len(availability) == BASELINE_COUNTS["formula_assignment_rows"],
        "PR168_RP_AVAILABILITY_COUNT",
        f"expected 20387 availability rows, got {len(availability)}",
    )
    for item in availability:
        assert_true(item.get("evidence_tier") in EVIDENCE_TIERS, "PR168_RP_UNKNOWN_EVIDENCE_TIER", str(item.get("evidence_tier")))
        assert_true(item.get("computed_status") in COMPUTED_STATUSES, "PR168_RP_UNKNOWN_STATUS", str(item.get("computed_status")))


def validate_formula_execution() -> None:
    computed = load("PR168_RP_ComputedPnLEvidence.report.json")
    gaps = load("PR168_RP_ActionableInputGapQueue.report.json")
    assert_true(computed or gaps, "PR168_RP_NO_CLASSIFIED_ROWS", "no computed rows and no gaps")
    for row in computed:
        assert_true(row.get("input_ref"), "PR168_RP_COMPUTED_INPUT_REF_MISSING", str(row.get("result_ref")))
        assert_true(row.get("output_ref"), "PR168_RP_COMPUTED_OUTPUT_REF_MISSING", str(row.get("result_ref")))
        assert_true(row.get("result_ref"), "PR168_RP_COMPUTED_RESULT_REF_MISSING", str(row.get("canonical_row_key")))
        metrics = _metrics(row)
        missing = sorted(field for field in NUMERIC_EVIDENCE_FIELDS if not _is_number(metrics.get(field)))
        assert_true(not missing, "PR168_RP_NUMERIC_EVIDENCE_MISSING", f"{row.get('result_ref')} missing {missing}")
        assert_true(row.get("computed_status") != "COMPUTED_POSITIVE_EDGE" or metrics.get("positive_negative_decision") is True, "PR168_RP_FAKE_POSITIVE", str(row.get("result_ref")))
    for gap in gaps:
        assert_true(gap.get("missing_variables"), "PR168_RP_INPUT_GAP_WITHOUT_VARIABLES", str(gap.get("result_ref")))
        get_gap_reason_code(str(gap.get("gap_reason_code")))


def validate_replay_paper_results() -> None:
    replay = load("PR168_RP_ComputedReplayResults.report.json")
    paper = load("PR168_RP_ComputedPaperResults.report.json")
    comparison = load("PR168_RP_ReplayPaperComparison.report.json")
    computed = load("PR168_RP_ComputedPnLEvidence.report.json")
    assert_true(len(replay) == len(computed), "PR168_RP_REPLAY_RESULT_COUNT", "replay rows must match computed rows")
    assert_true(len(paper) == len(computed), "PR168_RP_PAPER_RESULT_COUNT", "paper rows must match computed rows")
    assert_true(len(comparison) == len(computed), "PR168_RP_COMPARISON_COUNT", "comparison rows must match computed rows")


def validate_tca_math() -> None:
    rows = load("PR168_RP_ComputedPnLEvidence.report.json")
    for row in rows:
        metrics = _metrics(row)
        costs = sum(float(metrics[field]) for field in [
            "explicit_fee_cost",
            "spread_cost",
            "slippage_cost",
            "market_impact",
            "adverse_selection_penalty",
            "implementation_shortfall",
            "latency_decay",
            "queue_nonfill_penalty",
            "partial_fill_penalty",
            "stale_orderbook_penalty",
            "capacity_crowding_penalty",
            "overfit_fdr_penalty",
        ])
        expected_edge = float(metrics["gross_edge"]) - costs
        assert_true(
            abs(float(metrics["execution_adjusted_edge"]) - expected_edge) < 1e-8,
            "PR168_RP_EXECUTION_ADJUSTED_EDGE_MATH",
            str(row["result_ref"]),
        )
        expected_net = float(metrics["position_size"]) * float(metrics["execution_adjusted_edge"])
        assert_true(
            abs(float(metrics["net_expected_pnl_candidate"]) - expected_net) < 1e-8,
            "PR168_RP_NET_PNL_MATH",
            str(row["result_ref"]),
        )


def validate_microstructure() -> None:
    rows = load("PR168_RP_PredictionMarketMicrostructureFeatures.report.json")
    for row in rows:
        for field in ("top_of_book_bid", "top_of_book_ask", "midpoint", "spread", "fill_probability", "order_quantity"):
            assert_true(_is_number(row.get(field)), "PR168_RP_MICROSTRUCTURE_NUMERIC_MISSING", f"{row.get('result_ref')} {field}")
        assert_true(0 <= float(row["fill_probability"]) <= 1, "PR168_RP_FILL_PROBABILITY_RANGE", str(row.get("result_ref")))
        assert_true(float(row["spread"]) >= 0, "PR168_RP_NEGATIVE_SPREAD", str(row.get("result_ref")))


def validate_pretrade() -> None:
    computed = load("PR168_RP_ComputedPnLEvidence.report.json")
    pretrade = load("PR168_RP_PreTradeSimulationCandidates.report.json")
    ranking = load("PR168_RP_OrderPolicyCandidateRanking.report.json")
    no_trade = load("PR168_RP_NoTradeCandidateComparison.report.json")
    latency = load("PR168_RP_LatencyBudgetResults.report.json")
    scenarios = load("PR168_RP_ScenarioLadderResults.report.json")
    assert_true(len(pretrade) == len(computed) * len(ORDER_POLICIES), "PR168_RP_PRETRADE_COUNT", "each computed row needs all order policies")
    assert_true(len(ranking) == len(pretrade), "PR168_RP_ORDER_RANKING_COUNT", "ranking rows must match candidates")
    assert_true(len(no_trade) == len(pretrade), "PR168_RP_NO_TRADE_COUNT", "no-trade comparison rows must match candidates")
    assert_true(len(latency) == len(pretrade), "PR168_RP_LATENCY_COUNT", "latency rows must match candidates")
    assert_true(len(scenarios) == len(computed), "PR168_RP_SCENARIO_COUNT", "scenario rows must match computed rows")
    no_trade_rows = [row for row in pretrade if row.get("order_type_candidate") == "NO_TRADE_CANDIDATE"]
    assert_true(len(no_trade_rows) == len(computed), "PR168_RP_NO_TRADE_CANDIDATE_MISSING", "one no-trade candidate required per computed row")
    for row in pretrade:
        assert_true(row.get("live_authority") is False, "PR168_RP_PRETRADE_LIVE_AUTHORITY", str(row.get("candidate_id")))
        assert_true(row.get("connector_semantic_binding_state") == "NOT_BOUND_CANDIDATE_ONLY", "PR168_RP_PRETRADE_CONNECTOR_BOUND", str(row.get("candidate_id")))
        assert_true(row.get("computed_formula_output_ref"), "PR168_RP_PRETRADE_NO_OUTPUT_REF", str(row.get("candidate_id")))


def validate_negative_recovery() -> None:
    negative = load("PR168_RP_ComputedNegativeEdgeCandidates.report.json")
    attempts = load("PR168_RP_NegativeToPositiveRecoveryAttempts.report.json")
    assert_true(len(attempts) == len(negative), "PR168_RP_NEGATIVE_RECOVERY_COUNT", "each negative row needs recovery attempt")
    by_ref = {row["negative_recovery_ref"]: row for row in attempts}
    for row in negative:
        ref = row.get("negative_recovery_ref")
        assert_true(ref in by_ref, "PR168_RP_NEGATIVE_RECOVERY_REF_MISSING", str(row.get("result_ref")))
    for attempt in attempts:
        for reason in attempt.get("failure_reason_codes", []):
            get_negative_recovery_reason_code(str(reason))
        assert_true(
            attempt.get("repaired_positive_status") != "REPAIRED_COMPUTED_POSITIVE_EDGE",
            "PR168_RP_FORCED_REPAIRED_POSITIVE",
            str(attempt.get("negative_recovery_ref")),
        )


def validate_quantum() -> None:
    rows = load("PR168_RP_QuantumStructuralReadiness.report.json")
    for row in rows:
        assert_true(row.get("quantum_backend_execution_count") == 0, "PR168_RP_QUANTUM_BACKEND_EXECUTED", str(row.get("quantum_readiness_ref")))
        assert_true(row.get("quantum_advantage_claim_count") == 0, "PR168_RP_QUANTUM_ADVANTAGE_CLAIM_COUNT", str(row.get("quantum_readiness_ref")))
        assert_true(row.get("quantum_advantage_claim", False) is False, "PR168_RP_QUANTUM_ADVANTAGE_CLAIM", str(row.get("quantum_readiness_ref")))


def validate_connector() -> None:
    rows = load("PR168_RP_ConnectorCandidateRouteMap.report.json")
    for row in rows:
        assert_true(row.get("connector_semantic_binding_state") == "NOT_BOUND_CANDIDATE_ONLY", "PR168_RP_CONNECTOR_BOUND", str(row.get("connector_route_ref")))
        assert_true(row.get("connector_truth_authority") is False, "PR168_RP_CONNECTOR_TRUTH", str(row.get("connector_route_ref")))
        assert_true(row.get("live_authority") is False, "PR168_RP_CONNECTOR_LIVE", str(row.get("connector_route_ref")))


def validate_no_orphan() -> None:
    for filename in REQUIRED_REPORTS:
        for index, row in enumerate(load(filename), start=1):
            for key in ("producer", "consumer", "upstream_source", "downstream_route", "owning_agent", "no_orphan_status"):
                assert_true(key in row and row.get(key) not in ("", None), "PR168_RP_NO_ORPHAN_FIELD_MISSING", f"{filename} row {index} missing {key}")


def validate_dag() -> None:
    rows = load("PR168_RP_ArtifactInformationValueDAG.report.json")
    artifacts = {row.get("artifact_ref") for row in rows}
    for filename in REQUIRED_REPORTS:
        assert_true(filename in artifacts, "PR168_RP_ARTIFACT_DAG_MISSING", filename)


def validate_authority_boundaries() -> None:
    for filename in REQUIRED_REPORTS:
        root = load_root(filename)
        assert_true(root.get("order_authority") is False, "PR168_RP_ORDER_AUTHORITY_CREATED", filename)
        assert_true(root.get("private_state_read_count") == 0, "PR168_RP_PRIVATE_STATE_READ", filename)
        assert_true(root.get("runtime_cash_receipt_count") == 0, "PR168_RP_CASH_RECEIPT", filename)
        assert_true(root.get("quantum_backend_execution_count") == 0, "PR168_RP_QUANTUM_BACKEND_COUNT", filename)
        assert_true(root.get("llm_hot_path_authority") is False, "PR168_RP_LLM_HOT_PATH", filename)
    live_seed = load("PR168_RP_LivePreTradeDecisionGateSeed.report.json")
    assert_true(live_seed, "PR168_RP_LIVE_GATE_SEED_MISSING", "future gate seed is required")
    for row in live_seed:
        assert_true(row.get("live_authority_created_by_pr168_rp") is False, "PR168_RP_LIVE_GATE_AUTHORITY", str(row.get("gate_id")))
        assert_true(row.get("execution_router_required") is True, "PR168_RP_LIVE_GATE_ROUTER_REQUIREMENT", str(row.get("gate_id")))


def validate_compactness() -> None:
    for filename in REQUIRED_REPORTS:
        root = load_root(filename)
        root_count = len(root.get("records", []))
        record_count = int(root.get("record_count", root_count))
        if record_count > 1000:
            assert_true(root_count <= 5, "PR168_RP_ROOT_NOT_COMPACT", filename)
            assert_true(root.get("summary", {}).get("sharded_flag") is True, "PR168_RP_SHARD_FLAG_MISSING", filename)


def validate_scope_registry() -> None:
    allowed = [
        "tools/pr168_rp_compute_kernel.py",
        "tools/validate_pr168_rp_formula_execution.py",
        "docs/master_plan/generated/PR168_RP_FinalSummary.report.json",
        "docs/master_plan/generated/pr168_rp_shards/PR168_RP_ComputedPnLEvidence.part_0001_of_0001.report.json",
        "tests/pr168_rp/test_formula_execution.py",
    ]
    rejected = ["docs/master_plan/generated/PR168_GFP_AuthoritativeTruthOverlay.report.json", "docs/master_plan/QTT_MasterPlan_Current.md"]
    for path in allowed:
        assert_true(is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path), "PR168_RP_SCOPE_REJECTED_ALLOWED_PATH", path)
    for path in rejected:
        assert_true(not is_pr_scoped_changed_path_allowed(PR168_RP_BRANCH, path), "PR168_RP_SCOPE_ALLOWED_REJECTED_PATH", path)


def validate_windows_linux() -> None:
    reports = list((REPO_ROOT / GENERATED_DIR).glob("PR168_RP_*.report.json"))
    reports += list((REPO_ROOT / GENERATED_DIR / "pr168_rp_shards").glob("PR168_RP_*.report.json"))
    lowered: dict[str, Path] = {}
    for path in reports:
        key = path.relative_to(REPO_ROOT).as_posix().lower()
        assert_true(key not in lowered, "PR168_RP_PATH_CASE_COLLISION", f"{path} collides with {lowered.get(key)}")
        lowered[key] = path
        payload = json.loads(path.read_text(encoding="utf-8"))
        for value in _walk_values(payload):
            if isinstance(value, float):
                assert_true(math.isfinite(value), "PR168_RP_NONFINITE_JSON_NUMBER", str(path))


def validate_no_metadata_only() -> None:
    computed = load("PR168_RP_ComputedPnLEvidence.report.json")
    pretrade = load("PR168_RP_PreTradeSimulationCandidates.report.json")
    attempts = load("PR168_RP_NegativeToPositiveRecoveryAttempts.report.json")
    assert_true(computed, "PR168_RP_METADATA_ONLY_NO_COMPUTED_ROWS", "numeric computed rows are required where repo inputs exist")
    assert_true(pretrade, "PR168_RP_METADATA_ONLY_NO_PRETRADE_ROWS", "pretrade simulation rows are required")
    assert_true(attempts, "PR168_RP_METADATA_ONLY_NO_RECOVERY_ROWS", "negative recovery rows are required")


def validate_no_fake_labels() -> None:
    for row in load("PR168_RP_ComputedPositiveEdgeCandidates.report.json"):
        metrics = _metrics(row)
        assert_true(metrics.get("positive_negative_decision") is True, "PR168_RP_POSITIVE_WITHOUT_DECISION", str(row.get("result_ref")))
        assert_true(_is_number(metrics.get("net_expected_pnl_candidate")), "PR168_RP_POSITIVE_WITHOUT_NUMERIC_PNL", str(row.get("result_ref")))
    for row in load("PR168_RP_ComputedNegativeEdgeCandidates.report.json"):
        assert_true(row.get("computed_status") == "COMPUTED_NEGATIVE_EDGE", "PR168_RP_NEGATIVE_LABEL_INHERITED", str(row.get("result_ref")))


def validate_scattered_wording() -> None:
    scan_paths = [
        REPO_ROOT / "tools/pr168_rp_compute_kernel.py",
        REPO_ROOT / "tools/pr168_rp_report_writer.py",
    ]
    for path in scan_paths:
        result = validate_no_scattered_authority_wording(str(path))
        assert_true(result["status"] == "PASS", "PR168_RP_SCATTERED_AUTHORITY_WORDING", f"{path}: {result.get('findings', [])}")


def validate_forbidden_terms() -> None:
    for filename in REQUIRED_REPORTS:
        text = (REPO_ROOT / GENERATED_DIR / filename).read_text(encoding="utf-8")
        for term in FORBIDDEN_GENERATED_STRINGS:
            assert_true(term not in text, "PR168_RP_FORBIDDEN_TERM", f"{filename}: {term}")


def validate_strict_input_consumption() -> None:
    rows = load("PR168_RP_StrictInputConsumptionLedger.report.json")
    assert_true(rows, "PR168_RP_INPUT_LEDGER_EMPTY", "strict input ledger is required")
    for row in rows:
        assert_true(row.get("read_status") != "SILENTLY_SKIPPED", "PR168_RP_SILENT_UPSTREAM_SKIP", str(row.get("upstream_input")))
        assert_true(row.get("processed_status") in {"PROCESSED", "ABSENT_GAP_ROUTED", "CATEGORY_DISCOVERY_PROCESSED"}, "PR168_RP_BAD_UPSTREAM_STATUS", str(row))
        assert_true(row.get("downstream_outputs_created"), "PR168_RP_UPSTREAM_NO_DOWNSTREAM_OUTPUT", str(row.get("upstream_input")))


def validate_generic() -> None:
    validate_reports_exist()
    validate_universe()
    validate_formula_execution()
    validate_replay_paper_results()
    validate_tca_math()
    validate_microstructure()
    validate_pretrade()
    validate_negative_recovery()
    validate_quantum()
    validate_connector()
    validate_no_orphan()
    validate_dag()
    validate_authority_boundaries()
    validate_compactness()
    validate_scope_registry()
    validate_windows_linux()
    validate_no_metadata_only()
    validate_no_fake_labels()
    validate_forbidden_terms()
    validate_strict_input_consumption()


VALIDATORS: dict[str, Callable[[], None]] = {
    "formula_execution": lambda: (validate_reports_exist(), validate_universe(), validate_formula_execution()),
    "replay_paper_results": lambda: (validate_replay_paper_results(), validate_formula_execution()),
    "no_fake_computed_labels": validate_no_fake_labels,
    "tca_pnl_math": validate_tca_math,
    "microstructure_fill_model": validate_microstructure,
    "pretrade_simulation_kernel": validate_pretrade,
    "order_policy_candidate_ranking": validate_pretrade,
    "no_trade_candidate": validate_pretrade,
    "scenario_ladder": validate_pretrade,
    "latency_budget": validate_pretrade,
    "live_candidate_handoff_no_order_authority": validate_authority_boundaries,
    "probability_calibration": lambda: assert_true(bool(load("PR168_RP_ProbabilityCalibration.report.json")), "PR168_RP_PROBABILITY_CALIBRATION_EMPTY", "probability calibration rows required"),
    "overfit_fdr": lambda: assert_true(bool(load("PR168_RP_OverfitFDRResults.report.json")), "PR168_RP_OVERFIT_EMPTY", "overfit/FDR rows required"),
    "quantum_objective_recompute": validate_quantum,
    "quantum_structural_readiness": validate_quantum,
    "portfolio_marginal_utility": lambda: assert_true(bool(load("PR168_RP_PortfolioMarginalUtilityResults.report.json")), "PR168_RP_PORTFOLIO_EMPTY", "portfolio rows required"),
    "capacity_crowding": lambda: assert_true(bool(load("PR168_RP_CapacityCrowdingResults.report.json")), "PR168_RP_CAPACITY_EMPTY", "capacity rows required"),
    "regime_memory": lambda: assert_true(bool(load("PR168_RP_RegimeConditionedMemorySeed.report.json")), "PR168_RP_REGIME_EMPTY", "regime rows required"),
    "champion_challenger": lambda: assert_true(bool(load("PR168_RP_ChampionChallengerEligibility.report.json")), "PR168_RP_CHAMPION_ROWS_EMPTY", "champion/challenger rows required"),
    "combination_selection": lambda: assert_true(bool(load("PR168_RP_QKUCombinationCandidateResults.report.json")), "PR168_RP_COMBINATION_EMPTY", "combination rows required"),
    "negative_recovery": validate_negative_recovery,
    "edge_attribution": lambda: assert_true(bool(load("PR168_RP_EdgeAttribution.report.json")), "PR168_RP_EDGE_ATTRIBUTION_EMPTY", "edge attribution rows required"),
    "agent_duty_orchestration": lambda: assert_true(bool(load("PR168_RP_AgentDutyOrchestrationCrosswalk.report.json")), "PR168_RP_AGENT_DUTY_EMPTY", "agent duty rows required"),
    "connector_candidate_routing": validate_connector,
    "strict_input_consumption": validate_strict_input_consumption,
    "no_orphan_lineage": validate_no_orphan,
    "artifact_information_value_dag": validate_dag,
    "authority_boundaries": validate_authority_boundaries,
    "report_compactness": validate_compactness,
    "validation_scope_registry_integration": validate_scope_registry,
    "windows_linux_compatibility": validate_windows_linux,
    "no_metadata_only_pass": validate_no_metadata_only,
    "no_forced_negative_to_positive": validate_negative_recovery,
    "no_scattered_authority_wording": validate_scattered_wording,
}


def run_validation(mode: str) -> None:
    key = mode
    if key.startswith("validate_pr168_rp_"):
        key = key.removeprefix("validate_pr168_rp_")
    if key.endswith(".py"):
        key = key[:-3]
    validator = VALIDATORS.get(key)
    if validator is None:
        validate_generic()
    else:
        validator()
    validate_forbidden_terms()
    print(f"PR168_RP_VALIDATION_OK {key}")


def main(script_name: str | None = None) -> int:
    mode = script_name or Path(sys.argv[0]).stem
    run_validation(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
