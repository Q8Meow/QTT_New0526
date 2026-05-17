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
from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as registry
from src.qtt.core.testing import qtt_final_readiness_dependency_policy as policy
from src.qtt.core.testing.atomicrows_sha_freeze_final_readiness_state import (
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
)
from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.validate_master_plan_section_coverage import validate_json_schema_subset


REPO_ROOT = _REPO_ROOT
DEFAULT_CONTRACT = pathlib.Path(
    "docs/master_plan/launch/QttActiveNonShaDay1GateStateRegistryContract.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/launch/qtt_active_non_sha_day1_gate_state_registry_contract.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/QttActiveNonShaDay1GateStateRegistry.report.json"
)

SUCCESS_MARKER = "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_OK"
FAILURE_MARKER = "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_FAILED"
CONTRACT_ID = "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_CONTRACT"
CONTRACT_VERSION = "v1"
AUTHORITY_CLASS = (
    "DAY1_GATE_STATE_REGISTRY_CONTROL_PLANE_NOT_FINAL_READINESS_NOT_RUNTIME_NOT_LIVE"
)
CURRENT_STATE = (
    "ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_ESTABLISHED_ALL_POSITIVE_EVIDENCE_GATES_BLOCKED_GUARDS_ACTIVE"
)
SHA_DORMANCY_STATE = "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED"
FINAL_READINESS_POLICY_STATE = (
    "FINAL_READINESS_DEPENDENCY_POLICY_ACTIVE_NON_SHA_GATES_ONLY"
)
REPORT_ID = "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_REPORT"
VALIDATION_STATUS = "PASS"
VALIDATOR_NAME = "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"

FORBIDDEN_FALSE_FIELDS = (
    "sha_required_for_day1_final_readiness",
    "sha_dormancy_is_day1_gate_blocker",
    "sha_absence_is_day1_gate_blocker",
    "sha_presence_is_final_readiness_evidence",
    "current_pr_flips_any_gate",
    "current_pr_marks_any_gate_satisfied",
    "current_pr_creates_final_readiness",
    "current_pr_creates_day1_launch_authority",
    "current_pr_creates_runtime_live_order_source_connector_runtime_cash_backend_profit_authority",
    "current_pr_creates_replay_paper_optimizer_neural_quantum_backend_execution",
    "current_pr_claims_profit_latency_execution_quantum_advantage_evidence",
    "source_facts_accepted_by_this_pr",
    "connector_semantics_bound_by_this_pr",
    "runtime_cash_receipts_created_by_this_pr",
    "order_fill_account_receipts_created_by_this_pr",
    "qubo_qaoa_vqe_ising_annealing_backend_simulator_execution_created_by_this_pr",
)

REQUIRED_TRUE_FIELDS = (
    "sha_dormancy_system_excluded_from_active_gate_ids",
    "positive_evidence_gates_currently_blocking_final_readiness",
    "guard_gates_active_and_unviolated",
    "quantum_backend_gate_conditional_not_required_for_non_backend_day1",
    "quantum_backend_gate_blocks_unauthorized_backend_simulator_provider_execution",
    "quantum_backend_gate_does_not_block_static_quantum_metadata_or_planning",
    "future_prs_must_flip_one_gate_state_at_a_time",
    "future_prs_must_materialize_only_one_artifact_or_capability_at_a_time",
    "registry_is_not_final_readiness",
    "registry_is_not_live_authority",
    "registry_is_not_profit_evidence",
    "registry_is_not_quantum_advantage_evidence",
)

