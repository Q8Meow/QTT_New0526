"""Validate PR166-QB generated artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import FORBIDDEN_AUTHORITY_FLAGS, ZERO_AUTHORITY_KEYS
from .io import read_json, records_from_report_payload
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import NumericDomainError
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ReasonCode
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_companion_alignment_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_manifest_consistency_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_directory_entries_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_schema_records_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_schema_session_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import is_finite_json_number_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import is_nonnegative_json_integer_v1
from .report_writer import schema_filename


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    schema_check = _report_schema_session_v1(repo_root, c, read_json, profile="QB", schema_name=schema_filename)
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_REPORT::{filename}")
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = _report_schema_records_v1(repo_root, payload, read_json, schema_check, filename)
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))
    _validate_schemas(repo_root, payloads, failures)
    _validate_payload_contracts(payloads, records, failures)
    try:
        _report_manifest_consistency_v1(
            payloads, records, c.REPORT_FILENAMES,
            "PR166_QB_ReportManifest.report.json", c.GENERATED_DIR, c.SCHEMA_DIR,
            style="ROOT_REFERENCE", schema_refs=None,
        )
    except SerializationSafetyError as exc:
        failures.append(str(exc))
    _validate_inputs(repo_root, records, failures)
    _validate_benchmark_rows(records, failures)
    _validate_budget(records, failures)
    _validate_fairness(records, failures)
    _validate_race(records, failures)
    _validate_receipts(records, failures)
    _validate_repair_lab(records, failures)
    _validate_cloud_and_owner(records, failures)
    _validate_market_portability(records, failures)
    _validate_agents_and_orphans(records, failures)
    _validate_artifact_map(records, failures)
    _validate_summary(records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(ok=not failures, failures=tuple(failures))


def _validate_schemas(
    repo_root: Path,
    payloads: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for filename, payload in payloads.items():
        schema_ref = payload.get("schema_ref")
        if not schema_ref:
            failures.append(f"MISSING_SCHEMA_REF::{filename}")
            continue
        if not (repo_root / c.SCHEMA_DIR / str(schema_ref)).exists():
            failures.append(f"MISSING_SCHEMA_FILE::{filename}::{schema_ref}")


def _validate_payload_contracts(
    payloads: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in payloads.items():
        if payload.get("roadmap_pr_id") != c.PR_ID:
            failures.append(f"BAD_ROADMAP_PR::{filename}")
        if payload.get("created_by_pr") != c.PR_ID:
            failures.append(f"BAD_CREATED_BY_PR::{filename}")
        if not is_nonnegative_json_integer_v1(payload.get("record_count")) or payload.get("record_count") != len(records[filename]):
            failures.append(f"BAD_RECORD_COUNT::{filename}")
        for key in ZERO_AUTHORITY_KEYS:
            if (not is_nonnegative_json_integer_v1(payload.get(key, 0)) or payload.get(key, 0) != 0):
                failures.append(f"PAYLOAD_FORBIDDEN_AUTHORITY_COUNT::{filename}::{key}")
        if filename in c.BENCHMARK_ROW_REPORTS and not payload.get("sharded_flag"):
            failures.append(f"ROW_REPORT_NOT_SHARDED::{filename}")


def _validate_inputs(
    repo_root: Path,
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    lineage_primary = None
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_INPUT_REPORT::{filename}")
            continue
        payload = read_json(path)
        expanded = records_from_report_payload(repo_root, payload)
        if filename == 'PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json':
            lineage_primary = expanded
        if filename in c.EXPECTED_559_INPUTS and len(expanded) != 559:
            failures.append(f"INPUT_COUNT_DRIFT::{filename}::{len(expanded)}")
    input_rows = records["PR166_QB_InputConsumption.report.json"]
    if len(input_rows) != len(c.STRICT_INPUT_REPORTS):
        failures.append("INPUT_CONSUMPTION_ROW_COUNT_MISMATCH")
    for row in input_rows:
        if not row.get("record_count_matches_expected_flag"):
            failures.append(f"INPUT_EXPECTED_COUNT_FAIL::{row.get('source_report_ref')}")

    try:
        _report_companion_alignment_v1(
            lineage_primary, {name: records[name] for name in c.BENCHMARK_ROW_REPORTS}
        )
    except SerializationSafetyError:
        failures.append("INPUT_CANDIDATE_LINEAGE_MISMATCH")


def _validate_benchmark_rows(
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename in c.BENCHMARK_ROW_REPORTS:
        rows = records[filename]
        if len(rows) != 559:
            failures.append(f"BENCHMARK_ROW_COUNT_NOT_559::{filename}::{len(rows)}")
            continue
        row_ids = set()
        for row in rows:
            row_id = str(row.get("row_id"))
            if row_id in row_ids:
                failures.append(f"DUPLICATE_ROW_ID::{filename}::{row_id}")
            row_ids.add(row_id)
            disposition = row.get("benchmark_disposition")
            if disposition not in c.BENCHMARK_DISPOSITIONS:
                failures.append(f"BAD_BENCHMARK_DISPOSITION::{filename}::{row_id}::{disposition}")
            if disposition in c.FORBIDDEN_BENCHMARK_DISPOSITIONS:
                failures.append(f"FORBIDDEN_BENCHMARK_DISPOSITION::{filename}::{row_id}::{disposition}")
            mode = row.get("benchmark_execution_mode")
            if mode not in c.EXECUTION_MODES:
                failures.append(f"BAD_EXECUTION_MODE::{filename}::{row_id}::{mode}")
            if mode in c.FORBIDDEN_EXECUTION_MODES:
                failures.append(f"FORBIDDEN_EXECUTION_MODE::{filename}::{row_id}::{mode}")
            for key in ZERO_AUTHORITY_KEYS:
                if (not is_nonnegative_json_integer_v1(row.get(key, 0)) or row.get(key, 0) != 0):
                    failures.append(f"ROW_FORBIDDEN_AUTHORITY_COUNT::{filename}::{row_id}::{key}")
            for flag in FORBIDDEN_AUTHORITY_FLAGS:
                if row.get(flag) is not False:
                    failures.append(f"ROW_FORBIDDEN_AUTHORITY_FLAG::{filename}::{row_id}::{flag}")
            if not row.get("classical_fallback_required_flag", True):
                failures.append(f"MISSING_CLASSICAL_FALLBACK::{filename}::{row_id}")
            if row.get("profit_evidence_flag") is not False:
                failures.append(f"PROFIT_EVIDENCE_FLAG_TRUE::{filename}::{row_id}")


def _validate_budget(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    budget = records["PR166_QB_BudgetPolicy.report.json"][0]
    actual_size = budget.get("actual_benchmark_subset_size")
    if type(actual_size) is not int:
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT,
            "actual_benchmark_subset_size must be an integer, not a Boolean or coerced value",
        )
    if actual_size < 0:
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            "actual_benchmark_subset_size must be nonnegative",
        )
    selection_rows = records["PR166_QB_SubsetSelection.report.json"]
    for row in selection_rows:
        if type(row.get("benchmark_subset_flag")) is not bool:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                f"benchmark_subset_flag must be a Boolean: {row.get('row_id')}",
            )
    subset_rows = [row for row in selection_rows if row["benchmark_subset_flag"]]
    if len(subset_rows) != actual_size:
        failures.append("SUBSET_SIZE_MISMATCH")
    if len(subset_rows) > c.BENCHMARK_CAPS["max_actual_benchmark_rows_default_ci"]:
        failures.append("SUBSET_CAP_EXCEEDED")
    family_counts = Counter(row["model_family"] for row in subset_rows)
    for family, count in family_counts.items():
        if count > c.BENCHMARK_CAPS["max_rows_per_family_default_ci"]:
            failures.append(f"FAMILY_CAP_EXCEEDED::{family}::{count}")
    for row in subset_rows:
        for field, cap_field, failure_prefix in (
            ("iterations_used", "max_optimizer_iterations_default_ci", "ITERATION_CAP_EXCEEDED"),
            ("samples_or_reads_used", "max_samples_or_reads_default_ci", "SAMPLE_CAP_EXCEEDED"),
            ("seed_count", "max_random_seeds_default_ci", "SEED_CAP_EXCEEDED"),
            ("problem_variable_count", "max_problem_variables_default_ci", "VARIABLE_CAP_EXCEEDED"),
        ):
            value = row.get(field)
            if type(value) is not int:
                raise NumericDomainError(
                    ReasonCode.INVALID_NUMERIC_INPUT,
                    f"{field} must be an observed integer: {row.get('row_id')}",
                )
            if value < 0:
                raise NumericDomainError(
                    ReasonCode.OUT_OF_DOMAIN,
                    f"{field} must be nonnegative: {row.get('row_id')}",
                )
            if value > c.BENCHMARK_CAPS[cap_field]:
                failures.append(f"{failure_prefix}::{row.get('row_id')}")


def _validate_fairness(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QB_FairnessNorm.report.json"]:
        if row.get("objective_direction_normalized") != "MAXIMIZE_EXECUTION_ADJUSTED_EDGE":
            failures.append(f"FAIRNESS_DIRECTION_MISSING::{row.get('row_id')}")
        if row.get("minmax_sign") != 1:
            failures.append(f"FAIRNESS_SIGN_BAD::{row.get('row_id')}")
        if row.get("same_budget_comparison_flag") is not True:
            failures.append(f"FAIRNESS_SAME_BUDGET_MISSING::{row.get('row_id')}")
        if not row.get("energy_to_edge_translation"):
            failures.append(f"FAIRNESS_TRANSLATION_MISSING::{row.get('row_id')}")
        if row.get("constraint_penalty_policy") in {"", None}:
            failures.append(f"FAIRNESS_CONSTRAINT_POLICY_MISSING::{row.get('row_id')}")


def _validate_race(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QB_RaceArb.report.json"]:
        for key in (
            "classical_route_score",
            "quantum_inspired_route_score",
            "true_quantum_structural_route_score",
            "hybrid_route_score",
            "final_arbitration_score",
        ):
            if not is_finite_json_number_v1(row.get(key)):
                failures.append(f"RACE_SCORE_MISSING::{row.get('row_id')}::{key}")
        if row.get("classical_fallback_required_flag") is not True:
            failures.append(f"RACE_CLASSICAL_FALLBACK_MISSING::{row.get('row_id')}")
        if row.get("hot_path_allowed_flag") is not False:
            failures.append(f"RACE_HOT_PATH_ALLOWED::{row.get('row_id')}")
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"RACE_LIVE_AUTHORITY::{row.get('row_id')}")
        if row.get("winning_nonlive_route") == "TRUE_QUANTUM_STRUCTURAL_PAPER_ONLY":
            failures.append(f"TRUE_QUANTUM_CANNOT_WIN_LIVE_ROUTE::{row.get('row_id')}")


def _validate_receipts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    qaoa = records["PR166_QB_QAOAReceipt.report.json"]
    svqe = records["PR166_QB_SamplingVQEReceipt.report.json"]
    for row in [*qaoa, *svqe]:
        if row.get("dependency_available_flag") is not False:
            failures.append(f"SIMULATOR_DEPENDENCY_SHOULD_BE_UNAVAILABLE::{row.get('row_id')}")
        if row.get("benchmark_executed_flag") is not False:
            failures.append(f"SIMULATOR_DEP_UNAVAILABLE_EXECUTED::{row.get('row_id')}")
        if row.get("cloud_backend_execution_flag") is not False:
            failures.append(f"SIMULATOR_CLOUD_EXECUTION::{row.get('row_id')}")
    executed_local = [
        row
        for row in records["PR166_QB_ClassicalReceipt.report.json"]
        if row.get("benchmark_executed_flag")
    ]
    if not executed_local:
        failures.append("NO_CLASSICAL_LOCAL_EXECUTION_RECEIPTS")
    qinspired = [
        row
        for row in records["PR166_QB_QInspiredReceipt.report.json"]
        if row.get("benchmark_executed_flag")
    ]
    if not qinspired:
        failures.append("NO_QINSPIRED_LOCAL_EXECUTION_RECEIPTS")


def _validate_repair_lab(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QB_QuantumRepairLab.report.json"]:
        if not row.get("repair_row_id"):
            failures.append(f"REPAIR_ROW_ID_MISSING::{row.get('row_id')}")
        if row.get("not_profit_evidence_flag") is not True:
            failures.append(f"REPAIR_PROFIT_EVIDENCE::{row.get('row_id')}")
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"REPAIR_LIVE_AUTHORITY::{row.get('row_id')}")
        if not row.get("downstream_pr166_qc_route_ref") and not row.get("downstream_pr162e_q_route_ref"):
            failures.append(f"REPAIR_ROUTE_MISSING::{row.get('row_id')}")


def _validate_cloud_and_owner(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename in (
        "PR166_QB_CloudSwitchReady.report.json",
        "PR166_QB_OwnerQuantumControlReady.report.json",
    ):
        for row in records[filename]:
            if row.get("default_mode") != "OFF":
                failures.append(f"DEFAULT_MODE_NOT_OFF::{filename}::{row.get('row_id')}")
            for key in (
                "credential_access_allowed_flag",
                "backend_execution_allowed_flag",
                "live_order_authority_flag",
                "quantum_advantage_claim_flag",
                "profit_evidence_flag",
            ):
                if row.get(key) is not False:
                    failures.append(f"SWITCHBOARD_AUTHORITY_TRUE::{filename}::{row.get('row_id')}::{key}")
            if row.get("no_backend_execution_flag") is not True:
                failures.append(f"SWITCHBOARD_BACKEND_FLAG_MISSING::{filename}::{row.get('row_id')}")
            if filename.endswith("OwnerQuantumControlReady.report.json"):
                if row.get("dashboard_implementation_required_flag") is not True:
                    failures.append(f"OWNER_DASHBOARD_IMPL_REQUIRED_MISSING::{row.get('row_id')}")
                if row.get("dashboard_ui_implemented_flag") is not False:
                    failures.append(f"OWNER_DASHBOARD_UI_CLAIMED::{row.get('row_id')}")


def _validate_market_portability(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QB_MarketPortability.report.json"]:
        if row.get("stage1_prediction_market_flag") is not True:
            failures.append(f"MARKET_STAGE1_MISSING::{row.get('row_id')}")
        if row.get("future_market_portability_flag") is not True:
            failures.append(f"MARKET_PORTABILITY_MISSING::{row.get('row_id')}")
        if row.get("no_current_connector_binding_flag") is not True:
            failures.append(f"MARKET_CONNECTOR_BOUND::{row.get('row_id')}")
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"MARKET_LIVE_AUTHORITY::{row.get('row_id')}")


def _validate_agents_and_orphans(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QB_AgentWorkOrders.report.json"]:
        for key in (
            "work_order_id",
            "owning_agent_id",
            "agent_duty_ref",
            "expected_input_refs",
            "expected_output_refs",
            "downstream_agent_refs",
            "expected_agent_output_artifact",
        ):
            if not row.get(key):
                failures.append(f"AGENT_WORK_ORDER_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR166_QB_AgentDAG.report.json"]:
        for key in (
            "dag_node_id",
            "upstream_pr_refs",
            "upstream_row_refs",
            "race_arbitration_route",
            "future_cloud_switchboard_route",
            "future_owner_dashboard_route",
            "no_orphan_proof",
        ):
            if not row.get(key):
                failures.append(f"AGENT_DAG_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR166_QB_NoOrphanProof.report.json"]:
        if row.get("no_orphan_status") != "NO_ORPHAN":
            failures.append(f"NO_ORPHAN_STATUS_FAIL::{row.get('row_id')}")
        if not row.get("artifact_refs_checked"):
            failures.append(f"NO_ORPHAN_REFS_MISSING::{row.get('row_id')}")


def _validate_artifact_map(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_QB_ArtifactMap.report.json"]
    if not rows:
        failures.append("ARTIFACT_MAP_EMPTY")
    for row in rows:
        if not row.get("artifact_path"):
            failures.append(f"ARTIFACT_PATH_MISSING::{row.get('row_id')}")
        if not row.get("consumed_by_module"):
            failures.append(f"ARTIFACT_CONSUMER_MISSING::{row.get('row_id')}")
        if row.get("terminal_flag") and not row.get("terminal_reason"):
            failures.append(f"ARTIFACT_TERMINAL_REASON_MISSING::{row.get('row_id')}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_QB_FinalSummary.report.json"][0]
    if (not is_nonnegative_json_integer_v1(summary.get("consumed_pr166_qb_handoff_rows"))
            or summary.get("consumed_pr166_qb_handoff_rows") != 559):
        failures.append("SUMMARY_HANDOFF_COUNT_NOT_559")
    if not is_nonnegative_json_integer_v1(summary.get("benchmark_subset_count", 0)):
        failures.append("SUMMARY_SUBSET_COUNT_INVALID")
    elif summary.get("benchmark_subset_count", 0) > c.BENCHMARK_CAPS["max_actual_benchmark_rows_default_ci"]:
        failures.append("SUMMARY_SUBSET_CAP_EXCEEDED")
    if summary.get("forbidden_authority_counts_all_zero_flag") is not True:
        failures.append("SUMMARY_AUTHORITY_NOT_ZERO")
    if summary.get("cloud_switchboard_default_mode") != "OFF":
        failures.append("SUMMARY_CLOUD_DEFAULT_NOT_OFF")
    if summary.get("owner_dashboard_default_mode") != "OFF":
        failures.append("SUMMARY_OWNER_DEFAULT_NOT_OFF")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    from fnmatch import fnmatch
    for path in _report_directory_entries_v1(repo_root / c.GENERATED_DIR):
        if not fnmatch(path.name, "PR166_QB_*"):
            continue
        name = path.name.lower()
        if any(token in name for token in ("sha256", "checksum", "freeze", "global_digest")):
            failures.append(f"FORBIDDEN_DIGEST_ARTIFACT::{path.name}")
