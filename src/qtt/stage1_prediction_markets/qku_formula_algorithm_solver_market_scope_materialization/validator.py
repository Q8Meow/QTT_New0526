"""Fail-closed PR162B artifact validator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload
from .paths import resolve_repo_relative
from .report_builder import execute_algorithm_test_vector, execute_formula_test_vector


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
    _validate_mandatory_inputs(repo_root, reports, failures)
    _validate_qku_classification(loaded, failures)
    _validate_market_activation_dormancy(loaded, failures)
    _validate_formula_algorithm_materialization(loaded, failures)
    _validate_test_vectors(loaded, failures)
    _validate_solver_mappings_and_bindings(loaded, failures)
    _validate_pr162c_pr162r_pr163_handoff(loaded, failures)
    _validate_forbidden_authority(repo_root, reports, loaded, failures)
    _validate_no_absolute_paths(reports, loaded, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162B report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162B report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162B schema: {filename}")


def _validate_common_report_contracts(
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority class mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(tuple(payload.get("upstream_pr_refs") or ()) == c.UPSTREAM_PR_REFS, failures, f"{filename} upstream refs mismatch")
        for route in c.DOWNSTREAM_PR_ROUTES:
            _expect(route in payload.get("downstream_pr_routes", []), failures, f"{filename} missing downstream route {route}")
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation status must pass")
        for code in payload.get("blocker_codes") or []:
            _expect(code in c.BLOCKER_CODES, failures, f"{filename} blocker code not centralized: {code}")


def _manifest_by_report(
    manifest_payload: dict[str, Any],
    failures: list[str],
) -> dict[str, dict[str, Any]]:
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
        shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
        rows.extend(records_from_payload(shard_payload))
    return rows


def _validate_mandatory_inputs(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    summary = reports["PR162B_FinalSummary.report.json"]
    for ref in c.REQUIRED_INPUT_REPORTS:
        _expect((repo_root / ref).exists(), failures, f"mandatory PR162B input missing: {ref}")
    _expect(summary.get("pr136_control_plane_artifacts_consumed_flag") is True, failures, "PR136 inputs not consumed")
    _expect(summary.get("pr137r_pr138_atomicrows_contracts_consumed_flag") is True, failures, "PR137R/PR138 inputs not consumed")
    _expect(summary.get("pr161c_qku_inventory_graph_consumed_flag") is True, failures, "PR161C inputs not consumed")
    _expect(summary.get("pr161d_scoring_ranking_replay_paper_prep_consumed_flag") is True, failures, "PR161D inputs not consumed")
    _expect(summary.get("pr161e_pr161f_pr162_pr162a_artifacts_consumed_flag") is True, failures, "PR161E/F/162/162A inputs not consumed")


def _validate_qku_classification(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    execution = loaded["PR162B_QKUExecutionClassificationAudit.report.json"]
    _expect(len(execution) == 9360, failures, "all 9360 QKUs must be execution-classified")
    _expect(len({record["qku_id"] for record in execution}) == 9360, failures, "QKU execution classification duplicate/missing IDs")
    for record in execution:
        _expect(record["primary_execution_class"] in c.QKU_EXECUTION_CLASSES, failures, f"invalid execution class: {record['qku_id']}")
        _expect(record["primary_market_scope"] in c.MARKET_SCOPES, failures, f"invalid market scope: {record['qku_id']}")
        _expect(record["blocker_code"] in c.BLOCKER_CODES, failures, f"invalid blocker code: {record['qku_id']}")
        _expect(record["created_by_pr"] == c.PR_ID, failures, f"created_by_pr drift: {record['qku_id']}")


def _validate_market_activation_dormancy(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    market = loaded["PR162B_QKUMarketClassificationRegistry.report.json"]
    activation = loaded["PR162B_QKUStage1PredictionMarketActivationGate.report.json"]
    dormancy = loaded["PR162B_QKUDormancyRegistry.report.json"]
    allowlists = loaded["PR162B_QTTAgentStage1QKUActivationAllowlist.report.json"]
    _expect(len(market) == 9360, failures, "all QKUs must have market classification")
    _expect(len(activation) == 9360, failures, "activation gate must cover all QKUs")
    dormant_qkus = {record["qku_id"] for record in dormancy}
    for record in market:
        _expect(record["primary_market_scope"] in c.MARKET_SCOPES, failures, f"invalid market scope {record['qku_id']}")
        status = record["stage1_prediction_market_activation_status"]
        _expect(status in c.ACTIVATION_STATUSES, failures, f"invalid activation status {record['qku_id']}")
        if record["primary_market_scope"] in c.DORMANT_DEFAULT_MARKET_SCOPES:
            _expect(status.startswith("DORMANT_"), failures, f"non-stage1 market active: {record['qku_id']}")
    router = next(record for record in allowlists if record["agent_id"] == "QTT_EXECUTION_ROUTER_AGENT")
    routed = set(router.get("execution_allowed_qku_refs") or [])
    _expect(not (routed & dormant_qkus), failures, "dormant QKUs appear in execution-router allowlist")


def _validate_formula_algorithm_materialization(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    formulas = loaded["PR162B_QKUFormulaRegistry.report.json"]
    algorithms = loaded["PR162B_QKUAlgorithmRegistry.report.json"]
    objectives = loaded["PR162B_QKUObjectiveFunctionRegistry.report.json"]
    constraints = loaded["PR162B_QKUConstraintRegistry.report.json"]
    parameters = loaded["PR162B_QKUParameterValueRegistry.report.json"]
    tradable = loaded["PR162B_QKUTradableValueCandidateRegistry.report.json"]
    _expect(len(formulas) >= 50, failures, "core formula families must be materialized")
    _expect(len(algorithms) >= 14, failures, "core algorithm families must be materialized")
    _expect(objectives, failures, "objective registry missing")
    _expect(constraints, failures, "constraint registry missing")
    _expect(len(parameters) >= 17, failures, "parameter value registry missing required candidates")
    _expect(len(tradable) >= 17, failures, "tradable value registry missing required candidates")
    names = {record["formula_name"] for record in formulas}
    for required in (
        "expected_value_binary",
        "brier_score_binary",
        "log_loss_binary",
        "kelly_fraction",
        "sharpe_ratio",
        "max_drawdown",
        "QUBO objective x^T Q x",
        "Ising energy",
    ):
        _expect(required in names, failures, f"required formula missing: {required}")
    for record in formulas:
        _expect(record["implementation_status"] in c.FORMULA_IMPLEMENTATION_STATUSES, failures, f"invalid formula status: {record['formula_id']}")
        _expect(record["implementation_module"] and record["implementation_function"], failures, f"formula lacks implementation: {record['formula_id']}")
        _expect(record["test_vector_refs"], failures, f"formula lacks test vector: {record['formula_id']}")
        _expect(record["binding_proof_refs"], failures, f"formula lacks binding proof: {record['formula_id']}")
    for record in algorithms:
        _expect(record["implementation_module"] and record["implementation_function"], failures, f"algorithm lacks implementation: {record['algorithm_id']}")
        _expect(record["test_vector_refs"], failures, f"algorithm lacks test vector: {record['algorithm_id']}")


def _validate_test_vectors(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for record in loaded["PR162B_QKUFormulaTestVectorRegistry.report.json"]:
        try:
            ok = execute_formula_test_vector(record)
        except Exception as exc:
            failures.append(f"formula test vector execution failed {record['test_vector_id']}: {type(exc).__name__}:{exc}")
            continue
        _expect(ok, failures, f"formula test vector mismatch: {record['test_vector_id']}")
        _expect(record["test_status"] == "FORMULA_TEST_VECTOR_EXECUTED", failures, f"formula test vector status drift: {record['test_vector_id']}")
    for record in loaded["PR162B_QKUAlgorithmTestVectorRegistry.report.json"]:
        try:
            ok = execute_algorithm_test_vector(record)
        except Exception as exc:
            failures.append(f"algorithm test vector execution failed {record['test_vector_id']}: {type(exc).__name__}:{exc}")
            continue
        _expect(ok, failures, f"algorithm test vector mismatch: {record['test_vector_id']}")
        _expect(record["test_status"] == "ALGORITHM_TEST_VECTOR_EXECUTED", failures, f"algorithm test vector status drift: {record['test_vector_id']}")
    smoke = loaded["PR162B_QuantumSolverSmokeExecutionReport.report.json"]
    _expect(smoke, failures, "smoke solver report missing")
    _expect(all(record["smoke_execution_status"] == "SMOKE_EXECUTED_NO_TRADING_EVIDENCE" for record in smoke), failures, "smoke execution not labeled no-trading-evidence")


def _validate_solver_mappings_and_bindings(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    mappings = loaded["PR162B_QKUSolverMappingRegistry.report.json"]
    proofs = loaded["PR162B_QKUFormulaBindingProofMatrix.report.json"]
    proof_ids = {record["binding_proof_id"] for record in proofs}
    _expect(any(record["compatible_solver_family"].startswith("CLASSICAL") for record in mappings), failures, "classical solver mapping missing")
    _expect(any("QUBO" in record["compatible_solver_family"] or "ISING" in record["compatible_solver_family"] for record in mappings), failures, "QUBO/Ising solver mapping missing")
    _expect(any(record["binding_method"] == "BROAD_BINDING_ATTEMPT_REJECTED" for record in proofs), failures, "broad formula-to-QKU binding was not blocked")
    for record in proofs:
        _expect(record["binding_status"] in c.BINDING_PROOF_STATUSES, failures, f"invalid binding status: {record['binding_proof_id']}")
        _expect(record["blocker_code"] in c.BLOCKER_CODES, failures, f"invalid binding blocker: {record['binding_proof_id']}")
    for record in mappings:
        _expect(record["compatible_solver_family"] in c.SOLVER_FAMILIES, failures, f"invalid solver family: {record['solver_mapping_id']}")
        _expect(record["binding_proof_refs"], failures, f"solver mapping lacks binding proof: {record['solver_mapping_id']}")
        _expect(set(record["binding_proof_refs"]) <= proof_ids, failures, f"solver mapping proof missing: {record['solver_mapping_id']}")
        _expect(record["evidence_execution_allowed_flag"] is False, failures, f"solver mapping evidence execution allowed: {record['solver_mapping_id']}")
        _expect(record["live_execution_allowed_flag"] is False, failures, f"solver mapping live execution allowed: {record['solver_mapping_id']}")


def _validate_pr162c_pr162r_pr163_handoff(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = loaded["PR162B_FinalSummary.report.json"][0]
    handoff = loaded["PR162B_PR162CDataRequirementHandoff.report.json"]
    _expect(handoff, failures, "PR162C data requirement handoff missing")
    _expect("BLOCKED" in summary["pr162r_readiness_state"], failures, "PR162R incorrectly ready")
    _expect("BLOCKED" in summary["pr163_readiness_state"], failures, "PR163 incorrectly ready")
    for record in handoff:
        _expect(record["downstream_pr_route"] == "PR162C_STRICT_DATA_EXPANSION", failures, f"handoff route drift: {record['handoff_id']}")
        _expect(record["pr162r_ready_flag"] is False, failures, f"handoff marked PR162R ready: {record['handoff_id']}")


def _validate_forbidden_authority(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    scan = loaded["PR162B_ForbiddenAuthorityScan.report.json"][0]
    _expect(scan["scan_status"] == "PASS", failures, "forbidden authority scan failed")
    _expect(scan["no_scattered_hardcoded_policy_scan_status"] == "PASS", failures, "no-scattered-hardcoded-policy scan failed")
    for payload in reports.values():
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"authority flag drift {payload.get('report_filename')} {flag}")


def _validate_no_absolute_paths(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    def scan(value: Any, label: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                scan(item, f"{label}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                scan(item, f"{label}[{index}]")
        elif isinstance(value, str):
            if PureWindowsPath(value).drive:
                failures.append(f"absolute Windows path in generated output: {label}")

    for filename, payload in reports.items():
        scan(payload, filename)
    for filename, rows in loaded.items():
        scan(rows, filename)


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
