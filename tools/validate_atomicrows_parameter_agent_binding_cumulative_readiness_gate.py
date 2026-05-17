#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder  # noqa: E402
from tools import validate_atomicrows_parameter_agent_binding_consumer_gate as consumer_gate  # noqa: E402
from tools import validate_atomicrows_parameter_agent_binding_registry as binding_registry  # noqa: E402
from tools import validate_qtt_owner_global_override_authority as owner_authority  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_agent_binding_cumulative_readiness_gate.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_agent_binding_cumulative_readiness_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
)

DEFAULT_REGISTRY = binding_registry.DEFAULT_REGISTRY
DEFAULT_REGISTRY_SCHEMA = binding_registry.DEFAULT_SCHEMA
DEFAULT_REGISTRY_REPORT = binding_registry.DEFAULT_REPORT
DEFAULT_CONSUMER_GATE_SCHEMA = consumer_gate.DEFAULT_SCHEMA
DEFAULT_CONSUMER_GATE_REPORT = consumer_gate.DEFAULT_REPORT
OWNER_GLOBAL_OVERRIDE_POLICY = owner_authority.DEFAULT_POLICY
OWNER_GLOBAL_OVERRIDE_SCHEMA = owner_authority.DEFAULT_GLOBAL_SCHEMA
OWNER_GLOBAL_OVERRIDE_REPORT = owner_authority.DEFAULT_REPORT

CANONICAL_BUNDLE = binding_registry.CANONICAL_BUNDLE
CANONICAL_BUNDLE_SHA = binding_registry.CANONICAL_BUNDLE_SHA

REPORT_TYPE = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_REPORT"
)
CUMULATIVE_CHECK_ID = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE"
)
READINESS_DOMAIN = "ATOMICROWS_PARAMETER_AGENT_BINDING"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_VALIDATION_OK"
)
FAILURE_MARKER = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_VALIDATION_FAILED"
)
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_FINAL_INCOMPLETE"
)
VALIDATION_HOOK = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_STATIC_VALIDATION"
)

UPSTREAM_ARTIFACT_PATHS = (
    DEFAULT_REGISTRY,
    DEFAULT_REGISTRY_SCHEMA,
    DEFAULT_REGISTRY_REPORT,
    DEFAULT_CONSUMER_GATE_SCHEMA,
    DEFAULT_CONSUMER_GATE_REPORT,
    OWNER_GLOBAL_OVERRIDE_POLICY,
    OWNER_GLOBAL_OVERRIDE_REPORT,
)

MINIMUM_COUNTS = {
    "registry_binding_count": 13,
    "registry_owner_approved_binding_count": 7,
    "registry_owner_global_override_binding_count": 4,
    "registry_owner_override_satisfied_binding_count": 4,
    "registry_missing_binding_owner_override_satisfied_count": 1,
    "consumer_attempted_access_count": 38,
    "consumer_allowed_access_count": 28,
    "consumer_blocked_access_count": 10,
    "consumer_owner_override_attempt_count": 12,
    "consumer_owner_override_allowed_count": 12,
    "consumer_allowed_by_owner_global_override_count": 7,
    "consumer_allowed_by_agent_assignment_owner_approved_count": 1,
    "consumer_allowed_by_owner_override_satisfied_count": 4,
    "consumer_missing_binding_owner_override_satisfied_count": 1,
    "consumer_unauthorized_agent_role_owner_override_satisfied_count": 1,
    "consumer_unauthorized_agent_id_owner_override_satisfied_count": 1,
    "consumer_unauthorized_consumer_class_owner_override_satisfied_count": 1,
    "consumer_scope_mismatch_owner_override_satisfied_count": 1,
    "consumer_unknown_parameter_target_owner_override_satisfied_count": 1,
}

FORBIDDEN_ARTIFACT_FIELDS = (
    "real_runtime_artifact_created",
    "real_live_artifact_created",
    "real_order_artifact_created",
    "real_quantum_backend_artifact_created",
    "real_profit_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "private_state_fetch_created",
    "secret_materialization_created",
    "external_repo_clone_created",
    "package_install_created",
    "bundle_file_present",
    "bundle_sha_present",
)

