#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import subprocess
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (
    ATOMICROWS_BUNDLE_STATE_DEFINITIONS,
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    AtomicRowsBundleState,
    atomicrows_bundle_state_report,
    expected_atomicrows_bundle_state_from_contract,
    validate_current_atomicrows_bundle_state,
)
from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.validate_master_plan_section_coverage import validate_json_schema_subset


REPO_ROOT = _REPO_ROOT
DEFAULT_CONTRACT = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsBundleBoundaryStateContract.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_bundle_boundary_state_contract.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/AtomicRowsBundleBoundaryStateContract.report.json"
)

SUCCESS_MARKER = "QTT_ATOMICROWS_BUNDLE_BOUNDARY_STATE_CONTRACT_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_BUNDLE_BOUNDARY_STATE_CONTRACT_FAILED"
CONTRACT_ID = "ATOMICROWS_BUNDLE_BOUNDARY_STATE_CONTRACT"
CONTRACT_VERSION = "v1"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_BUNDLE_STATE_BOUNDARY_ONLY_NOT_BUNDLE_MATERIALIZATION_"
    "NOT_SHA_FREEZE_NOT_FINAL_READINESS"
)
VALIDATION_STATUS = "PASS"
REPORT_ID = "ATOMICROWS_BUNDLE_BOUNDARY_STATE_CONTRACT_REPORT"
VALIDATOR_NAME = "validate_atomicrows_bundle_boundary_state_contract.py"

FORBIDDEN_AUTHORITY_CLAIMS = [
    "SHA/freeze authority",
    "final readiness",
    "runtime/live/order/source/connector/runtime-cash/profit authority",
    "replay/paper execution",
    "optimizer execution",
    "quantum backend/simulator/provider execution",
    "computed scores/ranks/selections",
    "selected stack",
    "selected order intent",
    "profit/latency/execution/quantum-advantage evidence",
]