GATE_RECORD_REQUIRED_FIELDS = (
    "gate_id",
    "gate_class",
    "current_state",
    "evaluation_mode",
    "currently_blocks_final_readiness",
    "current_pr_may_flip",
    "future_flip_pr_must_be_separate",
    "future_materialization_must_be_separate_from_unrelated_gate_flips",
    "future_materialization_may_enable_only_one_artifact_or_capability_at_a_time",
    "future_required_artifact_or_receipt",
    "future_flip_pr_family",
    "guard_active_and_unviolated",
    "conditional_on_future_launch_scope",
    "conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend",
    "true_quantum_backend_required_for_non_backend_day1_launch_scope",
    "blocks_unauthorized_backend_simulator_provider_execution",
    "blocks_static_quantum_metadata_or_planning",
    "creates_authority_in_this_pr",
    "creates_evidence_in_this_pr",
    "executes_runtime_in_this_pr",
    "notes",
)

BLOCKER_EVALUATION_MODES = {
    "POSITIVE_EVIDENCE_BLOCKER",
    "POSITIVE_RECEIPT_BLOCKER",
    "STATIC_CONTRACT_BLOCKER",
    "RUNTIME_RECEIPT_BLOCKER",
    "REPLAY_PAPER_RESULT_BLOCKER",
    "REVIEW_BLOCKER",
    "PREFLIGHT_BLOCKER",
    "SAFETY_PRECONDITION_BLOCKER",
}

GUARD_EVALUATION_MODES = {
    "ACTIVE_GUARD_UNVIOLATED",
    "CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES",
}


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
    return len(path.read_text(encoding="utf-8").splitlines())


def _contract_records(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in contract.get("gate_records", [])
        if isinstance(item, dict)
    ]