OWNER_OVERRIDE_BLOCK_FIELDS = (
    "owner_override_blocked_count",
    "validators_block_owner_override_count",
    "codex_blocks_owner_override_count",
    "qtt_agents_block_owner_override_count",
    "generated_reports_block_owner_override_count",
    "validation_gates_block_owner_override_count",
)

FIXTURE_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "deterministic_output",
    "generated_at_utc",
    "validation_hook_ids",
    "expected_report",
}

FIXTURE_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_FIXTURE"
    ),
    "fixture_version": (
        "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_FIXTURE_V1"
    ),
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_BINDING_READINESS_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_BINDING_READINESS_AUTHORITY"
    ),
    "surface_kind": (
        "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE_STATIC"
    ),
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "generated_at_utc": DETERMINISTIC_GENERATED_AT,
}


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _normalize_path(path: pathlib.Path | str) -> str:
    return str(path).replace("\\", "/")


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _integer(report: Mapping[str, Any] | None, field: str) -> int:
    value = _mapping(report).get(field)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _bool(report: Mapping[str, Any] | None, field: str) -> bool:
    return _mapping(report).get(field) is True


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is invalid: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    missing = sorted(expected_fields - set(value))
    unexpected = sorted(set(value) - expected_fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "cumulative_check_id": CUMULATIVE_CHECK_ID,
        "readiness_domain": READINESS_DOMAIN,
        "registry_path": _normalize_path(DEFAULT_REGISTRY),
        "registry_schema_path": _normalize_path(DEFAULT_REGISTRY_SCHEMA),
        "registry_report_path": _normalize_path(DEFAULT_REGISTRY_REPORT),
        "consumer_gate_schema_path": _normalize_path(DEFAULT_CONSUMER_GATE_SCHEMA),
        "consumer_gate_report_path": _normalize_path(DEFAULT_CONSUMER_GATE_REPORT),
        "owner_global_override_policy_path": _normalize_path(
            OWNER_GLOBAL_OVERRIDE_POLICY
        ),
        "owner_global_override_report_path": _normalize_path(
            OWNER_GLOBAL_OVERRIDE_REPORT
        ),
        "upstream_artifact_count": len(UPSTREAM_ARTIFACT_PATHS),
        "upstream_artifacts_present_count": 0,
        "upstream_artifacts_missing_count": len(UPSTREAM_ARTIFACT_PATHS),
        "registry_present": False,
        "registry_schema_present": False,
        "registry_report_present": False,
        "consumer_gate_schema_present": False,
        "consumer_gate_report_present": False,
        "owner_global_override_report_present": False,
        "registry_binding_count": 0,
        "registry_owner_approved_binding_count": 0,
        "registry_owner_global_override_binding_count": 0,
        "registry_owner_override_satisfied_binding_count": 0,
        "registry_missing_binding_normal_blocked_count": 0,
        "registry_missing_binding_owner_override_satisfied_count": 0,
        "registry_runtime_binding_count": 0,
        "registry_live_binding_count": 0,
        "registry_quantum_backend_binding_count": 0,
        "registry_final_ready": False,
        "consumer_attempted_access_count": 0,
        "consumer_allowed_access_count": 0,
        "consumer_blocked_access_count": 0,
        "consumer_invalid_access_count": 0,
        "consumer_owner_override_attempt_count": 0,
        "consumer_owner_override_allowed_count": 0,
        "consumer_owner_override_blocked_count": 0,
        "consumer_allowed_by_owner_global_override_count": 0,
        "consumer_allowed_by_agent_assignment_owner_approved_count": 0,
        "consumer_allowed_by_owner_override_satisfied_count": 0,
        "consumer_missing_binding_owner_override_satisfied_count": 0,
        "consumer_unauthorized_agent_role_owner_override_satisfied_count": 0,
        "consumer_unauthorized_agent_id_owner_override_satisfied_count": 0,
        "consumer_unauthorized_consumer_class_owner_override_satisfied_count": 0,
        "consumer_scope_mismatch_owner_override_satisfied_count": 0,
        "consumer_unknown_parameter_target_owner_override_satisfied_count": 0,
        "owner_global_override_authority": False,
        "owner_override_satisfies_all_qtt_internal_requirements": False,
        "owner_override_satisfies_binding_readiness": False,
        "owner_override_blocked_count": 0,
        "validators_block_owner_override_count": 0,
        "codex_blocks_owner_override_count": 0,
        "qtt_agents_block_owner_override_count": 0,
        "generated_reports_block_owner_override_count": 0,
        "validation_gates_block_owner_override_count": 0,
        "static_binding_foundation_ready": False,
        "normal_full_binding_coverage_ready": False,
        "qtt_internal_binding_cumulative_ready": False,
        "final_qtt_internal_status": "BLOCKED_PENDING_BINDING_COVERAGE",
        "blocks_qtt_when_owner_override_present": False,
        "cumulative_ready_basis": "STATIC_FOUNDATION_ONLY",
        "final_ready": False,
        "real_runtime_artifact_created": False,
        "real_live_artifact_created": False,
        "real_order_artifact_created": False,
        "real_quantum_backend_artifact_created": False,
        "real_profit_artifact_created": False,
        "source_acceptance_artifact_created": False,
        "connector_binding_artifact_created": False,
        "private_state_fetch_created": False,
        "secret_materialization_created": False,
        "external_repo_clone_created": False,
        "package_install_created": False,
        "bundle_file_present": False,
        "bundle_sha_present": False,
        "uses_pr_number_as_authority": False,
        "authority_boundary_all_false": False,
    }


