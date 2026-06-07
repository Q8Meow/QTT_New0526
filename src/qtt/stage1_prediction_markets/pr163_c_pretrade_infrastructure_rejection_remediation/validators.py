"""Fail-closed validator for PR163-C generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .central_pretrade_repair_reason_codes import ALLOWED_DISPOSITIONS, PROHIBITED_DISPOSITIONS
from .json_io import read_json, records_from_payload
from .pretrade_repair_authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    validate_record_authority,
)
from .repair_formula_library import FORMULAS, apply_formula
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
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    _validate_manifest(records, failures)
    _validate_trigger_consumption(repo_root, records, failures)
    _validate_dispositions(records, failures)
    _validate_formula_registry(records, failures)
    _validate_candidate_imputation(records, failures)
    _validate_component_repairs(records, failures)
    _validate_model_risk(records, failures)
    _validate_counterfactual_and_delta(records, failures)
    _validate_quantum(records, failures)
    _validate_agents(records, failures)
    _validate_pr165_delta(records, failures)
    _validate_authority(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR163-C report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR163-C report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR163-C schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in p.PR164_REQUIRED_REPORTS:
        if not (repo_root / p.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR164 input for PR163-C: {filename}")
    trigger = repo_root / p.GENERATED_DIR / "PR164_PR163CRepairTriggerMatrix.report.json"
    if not trigger.exists():
        failures.append("PR164 PR163-C trigger matrix missing or unreadable")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR163-C", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        if filename in p.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root must not duplicate row records")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} shard row count mismatch")
        else:
            _expect(payload.get("record_count") == len(records_from_payload(payload)), failures, f"{filename} record_count mismatch")
        for key, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(key) is expected, failures, f"{filename} top-level authority flag drift: {key}")
        path = repo_root / p.GENERATED_DIR / filename
        if path.exists():
            _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds 10 MiB root report limit")
        for shard_path in payload.get("shard_files") or []:
            resolved = p.resolve_repo_relative(repo_root, shard_path)
            _expect(resolved.exists(), failures, f"{filename} missing shard: {shard_path}")
            if resolved.exists():
                _expect(resolved.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_path} exceeds 25 MiB shard limit")
        for record in records[filename]:
            failures.extend(validate_record_authority(record).failures)


def _validate_manifest(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    manifest = records["PR163_C_ReportManifest.report.json"]
    filenames = {row["report_filename"] for row in manifest}
    _expect(filenames == set(p.REPORT_FILENAMES), failures, "manifest does not cover every PR163-C report")
    shard_paths: set[str] = set()
    for row in manifest:
        for shard_path in row.get("shard_paths", []):
            shard_paths.add(shard_path)
    _expect(any(row.get("shard_count", 0) > 0 for row in manifest), failures, "manifest lacks shard coverage")
    _expect(all(row.get("downstream_consumer") for row in manifest), failures, "manifest row missing downstream consumer")
    _expect(all(path.startswith("docs/master_plan/generated/pr163_c_shards/") for path in shard_paths), failures, "manifest shard path outside PR163-C shard dir")


def _validate_trigger_consumption(repo_root: Path, records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    trigger_payload = read_json(repo_root / p.GENERATED_DIR / "PR164_PR163CRepairTriggerMatrix.report.json")
    expected_count = int(trigger_payload.get("record_count", 1266))
    taxonomy = records["PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json"]
    _expect(len(taxonomy) == expected_count, failures, "PR163-C did not consume every PR164 trigger row")
    consumed = {(row["candidate_packet_id"], row["qku_id"], row["pr164_trigger_ref"]) for row in taxonomy}
    _expect(len(consumed) == expected_count, failures, "PR163-C trigger consumption is not one-to-one")
    summary = records["PR163_C_FinalSummary.report.json"][0]
    _expect(summary.get("pr164_pr163c_trigger_rows_consumed") == expected_count, failures, "summary trigger count mismatch")
    fatal_missing = [row for row in records["PR163_C_InputConsumptionAudit.report.json"] if row.get("missing_artifact_is_fatal")]
    _expect(not fatal_missing, failures, "fatal required PR163-C input artifact missing")


def _validate_dispositions(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json"]:
        disposition = row.get("final_disposition")
        _expect(disposition in ALLOWED_DISPOSITIONS, failures, f"invalid disposition: {disposition}")
        _expect(disposition not in PROHIBITED_DISPOSITIONS, failures, f"prohibited disposition: {disposition}")
        _expect(row.get("causal_defect_ids"), failures, "taxonomy row missing causal defect classification")
        if row.get("artificial_or_valid") == "ARTIFICIAL_INFRASTRUCTURE_REJECTION":
            _expect(row.get("repair_action_ids"), failures, "repaired artificial row missing repair action")
            _expect(row.get("after_replay_eligible") is True, failures, "artificial row not replay-eligible after repair")
            _expect(row.get("after_paper_eligible") is True, failures, "artificial row not paper-eligible after repair")
        if row.get("artificial_or_valid") == "VALID_REJECTION":
            _expect(
                disposition == "RECLASSIFIED_VALID_REJECTION_NOT_REPAIRABLE",
                failures,
                "valid rejection was force-passed",
            )
    summary = records["PR163_C_FinalSummary.report.json"][0]
    _expect(summary.get("valid_rejection_force_pass_count") == 0, failures, "valid rejection force pass count drift")
    _expect(summary.get("pr162d_r3_misroute_count") == 0, failures, "PR162D-R3 misroute count drift")


def _validate_formula_registry(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    formulas = records["PR163_C_RepairFormulaRegistry.report.json"]
    vectors = records["PR163_C_RepairTestVectorRegistry.report.json"]
    _expect(len(formulas) > 0, failures, "repair formula registry empty")
    _expect(len(vectors) > 0, failures, "repair test vector registry empty")
    formula_ids = {row["formula_ref"] for row in formulas}
    _expect(set(FORMULAS).issubset(formula_ids), failures, "formula registry missing executable formulas")
    for row in vectors:
        actual = apply_formula(row["formula_ref"], row["inputs"])
        _expect(actual == row["expected_output"], failures, f"test vector mismatch: {row['test_vector_ref']}")
        _expect(row.get("test_vector_passed") is True, failures, f"test vector did not pass: {row['test_vector_ref']}")


def _validate_candidate_imputation(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_C_CandidateValueImputationLedger.report.json"]:
        for field in (
            "candidate_value",
            "unit",
            "scale",
            "allowed_range",
            "source_class",
            "source_locator_or_artifact_ref",
            "observed_at_utc",
            "imputation_method",
            "confidence_tier",
        ):
            _expect(row.get(field) not in (None, "", []), failures, f"candidate imputation missing {field}")
        _expect(row.get("candidate_not_truth_flag") is True, failures, "candidate value truth flag drift")
        _expect(row.get("replay_paper_only_flag") is True, failures, "candidate value replay/paper flag drift")
        _expect(row.get("connector_semantic_use_allowed") is False, failures, "candidate value connector use allowed")
        _expect(row.get("live_use_allowed") is False, failures, "candidate value live use allowed")


def _validate_component_repairs(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    expected = len(records["PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json"])
    component_reports = [
        "PR163_C_FeeModelRepairRegistry.report.json",
        "PR163_C_SlippageModelRepairRegistry.report.json",
        "PR163_C_LatencyModelRepairRegistry.report.json",
        "PR163_C_LatencyErrorBudgetLedger.report.json",
        "PR163_C_LiquiditySpreadDepthRepairRegistry.report.json",
        "PR163_C_MakerTakerQueueModelRegistry.report.json",
        "PR163_C_AdverseSelectionModelRegistry.report.json",
        "PR163_C_MarketStateRepairRegistry.report.json",
        "PR163_C_EventLifecycleRepairRegistry.report.json",
        "PR163_C_VenueNormalizationRepairRegistry.report.json",
        "PR163_C_CrossVenueComparabilityRepairRegistry.report.json",
        "PR163_C_OrderIntentRepairRegistry.report.json",
        "PR163_C_OrderLifecycleTraceRepairRegistry.report.json",
        "PR163_C_DuplicateOrderIntentRepairRegistry.report.json",
        "PR163_C_SyntheticFillModelRepairRegistry.report.json",
        "PR163_C_PortfolioExposureLedgerRepairRegistry.report.json",
        "PR163_C_TCAComponentRepairRegistry.report.json",
        "PR163_C_ImplementationShortfallModelRegistry.report.json",
        "PR163_C_RiskCapInputRepairRegistry.report.json",
        "PR163_C_ReplayPaperAdapterAlignmentRepairRegistry.report.json",
        "PR163_C_FormulaCalibrationRepairRegistry.report.json",
    ]
    for report in component_reports:
        _expect(len(records[report]) == expected, failures, f"{report} count mismatch")
    for row in records["PR163_C_FeeModelRepairRegistry.report.json"]:
        _expect(row.get("formula_ref") == "PR163C_FORMULA::FEE_COMPONENT", failures, "fee row formula missing")
        _expect(row.get("fee_model_test_vector_ref"), failures, "fee row test vector missing")
        _expect(row.get("fee_candidate_not_truth_flag") is True, failures, "fee candidate truth flag drift")
    for row in records["PR163_C_TCAComponentRepairRegistry.report.json"]:
        required = [
            "gross_edge_candidate",
            "exchange_fee_component",
            "spread_cross_component",
            "slippage_component",
            "latency_adverse_selection_component",
            "queue_nonfill_opportunity_cost_component",
            "cancel_replace_component",
            "capital_lock_component",
            "settlement_delay_component",
            "stale_data_penalty_component",
            "operational_error_component",
            "expected_net_profit_candidate",
        ]
        for field in required:
            _expect(field in row, failures, f"TCA row missing {field}")
        _expect(row.get("not_profit_evidence_flag") is True, failures, "TCA row profit evidence flag drift")
    for row in records["PR163_C_FutureLiveReadinessFieldPrep.report.json"]:
        _expect(row.get("live_authority_created") is False, failures, "future live prep created live authority")
    for row in records["PR163_C_PortfolioExposureLedgerRepairRegistry.report.json"]:
        _expect(row.get("no_runtime_cash_receipt_flag") is True, failures, "portfolio row runtime cash flag drift")


def _validate_model_risk(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_C_ModelRiskRepairLedger.report.json"]:
        for field in (
            "model_id",
            "model_family",
            "intended_use",
            "model_owner_agent",
            "independent_review_agent",
            "assumptions",
            "limitations",
            "input_fields",
            "output_fields",
            "calibration_basis",
            "test_vector_refs",
            "validation_metric_refs",
            "monitoring_metric_refs",
            "materiality_tier",
            "misuse_warning",
        ):
            _expect(bool(row.get(field)), failures, f"model risk row missing {field}")
        _expect(row.get("no_live_authority_flag") is True, failures, "model risk live flag drift")
        _expect(row.get("not_profit_evidence_flag") is True, failures, "model risk profit flag drift")


def _validate_counterfactual_and_delta(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    expected = len(records["PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json"])
    _expect(len(records["PR163_C_CounterfactualRepairEvaluation.report.json"]) == expected, failures, "counterfactual count mismatch")
    _expect(len(records["PR163_C_RepairDeltaRegistry.report.json"]) == expected, failures, "repair delta count mismatch")
    for row in records["PR163_C_CounterfactualRepairEvaluation.report.json"]:
        _expect(row.get("counterfactual_result") == "REPAIR_CONVERTS_TO_REPLAY_PAPER_READY_OR_NEARER", failures, "counterfactual result drift")
    for row in records["PR163_C_RepairDeltaRegistry.report.json"]:
        _expect(row.get("after_replay_eligible") is True, failures, "repair delta replay after false")
        _expect(row.get("after_paper_eligible") is True, failures, "repair delta paper after false")


def _validate_quantum(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_C_QuantumRepairPrioritizationLedger.report.json"]:
        applicable = any(
            row.get(field) is True
            for field in (
                "qaoa_candidate_applicable",
                "qubo_candidate_applicable",
                "bqm_candidate_applicable",
                "cqm_candidate_applicable",
                "ising_candidate_applicable",
            )
        )
        if applicable:
            _expect(bool(row.get("classical_comparator_ref")), failures, "quantum row missing comparator")
            _expect(bool(row.get("deterministic_classical_score_ref")), failures, "quantum row missing deterministic score")
        _expect(row.get("backend_execution_count") == 0, failures, "quantum backend execution count drift")
        _expect(row.get("quantum_advantage_claim_count") == 0, failures, "quantum advantage claim count drift")


def _validate_agents(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_C_AgentRepairOrchestrationRouter.report.json"]:
        for field in (
            "upstream_agent",
            "downstream_agent",
            "downstream_pr_route",
            "report_consumer",
            "replay_paper_consumer",
            "source_scout_agent",
            "qku_materialization_agent",
            "formula_objective_solver_agent",
            "pr163c_repair_agent",
            "pretrade_agent",
            "tca_agent",
            "latency_agent",
            "risk_agent",
            "replay_agent",
            "paper_agent",
            "formula_calibration_agent",
            "quantum_mapper_advisory_agent",
            "pr165_scoring_agent",
            "pr165b_negative_memory_agent",
            "pr162d_r3_acquisition_repair_agent",
            "plugin_future_agent",
            "dashboard_future_consumer",
            "governance_agent",
            "commander_agent",
        ):
            _expect(bool(row.get(field)), failures, f"agent route missing {field}")
    for row in records["PR163_C_AgentTaskHandoffMatrix.report.json"]:
        _expect(bool(row.get("handoff_to_pr165")), failures, "agent handoff missing PR165 route")
        _expect(bool(row.get("handoff_to_pr165b")), failures, "agent handoff missing PR165-B route")


def _validate_pr165_delta(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    row = records["PR163_C_PR165ReadinessDelta.report.json"][0]
    _expect(row["pr165_ready_after_pr163c"] > row["pr165_ready_before_pr163c"], failures, "PR165 ready count did not increase")
    _expect(row["pr165_blocked_after_pr163c"] < row["pr165_blocked_before_pr163c"], failures, "PR165 blocked count did not decrease")
    _expect(row["pr162d_r3_misroute_count"] == 0, failures, "PR162D-R3 misroute count nonzero")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR163_C_FinalSummary.report.json"][0]
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(key) == expected, failures, f"summary authority count drift: {key}")
    for key in (
        "source_acceptance_count",
        "connector_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "qtt_sha_freeze_checksum_count",
        "atomicrows_sha_hash_mutation_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "llm_runtime_rewrite_count",
        "orphan_qku_count",
        "orphan_pr_file_count",
        "dead_end_file_count",
        "metadata_only_rows",
        "placeholder_only_rows",
        "future_consumer_only_rows",
    ):
        _expect(summary.get(key) == 0, failures, f"summary zero-count drift: {key}")
    _expect(summary.get("all_orphan_counts_zero") is True, failures, "orphan summary not zero")
    _expect(summary.get("all_authority_counts_zero") is True, failures, "authority summary not zero")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
