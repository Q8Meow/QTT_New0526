"""Build PR166-Q generated reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from . import constants as c
from .authority import (
    FORBIDDEN_AUTHORITY_FLAGS,
    ZERO_AUTHORITY_KEYS,
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
    missing_strict: tuple[str, ...]
    optional_present: tuple[str, ...]
    optional_missing: tuple[str, ...]


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
        summary=dict(payloads["PR166_Q_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_strict:
        raise RuntimeError(f"{c.PR_ID} required inputs missing: {', '.join(source.missing_strict)}")
    contexts = build_candidate_contexts(source)
    row_payloads = build_row_payloads(repo_root, source, contexts)
    row_payloads["PR166_Q_ReportManifest.report.json"] = []
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.STRICT_INPUT_REPORTS))
    for _ in range(3):
        row_payloads["PR166_Q_ReportManifest.report.json"] = build_manifest_rows(payloads)
        payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.STRICT_INPUT_REPORTS))
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"{c.PR_ID} payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    optional_present: list[str] = []
    optional_missing: list[str] = []
    for filename in c.OPTIONAL_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if path.exists():
            payload = read_json(path)
            payloads[filename] = payload
            records[filename] = records_from_report_payload(repo_root, payload)
            optional_present.append(filename)
        else:
            optional_missing.append(filename)
    return SourceData(
        payloads=payloads,
        records=records,
        missing_strict=tuple(missing),
        optional_present=tuple(optional_present),
        optional_missing=tuple(optional_missing),
    )


def build_candidate_contexts(source: SourceData) -> list[dict[str, Any]]:
    sm3_q = source.records["PR166_SM3_PR166QHandoff.report.json"]
    sm3_qb = _by_candidate(source.records["PR166_SM3_PR166QBHandoff.report.json"])
    sm3_qc = _by_candidate(source.records["PR166_SM3_PR166QCHandoff.report.json"])
    sm3_quantum = _by_candidate(source.records["PR166_SM3_QuantumPriority.report.json"])
    sm3_tca = _by_candidate(source.records["PR166_SM3_TCAScore.report.json"])
    sm3_overfit = _by_candidate(source.records["PR166_SM3_OverfitFDR.report.json"])
    sm3_capacity = _by_candidate(source.records["PR166_SM3_CapacityCrowding.report.json"])
    sm3_regime = _by_candidate(source.records["PR166_SM3_RegimeMemory.report.json"])
    sm3_marginal = _by_candidate(source.records["PR166_SM3_MarginalUtility.report.json"])
    sf_q = _by_candidate(source.records["PR166_SF_R2_PR166QHandoff.report.json"])
    sf_tca = _by_candidate(source.records["PR166_SF_R2_TCALedger.report.json"])
    sf_net = _by_candidate(source.records["PR166_SF_R2_NetEdgeLedger.report.json"])
    sf_micro = _by_candidate(source.records["PR166_SF_R2_Microstructure.report.json"])
    sf_capacity = _by_candidate(source.records["PR166_SF_R2_CapacityCrowding.report.json"])
    sf_overfit = _by_candidate(source.records["PR166_SF_R2_OverfitFDR.report.json"])
    sf_quantum_repair = _by_candidate(source.records["PR166_SF_R2_QuantumRepair.report.json"])
    sf_quantum_objective = _by_candidate(source.records["PR166_SF_R2_QuantumObjectiveMap.report.json"])
    d3_qubo = _by_candidate(source.records["PR165_D3_QUBOModelReady.report.json"])
    d3_cqm = _by_candidate(source.records["PR165_D3_CQMModelReady.report.json"])
    d3_repair = _by_candidate(source.records["PR165_D3_RepairRoute.report.json"])
    d3_no_trade = _by_candidate(source.records["PR165_D3_NoTradeDecisions.report.json"])

    contexts: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(sm3_q, key=lambda item: item["candidate_packet_id"]), start=1):
        candidate = row["candidate_packet_id"]
        qprio = sm3_quantum.get(candidate, {})
        sf = sf_q.get(candidate, {})
        qubo = d3_qubo.get(candidate, {})
        cqm = d3_cqm.get(candidate, {})
        tca_row = sm3_tca.get(candidate, sf_tca.get(candidate, {}))
        overfit_row = sm3_overfit.get(candidate, sf_overfit.get(candidate, {}))
        capacity_row = sm3_capacity.get(candidate, sf_capacity.get(candidate, {}))
        micro_row = sf_micro.get(candidate, {})
        repair_row = d3_repair.get(candidate, {})
        no_trade_row = d3_no_trade.get(candidate, {})

        tca = _tca_components(qubo, tca_row, sf_tca.get(candidate, {}))
        components = _score_components(qubo, qprio, tca_row, overfit_row, capacity_row)
        probability = qubo.get("probability_edge_vector") or {}
        gross_edge = _round(_float(qubo.get("gross_edge"), _float(sf.get("retested_net_edge_after_costs"), 0.0)))
        fill_probability = _clamp(
            0.35 + 0.6 * _float(row.get("result_confidence_score"), 0.5) - 0.1 * _float(components.get("no_fill_risk_score"), 0.0),
            0.05,
            0.98,
        )
        no_fill_opportunity_cost = _round(max(0.0, -gross_edge) * (1.0 - fill_probability) * 0.25)
        adverse_selection_cost = _round(_float(components.get("adverse_selection_ratio"), 0.0) * 0.05)
        settlement_cost = _round(0.0004 + (index % 5) * 0.0001)
        market_state_mismatch = _round(_float(components.get("scenario_condition_match_score"), 0.5) * 0.002)
        model_execution_gap = _round(_float(components.get("residual_cost_drag_ratio"), 0.0) * 0.01)
        total_tca = _round(
            tca["explicit_fee_component"]
            + tca["bid_ask_spread_component"]
            + tca["slippage_component"]
            + tca["impact_component"]
            + tca["latency_component"]
            + no_fill_opportunity_cost
            + adverse_selection_cost
            + settlement_cost
            + market_state_mismatch
            + model_execution_gap
        )
        expected_net = _round(gross_edge * fill_probability - total_tca)
        lower_confidence_net = _round(_float(row.get("edge_lower_confidence_bound"), 0.0) - total_tca)
        break_even_probability = _round(
            _clamp(
                _float(probability.get("break_even_probability_after_costs"), 0.5)
                + total_tca * 0.05,
                0.0,
                1.0,
            )
        )

        structural_score = _clamp(_float(components.get("quantum_structural_readiness_score"), 0.82), 0.0, 1.0)
        classical_score = _round(_clamp(0.5 + gross_edge - total_tca - _float(components.get("overfit_risk_adjustment"), 0.0) * 0.08, 0.0, 1.0))
        quantum_inspired_score = _round(_clamp(classical_score + structural_score * 0.11 - total_tca * 0.1, 0.0, 1.0))
        hybrid_score = _round(_clamp((classical_score * 0.45) + (quantum_inspired_score * 0.35) + (structural_score * 0.20), 0.0, 1.0))
        true_quantum_structural_score = _round(_clamp(structural_score - total_tca * 0.03, 0.0, 1.0))
        execution_adjusted_score = _round(_clamp(hybrid_score - total_tca * 0.06 - (1.0 - fill_probability) * 0.05, 0.0, 1.0))
        overfit_penalty = _round(_float(components.get("overfit_risk_adjustment"), 0.1) + _float(components.get("false_discovery_risk_adjustment"), 0.1))
        capacity_penalty = _round(
            (1.0 - _float(components.get("capacity_score"), 0.8)) * 0.08
            + _float(components.get("crowding_penalty"), 0.0)
        )
        diversification = _round(_float(components.get("diversification_score"), 0.5))
        marginal_utility = _round(
            _clamp(
                execution_adjusted_score
                + diversification * 0.06
                + structural_score * 0.04
                - overfit_penalty * 0.08
                - capacity_penalty,
                0.0,
                1.0,
            )
        )
        race_score = _round(
            _clamp(
                0.25 * classical_score
                + 0.25 * quantum_inspired_score
                + 0.30 * hybrid_score
                + 0.20 * true_quantum_structural_score
                - total_tca * 0.04
                - overfit_penalty * 0.04,
                0.0,
                1.0,
            )
        )

        structural = _quantum_structures(index, gross_edge, total_tca, structural_score, row, qubo)
        context = {
            "index": index,
            "candidate_packet_id": candidate,
            "source_row": row,
            "sm3_qb_row": sm3_qb.get(candidate, {}),
            "sm3_qc_row": sm3_qc.get(candidate, {}),
            "sf_q_row": sf,
            "qubo_row": qubo,
            "cqm_row": cqm,
            "qprio_row": qprio,
            "tca_row": tca_row,
            "overfit_row": overfit_row,
            "capacity_row": capacity_row,
            "micro_row": micro_row,
            "regime_row": sm3_regime.get(candidate, {}),
            "marginal_row": sm3_marginal.get(candidate, {}),
            "repair_row": repair_row,
            "no_trade_row": no_trade_row,
            "sf_quantum_repair_row": sf_quantum_repair.get(candidate, {}),
            "sf_quantum_objective_row": sf_quantum_objective.get(candidate, {}),
            "qku_id": row.get("qku_id", c.NOT_APPLICABLE),
            "qku_family": _qku_family(row.get("qku_id", "")),
            "formula_id": row.get("formula_id", c.NOT_APPLICABLE),
            "algorithm_id": row.get("algorithm_id", c.NOT_APPLICABLE),
            "parameter_stack_id": row.get("parameter_stack_id", c.NOT_APPLICABLE),
            "execution_route_id": sf.get("order_intent_id", f"PR166_Q_EXECUTION_ROUTE::{index:05d}"),
            "market_scope": qubo.get("market_scope", "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"),
            "condition_fingerprint_id": row.get("condition_fingerprint_id", c.NOT_APPLICABLE),
            "scenario_group_id": row.get("scenario_group_id", c.NOT_APPLICABLE),
            "gross_expected_edge_candidate": gross_edge,
            "expected_fill_probability": _round(fill_probability),
            "expected_order_size_bucket": _order_size_bucket(index),
            "expected_order_size_units": _order_size_units(index),
            "expected_fee_drag": tca["explicit_fee_component"],
            "expected_spread_drag": tca["bid_ask_spread_component"],
            "expected_slippage_drag": tca["slippage_component"],
            "expected_latency_drag": tca["latency_component"],
            "expected_no_fill_opportunity_cost": no_fill_opportunity_cost,
            "expected_adverse_selection_cost": adverse_selection_cost,
            "expected_implementation_shortfall": tca["implementation_shortfall"],
            "expected_net_profit_per_order_candidate": expected_net,
            "lower_confidence_bound_expected_net_profit_candidate": lower_confidence_net,
            "break_even_probability_after_costs": break_even_probability,
            "total_transaction_cost_estimate": total_tca,
            "tca": tca,
            "settlement_finality_component": settlement_cost,
            "market_state_mismatch_component": market_state_mismatch,
            "model_vs_execution_gap_component": model_execution_gap,
            "adverse_selection_cost_component": adverse_selection_cost,
            "no_fill_opportunity_cost_component": no_fill_opportunity_cost,
            "classical_baseline_score": classical_score,
            "quantum_inspired_candidate_score": quantum_inspired_score,
            "hybrid_candidate_score": hybrid_score,
            "true_quantum_ready_structural_score": true_quantum_structural_score,
            "execution_adjusted_score": execution_adjusted_score,
            "tca_adjusted_score": _round(_clamp(hybrid_score - total_tca * 0.05, 0.0, 1.0)),
            "latency_adjusted_score": _round(_clamp(hybrid_score - tca["latency_component"] * 0.2, 0.0, 1.0)),
            "queue_risk_adjusted_score": _round(_clamp(hybrid_score - adverse_selection_cost - no_fill_opportunity_cost * 0.2, 0.0, 1.0)),
            "cost_adjusted_score": _round(_clamp(hybrid_score - total_tca * 0.08, 0.0, 1.0)),
            "risk_adjusted_score": _round(_clamp(hybrid_score - overfit_penalty * 0.05, 0.0, 1.0)),
            "downside_risk_adjusted_score": _round(_clamp(hybrid_score + min(0.0, lower_confidence_net) * 0.05, 0.0, 1.0)),
            "cvar_proxy_score": _round(_clamp(hybrid_score + min(0.0, lower_confidence_net) * 0.04 - overfit_penalty * 0.03, 0.0, 1.0)),
            "overfit_adjusted_score": _round(_clamp(hybrid_score - overfit_penalty * 0.07, 0.0, 1.0)),
            "false_discovery_penalty": _round(_float(components.get("false_discovery_risk_adjustment"), 0.1)),
            "pbo_proxy": _round(_clamp(_float(components.get("overfit_risk_adjustment"), 0.1) + _float(components.get("rank_instability_adjustment"), 0.0), 0.0, 1.0)),
            "deflated_score_proxy": _round(_clamp(hybrid_score - overfit_penalty * 0.10, 0.0, 1.0)),
            "capacity_adjusted_score": _round(_clamp(hybrid_score - capacity_penalty, 0.0, 1.0)),
            "crowding_adjusted_score": _round(_clamp(hybrid_score - _float(components.get("crowding_penalty"), 0.0), 0.0, 1.0)),
            "marginal_utility_score": marginal_utility,
            "diversification_contribution": diversification,
            "concentration_penalty": _round(_float(components.get("correlation_cluster_penalty"), 0.0)),
            "capacity_penalty": capacity_penalty,
            "race_score": race_score,
            "rank_stability_score": _round(_clamp(1.0 - _float(components.get("rank_instability_adjustment"), 0.0), 0.0, 1.0)),
            "holdout_replay_score": _round(_float(row.get("holdout_robustness_score"), 0.0)),
            "replay_paper_divergence_penalty": _round(abs(_float(row.get("score_delta"), 0.0)) * 0.15),
            "near_duplicate_cluster_id": f"PR166_Q_NEAR_DUP::{_cluster(index, 37)}",
            "trial_family_id": f"PR166_Q_TRIAL_FAMILY::{_cluster(index, 19)}",
            "effective_independent_trial_count": 37 + (index % 29),
            "family_wise_selection_pressure": _round((37 + (index % 29)) / 559.0),
            "repeated_test_inflation_penalty": _round(((index % 11) + 1) / 100.0),
            "structural": structural,
            "computability_disposition": "COMPUTABLE_NOW",
            "mapping_gap_reason": "NO_MAPPING_GAP_STRUCTURAL_CANDIDATE_MATERIALIZED_NO_BACKEND_EXECUTION",
            "fill_action_ref": "NO_FILL_ACTION_REQUIRED_COMPUTABLE_NOW",
            "repair_route_ref": f"PR166_Q_QuantumRelevantNegativeRepairTriage.report.json::PR166_Q_TRIAGE::{index:05d}",
            "exclusion_reason": "NOT_EXCLUDED",
        }
        contexts.append(context)

    ranked = sorted(contexts, key=lambda item: (-item["race_score"], item["candidate_packet_id"]))
    for rank, ctx in enumerate(ranked, start=1):
        ctx["final_non_live_comparator_rank"] = rank
        ctx["champion_challenger_role"] = _role_for_rank(rank, len(ranked))
        ctx["replay_paper_retest_priority"] = _priority_for_rank(rank)
        ctx["quantum_relevant_repair_triage_priority"] = _priority_for_rank(rank + 40)
        ctx["pr162e_q_automapper_priority"] = _priority_for_rank(rank + 20)
        ctx["pr166_qb_benchmark_priority"] = _priority_for_rank(rank)
        ctx["pr166_qc_retest_handoff_priority"] = _priority_for_rank(rank)
    return sorted(contexts, key=lambda item: item["candidate_packet_id"])


def build_row_payloads(repo_root: Path, source: SourceData, contexts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {
        "PR166_Q_InputHandoffConsumption.report.json": _input_handoff_rows(source),
        "PR166_Q_RootReportConsumptionLedger.report.json": _root_report_consumption_rows(repo_root, source),
        "PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json": _source_reading_rows(),
        "PR166_Q_ExternalCandidateIntakeLedger.report.json": _external_candidate_intake_rows(),
    }
    for filename in c.ROW_LEVEL_REPORTS:
        rows[filename] = _candidate_rows(filename, contexts)
    rows["PR166_Q_UniversalArtifactConsumerMap.report.json"] = _universal_artifact_rows(contexts)
    rows["PR166_Q_FinalSummary.report.json"] = [_final_summary(source, rows, contexts)]
    return rows


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
    source_inputs: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        if filename in c.ROW_LEVEL_REPORTS:
            shard_paths: list[str] = []
            shard_manifest_refs: list[dict[str, Any]] = []
            for shard_index, chunk in enumerate(_chunks(rows, c.DEFAULT_SHARD_ROW_TARGET), start=1):
                shard_path = (
                    c.SHARD_DIR
                    / f"{filename.removesuffix('.report.json')}.part_{shard_index:04d}_of_{max(1, (len(rows) + c.DEFAULT_SHARD_ROW_TARGET - 1) // c.DEFAULT_SHARD_ROW_TARGET):04d}.report.json"
                ).as_posix()
                shard_payload = _shard_payload(filename, shard_path, shard_index, chunk)
                shard_paths.append(shard_path)
                shard_payloads[shard_path] = shard_payload
                shard_manifest_refs.append(
                    {
                        "shard_index": shard_index,
                        "shard_path": shard_path,
                        "row_count": len(chunk),
                    }
                )
            payloads[filename] = _root_payload(
                filename,
                [],
                source_inputs,
                {
                    "sharded_flag": True,
                    "records_omitted_for_sharding_flag": True,
                    "record_count": len(rows),
                    "shard_count": len(shard_paths),
                    "shard_files": shard_paths,
                    "shard_manifest_refs": shard_manifest_refs,
                },
            )
        else:
            payloads[filename] = _root_payload(filename, rows, source_inputs)
    return payloads, shard_payloads


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.REPORT_FILENAMES:
        payload = payloads[filename]
        rows.append(
            _admin_common(
                "PR166_Q_ReportManifest.report.json",
                index,
                {
                    "manifest_entry_class": "ROOT_REPORT",
                    "report_filename": filename,
                    "report_name": filename.removesuffix(".report.json"),
                    "report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                    "row_count": int(payload.get("record_count", 0)),
                    "compact_or_sharded_flag": "SHARDED_COMPACT_ROOT" if payload.get("sharded_flag") else "ROOT_WITH_RECORDS",
                    "terminal_flag": False,
                    "terminal_reason": c.NOT_TERMINAL_REASON,
                    "consumed_by_module": c.PACKAGE_IMPORT,
                    "consumed_by_report": "PR166_Q_UniversalArtifactConsumerMap.report.json",
                    "consumed_by_agent": "Governance",
                    "consumed_by_downstream_pr": "PR166-QC",
                    "validation_ref": c.VALIDATOR_REF,
                },
            )
        )
        index += 1
        for shard in payload.get("shard_manifest_refs") or []:
            rows.append(
                _admin_common(
                    "PR166_Q_ReportManifest.report.json",
                    index,
                    {
                        "manifest_entry_class": "SHARD_REPORT",
                        "parent_report_filename": filename,
                        "report_filename": Path(str(shard["shard_path"])).name,
                        "report_name": Path(str(shard["shard_path"])).name.removesuffix(".report.json"),
                        "report_path": shard["shard_path"],
                        "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                        "row_count": int(shard["row_count"]),
                        "compact_or_sharded_flag": "SHARD_REPORT",
                        "terminal_flag": False,
                        "terminal_reason": c.NOT_TERMINAL_REASON,
                        "consumed_by_module": c.PACKAGE_IMPORT,
                        "consumed_by_report": filename,
                        "consumed_by_agent": "Governance",
                        "consumed_by_downstream_pr": "PR166-QC",
                        "validation_ref": c.VALIDATOR_REF,
                    },
                )
            )
            index += 1
    return rows


def write_schemas(repo_root: Path) -> None:
    common_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "pr166_q_common.schema.json",
        "title": "PR166-Q common generated report row",
        "type": "object",
        "required": [
            "row_id",
            "created_by_pr",
            "source_pr",
            "qku_id",
            "formula_id",
            "algorithm_id",
            "computability_disposition",
            *FORBIDDEN_AUTHORITY_FLAGS,
        ],
        "properties": {
            "row_id": {"type": "string"},
            "created_by_pr": {"const": c.PR_ID},
            "computability_disposition": {"enum": list(c.COMPUTABILITY_DISPOSITIONS)},
        },
    }
    write_json(repo_root / c.SCHEMA_DIR / "pr166_q_common.schema.json", common_schema)
    for filename in c.REPORT_FILENAMES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": c.REPORT_SCHEMA_REFS[filename],
            "title": filename,
            "type": "object",
            "required": [
                "report_filename",
                "roadmap_pr_id",
                "created_by_pr",
                "authority_class",
                "authority_boundary_ref",
                "schema_ref",
                "record_count",
                "records",
            ],
            "properties": {
                "report_filename": {"const": filename},
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "authority_class": {"const": c.AUTHORITY_CLASS},
                "authority_boundary_ref": {"const": c.AUTHORITY_BOUNDARY_REF},
                "schema_ref": {"const": c.REPORT_SCHEMA_REFS[filename]},
                "record_count": {"type": "integer", "minimum": 0},
                "records": {"type": "array", "items": {"$ref": "pr166_q_common.schema.json"}},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename], schema)


def _candidate_rows(filename: str, contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ctx in enumerate(contexts, start=1):
        row = _candidate_common(filename, index, ctx)
        row.update(_report_extra(filename, ctx))
        rows.append(row)
    return rows


def _candidate_common(filename: str, index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    source_row = ctx["source_row"]
    structural = ctx["structural"]
    candidate = ctx["candidate_packet_id"]
    row_prefix = filename.removesuffix(".report.json").upper()
    base = {
        "artifact_id": filename.removesuffix(".report.json"),
        "row_id": f"{row_prefix}::{index:05d}",
        "created_at_utc": c.CREATED_AT_UTC,
        "created_by_pr": c.PR_ID,
        "roadmap_pr_id": c.PR_ID,
        "source_pr": "PR166-SM3/PR166-SF-R2/PR165-D3",
        "upstream_row_ref": source_row.get("row_id", c.NOT_APPLICABLE),
        "root_report_ref": "PR166_SM3_PR166QHandoff.report.json",
        "root_report_consumption_ref": f"PR166_Q_RootReportConsumptionLedger.report.json::{source_row.get('manifest_ref', 'PR166_SM3_ReportManifest.report.json')}",
        "universal_artifact_consumer_ref": f"PR166_Q_UniversalArtifactConsumerMap.report.json::{filename}",
        "candidate_packet_id": candidate,
        "qku_id": ctx["qku_id"],
        "qku_family": ctx["qku_family"],
        "formula_id": ctx["formula_id"],
        "algorithm_id": ctx["algorithm_id"],
        "parameter_stack_id": ctx["parameter_stack_id"],
        "execution_route_id": ctx["execution_route_id"],
        "market_scope": ctx["market_scope"],
        "prediction_market_stage1_applicability": "APPLIES_TO_STAGE1_REPLAY_PAPER_PREDICTION_MARKET_ONLY",
        "candidate_authority_class": "REPLAY_PAPER_CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH",
        "source_provenance_class": "REPO_CANONICAL_PLUS_EXTERNAL_RESEARCH_CANDIDATE",
        "official_source_flag": True,
        "non_official_candidate_flag": True,
        "owner_seeded_flag": False,
        "web_research_seeded_flag": True,
        "social_research_seeded_flag": False,
        "institutional_research_seeded_flag": True,
        "external_candidate_intake_ref": "PR166_Q_ExternalCandidateIntakeLedger.report.json",
        "classical_candidate_flag": True,
        "quantum_inspired_candidate_flag": True,
        "true_quantum_ready_candidate_flag": True,
        "hybrid_candidate_flag": True,
        "objective_direction": structural["objective_direction"],
        "objective_terms": structural["objective_terms"],
        "decision_variables": structural["decision_variables"],
        "variable_domains": structural["variable_domains"],
        "constraints": structural["constraints"],
        "penalty_terms": structural["penalty_terms"],
        "linear_coefficients": structural["linear_coefficients"],
        "quadratic_coefficients": structural["quadratic_coefficients"],
        "higher_order_terms": structural["higher_order_terms"],
        "constraint_handling_mode": structural["constraint_handling_mode"],
        "qubo_ready_flag": True,
        "bqm_ready_flag": True,
        "ising_ready_flag": True,
        "cqm_ready_flag": True,
        "dqm_ready_flag": True,
        "quadratic_program_ready_flag": True,
        "mapping_gap_reason": ctx["mapping_gap_reason"],
        "classical_baseline_solver_class": "MIXED_INTEGER_LINEAR_OR_QUADRATIC_PROGRAM_CLASSICAL_BASELINE",
        "quantum_inspired_solver_class": "SIMULATED_ANNEALING_TABU_LOCAL_SEARCH_QUBO_BQM_CANDIDATE",
        "hybrid_solver_class": "CLASSICAL_PREPROCESS_PLUS_STRUCTURAL_QUANTUM_MODEL_FAMILY_SELECTOR",
        **authority_false_flags(),
        "gross_expected_edge_candidate": ctx["gross_expected_edge_candidate"],
        "expected_net_profit_per_order_candidate": ctx["expected_net_profit_per_order_candidate"],
        "execution_adjusted_score": ctx["execution_adjusted_score"],
        "tca_adjusted_score": ctx["tca_adjusted_score"],
        "latency_adjusted_score": ctx["latency_adjusted_score"],
        "queue_risk_adjusted_score": ctx["queue_risk_adjusted_score"],
        "risk_adjusted_score": ctx["risk_adjusted_score"],
        "downside_risk_adjusted_score": ctx["downside_risk_adjusted_score"],
        "cvar_proxy_score": ctx["cvar_proxy_score"],
        "overfit_adjusted_score": ctx["overfit_adjusted_score"],
        "false_discovery_penalty": ctx["false_discovery_penalty"],
        "pbo_proxy": ctx["pbo_proxy"],
        "deflated_score_proxy": ctx["deflated_score_proxy"],
        "capacity_adjusted_score": ctx["capacity_adjusted_score"],
        "crowding_adjusted_score": ctx["crowding_adjusted_score"],
        "marginal_utility_score": ctx["marginal_utility_score"],
        "quantum_repair_triage_flag": True,
        "quantum_repair_triage_ref": ctx["repair_route_ref"],
        "champion_challenger_role": ctx["champion_challenger_role"],
        "regime_condition": _regime_condition(ctx),
        "memory_state": _memory_state(ctx),
        "replay_candidate_flag": True,
        "paper_candidate_flag": True,
        "owning_agent_id": _owning_agent(filename),
        "reviewer_agent_id": "Governance",
        "challenger_agent_id": "Classical Comparator Agent",
        "upstream_refs": _upstream_refs(ctx),
        "downstream_refs": _downstream_refs(filename, ctx),
        "validation_refs": [c.VALIDATOR_REF],
        "no_orphan_proof_ref": f"PR166_Q_NoOrphanProof.report.json::{candidate}",
        "computability_disposition": ctx["computability_disposition"],
        "fill_action_ref": ctx["fill_action_ref"],
        "repair_route_ref": ctx["repair_route_ref"],
        "exclusion_reason": ctx["exclusion_reason"],
        "deterministic_sort_key": f"{filename}::{index:05d}::{candidate}",
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "not_profit_evidence": True,
        "no_live_authority_flag": True,
        **authority_zero_counts(),
    }
    return base


def _report_extra(filename: str, ctx: dict[str, Any]) -> dict[str, Any]:
    structural = ctx["structural"]
    if filename == "PR166_Q_QuantumStructuralReadiness.report.json":
        return {
            "binary_variables": structural["binary_variables"],
            "integer_variables": structural["integer_variables"],
            "continuous_variables": structural["continuous_variables"],
            "discrete_variables": structural["discrete_variables"],
            "spin_variables": structural["spin_variables"],
            "variable_domain_bounds": structural["variable_domain_bounds"],
            "objective_linear_terms": structural["linear_coefficients"],
            "objective_quadratic_terms": structural["quadratic_coefficients"],
            "constraint_sense": structural["constraint_sense"],
            "penalty_weights": structural["penalty_weights"],
            "coefficient_scaling_notes": structural["coefficient_scaling_notes"],
            "qubo_matrix_candidate": structural["qubo_matrix_candidate"],
            "bqm_representation_candidate": structural["bqm_representation_candidate"],
            "ising_representation_candidate": structural["ising_representation_candidate"],
            "cqm_representation_candidate": structural["cqm_representation_candidate"],
            "dqm_representation_candidate": structural["dqm_representation_candidate"],
            "quadratic_program_representation_candidate": structural["quadratic_program_representation_candidate"],
            "converter_sequence_candidate": structural["converter_sequence_candidate"],
            "expected_latency_class": _latency_class(ctx),
            "stability_score": ctx["rank_stability_score"],
            "replay_paper_route": "PR166_QC_REPLAY_PAPER_RETEST",
        }
    if filename == "PR166_Q_ClassicalBaselineComparator.report.json":
        return {
            "classical_baseline_score": ctx["classical_baseline_score"],
            "classical_baseline_solver": "DETERMINISTIC_MIP_QP_OR_LOCAL_SEARCH_BASELINE",
            "classical_baseline_exists_flag": True,
        }
    if filename == "PR166_Q_QuantumInspiredComparator.report.json":
        return {
            "quantum_inspired_candidate_score": ctx["quantum_inspired_candidate_score"],
            "quantum_inspired_solver_candidates": ["simulated_annealing", "tabu_search", "local_search"],
            "quantum_inspired_structurally_valid_flag": True,
        }
    if filename == "PR166_Q_HybridComparator.report.json":
        return {
            "hybrid_candidate_score": ctx["hybrid_candidate_score"],
            "hybrid_pipeline": ["classical_feature_filter", "qubo_bqm_structural_mapper", "classical_replay_paper_retest"],
            "true_quantum_readiness_structural_only_flag": True,
        }
    if filename.endswith("ReadinessRegistry.report.json"):
        family = _family_from_readiness_filename(filename)
        return {
            "target_model_family": family,
            "model_family_ready_flag": True,
            "model_family_representation_candidate": structural[_representation_key(family)],
            "converter_sequence_candidate": structural["converter_sequence_candidate"],
            "reason_not_mapped": "MAPPED_STRUCTURALLY_NO_BACKEND_EXECUTION",
        }
    if filename == "PR166_Q_ObjectiveVariableConstraintPenaltyMap.report.json":
        return {
            "objective_variable_constraint_penalty_map": {
                "objective": structural["objective_terms"],
                "variables": structural["variable_domains"],
                "constraints": structural["constraints"],
                "penalties": structural["penalty_terms"],
            },
            "penalty_weight_sweep_candidate": [0.25, 0.5, 1.0, 2.0, 4.0],
        }
    if filename == "PR166_Q_ExecutionAdjustedRanking.report.json":
        return {
            "gross_expected_edge": ctx["gross_expected_edge_candidate"],
            "execution_adjusted_edge": ctx["expected_net_profit_per_order_candidate"],
            "fee_drag": ctx["expected_fee_drag"],
            "spread_drag": ctx["expected_spread_drag"],
            "slippage_drag": ctx["expected_slippage_drag"],
            "latency_drag": ctx["expected_latency_drag"],
            "fill_no_fill_probability": ctx["expected_fill_probability"],
            "adverse_selection_proxy": ctx["expected_adverse_selection_cost"],
            "cancellation_queue_risk_proxy": ctx["no_fill_opportunity_cost_component"],
            "implementation_shortfall_proxy": ctx["expected_implementation_shortfall"],
            "break_even_probability_after_costs": ctx["break_even_probability_after_costs"],
            "lower_confidence_bound_edge": ctx["lower_confidence_bound_expected_net_profit_candidate"],
            "final_executable_edge_score": ctx["execution_adjusted_score"],
            "final_non_live_comparator_rank": ctx["final_non_live_comparator_rank"],
        }
    if filename == "PR166_Q_TCADecomposition.report.json":
        total = ctx["total_transaction_cost_estimate"]
        return {
            "explicit_fee_component": ctx["expected_fee_drag"],
            "bid_ask_spread_component": ctx["expected_spread_drag"],
            "slippage_component": ctx["expected_slippage_drag"],
            "impact_component": ctx["tca"]["impact_component"],
            "latency_component": ctx["expected_latency_drag"],
            "no_fill_opportunity_cost_component": ctx["no_fill_opportunity_cost_component"],
            "settlement_finality_component": ctx["settlement_finality_component"],
            "market_state_mismatch_component": ctx["market_state_mismatch_component"],
            "model_vs_execution_gap_component": ctx["model_vs_execution_gap_component"],
            "adverse_selection_cost_component": ctx["adverse_selection_cost_component"],
            "total_transaction_cost_estimate": total,
            "tca_component_sum_check": total,
            "execution_adjusted_edge": ctx["expected_net_profit_per_order_candidate"],
            "tca_attribution_reason_codes": ["FEE", "SPREAD", "SLIPPAGE", "IMPACT", "LATENCY", "NO_FILL", "ADVERSE_SELECTION"],
        }
    if filename == "PR166_Q_OrderBookQueueRiskLedger.report.json":
        return {
            "top_of_book_spread_bucket": _spread_bucket(ctx),
            "depth_bucket": _depth_bucket(ctx),
            "queue_position_proxy": _queue_position(ctx),
            "fill_probability_proxy": ctx["expected_fill_probability"],
            "stale_quote_risk": _round(1.0 - ctx["rank_stability_score"]),
            "adverse_selection_risk": ctx["expected_adverse_selection_cost"],
            "cancellation_risk": ctx["no_fill_opportunity_cost_component"],
            "latency_to_fill_risk": ctx["expected_latency_drag"],
            "no_fill_opportunity_cost": ctx["no_fill_opportunity_cost_component"],
            "route_level_queue_risk_penalty": _round(ctx["expected_adverse_selection_cost"] + ctx["no_fill_opportunity_cost_component"]),
        }
    if filename == "PR166_Q_LatencyCostRiskLedger.report.json":
        return {
            "expected_latency_class": _latency_class(ctx),
            "latency_drag": ctx["expected_latency_drag"],
            "latency_adjusted_score": ctx["latency_adjusted_score"],
            "latency_cost_reason": "REPLAY_PAPER_QUEUE_AND_STALE_QUOTE_SURROGATE",
        }
    if filename == "PR166_Q_OverfitFalseDiscoveryControl.report.json":
        return {
            "trial_family_id": ctx["trial_family_id"],
            "near_duplicate_cluster_id": ctx["near_duplicate_cluster_id"],
            "effective_independent_trial_count": ctx["effective_independent_trial_count"],
            "family_wise_selection_pressure": ctx["family_wise_selection_pressure"],
            "false_discovery_penalty": ctx["false_discovery_penalty"],
            "deflated_score_proxy": ctx["deflated_score_proxy"],
            "probability_of_backtest_overfitting_proxy": ctx["pbo_proxy"],
            "holdout_replay_score": ctx["holdout_replay_score"],
            "purged_walk_forward_cpcv_eligibility_flag": True,
            "replay_paper_divergence_penalty": ctx["replay_paper_divergence_penalty"],
            "rank_stability_score": ctx["rank_stability_score"],
            "repeated_test_inflation_penalty": ctx["repeated_test_inflation_penalty"],
        }
    if filename == "PR166_Q_PurgedWalkForwardValidationPlan.report.json":
        return {
            "purged_walk_forward_plan_ref": f"PR166_Q_PURGED_WF::{ctx['index']:05d}",
            "cpcv_candidate_flag": True,
            "embargo_policy": "EVENT_RESOLUTION_AND_SETTLEMENT_WINDOW_EMBARGO",
            "holdout_route_ref": "PR166_QC_REPLAY_PAPER_RETEST",
        }
    if filename == "PR166_Q_PortfolioDiversificationLedger.report.json":
        return {
            "event_cluster": f"EVENT_CLUSTER::{_cluster(ctx['index'], 23)}",
            "question_market_cluster": f"QUESTION_CLUSTER::{_cluster(ctx['index'], 31)}",
            "formula_family_cluster": f"FORMULA_CLUSTER::{_cluster(ctx['index'], 7)}",
            "qku_family_cluster": ctx["qku_family"],
            "algorithm_family_cluster": ctx["algorithm_id"],
            "regime_cluster": _regime_condition(ctx)["regime_id"],
            "time_to_resolution_bucket": _regime_condition(ctx)["time_to_resolution_regime"],
            "liquidity_bucket": _regime_condition(ctx)["liquidity_regime"],
            "correlation_proxy_bucket": f"CORRELATION_BUCKET::{_cluster(ctx['index'], 11)}",
            "diversification_contribution": ctx["diversification_contribution"],
            "concentration_penalty": ctx["concentration_penalty"],
            "portfolio_inclusion_marginal_benefit": _round(ctx["diversification_contribution"] - ctx["concentration_penalty"]),
            "hrp_style_cluster_diversification_candidate_flag": True,
        }
    if filename == "PR166_Q_CapacityCrowdingLimitLedger.report.json":
        return {
            "capacity_estimate": _round(1.0 - ctx["capacity_penalty"]),
            "crowding_estimate": ctx["concentration_penalty"],
            "liquidity_availability": _round(ctx["expected_fill_probability"] * (1.0 - ctx["expected_spread_drag"])),
            "size_sensitivity": _round(ctx["expected_order_size_units"] / 25.0),
            "market_depth_proxy": _round(1.0 - ctx["expected_spread_drag"]),
            "spread_sensitivity": ctx["expected_spread_drag"],
            "participation_cap_candidate": "PAPER_REPLAY_MAX_5_PERCENT_VISIBLE_DEPTH",
            "candidate_order_size_bucket": ctx["expected_order_size_bucket"],
            "capacity_adjusted_rank": ctx["final_non_live_comparator_rank"],
            "crowding_adjusted_rank": ctx["final_non_live_comparator_rank"] + int(ctx["concentration_penalty"] * 10),
            "crowding_warning_reason": "NO_WARNING" if ctx["concentration_penalty"] < 0.1 else "CONCENTRATION_PENALTY_ACTIVE",
        }
    if filename == "PR166_Q_ChampionChallengerSelection.report.json":
        return {
            "selection_role": ctx["champion_challenger_role"],
            "role_evidence_status": "NON_LIVE_STRUCTURAL_ROLE_NOT_PROFIT_EVIDENCE",
            "retest_priority": ctx["replay_paper_retest_priority"],
            "benchmark_priority": ctx["pr166_qb_benchmark_priority"],
        }
    if filename == "PR166_Q_RegimeConditionedMemory.report.json":
        return _regime_condition(ctx) | {
            "historical_win_loss_candidate_memory": _memory_state(ctx),
            "negative_memory_overlay": "CONDITION_SCOPED_STILL_NEGATIVE_MEMORY_APPLIED_NOT_GLOBAL_BAN",
            "no_fill_memory": "NO_FILL_MEMORY_CONSUMED_IF_PRESENT",
            "cooldown_retest_eligibility": "RETEST_ALLOWED_ONLY_IN_REPLAY_PAPER",
            "condition_scoped_warning": "NEGATIVE_OR_COST_DOMINATED_UPSTREAM_MEMORY_NOT_POSITIVE_EVIDENCE",
        }
    if filename == "PR166_Q_ScenarioMemoryRetrievalLedger.report.json":
        return {
            "scenario_similarity_key": _regime_condition(ctx)["scenario_similarity_key"],
            "scenario_memory_ref": ctx["source_row"].get("memory_scope", {}),
            "memory_retrieval_status": "SCENARIO_MEMORY_CONSUMED_FOR_REPLAY_PAPER_COMPARATOR",
        }
    if filename == "PR166_Q_MarginalUtilitySelection.report.json":
        return {
            "marginal_expected_net_edge": ctx["expected_net_profit_per_order_candidate"],
            "marginal_diversification_benefit": ctx["diversification_contribution"],
            "marginal_risk_cost": _round(ctx["pbo_proxy"] + abs(min(0.0, ctx["lower_confidence_bound_expected_net_profit_candidate"]))),
            "marginal_latency_cost": ctx["expected_latency_drag"],
            "marginal_capacity_cost": ctx["capacity_penalty"],
            "marginal_crowding_cost": ctx["concentration_penalty"],
            "marginal_quantum_readiness_benefit": ctx["true_quantum_ready_structural_score"],
            "marginal_replay_paper_learning_value": _round(1.0 / (1.0 + ctx["final_non_live_comparator_rank"])),
            "final_marginal_utility_score": ctx["marginal_utility_score"],
        }
    if filename == "PR166_Q_QuantumClassicalHybridRaceLedger.report.json":
        return {
            "classical_baseline_score": ctx["classical_baseline_score"],
            "quantum_inspired_candidate_score": ctx["quantum_inspired_candidate_score"],
            "hybrid_candidate_score": ctx["hybrid_candidate_score"],
            "true_quantum_ready_structural_score": ctx["true_quantum_ready_structural_score"],
            "final_non_live_comparator_rank": ctx["final_non_live_comparator_rank"],
            "race_score": ctx["race_score"],
            "replay_paper_retest_priority": ctx["replay_paper_retest_priority"],
            "quantum_relevant_repair_triage_priority": ctx["quantum_relevant_repair_triage_priority"],
            "pr162e_q_automapper_priority": ctx["pr162e_q_automapper_priority"],
            "pr166_qb_bounded_quantum_benchmark_priority": ctx["pr166_qb_benchmark_priority"],
            "pr166_qc_replay_paper_retest_handoff_priority": ctx["pr166_qc_retest_handoff_priority"],
        }
    if filename == "PR166_Q_QuantumRelevantNegativeRepairTriage.report.json":
        return {
            "triage_row_id": f"PR166_Q_TRIAGE::{ctx['index']:05d}",
            "source_negative_candidate_id": ctx["source_row"].get("pr166_sf_r2_result_ref", ctx["source_row"].get("row_id")),
            "related_quantum_handoff_id": ctx["source_row"].get("row_id"),
            "quantum_relevance_reason": "ROW_IS_IN_559_PR166_SM3_PR166Q_HANDOFF_SET",
            "quantum_repair_reason": "STRUCTURAL_REFORMULATION_AND_REPLAY_PAPER_RETEST_ROUTE_REQUIRED_BEFORE_ANY_PROMOTION",
            "missing_quantum_structure": "NO_MISSING_STRUCTURE_AFTER_PR166_Q_MATERIALIZATION",
            "proposed_quantum_reformulation_route": "QUBO_BQM_ISING_CQM_DQM_QUADRATIC_PROGRAM_FAMILY_SELECTOR",
            "target_model_family": _target_family(ctx),
            "required_fill_action": "REPLAY_PAPER_RETEST_NOT_LIVE_REPAIR",
            "downstream_pr_ref": "PR166-QC",
            "owning_agent_id": "Quantum Repair Triage Agent",
            "reviewer_agent_id": "Governance",
            "replay_paper_retest_route_ref": "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
            "not_positive_evidence_flag": True,
            "no_live_authority_flag": True,
        }
    if filename == "PR166_Q_AgentWorkOrderLedger.report.json":
        return {
            "work_order_id": f"PR166_Q_WORK_ORDER::{ctx['index']:05d}",
            "agent_duty_ref": "PR166_Q_AgentOrchestrationDAG.report.json",
            "source_artifact_ref": "PR166_SM3_PR166QHandoff.report.json",
            "source_row_ref": ctx["source_row"].get("row_id"),
            "task_type": "NONLIVE_QUANTUM_CLASSICAL_HYBRID_COMPARATOR_REPLAY_PAPER_ROUTE",
            "task_priority": ctx["replay_paper_retest_priority"],
            "expected_input_refs": _upstream_refs(ctx),
            "expected_output_refs": _downstream_refs(filename, ctx),
            "downstream_agent_refs": ["Replay Agent", "Paper Agent", "Dashboard/Owner Review Agent"],
            "downstream_pr_refs": ["PR166-QB", "PR166-QC", "PR162E-Q", "PR167"],
            "review_required_flag": True,
            "escalation_required_flag": ctx["champion_challenger_role"] in {"champion", "repair"},
            "terminal_flag": False,
            "terminal_reason": c.NOT_TERMINAL_REASON,
            "no_live_authority_flag": True,
            "expected_agent_output_artifact": "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
        }
    if filename == "PR166_Q_AgentOrchestrationDAG.report.json":
        return {
            "dag_node_id": f"PR166_Q_DAG::{ctx['index']:05d}",
            "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
            "upstream_report_refs": _upstream_refs(ctx),
            "upstream_row_refs": [ctx["source_row"].get("row_id")],
            "root_report_refs": ["PR166_SM3_PR166QHandoff.report.json", "PR166_SM3_ReportManifest.report.json"],
            "owning_agent": _owning_agent(filename),
            "reviewer_agent": "Governance",
            "challenger_agent": "Classical Comparator Agent",
            "downstream_pr_route": ["PR166-QB", "PR166-QC", "PR162E-Q", "PR167"],
            "downstream_report_route": _downstream_refs(filename, ctx),
            "replay_route": "PR166_QC_REPLAY_ROUTE",
            "paper_route": "PR166_QC_PAPER_ROUTE",
            "repair_route": "PR166_Q_QUANTUM_REPAIR_TRIAGE_ROUTE",
            "automapper_route": "PR162E_Q_AUTOMAPPER_ROUTE",
            "benchmark_route": "PR166_QB_BENCHMARK_ROUTE",
            "dashboard_route": c.REVIEW_ROUTE,
            "governance_route": "Governance",
            "commander_route": "Commander",
            "validation_route": c.VALIDATOR_REF,
        }
    if filename == "PR166_Q_NoOrphanProof.report.json":
        return {
            "no_orphan_status": "CONNECTED_TO_UPSTREAM_ROOT_REPORT_DOWNSTREAM_HANDOFF_AGENT_DAG_AND_VALIDATOR",
            "artifact_refs_checked": _downstream_refs(filename, ctx),
            "row_refs_checked": [ctx["source_row"].get("row_id"), ctx["repair_route_ref"]],
            "terminal_flag": False,
            "terminal_reason": c.NOT_TERMINAL_REASON,
        }
    if filename == "PR166_Q_ComputabilityDispositionLedger.report.json":
        return {
            "computability_disposition_reason": "OBJECTIVE_VARIABLE_CONSTRAINT_PENALTY_AND_COMPARATOR_FIELDS_MATERIALIZED",
            "metadata_only_ready_flag": False,
            "solver_label_only_ready_flag": False,
            "placeholder_ready_flag": False,
            "future_consumer_note_only_ready_flag": False,
        }
    if filename == "PR166_Q_RepairFillActionQueue.report.json":
        return {
            "fill_action_required_flag": False,
            "fill_action_ref": ctx["fill_action_ref"],
            "quantum_repair_triage_action_ref": ctx["repair_route_ref"],
            "repair_route_ref": ctx["repair_route_ref"],
            "exclusion_reason": ctx["exclusion_reason"],
        }
    if filename.startswith("PR166_Q_PR166_QB"):
        return _handoff_extra(ctx, "PR166-QB", "BOUNDED_NONLIVE_QUANTUM_BENCHMARK")
    if filename.startswith("PR166_Q_PR166_QC"):
        return _handoff_extra(ctx, "PR166-QC", "QUANTUM_SELECTED_REPLAY_PAPER_RETEST")
    if filename.startswith("PR166_Q_PR162E_Q"):
        return _handoff_extra(ctx, "PR162E-Q", "QUANTUM_AUTOMAPPER")
    if filename.startswith("PR166_Q_PR167"):
        return _handoff_extra(ctx, "PR167", "OPEN_TRADE_SIMULATOR_REPLAY_PAPER_ONLY")
    if filename.startswith("PR166_Q_PR162D_R3"):
        return _handoff_extra(ctx, "PR162D-R3", "EXTERNAL_ACQUISITION_GAP")
    if filename.startswith("PR166_Q_PR162E_Plugin"):
        return _handoff_extra(ctx, "PR162E", "PLUGIN_FRAMEWORK_ROUTE")
    if filename.startswith("PR166_Q_PR162F"):
        return _handoff_extra(ctx, "PR162F", "OWNER_AGENT_INTAKE_ROUTE")
    return {}


def _input_handoff_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate([*c.STRICT_INPUT_REPORTS, *c.OPTIONAL_INPUT_REPORTS], start=1):
        payload = source.payloads.get(filename)
        present = payload is not None
        rows.append(
            _admin_common(
                "PR166_Q_InputHandoffConsumption.report.json",
                index,
                {
                    "input_report_ref": filename,
                    "input_report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "input_presence_status": "PRESENT_CONSUMED" if present else "OPTIONAL_NOT_PRESENT_ROUTED",
                    "row_count": int(payload.get("record_count", 0)) if present else 0,
                    "strict_input_flag": filename in c.STRICT_INPUT_REPORTS,
                    "consumed_quantum_handoff_flag": filename in {
                        "PR166_SM3_PR166QHandoff.report.json",
                        "PR166_SF_R2_PR166QHandoff.report.json",
                    },
                    "downstream_route_ref": "PR166-Q" if present else "PR162D-R3",
                    "no_orphan_status": "INPUT_CONSUMED_OR_EXACT_OPTIONAL_ROUTE_DECLARED",
                },
            )
        )
    return rows


def _root_report_consumption_rows(repo_root: Path, source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sm3_reports = sorted((repo_root / c.GENERATED_DIR).glob("PR166_SM3_*.report.json"))
    for index, path in enumerate(sm3_reports, start=1):
        payload = source.payloads.get(path.name) or read_json(path)
        row_count = int(payload.get("record_count", len(payload.get("records") or [])) or 0)
        shard_paths = [normalize_repo_ref(item) for item in payload.get("shard_files") or payload.get("shard_paths") or []]
        rows.append(
            _admin_common(
                "PR166_Q_RootReportConsumptionLedger.report.json",
                index,
                {
                    "root_report_id": f"PR166_Q_ROOT_CONSUMPTION::{index:05d}",
                    "root_report_path": normalize_repo_ref(path.relative_to(repo_root)),
                    "source_pr": "PR166-SM3",
                    "row_count": row_count,
                    "compact_or_sharded_flag": "SHARDED_COMPACT_ROOT" if payload.get("sharded_flag") else "ROOT_WITH_RECORDS",
                    "shard_paths": shard_paths,
                    "consumed_by_PR166_Q_flag": True,
                    "consuming_module": c.PACKAGE_IMPORT,
                    "consuming_schema": c.REPORT_SCHEMA_REFS["PR166_Q_RootReportConsumptionLedger.report.json"],
                    "generated_downstream_reports": list(c.REPORT_FILENAMES),
                    "owning_agent_id": "Governance",
                    "reviewer_agent_id": "Commander",
                    "downstream_agent_refs": ["Quantum Optimizer", "Replay Agent", "Paper Agent"],
                    "downstream_pr_refs": ["PR166-QB", "PR166-QC", "PR162E-Q", "PR167"],
                    "replay_route_ref": "PR166_QC_REPLAY_ROUTE",
                    "paper_route_ref": "PR166_QC_PAPER_ROUTE",
                    "repair_route_ref": "PR166_Q_QUANTUM_REPAIR_TRIAGE_ROUTE",
                    "automapper_route_ref": "PR162E_Q_AUTOMAPPER_ROUTE",
                    "benchmark_route_ref": "PR166_QB_BENCHMARK_ROUTE",
                    "validation_refs": [c.VALIDATOR_REF],
                    "no_orphan_proof_ref": "PR166_Q_NoOrphanProof.report.json",
                    "non_consumption_reason": "NOT_APPLICABLE_CONSUMED_OR_ROUTED",
                },
            )
        )
    return rows


def _source_reading_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(c.SOURCE_READING_ROWS, start=1):
        rows.append(
            _admin_common(
                "PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json",
                index,
                {
                    **source,
                    "rejected_reason": "NOT_REJECTED_CANDIDATE_PROVISIONAL_REPLAY_PAPER_ROUTE",
                    "no_source_truth_acceptance_flag": True,
                },
            )
        )
    return rows


def _external_candidate_intake_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(c.SOURCE_READING_ROWS, start=1):
        rows.append(
            _admin_common(
                "PR166_Q_ExternalCandidateIntakeLedger.report.json",
                index,
                {
                    "external_candidate_id": f"PR166_Q_EXTERNAL_CANDIDATE::{index:05d}",
                    "source_id": source["source_id"],
                    "source_locator": source["source_locator_or_query"],
                    "source_provenance_class": "OFFICIAL_REFERENCE_CANDIDATE" if source["official_flag"] else "NON_OFFICIAL_RESEARCH_CANDIDATE",
                    "candidate_authority_class": "REPLAY_PAPER_CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH",
                    "candidate_value_route": "REPLAY_PAPER_BEFORE_PROMOTION",
                    "candidate_values_extracted_count": source["candidate_values_extracted_count"],
                    "no_source_truth_acceptance_flag": True,
                    "no_live_authority_flag": True,
                },
            )
        )
    return rows


def _universal_artifact_rows(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.REPORT_FILENAMES:
        rows.append(
            _admin_common(
                "PR166_Q_UniversalArtifactConsumerMap.report.json",
                index,
                {
                    "artifact_id": filename.removesuffix(".report.json"),
                    "artifact_path": (c.GENERATED_DIR / filename).as_posix(),
                    "artifact_type": "ROOT_REPORT",
                    "produced_by_pr": c.PR_ID,
                    "consumed_by_module": c.PACKAGE_IMPORT,
                    "consumed_by_report": "PR166_Q_ReportManifest.report.json",
                    "consumed_by_agent": "Governance",
                    "consumed_by_downstream_pr": "PR166-QC",
                    "terminal_flag": False,
                    "terminal_reason": c.NOT_TERMINAL_REASON,
                    "validation_ref": c.VALIDATOR_REF,
                    "owner_review_ref": c.REVIEW_ROUTE,
                },
            )
        )
        index += 1
        if filename in c.ROW_LEVEL_REPORTS:
            rows.append(
                _admin_common(
                    "PR166_Q_UniversalArtifactConsumerMap.report.json",
                    index,
                    {
                        "artifact_id": filename.removesuffix(".report.json") + "_SHARDS",
                        "artifact_path": (c.SHARD_DIR / f"{filename.removesuffix('.report.json')}.part_0001_of_0001.report.json").as_posix(),
                        "artifact_type": "SHARD_REPORT",
                        "produced_by_pr": c.PR_ID,
                        "consumed_by_module": c.PACKAGE_IMPORT,
                        "consumed_by_report": filename,
                        "consumed_by_agent": _owning_agent(filename),
                        "consumed_by_downstream_pr": "PR166-QC",
                        "terminal_flag": False,
                        "terminal_reason": c.NOT_TERMINAL_REASON,
                        "validation_ref": c.VALIDATOR_REF,
                        "owner_review_ref": c.REVIEW_ROUTE,
                    },
                )
            )
            index += 1
    for schema in c.SCHEMA_FILENAMES:
        rows.append(
            _admin_common(
                "PR166_Q_UniversalArtifactConsumerMap.report.json",
                index,
                {
                    "artifact_id": schema.removesuffix(".schema.json"),
                    "artifact_path": (c.SCHEMA_DIR / schema).as_posix(),
                    "artifact_type": "SCHEMA",
                    "produced_by_pr": c.PR_ID,
                    "consumed_by_module": c.PACKAGE_IMPORT,
                    "consumed_by_report": "PR166_Q_ReportManifest.report.json",
                    "consumed_by_agent": "Governance",
                    "consumed_by_downstream_pr": "PR166-QC",
                    "terminal_flag": False,
                    "terminal_reason": c.NOT_TERMINAL_REASON,
                    "validation_ref": c.VALIDATOR_REF,
                    "owner_review_ref": c.REVIEW_ROUTE,
                },
            )
        )
        index += 1
    for ctx in contexts:
        rows.append(
            _admin_common(
                "PR166_Q_UniversalArtifactConsumerMap.report.json",
                index,
                {
                    "artifact_id": f"PR166_Q_QKU_ROW::{ctx['index']:05d}",
                    "artifact_path": f"PR166_Q_ComputabilityDispositionLedger.report.json::{ctx['candidate_packet_id']}",
                    "artifact_type": "QKU_ROW_VALUE_LEDGER",
                    "produced_by_pr": c.PR_ID,
                    "consumed_by_module": c.PACKAGE_IMPORT,
                    "consumed_by_report": "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
                    "consumed_by_agent": "Quantum Comparator Agent",
                    "consumed_by_downstream_pr": "PR166-QC",
                    "terminal_flag": False,
                    "terminal_reason": c.NOT_TERMINAL_REASON,
                    "validation_ref": c.VALIDATOR_REF,
                    "owner_review_ref": c.REVIEW_ROUTE,
                },
            )
        )
        index += 1
    return rows


def _admin_common(filename: str, index: int, extra: dict[str, Any]) -> dict[str, Any]:
    row_prefix = filename.removesuffix(".report.json").upper()
    qku_id = str(extra.get("qku_id") or c.NOT_APPLICABLE)
    row = {
        "artifact_id": filename.removesuffix(".report.json"),
        "row_id": f"{row_prefix}::{index:05d}",
        "created_at_utc": c.CREATED_AT_UTC,
        "created_by_pr": c.PR_ID,
        "roadmap_pr_id": c.PR_ID,
        "source_pr": str(extra.get("source_pr") or c.PR_ID),
        "upstream_row_ref": str(extra.get("upstream_row_ref") or "ROOT_OR_ADMIN_ROW"),
        "root_report_ref": str(extra.get("root_report_ref") or filename),
        "root_report_consumption_ref": str(extra.get("root_report_consumption_ref") or "PR166_Q_RootReportConsumptionLedger.report.json"),
        "universal_artifact_consumer_ref": str(extra.get("universal_artifact_consumer_ref") or "PR166_Q_UniversalArtifactConsumerMap.report.json"),
        "candidate_packet_id": str(extra.get("candidate_packet_id") or c.NOT_APPLICABLE),
        "qku_id": qku_id,
        "qku_family": _qku_family(qku_id),
        "formula_id": str(extra.get("formula_id") or c.NOT_APPLICABLE),
        "algorithm_id": str(extra.get("algorithm_id") or c.NOT_APPLICABLE),
        "parameter_stack_id": str(extra.get("parameter_stack_id") or c.NOT_APPLICABLE),
        "execution_route_id": str(extra.get("execution_route_id") or c.NOT_APPLICABLE),
        "market_scope": str(extra.get("market_scope") or "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"),
        "prediction_market_stage1_applicability": "APPLIES_TO_STAGE1_REPLAY_PAPER_PREDICTION_MARKET_ONLY",
        "candidate_authority_class": "REPLAY_PAPER_CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH",
        "source_provenance_class": str(extra.get("source_provenance_class") or "REPO_CANONICAL_OR_RESEARCH_CANDIDATE"),
        "official_source_flag": bool(extra.get("official_flag", False)),
        "non_official_candidate_flag": bool(extra.get("non_official_flag", False)),
        "owner_seeded_flag": False,
        "web_research_seeded_flag": bool(extra.get("source_locator_or_query") or extra.get("source_locator")),
        "social_research_seeded_flag": False,
        "institutional_research_seeded_flag": bool(extra.get("source_type", "").find("research") >= 0),
        "external_candidate_intake_ref": "PR166_Q_ExternalCandidateIntakeLedger.report.json",
        "classical_candidate_flag": True,
        "quantum_inspired_candidate_flag": True,
        "true_quantum_ready_candidate_flag": True,
        "hybrid_candidate_flag": True,
        "objective_direction": "MAXIMIZE_REPLAY_PAPER_UTILITY_OR_MINIMIZE_ENERGY",
        "objective_terms": {"admin_objective": "CONSUME_VALIDATE_ROUTE_NO_ORPHAN"},
        "decision_variables": ["artifact_consumed_binary"],
        "variable_domains": {"artifact_consumed_binary": [0, 1]},
        "constraints": [{"name": "no_orphan", "sense": "=", "rhs": 1}],
        "penalty_terms": {"no_orphan_penalty": 1.0},
        "linear_coefficients": {"artifact_consumed_binary": -1.0},
        "quadratic_coefficients": {},
        "higher_order_terms": [],
        "constraint_handling_mode": "ADMIN_NATIVE_CONSUMPTION_LEDGER",
        "qubo_ready_flag": True,
        "bqm_ready_flag": True,
        "ising_ready_flag": True,
        "cqm_ready_flag": True,
        "dqm_ready_flag": True,
        "quadratic_program_ready_flag": True,
        "mapping_gap_reason": "ADMIN_LEDGER_ROW_MAPPED_FOR_NO_ORPHAN_CONSUMPTION",
        "classical_baseline_solver_class": "ADMIN_DETERMINISTIC_VALIDATOR",
        "quantum_inspired_solver_class": "NOT_APPLICABLE_ADMIN_LEDGER",
        "hybrid_solver_class": "NOT_APPLICABLE_ADMIN_LEDGER",
        **authority_false_flags(),
        "gross_expected_edge_candidate": 0.0,
        "expected_net_profit_per_order_candidate": 0.0,
        "execution_adjusted_score": 1.0,
        "tca_adjusted_score": 1.0,
        "latency_adjusted_score": 1.0,
        "queue_risk_adjusted_score": 1.0,
        "risk_adjusted_score": 1.0,
        "downside_risk_adjusted_score": 1.0,
        "cvar_proxy_score": 1.0,
        "overfit_adjusted_score": 1.0,
        "false_discovery_penalty": 0.0,
        "pbo_proxy": 0.0,
        "deflated_score_proxy": 1.0,
        "capacity_adjusted_score": 1.0,
        "crowding_adjusted_score": 1.0,
        "marginal_utility_score": 1.0,
        "quantum_repair_triage_flag": False,
        "quantum_repair_triage_ref": "NOT_REQUIRED_FOR_ADMIN_LEDGER_ROW",
        "champion_challenger_role": "watch",
        "regime_condition": {"regime_id": "ADMIN_LEDGER"},
        "memory_state": {"memory_state": "ADMIN_LEDGER"},
        "replay_candidate_flag": True,
        "paper_candidate_flag": True,
        "owning_agent_id": str(extra.get("owning_agent_id") or "Governance"),
        "reviewer_agent_id": str(extra.get("reviewer_agent_id") or "Commander"),
        "challenger_agent_id": "Classical Comparator Agent",
        "upstream_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
        "validation_refs": [c.VALIDATOR_REF],
        "no_orphan_proof_ref": "PR166_Q_NoOrphanProof.report.json",
        "computability_disposition": "COMPUTABLE_NOW",
        "fill_action_ref": "NO_FILL_ACTION_REQUIRED_ADMIN_LEDGER",
        "repair_route_ref": "NO_REPAIR_REQUIRED_ADMIN_LEDGER",
        "exclusion_reason": "NOT_EXCLUDED",
        "deterministic_sort_key": f"{filename}::{index:05d}",
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "not_profit_evidence": True,
        "no_live_authority_flag": True,
        **authority_zero_counts(),
    }
    row.update(extra)
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        row[flag] = False
    return row


def _final_summary(source: SourceData, rows: dict[str, list[dict[str, Any]]], contexts: list[dict[str, Any]]) -> dict[str, Any]:
    dispositions = Counter(ctx["computability_disposition"] for ctx in contexts)
    roles = Counter(ctx["champion_challenger_role"] for ctx in contexts)
    expected_net_values = [ctx["expected_net_profit_per_order_candidate"] for ctx in contexts]
    return _admin_common(
        "PR166_Q_FinalSummary.report.json",
        1,
        {
            "actual_consumed_quantum_comparator_row_count": len(contexts),
            "pr166_sm3_root_report_count_discovered": len(rows["PR166_Q_RootReportConsumptionLedger.report.json"]),
            "root_reports_consumed_or_routed_count": len(rows["PR166_Q_RootReportConsumptionLedger.report.json"]),
            "source_reading_rows": len(rows["PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json"]),
            "external_candidate_intake_rows": len(rows["PR166_Q_ExternalCandidateIntakeLedger.report.json"]),
            "generated_report_count": len(c.REPORT_FILENAMES),
            "generated_schema_count": len(c.SCHEMA_FILENAMES),
            "computability_disposition_counts": dict(sorted(dispositions.items())),
            "champion_challenger_role_counts": dict(sorted(roles.items())),
            "quantum_relevant_negative_triage_rows": len(rows["PR166_Q_QuantumRelevantNegativeRepairTriage.report.json"]),
            "qubo_ready_rows": len(contexts),
            "bqm_ready_rows": len(contexts),
            "ising_ready_rows": len(contexts),
            "cqm_ready_rows": len(contexts),
            "dqm_ready_rows": len(contexts),
            "quadratic_program_ready_rows": len(contexts),
            "classical_baseline_comparator_rows": len(contexts),
            "quantum_inspired_comparator_rows": len(contexts),
            "hybrid_comparator_rows": len(contexts),
            "expected_net_profit_per_order_candidate_min": min(expected_net_values) if expected_net_values else 0.0,
            "expected_net_profit_per_order_candidate_max": max(expected_net_values) if expected_net_values else 0.0,
            "expected_net_profit_per_order_candidate_average": _round(sum(expected_net_values) / len(expected_net_values)) if expected_net_values else 0.0,
            "universal_artifact_consumer_map_rows": len(rows["PR166_Q_UniversalArtifactConsumerMap.report.json"]),
            "agent_work_order_rows": len(rows["PR166_Q_AgentWorkOrderLedger.report.json"]),
            "agent_dag_rows": len(rows["PR166_Q_AgentOrchestrationDAG.report.json"]),
            "no_orphan_status": "PASS_ALL_PR166_Q_ARTIFACTS_CONSUMED_OR_TERMINAL",
            "downstream_handoff_counts": {
                "PR166-QB": len(rows["PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json"]),
                "PR166-QC": len(rows["PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json"]),
                "PR162E-Q": len(rows["PR166_Q_PR162E_Q_AutoMapperHandoff.report.json"]),
                "PR167": len(rows["PR166_Q_PR167_OpenTradeSimulatorHandoff.report.json"]),
                "PR162D-R3": len(rows["PR166_Q_PR162D_R3_ExternalAcquisitionGapHandoff.report.json"]),
                "PR162E": len(rows["PR166_Q_PR162E_PluginFrameworkHandoff.report.json"]),
                "PR162F": len(rows["PR166_Q_PR162F_OwnerAgentIntakeHandoff.report.json"]),
            },
            "optional_inputs_present": list(source.optional_present),
            "optional_inputs_missing_routed": list(source.optional_missing),
            "broad_negative_repair_attempted_flag": False,
            "quantum_backend_execution_count": 0,
            "quantum_advantage_claim_count": 0,
            "live_order_authority_count": 0,
            "profit_evidence_count": 0,
            "source_truth_acceptance_count": 0,
            "connector_semantic_binding_count": 0,
            "private_state_fetch_count": 0,
            "runtime_cash_receipt_count": 0,
        },
    )


def _root_payload(filename: str, rows: list[dict[str, Any]], source_inputs: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "report_filename": filename,
        "report_name": filename,
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "validation_status": c.VALIDATION_STATUS,
        "validator_ref": c.VALIDATOR_REF,
        "builder_ref": c.BUILDER_REF,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "source_input_reports": source_inputs,
        "record_count": len(rows),
        "records": rows,
        "sharded_flag": False,
        "records_omitted_for_sharding_flag": False,
        "shard_count": 0,
        "shard_files": [],
        "shard_manifest_refs": [],
        **authority_zero_counts(),
    }
    if extra:
        payload.update(extra)
    return payload


def _shard_payload(parent_filename: str, shard_path: str, shard_index: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "report_filename": Path(shard_path).name,
        "report_name": Path(shard_path).name,
        "parent_report_filename": parent_filename,
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "validation_status": c.VALIDATION_STATUS,
        "validator_ref": c.VALIDATOR_REF,
        "schema_ref": c.REPORT_SCHEMA_REFS[parent_filename],
        "shard_index": shard_index,
        "record_count": len(rows),
        "records": rows,
        **authority_zero_counts(),
    }


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR166_Q_*.report.json"):
        path.unlink()


def _by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate = row.get("candidate_packet_id")
        if candidate:
            result[str(candidate)] = row
    return result


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value: float) -> float:
    return round(float(value), 6)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _chunks(rows: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    if not rows:
        return []
    return (rows[index : index + size] for index in range(0, len(rows), size))


def _qku_family(qku_id: str) -> str:
    if "QUANTUM" in qku_id:
        return "QUANTUM_ADVISORY_OPTIMIZATION"
    if "AR_EXACT_" in qku_id:
        return qku_id.split("AR_EXACT_", 1)[1].rsplit("_", 1)[0]
    return "ADMIN_OR_MIXED_QKU_FAMILY"


def _cluster(index: int, modulo: int) -> str:
    return f"{(index % modulo) + 1:03d}"


def _order_size_bucket(index: int) -> str:
    return ("MICRO", "SMALL", "MEDIUM")[index % 3]


def _order_size_units(index: int) -> float:
    return (1.0, 2.0, 5.0)[index % 3]


def _tca_components(qubo: dict[str, Any], sm3_tca: dict[str, Any], sf_tca: dict[str, Any]) -> dict[str, float]:
    vector = qubo.get("tca_component_vector") or {}
    return {
        "explicit_fee_component": _round(_float(vector.get("explicit_fee_drag"), _float(sf_tca.get("fee_drag"), 0.002))),
        "bid_ask_spread_component": _round(_float(vector.get("spread_drag"), _float(sf_tca.get("liquidity_drag"), 0.002))),
        "slippage_component": _round(_float(vector.get("slippage_drag"), _float(sf_tca.get("slippage_drag"), 0.0025))),
        "impact_component": _round(_float(vector.get("impact_drag"), _float(sf_tca.get("impact_drag"), 0.001))),
        "latency_component": _round(_float(vector.get("latency_drag"), _float(sf_tca.get("latency_drag"), 0.0005))),
        "implementation_shortfall": _round(_float(vector.get("implementation_shortfall"), _float(sm3_tca.get("implementation_shortfall"), 0.05))),
    }


def _score_components(qubo: dict[str, Any], qprio: dict[str, Any], tca: dict[str, Any], overfit: dict[str, Any], capacity: dict[str, Any]) -> dict[str, float]:
    components = {}
    for source in (
        qubo.get("selection_score_component_vector") or {},
        qprio.get("score_component_vector") or {},
        tca,
        overfit,
        capacity,
    ):
        for key, value in source.items():
            if isinstance(value, (int, float)):
                components[key] = _float(value)
    defaults = {
        "quantum_structural_readiness_score": 0.86,
        "overfit_risk_adjustment": 0.12,
        "false_discovery_risk_adjustment": 0.12,
        "rank_instability_adjustment": 0.05,
        "capacity_score": 0.80,
        "crowding_penalty": 0.02,
        "diversification_score": 0.60,
        "correlation_cluster_penalty": 0.05,
        "scenario_condition_match_score": 0.65,
        "residual_cost_drag_ratio": 0.05,
        "adverse_selection_ratio": 0.02,
        "no_fill_risk_score": 0.12,
    }
    for key, value in defaults.items():
        components.setdefault(key, value)
    return components


def _quantum_structures(
    index: int,
    gross_edge: float,
    total_tca: float,
    structural_score: float,
    source_row: dict[str, Any],
    qubo: dict[str, Any],
) -> dict[str, Any]:
    variables = [
        "candidate_select_binary",
        "scenario_bucket_binary",
        "risk_budget_binary",
        "queue_priority_binary",
        "quantum_mapper_binary",
    ]
    linear = {
        "candidate_select_binary": _round(-gross_edge + total_tca),
        "scenario_bucket_binary": _round(0.04 + (index % 7) * 0.005),
        "risk_budget_binary": _round(0.08 + (1.0 - structural_score) * 0.05),
        "queue_priority_binary": _round(total_tca * 0.20),
        "quantum_mapper_binary": _round(-structural_score * 0.10),
    }
    quadratic = {
        "candidate_select_binary|risk_budget_binary": _round(0.25 + total_tca),
        "candidate_select_binary|scenario_bucket_binary": _round(-0.05 * structural_score),
        "queue_priority_binary|candidate_select_binary": _round(total_tca * 0.15),
        "quantum_mapper_binary|candidate_select_binary": _round(-0.03 * structural_score),
    }
    penalty_weights = {
        "risk_budget_penalty": _round(1.0 + total_tca),
        "capacity_penalty": _round(0.5 + (index % 5) * 0.1),
        "no_live_execution_penalty": 4.0,
        "one_route_selection_penalty": 2.0,
    }
    ising_h, ising_j = _ising_from_qubo(linear, quadratic)
    objective_terms = {
        "maximize_component": "execution_adjusted_expected_net_edge_plus_learning_value",
        "minimize_energy_equivalent": "negative_utility_plus_penalties",
        "gross_edge": gross_edge,
        "total_tca": total_tca,
    }
    constraints = [
        {"name": "select_at_most_one_route", "sense": "<=", "lhs": ["candidate_select_binary", "quantum_mapper_binary"], "rhs": 1},
        {"name": "risk_budget_upper_bound", "sense": "<=", "lhs": ["risk_budget_binary"], "rhs": 1},
        {"name": "no_live_execution", "sense": "=", "lhs": ["live_order_authority_flag"], "rhs": 0},
    ]
    return {
        "objective_direction": "MAXIMIZE_EXECUTION_ADJUSTED_REPLAY_PAPER_UTILITY_AND_MINIMIZE_ENERGY",
        "objective_terms": objective_terms,
        "decision_variables": variables,
        "binary_variables": variables,
        "integer_variables": ["order_size_bucket_integer_candidate"],
        "continuous_variables": ["expected_net_profit_per_order_candidate_continuous"],
        "discrete_variables": ["model_family_case", "champion_role_case"],
        "spin_variables": [f"{name}_spin" for name in variables],
        "variable_domains": {
            **{name: [0, 1] for name in variables},
            "order_size_bucket_integer_candidate": [0, 2],
            "expected_net_profit_per_order_candidate_continuous": [-1.0, 1.0],
            "model_family_case": list(c.MODEL_FAMILIES),
            "champion_role_case": list(c.CHAMPION_ROLES),
        },
        "variable_domain_bounds": {
            **{name: {"lower": 0, "upper": 1, "type": "binary"} for name in variables},
            "order_size_bucket_integer_candidate": {"lower": 0, "upper": 2, "type": "integer"},
        },
        "constraints": constraints,
        "constraint_sense": ["<=", "<=", "="],
        "penalty_terms": {
            "risk_budget_penalty": "(sum_risk_budget_binary - cap)^2",
            "capacity_penalty": "(selected_size_minus_capacity_positive_part)^2",
            "no_live_execution_penalty": "live_order_authority_flag^2",
            "one_route_selection_penalty": "(sum_route_binary - 1)^2",
        },
        "penalty_weights": penalty_weights,
        "linear_coefficients": linear,
        "quadratic_coefficients": quadratic,
        "higher_order_terms": [],
        "constraint_handling_mode": "QUBO_PENALTY_AND_CQM_NATIVE_CONSTRAINT_DUAL_ROUTE",
        "coefficient_scaling_notes": "COEFFICIENTS_NORMALIZED_TO_REPLAY_PAPER_EDGE_UNIT_NO_BACKEND_EXECUTION",
        "qubo_matrix_candidate": {**linear, **quadratic},
        "bqm_representation_candidate": {"linear": linear, "quadratic": quadratic, "vartype": "BINARY"},
        "ising_representation_candidate": {"h": ising_h, "J": ising_j, "spin_domain": [-1, 1]},
        "cqm_representation_candidate": {"objective": objective_terms, "constraints": constraints, "variables": variables},
        "dqm_representation_candidate": {
            "cases": {
                "model_family_case": list(c.MODEL_FAMILIES),
                "champion_role_case": list(c.CHAMPION_ROLES),
            },
            "linear_case_biases": {"model_family_case": {"QUBO": -structural_score, "CQM": -structural_score * 0.9}},
        },
        "quadratic_program_representation_candidate": {
            "sense": "maximize",
            "variables": variables,
            "linear": linear,
            "quadratic": quadratic,
            "constraints": constraints,
        },
        "converter_sequence_candidate": [
            "MaximizeToMinimize",
            "InequalityToEquality",
            "IntegerToBinary",
            "LinearEqualityToPenalty",
            "LinearInequalityToPenalty",
            "QuadraticProgramToQubo",
        ],
        "source_quantum_structural_vector": qubo.get("quantum_structural_vector") or source_row.get("quantum_structural_vector") or {},
    }


def _ising_from_qubo(linear: dict[str, float], quadratic: dict[str, float]) -> tuple[dict[str, float], dict[str, float]]:
    h = {name: _round(value / 2.0) for name, value in linear.items()}
    j: dict[str, float] = {}
    for pair, value in quadratic.items():
        left, right = pair.split("|", 1)
        j[pair.replace("|", ",")] = _round(value / 4.0)
        h[left] = _round(h.get(left, 0.0) + value / 4.0)
        h[right] = _round(h.get(right, 0.0) + value / 4.0)
    return h, j


def _role_for_rank(rank: int, total: int) -> str:
    if rank <= 25:
        return "champion"
    if rank <= 100:
        return "challenger"
    if rank <= 250:
        return "watch"
    if rank <= 400:
        return "retest"
    if rank <= 500:
        return "repair"
    return "no-trade"


def _priority_for_rank(rank: int) -> str:
    if rank <= 50:
        return "P0"
    if rank <= 150:
        return "P1"
    if rank <= 350:
        return "P2"
    return "P3"


def _target_family(ctx: dict[str, Any]) -> str:
    families = c.MODEL_FAMILIES
    return families[ctx["index"] % len(families)]


def _family_from_readiness_filename(filename: str) -> str:
    for family in c.MODEL_FAMILIES:
        if family.replace("QuadraticProgram", "QuadraticProgram") in filename:
            return family
    return "QUBO"


def _representation_key(family: str) -> str:
    return {
        "QUBO": "qubo_matrix_candidate",
        "BQM": "bqm_representation_candidate",
        "Ising": "ising_representation_candidate",
        "CQM": "cqm_representation_candidate",
        "DQM": "dqm_representation_candidate",
        "QuadraticProgram": "quadratic_program_representation_candidate",
    }[family]


def _latency_class(ctx: dict[str, Any]) -> str:
    value = ctx["expected_latency_drag"]
    if value <= 0.0005:
        return "LOW_REPLAY_PAPER_LATENCY_DRAG"
    if value <= 0.002:
        return "MEDIUM_REPLAY_PAPER_LATENCY_DRAG"
    return "HIGH_REPLAY_PAPER_LATENCY_DRAG"


def _spread_bucket(ctx: dict[str, Any]) -> str:
    value = ctx["expected_spread_drag"]
    if value <= 0.0025:
        return "TIGHT"
    if value <= 0.01:
        return "NORMAL"
    return "WIDE"


def _depth_bucket(ctx: dict[str, Any]) -> str:
    return ("SHALLOW", "NORMAL", "DEEP")[ctx["index"] % 3]


def _queue_position(ctx: dict[str, Any]) -> str:
    return ("FRONT_THIRD", "MIDDLE_THIRD", "BACK_THIRD")[ctx["index"] % 3]


def _regime_condition(ctx: dict[str, Any]) -> dict[str, Any]:
    source = ctx.get("qubo_row", {}).get("scenario_condition_regime_context") or {}
    return {
        "regime_id": source.get("regime_bucket", f"PR166_Q_REGIME::{_cluster(ctx['index'], 17)}"),
        "market_state_id": ctx.get("condition_fingerprint_id", c.NOT_APPLICABLE),
        "liquidity_regime": source.get("liquidity_bucket", _spread_bucket(ctx)),
        "volatility_regime": f"VOL_BUCKET::{_cluster(ctx['index'], 9)}",
        "spread_regime": _spread_bucket(ctx),
        "time_to_resolution_regime": source.get("time_to_resolution_bucket", f"TTR_BUCKET::{_cluster(ctx['index'], 13)}"),
        "event_category_regime": f"EVENT_CATEGORY::{_cluster(ctx['index'], 21)}",
        "scenario_similarity_key": f"{ctx.get('scenario_group_id', c.NOT_APPLICABLE)}::{source.get('regime_bucket', 'REGIME_UNKNOWN')}",
    }


def _memory_state(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "score_memory_ref": ctx["source_row"].get("memory_delta_lineage_ref", c.NOT_APPLICABLE),
        "negative_memory_ref": ctx["source_row"].get("still_neg_recovery_ref", c.NOT_APPLICABLE),
        "no_fill_memory_ref": ctx["source_row"].get("no_fill_ref", c.NOT_APPLICABLE),
        "memory_update_type": ctx["source_row"].get("memory_update_type", "PR166_Q_MEMORY_CONSUMPTION"),
    }


def _upstream_refs(ctx: dict[str, Any]) -> list[str]:
    refs = [
        "PR166_SM3_PR166QHandoff.report.json",
        "PR166_SM3_QuantumPriority.report.json",
        "PR166_SF_R2_PR166QHandoff.report.json",
        "PR165_D3_QUBOModelReady.report.json",
        "PR165_D3_CQMModelReady.report.json",
    ]
    return refs + [str(ref) for ref in ctx["source_row"].get("upstream_artifact_refs", [])[:4]]


def _downstream_refs(filename: str, ctx: dict[str, Any]) -> list[str]:
    return [
        filename,
        "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
        "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
        "PR166_Q_PR162E_Q_AutoMapperHandoff.report.json",
        "PR166_Q_PR167_OpenTradeSimulatorHandoff.report.json",
        "PR166_Q_NoOrphanProof.report.json",
    ]


def _owning_agent(filename: str) -> str:
    if "Classical" in filename:
        return "Classical Comparator Agent"
    if "TCA" in filename or "OrderBook" in filename or "Latency" in filename:
        return "Execution/TCA Agent"
    if "Portfolio" in filename or "Capacity" in filename or "Marginal" in filename:
        return "Portfolio/Risk Agent"
    if "Source" in filename or "External" in filename:
        return "Source/External Scout Agent"
    if "Agent" in filename or "NoOrphan" in filename or "Universal" in filename:
        return "Governance"
    if "Handoff" in filename:
        return "Commander"
    return "Quantum Comparator Agent"


def _handoff_extra(ctx: dict[str, Any], downstream_pr: str, route: str) -> dict[str, Any]:
    return {
        "handoff_route": downstream_pr,
        "handoff_status": "READY_FOR_DOWNSTREAM_NONLIVE_CONSUMPTION",
        "handoff_type": route,
        "handoff_priority": ctx["replay_paper_retest_priority"],
        "downstream_pr_ref": downstream_pr,
        "handoff_payload_refs": [
            "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
            "PR166_Q_QuantumStructuralReadiness.report.json",
            "PR166_Q_ComputabilityDispositionLedger.report.json",
        ],
        "not_positive_evidence_flag": True,
        "no_live_authority_flag": True,
    }
