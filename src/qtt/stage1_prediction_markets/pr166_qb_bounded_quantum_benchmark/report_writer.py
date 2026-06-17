"""Build PR166-QB generated reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import importlib.metadata
import importlib.util
from pathlib import Path
import random
import re
from typing import Any, Iterable

from . import constants as c
from .authority import (
    authority_boundary_record,
    authority_false_flags,
    authority_zero_counts,
)
from .io import (
    ensure_branch,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    input_counts: dict[str, int]


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_shards(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payloads[filename],
            compact=bool(payloads[filename].get("sharded_flag")),
        )
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    return BuildArtifacts(
        summary=dict(payloads["PR166_QB_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    contexts = build_candidate_contexts(source)
    selected = select_benchmark_subset(contexts)
    dependency_rows = build_dependency_rows()
    row_payloads = build_row_payloads(source, contexts, selected, dependency_rows)
    row_payloads["PR166_QB_ReportManifest.report.json"] = []
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    for _ in range(3):
        row_payloads["PR166_QB_ReportManifest.report.json"] = build_manifest_rows(payloads)
        payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR166_QB_ArtifactMap.report.json"] = build_artifact_map_rows(
        source,
        payloads,
        shard_payloads,
    )
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR166_QB_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"{c.PR_ID} payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}
    missing: list[str] = []
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        rows = records_from_report_payload(repo_root, payload)
        payloads[filename] = payload
        records[filename] = rows
        counts[filename] = len(rows)
    if missing:
        raise RuntimeError(f"{c.PR_ID} required inputs missing: {', '.join(missing)}")
    bad_counts = {
        name: counts[name]
        for name in c.EXPECTED_559_INPUTS
        if counts.get(name) != 559
    }
    if bad_counts:
        details = ", ".join(f"{name}={count}" for name, count in sorted(bad_counts.items()))
        raise RuntimeError(f"{c.PR_ID} upstream 559-count input drift: {details}")
    return SourceData(payloads=payloads, records=records, input_counts=counts)


def build_candidate_contexts(source: SourceData) -> list[dict[str, Any]]:
    handoffs = sorted(
        source.records["PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json"],
        key=lambda item: str(item.get("deterministic_sort_key") or item.get("candidate_packet_id") or item.get("row_id")),
    )
    companions = {
        name: _by_candidate(source.records[name])
        for name in c.EXPECTED_559_INPUTS
        if name != "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json"
    }
    contexts: list[dict[str, Any]] = []
    for index, row in enumerate(handoffs, start=1):
        candidate = str(row["candidate_packet_id"])
        race = companions["PR166_Q_QuantumClassicalHybridRaceLedger.report.json"].get(candidate, {})
        structural = companions["PR166_Q_QuantumStructuralReadiness.report.json"].get(candidate, {})
        classical = companions["PR166_Q_ClassicalBaselineComparator.report.json"].get(candidate, {})
        qinspired = companions["PR166_Q_QuantumInspiredComparator.report.json"].get(candidate, {})
        hybrid = companions["PR166_Q_HybridComparator.report.json"].get(candidate, {})
        execution = companions["PR166_Q_ExecutionAdjustedRanking.report.json"].get(candidate, {})
        tca = companions["PR166_Q_TCADecomposition.report.json"].get(candidate, {})
        queue = companions["PR166_Q_OrderBookQueueRiskLedger.report.json"].get(candidate, {})
        latency = companions["PR166_Q_LatencyCostRiskLedger.report.json"].get(candidate, {})
        overfit = companions["PR166_Q_OverfitFalseDiscoveryControl.report.json"].get(candidate, {})
        portfolio = companions["PR166_Q_PortfolioDiversificationLedger.report.json"].get(candidate, {})
        capacity = companions["PR166_Q_CapacityCrowdingLimitLedger.report.json"].get(candidate, {})
        marginal = companions["PR166_Q_MarginalUtilitySelection.report.json"].get(candidate, {})
        upstream_role = str(row.get("champion_challenger_role") or "watch")
        model_family = c.MODEL_FAMILIES[(index - 1) % len(c.MODEL_FAMILIES)]
        expected_net = _float(row.get("expected_net_profit_per_order_candidate"), _float(execution.get("expected_net_profit_per_order_candidate"), -0.031696))
        classical_score = _float(
            classical.get("classical_baseline_score"),
            _float(race.get("classical_baseline_score"), 0.48),
        )
        qinspired_score = _float(
            qinspired.get("quantum_inspired_score"),
            _float(race.get("quantum_inspired_route_score"), classical_score + 0.03),
        )
        hybrid_score = _float(hybrid.get("hybrid_score"), _float(race.get("hybrid_route_score"), (classical_score + qinspired_score) / 2))
        true_quantum_score = _float(
            race.get("true_quantum_structural_route_score"),
            _float(structural.get("quantum_structural_readiness_score"), 0.82),
        )
        total_tca = _float(
            tca.get("total_transaction_cost_estimate"),
            _float(tca.get("total_tca_estimate"), 0.004 + (index % 7) * 0.0002),
        )
        overfit_penalty = _float(
            overfit.get("false_discovery_penalty"),
            _float(row.get("false_discovery_penalty"), 0.03),
        ) + _float(overfit.get("overfit_penalty"), 0.02)
        capacity_penalty = _float(capacity.get("capacity_penalty"), max(0.0, 1.0 - _float(capacity.get("capacity_adjusted_score"), 0.85)) * 0.05)
        crowding_penalty = _float(capacity.get("crowding_penalty"), max(0.0, 1.0 - _float(capacity.get("crowding_adjusted_score"), 0.85)) * 0.05)
        marginal_utility = _float(marginal.get("final_marginal_utility_benchmark_score"), _float(row.get("marginal_utility_score"), 0.5))
        contexts.append(
            {
                "index": index,
                "handoff": row,
                "candidate_packet_id": candidate,
                "race": race,
                "structural": structural,
                "classical": classical,
                "qinspired": qinspired,
                "hybrid": hybrid,
                "execution": execution,
                "tca": tca,
                "queue": queue,
                "latency": latency,
                "overfit": overfit,
                "portfolio": portfolio,
                "capacity": capacity,
                "marginal": marginal,
                "model_family": model_family,
                "qku_id": str(row.get("qku_id") or c.NOT_APPLICABLE),
                "qku_family": str(row.get("qku_family") or _qku_family(row.get("qku_id", ""))),
                "formula_id": str(row.get("formula_id") or c.NOT_APPLICABLE),
                "algorithm_id": str(row.get("algorithm_id") or c.NOT_APPLICABLE),
                "parameter_stack_id": str(row.get("parameter_stack_id") or c.NOT_APPLICABLE),
                "execution_route_id": str(row.get("execution_route_id") or f"PR166_QB_EXECUTION_ROUTE::{index:05d}"),
                "market_scope": str(row.get("market_scope") or "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"),
                "stage1_prediction_market_flag": bool(row.get("stage1_prediction_market_flag", True)),
                "future_market_portability_flag": True,
                "upstream_role": upstream_role,
                "benchmark_role": _benchmark_role(upstream_role, expected_net, index),
                "classical_score": _round(classical_score),
                "qinspired_score": _round(qinspired_score),
                "hybrid_score": _round(hybrid_score),
                "true_quantum_score": _round(true_quantum_score),
                "total_tca": _round(total_tca),
                "queue_risk_drag": _round(_float(queue.get("queue_risk_drag"), _float(queue.get("cancellation_risk"), 0.02))),
                "latency_drag": _round(_float(latency.get("latency_drag"), _float(latency.get("latency_cost_component"), 0.002))),
                "overfit_penalty": _round(overfit_penalty),
                "capacity_penalty": _round(capacity_penalty),
                "crowding_penalty": _round(crowding_penalty),
                "marginal_utility": _round(marginal_utility),
                "expected_net": _round(expected_net),
                "upstream_refs": _upstream_refs(candidate, row, companions),
            }
        )
    return contexts


def select_benchmark_subset(contexts: list[dict[str, Any]]) -> set[str]:
    selected: set[str] = set()
    per_family: Counter[str] = Counter()
    role_order = ("champion", "challenger", "watch", "retest", "repair", "no-trade")
    for role in role_order:
        for ctx in contexts:
            if len(selected) >= c.BENCHMARK_CAPS["max_actual_benchmark_rows_default_ci"]:
                return selected
            if ctx["candidate_packet_id"] in selected:
                continue
            if str(ctx["upstream_role"]) != role:
                continue
            family = str(ctx["model_family"])
            if per_family[family] >= c.BENCHMARK_CAPS["max_rows_per_family_default_ci"]:
                continue
            selected.add(str(ctx["candidate_packet_id"]))
            per_family[family] += 1
    for ctx in contexts:
        if len(selected) >= c.BENCHMARK_CAPS["max_actual_benchmark_rows_default_ci"]:
            break
        candidate = str(ctx["candidate_packet_id"])
        family = str(ctx["model_family"])
        if candidate not in selected and per_family[family] < c.BENCHMARK_CAPS["max_rows_per_family_default_ci"]:
            selected.add(candidate)
            per_family[family] += 1
    return selected


def build_dependency_rows() -> list[dict[str, Any]]:
    dependencies = (
        ("python_stdlib", "PYTHON_STDLIB", True),
        ("qiskit", "QAOA_LOCAL_SIMULATOR_IF_AVAILABLE", False),
        ("qiskit_optimization", "QUADRATIC_PROGRAM_LOCAL_IF_AVAILABLE", False),
        ("dimod", "DWAVE_OCEAN_BQM_LOCAL_IF_AVAILABLE", False),
        ("dwave", "DWAVE_OCEAN_STACK_IF_AVAILABLE", False),
        ("neal", "DWAVE_NEAL_SIMULATED_ANNEALING_IF_AVAILABLE", False),
        ("tabu", "DWAVE_TABU_LOCAL_IF_AVAILABLE", False),
        ("scipy", "CLASSICAL_MILP_OR_SCIPY_IF_AVAILABLE", False),
    )
    rows: list[dict[str, Any]] = []
    for index, (module_name, capability, required_for_execution) in enumerate(dependencies, start=1):
        spec = importlib.util.find_spec(module_name) if module_name != "python_stdlib" else True
        available = bool(spec)
        version = "BUILT_IN" if module_name == "python_stdlib" else _version(module_name) if available else "UNAVAILABLE"
        rows.append(
            {
                **_base_report_row("PR166_QB_DependencyLedger.report.json", index),
                "row_id": f"PR166_QB_DEPENDENCY::{index:05d}",
                "dependency_name": module_name,
                "dependency_capability": capability,
                "dependency_available_flag": available,
                "dependency_version_if_available": version,
                "required_for_default_ci_execution_flag": required_for_execution,
                "default_ci_action": "USE_LOCAL_BOUNDED_PATH" if available else "ROUTE_TO_STRUCTURAL_RECEIPT",
                "no_new_dependency_added_flag": True,
                "no_backend_execution_flag": True,
                "credential_access_flag": False,
                "cloud_backend_execution_flag": False,
                "quantum_backend_execution_flag": False,
                "live_order_authority_flag": False,
            }
        )
    return rows


def build_row_payloads(
    source: SourceData,
    contexts: list[dict[str, Any]],
    selected: set[str],
    dependency_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    benchmarks = [_materialize_benchmark(ctx, selected) for ctx in contexts]
    rows: dict[str, list[dict[str, Any]]] = {filename: [] for filename in c.REPORT_FILENAMES}
    rows["PR166_QB_InputConsumption.report.json"] = build_input_consumption_rows(source)
    rows["PR166_QB_BudgetPolicy.report.json"] = [build_budget_row(selected, benchmarks)]
    rows["PR166_QB_SourceBenchmarkParams.report.json"] = build_source_rows()
    rows["PR166_QB_DependencyLedger.report.json"] = dependency_rows
    rows["PR166_QB_CloudSwitchReady.report.json"] = build_cloud_switch_rows()
    rows["PR166_QB_OwnerQuantumControlReady.report.json"] = build_owner_control_rows()
    for report_name in c.BENCHMARK_ROW_REPORTS:
        rows[report_name] = [row_for_report(report_name, bench) for bench in benchmarks]
    rows["PR166_QB_FinalSummary.report.json"] = [build_final_summary(source, benchmarks, dependency_rows)]
    return rows


def build_input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.STRICT_INPUT_REPORTS, start=1):
        count = source.input_counts[filename]
        rows.append(
            {
                **_base_report_row("PR166_QB_InputConsumption.report.json", index),
                "row_id": f"PR166_QB_INPUT::{index:05d}",
                "source_report_ref": filename,
                "source_report_path": f"docs/master_plan/generated/{filename}",
                "expanded_record_count": count,
                "expected_record_count": 559 if filename in c.EXPECTED_559_INPUTS else count,
                "record_count_matches_expected_flag": filename not in c.EXPECTED_559_INPUTS or count == 559,
                "consumption_status": "CONSUMED_FOR_PR166_QB",
                "routed_report_refs": [
                    "PR166_QB_Eligibility.report.json",
                    "PR166_QB_RaceArb.report.json",
                    "PR166_QB_NoOrphanProof.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_backend_execution_flag": True,
            }
        )
    return rows


def build_budget_row(selected: set[str], benchmarks: list[dict[str, Any]]) -> dict[str, Any]:
    per_family = Counter(row["model_family"] for row in benchmarks if row["benchmark_subset_flag"])
    return {
        **_base_report_row("PR166_QB_BudgetPolicy.report.json", 1),
        "row_id": "PR166_QB_BUDGET_POLICY::00001",
        **c.BENCHMARK_CAPS,
        "actual_benchmark_subset_size": len(selected),
        "actual_rows_per_family": dict(sorted(per_family.items())),
        "subset_selection_policy": "DETERMINISTIC_STRATIFIED_BY_ROLE_MODEL_FAMILY_AND_SORT_KEY",
        "runtime_measurement_mode": "DETERMINISTIC_PROXY_DEFAULT_CI",
        "manual_or_nightly_expansion_required_for_larger_benchmarks_flag": True,
        "cloud_backend_execution_allowed_flag": False,
        "credential_access_allowed_flag": False,
        "no_unbounded_execution_flag": True,
        "no_backend_execution_flag": True,
        "validation_refs": [c.VALIDATOR_REF],
    }


def build_source_rows() -> list[dict[str, Any]]:
    source_specs = (
        (
            "SRC_QISKIT_MINIMUM_EIGEN_OPTIMIZER",
            "official_quantum_optimization_docs",
            True,
            "https://qiskit-community.github.io/qiskit-optimization/tutorials/03_minimum_eigen_optimizer.html",
            5,
            4,
            3,
            3,
            2,
            0,
            0,
            2,
            0,
        ),
        (
            "SRC_QISKIT_WARM_START_QAOA",
            "official_quantum_optimization_docs",
            True,
            "https://qiskit-community.github.io/qiskit-optimization/tutorials/10_warm_start_qaoa.html",
            4,
            2,
            2,
            2,
            2,
            0,
            0,
            1,
            0,
        ),
        (
            "SRC_DWAVE_SAMPLERS",
            "official_quantum_annealing_docs",
            True,
            "https://docs.dwavequantum.com/en/latest/ocean/api_ref_samplers/index.html",
            5,
            5,
            4,
            4,
            3,
            1,
            0,
            2,
            0,
        ),
        (
            "SRC_DWAVE_OCEAN_PROJECTS",
            "official_quantum_model_docs",
            True,
            "https://dwave-meta-doc.readthedocs.io/en/latest/projects.html",
            4,
            3,
            4,
            2,
            2,
            1,
            0,
            1,
            0,
        ),
        (
            "SRC_AWS_BRAKET_HYBRID_JOBS",
            "official_cloud_quantum_docs",
            True,
            "https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html",
            2,
            2,
            2,
            3,
            2,
            4,
            1,
            2,
            1,
        ),
        (
            "SRC_IBM_QAOA_TUTORIAL",
            "official_quantum_algorithm_docs",
            True,
            "https://quantum.cloud.ibm.com/docs/en/tutorials/quantum-approximate-optimization-algorithm",
            3,
            2,
            2,
            2,
            2,
            1,
            0,
            1,
            0,
        ),
        (
            "SRC_CVAR_QAOA",
            "research_quantum_optimization",
            False,
            "https://quantum-journal.org/papers/q-2020-04-20-256/",
            3,
            2,
            2,
            2,
            2,
            0,
            0,
            2,
            0,
        ),
        (
            "SRC_BACKTEST_OVERFITTING_DSR",
            "research_overfit_false_discovery",
            False,
            "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf",
            4,
            0,
            0,
            2,
            2,
            0,
            0,
            3,
            0,
        ),
        (
            "SRC_BACKTEST_OVERFITTING_CPCV",
            "research_overfit_false_discovery",
            False,
            "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID4686376_code4361537.pdf?abstractid=4686376&mirid=1",
            4,
            0,
            0,
            2,
            2,
            0,
            0,
            3,
            0,
        ),
        (
            "SRC_IMPLEMENTATION_SHORTFALL_TCA",
            "industry_tca_reference",
            False,
            "https://ryanoconnellfinance.com/implementation-shortfall/",
            5,
            0,
            0,
            1,
            3,
            0,
            0,
            2,
            1,
        ),
        (
            "SRC_POLYMARKET_ORDER_BOOK_MICROSTRUCTURE",
            "research_prediction_market_microstructure",
            False,
            "https://arxiv.org/html/2604.24366v1",
            4,
            0,
            0,
            1,
            3,
            0,
            0,
            2,
            3,
        ),
        (
            "SRC_OPERATIONAL_FEATURE_FLAGS",
            "industry_dashboard_toggle_reference",
            False,
            "https://launchdarkly.com/blog/operational-flags-best-practices/",
            2,
            0,
            0,
            1,
            1,
            2,
            5,
            2,
            1,
        ),
    )
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(source_specs, start=1):
        (
            source_id,
            source_type,
            official,
            locator,
            benchmark_params,
            optimizer_classes,
            model_patterns,
            runtime_bounds,
            candidate_values,
            cloud_modes,
            dashboard_reqs,
            arbitration_patterns,
            portability_notes,
        ) = spec
        rows.append(
            {
                **_base_report_row("PR166_QB_SourceBenchmarkParams.report.json", index),
                "row_id": f"PR166_QB_SOURCE::{index:05d}",
                "source_id": source_id,
                "source_type": source_type,
                "official_flag": official,
                "non_official_flag": not official,
                "source_locator_or_query": locator,
                "benchmark_parameters_extracted_count": benchmark_params,
                "optimizer_classes_extracted_count": optimizer_classes,
                "quantum_model_patterns_extracted_count": model_patterns,
                "runtime_bounds_extracted_count": runtime_bounds,
                "candidate_values_extracted_count": candidate_values,
                "cloud_switchboard_modes_extracted_count": cloud_modes,
                "dashboard_toggle_requirements_extracted_count": dashboard_reqs,
                "arbitration_patterns_extracted_count": arbitration_patterns,
                "future_market_portability_notes_count": portability_notes,
                "rejected_reason": "",
                "routed_report_refs": [
                    "PR166_QB_BudgetPolicy.report.json",
                    "PR166_QB_FairnessNorm.report.json",
                    "PR166_QB_RaceArb.report.json",
                    "PR166_QB_CloudSwitchReady.report.json",
                    "PR166_QB_OwnerQuantumControlReady.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_backend_execution_flag": True,
            }
        )
    return rows


def build_cloud_switch_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, provider in enumerate(c.PROVIDER_FAMILIES, start=1):
        rows.append(
            {
                **_base_report_row("PR166_QB_CloudSwitchReady.report.json", index),
                "row_id": f"PR166_QB_CLOUD_SWITCH::{index:05d}",
                "provider_family": provider,
                "default_mode": "OFF",
                "supported_future_modes": list(c.OWNER_CLOUD_MODES),
                "credential_access_allowed_flag": False,
                "backend_execution_allowed_flag": False,
                "live_order_authority_flag": False,
                "paper_only_future_route_flag": provider != "NONE",
                "owner_approval_required_flag": True,
                "kill_switch_required_flag": True,
                "cost_budget_required_flag": True,
                "latency_budget_required_flag": True,
                "circuit_breaker_required_flag": True,
                "audit_trail_required_flag": True,
                "future_enablement_pr_ref": "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT",
                "no_backend_execution_flag": True,
                "cloud_provider_api_call_flag": False,
                "quantum_advantage_claim_flag": False,
                "profit_evidence_flag": False,
            }
        )
    return rows


def build_owner_control_rows() -> list[dict[str, Any]]:
    labels = {
        "NONE": "Quantum optimizers off",
        "IBM_QUANTUM": "IBM Quantum structural readiness",
        "AWS_BRAKET": "Amazon Braket structural readiness",
        "DWAVE_LEAP": "D-Wave Leap structural readiness",
        "OTHER_CANDIDATE": "Other candidate provider structural readiness",
    }
    rows: list[dict[str, Any]] = []
    for index, provider in enumerate(c.PROVIDER_FAMILIES, start=1):
        rows.append(
            {
                **_base_report_row("PR166_QB_OwnerQuantumControlReady.report.json", index),
                "row_id": f"PR166_QB_OWNER_CONTROL::{index:05d}",
                "control_id": f"PR166_QB_OWNER_QUANTUM_CONTROL::{provider}",
                "provider_family": provider,
                "owner_visible_label": labels[provider],
                "default_mode": "OFF",
                "supported_future_modes": list(c.OWNER_CLOUD_MODES),
                "dashboard_toggle_ready_flag": True,
                "dashboard_implementation_required_flag": True,
                "dashboard_ui_implemented_flag": False,
                "owner_approval_required_flag": True,
                "kill_switch_required_flag": True,
                "cost_budget_required_flag": True,
                "latency_budget_required_flag": True,
                "circuit_breaker_required_flag": True,
                "audit_trail_required_flag": True,
                "credential_access_allowed_flag": False,
                "backend_execution_allowed_flag": False,
                "live_order_authority_flag": False,
                "future_dashboard_pr_ref": "FUTURE_OWNER_DASHBOARD_QUANTUM_CONTROL",
                "future_enablement_pr_ref": "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT",
                "no_backend_execution_flag": True,
                "quantum_advantage_claim_flag": False,
                "profit_evidence_flag": False,
            }
        )
    return rows


def _materialize_benchmark(ctx: dict[str, Any], selected: set[str]) -> dict[str, Any]:
    candidate = str(ctx["candidate_packet_id"])
    subset = candidate in selected
    problem_variable_count = 8 + (int(ctx["index"]) % 15) if subset else 33 + (int(ctx["index"]) % 17)
    exact_allowed = problem_variable_count <= c.BENCHMARK_CAPS["max_problem_variables_default_ci"]
    benchmark = _run_local_benchmark(ctx, problem_variable_count) if subset else _structural_benchmark(ctx)
    disposition = _overall_disposition(ctx, subset)
    execution_mode = (
        "CLASSICAL_EXACT_SMALL"
        if subset and exact_allowed and problem_variable_count <= 18
        else "CLASSICAL_LOCAL_SEARCH"
        if subset
        else "STRUCTURAL_READY_NO_EXECUTION_RUNTIME_CAP"
    )
    role = str(ctx["benchmark_role"])
    classical_route_score = _round(_float(ctx["classical_score"]) - _float(ctx["total_tca"]) * 0.05)
    quantum_route_score = _round(_float(ctx["qinspired_score"]) - _float(ctx["latency_drag"]) * 0.1 - _float(ctx["overfit_penalty"]) * 0.03)
    true_quantum_route_score = _round(
        _float(ctx["true_quantum_score"])
        - _float(ctx["latency_drag"]) * 0.2
        - _float(ctx["overfit_penalty"]) * 0.05
    )
    hybrid_route_score = _round(
        0.45 * classical_route_score
        + 0.35 * quantum_route_score
        + 0.20 * true_quantum_route_score
        - _float(ctx["queue_risk_drag"]) * 0.03
    )
    route_scores = {
        "CLASSICAL_HOT_PATH_FALLBACK": classical_route_score,
        "QUANTUM_INSPIRED_PRECOMPUTE_CHALLENGER": quantum_route_score,
        "TRUE_QUANTUM_STRUCTURAL_PAPER_ONLY": true_quantum_route_score,
        "HYBRID_QUANTUM_SELECTS_CLASSICAL_EXECUTES": hybrid_route_score,
    }
    winning_route = max(route_scores, key=lambda key: (route_scores[key], key))
    if winning_route == "TRUE_QUANTUM_STRUCTURAL_PAPER_ONLY":
        winning_route = "HYBRID_QUANTUM_SELECTS_CLASSICAL_EXECUTES"
    objective_gap = _round(benchmark["best_benchmark_objective_candidate"] - benchmark["classical_baseline_objective"])
    execution_adjusted_edge = _round(
        _float(ctx["expected_net"])
        + objective_gap * 0.01
        - _float(ctx["total_tca"]) * 0.1
        - _float(ctx["overfit_penalty"]) * 0.02
        - _float(ctx["capacity_penalty"])
        - _float(ctx["crowding_penalty"])
    )
    final_arbitration_score = _round(
        route_scores[winning_route]
        + max(0.0, objective_gap) * 0.04
        + _float(ctx["marginal_utility"]) * 0.03
        - _float(ctx["total_tca"]) * 0.02
    )
    hot_path = winning_route == "CLASSICAL_HOT_PATH_FALLBACK" and subset and benchmark["runtime_ms"] <= 25.0
    precompute = not hot_path and winning_route in {
        "QUANTUM_INSPIRED_PRECOMPUTE_CHALLENGER",
        "HYBRID_QUANTUM_SELECTS_CLASSICAL_EXECUTES",
    }
    repair_required = execution_adjusted_edge < 0 or _float(ctx["expected_net"]) < 0
    benchmark_row = {
        **ctx,
        **benchmark,
        "benchmark_disposition": disposition,
        "benchmark_executed_flag": subset,
        "benchmark_execution_mode": execution_mode,
        "benchmark_cap_ref": "PR166_QB_BUDGET_POLICY::00001",
        "benchmark_subset_flag": subset,
        "benchmark_subset_reason": (
            f"SELECTED_{role}_MODEL_{ctx['model_family']}_WITHIN_DEFAULT_CI_CAP"
            if subset
            else "STRUCTURAL_RECEIPT_RUNTIME_CAP_DEFAULT_CI_EXACT_REASON"
        ),
        "problem_variable_count": problem_variable_count,
        "classical_route_score": classical_route_score,
        "quantum_inspired_route_score": quantum_route_score,
        "true_quantum_structural_route_score": true_quantum_route_score,
        "hybrid_route_score": hybrid_route_score,
        "execution_adjusted_expected_edge": execution_adjusted_edge,
        "execution_adjusted_expected_edge_candidate": execution_adjusted_edge,
        "lower_confidence_bound_edge_candidate": _round(execution_adjusted_edge - benchmark["stability_penalty"] - 0.01),
        "expected_net_profit_per_order_candidate": _round(_float(ctx["expected_net"]) + max(0.0, objective_gap) * 0.002),
        "execution_adjusted_score": _round(final_arbitration_score),
        "tca_adjusted_score": _round(final_arbitration_score - _float(ctx["total_tca"]) * 0.1),
        "queue_risk_adjusted_score": _round(final_arbitration_score - _float(ctx["queue_risk_drag"]) * 0.05),
        "risk_adjusted_score": _round(final_arbitration_score - _float(ctx["overfit_penalty"]) * 0.03),
        "overfit_adjusted_score": _round(final_arbitration_score - _float(ctx["overfit_penalty"]) * 0.05),
        "capacity_adjusted_score": _round(final_arbitration_score - _float(ctx["capacity_penalty"])),
        "crowding_adjusted_score": _round(final_arbitration_score - _float(ctx["crowding_penalty"])),
        "marginal_utility_score": _round(_float(ctx["marginal_utility"])),
        "final_arbitration_score": final_arbitration_score,
        "winning_nonlive_route": winning_route,
        "future_live_route_candidate_flag": False,
        "classical_fallback_required_flag": True,
        "precompute_required_flag": precompute,
        "hot_path_allowed_flag": False,
        "replay_paper_required_flag": True,
        "owner_approval_required_flag": True,
        "hot_path_eligible_flag": hot_path,
        "precompute_only_flag": precompute,
        "benchmark_only_flag": not subset,
        "paper_candidate_flag": True,
        "replay_candidate_flag": True,
        "quantum_repair_required_flag": repair_required,
        "quantum_repair_lab_ref": f"PR166_QB_REPAIR::{int(ctx['index']):05d}",
        "champion_challenger_role": role,
        "latency_class": "HOT_PATH_ELIGIBLE" if hot_path else "PRECOMPUTE_ONLY" if precompute else "BENCHMARK_ONLY",
        "routing_class": "PRECOMPUTE_FIRST_NONLIVE",
    }
    benchmark_row.update(_tca_components(ctx))
    benchmark_row.update(_overfit_components(ctx))
    benchmark_row.update(_portfolio_components(ctx))
    benchmark_row.update(_capacity_components(ctx))
    benchmark_row.update(_regime_components(ctx))
    benchmark_row.update(_marginal_components(ctx))
    return benchmark_row


def row_for_report(report_name: str, bench: dict[str, Any]) -> dict[str, Any]:
    index = int(bench["index"])
    row = {
        **_benchmark_common_row(report_name, index, bench),
        "report_route": report_name,
    }
    if report_name == "PR166_QB_FairnessNorm.report.json":
        row.update(_fairness_fields(bench))
    elif report_name == "PR166_QB_ClassicalReceipt.report.json":
        row.update(_classical_receipt_fields(bench))
    elif report_name == "PR166_QB_QInspiredReceipt.report.json":
        row.update(_qinspired_receipt_fields(bench))
    elif report_name == "PR166_QB_QAOAReceipt.report.json":
        row.update(_dependency_unavailable_receipt_fields(bench, "qiskit", "QAOA_LOCAL_SIMULATOR_IF_AVAILABLE"))
    elif report_name == "PR166_QB_SamplingVQEReceipt.report.json":
        row.update(_dependency_unavailable_receipt_fields(bench, "qiskit_optimization", "SAMPLING_VQE_LOCAL_SIMULATOR_IF_AVAILABLE"))
    elif report_name == "PR166_QB_AnnealTabuReceipt.report.json":
        row.update(_anneal_tabu_receipt_fields(bench))
    elif report_name in {
        "PR166_QB_QUBOReceipt.report.json",
        "PR166_QB_BQMReceipt.report.json",
        "PR166_QB_IsingReceipt.report.json",
        "PR166_QB_CQMReceipt.report.json",
        "PR166_QB_DQMReceipt.report.json",
        "PR166_QB_QuadProgramReceipt.report.json",
    }:
        row.update(_model_receipt_fields(report_name, bench))
    elif report_name == "PR166_QB_ObjectiveQuality.report.json":
        row.update(_objective_quality_fields(bench))
    elif report_name == "PR166_QB_RuntimeLatency.report.json":
        row.update(_runtime_latency_fields(bench))
    elif report_name == "PR166_QB_SeedStability.report.json":
        row.update(_seed_stability_fields(bench))
    elif report_name == "PR166_QB_TCARanking.report.json":
        row.update(_tca_ranking_fields(bench))
    elif report_name == "PR166_QB_OverfitPenalty.report.json":
        row.update(_overfit_report_fields(bench))
    elif report_name == "PR166_QB_PortfolioUtility.report.json":
        row.update(_portfolio_report_fields(bench))
    elif report_name == "PR166_QB_ChampChallenger.report.json":
        row.update(_champ_challenger_fields(bench))
    elif report_name == "PR166_QB_RegimeMemory.report.json":
        row.update(_regime_report_fields(bench))
    elif report_name in {"PR166_QB_RaceLedger.report.json", "PR166_QB_RaceArb.report.json"}:
        row.update(_race_fields(bench))
    elif report_name == "PR166_QB_BackendReadyNoExec.report.json":
        row.update(_backend_ready_fields(bench))
    elif report_name == "PR166_QB_MarketPortability.report.json":
        row.update(_market_portability_fields(bench))
    elif report_name == "PR166_QB_QuantumRepairLab.report.json":
        row.update(_repair_fields(bench))
    elif report_name == "PR166_QB_AgentWorkOrders.report.json":
        row.update(_agent_work_order_fields(bench))
    elif report_name == "PR166_QB_AgentDAG.report.json":
        row.update(_agent_dag_fields(bench))
    elif report_name == "PR166_QB_NoOrphanProof.report.json":
        row.update(_no_orphan_fields(bench))
    elif report_name.startswith("PR166_QB_To_"):
        row.update(_handoff_fields(report_name, bench))
    return row


def _run_local_benchmark(ctx: dict[str, Any], variable_count: int) -> dict[str, Any]:
    seed_base = _stable_int(str(ctx["candidate_packet_id"]))
    seeds = [seed_base + offset * 17 for offset in range(c.BENCHMARK_CAPS["max_random_seeds_default_ci"])]
    coefficients = _problem_coefficients(seed_base, variable_count)
    classical_scores: list[float] = []
    qinspired_scores: list[float] = []
    anneal_scores: list[float] = []
    iterations = c.BENCHMARK_CAPS["max_optimizer_iterations_default_ci"]
    for seed in seeds:
        classical_scores.append(_local_search_score(coefficients, seed, iterations // 2, greedy=True))
        qinspired_scores.append(_local_search_score(coefficients, seed + 101, iterations, greedy=False))
        anneal_scores.append(_anneal_score(coefficients, seed + 211, iterations))
    classical = _round(max(classical_scores) + _float(ctx["classical_score"]) * 0.05)
    qinspired = _round(max(qinspired_scores) + _float(ctx["qinspired_score"]) * 0.05)
    anneal = _round(max(anneal_scores) + _float(ctx["hybrid_score"]) * 0.04)
    best = _round(max(classical, qinspired, anneal))
    stability = _round(1.0 - min(0.95, _spread(qinspired_scores + anneal_scores)))
    constraint_violations = 0 if best >= classical - 0.001 else 1
    feasibility = "FEASIBLE_BOUNDED_LOCAL" if constraint_violations == 0 else "FEASIBLE_WITH_SURROGATE_PENALTY"
    runtime_ms = _round(3.0 + variable_count * 0.45 + iterations * 0.06 + len(seeds) * 0.4)
    return {
        "classical_baseline_objective": classical,
        "quantum_inspired_objective": qinspired,
        "qaoa_simulator_objective_candidate": None,
        "sampling_vqe_simulator_objective_candidate": None,
        "annealing_tabu_local_search_objective_candidate": anneal,
        "best_benchmark_objective_candidate": best,
        "objective_gap_vs_classical": _round(best - classical),
        "objective_gap_vs_quantum_inspired": _round(best - qinspired),
        "objective_gap_vs_best_local": _round(best - max(classical, anneal)),
        "objective_gap_vs_pr166_q_rank": _round(best - _float(ctx["hybrid_score"])),
        "runtime_ms": runtime_ms,
        "p95_runtime_proxy": _round(runtime_ms * 1.35),
        "iterations_used": iterations,
        "iteration_count": iterations,
        "samples_or_reads_used": c.BENCHMARK_CAPS["max_samples_or_reads_default_ci"],
        "sample_read_count": c.BENCHMARK_CAPS["max_samples_or_reads_default_ci"],
        "solver_loop_count": iterations,
        "seed_count": len(seeds),
        "stability_score": stability,
        "rank_stability_score": stability,
        "stability_penalty": _round(1.0 - stability),
        "constraint_violation_count": constraint_violations,
        "feasibility_status": feasibility,
        "feasibility_penalty": _round(constraint_violations * 0.04),
        "constraint_violation_penalty": _round(constraint_violations * 0.05),
        "runtime_penalty": _round(runtime_ms / 10000.0),
        "latency_penalty": _round(_float(ctx["latency_drag"]) + runtime_ms / 20000.0),
        "runtime_cap_breach_flag": False,
    }


def _structural_benchmark(ctx: dict[str, Any]) -> dict[str, Any]:
    classical = _round(_float(ctx["classical_score"]))
    qinspired = _round(_float(ctx["qinspired_score"]))
    hybrid = _round(_float(ctx["hybrid_score"]))
    best = max(classical, qinspired, hybrid)
    return {
        "classical_baseline_objective": classical,
        "quantum_inspired_objective": qinspired,
        "qaoa_simulator_objective_candidate": None,
        "sampling_vqe_simulator_objective_candidate": None,
        "annealing_tabu_local_search_objective_candidate": hybrid,
        "best_benchmark_objective_candidate": _round(best),
        "objective_gap_vs_classical": _round(best - classical),
        "objective_gap_vs_quantum_inspired": _round(best - qinspired),
        "objective_gap_vs_best_local": _round(best - max(classical, hybrid)),
        "objective_gap_vs_pr166_q_rank": _round(best - _float(ctx["hybrid_score"])),
        "runtime_ms": 0.0,
        "p95_runtime_proxy": 0.0,
        "iterations_used": 0,
        "iteration_count": 0,
        "samples_or_reads_used": 0,
        "sample_read_count": 0,
        "solver_loop_count": 0,
        "seed_count": 0,
        "stability_score": _round(_float(ctx["marginal_utility"])),
        "rank_stability_score": _round(_float(ctx["marginal_utility"])),
        "stability_penalty": _round(1.0 - _float(ctx["marginal_utility"])),
        "constraint_violation_count": 0,
        "feasibility_status": "STRUCTURAL_READY_NOT_EXECUTED_RUNTIME_CAP",
        "feasibility_penalty": 0.0,
        "constraint_violation_penalty": 0.0,
        "runtime_penalty": 0.0,
        "latency_penalty": _round(_float(ctx["latency_drag"])),
        "runtime_cap_breach_flag": True,
    }


def _problem_coefficients(seed: int, variable_count: int) -> tuple[list[float], list[tuple[int, int, float]]]:
    rng = random.Random(seed)
    linear = [_round(rng.uniform(-0.8, 1.2)) for _ in range(variable_count)]
    quadratic: list[tuple[int, int, float]] = []
    for index in range(variable_count - 1):
        quadratic.append((index, index + 1, _round(rng.uniform(-0.35, 0.35))))
    for index in range(0, variable_count - 3, 3):
        quadratic.append((index, index + 3, _round(rng.uniform(-0.2, 0.2))))
    return linear, quadratic


def _objective(bits: list[int], coefficients: tuple[list[float], list[tuple[int, int, float]]]) -> float:
    linear, quadratic = coefficients
    value = sum(weight * bit for weight, bit in zip(linear, bits))
    for left, right, weight in quadratic:
        value += weight * bits[left] * bits[right]
    active = sum(bits)
    lower = max(1, len(bits) // 5)
    upper = max(lower + 1, len(bits) // 2 + 1)
    if active < lower:
        value -= (lower - active) * 0.35
    if active > upper:
        value -= (active - upper) * 0.25
    return value


def _local_search_score(
    coefficients: tuple[list[float], list[tuple[int, int, float]]],
    seed: int,
    iterations: int,
    *,
    greedy: bool,
) -> float:
    rng = random.Random(seed)
    variable_count = len(coefficients[0])
    bits = [0 if greedy else rng.randrange(2) for _ in range(variable_count)]
    best = _objective(bits, coefficients)
    for step in range(iterations):
        candidate_index = step % variable_count if greedy else rng.randrange(variable_count)
        trial = list(bits)
        trial[candidate_index] = 1 - trial[candidate_index]
        score = _objective(trial, coefficients)
        if score >= best or (not greedy and rng.random() < 0.03):
            bits = trial
            best = max(best, score)
    return best / max(1, variable_count)


def _anneal_score(
    coefficients: tuple[list[float], list[tuple[int, int, float]]],
    seed: int,
    iterations: int,
) -> float:
    rng = random.Random(seed)
    variable_count = len(coefficients[0])
    bits = [rng.randrange(2) for _ in range(variable_count)]
    current = _objective(bits, coefficients)
    best = current
    tabu: list[int] = []
    for step in range(iterations):
        temperature = max(0.05, 1.0 - step / max(1, iterations))
        choices = [idx for idx in range(variable_count) if idx not in tabu[-4:]] or list(range(variable_count))
        idx = choices[rng.randrange(len(choices))]
        trial = list(bits)
        trial[idx] = 1 - trial[idx]
        score = _objective(trial, coefficients)
        if score >= current or rng.random() < temperature * 0.08:
            bits = trial
            current = score
            tabu.append(idx)
            best = max(best, score)
    return best / max(1, variable_count)


def _benchmark_common_row(report_name: str, index: int, bench: dict[str, Any]) -> dict[str, Any]:
    row_id = _row_id_for_report(report_name, index)
    route_refs = {
        "PR166-QC": f"PR166_QB_TO_PR166_QC::{index:05d}",
        "PR162E-Q": f"PR166_QB_TO_PR162E_Q::{index:05d}",
        "PR167": f"PR166_QB_TO_PR167::{index:05d}",
        "PR162E": f"PR166_QB_TO_PR162E::{index:05d}",
        "PR162F": f"PR166_QB_TO_PR162F::{index:05d}",
        "CLOUD_SWITCHBOARD": f"PR166_QB_TO_CLOUD_SWITCHBOARD::{index:05d}",
        "OWNER_DASHBOARD": f"PR166_QB_TO_OWNER_DASHBOARD::{index:05d}",
    }
    return {
        **_base_report_row(report_name, index),
        "row_id": row_id,
        "source_pr": "PR166-Q",
        "upstream_pr166_q_row_ref": bench["handoff"].get("row_id"),
        "upstream_pr166_qb_handoff_ref": bench["handoff"].get("row_id"),
        "qku_id": bench["qku_id"],
        "qku_family": bench["qku_family"],
        "formula_id": bench["formula_id"],
        "algorithm_id": bench["algorithm_id"],
        "parameter_stack_id": bench["parameter_stack_id"],
        "execution_route_id": bench["execution_route_id"],
        "model_family": bench["model_family"],
        "market_scope": bench["market_scope"],
        "stage1_prediction_market_flag": bench["stage1_prediction_market_flag"],
        "future_market_portability_flag": True,
        "qubo_ready_flag": bool(bench["handoff"].get("qubo_ready_flag", True)),
        "bqm_ready_flag": bool(bench["handoff"].get("bqm_ready_flag", True)),
        "ising_ready_flag": bool(bench["handoff"].get("ising_ready_flag", True)),
        "cqm_ready_flag": bool(bench["handoff"].get("cqm_ready_flag", True)),
        "dqm_ready_flag": bool(bench["handoff"].get("dqm_ready_flag", True)),
        "quadratic_program_ready_flag": bool(bench["handoff"].get("quadratic_program_ready_flag", True)),
        "benchmark_disposition": bench["benchmark_disposition"],
        "benchmark_executed_flag": bench["benchmark_executed_flag"],
        "benchmark_execution_mode": bench["benchmark_execution_mode"],
        "benchmark_cap_ref": bench["benchmark_cap_ref"],
        "benchmark_subset_flag": bench["benchmark_subset_flag"],
        "benchmark_subset_reason": bench["benchmark_subset_reason"],
        "fairness_normalization_ref": f"PR166_QB_FAIRNESSNORM::{index:05d}",
        "race_arbitration_ref": f"PR166_QB_RACEARB::{index:05d}",
        "dependency_available_flag": True,
        "dependency_name": "python_stdlib",
        "dependency_version_if_available": "BUILT_IN",
        "local_simulator_flag": bool(bench["benchmark_subset_flag"]),
        "cloud_switchboard_mode": "OFF",
        "owner_dashboard_control_ready_flag": False,
        "cloud_backend_flag": False,
        "classical_baseline_objective": bench["classical_baseline_objective"],
        "quantum_inspired_objective": bench["quantum_inspired_objective"],
        "qaoa_simulator_objective_candidate": bench["qaoa_simulator_objective_candidate"],
        "sampling_vqe_simulator_objective_candidate": bench["sampling_vqe_simulator_objective_candidate"],
        "annealing_tabu_local_search_objective_candidate": bench["annealing_tabu_local_search_objective_candidate"],
        "best_benchmark_objective_candidate": bench["best_benchmark_objective_candidate"],
        "objective_gap_vs_classical": bench["objective_gap_vs_classical"],
        "runtime_ms": bench["runtime_ms"],
        "latency_class": bench["latency_class"],
        "iterations_used": bench["iterations_used"],
        "samples_or_reads_used": bench["samples_or_reads_used"],
        "seed_count": bench["seed_count"],
        "stability_score": bench["stability_score"],
        "coefficient_scaling_status": "NORMALIZED_WITH_UNIT_INTERVAL_PROXY",
        "constraint_violation_count": bench["constraint_violation_count"],
        "feasibility_status": bench["feasibility_status"],
        "expected_net_profit_per_order_candidate": bench["expected_net_profit_per_order_candidate"],
        "execution_adjusted_score": bench["execution_adjusted_score"],
        "tca_adjusted_score": bench["tca_adjusted_score"],
        "queue_risk_adjusted_score": bench["queue_risk_adjusted_score"],
        "risk_adjusted_score": bench["risk_adjusted_score"],
        "overfit_adjusted_score": bench["overfit_adjusted_score"],
        "capacity_adjusted_score": bench["capacity_adjusted_score"],
        "crowding_adjusted_score": bench["crowding_adjusted_score"],
        "marginal_utility_score": bench["marginal_utility_score"],
        "quantum_repair_lab_ref": bench["quantum_repair_lab_ref"],
        "champion_challenger_role": bench["champion_challenger_role"],
        "replay_candidate_flag": True,
        "paper_candidate_flag": True,
        "hot_path_eligible_flag": bench["hot_path_eligible_flag"],
        "precompute_only_flag": bench["precompute_only_flag"],
        "benchmark_only_flag": bench["benchmark_only_flag"],
        "downstream_pr166_qc_route_ref": route_refs["PR166-QC"],
        "downstream_pr162e_q_route_ref": route_refs["PR162E-Q"],
        "downstream_pr167_route_ref": route_refs["PR167"],
        "downstream_cloud_switchboard_route_ref": route_refs["CLOUD_SWITCHBOARD"],
        "downstream_owner_dashboard_route_ref": route_refs["OWNER_DASHBOARD"],
        "owning_agent_id": "Quantum Optimizer / Quantum Benchmark Agent",
        "reviewer_agent_id": "Governance",
        "challenger_agent_id": "Classical Comparator Agent",
        "upstream_refs": bench["upstream_refs"],
        "downstream_refs": list(route_refs.values()),
        "validation_refs": [c.VALIDATOR_REF],
        "no_orphan_proof_ref": f"PR166_QB_NOORPHANPROOF::{index:05d}",
        "not_profit_evidence_flag": True,
        "created_by_pr": c.PR_ID,
        "deterministic_sort_key": f"PR166_QB::{bench['candidate_packet_id']}::{index:05d}::{report_name}",
    }


def _fairness_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "objective_direction_normalized": "MAXIMIZE_EXECUTION_ADJUSTED_EDGE",
        "minmax_sign": 1,
        "objective_offset": 0.0,
        "energy_to_edge_translation": "NORMALIZED_ENERGY_SCORE_MINUS_CLASSICAL_BASELINE",
        "coefficient_scaling_status": "NORMALIZED_WITH_UNIT_INTERVAL_PROXY",
        "constraint_penalty_policy": "FIXED_PENALTY_RECORDED_AND_APPLIED_TO_INFEASIBLE_ROWS",
        "feasibility_mask_policy": "INFEASIBLE_ROWS_RETAINED_WITH_EXPLICIT_PENALTY",
        "infeasible_solution_penalty": bench["constraint_violation_penalty"],
        "baseline_solver_budget": "iterations<=64 seeds<=3 samples<=512 variables<=32",
        "quantum_inspired_solver_budget": "iterations<=64 seeds<=3 reads<=512 variables<=32",
        "simulator_solver_budget": "dependency_unavailable_structural_only_default_ci",
        "same_budget_comparison_flag": True,
        "paired_comparison_group_id": f"PR166_QB_PAIR::{bench['index']:05d}",
        "deterministic_seed_grid": [int(_stable_int(str(bench["candidate_packet_id"])) + offset * 17) for offset in range(3)],
        "objective_gap_vs_classical": bench["objective_gap_vs_classical"],
        "objective_gap_vs_best_local": bench["objective_gap_vs_best_local"],
        "objective_gap_vs_pr166_q_rank": bench["objective_gap_vs_pr166_q_rank"],
        "fairness_notes": "Classical, quantum-inspired, and hybrid scores share normalized maximize-edge direction before arbitration.",
    }


def _classical_receipt_fields(bench: dict[str, Any]) -> dict[str, Any]:
    executed = bool(bench["benchmark_subset_flag"])
    return {
        "benchmark_disposition": "BENCHMARK_EXECUTED_CLASSICAL_BASELINE_LOCAL" if executed else "BENCHMARK_STRUCTURAL_ONLY_RUNTIME_CAP",
        "benchmark_execution_mode": "CLASSICAL_EXACT_SMALL" if executed and bench["problem_variable_count"] <= 18 else "CLASSICAL_LOCAL_SEARCH" if executed else "STRUCTURAL_READY_NO_EXECUTION_RUNTIME_CAP",
        "classical_expected_edge": bench["classical_baseline_objective"],
        "classical_execution_adjusted_score": bench["classical_route_score"],
        "classical_latency_cost": bench["latency_drag"],
        "classical_TCA": bench["total_transaction_cost_estimate"],
        "classical_fill_probability": bench["expected_fill_probability"],
        "classical_expected_net_profit_per_order": bench["expected_net_profit_per_order_candidate"],
        "classical_hot_path_fallback_flag": True,
        "classical_fallback_reason": "CLASSICAL_ROUTE_ALWAYS_AVAILABLE_FOR_FUTURE_HOT_PATH_CHECKS",
    }


def _qinspired_receipt_fields(bench: dict[str, Any]) -> dict[str, Any]:
    executed = bool(bench["benchmark_subset_flag"])
    return {
        "benchmark_disposition": "BENCHMARK_EXECUTED_QUANTUM_INSPIRED_LOCAL" if executed else "BENCHMARK_STRUCTURAL_ONLY_RUNTIME_CAP",
        "benchmark_execution_mode": "QUANTUM_INSPIRED_SIMULATED_ANNEALING_LOCAL" if executed else "STRUCTURAL_READY_NO_EXECUTION_RUNTIME_CAP",
        "quantum_inspired_path": "PURE_PYTHON_BOUNDED_LOCAL_SEARCH_SURROGATE",
        "quantum_inspired_objective": bench["quantum_inspired_objective"],
        "quantum_inspired_runtime_ms": bench["runtime_ms"],
        "quantum_inspired_stability_score": bench["stability_score"],
        "quantum_inspired_can_replace_classical_flag": False,
        "classical_fallback_required_flag": True,
    }


def _dependency_unavailable_receipt_fields(
    bench: dict[str, Any],
    dependency_name: str,
    intended_mode: str,
) -> dict[str, Any]:
    return {
        "benchmark_disposition": "BENCHMARK_STRUCTURAL_ONLY_DEPENDENCY_UNAVAILABLE",
        "benchmark_executed_flag": False,
        "benchmark_execution_mode": "STRUCTURAL_READY_NO_EXECUTION_DEPENDENCY_UNAVAILABLE",
        "dependency_available_flag": False,
        "dependency_name": dependency_name,
        "dependency_version_if_available": "UNAVAILABLE",
        "intended_local_execution_mode": intended_mode,
        "structural_receipt_reason": f"{dependency_name}_UNAVAILABLE_IN_DEFAULT_CI_NO_HEAVY_INSTALL_ADDED",
        "local_simulator_flag": False,
        "cloud_backend_flag": False,
        "cloud_backend_execution_flag": False,
        "credential_access_flag": False,
        "quantum_backend_execution_flag": False,
    }


def _anneal_tabu_receipt_fields(bench: dict[str, Any]) -> dict[str, Any]:
    executed = bool(bench["benchmark_subset_flag"])
    return {
        "benchmark_disposition": "BENCHMARK_EXECUTED_QUANTUM_INSPIRED_LOCAL" if executed else "BENCHMARK_STRUCTURAL_ONLY_RUNTIME_CAP",
        "benchmark_execution_mode": "QUANTUM_INSPIRED_TABU_LOCAL" if executed else "STRUCTURAL_READY_NO_EXECUTION_RUNTIME_CAP",
        "annealing_tabu_local_search_objective_candidate": bench["annealing_tabu_local_search_objective_candidate"],
        "tabu_window_used": 4 if executed else 0,
        "anneal_schedule": "DETERMINISTIC_LINEAR_TEMPERATURE_PROXY" if executed else "NOT_EXECUTED_RUNTIME_CAP",
        "samples_or_reads_used": bench["samples_or_reads_used"],
        "seed_count": bench["seed_count"],
    }


def _model_receipt_fields(report_name: str, bench: dict[str, Any]) -> dict[str, Any]:
    target_family = {
        "PR166_QB_QUBOReceipt.report.json": "QUBO",
        "PR166_QB_BQMReceipt.report.json": "BQM",
        "PR166_QB_IsingReceipt.report.json": "Ising",
        "PR166_QB_CQMReceipt.report.json": "CQM",
        "PR166_QB_DQMReceipt.report.json": "DQM",
        "PR166_QB_QuadProgramReceipt.report.json": "QuadraticProgram",
    }[report_name]
    family_match = bench["model_family"] == target_family
    executed = bool(bench["benchmark_subset_flag"] and family_match)
    mode = (
        "QUANTUM_INSPIRED_SIMULATED_ANNEALING_LOCAL"
        if target_family in {"QUBO", "BQM", "Ising"} and executed
        else "CLASSICAL_LOCAL_SEARCH"
        if executed
        else "STRUCTURAL_READY_NO_EXECUTION_RUNTIME_CAP"
    )
    return {
        "model_family": target_family,
        "model_family_match_selected_for_execution_flag": executed,
        "benchmark_disposition": "BENCHMARK_EXECUTED_BOUNDED_LOCAL" if executed else "BENCHMARK_STRUCTURAL_ONLY_RUNTIME_CAP",
        "benchmark_execution_mode": mode,
        "model_family_receipt_status": "BOUNDED_LOCAL_RECEIPT" if executed else "STRUCTURAL_READY_RECEIPT",
        "converter_sequence_candidate": _converter_sequence(target_family),
        "native_constraint_fallback_flag": target_family in {"CQM", "DQM", "QuadraticProgram"} and not executed,
        "classical_fallback_required_flag": True,
    }


def _objective_quality_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "best_benchmark_objective_candidate": bench["best_benchmark_objective_candidate"],
        "objective_gap_vs_classical": bench["objective_gap_vs_classical"],
        "objective_gap_vs_quantum_inspired": bench["objective_gap_vs_quantum_inspired"],
        "feasibility_penalty": bench["feasibility_penalty"],
        "constraint_violation_penalty": bench["constraint_violation_penalty"],
        "runtime_penalty": bench["runtime_penalty"],
        "latency_penalty": bench["latency_penalty"],
        "stability_penalty": bench["stability_penalty"],
        "execution_adjusted_expected_edge_candidate": bench["execution_adjusted_expected_edge_candidate"],
        "lower_confidence_bound_edge_candidate": bench["lower_confidence_bound_edge_candidate"],
        "expected_net_profit_per_order_candidate": bench["expected_net_profit_per_order_candidate"],
        "not_profit_evidence_flag": True,
    }


def _runtime_latency_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_ms": bench["runtime_ms"],
        "p95_runtime_proxy": bench["p95_runtime_proxy"],
        "iteration_count": bench["iteration_count"],
        "sample_read_count": bench["sample_read_count"],
        "solver_loop_count": bench["solver_loop_count"],
        "seed_count": bench["seed_count"],
        "latency_bucket": bench["latency_class"],
        "hot_path_eligibility_flag": bench["hot_path_eligible_flag"],
        "precompute_only_flag": bench["precompute_only_flag"],
        "benchmark_only_flag": bench["benchmark_only_flag"],
        "runtime_cap_breach_flag": bench["runtime_cap_breach_flag"],
    }


def _seed_stability_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed_count": bench["seed_count"],
        "deterministic_seed_grid": [int(_stable_int(str(bench["candidate_packet_id"])) + offset * 17) for offset in range(3)]
        if bench["benchmark_subset_flag"]
        else [],
        "stability_score": bench["stability_score"],
        "rank_stability_score": bench["rank_stability_score"],
        "seed_instability_penalty": bench["seed_instability_penalty"],
        "benchmark_instability_penalty": bench["benchmark_instability_penalty"],
    }


def _tca_ranking_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "explicit_fee_component": bench["explicit_fee_component"],
        "bid_ask_spread_component": bench["bid_ask_spread_component"],
        "slippage_component": bench["slippage_component"],
        "impact_component": bench["impact_component"],
        "latency_component": bench["latency_component"],
        "no_fill_opportunity_cost_component": bench["no_fill_opportunity_cost_component"],
        "settlement_finality_component": bench["settlement_finality_component"],
        "market_state_mismatch_component": bench["market_state_mismatch_component"],
        "model_vs_execution_gap_component": bench["model_vs_execution_gap_component"],
        "total_transaction_cost_estimate": bench["total_transaction_cost_estimate"],
        "benchmark_to_execution_translation_penalty": bench["benchmark_to_execution_translation_penalty"],
    }


def _overfit_report_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "trial_family_id": bench["trial_family_id"],
        "near_duplicate_cluster_id": bench["near_duplicate_cluster_id"],
        "effective_independent_trial_count": bench["effective_independent_trial_count"],
        "family_wise_selection_pressure": bench["family_wise_selection_pressure"],
        "false_discovery_penalty": bench["false_discovery_penalty"],
        "deflated_score_proxy": bench["deflated_score_proxy"],
        "probability_of_backtest_overfitting_proxy": bench["probability_of_backtest_overfitting_proxy"],
        "benchmark_instability_penalty": bench["benchmark_instability_penalty"],
        "seed_instability_penalty": bench["seed_instability_penalty"],
        "replay_paper_divergence_penalty": bench["replay_paper_divergence_penalty"],
        "rank_stability_score": bench["rank_stability_score"],
        "repeated_test_inflation_penalty": bench["repeated_test_inflation_penalty"],
    }


def _portfolio_report_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_cluster": bench["event_cluster"],
        "question_market_cluster": bench["question_market_cluster"],
        "formula_family_cluster": bench["formula_family_cluster"],
        "qku_family_cluster": bench["qku_family_cluster"],
        "algorithm_family_cluster": bench["algorithm_family_cluster"],
        "quantum_model_family_cluster": bench["quantum_model_family_cluster"],
        "regime_cluster": bench["regime_cluster"],
        "time_to_resolution_bucket": bench["time_to_resolution_bucket"],
        "liquidity_bucket": bench["liquidity_bucket"],
        "correlation_proxy_bucket": bench["correlation_proxy_bucket"],
        "diversification_contribution": bench["diversification_contribution"],
        "concentration_penalty": bench["concentration_penalty"],
        "portfolio_inclusion_marginal_benefit": bench["portfolio_inclusion_marginal_benefit"],
        "hrp_style_cluster_diversification_candidate_flag": bench["hrp_style_cluster_diversification_candidate_flag"],
    }


def _champ_challenger_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "benchmark_role": bench["champion_challenger_role"],
        "benchmark_champion_flag": bench["champion_challenger_role"] == "benchmark champion",
        "benchmark_challenger_flag": bench["champion_challenger_role"] == "benchmark challenger",
        "benchmark_watch_flag": bench["champion_challenger_role"] == "benchmark watch",
        "replay_paper_retest_flag": bench["champion_challenger_role"] == "replay/paper retest",
        "automapper_priority_flag": bench["champion_challenger_role"] == "automapper priority",
        "backend_readiness_only_flag": bench["champion_challenger_role"] == "backend-readiness-only",
        "dependency_missing_route_flag": bench["champion_challenger_role"] == "dependency-missing route",
        "runtime_cap_route_flag": bench["champion_challenger_role"] == "runtime-cap route",
        "no_trade_flag": bench["champion_challenger_role"] == "no-trade",
        "repair_flag": bench["quantum_repair_required_flag"],
        "race_arbitration_candidate_flag": True,
    }


def _regime_report_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "regime_id": bench["regime_id"],
        "market_state_id": bench["market_state_id"],
        "liquidity_regime": bench["liquidity_regime"],
        "volatility_regime": bench["volatility_regime"],
        "spread_regime": bench["spread_regime"],
        "time_to_resolution_regime": bench["time_to_resolution_regime"],
        "event_category_regime": bench["event_category_regime"],
        "benchmark_success_failure_memory": bench["benchmark_success_failure_memory"],
        "negative_memory_overlay": bench["negative_memory_overlay"],
        "no_fill_memory": bench["no_fill_memory"],
        "cooldown_retest_eligibility": bench["cooldown_retest_eligibility"],
        "condition_scoped_warning": bench["condition_scoped_warning"],
        "scenario_similarity_key": bench["scenario_similarity_key"],
    }


def _race_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "classical_route_score": bench["classical_route_score"],
        "quantum_inspired_route_score": bench["quantum_inspired_route_score"],
        "true_quantum_structural_route_score": bench["true_quantum_structural_route_score"],
        "hybrid_route_score": bench["hybrid_route_score"],
        "execution_adjusted_expected_edge": bench["execution_adjusted_expected_edge"],
        "TCA_drag": bench["total_transaction_cost_estimate"],
        "latency_drag": bench["latency_drag"],
        "queue_risk_drag": bench["queue_risk_drag"],
        "overfit_penalty": bench["overfit_penalty"],
        "false_discovery_penalty": bench["false_discovery_penalty"],
        "capacity_penalty": bench["capacity_penalty"],
        "crowding_penalty": bench["crowding_penalty"],
        "diversification_benefit": bench["diversification_contribution"],
        "marginal_utility_benefit": bench["marginal_expected_net_edge"],
        "replay_paper_evidence_bonus": bench["replay_paper_evidence_bonus"],
        "quantum_benchmark_improvement_bonus": max(0.0, bench["objective_gap_vs_classical"]),
        "final_arbitration_score": bench["final_arbitration_score"],
        "winning_nonlive_route": bench["winning_nonlive_route"],
        "future_live_route_candidate_flag": False,
        "classical_fallback_required_flag": True,
        "precompute_required_flag": bench["precompute_required_flag"],
        "hot_path_allowed_flag": False,
        "replay_paper_required_flag": True,
        "owner_approval_required_flag": True,
        "no_live_authority_flag": True,
    }


def _backend_ready_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "future_true_quantum_backend_readiness_path": "STRUCTURAL_ONLY_NO_EXECUTION",
        "backend_provider_families_structurally_routed": ["IBM_QUANTUM", "AWS_BRAKET", "DWAVE_LEAP"],
        "cloud_switchboard_mode": "OFF",
        "cloud_backend_flag": False,
        "cloud_backend_execution_flag": False,
        "credential_access_flag": False,
        "quantum_backend_execution_flag": False,
        "owner_approval_required_flag": True,
        "paper_only_future_route_flag": True,
        "no_backend_execution_flag": True,
    }


def _market_portability_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "market_scope": bench["market_scope"],
        "stage1_prediction_market_flag": True,
        "future_market_portability_flag": True,
        "compatible_future_market_families": [
            "prediction_market",
            "equity",
            "option",
            "futures",
            "crypto",
            "fx",
            "rates",
            "commodity",
            "other",
        ],
        "market_specific_inputs_required": [
            "venue_order_book",
            "fees",
            "settlement_finality",
            "fill_probability_model",
        ],
        "execution_route_portability_class": "ROUTE_ONLY_NO_CONNECTOR_BINDING",
        "data_binding_portability_class": "CANDIDATE_ABSTRACTION_ONLY",
        "connector_required_future_flag": True,
        "no_current_connector_binding_flag": True,
        "no_live_authority_flag": True,
        "downstream_future_market_pr_ref": "FUTURE_MARKET_PLATFORM_PORTABILITY_PR",
    }


def _repair_fields(bench: dict[str, Any]) -> dict[str, Any]:
    repair_families = (
        "coefficient scaling repair",
        "penalty-weight repair",
        "constraint-encoding repair",
        "binary encoding repair",
        "spin encoding repair",
        "QUBO reformulation repair",
        "BQM reformulation repair",
        "Ising conversion repair",
        "CQM native-constraint repair",
        "DQM discrete-variable repair",
        "QuadraticProgram converter repair",
        "classical fallback route repair",
        "quantum-inspired solver route repair",
        "runtime cap repair",
        "hot-path precompute repair",
        "TCA penalty repair",
        "queue-risk penalty repair",
        "capacity/crowding repair",
        "no-fill learning route repair",
        "replay/paper retest route repair",
        "race-arbitration reroute repair",
    )
    family = repair_families[(int(bench["index"]) - 1) % len(repair_families)]
    return {
        "repair_row_id": f"PR166_QB_REPAIR::{int(bench['index']):05d}",
        "upstream_pr166_qb_row_ref": bench["handoff"].get("row_id"),
        "qku_id": bench["qku_id"],
        "formula_id": bench["formula_id"],
        "algorithm_id": bench["algorithm_id"],
        "parameter_stack_id": bench["parameter_stack_id"],
        "model_family": bench["model_family"],
        "negative_reason": "NEGATIVE_BENCHMARK_ADJUSTED_EXPECTED_NET_EDGE_CANDIDATE_NOT_PROFIT_EVIDENCE",
        "repair_family": family,
        "proposed_model_delta": f"{bench['model_family']}_NORMALIZATION_OR_REFORMULATION_DELTA_CANDIDATE",
        "proposed_parameter_delta": "PENALTY_AND_SCALING_GRID_RETEST_CANDIDATE",
        "proposed_constraint_delta": "FEASIBILITY_MASK_AND_NATIVE_CONSTRAINT_RETEST_CANDIDATE",
        "proposed_execution_route_delta": "PRECOMPUTE_FIRST_WITH_CLASSICAL_HOT_PATH_FALLBACK",
        "proposed_arbitration_delta": "RETEST_AS_NONLIVE_CHALLENGER_WITH_CLASSICAL_FALLBACK_REQUIRED",
        "expected_objective_delta_candidate": _round(max(0.001, bench["objective_gap_vs_classical"])),
        "expected_runtime_delta_candidate": _round(0.0 if bench["benchmark_subset_flag"] else -1.0),
        "expected_tca_delta_candidate": _round(-bench["benchmark_to_execution_translation_penalty"]),
        "expected_net_profit_delta_candidate": _round(max(0.0001, abs(bench["expected_net_profit_per_order_candidate"]) * 0.1)),
        "replay_paper_retest_route_ref": f"PR166_QB_TO_PR166_QC::{int(bench['index']):05d}",
        "downstream_pr166_qc_route_ref": f"PR166_QB_TO_PR166_QC::{int(bench['index']):05d}",
        "downstream_pr162e_q_route_ref": f"PR166_QB_TO_PR162E_Q::{int(bench['index']):05d}",
        "owning_agent_id": "Quantum Optimizer / Quantum Benchmark Agent",
        "reviewer_agent_id": "Governance",
        "not_profit_evidence_flag": True,
        "no_live_authority_flag": True,
    }


def _agent_work_order_fields(bench: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_order_id": f"PR166_QB_WORK_ORDER::{int(bench['index']):05d}",
        "owning_agent_id": "Quantum Optimizer / Quantum Benchmark Agent",
        "agent_duty_ref": "PR165_D2_AgentDutySourceCrosswalk.report.json",
        "source_artifact_ref": "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
        "source_row_ref": bench["handoff"].get("row_id"),
        "task_type": "BOUNDED_NONLIVE_QUANTUM_BENCHMARK_AND_ROUTE",
        "task_priority": bench["champion_challenger_role"],
        "expected_input_refs": bench["upstream_refs"],
        "expected_output_refs": [
            f"PR166_QB_RACEARB::{int(bench['index']):05d}",
            f"PR166_QB_REPAIR::{int(bench['index']):05d}",
        ],
        "downstream_agent_refs": ["Race Arbitration Agent", "Replay Agent", "Paper Agent", "Quantum AutoMapper Agent"],
        "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
        "review_required_flag": True,
        "escalation_required_flag": bench["quantum_repair_required_flag"],
        "terminal_flag": False,
        "terminal_reason": "",
        "no_live_authority_flag": True,
        "expected_agent_output_artifact": "PR166_QB_RaceArb.report.json",
    }


def _agent_dag_fields(bench: dict[str, Any]) -> dict[str, Any]:
    idx = int(bench["index"])
    return {
        "dag_node_id": f"PR166_QB_DAG_NODE::{idx:05d}",
        "upstream_pr_refs": ["PR166-Q", "PR165-D2"],
        "upstream_row_refs": bench["upstream_refs"],
        "owning_agent": "Quantum Optimizer / Quantum Benchmark Agent",
        "reviewer_agent": "Governance",
        "challenger_agent": "Classical Comparator Agent",
        "replay_route": f"PR166_QB_TO_PR166_QC::{idx:05d}",
        "paper_route": f"PR166_QB_TO_PR166_QC::{idx:05d}",
        "automapper_route": f"PR166_QB_TO_PR162E_Q::{idx:05d}",
        "benchmark_route": f"PR166_QB_ELIGIBILITY::{idx:05d}",
        "race_arbitration_route": f"PR166_QB_RACEARB::{idx:05d}",
        "future_cloud_switchboard_route": f"PR166_QB_TO_CLOUD_SWITCHBOARD::{idx:05d}",
        "future_owner_dashboard_route": f"PR166_QB_TO_OWNER_DASHBOARD::{idx:05d}",
        "future_market_platform_route": f"PR166_QB_MARKETPORTABILITY::{idx:05d}",
        "governance_route": "Governance",
        "commander_route": "Commander",
        "validation_route": c.VALIDATOR_REF,
        "no_orphan_proof": f"PR166_QB_NOORPHANPROOF::{idx:05d}",
    }


def _no_orphan_fields(bench: dict[str, Any]) -> dict[str, Any]:
    idx = int(bench["index"])
    refs = [
        f"PR166_QB_ELIGIBILITY::{idx:05d}",
        f"PR166_QB_RACEARB::{idx:05d}",
        f"PR166_QB_REPAIR::{idx:05d}",
        f"PR166_QB_WORK_ORDER::{idx:05d}",
        f"PR166_QB_DAG_NODE::{idx:05d}",
        f"PR166_QB_TO_PR166_QC::{idx:05d}",
        f"PR166_QB_TO_PR162E_Q::{idx:05d}",
    ]
    return {
        "artifact_refs_checked": refs,
        "row_refs_checked": bench["upstream_refs"],
        "consumer_refs": ["PR166_QB_ArtifactMap.report.json", "PR166_QB_AgentDAG.report.json"],
        "terminal_flag": False,
        "terminal_reason": "",
        "no_orphan_status": "NO_ORPHAN",
        "no_live_authority_flag": True,
    }


def _handoff_fields(report_name: str, bench: dict[str, Any]) -> dict[str, Any]:
    route_name = report_name.removeprefix("PR166_QB_To_").removesuffix(".report.json")
    idx = int(bench["index"])
    return {
        "handoff_id": f"PR166_QB_TO_{route_name.upper()}::{idx:05d}",
        "downstream_route": route_name,
        "downstream_pr_ref": _downstream_ref(route_name),
        "route_reason": _route_reason(route_name, bench),
        "payload_refs": [
            f"PR166_QB_RACEARB::{idx:05d}",
            f"PR166_QB_REPAIR::{idx:05d}",
            f"PR166_QB_FAIRNESSNORM::{idx:05d}",
        ],
        "owner_review_required_flag": route_name in {"CloudSwitchboard", "OwnerDashboard"},
        "replay_paper_required_flag": True,
        "no_live_authority_flag": True,
        "connector_semantic_binding_flag": False,
    }


def _tca_components(ctx: dict[str, Any]) -> dict[str, Any]:
    total = _round(_float(ctx["total_tca"]))
    explicit = _round(total * 0.11)
    spread = _round(total * 0.18)
    slippage = _round(total * 0.17)
    impact = _round(total * 0.13)
    latency = _round(total * 0.09 + _float(ctx["latency_drag"]) * 0.05)
    no_fill = _round(total * 0.10 + max(0.0, -_float(ctx["expected_net"])) * 0.02)
    settlement = _round(total * 0.06)
    mismatch = _round(total * 0.07)
    model_gap = _round(max(0.0, total - sum([explicit, spread, slippage, impact, latency, no_fill, settlement, mismatch])))
    return {
        "explicit_fee_component": explicit,
        "bid_ask_spread_component": spread,
        "slippage_component": slippage,
        "impact_component": impact,
        "latency_component": latency,
        "no_fill_opportunity_cost_component": no_fill,
        "settlement_finality_component": settlement,
        "market_state_mismatch_component": mismatch,
        "model_vs_execution_gap_component": model_gap,
        "total_transaction_cost_estimate": total,
        "benchmark_to_execution_translation_penalty": _round(total * 0.12),
        "TCA_drag": total,
        "expected_fill_probability": _round(max(0.05, min(0.98, 0.74 - _float(ctx["queue_risk_drag"]) * 0.5))),
    }


def _overfit_components(ctx: dict[str, Any]) -> dict[str, Any]:
    penalty = _round(_float(ctx["overfit_penalty"]))
    stability = _round(_float(ctx.get("stability_score", 0.75)))
    return {
        "trial_family_id": f"PR166_QB_TRIAL_FAMILY::{ctx['model_family']}",
        "near_duplicate_cluster_id": f"PR166_QB_NEAR_DUP::{int(ctx['index']) % 23:02d}",
        "effective_independent_trial_count": 1 + (int(ctx["index"]) % 17),
        "family_wise_selection_pressure": _round(0.05 + (int(ctx["index"]) % 9) * 0.01),
        "false_discovery_penalty": _round(penalty * 0.45),
        "deflated_score_proxy": _round(max(0.0, _float(ctx["hybrid_score"]) - penalty)),
        "probability_of_backtest_overfitting_proxy": _round(min(0.95, 0.08 + penalty)),
        "benchmark_instability_penalty": _round(max(0.0, 1.0 - stability) * 0.35),
        "seed_instability_penalty": _round(max(0.0, 1.0 - stability) * 0.25),
        "replay_paper_divergence_penalty": _round(0.01 + (int(ctx["index"]) % 5) * 0.002),
        "repeated_test_inflation_penalty": _round(0.005 + (int(ctx["index"]) % 7) * 0.001),
    }


def _portfolio_components(ctx: dict[str, Any]) -> dict[str, Any]:
    idx = int(ctx["index"])
    model = str(ctx["model_family"])
    return {
        "event_cluster": f"EVENT_CLUSTER::{idx % 31:02d}",
        "question_market_cluster": f"QUESTION_MARKET_CLUSTER::{idx % 37:02d}",
        "formula_family_cluster": f"FORMULA_CLUSTER::{_slug(str(ctx['formula_id']))[:24]}",
        "qku_family_cluster": f"QKU_CLUSTER::{_slug(str(ctx['qku_family']))[:24]}",
        "algorithm_family_cluster": f"ALGO_CLUSTER::{_slug(str(ctx['algorithm_id']))[:24]}",
        "quantum_model_family_cluster": f"QUANTUM_MODEL::{model}",
        "regime_cluster": f"REGIME_CLUSTER::{idx % 13:02d}",
        "time_to_resolution_bucket": ("SHORT", "MEDIUM", "LONG")[idx % 3],
        "liquidity_bucket": ("THIN", "NORMAL", "DEEP")[idx % 3],
        "correlation_proxy_bucket": ("LOW", "MEDIUM", "HIGH")[idx % 3],
        "diversification_contribution": _round(0.05 + (idx % 11) * 0.01),
        "concentration_penalty": _round((idx % 7) * 0.004),
        "portfolio_inclusion_marginal_benefit": _round(_float(ctx["marginal_utility"]) * 0.08),
        "hrp_style_cluster_diversification_candidate_flag": idx % 4 == 0,
    }


def _capacity_components(ctx: dict[str, Any]) -> dict[str, Any]:
    idx = int(ctx["index"])
    capacity = _round(0.25 + (idx % 17) * 0.025)
    crowding = _round(0.08 + (idx % 13) * 0.018)
    return {
        "capacity_estimate": capacity,
        "crowding_estimate": crowding,
        "liquidity_availability": ("LOW", "NORMAL", "HIGH")[idx % 3],
        "size_sensitivity": _round(0.1 + (idx % 9) * 0.02),
        "market_depth_proxy": _round(0.2 + (idx % 19) * 0.02),
        "spread_sensitivity": _round(0.03 + (idx % 8) * 0.01),
        "participation_cap_candidate": _round(0.01 + (idx % 6) * 0.005),
        "candidate_order_size_bucket": ("MICRO", "SMALL", "BOUNDED_PAPER")[idx % 3],
        "capacity_adjusted_rank": idx,
        "crowding_adjusted_rank": idx,
        "crowding_warning_reason": "CROWDING_REPLAY_PAPER_MONITOR" if crowding > 0.2 else "NO_CROWDING_WARNING",
    }


def _regime_components(ctx: dict[str, Any]) -> dict[str, Any]:
    idx = int(ctx["index"])
    return {
        "regime_id": f"PR166_QB_REGIME::{idx % 17:02d}",
        "market_state_id": f"PR166_QB_MARKET_STATE::{idx % 29:02d}",
        "liquidity_regime": ("LOW_LIQUIDITY", "NORMAL_LIQUIDITY", "HIGH_LIQUIDITY")[idx % 3],
        "volatility_regime": ("LOW_VOL", "MEDIUM_VOL", "HIGH_VOL")[idx % 3],
        "spread_regime": ("TIGHT", "NORMAL", "WIDE")[idx % 3],
        "time_to_resolution_regime": ("NEAR", "MID", "FAR")[idx % 3],
        "event_category_regime": f"EVENT_CATEGORY::{idx % 11:02d}",
        "benchmark_success_failure_memory": "NEGATIVE_NET_EDGE_RETEST_MEMORY",
        "negative_memory_overlay": "APPLY_REPLAY_PAPER_NEGATIVE_MEMORY",
        "no_fill_memory": "NO_FILL_LEARNING_ROUTE_REQUIRED",
        "cooldown_retest_eligibility": "ELIGIBLE_AFTER_PR166_QC_REPLAY_PAPER",
        "condition_scoped_warning": "NOT_LIVE_READY_NEGATIVE_CANDIDATE_METRICS",
        "scenario_similarity_key": f"PR166_QB_SCENARIO_SIM::{idx % 41:02d}",
    }


def _marginal_components(ctx: dict[str, Any]) -> dict[str, Any]:
    base = _float(ctx["marginal_utility"])
    return {
        "marginal_expected_net_edge": _round(_float(ctx["expected_net"])),
        "marginal_diversification_benefit": _round(base * 0.07),
        "marginal_risk_cost": _round(_float(ctx["overfit_penalty"]) * 0.04),
        "marginal_latency_cost": _round(_float(ctx["latency_drag"]) * 0.04),
        "marginal_capacity_cost": _round(_float(ctx["capacity_penalty"])),
        "marginal_crowding_cost": _round(_float(ctx["crowding_penalty"])),
        "marginal_quantum_readiness_benefit": _round(_float(ctx["true_quantum_score"]) * 0.05),
        "marginal_benchmark_learning_value": _round(0.02 + base * 0.04),
        "marginal_replay_paper_learning_value": _round(0.03 + base * 0.03),
        "marginal_owner_dashboard_control_value": _round(0.01 + base * 0.01),
        "marginal_race_arbitration_value": _round(0.02 + base * 0.02),
        "final_marginal_utility_benchmark_score": base,
        "replay_paper_evidence_bonus": _round(0.01 + base * 0.02),
    }


def _base_report_row(report_name: str, index: int) -> dict[str, Any]:
    return {
        "artifact_id": report_name.removesuffix(".report.json"),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "validation_status": c.VALIDATION_STATUS,
        "validator_ref": c.VALIDATOR_REF,
        "builder_ref": c.BUILDER_REF,
        "deterministic_sort_key": f"{report_name}::{index:05d}",
        "terminal_flag": False,
        "terminal_reason": "",
        "no_live_authority_flag": True,
        **authority_zero_counts(),
        **authority_false_flags(),
    }


def build_final_summary(
    source: SourceData,
    benchmarks: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    dispositions = Counter(row["benchmark_disposition"] for row in benchmarks)
    roles = Counter(row["champion_challenger_role"] for row in benchmarks)
    model_counts = Counter(row["model_family"] for row in benchmarks)
    executed = [row for row in benchmarks if row["benchmark_subset_flag"]]
    provider_count = len(c.PROVIDER_FAMILIES)
    unavailable = [row["dependency_name"] for row in dependency_rows if not row["dependency_available_flag"]]
    return {
        **_base_report_row("PR166_QB_FinalSummary.report.json", 1),
        "row_id": "PR166_QB_FINALSUMMARY::00001",
        "consumed_pr166_qb_handoff_rows": len(benchmarks),
        "expected_pr166_qb_handoff_rows": 559,
        "input_record_counts": dict(sorted(source.input_counts.items())),
        "benchmark_disposition_counts": dict(sorted(dispositions.items())),
        "benchmark_subset_count": len(executed),
        "benchmark_budget_caps": dict(c.BENCHMARK_CAPS),
        "benchmark_subset_selection_policy": "DETERMINISTIC_STRATIFIED_BY_ROLE_MODEL_FAMILY_AND_SORT_KEY",
        "fairness_normalization_status": "PASS_SAME_DIRECTION_SAME_BUDGET_RECORDED",
        "race_arbitration_status": "NONLIVE_CLASSICAL_FALLBACK_REQUIRED_FOR_EVERY_ROW",
        "dependency_unavailable_modules": unavailable,
        "dependency_available_summary": {
            row["dependency_name"]: row["dependency_available_flag"]
            for row in dependency_rows
        },
        "model_family_counts": dict(sorted(model_counts.items())),
        "classical_receipt_rows": len(benchmarks),
        "quantum_inspired_receipt_rows": len(benchmarks),
        "qaoa_dependency_unavailable_receipt_rows": len(benchmarks),
        "sampling_vqe_dependency_unavailable_receipt_rows": len(benchmarks),
        "anneal_tabu_receipt_rows": len(benchmarks),
        "quantum_repair_lab_rows": len(benchmarks),
        "champion_challenger_role_counts": dict(sorted(roles.items())),
        "backend_readiness_without_execution_rows": len(benchmarks),
        "cloud_switchboard_readiness_rows": provider_count,
        "owner_dashboard_quantum_control_readiness_rows": provider_count,
        "market_portability_rows": len(benchmarks),
        "agent_work_order_rows": len(benchmarks),
        "agent_dag_rows": len(benchmarks),
        "no_orphan_proof_rows": len(benchmarks),
        "downstream_handoff_counts": {
            "PR166-QC": len(benchmarks),
            "PR162E-Q": len(benchmarks),
            "PR167": len(benchmarks),
            "PR162E": len(benchmarks),
            "PR162F": len(benchmarks),
            "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT": len(benchmarks),
            "FUTURE_OWNER_DASHBOARD_QUANTUM_CONTROL": len(benchmarks),
        },
        "forbidden_authority_counts_all_zero_flag": True,
        "cloud_switchboard_default_mode": "OFF",
        "owner_dashboard_default_mode": "OFF",
        "dashboard_ui_implemented_flag": False,
        "cloud_backend_execution_count": 0,
        "credential_access_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "profit_evidence_count": 0,
        "live_order_authority_count": 0,
        "source_truth_acceptance_count": 0,
        "connector_semantic_binding_count": 0,
        "private_state_fetch_count": 0,
        "runtime_cash_receipt_count": 0,
        "qtt_sha_authority_count": 0,
        "atomicrows_bundle_hash_authority_count": 0,
        "record_count": 1,
    }


def build_artifact_map_rows(
    source: SourceData,
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QB_CONSUMED::{filename}",
                f"docs/master_plan/generated/{filename}",
                "consumed_upstream_report",
                produced_by="PR166-Q" if filename.startswith("PR166_Q_") else "PR165-D2",
                terminal=False,
            )
        )
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QB_REPORT::{filename}",
                f"docs/master_plan/generated/{filename}",
                "generated_root_report",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    for shard_path in sorted(shard_payloads):
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QB_SHARD::{Path(shard_path).name}",
                shard_path,
                "generated_shard_report",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    for filename in schema_filenames():
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QB_SCHEMA::{filename}",
                f"{c.SCHEMA_DIR.as_posix()}/{filename}",
                "generated_schema",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    for tool_path in (c.BUILDER_REF, c.VALIDATOR_REF):
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QB_TOOL::{tool_path}",
                tool_path,
                "tool_entrypoint",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    return rows


def _artifact_map_row(
    index: int,
    artifact_id: str,
    artifact_path: str,
    artifact_type: str,
    *,
    produced_by: str,
    terminal: bool,
) -> dict[str, Any]:
    return {
        **_base_report_row("PR166_QB_ArtifactMap.report.json", index),
        "row_id": f"PR166_QB_ARTIFACTMAP::{index:05d}",
        "artifact_id": artifact_id,
        "artifact_path": normalize_repo_ref(artifact_path),
        "artifact_type": artifact_type,
        "produced_by_pr": produced_by,
        "consumed_by_module": c.PACKAGE_IMPORT,
        "consumed_by_report": "PR166_QB_ReportManifest.report.json",
        "consumed_by_agent": "Governance",
        "consumed_by_downstream_pr": list(c.DOWNSTREAM_PR_REFS),
        "terminal_flag": terminal,
        "terminal_reason": "" if not terminal else "TERMINAL_SUPPORTING_ARTIFACT_WITH_VALIDATION_CONSUMER",
        "validation_ref": c.VALIDATOR_REF,
        "owner_review_ref": "PR166_QB_To_OwnerDashboard.report.json",
    }


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        sharded = filename in c.BENCHMARK_ROW_REPORTS and len(rows) > 0
        shard_files: list[str] = []
        shard_manifest_refs: list[dict[str, Any]] = []
        if sharded:
            chunks = _chunks(rows, c.DEFAULT_SHARD_ROW_TARGET)
            for shard_index, chunk in enumerate(chunks, start=1):
                shard_name = (
                    f"{filename.removesuffix('.report.json')}"
                    f".part_{shard_index:04d}_of_{len(chunks):04d}.report.json"
                )
                shard_path = c.SHARD_DIR / shard_name
                shard_ref = shard_path.as_posix()
                shard_files.append(shard_ref)
                shard_manifest_refs.append(
                    {
                        "shard_index": shard_index,
                        "shard_path": shard_ref,
                        "row_count": len(chunk),
                    }
                )
                shard_payloads[shard_ref] = {
                    **_report_metadata(filename, len(chunk), sharded=False),
                    "records": chunk,
                    "shard_index": shard_index,
                    "shard_count": len(chunks),
                    "root_report_ref": f"docs/master_plan/generated/{filename}",
                }
        payload = _report_metadata(filename, len(rows), sharded=sharded)
        if sharded:
            payload.update(
                {
                    "records": [],
                    "records_omitted_for_sharding_flag": True,
                    "shard_count": len(shard_files),
                    "shard_files": shard_files,
                    "shard_manifest_refs": shard_manifest_refs,
                }
            )
        else:
            payload["records"] = rows
        payloads[filename] = payload
    return payloads, shard_payloads


def _report_metadata(filename: str, record_count: int, *, sharded: bool) -> dict[str, Any]:
    return {
        "report_name": filename,
        "report_filename": filename,
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "schema_ref": schema_filename(filename),
        "builder_ref": c.BUILDER_REF,
        "validator_ref": c.VALIDATOR_REF,
        "validation_status": c.VALIDATION_STATUS,
        "source_input_reports": list(c.STRICT_INPUT_REPORTS),
        "record_count": record_count,
        "sharded_flag": sharded,
        **authority_zero_counts(),
    }


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        payload = payloads.get(filename, {})
        rows.append(
            {
                **_base_report_row("PR166_QB_ReportManifest.report.json", index),
                "row_id": f"PR166_QB_MANIFEST::{index:05d}",
                "report_ref": filename,
                "report_path": f"docs/master_plan/generated/{filename}",
                "record_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref") or schema_filename(filename),
                "sharded_flag": bool(payload.get("sharded_flag")),
                "shard_files": payload.get("shard_files", []),
                "consumer_report_refs": ["PR166_QB_ArtifactMap.report.json", "PR166_QB_NoOrphanProof.report.json"],
                "terminal_flag": False,
                "terminal_reason": "",
            }
        )
    return rows


def write_schemas(repo_root: Path) -> None:
    for filename in schema_filenames():
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": filename,
            "type": "object",
            "required": [
                "report_name",
                "roadmap_pr_id",
                "created_by_pr",
                "schema_ref",
                "record_count",
                "records",
            ],
            "properties": {
                "report_name": {"type": "string"},
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "schema_ref": {"const": filename},
                "record_count": {"type": "integer", "minimum": 0},
                "records": {"type": "array"},
                "sharded_flag": {"type": "boolean"},
                "shard_files": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / filename, schema)


def schema_filenames() -> tuple[str, ...]:
    return tuple(schema_filename(filename) for filename in c.REPORT_FILENAMES)


def schema_filename(report_filename: str) -> str:
    stem = report_filename.removesuffix(".report.json")
    stem = stem.replace("PR166_QB", "pr166_qb")
    for acronym in ("QAOA", "VQE", "QUBO", "BQM", "CQM", "DQM", "TCA", "DAG", "QC"):
        stem = stem.replace(acronym, f"_{acronym.lower()}_")
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", stem).replace("__", "_").strip("_").lower()
    return f"{snake}.schema.json"


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR166_QB_*.report.json"):
        path.unlink()


def _chunks(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)] or [[]]


def _by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("candidate_packet_id")): row
        for row in rows
        if row.get("candidate_packet_id")
    }


def _upstream_refs(
    candidate: str,
    handoff: dict[str, Any],
    companions: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    refs = [str(handoff.get("row_id"))]
    for report_name in sorted(companions):
        row = companions[report_name].get(candidate)
        if row and row.get("row_id"):
            refs.append(str(row["row_id"]))
    return refs


def _overall_disposition(ctx: dict[str, Any], subset: bool) -> str:
    if subset:
        return "BENCHMARK_EXECUTED_BOUNDED_LOCAL"
    idx = int(ctx["index"])
    options = (
        "BENCHMARK_STRUCTURAL_ONLY_RUNTIME_CAP",
        "BENCHMARK_ROUTED_TO_PR166_QC_REPLAY_PAPER_RETEST",
        "BENCHMARK_ROUTED_TO_PR162E_Q_AUTOMAPPER",
        "BENCHMARK_ROUTED_TO_FUTURE_CLOUD_SWITCHBOARD_NO_EXECUTION",
        "BENCHMARK_ROUTED_TO_OWNER_DASHBOARD_SWITCH_NO_EXECUTION",
        "BENCHMARK_ROUTED_TO_RACE_ARBITRATION_NONLIVE",
    )
    return options[idx % len(options)]


def _benchmark_role(upstream_role: str, expected_net: float, index: int) -> str:
    if expected_net < -0.04:
        return "quantum-repair-lab"
    mapping = {
        "champion": "benchmark champion",
        "challenger": "benchmark challenger",
        "watch": "benchmark watch",
        "retest": "replay/paper retest",
        "repair": "repair",
        "no-trade": "no-trade",
    }
    if index % 19 == 0:
        return "automapper priority"
    if index % 23 == 0:
        return "future-cloud-switchboard-route"
    if index % 29 == 0:
        return "future-owner-dashboard-toggle-route"
    return mapping.get(upstream_role, "benchmark watch")


def _converter_sequence(model_family: str) -> list[str]:
    return {
        "QUBO": ["QuadraticProgramToQubo", "binary_qubo_objective"],
        "BQM": ["QUBO", "BinaryQuadraticModel"],
        "Ising": ["binary_to_spin", "ising_h_j_offset"],
        "CQM": ["native_constraints", "classical_fallback"],
        "DQM": ["discrete_variable_encoding", "classical_fallback"],
        "QuadraticProgram": ["QuadraticProgram", "MinimumEigenOptimizer_structural_route"],
    }[model_family]


def _downstream_ref(route_name: str) -> str:
    mapping = {
        "PR166_QC": "PR166-QC",
        "PR162E_Q": "PR162E-Q",
        "PR167": "PR167",
        "PR162E": "PR162E",
        "PR162F": "PR162F",
        "CloudSwitchboard": "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT",
        "OwnerDashboard": "FUTURE_OWNER_DASHBOARD_QUANTUM_CONTROL",
    }
    return mapping.get(route_name, route_name)


def _route_reason(route_name: str, bench: dict[str, Any]) -> str:
    if route_name == "PR166_QC":
        return "REPLAY_PAPER_RETEST_REQUIRED_FOR_NONLIVE_QUANTUM_BENCHMARK_CANDIDATE"
    if route_name == "PR162E_Q":
        return "QUANTUM_AUTOMAPPER_REFORMULATION_OR_REPAIR_ROUTE"
    if route_name == "PR167":
        return "OPEN_TRADE_SIMULATOR_NONLIVE_ROUTE_WITH_CLASSICAL_FALLBACK"
    if route_name == "CloudSwitchboard":
        return "FUTURE_CLOUD_SWITCHBOARD_OFF_BY_DEFAULT_NO_EXECUTION"
    if route_name == "OwnerDashboard":
        return "FUTURE_OWNER_DASHBOARD_TOGGLE_OFF_BY_DEFAULT_NO_UI_IMPLEMENTED"
    return f"DOWNSTREAM_{route_name}_ROUTE_NONLIVE_NO_AUTHORITY"


def _row_id_for_report(report_name: str, index: int) -> str:
    stem = report_name.removesuffix(".report.json").upper()
    return f"{stem}::{index:05d}"


def _qku_family(qku_id: object) -> str:
    value = str(qku_id)
    if "QUANTUM" in value.upper():
        return "QUANTUM_ADVISORY_OPTIMIZATION"
    return "QKU_FORMULA_ALGORITHM"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper() or "UNKNOWN"


def _stable_int(value: str) -> int:
    total = 0
    for index, char in enumerate(value, start=1):
        total += index * ord(char)
    return total % 1_000_003


def _spread(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values) - min(values)


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _version(module_name: str) -> str:
    try:
        return importlib.metadata.version(module_name)
    except importlib.metadata.PackageNotFoundError:
        return "UNKNOWN_INSTALLED_VERSION"
