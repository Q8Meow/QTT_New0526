#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import pathlib
import subprocess
import sys
import tempfile
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    AtomicRowsBundleState,
    expected_atomicrows_bundle_state_from_contract,
)
from src.qtt.core.testing import atomicrows_sha_system_dormancy_state as sha_dormancy  # noqa: E402
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as readiness_policy  # noqa: E402
from src.qtt.core.testing.atomicrows_sha_freeze_final_readiness_state import (  # noqa: E402
    ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS,
    BUILTIN_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_AUTHORITY_PATHS,
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
    AtomicRowsShaFreezeFinalReadinessState,
    atomicrows_sha_freeze_final_readiness_state_report,
    canonical_atomicrows_sha_freeze_presence,
    expected_atomicrows_sha_freeze_final_readiness_state_from_contract,
    validate_current_atomicrows_sha_freeze_final_readiness_state,
)
from tools import validate_atomicrows_bundle_boundary_state_contract as boundary_gate  # noqa: E402
from tools import validate_atomicrows_bundle_materialization_manifest as materialization_gate  # noqa: E402
from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as sha_freeze_gate  # noqa: E402
from tools import validate_no_runtime_artifacts  # noqa: E402
from tools.build_master_plan_section_coverage_report import load_yaml_subset  # noqa: E402
from tools.validate_master_plan_section_coverage import validate_json_schema_subset  # noqa: E402


REPO_ROOT = _REPO_ROOT
DEFAULT_CONTRACT = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsShaFreezeFinalReadinessStateContract.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_sha_freeze_final_readiness_state_contract.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/AtomicRowsShaFreezeFinalReadinessStateContract.report.json"
)

SUCCESS_MARKER = "QTT_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT_FAILED"
CONTRACT_ID = "ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT"
CONTRACT_VERSION = "v1"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_BOUNDARY_ONLY_NOT_SHA_"
    "CREATION_NOT_FREEZE_AUTHORITY_NOT_FINAL_READINESS_NOT_RUNTIME_NOT_LIVE"
)
VALIDATION_STATUS = "PASS"
REPORT_ID = "ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT_REPORT"
VALIDATOR_NAME = "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
CURRENT_EXPECTED_STATE = (
    AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE
)
NEXT_ALLOWED_TRANSITION = (
    "BUNDLE_MATERIALIZED_PRE_SHA_FREEZE_TO_"
    "FINAL_READINESS_AUTHORIZED_ACTIVE_NON_SHA_GATES_ONLY"
)
FUTURE_ONLY_HANDOFF = "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
SHA_REACTIVATION_HANDOFF = (
    "OPTIONAL_FUTURE_OWNER_APPROVED_SHA_REACTIVATION_ONLY_NOT_DAY1_REQUIRED_"
    "NOT_EXECUTED"
)
FINAL_READINESS_HANDOFF = (
    "FUTURE_FINAL_READINESS_ACTIVE_NON_SHA_GATES_ONLY_NOT_EXECUTED"
)

EXISTING_BLOCKED_STATIC_GATE_ARTIFACTS = [
    "docs/master_plan/atomicrows/AtomicRowsBundleShaFreezeAuthorityGate.yaml",
    "docs/master_plan/generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json",
    "tools/validate_atomicrows_bundle_sha_freeze_authority_gate.py",
    "tests/atomicrows/test_atomicrows_bundle_sha_freeze_authority_gate.py",
]

FORBIDDEN_CURRENT_AUTHORITY_CLAIMS = [
    "SHA/freeze authority",
    "final readiness",
    "runtime/live/order/source/connector/runtime-cash/backend/profit authority",
    "replay/paper execution",
    "optimizer execution",
    "quantum backend/simulator/provider execution",
    "computed scores/ranks/selections",
    "selected stack",
    "selected order intent",
    "profit/latency/execution/quantum-advantage evidence",
]

