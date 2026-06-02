"""Fail-closed PR162C artifact validator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from . import constants as c
from .formula_test_vectors import execute_test_vector
from .json_io import read_json, records_from_payload
from .paths import resolve_repo_relative


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_common_report_contracts(reports, failures)
    manifest_by_report = _manifest_by_report(reports[c.SHARD_MANIFEST_REPORT_FILENAME], failures)
    loaded = {
        filename: _load_records(repo_root, filename, reports[filename], manifest_by_report, failures)
        for filename in c.REPORT_FILENAMES
        if filename != c.SHARD_MANIFEST_REPORT_FILENAME
    }
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_preflight(reports, failures)
    _validate_pr162b_baseline_consumed(repo_root, failures)
    _validate_requirement_classification(reports, loaded, failures)
    _validate_qku_execution_market_agent_coverage(loaded, failures)
    _validate_delta_records(loaded, failures)
    _validate_strict_coverage_and_readiness(reports, loaded, failures)
    _validate_source_and_owner_commands(loaded, failures)
    _validate_forbidden_authority(reports, loaded, failures)
    _validate_pr162a_repaired_state(reports, failures)
    _validate_no_absolute_paths(reports, loaded, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162C report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162C report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162C schema: {filename}")


def _validate_common_report_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority class mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(isinstance(payload.get("source_inputs"), list), failures, f"{filename} missing source_inputs")
        _expect(tuple(payload.get("upstream_pr_refs") or ()) == c.UPSTREAM_PR_REFS, failures, f"{filename} upstream refs mismatch")
        for route in c.DOWNSTREAM_PR_ROUTES:
            _expect(route in payload.get("downstream_pr_routes", []), failures, f"{filename} missing downstream route {route}")
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation status must pass")
        for code in payload.get("blocker_codes") or []:
            _expect(code in c.BLOCKER_CODES, failures, f"{filename} blocker code not centralized: {code}")


def _manifest_by_report(manifest_payload: dict[str, Any], failures: list[str]) -> dict[str, dict[str, Any]]:
    records = records_from_payload(manifest_payload)
    manifest = {record["report_filename"]: record for record in records}
    for record in records:
        _expect(record.get("posix_relative_shard_refs_flag") is True, failures, f"non-portable shard refs: {record.get('report_filename')}")
    return manifest


def _load_records(
    repo_root: Path,
    filename: str,
    payload: dict[str, Any],
    manifest_by_report: dict[str, dict[str, Any]],
    failures: list[str],
) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest_record = manifest_by_report.get(filename)
    if not manifest_record:
        failures.append(f"missing shard manifest record for {filename}")
        return []
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_record.get("shard_files", []):
        if "\\" in shard_ref or PureWindowsPath(shard_ref).drive:
            failures.append(f"non-portable shard path: {shard_ref}")
            continue
        rows.extend(records_from_payload(read_json(resolve_repo_relative(repo_root, shard_ref))))
    return rows


def _validate_preflight(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename in (c.PREFLIGHT_REPORT_FILENAME, c.PREFLIGHT_ALIAS_REPORT_FILENAME):
        receipt = reports[filename]
        _expect(receipt.get("PR136_control_plane_consumed") is True, failures, f"{filename} PR136 not consumed")
        _expect(receipt.get("PR162B_handoff_consumed") is True, failures, f"{filename} PR162B handoff not consumed")
        _expect(receipt.get("PR162B_registry_baseline_consumed") is True, failures, f"{filename} PR162B baseline not consumed")
        _expect(receipt.get("PR162A_repaired_state_consumed") is True, failures, f"{filename} PR162A repaired state not consumed")
        _expect(receipt.get("online_discovery_allowed") is True, failures, f"{filename} online discovery flag drift")
        _expect(receipt.get("ci_offline_required") is True, failures, f"{filename} CI offline flag drift")
        _expect(receipt.get("no_sha_freeze_hash_authority_confirmed") is True, failures, f"{filename} digest-authority guard missing")
        _expect(receipt.get("no_atomicrows_bundle_mutation_confirmed") is True, failures, f"{filename} AtomicRows mutation guard missing")
    missing = reports[c.PREFLIGHT_REPORT_FILENAME].get("required_inputs_missing") or []
    fallbacks = reports[c.PREFLIGHT_REPORT_FILENAME].get("fallback_paths_used") or []
    if "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json" in missing:
        _expect(fallbacks, failures, "missing PR136 section crosswalk must have deterministic fallback")


def _validate_pr162b_baseline_consumed(repo_root: Path, failures: list[str]) -> None:
    for filename in c.PR162B_REGISTRY_REPORTS:
        payload = read_json(repo_root / c.GENERATED_DIR / filename)
        _expect(payload.get("created_by_pr") == "PR162B", failures, f"PR162B registry overwritten or malformed: {filename}")


def _validate_requirement_classification(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = reports["PR162C_FinalSummary.report.json"]
    ledger = loaded["PR162C_DataRequirementClassificationLedger.report.json"]
    proofs = loaded["PR162C_StrictQKUCoverageProofMatrix.report.json"]
    _expect(summary.get("data_requirement_total") == 6502, failures, "PR162C must consume 6502 PR162B requirements")
    _expect(len(ledger) == 6502, failures, "all 6502 data requirements must be classified")
    _expect(len(proofs) == 6502, failures, "strict proof matrix must cover all 6502 requirements")
    _expect(summary.get("unclassified_requirement_count") == 0, failures, "unclassified requirement count must be zero")
    statuses = {record["terminal_status"] for record in ledger}
    _expect(statuses <= set(c.TERMINAL_REQUIREMENT_STATUSES), failures, f"requirement terminal status not centralized: {sorted(statuses)}")
    _expect(all(record["blocker_code"] in c.BLOCKER_CODES for record in ledger), failures, "requirement blocker not centralized")


def _validate_qku_execution_market_agent_coverage(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    qkus = loaded["PR162C_QKUExecutionClassificationRegistry.report.json"]
    routes = loaded["PR162C_QTTAgentExecutableQKURoutingMatrix.report.json"]
    market = loaded["PR162C_QKUMarketClassificationContinuityAudit.report.json"]
    activation = loaded["PR162C_QKUStage1ActivationContinuityAudit.report.json"]
    dormancy = loaded["PR162C_QKUDormancyContinuityAudit.report.json"]
    _expect(len(qkus) == 9360, failures, "all 9360 QKUs must be PR162C execution-classified")
    _expect(len({record["qku_id"] for record in qkus}) == 9360, failures, "duplicate/missing PR162C QKU classification IDs")
    _expect(len(routes) == 9360, failures, "all 9360 QKUs must have agent routes")
    _expect(len(market) == 9360 and len(activation) == 9360 and len(dormancy) == 9360, failures, "market/activation/dormancy continuity must cover all QKUs")
    route_qkus = {record["qku_id"] for record in routes}
    for record in qkus:
        _expect(record["primary_execution_class"] in c.QKU_EXECUTION_CLASSES, failures, f"invalid PR162C execution class: {record['qku_id']}")
        _expect(record["primary_market_scope"] in c.MARKET_SCOPES, failures, f"invalid PR162C market scope: {record['qku_id']}")
        _expect(record["stage1_prediction_market_activation_status"] in c.ACTIVATION_STATUSES, failures, f"invalid activation status: {record['qku_id']}")
        _expect(record["dormancy_status"] in c.DORMANCY_STATUSES, failures, f"invalid dormancy status: {record['qku_id']}")
        _expect(record["qku_id"] in route_qkus, failures, f"orphan QKU without route: {record['qku_id']}")
        if record["primary_execution_class"] == c.EXECUTION_METADATA_ONLY_BLOCKED:
            _expect(record["blocker_code"] != "NONE", failures, f"metadata-only QKU lacks blocker: {record['qku_id']}")


def _validate_delta_records(loaded: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    formulas = loaded["PR162C_QKUFormulaRegistryDelta.report.json"]
    algorithms = loaded["PR162C_QKUAlgorithmRegistryDelta.report.json"]
    values = (
        loaded["PR162C_QKUParameterValueRegistryDelta.report.json"]
        + loaded["PR162C_QKUTradableValueCandidateRegistryDelta.report.json"]
    )
    solvers = loaded["PR162C_QKUSolverMappingRegistryDelta.report.json"]
    tests = loaded["PR162C_QKUFormulaTestVectorRegistryDelta.report.json"]
    _expect(formulas, failures, "formula delta records missing")
    _expect(algorithms, failures, "algorithm delta records missing")
    _expect(values, failures, "value delta records missing")
    _expect(solvers, failures, "solver delta records missing")
    for record in formulas + algorithms + values + solvers:
        _expect(record.get("source_class") in c.SOURCE_CLASSES, failures, f"delta source class not centralized: {record.get('source_class')}")
        _expect(bool(record.get("source_locator")), failures, f"delta lacks source locator: {record.get('record_id') or record.get('formula_id') or record.get('algorithm_id')}")
        _expect(record.get("not_live_authority") is True, failures, f"delta creates live authority: {record.get('formula_id') or record.get('algorithm_id')}")
    test_ids = {record["test_vector_id"] for record in tests}
    for record in formulas:
        _expect(set(record.get("test_vector_refs") or []) <= test_ids, failures, f"formula delta test vector missing: {record['formula_id']}")
    for record in algorithms:
        _expect(set(record.get("test_vector_refs") or []) <= test_ids, failures, f"algorithm delta test vector missing: {record['algorithm_id']}")
    for record in tests:
        try:
            ok = execute_test_vector(record)
        except Exception as exc:
            failures.append(f"PR162C test vector execution failed {record['test_vector_id']}: {type(exc).__name__}:{exc}")
            continue
        _expect(ok, failures, f"PR162C test vector mismatch: {record['test_vector_id']}")


def _validate_strict_coverage_and_readiness(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = reports["PR162C_FinalSummary.report.json"]
    proofs = loaded["PR162C_StrictQKUCoverageProofMatrix.report.json"]
    pr162r = loaded["PR162C_PR162RAdapterRerunReadinessBridge.report.json"]
    pr163 = loaded["PR162C_PR163ReadinessBlockerStatus.report.json"]
    ready_proofs = [record for record in proofs if record["pr162r_ready_flag"]]
    _expect(summary.get("strict_run_capable_qku_count") == len(ready_proofs), failures, "strict ready summary drift")
    _expect(all(record["pr163_ready_flag"] is False for record in proofs), failures, "PR163 marked ready in proof")
    _expect(all(record["pr163_ready_flag"] is False for record in pr163), failures, "PR163 blocker report marked ready")
    _expect(summary.get("pr163_blocker_status", "").startswith("BLOCKED_"), failures, "PR163 must remain blocked")
    for record in pr162r:
        if record["pr162r_ready_flag"]:
            _expect(record["strict_coverage_status"] == c.STATUS_STRICT_COVERED_REPO_LOCAL, failures, f"PR162R ready without strict coverage: {record['qku_id']}")
    if summary.get("success_state") == "HONEST_BLOCKER":
        _expect(summary.get("strict_run_capable_qku_count") == 0, failures, "honest blocker cannot have strict ready QKUs")
        _expect(summary.get("pr162r_readiness_status") == "BLOCKED_NO_STRICT_COVERED_QKUS", failures, "PR162R status must be blocked in honest blocker state")


def _validate_source_and_owner_commands(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    sources = loaded["PR162C_SourcePortfolioRegistry.report.json"]
    commands = loaded["PR162C_OwnerMaterializationCommandQueue.report.json"]
    _expect(len(sources) >= 6, failures, "source portfolio should include prioritized lanes")
    source_classes = {record["source_class"] for record in sources}
    for source_class in (
        "OFFICIAL_VENUE_PUBLIC_API",
        "OFFICIAL_VENUE_PUBLIC_CSV",
        "PUBLIC_RESEARCH_DATASET_CANDIDATE",
        "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
    ):
        _expect(source_class in source_classes, failures, f"missing source class: {source_class}")
    _expect(commands, failures, "owner materialization command queue missing")
    for record in commands:
        _expect(record["execute_in_default_ci_flag"] is False, failures, f"owner command executes in CI: {record['command_id']}")
        _expect(not Path(record["destination_path"]).is_absolute(), failures, f"owner command destination absolute: {record['command_id']}")


def _validate_forbidden_authority(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = reports["PR162C_FinalSummary.report.json"]
    scan = loaded["PR162C_ForbiddenAuthorityScan.report.json"][0]
    _expect(scan["scan_status"] == "PASS", failures, "forbidden authority scan failed")
    _expect(scan["no_scattered_hardcoded_policy_scan_status"] == "PASS", failures, "no-scattered policy scan failed")
    _expect(summary["forbidden_authority_scan_result"] == "PASS", failures, "summary forbidden scan drift")
    _expect(summary["no_sha_freeze_hash_authority_confirmed"] is True, failures, "digest authority guard drift")
    _expect(summary["no_atomicrows_bundle_mutation_confirmed"] is True, failures, "AtomicRows mutation guard drift")


def _validate_pr162a_repaired_state(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = reports["PR162C_FinalSummary.report.json"]
    _expect(summary.get("pr162a_repaired_qkus_mapped_to_run_capable_datasets") == 0, failures, "PR162A repaired qku run-capable count drift")
    _expect(summary.get("pr162a_repaired_pr162_adapter_rerun_ready_count") == 0, failures, "PR162A repaired rerun ready drift")
    _expect(summary.get("pr162a_repaired_pr162_adapter_rerun_blocked_count") == 9360, failures, "PR162A repaired rerun blocked drift")
    _expect(summary.get("pr162a_repaired_run_capable_dataset_count") == 1, failures, "PR162A repaired run-capable dataset count drift")


def _validate_no_absolute_paths(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    def walk(value: Any, location: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{location}[{index}]")
        elif isinstance(value, str):
            text = value.replace("\\", "/")
            if PureWindowsPath(value).drive or text.startswith("//"):
                failures.append(f"absolute path leaked into PR162C artifact at {location}: {value}")
    for filename, payload in reports.items():
        walk(payload, filename)
    for filename, records in loaded.items():
        walk(records, filename)


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