REPORT_FIELDS = tuple(_empty_report())


def _sum_report_fields(
    reports: Sequence[Mapping[str, Any] | None],
    field: str,
) -> int:
    return sum(_integer(report, field) for report in reports)


def _any_report_true(
    reports: Sequence[Mapping[str, Any] | None],
    field: str,
) -> bool:
    return any(_bool(report, field) for report in reports)


def _upstream_presence(repo_root: pathlib.Path) -> dict[str, bool]:
    root = repo_root.resolve()
    return {
        _normalize_path(path): (root / path).exists()
        for path in UPSTREAM_ARTIFACT_PATHS
    }


def _reports_are_deterministic(*reports: Mapping[str, Any] | None) -> bool:
    return all(
        _mapping(report).get("deterministic_output") is True
        and _mapping(report).get("generated_at_utc") == DETERMINISTIC_GENERATED_AT
        for report in reports
    )


def _owner_policy_satisfies_override(policy: Mapping[str, Any] | None) -> bool:
    policy = _mapping(policy)
    return (
        policy.get("owner_global_override_authority") is True
        and policy.get("owner_override_satisfies_all_qtt_internal_requirements")
        is True
        and policy.get("chatgpt_authority_over_owner") is False
        and policy.get("codex_authority_over_owner") is False
        and policy.get("qtt_agent_authority_over_owner") is False
        and policy.get("validator_authority_over_owner") is False
        and policy.get("generated_report_authority_over_owner") is False
        and policy.get("qtt_gate_authority_over_owner") is False
    )