FUTURE_HANDOFF = {
    "future_sha_freeze_authority_pr_required": SHA_REACTIVATION_HANDOFF,
    "future_final_readiness_pr_required": FINAL_READINESS_HANDOFF,
    "future_runtime_live_state_centralization_required": FUTURE_ONLY_HANDOFF,
    "future_profit_evidence_state_centralization_required": FUTURE_ONLY_HANDOFF,
    "future_quantum_execution_state_centralization_required": FUTURE_ONLY_HANDOFF,
}

VALIDATOR_CONTRACT = {
    "validator_name": VALIDATOR_NAME,
    "success_marker": SUCCESS_MARKER,
    "expected_current_state": CURRENT_EXPECTED_STATE.value,
    "fail_closed_on_missing_bundle_jsonl": True,
    "fail_closed_on_invalid_bundle_jsonl": True,
    "fail_closed_on_unexpected_bundle_sha256": True,
    "fail_closed_on_future_sha_freeze_authority_artifact": True,
    "fail_closed_on_future_freeze_receipt": True,
    "fail_closed_on_future_final_readiness_artifact": True,
    "creates_bundle_sha256": False,
    "creates_sha_freeze_authority": False,
    "creates_freeze_receipt": False,
    "creates_final_readiness": False,
    "creates_runtime_live_order_source_connector_cash_backend_profit_quantum_authority": False,
}

TRANSITION_RULES = [
    {
        "from_state": "BUNDLE_MATERIALIZED_PRE_SHA_FREEZE",
        "to_state": "SHA_FREEZE_AUTHORIZED_PRE_FINAL_READINESS",
        "allowed_only_in": "EXPLICIT_FUTURE_OWNER_APPROVED_SHA_REACTIVATION_PR_ONLY",
        "requires": [
            "future owner-approved SHA reactivation PR",
            "existing valid AtomicRows.bundle.jsonl",
            "exactly 4,183 bundle rows",
            "central SHA dormancy policy changed away from dormant by owner approval",
            "deterministic SHA computation",
            "SHA value matches bundle bytes",
            "SHA/freeze receipt or authority artifact",
        ],
        "must_not_create": [
            "final readiness",
            "runtime/live/order/profit/quantum-backend authority",
        ],
    },
    {
        "from_state": "BUNDLE_MATERIALIZED_PRE_SHA_FREEZE",
        "to_state": "FINAL_READINESS_AUTHORIZED",
        "allowed_only_in": "EXPLICIT_FUTURE_FINAL_READINESS_PR_ACTIVE_NON_SHA_GATES_ONLY",
        "requires": [
            "existing valid bundle",
            "current final-readiness dependency policy active non-SHA gates only",
            "SHA not required for Day-1 final readiness",
            "SHA dormancy not a Day-1 final-readiness blocker",
            "owner Day-1 launch approval",
            "lifecycle gates",
            "agent binding gates",
            "selection gates",
            "scoring gates",
            "owner override gates",
            "command matrix gates",
            "other required gates",
        ],
        "must_not_create": [
            "live trading by itself",
        ],
    },
    {
        "from_state": "FINAL_READINESS_AUTHORIZED",
        "to_state": "RUNTIME_OR_LIVE_AUTHORITY",
        "allowed_only_in": "FUTURE_ONLY_SEPARATE_RUNTIME_LIVE_PR",
        "requires": [
            "separate runtime/live centralization",
            "owner approval",
        ],
        "must_not_create": [
            "runtime/live authority in PR114A",
        ],
    },
]


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


def _state_definition_dict(
    state: AtomicRowsShaFreezeFinalReadinessState,
) -> dict[str, Any]:
    return asdict(ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS[state])


def _expected_state_definitions() -> dict[str, dict[str, Any]]:
    return {
        state.value: _state_definition_dict(state)
        for state in AtomicRowsShaFreezeFinalReadinessState
    }


