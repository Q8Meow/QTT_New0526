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
from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as gate_registry
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as policy
from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.validate_master_plan_section_coverage import validate_json_schema_subset


REPO_ROOT = _REPO_ROOT
DEFAULT_CONTRACT = pathlib.Path(
    "docs/master_plan/launch/QttFinalReadinessDependencyPolicyContract.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/launch/qtt_final_readiness_dependency_policy_contract.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/QttFinalReadinessDependencyPolicy.report.json"
)

SUCCESS_MARKER = "QTT_FINAL_READINESS_DEPENDENCY_POLICY_OK"
FAILURE_MARKER = "QTT_FINAL_READINESS_DEPENDENCY_POLICY_FAILED"
CONTRACT_ID = "QTT_FINAL_READINESS_DEPENDENCY_POLICY_CONTRACT"
CONTRACT_VERSION = "v1"
AUTHORITY_CLASS = (
    "DAY1_FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY_NOT_FINAL_READINESS"
)
CURRENT_STATE = "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY"
REPORT_ID = "QTT_FINAL_READINESS_DEPENDENCY_POLICY_REPORT"
VALIDATION_STATUS = "PASS"
VALIDATOR_NAME = "validate_qtt_final_readiness_dependency_policy_contract.py"

SHA_DEPENDENCY_TOKENS = (
    "SHA",
    "SHA_FREEZE",
    "SHA_FILE",
    "SHA_DIGEST",
    "SHA_ABSENCE",
    "SHA_PRESENCE",
    "SHA_REACTIVATION",
)