FUTURE_HANDOFF = {
    "current_pr_state_transition_allowed": True,
    "state_transition_executed_by_this_pr": True,
    "transition_from_state": AtomicRowsBundleState.PRE_MATERIALIZATION.value,
    "transition_to_state": AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA.value,
    "next_allowed_transition": "POST_MATERIALIZATION_PRE_SHA_TO_POST_SHA_FREEZE",
    "future_bundle_materialization_handoff_state": (
        "BUNDLE_MATERIALIZED_BY_PR113_NOT_SHA_NOT_FREEZE"
    ),
    "future_sha_freeze_handoff_state": "SHA_FREEZE_REQUIRED_FUTURE_ONLY_NOT_EXECUTED",
    "future_final_readiness_handoff_state": (
        "FINAL_READINESS_REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    ),
    "future_sha_freeze_state_centralization_required": (
        "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    ),
    "future_final_readiness_state_centralization_required": (
        "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    ),
    "future_runtime_live_state_centralization_required": (
        "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    ),
    "future_profit_evidence_state_centralization_required": (
        "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    ),
    "future_quantum_execution_state_centralization_required": (
        "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    ),
}

UNAUTHORIZED_AUTHORITY_PATHS = {
    "sha_freeze_authority_created": [
        pathlib.PurePosixPath("docs/master_plan/atomic_rows/AtomicRowsBundleFreezeAuthority.yaml"),
        pathlib.PurePosixPath("docs/master_plan/atomicrows/AtomicRowsBundleFreezeAuthority.yaml"),
    ],
    "final_readiness_created": [
        pathlib.PurePosixPath(
            "docs/master_plan/generated/AtomicRowsFullBundleFinalReadinessGate.report.json"
        ),
        pathlib.PurePosixPath(
            "docs/master_plan/atomicrows/AtomicRowsFullBundleFinalReadinessGate.yaml"
        ),
    ],
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(repo_root: pathlib.Path, path: pathlib.Path | pathlib.PurePosixPath) -> pathlib.Path:
    concrete = pathlib.Path(*path.parts) if isinstance(path, pathlib.PurePosixPath) else path
    return concrete if concrete.is_absolute() else repo_root / concrete


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    value = load_yaml_subset(path)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8", newline="\n")


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _state_definition_dict(state: AtomicRowsBundleState) -> dict[str, bool]:
    definition = ATOMICROWS_BUNDLE_STATE_DEFINITIONS[state]
    return {
        "bundle_jsonl_required": definition.bundle_jsonl_required,
        "bundle_jsonl_allowed": definition.bundle_jsonl_allowed,
        "bundle_sha_required": definition.bundle_sha_required,
        "bundle_sha_allowed": definition.bundle_sha_allowed,
        "sha_freeze_authority_allowed": definition.sha_freeze_authority_allowed,
        "final_readiness_allowed": definition.final_readiness_allowed,
    }


def _expected_state_definitions() -> dict[str, dict[str, bool]]:
    return {
        state.value: _state_definition_dict(state)
        for state in AtomicRowsBundleState
    }


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    return [
        f"CONTRACT {failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def validate_contract_payload(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(contract, schema)
    expected_top = {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "current_expected_state": AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA.value,
        "allowed_states": [state.value for state in AtomicRowsBundleState],
        "state_definitions": _expected_state_definitions(),
        "canonical_paths": {
            "bundle_jsonl": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
            "bundle_sha256": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        },
        "forbidden_current_artifacts": [
            CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        ],
        "forbidden_authority_claims": FORBIDDEN_AUTHORITY_CLAIMS,
        "future_handoff": FUTURE_HANDOFF,
        "generated_report_path": DEFAULT_REPORT.as_posix(),
    }
    for field, expected in expected_top.items():
        if contract.get(field) != expected:
            failures.append(f"contract.{field} must be {expected!r}")

    validator_contract = _mapping(contract.get("validator_contract"))
    expected_validator_contract = {
        "validator_name": VALIDATOR_NAME,
        "success_marker": SUCCESS_MARKER,
        "expected_current_state": AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA.value,
        "fail_closed_on_missing_bundle_jsonl": True,
        "fail_closed_on_unexpected_bundle_sha256": True,
        "creates_bundle_jsonl": False,
        "creates_bundle_sha256": False,
        "creates_sha_freeze_authority": False,
        "creates_final_readiness": False,
        "creates_runtime_live_order_source_connector_cash_backend_profit_quantum_authority": False,
    }
    if validator_contract != expected_validator_contract:
        failures.append("contract.validator_contract must match the PR112A static validator boundary")

    transition_rules = _list_of_mappings(contract.get("transition_rules"))
    expected_transitions = [
        ("PRE_MATERIALIZATION", "POST_MATERIALIZATION_PRE_SHA"),
        ("POST_MATERIALIZATION_PRE_SHA", "POST_SHA_FREEZE"),
        ("POST_SHA_FREEZE", "FINAL_READINESS"),
    ]
    observed_transitions = [
        (rule.get("from_state"), rule.get("to_state")) for rule in transition_rules
    ]
    if observed_transitions != expected_transitions:
        failures.append("contract.transition_rules must preserve canonical transition order")
    for index, rule in enumerate(transition_rules):
        requires = rule.get("requires")
        must_not_create = rule.get("must_not_create")
        if not isinstance(requires, list) or not requires:
            failures.append(f"contract.transition_rules[{index}].requires must not be empty")
        if not isinstance(must_not_create, list) or not must_not_create:
            failures.append(
                f"contract.transition_rules[{index}].must_not_create must not be empty"
            )
    return failures


def git_diff_check(repo_root: pathlib.Path, pathspec: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", pathspec],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    changed = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]
    return {
        "pathspec": pathspec,
        "unchanged": completed.returncode == 0 and not changed,
        "changed_paths": changed,
        "git_returncode": completed.returncode,
    }


def unauthorized_artifact_flags(repo_root: pathlib.Path) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for field, paths in UNAUTHORIZED_AUTHORITY_PATHS.items():
        flags[field] = any(_resolve(repo_root, path).exists() for path in paths)
    return flags


def build_report(
    *,
    repo_root: pathlib.Path,
    contract: dict[str, Any],
    validation_errors: list[str],
) -> dict[str, Any]:
    state = expected_atomicrows_bundle_state_from_contract(repo_root)
    state_report = atomicrows_bundle_state_report(repo_root, state)
    artifact_flags = unauthorized_artifact_flags(repo_root)
    bundle_path = _resolve(repo_root, CANONICAL_ATOMICROWS_BUNDLE)
    sha_path = _resolve(repo_root, CANONICAL_ATOMICROWS_BUNDLE_SHA)
    master_plan_diff = git_diff_check(
        repo_root, "docs/master_plan/QTT_MasterPlan_Current.md"
    )
    exact_row_source_diff = git_diff_check(
        repo_root, "docs/master_plan/atomic_rows/exact_row_sources"
    )
    forbidden_artifact_checks = {
        CANONICAL_ATOMICROWS_BUNDLE.as_posix(): {
            "exists": bundle_path.exists(),
            "expected_exists": True,
            "valid": bundle_path.exists(),
        },
        CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(): {
            "exists": sha_path.exists(),
            "expected_exists": False,
            "valid": not sha_path.exists(),
        },
    }
    result_ok = not validation_errors
    return {
        "report_id": REPORT_ID,
        "contract_id": CONTRACT_ID,
        "validator_name": VALIDATOR_NAME,
        "validation_status": VALIDATION_STATUS if result_ok else "FAIL",
        "current_expected_state": state.value,
        "bundle_jsonl_path": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
        "bundle_sha256_path": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        "bundle_jsonl_exists": bundle_path.exists(),
        "bundle_sha256_exists": sha_path.exists(),
        "expected_bundle_jsonl_exists": state_report["expected_bundle_jsonl_exists"],
        "expected_bundle_sha256_exists": state_report["expected_bundle_sha256_exists"],
        "bundle_state_valid": state_report["bundle_state_valid"],
        "sha_state_valid": state_report["sha_state_valid"],
        "sha_freeze_authority_created": artifact_flags["sha_freeze_authority_created"],
        "final_readiness_created": artifact_flags["final_readiness_created"],
        "runtime_live_authority_created": False,
        "source_connector_authority_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_authority_created": False,
        "state_transition_allowed_in_this_pr": True,
        "state_transition_executed_by_this_pr": True,
        "transition_from_state": AtomicRowsBundleState.PRE_MATERIALIZATION.value,
        "transition_to_state": AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA.value,
        "next_allowed_transition": _mapping(contract.get("future_handoff")).get(
            "next_allowed_transition"
        ),
        "future_bundle_materialization_handoff_state": _mapping(
            contract.get("future_handoff")
        ).get("future_bundle_materialization_handoff_state"),
        "future_sha_freeze_handoff_state": _mapping(contract.get("future_handoff")).get(
            "future_sha_freeze_handoff_state"
        ),
        "future_final_readiness_handoff_state": _mapping(
            contract.get("future_handoff")
        ).get("future_final_readiness_handoff_state"),
        "future_sha_freeze_state_centralization_required": _mapping(
            contract.get("future_handoff")
        ).get("future_sha_freeze_state_centralization_required"),
        "future_final_readiness_state_centralization_required": _mapping(
            contract.get("future_handoff")
        ).get("future_final_readiness_state_centralization_required"),
        "future_runtime_live_state_centralization_required": _mapping(
            contract.get("future_handoff")
        ).get("future_runtime_live_state_centralization_required"),
        "future_profit_evidence_state_centralization_required": _mapping(
            contract.get("future_handoff")
        ).get("future_profit_evidence_state_centralization_required"),
        "future_quantum_execution_state_centralization_required": _mapping(
            contract.get("future_handoff")
        ).get("future_quantum_execution_state_centralization_required"),
        "forbidden_artifact_checks": forbidden_artifact_checks,
        "master_plan_diff_check": master_plan_diff,
        "exact_row_source_diff_check": exact_row_source_diff,
        "validation_errors": validation_errors,
        "validation_warnings": [],
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "validation_status": VALIDATION_STATUS,
        "current_expected_state": AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA.value,
        "bundle_jsonl_exists": True,
        "bundle_sha256_exists": False,
        "expected_bundle_jsonl_exists": True,
        "expected_bundle_sha256_exists": False,
        "bundle_state_valid": True,
        "sha_state_valid": True,
        "sha_freeze_authority_created": False,
        "final_readiness_created": False,
        "runtime_live_authority_created": False,
        "source_connector_authority_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_authority_created": False,
        "state_transition_allowed_in_this_pr": True,
        "state_transition_executed_by_this_pr": True,
        "transition_from_state": AtomicRowsBundleState.PRE_MATERIALIZATION.value,
        "transition_to_state": AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA.value,
        "future_bundle_materialization_handoff_state": (
            "BUNDLE_MATERIALIZED_BY_PR113_NOT_SHA_NOT_FREEZE"
        ),
        "future_sha_freeze_handoff_state": "SHA_FREEZE_REQUIRED_FUTURE_ONLY_NOT_EXECUTED",
        "future_final_readiness_handoff_state": (
            "FINAL_READINESS_REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
        ),
        "future_sha_freeze_state_centralization_required": (
            "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
        ),
        "future_final_readiness_state_centralization_required": (
            "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
        ),
        "future_runtime_live_state_centralization_required": (
            "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
        ),
        "future_profit_evidence_state_centralization_required": (
            "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
        ),
        "future_quantum_execution_state_centralization_required": (
            "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
        ),
        "result_marker": SUCCESS_MARKER,
    }
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            failures.append(f"report.{field} must be {expected_value!r}")
    if report.get("validation_errors") != []:
        failures.append("report.validation_errors must be empty")
    for path, check in _mapping(report.get("forbidden_artifact_checks")).items():
        if _mapping(check).get("valid") is not True:
            failures.append(f"report.forbidden_artifact_checks.{path}.valid must be true")
    for field in ("master_plan_diff_check", "exact_row_source_diff_check"):
        if _mapping(report.get(field)).get("unchanged") is not True:
            failures.append(f"report.{field}.unchanged must be true")
    if report != json.loads(serialize_report(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    contract_path: pathlib.Path = DEFAULT_CONTRACT,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    report_out: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        contract = load_yaml(_resolve(repo_root, contract_path))
        schema = load_json(_resolve(repo_root, schema_path))
    except Exception as exc:
        return ValidationResult(False, (f"could not load bundle boundary input: {exc}",), None)

    failures.extend(validate_contract_payload(contract, schema))
    failures.extend(
        validate_current_atomicrows_bundle_state(
            repo_root,
            label="AtomicRowsBundleBoundaryStateContract",
        )
    )
    for field, created in unauthorized_artifact_flags(repo_root).items():
        if created:
            failures.append(f"unauthorized authority artifact created: {field}")
    master_plan_diff = git_diff_check(repo_root, "docs/master_plan/QTT_MasterPlan_Current.md")
    if master_plan_diff["unchanged"] is not True:
        failures.append("docs/master_plan/QTT_MasterPlan_Current.md must remain unchanged")
    exact_diff = git_diff_check(repo_root, "docs/master_plan/atomic_rows/exact_row_sources")
    if exact_diff["unchanged"] is not True:
        failures.append("docs/master_plan/atomic_rows/exact_row_sources must remain unchanged")

    report = build_report(
        repo_root=repo_root,
        contract=contract,
        validation_errors=[] if not failures else failures,
    )
    if failures:
        return ValidationResult(False, tuple(failures), report)

    report_failures = validate_report(report)
    if report_failures:
        return ValidationResult(False, tuple(report_failures), report)

    write_json_report(report, _resolve(repo_root, report_out))
    return ValidationResult(True, tuple(), report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--contract", type=pathlib.Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--report-out", type=pathlib.Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        contract_path=args.contract,
        schema_path=args.schema,
        report_out=args.report_out,
    )
    if not result.ok:
        for failure in result.failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