def build_report(
    *,
    repo_root: pathlib.Path,
    binding_report: Mapping[str, Any] | None,
    consumer_report: Mapping[str, Any] | None,
    owner_report: Mapping[str, Any] | None,
    owner_policy: Mapping[str, Any] | None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    presence = _upstream_presence(root)
    present_count = sum(1 for present in presence.values() if present)
    missing_count = len(UPSTREAM_ARTIFACT_PATHS) - present_count
    owner_schema_present = (root / OWNER_GLOBAL_OVERRIDE_SCHEMA).exists()
    bundle_file_present = (root / CANONICAL_BUNDLE).exists() or _any_report_true(
        (binding_report, consumer_report),
        "bundle_file_present",
    )
    bundle_sha_present = (root / CANONICAL_BUNDLE_SHA).exists() or _any_report_true(
        (binding_report, consumer_report),
        "bundle_sha_present",
    )

    report = _empty_report()
    report.update(
        {
            "upstream_artifacts_present_count": present_count,
            "upstream_artifacts_missing_count": missing_count,
            "registry_present": presence[_normalize_path(DEFAULT_REGISTRY)],
            "registry_schema_present": presence[
                _normalize_path(DEFAULT_REGISTRY_SCHEMA)
            ],
            "registry_report_present": presence[
                _normalize_path(DEFAULT_REGISTRY_REPORT)
            ],
            "consumer_gate_schema_present": presence[
                _normalize_path(DEFAULT_CONSUMER_GATE_SCHEMA)
            ],
            "consumer_gate_report_present": presence[
                _normalize_path(DEFAULT_CONSUMER_GATE_REPORT)
            ],
            "owner_global_override_report_present": presence[
                _normalize_path(OWNER_GLOBAL_OVERRIDE_REPORT)
            ],
            "registry_binding_count": _integer(binding_report, "binding_count"),
            "registry_owner_approved_binding_count": _integer(
                binding_report,
                "owner_approved_binding_count",
            ),
            "registry_owner_global_override_binding_count": _integer(
                binding_report,
                "owner_global_override_binding_count",
            ),
            "registry_owner_override_satisfied_binding_count": _integer(
                binding_report,
                "owner_override_satisfied_binding_count",
            ),
            "registry_missing_binding_normal_blocked_count": _integer(
                binding_report,
                "missing_binding_normal_blocked_count",
            ),
            "registry_missing_binding_owner_override_satisfied_count": _integer(
                binding_report,
                "missing_binding_owner_override_satisfied_count",
            ),
            "registry_runtime_binding_count": _integer(
                binding_report,
                "runtime_binding_count",
            ),
            "registry_live_binding_count": _integer(
                binding_report,
                "live_binding_count",
            ),
            "registry_quantum_backend_binding_count": _integer(
                binding_report,
                "quantum_backend_binding_count",
            ),
            "registry_final_ready": _bool(binding_report, "final_ready"),
            "consumer_attempted_access_count": _integer(
                consumer_report,
                "attempted_access_count",
            ),
            "consumer_allowed_access_count": _integer(
                consumer_report,
                "allowed_access_count",
            ),
            "consumer_blocked_access_count": _integer(
                consumer_report,
                "blocked_access_count",
            ),
            "consumer_invalid_access_count": _integer(
                consumer_report,
                "invalid_access_count",
            ),
            "consumer_owner_override_attempt_count": _integer(
                consumer_report,
                "owner_override_access_attempt_count",
            ),
            "consumer_owner_override_allowed_count": _integer(
                consumer_report,
                "owner_override_access_allowed_count",
            ),
            "consumer_owner_override_blocked_count": _integer(
                consumer_report,
                "owner_override_access_blocked_count",
            ),
            "consumer_allowed_by_owner_global_override_count": _integer(
                consumer_report,
                "allowed_by_owner_global_override_count",
            ),
            "consumer_allowed_by_agent_assignment_owner_approved_count": _integer(
                consumer_report,
                "allowed_by_agent_assignment_owner_approved_count",
            ),
            "consumer_allowed_by_owner_override_satisfied_count": _integer(
                consumer_report,
                "allowed_by_owner_override_satisfied_count",
            ),
            "consumer_missing_binding_owner_override_satisfied_count": _integer(
                consumer_report,
                "missing_binding_owner_override_satisfied_count",
            ),
            "consumer_unauthorized_agent_role_owner_override_satisfied_count": _integer(
                consumer_report,
                "unauthorized_agent_role_owner_override_satisfied_count",
            ),
            "consumer_unauthorized_agent_id_owner_override_satisfied_count": _integer(
                consumer_report,
                "unauthorized_agent_id_owner_override_satisfied_count",
            ),
            "consumer_unauthorized_consumer_class_owner_override_satisfied_count": _integer(
                consumer_report,
                "unauthorized_consumer_class_owner_override_satisfied_count",
            ),
            "consumer_scope_mismatch_owner_override_satisfied_count": _integer(
                consumer_report,
                "scope_mismatch_owner_override_satisfied_count",
            ),
            "consumer_unknown_parameter_target_owner_override_satisfied_count": _integer(
                consumer_report,
                "unknown_parameter_target_owner_override_satisfied_count",
            ),
            "owner_global_override_authority": _bool(
                owner_report,
                "owner_global_override_authority",
            ),
            "owner_override_satisfies_all_qtt_internal_requirements": _bool(
                owner_report,
                "owner_override_satisfies_all_qtt_internal_requirements",
            ),
            "owner_override_blocked_count": _integer(
                owner_report,
                "owner_override_blocked_case_count",
            )
            + _integer(consumer_report, "owner_override_access_blocked_count"),
            "validators_block_owner_override_count": _sum_report_fields(
                (owner_report, consumer_report),
                "validators_block_owner_override_count",
            ),
            "codex_blocks_owner_override_count": _sum_report_fields(
                (owner_report, consumer_report),
                "codex_blocks_owner_override_count",
            ),
            "qtt_agents_block_owner_override_count": _sum_report_fields(
                (owner_report, consumer_report),
                "qtt_agents_block_owner_override_count",
            ),
            "generated_reports_block_owner_override_count": _sum_report_fields(
                (owner_report, consumer_report),
                "generated_reports_block_owner_override_count",
            ),
            "validation_gates_block_owner_override_count": _sum_report_fields(
                (owner_report, consumer_report),
                "validation_gates_block_owner_override_count",
            ),
            "real_runtime_artifact_created": _any_report_true(
                (binding_report, consumer_report),
                "real_runtime_artifact_created",
            ),
            "real_live_artifact_created": _any_report_true(
                (binding_report, consumer_report),
                "real_live_artifact_created",
            ),
            "real_order_artifact_created": _any_report_true(
                (binding_report, consumer_report),
                "real_order_artifact_created",
            ),
            "real_quantum_backend_artifact_created": _any_report_true(
                (binding_report, consumer_report),
                "real_quantum_backend_artifact_created",
            ),
            "real_profit_artifact_created": _any_report_true(
                (binding_report, consumer_report),
                "real_profit_artifact_created",
            ),
            "source_acceptance_artifact_created": _bool(
                consumer_report,
                "source_acceptance_artifact_created",
            ),
            "connector_binding_artifact_created": _bool(
                consumer_report,
                "connector_binding_artifact_created",
            ),
            "private_state_fetch_created": _bool(
                consumer_report,
                "private_state_fetch_created",
            ),
            "secret_materialization_created": _bool(
                consumer_report,
                "secret_materialization_created",
            ),
            "external_repo_clone_created": _bool(
                consumer_report,
                "external_repo_clone_created",
            ),
            "package_install_created": _bool(
                consumer_report,
                "package_install_created",
            ),
            "bundle_file_present": bundle_file_present,
            "bundle_sha_present": bundle_sha_present,
            "uses_pr_number_as_authority": _any_report_true(
                (binding_report, consumer_report, owner_report),
                "uses_pr_number_as_authority",
            ),
        }
    )

    owner_override_satisfies = (
        report["owner_global_override_authority"] is True
        and report["owner_override_satisfies_all_qtt_internal_requirements"] is True
        and _owner_policy_satisfies_override(owner_policy)
    )
    normal_full_ready = (
        report["registry_final_ready"] is True
        and _bool(consumer_report, "final_ready") is True
        and bundle_file_present
        and bundle_sha_present
    )
    forbidden_clear = all(
        report[field] is False
        for field in FORBIDDEN_ARTIFACT_FIELDS
        if field != "bundle_file_present"
    )
    owner_block_counts_clear = all(
        report[field] == 0 for field in OWNER_OVERRIDE_BLOCK_FIELDS
    )
    minimums_satisfied = all(
        report[field] >= minimum for field, minimum in MINIMUM_COUNTS.items()
    )
    static_foundation_ready = (
        missing_count == 0
        and owner_schema_present
        and _reports_are_deterministic(binding_report, consumer_report, owner_report)
        and _bool(binding_report, "authority_boundary_all_false")
        and _bool(consumer_report, "authority_boundary_all_false")
        and _bool(owner_report, "authority_boundary_all_false")
        and minimums_satisfied
        and report["consumer_invalid_access_count"] == 0
        and owner_override_satisfies
        and forbidden_clear
        and owner_block_counts_clear
        and report["uses_pr_number_as_authority"] is False
    )
    qtt_internal_ready = normal_full_ready or owner_override_satisfies
    if normal_full_ready:
        final_status = "NORMAL_FULL_BINDING_COVERAGE_READY"
        cumulative_basis = "NORMAL_FULL_BINDING_COVERAGE"
    elif owner_override_satisfies:
        final_status = "OWNER_OVERRIDE_SATISFIED"
        cumulative_basis = "OWNER_GLOBAL_OVERRIDE"
    else:
        final_status = "BLOCKED_PENDING_BINDING_COVERAGE"
        cumulative_basis = "STATIC_FOUNDATION_ONLY"

    report.update(
        {
            "owner_override_satisfies_binding_readiness": owner_override_satisfies,
            "static_binding_foundation_ready": static_foundation_ready,
            "normal_full_binding_coverage_ready": normal_full_ready,
            "qtt_internal_binding_cumulative_ready": qtt_internal_ready,
            "final_qtt_internal_status": final_status,
            "blocks_qtt_when_owner_override_present": False,
            "cumulative_ready_basis": cumulative_basis,
            "final_ready": False,
            "authority_boundary_all_false": (
                _bool(binding_report, "authority_boundary_all_false")
                and _bool(consumer_report, "authority_boundary_all_false")
                and _bool(owner_report, "authority_boundary_all_false")
                and forbidden_clear
                and owner_block_counts_clear
                and report["uses_pr_number_as_authority"] is False
            ),
        }
    )
    return report


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    report_schema = defs.get("cumulative_readiness_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.cumulative_readiness_report must be an object"]
    if report_schema.get("required") != list(REPORT_FIELDS):
        return ["schema.$defs.cumulative_readiness_report.required is not exact"]
    return []


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(schema.get("$defs")).get("cumulative_readiness_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.cumulative_readiness_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _validate_fixture_shape(
    *,
    fixture: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(fixture, FIXTURE_FIELDS, "fixture")
    for field, expected in sorted(FIXTURE_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    expected_report = fixture.get("expected_report")
    if not isinstance(expected_report, dict):
        failures.append("fixture.expected_report must be an object")
    elif set(expected_report) != set(REPORT_FIELDS):
        failures.append("fixture.expected_report fields are not exact")
    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_upstream_report_identity(
    report: Mapping[str, Any] | None,
    *,
    label: str,
    report_type: str,
) -> list[str]:
    report = _mapping(report)
    failures: list[str] = []
    if report.get("report_type") != report_type:
        failures.append(f"{label}.report_type must be {report_type}")
    if report.get("deterministic_output") is not True:
        failures.append(f"{label}.deterministic_output must be true")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append(f"{label}.generated_at_utc must be deterministic")
    return failures


def _load_upstreams(
    *,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    registry_schema_path: pathlib.Path,
    registry_report_path: pathlib.Path,
    consumer_gate_schema_path: pathlib.Path,
    consumer_gate_report_path: pathlib.Path,
    owner_global_override_policy_path: pathlib.Path,
    owner_global_override_schema_path: pathlib.Path,
    owner_global_override_report_path: pathlib.Path,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    root = repo_root.resolve()
    failures: list[str] = []
    for path in (
        registry_path,
        registry_schema_path,
        registry_report_path,
        consumer_gate_schema_path,
        consumer_gate_report_path,
        owner_global_override_policy_path,
        owner_global_override_schema_path,
        owner_global_override_report_path,
    ):
        if not (root / path).exists():
            failures.append(f"required upstream artifact is missing: {path.as_posix()}")

    binding_report, binding_report_failures = _load_json(root / registry_report_path)
    consumer_report, consumer_report_failures = _load_json(
        root / consumer_gate_report_path
    )
    owner_report, owner_report_failures = _load_json(
        root / owner_global_override_report_path
    )
    failures.extend(binding_report_failures)
    failures.extend(consumer_report_failures)
    failures.extend(owner_report_failures)

    owner_policy, owner_policy_failures = owner_authority._parse_policy_yaml(
        root / owner_global_override_policy_path
    )
    failures.extend(owner_policy_failures)

    registry_result = binding_registry.validate(
        mode="dev",
        repo_root=root,
        registry_path=registry_path,
        schema_path=registry_schema_path,
        fixture_path=binding_registry.DEFAULT_FIXTURE,
        output_path=None,
    )
    failures.extend(
        f"binding registry validation: {failure}"
        for failure in registry_result.failures
    )
    if binding_report is not None and registry_result.report is not None:
        if binding_report != registry_result.report:
            failures.append("binding registry report is stale or non-deterministic")

    consumer_result = consumer_gate.validate(
        mode="dev",
        repo_root=root,
        registry_path=registry_path,
        binding_report_path=registry_report_path,
        schema_path=consumer_gate_schema_path,
        fixture_path=consumer_gate.DEFAULT_FIXTURE,
        output_path=None,
    )
    failures.extend(
        f"binding consumer gate validation: {failure}"
        for failure in consumer_result.failures
    )
    if consumer_report is not None and consumer_result.report is not None:
        if consumer_report != consumer_result.report:
            failures.append("binding consumer gate report is stale or non-deterministic")

    owner_failures, expected_owner_report = owner_authority.validate_static_surface(
        repo_root=root,
        global_schema_path=root / owner_global_override_schema_path,
        receipt_schema_path=root / owner_authority.DEFAULT_RECEIPT_SCHEMA,
        approval_request_schema_path=root / owner_authority.DEFAULT_APPROVAL_REQUEST_SCHEMA,
        policy_path=root / owner_global_override_policy_path,
        authority_fixture_path=root / owner_authority.DEFAULT_AUTHORITY_FIXTURE,
        receipt_fixture_path=root / owner_authority.DEFAULT_RECEIPT_FIXTURE,
        approval_request_fixture_path=root / owner_authority.DEFAULT_APPROVAL_REQUEST_FIXTURE,
        report_path=root / owner_global_override_report_path,
    )
    failures.extend(f"owner global override validation: {failure}" for failure in owner_failures)
    if owner_report is not None and expected_owner_report is not None:
        if owner_report != expected_owner_report:
            failures.append("owner global override report is stale or non-deterministic")

    failures.extend(
        _validate_upstream_report_identity(
            binding_report,
            label="binding registry report",
            report_type=binding_registry.REPORT_TYPE,
        )
    )
    failures.extend(
        _validate_upstream_report_identity(
            consumer_report,
            label="binding consumer gate report",
            report_type=consumer_gate.REPORT_TYPE,
        )
    )
    failures.extend(
        _validate_upstream_report_identity(
            owner_report,
            label="owner global override report",
            report_type=owner_authority.REPORT_TYPE,
        )
    )
    return binding_report, consumer_report, owner_report, owner_policy, failures


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("upstream_artifact_count", 0) < 7:
        failures.append("report.upstream_artifact_count must be at least 7")
    if report.get("upstream_artifacts_present_count") != report.get(
        "upstream_artifact_count"
    ):
        failures.append("all required upstream artifacts must be present")
    if report.get("upstream_artifacts_missing_count") != 0:
        failures.append("report.upstream_artifacts_missing_count must be 0")
    for field in (
        "registry_present",
        "registry_schema_present",
        "registry_report_present",
        "consumer_gate_schema_present",
        "consumer_gate_report_present",
        "owner_global_override_report_present",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "owner_override_satisfies_binding_readiness",
        "static_binding_foundation_ready",
        "qtt_internal_binding_cumulative_ready",
        "authority_boundary_all_false",
    ):
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    if report.get("normal_full_binding_coverage_ready") is not False:
        failures.append("report.normal_full_binding_coverage_ready must remain false")
    if report.get("final_qtt_internal_status") != "OWNER_OVERRIDE_SATISFIED":
        failures.append("report.final_qtt_internal_status must be OWNER_OVERRIDE_SATISFIED")
    if report.get("blocks_qtt_when_owner_override_present") is not False:
        failures.append("owner override must not block QTT internal workflow")
    if report.get("cumulative_ready_basis") != "OWNER_GLOBAL_OVERRIDE":
        failures.append("report.cumulative_ready_basis must be OWNER_GLOBAL_OVERRIDE")
    if report.get("final_ready") is not False:
        failures.append("report.final_ready must remain false")
    if report.get("consumer_invalid_access_count") != 0:
        failures.append("report.consumer_invalid_access_count must be 0")
    for field, minimum in sorted(MINIMUM_COUNTS.items()):
        if report.get(field, 0) < minimum:
            failures.append(f"report.{field} must be at least {minimum}")
    for field in OWNER_OVERRIDE_BLOCK_FIELDS:
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")
    for field in FORBIDDEN_ARTIFACT_FIELDS:
        if field == "bundle_file_present":
            continue
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("uses_pr_number_as_authority") is not False:
        failures.append("report.uses_pr_number_as_authority must be false")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is nondeterministic")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
    registry_path: pathlib.Path = DEFAULT_REGISTRY,
    registry_schema_path: pathlib.Path = DEFAULT_REGISTRY_SCHEMA,
    registry_report_path: pathlib.Path = DEFAULT_REGISTRY_REPORT,
    consumer_gate_schema_path: pathlib.Path = DEFAULT_CONSUMER_GATE_SCHEMA,
    consumer_gate_report_path: pathlib.Path = DEFAULT_CONSUMER_GATE_REPORT,
    owner_global_override_policy_path: pathlib.Path = OWNER_GLOBAL_OVERRIDE_POLICY,
    owner_global_override_schema_path: pathlib.Path = OWNER_GLOBAL_OVERRIDE_SCHEMA,
    owner_global_override_report_path: pathlib.Path = OWNER_GLOBAL_OVERRIDE_REPORT,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json(root / schema_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_failures)
    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if fixture is not None:
        failures.extend(_validate_fixture_shape(fixture=fixture, schema=schema))

    binding_report, consumer_report, owner_report, owner_policy, upstream_failures = (
        _load_upstreams(
            repo_root=root,
            registry_path=registry_path,
            registry_schema_path=registry_schema_path,
            registry_report_path=registry_report_path,
            consumer_gate_schema_path=consumer_gate_schema_path,
            consumer_gate_report_path=consumer_gate_report_path,
            owner_global_override_policy_path=owner_global_override_policy_path,
            owner_global_override_schema_path=owner_global_override_schema_path,
            owner_global_override_report_path=owner_global_override_report_path,
        )
    )
    failures.extend(upstream_failures)

    report = build_report(
        repo_root=root,
        binding_report=binding_report,
        consumer_report=consumer_report,
        owner_report=owner_report,
        owner_policy=owner_policy,
    )
    second_report = build_report(
        repo_root=root,
        binding_report=binding_report,
        consumer_report=consumer_report,
        owner_report=owner_report,
        owner_policy=owner_policy,
    )
    if report != second_report:
        failures.append("generated cumulative readiness report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if fixture is not None and isinstance(fixture.get("expected_report"), dict):
        expected_report = dict(fixture["expected_report"])
        report_compare = dict(report)
        expected_report["bundle_file_present"] = report_compare.get(
            "bundle_file_present"
        )
        if expected_report != report_compare:
            failures.append("fixture.expected_report does not match deterministic report")

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: AtomicRows parameter-agent binding full coverage "
            "and bundle readiness are not complete"
        )

    if output_path is not None and not failures:
        write_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"static_foundation={report.get('static_binding_foundation_ready', False)} "
            f"owner_override_ready="
            f"{report.get('owner_override_satisfies_binding_readiness', False)} "
            f"qtt_internal_ready="
            f"{report.get('qtt_internal_binding_cumulative_ready', False)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