FORBIDDEN_FALSE_FIELDS = (
    "sha_required_for_final_readiness",
    "sha_dormancy_is_final_readiness_blocker",
    "sha_absence_is_final_readiness_blocker",
    "sha_presence_is_final_readiness_evidence",
    "sha_reactivation_required_for_day1_launch",
    "current_pr_creates_final_readiness",
    "current_pr_creates_day1_launch_authority",
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
    "active_gate_state_registry_required",
    "active_gate_state_registry_is_source_of_day1_gate_state",
    "final_readiness_dependency_policy_does_not_hardcode_gate_states_independently",
    "final_readiness_dependency_policy_consumes_or_validates_registry_gate_ids",
    "active_non_sha_final_readiness_dependencies_required",
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


def _contains_sha_dependency(value: str) -> bool:
    return any(token in value for token in SHA_DEPENDENCY_TOKENS)


def validate_contract_payload(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(contract, schema)
    expected = {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "current_final_readiness_dependency_policy_state": CURRENT_STATE,
        "allowed_final_readiness_dependency_policy_states": list(
            policy.QTT_FINAL_READINESS_DEPENDENCY_POLICY_STATES
        ),
        "active_non_sha_final_readiness_dependencies": list(
            policy.ACTIVE_NON_SHA_FINAL_READINESS_DEPENDENCIES
        ),
        "active_gate_state_registry_contract_path": (
            "docs/master_plan/launch/QttActiveNonShaDay1GateStateRegistryContract.yaml"
        ),
        "excluded_non_participating_subsystems": list(
            policy.EXCLUDED_NON_PARTICIPATING_FINAL_READINESS_SUBSYSTEMS
        ),
    }
    for field, expected_value in expected.items():
        if contract.get(field) != expected_value:
            failures.append(f"contract.{field} must be {expected_value!r}")
    for field in FORBIDDEN_FALSE_FIELDS:
        if contract.get(field) is not False:
            failures.append(f"contract.{field} must be false")
    if (
        contract.get(
            "final_readiness_may_be_authorized_without_sha_if_all_active_non_sha_gates_pass_and_owner_approves"
        )
        is not True
    ):
        failures.append("contract final-readiness-without-SHA policy must be true")
    for field in REQUIRED_TRUE_FIELDS:
        if contract.get(field) is not True:
            failures.append(f"contract.{field} must be true")
    if (
        tuple(contract.get("active_non_sha_final_readiness_dependencies", []))
        != gate_registry.get_active_non_sha_day1_gate_ids()
    ):
        failures.append(
            "contract.active_non_sha_final_readiness_dependencies must match the central active gate registry"
        )
    for dependency in contract.get("active_non_sha_final_readiness_dependencies", []):
        if not isinstance(dependency, str) or _contains_sha_dependency(dependency):
            failures.append(f"active dependency must be non-SHA only: {dependency!r}")

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
        failures.append(
            "contract.validator_contract must match the final-readiness policy validator boundary"
        )
    return failures


def build_report(
    *,
    contract: dict[str, Any],
    validation_errors: list[str],
) -> dict[str, Any]:
    result_ok = not validation_errors
    dependencies = list(policy.get_active_non_sha_final_readiness_dependencies())
    return {
        "report_id": REPORT_ID,
        "contract_id": CONTRACT_ID,
        "validator_name": VALIDATOR_NAME,
        "validation_status": VALIDATION_STATUS if result_ok else "FAIL",
        "current_final_readiness_dependency_policy_state": (
            policy.get_qtt_final_readiness_dependency_policy_state()
        ),
        "sha_system_dormant": sha_state.is_sha_system_dormant(),
        "sha_system_non_participating_for_final_readiness": (
            sha_state.is_sha_system_non_participating_for_final_readiness()
        ),
        "sha_required_for_final_readiness": policy.is_sha_required_for_final_readiness(),
        "sha_dormancy_is_final_readiness_blocker": (
            policy.is_sha_dormancy_a_final_readiness_blocker()
        ),
        "sha_absence_is_final_readiness_blocker": contract.get(
            "sha_absence_is_final_readiness_blocker"
        ),
        "sha_presence_is_final_readiness_evidence": contract.get(
            "sha_presence_is_final_readiness_evidence"
        ),
        "sha_reactivation_required_for_day1_launch": contract.get(
            "sha_reactivation_required_for_day1_launch"
        ),
        "final_readiness_may_be_authorized_without_sha_if_all_active_non_sha_gates_pass_and_owner_approves": contract.get(
            "final_readiness_may_be_authorized_without_sha_if_all_active_non_sha_gates_pass_and_owner_approves"
        ),
        "current_pr_creates_final_readiness": contract.get(
            "current_pr_creates_final_readiness"
        ),
        "current_pr_creates_day1_launch_authority": contract.get(
            "current_pr_creates_day1_launch_authority"
        ),
        "active_non_sha_final_readiness_dependencies": dependencies,
        "active_gate_state_registry_contract_path": contract.get(
            "active_gate_state_registry_contract_path"
        ),
        "active_gate_state_registry_required": contract.get(
            "active_gate_state_registry_required"
        ),
        "active_gate_state_registry_is_source_of_day1_gate_state": contract.get(
            "active_gate_state_registry_is_source_of_day1_gate_state"
        ),
        "final_readiness_dependency_policy_does_not_hardcode_gate_states_independently": contract.get(
            "final_readiness_dependency_policy_does_not_hardcode_gate_states_independently"
        ),
        "final_readiness_dependency_policy_consumes_or_validates_registry_gate_ids": contract.get(
            "final_readiness_dependency_policy_consumes_or_validates_registry_gate_ids"
        ),
        "active_non_sha_final_readiness_dependencies_required": contract.get(
            "active_non_sha_final_readiness_dependencies_required"
        ),
        "active_gate_ids_match_gate_state_registry": (
            tuple(dependencies) == gate_registry.get_active_non_sha_day1_gate_ids()
        ),
        "active_non_sha_final_readiness_dependencies_include_sha": any(
            _contains_sha_dependency(item) for item in dependencies
        ),
        "excluded_non_participating_subsystems": list(
            policy.get_excluded_non_participating_final_readiness_subsystems()
        ),
        "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created": False,
        "replay_paper_optimizer_neural_quantum_backend_execution_created": False,
        "profit_latency_execution_quantum_advantage_evidence_claimed": False,
        "validation_errors": validation_errors,
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }


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
        return ValidationResult(
            False,
            (f"could not load final-readiness dependency input: {exc}",),
            None,
        )

    failures.extend(validate_contract_payload(contract, schema))
    if policy.get_qtt_final_readiness_dependency_policy_state() != CURRENT_STATE:
        failures.append(f"central final-readiness dependency state must be {CURRENT_STATE}")
    if policy.is_sha_required_for_final_readiness():
        failures.append("SHA must not be required for final readiness")
    if policy.is_sha_dormancy_a_final_readiness_blocker():
        failures.append("SHA dormancy must not be a final-readiness blocker")
    if not sha_state.is_sha_system_non_participating_for_final_readiness():
        failures.append("SHA system must be non-participating for final readiness")
    if "SHA_DORMANCY_SYSTEM" not in policy.get_excluded_non_participating_final_readiness_subsystems():
        failures.append("excluded non-participating subsystems must include SHA_DORMANCY_SYSTEM")
    if any(
        _contains_sha_dependency(item)
        for item in policy.get_active_non_sha_final_readiness_dependencies()
    ):
        failures.append("active non-SHA dependencies must not include SHA-related dependencies")
    if (
        policy.get_active_non_sha_final_readiness_dependencies()
        != gate_registry.get_active_non_sha_day1_gate_ids()
    ):
        failures.append("active non-SHA dependencies must match central gate registry IDs")

    for assertion in (
        policy.assert_final_readiness_policy_active_non_sha_gates_only,
        policy.assert_sha_not_required_for_final_readiness,
        policy.assert_sha_dormancy_not_final_readiness_blocker,
        policy.assert_sha_absence_not_final_readiness_blocker,
        policy.assert_sha_presence_not_final_readiness_evidence,
        policy.assert_active_dependencies_consume_gate_registry,
        policy.assert_day1_final_readiness_must_ignore_sha_dormancy_when_non_sha_gates_pass,
        policy.assert_current_pr_does_not_create_final_readiness,
    ):
        try:
            assertion()
        except AssertionError as exc:
            failures.append(str(exc))

    report = build_report(
        contract=contract,
        validation_errors=[] if not failures else failures,
    )
    if failures:
        return ValidationResult(False, tuple(failures), report)
    if report != json.loads(serialize_report(report)):
        return ValidationResult(False, ("report serialization must be deterministic",), report)
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