def _expected_artifact_authority_paths() -> list[dict[str, Any]]:
    return [
        {
            "path": str(item["path"]),
            "artifact_kind": str(item["artifact_kind"]),
            "future_only": True,
            "must_not_exist_in_current_state": True,
            "created_by_future_pr_only": True,
        }
        for item in BUILTIN_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_AUTHORITY_PATHS
    ]


def _expected_forbidden_current_artifacts() -> list[str]:
    return [item["path"] for item in _expected_artifact_authority_paths()]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    return [
        f"CONTRACT {failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def validate_contract_payload(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(contract, schema)
    expected = {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "current_expected_state": CURRENT_EXPECTED_STATE.value,
        "allowed_states": [
            state.value for state in AtomicRowsShaFreezeFinalReadinessState
        ],
        "state_definitions": _expected_state_definitions(),
        "canonical_paths": {
            "bundle_jsonl": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
            "bundle_sha256": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        },
        "artifact_authority_paths": _expected_artifact_authority_paths(),
        "transition_rules": TRANSITION_RULES,
        "forbidden_current_artifacts": _expected_forbidden_current_artifacts(),
        "forbidden_current_authority_claims": FORBIDDEN_CURRENT_AUTHORITY_CLAIMS,
        "existing_blocked_static_gate_artifacts": EXISTING_BLOCKED_STATIC_GATE_ARTIFACTS,
        "future_handoff": FUTURE_HANDOFF,
        "validator_contract": VALIDATOR_CONTRACT,
        "generated_report_path": DEFAULT_REPORT.as_posix(),
    }
    for field, expected_value in expected.items():
        if contract.get(field) != expected_value:
            failures.append(f"contract.{field} must be {expected_value!r}")

    current_definition = _mapping(
        _mapping(contract.get("state_definitions")).get(CURRENT_EXPECTED_STATE.value)
    )
    for field in (
        "bundle_sha256_required",
        "bundle_sha256_allowed",
        "sha_freeze_authority_required",
        "sha_freeze_authority_allowed",
        "freeze_receipt_required",
        "freeze_receipt_allowed",
        "final_readiness_required",
        "final_readiness_allowed",
        "live_trading_allowed",
        "runtime_live_authority_allowed",
        "order_authority_allowed",
        "source_connector_authority_allowed",
        "runtime_cash_authority_allowed",
        "backend_authority_allowed",
        "profit_evidence_allowed",
        "quantum_backend_authority_allowed",
        "replay_paper_execution_allowed",
        "optimizer_execution_allowed",
        "scoring_ranking_selection_execution_allowed",
    ):
        if current_definition.get(field) is not False:
            failures.append(f"contract current state {field} must be false")
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


def _temporary_report_path(temp_dir: pathlib.Path, name: str) -> pathlib.Path:
    return temp_dir / name


def validate_existing_gates(repo_root: pathlib.Path) -> tuple[list[str], dict[str, bool]]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="qtt_pr114a_state_") as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)
        sha_result = sha_freeze_gate.validate(
            repo_root=repo_root,
            output_path=_temporary_report_path(temp_dir, "sha_freeze_gate.report.json"),
        )
        materialization_result = materialization_gate.validate(
            repo_root=repo_root,
            report_out=_temporary_report_path(temp_dir, "materialization.report.json"),
        )
        boundary_result = boundary_gate.validate(
            repo_root=repo_root,
            report_out=_temporary_report_path(temp_dir, "boundary.report.json"),
        )

    sha_report = sha_result.report or {}
    existing_blocked_static_sha_freeze_gate_valid = (
        sha_result.ok
        and sha_report.get("gate_mode") == "BLOCKED"
        and sha_report.get("validation_result") == "PASS_BLOCKED_EXPECTED"
        and sha_report.get("validator_stdout_marker") == sha_freeze_gate.SUCCESS_MARKER
        and sha_report.get("freeze_authority_created") is False
        and sha_report.get("final_readiness_created") is False
    )
    existing_bundle_materialization_valid = materialization_result.ok
    existing_bundle_boundary_state_valid = (
        boundary_result.ok
        and expected_atomicrows_bundle_state_from_contract(repo_root)
        is AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA
    )

    if not existing_blocked_static_sha_freeze_gate_valid:
        failures.append("existing blocked static SHA/freeze gate must remain valid and blocked")
        failures.extend(str(item) for item in sha_result.failures)
    if not existing_bundle_materialization_valid:
        failures.append("existing bundle materialization validator must pass")
        failures.extend(str(item) for item in materialization_result.failures)
    if not existing_bundle_boundary_state_valid:
        failures.append("existing bundle boundary state validator must pass")
        failures.extend(str(item) for item in boundary_result.failures)

    return failures, {
        "existing_blocked_static_sha_freeze_gate_valid": existing_blocked_static_sha_freeze_gate_valid,
        "existing_bundle_materialization_valid": existing_bundle_materialization_valid,
        "existing_bundle_boundary_state_valid": existing_bundle_boundary_state_valid,
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    contract: dict[str, Any],
    existing_gate_flags: dict[str, bool],
    validation_errors: list[str],
) -> dict[str, Any]:
    state = expected_atomicrows_sha_freeze_final_readiness_state_from_contract(repo_root)
    state_report = atomicrows_sha_freeze_final_readiness_state_report(repo_root, state)
    presence = canonical_atomicrows_sha_freeze_presence(repo_root)
    master_plan_diff = git_diff_check(
        repo_root, "docs/master_plan/QTT_MasterPlan_Current.md"
    )
    exact_row_source_diff = git_diff_check(
        repo_root, "docs/master_plan/atomic_rows/exact_row_sources"
    )
    bundle_jsonl_diff = git_diff_check(
        repo_root, CANONICAL_ATOMICROWS_BUNDLE.as_posix()
    )
    no_runtime_scanner_diff = git_diff_check(
        repo_root, "tools/validate_no_runtime_artifacts.py"
    )
    result_ok = not validation_errors
    future_handoff = _mapping(contract.get("future_handoff"))
    return {
        "report_id": REPORT_ID,
        "contract_id": CONTRACT_ID,
        "validator_name": VALIDATOR_NAME,
        "validation_status": VALIDATION_STATUS if result_ok else "FAIL",
        "current_expected_state": state.value,
        "sha_system_dormancy_state": (
            sha_dormancy.get_atomicrows_sha_system_dormancy_state()
        ),
        "sha_system_dormant": sha_dormancy.is_sha_system_dormant(),
        "sha_system_non_participating_for_final_readiness": (
            sha_dormancy.is_sha_system_non_participating_for_final_readiness()
        ),
        "sha_generation_allowed": sha_dormancy.is_sha_generation_allowed(),
        "sha_freeze_authority_allowed_by_dormancy_policy": (
            sha_dormancy.is_sha_freeze_authority_allowed()
        ),
        "final_readiness_dependency_policy_state": (
            readiness_policy.get_qtt_final_readiness_dependency_policy_state()
        ),
        "sha_required_for_final_readiness": (
            readiness_policy.is_sha_required_for_final_readiness()
        ),
        "sha_dormancy_is_final_readiness_blocker": (
            readiness_policy.is_sha_dormancy_a_final_readiness_blocker()
        ),
        "bundle_jsonl_path": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
        "bundle_sha256_path": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        "bundle_jsonl_exists": state_report["bundle_jsonl_exists"],
        "bundle_sha256_exists": state_report["bundle_sha256_exists"],
        "bundle_row_count": state_report["bundle_row_count"],
        "expected_bundle_row_count": EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
        "bundle_jsonl_valid": state_report["bundle_jsonl_valid"],
        "bundle_jsonl_byte_preserved": bundle_jsonl_diff["unchanged"],
        "bundle_sha256_expected_absent": state_report["bundle_sha256_expected_absent"],
        "bundle_sha256_forbidden_absent": state_report["bundle_sha256_forbidden_absent"],
        "sha_freeze_authority_created": presence.sha_freeze_authority_exists,
        "freeze_receipt_created": presence.freeze_receipt_exists,
        "final_readiness_created": presence.final_readiness_exists,
        "runtime_live_authority_created": False,
        "source_connector_authority_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_authority_created": False,
        "replay_paper_execution_created": False,
        "optimizer_execution_created": False,
        "scoring_ranking_selection_execution_created": False,
        "existing_blocked_static_sha_freeze_gate_valid": existing_gate_flags.get(
            "existing_blocked_static_sha_freeze_gate_valid", False
        ),
        "existing_bundle_materialization_valid": existing_gate_flags.get(
            "existing_bundle_materialization_valid", False
        ),
        "existing_bundle_boundary_state_valid": existing_gate_flags.get(
            "existing_bundle_boundary_state_valid", False
        ),
        "state_transition_allowed_in_this_pr": False,
        "next_allowed_transition": NEXT_ALLOWED_TRANSITION,
        "future_sha_freeze_authority_handoff_state": future_handoff.get(
            "future_sha_freeze_authority_pr_required"
        ),
        "future_final_readiness_handoff_state": future_handoff.get(
            "future_final_readiness_pr_required"
        ),
        "future_runtime_live_state_centralization_required": future_handoff.get(
            "future_runtime_live_state_centralization_required"
        ),
        "future_profit_evidence_state_centralization_required": future_handoff.get(
            "future_profit_evidence_state_centralization_required"
        ),
        "future_quantum_execution_state_centralization_required": future_handoff.get(
            "future_quantum_execution_state_centralization_required"
        ),
        "forbidden_artifact_checks": state_report["forbidden_artifact_checks"],
        "master_plan_diff_check": master_plan_diff,
        "exact_row_source_diff_check": exact_row_source_diff,
        "bundle_jsonl_diff_check": bundle_jsonl_diff,
        "no_runtime_scanner_diff_check": no_runtime_scanner_diff,
        "validation_errors": validation_errors,
        "validation_warnings": [],
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "validation_status": VALIDATION_STATUS,
        "current_expected_state": CURRENT_EXPECTED_STATE.value,
        "sha_system_dormancy_state": (
            "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED"
        ),
        "sha_system_dormant": True,
        "sha_system_non_participating_for_final_readiness": True,
        "sha_generation_allowed": False,
        "sha_freeze_authority_allowed_by_dormancy_policy": False,
        "final_readiness_dependency_policy_state": (
            "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY"
        ),
        "sha_required_for_final_readiness": False,
        "sha_dormancy_is_final_readiness_blocker": False,
        "bundle_jsonl_exists": True,
        "bundle_sha256_exists": False,
        "bundle_row_count": EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
        "expected_bundle_row_count": EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
        "bundle_jsonl_valid": True,
        "bundle_jsonl_byte_preserved": True,
        "bundle_sha256_expected_absent": True,
        "bundle_sha256_forbidden_absent": True,
        "sha_freeze_authority_created": False,
        "freeze_receipt_created": False,
        "final_readiness_created": False,
        "runtime_live_authority_created": False,
        "source_connector_authority_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_authority_created": False,
        "replay_paper_execution_created": False,
        "optimizer_execution_created": False,
        "scoring_ranking_selection_execution_created": False,
        "existing_blocked_static_sha_freeze_gate_valid": True,
        "existing_bundle_materialization_valid": True,
        "existing_bundle_boundary_state_valid": True,
        "state_transition_allowed_in_this_pr": False,
        "next_allowed_transition": NEXT_ALLOWED_TRANSITION,
        "future_sha_freeze_authority_handoff_state": SHA_REACTIVATION_HANDOFF,
        "future_final_readiness_handoff_state": FINAL_READINESS_HANDOFF,
        "future_runtime_live_state_centralization_required": FUTURE_ONLY_HANDOFF,
        "future_profit_evidence_state_centralization_required": FUTURE_ONLY_HANDOFF,
        "future_quantum_execution_state_centralization_required": FUTURE_ONLY_HANDOFF,
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
    for field in (
        "master_plan_diff_check",
        "exact_row_source_diff_check",
        "bundle_jsonl_diff_check",
        "no_runtime_scanner_diff_check",
    ):
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
    write_report: bool = False,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        contract = load_yaml(_resolve(repo_root, contract_path))
        schema = load_json(_resolve(repo_root, schema_path))
    except Exception as exc:
        return ValidationResult(
            False,
            (f"could not load SHA/freeze/final-readiness state input: {exc}",),
            None,
        )

    failures.extend(validate_contract_payload(contract, schema))
    state = expected_atomicrows_sha_freeze_final_readiness_state_from_contract(repo_root)
    if state is not CURRENT_EXPECTED_STATE:
        failures.append(f"current expected state must be {CURRENT_EXPECTED_STATE.value}")
    failures.extend(
        validate_current_atomicrows_sha_freeze_final_readiness_state(
            repo_root,
            label="AtomicRowsShaFreezeFinalReadinessStateContract",
        )
    )
    if not sha_dormancy.is_sha_system_dormant():
        failures.append("central SHA system must remain dormant")
    if not sha_dormancy.is_sha_system_non_participating_for_final_readiness():
        failures.append(
            "central SHA system must remain non-participating for final readiness"
        )
    if sha_dormancy.is_sha_generation_allowed():
        failures.append("central SHA generation must remain disabled")
    if sha_dormancy.is_sha_freeze_authority_allowed():
        failures.append("central SHA/freeze authority must remain disabled")
    if readiness_policy.is_sha_required_for_final_readiness():
        failures.append("central final-readiness policy must not require SHA")
    if readiness_policy.is_sha_dormancy_a_final_readiness_blocker():
        failures.append(
            "central final-readiness policy must not treat SHA dormancy as a blocker"
        )

    presence = canonical_atomicrows_sha_freeze_presence(repo_root)
    if not presence.bundle_jsonl_exists:
        failures.append("AtomicRows.bundle.jsonl must exist")
    if presence.bundle_sha256_exists:
        failures.append("AtomicRows.bundle.sha256 must remain absent")
    if presence.sha_freeze_authority_exists:
        failures.append("future SHA/freeze authority artifacts must remain absent")
    if presence.freeze_receipt_exists:
        failures.append("future freeze receipts must remain absent")
    if presence.final_readiness_exists:
        failures.append("future final-readiness artifacts must remain absent")
    if "AtomicRows.bundle.sha256" not in validate_no_runtime_artifacts.FORBIDDEN_NAMES:
        failures.append("AtomicRows.bundle.sha256 must remain forbidden in no-runtime scanner")

    gate_failures, existing_gate_flags = validate_existing_gates(repo_root)
    failures.extend(gate_failures)

    for pathspec, message in (
        ("docs/master_plan/QTT_MasterPlan_Current.md", "master plan must remain unchanged"),
        ("docs/master_plan/atomic_rows/exact_row_sources", "exact row sources must remain unchanged"),
        (CANONICAL_ATOMICROWS_BUNDLE.as_posix(), "AtomicRows.bundle.jsonl must remain unchanged"),
        ("tools/validate_no_runtime_artifacts.py", "no-runtime scanner must remain unchanged"),
    ):
        if git_diff_check(repo_root, pathspec)["unchanged"] is not True:
            failures.append(message)

    report = build_report(
        repo_root=repo_root,
        contract=contract,
        existing_gate_flags=existing_gate_flags,
        validation_errors=[] if not failures else failures,
    )
    if failures:
        return ValidationResult(False, tuple(failures), report)

    report_failures = validate_report(report)
    if report_failures:
        return ValidationResult(False, tuple(report_failures), report)

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
