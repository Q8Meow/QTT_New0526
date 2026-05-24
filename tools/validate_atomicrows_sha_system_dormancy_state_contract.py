#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing import atomicrows_sha_system_dormancy_state as sha_state
from src.qtt.core.testing.atomicrows_sha_freeze_final_readiness_state import (
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
)
from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.validate_master_plan_section_coverage import validate_json_schema_subset


REPO_ROOT = _REPO_ROOT
DEFAULT_CONTRACT = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsShaSystemDormancyStateContract.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_sha_system_dormancy_state_contract.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/AtomicRowsShaSystemDormancyStateContract.report.json"
)

SUCCESS_MARKER = "QTT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE_CONTRACT_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE_CONTRACT_FAILED"
CONTRACT_ID = "ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE_CONTRACT"
CONTRACT_VERSION = "v1"
AUTHORITY_CLASS = (
    "OWNER_GLOBAL_SHA_DORMANCY_POLICY_NOT_FINAL_READINESS_NOT_RUNTIME_NOT_LIVE"
)
CURRENT_STATE = "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED"
REPORT_ID = "ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE_CONTRACT_REPORT"
VALIDATION_STATUS = "PASS"
VALIDATOR_NAME = "validate_atomicrows_sha_system_dormancy_state_contract.py"

FORBIDDEN_FALSE_FIELDS = (
    "sha_generation_allowed",
    "sha_freeze_authority_allowed",
    "sha_reactivation_performed_in_this_pr",
    "atomicrows_bundle_sha256_created_by_this_pr",
    "current_pr_creates_runtime_live_order_source_connector_runtime_cash_backend_profit_authority",
    "current_pr_creates_replay_paper_optimizer_neural_quantum_backend_execution",
    "current_pr_claims_profit_latency_execution_quantum_advantage_evidence",
    "source_facts_accepted_by_this_pr",
    "connector_semantics_bound_by_this_pr",
    "runtime_cash_receipts_created_by_this_pr",
    "live_trading_authority_created_by_this_pr",
    "bug_free_status_claimed_by_this_pr",
)