def validate_contract_payload(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(contract, schema)
    expected = {
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "authority_class": AUTHORITY_CLASS,
        "current_gate_registry_state": CURRENT_STATE,
        "current_sha_system_dormancy_state_required": SHA_DORMANCY_STATE,
        "current_final_readiness_dependency_policy_state_required": (
            FINAL_READINESS_POLICY_STATE
        ),
        "active_non_sha_gate_ids": list(registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS),
        "excluded_non_participating_subsystems": list(
            registry.EXCLUDED_NON_PARTICIPATING_SUBSYSTEMS
        ),
        "gate_records": [
            dict(record)
            for record in registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_RECORDS
        ],
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

    active_ids = contract.get("active_non_sha_gate_ids", [])
    if active_ids != list(registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS):
        failures.append("contract.active_non_sha_gate_ids must match central registry exactly")
    if "SHA_DORMANCY_SYSTEM" in active_ids:
        failures.append("SHA_DORMANCY_SYSTEM must not appear in active_non_sha_gate_ids")
    if len(active_ids) != len(set(active_ids)):
        failures.append("active_non_sha_gate_ids must be unique")

    records = _contract_records(contract)
    if len(records) != len(active_ids):
        failures.append("every active gate ID must have exactly one gate record")
    record_ids = [record.get("gate_id") for record in records]
    if record_ids != active_ids:
        failures.append("gate_records must be ordered exactly like active_non_sha_gate_ids")
    if len(record_ids) != len(set(record_ids)):
        failures.append("gate_records must not contain duplicate gate IDs")

    for record in records:
        missing = [field for field in GATE_RECORD_REQUIRED_FIELDS if field not in record]
        if missing:
            failures.append(
                f"gate record {record.get('gate_id')!r} missing fields {missing!r}"
            )
            continue
        gate_id = str(record["gate_id"])
        if gate_id not in registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_IDS:
            failures.append(f"unknown gate ID in gate_records: {gate_id}")
        if record["gate_class"] not in registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_CLASSES:
            failures.append(f"unknown gate class for {gate_id}: {record['gate_class']}")
        if record["current_state"] not in registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_STATES:
            failures.append(f"unknown gate state for {gate_id}: {record['current_state']}")
        if (
            record["evaluation_mode"]
            not in registry.QTT_ACTIVE_NON_SHA_DAY1_GATE_EVALUATION_MODES
        ):
            failures.append(
                f"unknown evaluation mode for {gate_id}: {record['evaluation_mode']}"
            )
        if record["current_pr_may_flip"] is not False:
            failures.append(f"{gate_id} current_pr_may_flip must be false")
        if record["current_state"] == "SATISFIED_BY_CANONICAL_RECEIPT":
            failures.append(f"{gate_id} must not be marked satisfied")
        for field in (
            "creates_authority_in_this_pr",
            "creates_evidence_in_this_pr",
            "executes_runtime_in_this_pr",
        ):
            if record[field] is not False:
                failures.append(f"{gate_id}.{field} must be false")
        for field in (
            "future_flip_pr_must_be_separate",
            "future_materialization_must_be_separate_from_unrelated_gate_flips",
            "future_materialization_may_enable_only_one_artifact_or_capability_at_a_time",
        ):
            if record[field] is not True:
                failures.append(f"{gate_id}.{field} must be true")
        if (
            record["evaluation_mode"] in BLOCKER_EVALUATION_MODES
            and record["currently_blocks_final_readiness"] is not True
        ):
            failures.append(f"{gate_id} positive blocker must block final readiness")
        if record["evaluation_mode"] in BLOCKER_EVALUATION_MODES and not str(
            record["current_state"]
        ).startswith("BLOCKED_"):
            failures.append(f"{gate_id} positive blocker must remain blocked")
        if (
            record["evaluation_mode"] in GUARD_EVALUATION_MODES
            and record["guard_active_and_unviolated"] is not True
        ):
            failures.append(f"{gate_id} guard gate must be active and unviolated")
        if record["gate_class"] == "REQUIRED_NO_CLAIM_GUARD_GATE":
            if record["evaluation_mode"] != "ACTIVE_GUARD_UNVIOLATED":
                failures.append(f"{gate_id} no-claim guard must use active guard mode")
            if not str(record["current_state"]).startswith("GUARD_ACTIVE_NO_"):
                failures.append(f"{gate_id} no-claim guard must be guard-active")
            if record["creates_evidence_in_this_pr"] is not False:
                failures.append(f"{gate_id} no-claim guard must not create evidence")

    quantum_record = _mapping(
        next(
            (
                record
                for record in records
                if record.get("gate_id") == "QUANTUM_BACKEND_AUTHORITY_GATE"
            ),
            {},
        )
    )
    if quantum_record.get("evaluation_mode") != (
        "CONDITIONAL_AUTHORITY_GUARD_NONBLOCKING_UNLESS_SCOPE_REQUIRES"
    ):
        failures.append("QUANTUM_BACKEND_AUTHORITY_GATE must be conditional")
    if (
        quantum_record.get(
            "conditional_blocks_final_readiness_if_selected_stack_requires_true_quantum_backend"
        )
        is not True
    ):
        failures.append("quantum backend gate must block if true backend scope is selected")
    if (
        quantum_record.get(
            "true_quantum_backend_required_for_non_backend_day1_launch_scope"
        )
        is not False
    ):
        failures.append(
            "quantum backend gate must not require true backend for non-backend Day-1"
        )
    if (
        quantum_record.get("blocks_unauthorized_backend_simulator_provider_execution")
        is not True
    ):
        failures.append(
            "quantum backend gate must block unauthorized backend/simulator/provider execution"
        )
    if quantum_record.get("blocks_static_quantum_metadata_or_planning") is not False:
        failures.append(
            "quantum backend gate must not block static quantum metadata or planning"
        )

    validator_contract = _mapping(contract.get("validator_contract"))
    expected_validator = {
        "validator_name": VALIDATOR_NAME,
        "success_marker": SUCCESS_MARKER,
        "schema_path": DEFAULT_SCHEMA.as_posix(),
        "generated_report_path": DEFAULT_REPORT.as_posix(),
        "creates_final_readiness": False,
        "creates_day1_launch_authority": False,
        "creates_runtime_live_order_source_connector_cash_backend_profit_quantum_authority": False,
    }
    if validator_contract != expected_validator:
        failures.append(
            "contract.validator_contract must match the active gate registry validator boundary"
        )
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
        "current_gate_registry_state": (
            registry.get_qtt_active_non_sha_day1_gate_registry_state()
        ),
        "current_sha_system_dormancy_state": (
            sha_state.get_atomicrows_sha_system_dormancy_state()
        ),
        "current_final_readiness_dependency_policy_state": (
            policy.get_qtt_final_readiness_dependency_policy_state()
        ),
        "active_non_sha_gate_ids": list(registry.get_active_non_sha_day1_gate_ids()),
        "active_gate_ids_match_final_readiness_dependency_policy": (
            registry.get_active_non_sha_day1_gate_ids()
            == policy.get_active_non_sha_final_readiness_dependencies()
        ),
        "sha_dormancy_system_excluded_from_active_gate_ids": (
            registry.is_sha_dormancy_system_excluded()
        ),
        "sha_required_for_day1_final_readiness": (
            policy.is_sha_required_for_final_readiness()
        ),
        "sha_dormancy_is_day1_gate_blocker": (
            policy.is_sha_dormancy_a_final_readiness_blocker()
        ),
        "sha_absence_is_day1_gate_blocker": (
            policy.is_sha_absence_a_final_readiness_blocker()
        ),
        "sha_presence_is_final_readiness_evidence": (
            policy.is_sha_presence_final_readiness_evidence()
        ),
        "currently_blocking_positive_gate_ids": list(
            registry.get_currently_blocking_positive_gate_ids()
        ),
        "guard_active_gate_ids": list(registry.get_guard_active_gate_ids()),
        "no_claim_guard_gate_ids": list(registry.get_no_claim_guard_gate_ids()),
        "conditional_authority_guard_gate_ids": list(
            registry.get_conditional_authority_guard_gate_ids()
        ),
        "no_gate_flipped_by_this_pr": not registry.CURRENT_PR_FLIPS_ANY_GATE,
        "no_gate_satisfied_by_this_pr": (
            not registry.CURRENT_PR_MARKS_ANY_GATE_SATISFIED
        ),
        "final_readiness_created": registry.CURRENT_PR_CREATES_FINAL_READINESS,
        "day1_launch_authority_created": (
            registry.CURRENT_PR_CREATES_DAY1_LAUNCH_AUTHORITY
        ),
        "runtime_live_order_source_connector_runtime_cash_backend_profit_authority_created": (
            registry.CURRENT_PR_CREATES_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_RUNTIME_CASH_BACKEND_PROFIT_AUTHORITY
        ),
        "replay_paper_optimizer_neural_quantum_backend_execution_created": (
            registry.CURRENT_PR_CREATES_REPLAY_PAPER_OPTIMIZER_NEURAL_QUANTUM_BACKEND_EXECUTION
        ),
        "profit_latency_execution_quantum_advantage_evidence_claimed": (
            registry.CURRENT_PR_CLAIMS_PROFIT_LATENCY_EXECUTION_QUANTUM_ADVANTAGE_EVIDENCE
        ),
        "source_facts_accepted_by_this_pr": (
            registry.CURRENT_PR_ACCEPTS_SOURCE_FACTS
        ),
        "connector_semantics_bound_by_this_pr": (
            registry.CURRENT_PR_BINDS_CONNECTOR_SEMANTICS
        ),
        "runtime_cash_receipts_created_by_this_pr": (
            registry.CURRENT_PR_CREATES_RUNTIME_CASH_RECEIPTS
        ),
        "order_fill_account_receipts_created_by_this_pr": (
            registry.CURRENT_PR_CREATES_ORDER_FILL_ACCOUNT_RECEIPTS
        ),
        "qubo_qaoa_vqe_ising_annealing_backend_simulator_execution_created_by_this_pr": (
            registry.CURRENT_PR_EXECUTES_QUBO_QAOA_VQE_ISING_ANNEALING_BACKEND_SIMULATOR
        ),
        "quantum_backend_gate_conditional_not_required_for_non_backend_day1": (
            registry.is_quantum_backend_gate_conditional()
        ),
        "quantum_backend_gate_blocks_unauthorized_backend_simulator_provider_execution": (
            registry.get_gate_record("QUANTUM_BACKEND_AUTHORITY_GATE")[
                "blocks_unauthorized_backend_simulator_provider_execution"
            ]
        ),
        "quantum_backend_gate_does_not_block_static_quantum_metadata_or_planning": (
            not registry.get_gate_record("QUANTUM_BACKEND_AUTHORITY_GATE")[
                "blocks_static_quantum_metadata_or_planning"
            ]
        ),
        "atomicrows_bundle_path": CANONICAL_ATOMICROWS_BUNDLE.as_posix(),
        "atomicrows_bundle_exists": bundle_path.exists(),
        "atomicrows_bundle_line_count": _line_count(bundle_path),
        "atomicrows_bundle_expected_line_count": EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
        "atomicrows_bundle_sha256_path": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        "atomicrows_bundle_sha256_exists": sha_path.exists(),
        "future_prs_must_flip_one_gate_state_at_a_time": contract.get(
            "future_prs_must_flip_one_gate_state_at_a_time"
        ),
        "future_prs_must_materialize_only_one_artifact_or_capability_at_a_time": (
            contract.get(
                "future_prs_must_materialize_only_one_artifact_or_capability_at_a_time"
            )
        ),
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
            (f"could not load active non-SHA gate registry input: {exc}",),
            None,
        )

    failures.extend(validate_contract_payload(contract, schema))

    if registry.get_qtt_active_non_sha_day1_gate_registry_state() != CURRENT_STATE:
        failures.append(f"central gate registry state must be {CURRENT_STATE}")
    if sha_state.get_atomicrows_sha_system_dormancy_state() != SHA_DORMANCY_STATE:
        failures.append(f"central SHA dormancy state must be {SHA_DORMANCY_STATE}")
    if policy.get_qtt_final_readiness_dependency_policy_state() != FINAL_READINESS_POLICY_STATE:
        failures.append(
            "central final-readiness dependency policy must remain active non-SHA gates only"
        )
    if not registry.is_sha_dormancy_system_excluded():
        failures.append("SHA_DORMANCY_SYSTEM must be excluded from active gate IDs")
    if policy.is_sha_required_for_final_readiness():
        failures.append("SHA must not be required for Day-1 final readiness")
    if policy.is_sha_dormancy_a_final_readiness_blocker():
        failures.append("SHA dormancy must not be a Day-1 gate blocker")
    if policy.is_sha_absence_a_final_readiness_blocker():
        failures.append("SHA absence must not be a Day-1 gate blocker")
    if policy.is_sha_presence_final_readiness_evidence():
        failures.append("SHA presence must not be final-readiness evidence")
    if (
        registry.get_active_non_sha_day1_gate_ids()
        != policy.get_active_non_sha_final_readiness_dependencies()
    ):
        failures.append(
            "active gate IDs must match final-readiness dependency policy exactly"
        )

    for assertion in (
        registry.assert_registry_current,
        registry.assert_no_gate_flipped_by_this_pr,
        registry.assert_no_gate_satisfied_by_this_pr,
        registry.assert_all_positive_evidence_gates_remain_blocked,
        registry.assert_guard_gates_active_and_unviolated,
        registry.assert_sha_dormancy_system_excluded,
        registry.assert_quantum_backend_gate_does_not_require_backend_for_non_backend_day1,
        registry.assert_current_pr_creates_no_final_readiness,
        registry.assert_current_pr_creates_no_runtime_live_profit_or_backend_authority,
        registry.assert_current_pr_creates_no_replay_paper_optimizer_neural_quantum_execution,
        registry.assert_current_pr_creates_no_profit_latency_execution_quantum_advantage_evidence,
        policy.assert_active_dependencies_consume_gate_registry,
        policy.assert_day1_final_readiness_must_ignore_sha_dormancy_when_non_sha_gates_pass,
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

    report = build_report(
        repo_root=repo_root,
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