REQUIRED_TRUE_FIELDS = (
    "sha_reactivation_requires_future_owner_approved_pr",
    "sha_reactivation_is_not_required_for_day1_final_readiness",
    "sha_system_non_participating_for_final_readiness",
    "sha_dormancy_is_not_final_readiness",
    "sha_dormancy_is_not_final_readiness_blocker",
    "sha_dormancy_does_not_create_runtime_live_profit_or_quantum_backend_authority",
    "sha_dormancy_does_not_block_research_candidate_intake",
    "sha_dormancy_does_not_block_future_parameter_additions",
    "sha_dormancy_does_not_block_future_algorithm_additions",
    "sha_dormancy_does_not_block_future_quantum_metadata_additions",
    "sha_dormancy_does_not_block_qubo_qaoa_vqe_ising_annealing_metadata_additions",
    "atomicrows_bundle_required_present",
    "atomicrows_bundle_sha256_absence_is_not_final_readiness_blocker",
    "atomicrows_bundle_sha256_presence_is_not_final_readiness_evidence",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(repo_root: pathlib.Path, path: pathlib.Path | pathlib.PurePosixPath) -> pathlib.Path:
    concrete = pathlib.Path(*path.parts) if isinstance(path, pathlib.PurePosixPath) else path
    return concrete if concrete.is_absolute() else repo_root / concrete


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    return [
        f"CONTRACT {failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def _line_count(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    data = path.read_bytes()
    return len(data.decode("utf-8").splitlines())


def validate_contract_payload(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(contract, schema)
    expected = {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "current_sha_system_dormancy_state": CURRENT_STATE,
        "allowed_sha_system_dormancy_states": list(
            sha_state.ATOMICROWS_SHA_SYSTEM_DORMANCY_STATES
        ),
        "atomicrows_bundle_path": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
        "atomicrows_bundle_sha256_path": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        "atomicrows_bundle_expected_line_count": EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
    }
    for field, expected_value in expected.items():
        if contract.get(field) != expected_value:
            failures.append(f"contract.{field} must be {expected_value!r}")
    for field in FORBIDDEN_FALSE_FIELDS:
        if contract.get(field) is not False:
            failures.append(f"contract.{field} must be false")
    for field in REQUIRED_TRUE_FIELDS:
        if contract.get(field) is not True:
            failures.append(f"contract.{field} must be true")

    validator_contract = _mapping(contract.get("validator_contract"))
    expected_validator = {
        "validator_name": VALIDATOR_NAME,
        "success_marker": SUCCESS_MARKER,
        "schema_path": DEFAULT_SCHEMA.as_posix(),
        "generated_report_path": DEFAULT_REPORT.as_posix(),
        "creates_sha": False,
        "creates_sha_freeze_authority": False,
        "creates_final_readiness": False,
        "creates_day1_launch_authority": False,
        "creates_runtime_live_order_source_connector_cash_backend_profit_quantum_authority": False,
    }
    if validator_contract != expected_validator:
        failures.append("contract.validator_contract must match the SHA dormancy validator boundary")
    return failures


def build_report(
    *,
    repo_root: pathlib.Path,
    contract: dict[str, Any],
    validation_errors: list[str],
) -> dict[str, Any]:
    bundle_path = _resolve(repo_root, CANONICAL_ATOMICROWS_BUNDLE)
    sha_path = _resolve(repo_root, CANONICAL_ATOMICROWS_BUNDLE_SHA)
    result_ok = not validation_errors
    return {
        "report_id": REPORT_ID,
        "contract_id": CONTRACT_ID,
        "validator_name": VALIDATOR_NAME,
        "validation_status": VALIDATION_STATUS if result_ok else "FAIL",
        "current_sha_system_dormancy_state": sha_state.get_atomicrows_sha_system_dormancy_state(),
        "sha_system_dormant": sha_state.is_sha_system_dormant(),
        "sha_system_non_participating_for_final_readiness": (
            sha_state.is_sha_system_non_participating_for_final_readiness()
        ),
        "sha_generation_allowed": sha_state.is_sha_generation_allowed(),
        "sha_freeze_authority_allowed": sha_state.is_sha_freeze_authority_allowed(),
        "sha_reactivation_performed_in_this_pr": contract.get(
            "sha_reactivation_performed_in_this_pr"
        ),
        "sha_reactivation_requires_future_owner_approved_pr": contract.get(
            "sha_reactivation_requires_future_owner_approved_pr"
        ),
        "sha_reactivation_is_not_required_for_day1_final_readiness": contract.get(
            "sha_reactivation_is_not_required_for_day1_final_readiness"
        ),
        "sha_dormancy_is_not_final_readiness": contract.get(
            "sha_dormancy_is_not_final_readiness"
        ),
        "sha_dormancy_is_not_final_readiness_blocker": contract.get(
            "sha_dormancy_is_not_final_readiness_blocker"
        ),
        "atomicrows_bundle_path": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
        "atomicrows_bundle_exists": bundle_path.exists(),
        "atomicrows_bundle_line_count": _line_count(bundle_path),
        "atomicrows_bundle_expected_line_count": EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
        "atomicrows_bundle_sha256_path": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        "atomicrows_bundle_sha256_exists": sha_path.exists(),
        "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created": False,
        "replay_paper_optimizer_neural_quantum_backend_execution_created": False,
        "profit_latency_execution_quantum_advantage_evidence_claimed": False,
        "research_candidate_intake_blocked_by_sha_dormancy": False,
        "future_parameter_additions_blocked_by_sha_dormancy": False,
        "future_algorithm_additions_blocked_by_sha_dormancy": False,
        "future_quantum_metadata_additions_blocked_by_sha_dormancy": False,
        "validation_errors": validation_errors,
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    contract_path: pathlib.Path = DEFAULT_CONTRACT,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    report_out: pathlib.Path = DEFAULT_REPORT,
    write_report: bool = False,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        contract = load_yaml(_resolve(repo_root, contract_path))
        schema = load_json(_resolve(repo_root, schema_path))
    except Exception as exc:
        return ValidationResult(False, (f"could not load SHA dormancy input: {exc}",), None)

    failures.extend(validate_contract_payload(contract, schema))
    if sha_state.get_atomicrows_sha_system_dormancy_state() != CURRENT_STATE:
        failures.append(f"central SHA dormancy state must be {CURRENT_STATE}")
    if not sha_state.is_sha_system_dormant():
        failures.append("central SHA system must be dormant")
    if not sha_state.is_sha_system_non_participating_for_final_readiness():
        failures.append("central SHA system must be non-participating for final readiness")
    if sha_state.is_sha_generation_allowed():
        failures.append("central SHA generation must be disabled")
    if sha_state.is_sha_freeze_authority_allowed():
        failures.append("central SHA/freeze authority must be disabled")

    for assertion in (
        sha_state.assert_sha_system_dormant_non_participating,
        sha_state.assert_sha_generation_disabled,
        sha_state.assert_sha_freeze_authority_disabled,
        sha_state.assert_sha_dormancy_does_not_create_final_readiness,
        sha_state.assert_sha_dormancy_does_not_block_final_readiness,
        sha_state.assert_sha_reactivation_not_performed,
        sha_state.assert_sha_reactivation_requires_future_owner_approved_pr,
    ):
        try:
            assertion()
        except AssertionError as exc:
            failures.append(str(exc))

    bundle_path = _resolve(repo_root, CANONICAL_ATOMICROWS_BUNDLE)
    sha_path = _resolve(repo_root, CANONICAL_ATOMICROWS_BUNDLE_SHA)
    if not bundle_path.exists():
        failures.append("AtomicRows.bundle.jsonl must exist")
    if _line_count(bundle_path) != EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT:
        failures.append("AtomicRows.bundle.jsonl must have exactly 4,183 rows")
    if sha_path.exists():
        failures.append("AtomicRows.bundle.sha256 must remain absent")

    for field in FORBIDDEN_FALSE_FIELDS:
        if contract.get(field) is not False:
            failures.append(f"forbidden authority or claim flag must be false: {field}")

    report = build_report(
        repo_root=repo_root,
        contract=contract,
        validation_errors=[] if not failures else failures,
    )
    if failures:
        return ValidationResult(False, tuple(failures), report)
    if report != json.loads(serialize_report(report)):
        return ValidationResult(False, ("report serialization must be deterministic",), report)
    report_path = _resolve(repo_root, report_out)
    if write_report or report_path != _resolve(repo_root, DEFAULT_REPORT):
        write_json_report(report, report_path)
    return ValidationResult(True, tuple(), report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--contract", type=pathlib.Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--report-out", type=pathlib.Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        contract_path=args.contract,
        schema_path=args.schema,
        report_out=args.report_out,
        write_report=args.write_report,
    )
    if not result.ok:
        for failure in result.failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
