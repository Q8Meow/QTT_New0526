#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder  # noqa: E402
from tools import validate_atomicrows_parameter_agent_binding_registry as binding_registry  # noqa: E402
from tools.build_master_plan_section_coverage_report import RegistryParseError  # noqa: E402
from tools.build_master_plan_section_coverage_report import load_yaml_subset  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_agent_binding_consumer_gate.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_agent_binding_consumer_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterAgentBindingConsumerGate.report.json"
)

DEFAULT_REGISTRY = binding_registry.DEFAULT_REGISTRY
DEFAULT_BINDING_REPORT = binding_registry.DEFAULT_REPORT
OWNER_AUTHORITY_PATH = (
    pathlib.Path("docs")
    / "master_plan"
    / "governance"
    / "QTTOwnerGlobalOverrideAuthority.yaml"
)
OWNER_AUTHORITY_SCHEMA = (
    pathlib.Path("schemas")
    / "governance"
    / "qtt_owner_global_override_authority.schema.json"
)
OWNER_AUTHORITY_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTOwnerGlobalOverrideAuthority.report.json"
)

RELATED_ATOMICROWS_REPORTS = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterLifecycleReport.json",
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleConsumerGate.report.json",
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecyclePromotionReceiptGate.report.json",
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleRegistryMutationGuard.report.json",
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleCumulativeReadinessGate.report.json",
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleGateCommandMatrix.json",
)

CANONICAL_BUNDLE = binding_registry.CANONICAL_BUNDLE
CANONICAL_BUNDLE_SHA = binding_registry.CANONICAL_BUNDLE_SHA

REPORT_TYPE = "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_FINAL_INCOMPLETE"
)
VALIDATION_HOOK = "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_STATIC_VALIDATION"

AGENT_ROLES = binding_registry.AGENT_ROLES
CONSUMER_CLASSES = binding_registry.CONSUMER_CLASSES
AGENT_USE_SCOPES = binding_registry.AGENT_USE_SCOPES

ACCESS_DECISIONS = (
    "ALLOWED_BY_BINDING",
    "ALLOWED_BY_OWNER_APPROVED_BINDING",
    "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE",
    "ALLOWED_BY_AGENT_ASSIGNMENT_OWNER_APPROVED",
    "ALLOWED_BY_OWNER_OVERRIDE_SATISFIED",
    "ALLOWED_BY_ROW_BINDING",
    "ALLOWED_BY_PATTERN_BINDING",
    "ALLOWED_BY_FAMILY_BINDING",
    "ALLOWED_BY_AGENT_ID_BINDING",
    "ALLOWED_BY_QUARANTINE_REVIEW_BINDING",
    "ALLOWED_BY_RETIREMENT_AUDIT_BINDING",
    "BLOCKED_MISSING_BINDING",
    "BLOCKED_UNAUTHORIZED_AGENT_ROLE",
    "BLOCKED_UNAUTHORIZED_AGENT_ID",
    "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_UNKNOWN_AGENT_ROLE",
    "BLOCKED_UNKNOWN_CONSUMER_CLASS",
    "BLOCKED_QUARANTINE",
    "BLOCKED_RETIRED",
    "BLOCKED_PARAMETER_TARGET_UNKNOWN",
    "INVALID_ATTEMPT",
)

ALLOWED_ACCESS_DECISIONS = {
    decision for decision in ACCESS_DECISIONS if decision.startswith("ALLOWED_")
}
BLOCKED_ACCESS_DECISIONS = {
    decision for decision in ACCESS_DECISIONS if decision.startswith("BLOCKED_")
}

BINDING_LOOKUP_STATUSES = (
    "MATCHED_FAMILY_BINDING",
    "MATCHED_ROW_BINDING",
    "MATCHED_PATTERN_BINDING",
    "MATCHED_AGENT_ROLE_BINDING",
    "MATCHED_AGENT_ID_BINDING",
    "MATCHED_OWNER_APPROVED_BINDING",
    "MATCHED_OWNER_GLOBAL_OVERRIDE_BINDING",
    "MATCHED_AGENT_ASSIGNMENT_OWNER_APPROVED_BINDING",
    "MISSING_BINDING_NORMAL_BLOCK",
    "MISSING_BINDING_OWNER_OVERRIDE_SATISFIED",
    "UNKNOWN_PARAMETER_TARGET",
    "UNKNOWN_AGENT_ROLE",
    "UNKNOWN_AGENT_ID",
    "UNKNOWN_CONSUMER_CLASS",
    "QUARANTINE_REVIEW_MATCH",
    "RETIREMENT_AUDIT_MATCH",
)

OWNER_OVERRIDE_SATISFACTION_BASES = (
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_APPROVED",
    "OWNER_APPROVED_OVERRIDE",
    "OWNER_OVERRIDE_SATISFIED",
    "AGENT_ASSIGNMENT_OWNER_APPROVED",
    "OWNER_APPROVED_NOT_EXTERNALLY_VERIFIED",
    "OWNER_APPROVED_UNVERIFIED",
    "OWNER_RISK_ACCEPTED",
    "OWNER_ASSUMED_RESPONSIBILITY",
    "OWNER_WAIVED_REQUIREMENT",
    "OWNER_APPROVED_MISSING_VALUE",
)
OWNER_OVERRIDE_FINAL_STATUSES = {
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED",
    "OWNER_APPROVED_OVERRIDE",
    "OWNER_GLOBAL_OVERRIDE",
    "AGENT_ASSIGNMENT_OWNER_APPROVED",
}
OWNER_OVERRIDE_ALLOWED_DECISIONS = {
    "ALLOWED_BY_OWNER_APPROVED_BINDING",
    "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE",
    "ALLOWED_BY_AGENT_ASSIGNMENT_OWNER_APPROVED",
    "ALLOWED_BY_OWNER_OVERRIDE_SATISFIED",
}

ATTEMPT_FIELDS = (
    "attempted_access_id",
    "parameter_family",
    "atomic_parameter_row_id",
    "row_pattern_id",
    "requesting_agent_role",
    "requesting_agent_id",
    "requested_consumer_class",
    "requested_use_scope",
    "matching_binding_id",
    "binding_lookup_status",
    "binding_authority_basis",
    "owner_override_applied",
    "owner_override_satisfaction_basis",
    "owner_approved_value",
    "final_qtt_internal_status",
    "access_decision",
    "blocked_reason",
    "blocks_qtt_when_owner_override_present",
    "normal_access_would_block",
    "owner_override_resolved_block",
    "registry_binding_required",
    "binding_registry_path",
    "upstream_owner_authority_path",
    "real_runtime_artifact_created",
    "real_live_artifact_created",
    "real_order_artifact_created",
    "real_quantum_backend_artifact_created",
    "real_profit_artifact_created",
    "notes",
)

ROOT_FIELDS = (
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "deterministic_output",
    "generated_at_utc",
    "binding_registry_path",
    "binding_report_path",
    "owner_global_override_report_path",
    "agent_roles",
    "consumer_classes",
    "agent_use_scopes",
    "access_decisions",
    "binding_lookup_statuses",
    "owner_override_satisfaction_bases",
    "authority_boundary",
    "validation_hook_ids",
    "attempted_access",
)

AUTHORITY_BOUNDARY_FIELDS = (
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
    "uses_pr_number_as_authority",
)

REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "binding_registry_present",
    "binding_registry_path",
    "binding_report_present",
    "owner_global_override_report_present",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "attempted_access_count",
    "allowed_access_count",
    "blocked_access_count",
    "invalid_access_count",
    "allowed_by_binding_count",
    "allowed_by_owner_approved_binding_count",
    "allowed_by_owner_global_override_count",
    "allowed_by_agent_assignment_owner_approved_count",
    "allowed_by_owner_override_satisfied_count",
    "allowed_by_row_binding_count",
    "allowed_by_pattern_binding_count",
    "allowed_by_family_binding_count",
    "allowed_by_agent_id_binding_count",
    "allowed_by_quarantine_review_count",
    "allowed_by_retirement_audit_count",
    "blocked_missing_binding_count",
    "missing_binding_owner_override_satisfied_count",
    "blocked_unauthorized_agent_role_count",
    "unauthorized_agent_role_owner_override_satisfied_count",
    "blocked_unauthorized_agent_id_count",
    "unauthorized_agent_id_owner_override_satisfied_count",
    "blocked_unauthorized_consumer_class_count",
    "unauthorized_consumer_class_owner_override_satisfied_count",
    "blocked_scope_mismatch_count",
    "scope_mismatch_owner_override_satisfied_count",
    "blocked_quarantine_count",
    "quarantine_review_allowed_count",
    "blocked_retired_count",
    "retirement_audit_allowed_count",
    "unknown_agent_role_count",
    "unknown_consumer_class_count",
    "unknown_parameter_target_count",
    "unknown_parameter_target_owner_override_satisfied_count",
    "row_level_access_allowed_count",
    "pattern_level_access_allowed_count",
    "family_level_access_allowed_count",
    "agent_role_level_access_allowed_count",
    "agent_id_level_access_allowed_count",
    "runtime_consumer_access_allowed_count",
    "live_consumer_access_allowed_count",
    "quantum_backend_consumer_access_allowed_count",
    "optimizer_consumer_access_allowed_count",
    "risk_consumer_access_allowed_count",
    "sizing_consumer_access_allowed_count",
    "replay_paper_consumer_access_allowed_count",
    "source_evidence_consumer_access_allowed_count",
    "research_consumer_access_allowed_count",
    "owner_override_access_attempt_count",
    "owner_override_access_allowed_count",
    "owner_override_access_blocked_count",
    "validators_block_owner_override_count",
    "codex_blocks_owner_override_count",
    "qtt_agents_block_owner_override_count",
    "generated_reports_block_owner_override_count",
    "validation_gates_block_owner_override_count",
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
    "uses_pr_number_as_authority",
    "final_ready",
    "authority_boundary_all_false",
)

PR_NUMBER_PATTERN = re.compile(
    r"\bPR\s*#?\s*\d+\b|(?<![A-Za-z])pr\d+\b",
    re.IGNORECASE,
)
ATTEMPT_ID_PATTERN = re.compile(r"^attempt_[0-9]{3}_[a-z0-9_]+$")


@dataclass(frozen=True)
class AccessEvaluation:
    attempt: dict[str, Any]
    expected_decisions: frozenset[str]
    expected_blocked_reason: str | None
    expected_binding_id: str | None
    matched_binding: dict[str, Any] | None
    invalid_reasons: tuple[str, ...]

    @property
    def invalid(self) -> bool:
        return bool(self.invalid_reasons)

    @property
    def declared_decision(self) -> str:
        return str(self.attempt.get("access_decision"))

    @property
    def declared_allowed(self) -> bool:
        return self.declared_decision in ALLOWED_ACCESS_DECISIONS

    @property
    def declared_blocked(self) -> bool:
        return self.declared_decision in BLOCKED_ACCESS_DECISIONS


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _present_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def _uses_pr_number(value: Any) -> bool:
    if isinstance(value, str):
        return PR_NUMBER_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_uses_pr_number(item) for item in value.values())
    if isinstance(value, list):
        return any(_uses_pr_number(item) for item in value)
    return False


def _owner_override_present(attempt: dict[str, Any]) -> bool:
    basis_values = {
        attempt.get("owner_override_satisfaction_basis"),
        attempt.get("binding_authority_basis"),
        attempt.get("owner_approved_value"),
        attempt.get("final_qtt_internal_status"),
    }
    explicit_basis = set(OWNER_OVERRIDE_SATISFACTION_BASES) - {"OWNER_APPROVED"}
    return attempt.get("owner_override_applied") is True or bool(
        explicit_basis & {str(value) for value in basis_values if value}
    )


def _target_missing(attempt: dict[str, Any]) -> bool:
    return not any(
        _present_string(attempt.get(field))
        for field in ("parameter_family", "atomic_parameter_row_id", "row_pattern_id")
    )


def _binding_matches_attempt(binding: dict[str, Any], attempt: dict[str, Any]) -> bool:
    for field in ("atomic_parameter_row_id", "row_pattern_id", "parameter_family"):
        value = attempt.get(field)
        if _present_string(value) and binding.get(field) == value:
            return True
    return False


def _find_binding(
    registry: dict[str, Any],
    attempt: dict[str, Any],
) -> dict[str, Any] | None:
    bindings = registry.get("bindings")
    if not isinstance(bindings, list):
        return None
    matches = [
        binding
        for binding in bindings
        if isinstance(binding, dict) and _binding_matches_attempt(binding, attempt)
    ]
    if not matches:
        return None
    binding_id = attempt.get("matching_binding_id")
    if _present_string(binding_id):
        for binding in matches:
            if binding.get("binding_id") == binding_id:
                return binding
    return sorted(matches, key=lambda item: str(item.get("binding_id") or ""))[0]


def _identity_unknown(attempt: dict[str, Any]) -> bool:
    values = [
        attempt.get("parameter_family"),
        attempt.get("atomic_parameter_row_id"),
        attempt.get("row_pattern_id"),
    ]
    return any(
        isinstance(value, str) and value.startswith("UNKNOWN_") for value in values
    )


def _normal_allowed_decisions(
    binding: dict[str, Any],
    attempt: dict[str, Any],
) -> set[str]:
    decisions = {"ALLOWED_BY_BINDING"}
    if _present_string(attempt.get("parameter_family")):
        decisions.add("ALLOWED_BY_FAMILY_BINDING")
    if _present_string(attempt.get("atomic_parameter_row_id")) and binding.get(
        "atomic_parameter_row_id"
    ) == attempt.get("atomic_parameter_row_id"):
        decisions.add("ALLOWED_BY_ROW_BINDING")
    if _present_string(attempt.get("row_pattern_id")) and binding.get(
        "row_pattern_id"
    ) == attempt.get("row_pattern_id"):
        decisions.add("ALLOWED_BY_PATTERN_BINDING")
    if _present_string(attempt.get("requesting_agent_id")) and attempt.get(
        "requesting_agent_id"
    ) in binding.get("authorized_agent_ids", []):
        decisions.add("ALLOWED_BY_AGENT_ID_BINDING")
    if binding.get("binding_status") == "OWNER_APPROVED_BINDING":
        decisions.add("ALLOWED_BY_OWNER_APPROVED_BINDING")
    return decisions


def _expected_decision_for_owner_override(attempt: dict[str, Any]) -> set[str]:
    basis = attempt.get("owner_override_satisfaction_basis")
    authority_basis = attempt.get("binding_authority_basis")
    if basis == "AGENT_ASSIGNMENT_OWNER_APPROVED":
        return {"ALLOWED_BY_AGENT_ASSIGNMENT_OWNER_APPROVED"}
    if authority_basis == "OWNER_GLOBAL_OVERRIDE" and attempt.get(
        "access_decision"
    ) == "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE":
        return {"ALLOWED_BY_OWNER_GLOBAL_OVERRIDE"}
    return {"ALLOWED_BY_OWNER_OVERRIDE_SATISFIED"}


def _evaluate_one(
    *,
    registry: dict[str, Any],
    attempt: dict[str, Any],
    label: str,
) -> AccessEvaluation:
    invalid_reasons: list[str] = []
    owner_override = _owner_override_present(attempt)
    role = attempt.get("requesting_agent_role")
    consumer_class = attempt.get("requested_consumer_class")
    scope = attempt.get("requested_use_scope")
    matched_binding = _find_binding(registry, attempt)
    expected_binding_id = (
        str(matched_binding.get("binding_id")) if matched_binding is not None else None
    )

    if _target_missing(attempt):
        if not owner_override:
            return AccessEvaluation(
                attempt,
                frozenset({"INVALID_ATTEMPT"}),
                "INVALID_ATTEMPT",
                None,
                None,
                tuple(invalid_reasons),
            )
        if attempt.get("owner_override_satisfaction_basis") not in {
            "OWNER_APPROVED_MISSING_VALUE",
            "OWNER_GLOBAL_OVERRIDE",
            "OWNER_OVERRIDE_SATISFIED",
        }:
            invalid_reasons.append(
                f"{label}: missing parameter target requires owner-approved missing value"
            )
        return AccessEvaluation(
            attempt,
            frozenset({"ALLOWED_BY_OWNER_OVERRIDE_SATISFIED"}),
            "BLOCKED_PARAMETER_TARGET_UNKNOWN",
            None,
            None,
            tuple(invalid_reasons),
        )

    if role not in AGENT_ROLES:
        if owner_override:
            return AccessEvaluation(
                attempt,
                frozenset(_expected_decision_for_owner_override(attempt)),
                "BLOCKED_UNKNOWN_AGENT_ROLE",
                expected_binding_id,
                matched_binding,
                tuple(invalid_reasons),
            )
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_UNKNOWN_AGENT_ROLE"}),
            "BLOCKED_UNKNOWN_AGENT_ROLE",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    if consumer_class not in CONSUMER_CLASSES:
        if owner_override:
            return AccessEvaluation(
                attempt,
                frozenset(_expected_decision_for_owner_override(attempt)),
                "BLOCKED_UNKNOWN_CONSUMER_CLASS",
                expected_binding_id,
                matched_binding,
                tuple(invalid_reasons),
            )
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_UNKNOWN_CONSUMER_CLASS"}),
            "BLOCKED_UNKNOWN_CONSUMER_CLASS",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    if scope not in AGENT_USE_SCOPES:
        invalid_reasons.append(f"{label}: requested_use_scope is not allowed")

    if matched_binding is None:
        if owner_override:
            expected = (
                {"ALLOWED_BY_OWNER_GLOBAL_OVERRIDE"}
                if attempt.get("binding_authority_basis") == "OWNER_GLOBAL_OVERRIDE"
                and attempt.get("access_decision") == "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE"
                else {"ALLOWED_BY_OWNER_OVERRIDE_SATISFIED"}
            )
            normal_reason = (
                "BLOCKED_PARAMETER_TARGET_UNKNOWN"
                if _identity_unknown(attempt)
                else "BLOCKED_MISSING_BINDING"
            )
            return AccessEvaluation(
                attempt,
                frozenset(expected),
                normal_reason,
                None,
                None,
                tuple(invalid_reasons),
            )
        normal_decision = (
            "BLOCKED_PARAMETER_TARGET_UNKNOWN"
            if _identity_unknown(attempt)
            else "BLOCKED_MISSING_BINDING"
        )
        return AccessEvaluation(
            attempt,
            frozenset({normal_decision}),
            normal_decision,
            None,
            None,
            tuple(invalid_reasons),
        )

    status = matched_binding.get("binding_status")
    authorized_roles = matched_binding.get("authorized_agent_roles", [])
    authorized_ids = matched_binding.get("authorized_agent_ids", [])
    blocked_roles = matched_binding.get("blocked_agent_roles", [])
    blocked_ids = matched_binding.get("blocked_agent_ids", [])
    authorized_consumers = matched_binding.get("authorized_consumer_classes", [])
    blocked_consumers = matched_binding.get("blocked_consumer_classes", [])
    binding_scope = matched_binding.get("agent_use_scope")

    if owner_override:
        if status == "OWNER_GLOBAL_OVERRIDE_BINDING" or attempt.get(
            "binding_authority_basis"
        ) == "OWNER_GLOBAL_OVERRIDE":
            if attempt.get("access_decision") == "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE":
                return AccessEvaluation(
                    attempt,
                    frozenset({"ALLOWED_BY_OWNER_GLOBAL_OVERRIDE"}),
                    attempt.get("blocked_reason"),
                    expected_binding_id,
                    matched_binding,
                    tuple(invalid_reasons),
                )
        return AccessEvaluation(
            attempt,
            frozenset(_expected_decision_for_owner_override(attempt)),
            attempt.get("blocked_reason"),
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    if status == "QUARANTINED_BINDING":
        if (
            scope == "QUARANTINE_REVIEW_ONLY"
            and role in authorized_roles
            and consumer_class in authorized_consumers
        ):
            return AccessEvaluation(
                attempt,
                frozenset({"ALLOWED_BY_QUARANTINE_REVIEW_BINDING"}),
                None,
                expected_binding_id,
                matched_binding,
                tuple(invalid_reasons),
            )
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_QUARANTINE"}),
            "BLOCKED_QUARANTINE",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    if status == "RETIRED_BINDING":
        if (
            scope == "RETIREMENT_AUDIT_ONLY"
            and role in authorized_roles
            and consumer_class in authorized_consumers
        ):
            return AccessEvaluation(
                attempt,
                frozenset({"ALLOWED_BY_RETIREMENT_AUDIT_BINDING"}),
                None,
                expected_binding_id,
                matched_binding,
                tuple(invalid_reasons),
            )
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_RETIRED"}),
            "BLOCKED_RETIRED",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    if role in blocked_roles or (
        authorized_roles and role not in authorized_roles and not authorized_ids
    ):
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_UNAUTHORIZED_AGENT_ROLE"}),
            "BLOCKED_UNAUTHORIZED_AGENT_ROLE",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    agent_id = attempt.get("requesting_agent_id")
    if _present_string(agent_id):
        if agent_id in blocked_ids:
            return AccessEvaluation(
                attempt,
                frozenset({"BLOCKED_UNAUTHORIZED_AGENT_ID"}),
                "BLOCKED_UNAUTHORIZED_AGENT_ID",
                expected_binding_id,
                matched_binding,
                tuple(invalid_reasons),
            )
        if authorized_ids and agent_id not in authorized_ids:
            return AccessEvaluation(
                attempt,
                frozenset({"BLOCKED_UNAUTHORIZED_AGENT_ID"}),
                "BLOCKED_UNAUTHORIZED_AGENT_ID",
                expected_binding_id,
                matched_binding,
                tuple(invalid_reasons),
            )

    if consumer_class in blocked_consumers or consumer_class not in authorized_consumers:
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_UNAUTHORIZED_CONSUMER_CLASS"}),
            "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    if scope != binding_scope:
        return AccessEvaluation(
            attempt,
            frozenset({"BLOCKED_SCOPE_MISMATCH"}),
            "BLOCKED_SCOPE_MISMATCH",
            expected_binding_id,
            matched_binding,
            tuple(invalid_reasons),
        )

    return AccessEvaluation(
        attempt,
        frozenset(_normal_allowed_decisions(matched_binding, attempt)),
        None,
        expected_binding_id,
        matched_binding,
        tuple(invalid_reasons),
    )


def _allowed_lookup_statuses(
    evaluation: AccessEvaluation,
) -> set[str]:
    attempt = evaluation.attempt
    decision = evaluation.declared_decision
    binding = evaluation.matched_binding
    if decision == "BLOCKED_UNKNOWN_AGENT_ROLE":
        return {"UNKNOWN_AGENT_ROLE"}
    if decision == "BLOCKED_UNKNOWN_CONSUMER_CLASS":
        return {"UNKNOWN_CONSUMER_CLASS"}
    if decision == "BLOCKED_PARAMETER_TARGET_UNKNOWN":
        return {"UNKNOWN_PARAMETER_TARGET"}
    if decision == "BLOCKED_MISSING_BINDING":
        return {"MISSING_BINDING_NORMAL_BLOCK"}
    if decision == "BLOCKED_QUARANTINE":
        return {"QUARANTINE_REVIEW_MATCH", "MATCHED_FAMILY_BINDING"}
    if decision == "BLOCKED_RETIRED":
        return {"RETIREMENT_AUDIT_MATCH", "MATCHED_FAMILY_BINDING"}
    if binding is None:
        if _identity_unknown(attempt) or _target_missing(attempt):
            return {"UNKNOWN_PARAMETER_TARGET", "MISSING_BINDING_OWNER_OVERRIDE_SATISFIED"}
        return {"MISSING_BINDING_OWNER_OVERRIDE_SATISFIED"}
    if decision == "ALLOWED_BY_QUARANTINE_REVIEW_BINDING":
        return {"QUARANTINE_REVIEW_MATCH"}
    if decision == "ALLOWED_BY_RETIREMENT_AUDIT_BINDING":
        return {"RETIREMENT_AUDIT_MATCH"}
    if decision == "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE":
        return {"MATCHED_OWNER_GLOBAL_OVERRIDE_BINDING", "MISSING_BINDING_OWNER_OVERRIDE_SATISFIED"}
    if decision == "ALLOWED_BY_AGENT_ASSIGNMENT_OWNER_APPROVED":
        return {"MATCHED_AGENT_ASSIGNMENT_OWNER_APPROVED_BINDING"}
    statuses: set[str] = set()
    if _present_string(attempt.get("atomic_parameter_row_id")):
        statuses.add("MATCHED_ROW_BINDING")
    if _present_string(attempt.get("row_pattern_id")):
        statuses.add("MATCHED_PATTERN_BINDING")
    if _present_string(attempt.get("parameter_family")):
        statuses.add("MATCHED_FAMILY_BINDING")
    if _present_string(attempt.get("requesting_agent_id")):
        statuses.add("MATCHED_AGENT_ID_BINDING")
    if attempt.get("requesting_agent_role") in binding.get("authorized_agent_roles", []):
        statuses.add("MATCHED_AGENT_ROLE_BINDING")
    if binding.get("binding_status") == "OWNER_APPROVED_BINDING":
        statuses.add("MATCHED_OWNER_APPROVED_BINDING")
    if binding.get("binding_status") == "OWNER_GLOBAL_OVERRIDE_BINDING":
        statuses.add("MATCHED_OWNER_GLOBAL_OVERRIDE_BINDING")
    if not statuses:
        statuses.add("MATCHED_AGENT_ROLE_BINDING")
    return statuses


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    expectations = {
        "agent_role": list(AGENT_ROLES),
        "consumer_class": list(CONSUMER_CLASSES),
        "agent_use_scope": list(AGENT_USE_SCOPES),
        "access_decision": list(ACCESS_DECISIONS),
        "binding_lookup_status": list(BINDING_LOOKUP_STATUSES),
        "owner_override_satisfaction_basis": list(OWNER_OVERRIDE_SATISFACTION_BASES),
        "owner_override_final_status": sorted(OWNER_OVERRIDE_FINAL_STATUSES),
    }
    for name, expected in expectations.items():
        item = defs.get(name)
        if not isinstance(item, dict) or item.get("enum") != expected:
            failures.append(f"schema.$defs.{name} must contain the exact enum")
    attempt_schema = defs.get("attempted_access")
    if isinstance(attempt_schema, dict):
        if attempt_schema.get("required") != list(ATTEMPT_FIELDS):
            failures.append("schema.$defs.attempted_access.required is not exact")
    else:
        failures.append("schema.$defs.attempted_access must be an object")
    report_schema = defs.get("consumer_gate_report")
    if isinstance(report_schema, dict):
        if report_schema.get("required") != list(_empty_report()):
            failures.append("schema.$defs.consumer_gate_report.required is not exact")
    else:
        failures.append("schema.$defs.consumer_gate_report must be an object")
    return failures


def _validate_fixture_shape(
    *,
    fixture: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(fixture, set(ROOT_FIELDS), "fixture")
    expected_values: dict[str, Any] = {
        "fixture_id": "SYNTHETIC_ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_FIXTURE",
        "fixture_version": "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_FIXTURE_V1",
        "fixture_authority_class": (
            "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_PARAMETER_CONSUMER_AUTHORITY"
        ),
        "schema_authority_class": (
            "STATIC_SCHEMA_CONTRACT_ONLY_NOT_PARAMETER_CONSUMER_AUTHORITY"
        ),
        "surface_kind": "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE_STATIC",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "binding_registry_path": str(DEFAULT_REGISTRY).replace("\\", "/"),
        "binding_report_path": str(DEFAULT_BINDING_REPORT).replace("\\", "/"),
        "owner_global_override_report_path": str(OWNER_AUTHORITY_REPORT).replace(
            "\\", "/"
        ),
        "agent_roles": list(AGENT_ROLES),
        "consumer_classes": list(CONSUMER_CLASSES),
        "agent_use_scopes": list(AGENT_USE_SCOPES),
        "access_decisions": list(ACCESS_DECISIONS),
        "binding_lookup_statuses": list(BINDING_LOOKUP_STATUSES),
        "owner_override_satisfaction_bases": list(OWNER_OVERRIDE_SATISFACTION_BASES),
        "validation_hook_ids": [VALIDATION_HOOK],
    }
    for field, expected in expected_values.items():
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")

    boundary = fixture.get("authority_boundary")
    if not isinstance(boundary, dict):
        failures.append("fixture.authority_boundary must be an object")
    else:
        failures.extend(
            _require_exact_fields(
                boundary,
                set(AUTHORITY_BOUNDARY_FIELDS),
                "fixture.authority_boundary",
            )
        )
        for field in AUTHORITY_BOUNDARY_FIELDS:
            if boundary.get(field) is not False:
                failures.append(f"fixture.authority_boundary.{field} must remain false")

    attempts = fixture.get("attempted_access")
    if not isinstance(attempts, list) or len(attempts) < 38:
        failures.append("fixture.attempted_access must contain at least 38 records")
    elif len(attempts) != 38:
        failures.append("fixture.attempted_access must contain exactly 38 records")
    else:
        seen: set[str] = set()
        expected_prefixes = [f"attempt_{index:03d}_" for index in range(1, 39)]
        for index, attempt in enumerate(attempts):
            label = f"fixture.attempted_access[{index}]"
            if not isinstance(attempt, dict):
                failures.append(f"{label} must be an object")
                continue
            failures.extend(_require_exact_fields(attempt, set(ATTEMPT_FIELDS), label))
            attempt_id = attempt.get("attempted_access_id")
            if not _present_string(attempt_id):
                failures.append(f"{label}.attempted_access_id must be a non-empty string")
            elif str(attempt_id) in seen:
                failures.append(f"{label}.attempted_access_id is duplicated")
            else:
                seen.add(str(attempt_id))
            if _present_string(attempt_id):
                if not ATTEMPT_ID_PATTERN.match(str(attempt_id)):
                    failures.append(f"{label}.attempted_access_id is not deterministic")
                if not str(attempt_id).startswith(expected_prefixes[index]):
                    failures.append(
                        f"{label}.attempted_access_id does not preserve fixture order"
                    )
            if attempt.get("binding_lookup_status") not in BINDING_LOOKUP_STATUSES:
                failures.append(f"{label}.binding_lookup_status is not allowed")
            if attempt.get("access_decision") not in ACCESS_DECISIONS:
                failures.append(f"{label}.access_decision is not allowed")
            if attempt.get("requested_use_scope") not in AGENT_USE_SCOPES:
                failures.append(f"{label}.requested_use_scope is not allowed")
            if attempt.get("binding_registry_path") != str(DEFAULT_REGISTRY).replace(
                "\\", "/"
            ):
                failures.append(f"{label}.binding_registry_path is not canonical")
            if attempt.get("upstream_owner_authority_path") != str(
                OWNER_AUTHORITY_REPORT
            ).replace("\\", "/"):
                failures.append(f"{label}.upstream_owner_authority_path is not canonical")
            for field in (
                "owner_override_applied",
                "blocks_qtt_when_owner_override_present",
                "normal_access_would_block",
                "owner_override_resolved_block",
                "registry_binding_required",
                "real_runtime_artifact_created",
                "real_live_artifact_created",
                "real_order_artifact_created",
                "real_quantum_backend_artifact_created",
                "real_profit_artifact_created",
            ):
                if not isinstance(attempt.get(field), bool):
                    failures.append(f"{label}.{field} must be boolean")
    if _uses_pr_number(fixture):
        failures.append("fixture must not use a pull request number as authority")
    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_upstream_foundations(
    *,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    binding_report_path: pathlib.Path,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    registry: dict[str, Any] | None = None
    owner_report: dict[str, Any] | None = None
    try:
        registry = binding_registry.load_registry(repo_root / registry_path)
    except (OSError, RegistryParseError) as exc:
        failures.append(f"binding registry is missing or invalid: {exc}")

    binding_report, binding_report_failures = _load_json(repo_root / binding_report_path)
    failures.extend(binding_report_failures)
    if binding_report is not None:
        if binding_report.get("report_type") != binding_registry.REPORT_TYPE:
            failures.append("binding report has unexpected report_type")
        if binding_report.get("deterministic_output") is not True:
            failures.append("binding report deterministic_output must be true")
        if binding_report.get("authority_boundary_all_false") is not True:
            failures.append("binding report authority_boundary_all_false must be true")

    if not (repo_root / OWNER_AUTHORITY_PATH).exists():
        failures.append(f"owner authority policy is missing: {OWNER_AUTHORITY_PATH}")
    if not (repo_root / OWNER_AUTHORITY_SCHEMA).exists():
        failures.append(f"owner authority schema is missing: {OWNER_AUTHORITY_SCHEMA}")
    try:
        owner_policy = load_yaml_subset(repo_root / OWNER_AUTHORITY_PATH)
    except (OSError, RegistryParseError) as exc:
        failures.append(f"owner authority policy is invalid: {exc}")
    else:
        if owner_policy.get("owner_global_override_authority") is not True:
            failures.append("owner authority policy must allow owner global override")
        if (
            owner_policy.get("owner_override_satisfies_all_qtt_internal_requirements")
            is not True
        ):
            failures.append("owner authority policy must satisfy internal requirements")

    owner_report, owner_failures = _load_json(repo_root / OWNER_AUTHORITY_REPORT)
    failures.extend(owner_failures)
    if owner_report is not None:
        for field in (
            "owner_global_override_authority",
            "owner_override_satisfies_all_qtt_internal_requirements",
            "validators_must_not_block_owner_override",
            "codex_must_not_block_owner_override",
            "qtt_agents_must_not_block_owner_override",
            "generated_reports_must_not_block_owner_override",
            "validation_gates_must_not_block_owner_override",
            "agent_assignment_override_supported",
            "atomicrows_override_supported",
            "missing_required_value_override_supported",
        ):
            if owner_report.get(field) is not True:
                failures.append(f"owner authority report.{field} must be true")
        for field in (
            "validators_block_owner_override_count",
            "codex_blocks_owner_override_count",
            "qtt_agents_block_owner_override_count",
            "generated_reports_block_owner_override_count",
            "validation_gates_block_owner_override_count",
        ):
            if owner_report.get(field, 0) != 0:
                failures.append(f"owner authority report.{field} must be 0")
    for report_path in RELATED_ATOMICROWS_REPORTS:
        report, report_failures = _load_json(repo_root / report_path)
        failures.extend(report_failures)
        if report is not None and report.get("deterministic_output") is False:
            failures.append(f"{report_path.as_posix()} must be deterministic")
    return registry, owner_report, failures


def _evaluate_attempts(
    *,
    registry: dict[str, Any],
    fixture: dict[str, Any],
) -> tuple[list[AccessEvaluation], list[str]]:
    attempts = fixture.get("attempted_access")
    if not isinstance(attempts, list):
        return [], ["fixture.attempted_access must be a list"]
    evaluations: list[AccessEvaluation] = []
    failures: list[str] = []
    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, dict):
            continue
        label = f"attempted_access[{index}] {attempt.get('attempted_access_id')}"
        evaluation = _evaluate_one(registry=registry, attempt=attempt, label=label)
        evaluations.append(evaluation)
        failures.extend(evaluation.invalid_reasons)

        decision = attempt.get("access_decision")
        owner_override = _owner_override_present(attempt)
        if decision not in evaluation.expected_decisions:
            failures.append(
                f"{label}: access_decision {decision} is not one of "
                f"{sorted(evaluation.expected_decisions)}"
            )

        if attempt.get("matching_binding_id") != evaluation.expected_binding_id:
            failures.append(
                f"{label}: matching_binding_id must be {evaluation.expected_binding_id}"
            )

        lookup_status = attempt.get("binding_lookup_status")
        if lookup_status not in _allowed_lookup_statuses(evaluation):
            failures.append(f"{label}: binding_lookup_status {lookup_status} is invalid")

        if evaluation.expected_blocked_reason is None:
            if attempt.get("blocked_reason") is not None:
                failures.append(f"{label}: blocked_reason must be null")
        elif attempt.get("blocked_reason") != evaluation.expected_blocked_reason:
            failures.append(
                f"{label}: blocked_reason must be {evaluation.expected_blocked_reason}"
            )

        if owner_override:
            if decision in BLOCKED_ACCESS_DECISIONS:
                failures.append(f"{label}: owner override access may not remain blocked")
            if attempt.get("blocks_qtt_when_owner_override_present") is not False:
                failures.append(
                    f"{label}: blocks_qtt_when_owner_override_present must be false"
                )
            if attempt.get("final_qtt_internal_status") not in OWNER_OVERRIDE_FINAL_STATUSES:
                failures.append(
                    f"{label}: owner override final status is not owner-satisfied"
                )
            if attempt.get("normal_access_would_block") is True and attempt.get(
                "owner_override_resolved_block"
            ) is not True:
                failures.append(f"{label}: owner override did not resolve normal block")
        else:
            if decision in BLOCKED_ACCESS_DECISIONS and attempt.get(
                "owner_override_resolved_block"
            ) is True:
                failures.append(
                    f"{label}: owner_override_resolved_block requires owner override"
                )
            if decision in BLOCKED_ACCESS_DECISIONS and attempt.get(
                "blocks_qtt_when_owner_override_present"
            ) is not False:
                failures.append(
                    f"{label}: blocked normal access still may not block owner override"
                )
            if decision in ALLOWED_ACCESS_DECISIONS and attempt.get(
                "normal_access_would_block"
            ) is True:
                failures.append(
                    f"{label}: normal allowed access may not declare normal block"
                )

        if decision in BLOCKED_ACCESS_DECISIONS and owner_override:
            failures.append(f"{label}: blocked decisions are invalid with owner override")

        if decision in ALLOWED_ACCESS_DECISIONS and attempt.get("blocked_reason") in {
            "BLOCKED_MISSING_BINDING",
            "BLOCKED_UNAUTHORIZED_AGENT_ROLE",
            "BLOCKED_UNAUTHORIZED_AGENT_ID",
            "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
            "BLOCKED_SCOPE_MISMATCH",
            "BLOCKED_PARAMETER_TARGET_UNKNOWN",
        } and not owner_override:
            failures.append(f"{label}: normal blocker allowed without owner override")

        if attempt.get("registry_binding_required") is not True:
            failures.append(f"{label}: registry_binding_required must be true")

        for field in (
            "real_runtime_artifact_created",
            "real_live_artifact_created",
            "real_order_artifact_created",
            "real_quantum_backend_artifact_created",
            "real_profit_artifact_created",
        ):
            if attempt.get(field) is not False:
                failures.append(f"{label}: {field} must remain false")
    return evaluations, failures


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "binding_registry_present": False,
        "binding_registry_path": str(DEFAULT_REGISTRY).replace("\\", "/"),
        "binding_report_present": False,
        "owner_global_override_report_present": False,
        "owner_global_override_authority": False,
        "owner_override_satisfies_all_qtt_internal_requirements": False,
        "attempted_access_count": 0,
        "allowed_access_count": 0,
        "blocked_access_count": 0,
        "invalid_access_count": 0,
        "allowed_by_binding_count": 0,
        "allowed_by_owner_approved_binding_count": 0,
        "allowed_by_owner_global_override_count": 0,
        "allowed_by_agent_assignment_owner_approved_count": 0,
        "allowed_by_owner_override_satisfied_count": 0,
        "allowed_by_row_binding_count": 0,
        "allowed_by_pattern_binding_count": 0,
        "allowed_by_family_binding_count": 0,
        "allowed_by_agent_id_binding_count": 0,
        "allowed_by_quarantine_review_count": 0,
        "allowed_by_retirement_audit_count": 0,
        "blocked_missing_binding_count": 0,
        "missing_binding_owner_override_satisfied_count": 0,
        "blocked_unauthorized_agent_role_count": 0,
        "unauthorized_agent_role_owner_override_satisfied_count": 0,
        "blocked_unauthorized_agent_id_count": 0,
        "unauthorized_agent_id_owner_override_satisfied_count": 0,
        "blocked_unauthorized_consumer_class_count": 0,
        "unauthorized_consumer_class_owner_override_satisfied_count": 0,
        "blocked_scope_mismatch_count": 0,
        "scope_mismatch_owner_override_satisfied_count": 0,
        "blocked_quarantine_count": 0,
        "quarantine_review_allowed_count": 0,
        "blocked_retired_count": 0,
        "retirement_audit_allowed_count": 0,
        "unknown_agent_role_count": 0,
        "unknown_consumer_class_count": 0,
        "unknown_parameter_target_count": 0,
        "unknown_parameter_target_owner_override_satisfied_count": 0,
        "row_level_access_allowed_count": 0,
        "pattern_level_access_allowed_count": 0,
        "family_level_access_allowed_count": 0,
        "agent_role_level_access_allowed_count": 0,
        "agent_id_level_access_allowed_count": 0,
        "runtime_consumer_access_allowed_count": 0,
        "live_consumer_access_allowed_count": 0,
        "quantum_backend_consumer_access_allowed_count": 0,
        "optimizer_consumer_access_allowed_count": 0,
        "risk_consumer_access_allowed_count": 0,
        "sizing_consumer_access_allowed_count": 0,
        "replay_paper_consumer_access_allowed_count": 0,
        "source_evidence_consumer_access_allowed_count": 0,
        "research_consumer_access_allowed_count": 0,
        "owner_override_access_attempt_count": 0,
        "owner_override_access_allowed_count": 0,
        "owner_override_access_blocked_count": 0,
        "validators_block_owner_override_count": 0,
        "codex_blocks_owner_override_count": 0,
        "qtt_agents_block_owner_override_count": 0,
        "generated_reports_block_owner_override_count": 0,
        "validation_gates_block_owner_override_count": 0,
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
        "final_ready": False,
        "authority_boundary_all_false": False,
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    fixture: dict[str, Any],
    evaluations: Sequence[AccessEvaluation],
    owner_report: dict[str, Any] | None,
) -> dict[str, Any]:
    attempts = [evaluation.attempt for evaluation in evaluations]
    allowed = [
        evaluation
        for evaluation in evaluations
        if evaluation.declared_allowed and not evaluation.invalid
    ]
    blocked = [
        evaluation
        for evaluation in evaluations
        if evaluation.declared_blocked and not evaluation.invalid
    ]
    invalid = [
        evaluation
        for evaluation in evaluations
        if evaluation.declared_decision == "INVALID_ATTEMPT" or evaluation.invalid
    ]
    owner_attempts = [
        evaluation for evaluation in evaluations if _owner_override_present(evaluation.attempt)
    ]

    def count_decision(decision: str) -> int:
        return sum(1 for attempt in attempts if attempt.get("access_decision") == decision)

    def allowed_consumer_in(classes: set[str]) -> int:
        return sum(
            1
            for evaluation in allowed
            if evaluation.attempt.get("requested_consumer_class") in classes
        )

    def owner_resolved(reason: str) -> int:
        return sum(
            1
            for evaluation in owner_attempts
            if evaluation.attempt.get("blocked_reason") == reason
            and evaluation.attempt.get("owner_override_resolved_block") is True
            and evaluation.declared_allowed
        )

    boundary = _mapping(fixture.get("authority_boundary"))
    report = _empty_report()
    report.update(
        {
            "binding_registry_present": (repo_root / DEFAULT_REGISTRY).exists(),
            "binding_report_present": (repo_root / DEFAULT_BINDING_REPORT).exists(),
            "owner_global_override_report_present": (
                repo_root / OWNER_AUTHORITY_REPORT
            ).exists(),
            "owner_global_override_authority": owner_report is not None
            and owner_report.get("owner_global_override_authority") is True,
            "owner_override_satisfies_all_qtt_internal_requirements": owner_report
            is not None
            and owner_report.get("owner_override_satisfies_all_qtt_internal_requirements")
            is True,
            "attempted_access_count": len(evaluations),
            "allowed_access_count": len(allowed),
            "blocked_access_count": len(blocked),
            "invalid_access_count": len(invalid),
            "allowed_by_binding_count": sum(
                1
                for evaluation in allowed
                if evaluation.declared_decision
                in {
                    "ALLOWED_BY_BINDING",
                    "ALLOWED_BY_ROW_BINDING",
                    "ALLOWED_BY_PATTERN_BINDING",
                    "ALLOWED_BY_FAMILY_BINDING",
                    "ALLOWED_BY_AGENT_ID_BINDING",
                    "ALLOWED_BY_QUARANTINE_REVIEW_BINDING",
                    "ALLOWED_BY_RETIREMENT_AUDIT_BINDING",
                }
            ),
            "allowed_by_owner_approved_binding_count": count_decision(
                "ALLOWED_BY_OWNER_APPROVED_BINDING"
            ),
            "allowed_by_owner_global_override_count": count_decision(
                "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE"
            ),
            "allowed_by_agent_assignment_owner_approved_count": count_decision(
                "ALLOWED_BY_AGENT_ASSIGNMENT_OWNER_APPROVED"
            ),
            "allowed_by_owner_override_satisfied_count": count_decision(
                "ALLOWED_BY_OWNER_OVERRIDE_SATISFIED"
            ),
            "allowed_by_row_binding_count": count_decision("ALLOWED_BY_ROW_BINDING"),
            "allowed_by_pattern_binding_count": count_decision(
                "ALLOWED_BY_PATTERN_BINDING"
            ),
            "allowed_by_family_binding_count": count_decision(
                "ALLOWED_BY_FAMILY_BINDING"
            ),
            "allowed_by_agent_id_binding_count": count_decision(
                "ALLOWED_BY_AGENT_ID_BINDING"
            ),
            "allowed_by_quarantine_review_count": count_decision(
                "ALLOWED_BY_QUARANTINE_REVIEW_BINDING"
            ),
            "allowed_by_retirement_audit_count": count_decision(
                "ALLOWED_BY_RETIREMENT_AUDIT_BINDING"
            ),
            "blocked_missing_binding_count": count_decision("BLOCKED_MISSING_BINDING"),
            "missing_binding_owner_override_satisfied_count": owner_resolved(
                "BLOCKED_MISSING_BINDING"
            ),
            "blocked_unauthorized_agent_role_count": count_decision(
                "BLOCKED_UNAUTHORIZED_AGENT_ROLE"
            ),
            "unauthorized_agent_role_owner_override_satisfied_count": owner_resolved(
                "BLOCKED_UNAUTHORIZED_AGENT_ROLE"
            ),
            "blocked_unauthorized_agent_id_count": count_decision(
                "BLOCKED_UNAUTHORIZED_AGENT_ID"
            ),
            "unauthorized_agent_id_owner_override_satisfied_count": owner_resolved(
                "BLOCKED_UNAUTHORIZED_AGENT_ID"
            ),
            "blocked_unauthorized_consumer_class_count": count_decision(
                "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS"
            ),
            "unauthorized_consumer_class_owner_override_satisfied_count": owner_resolved(
                "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS"
            ),
            "blocked_scope_mismatch_count": count_decision("BLOCKED_SCOPE_MISMATCH"),
            "scope_mismatch_owner_override_satisfied_count": owner_resolved(
                "BLOCKED_SCOPE_MISMATCH"
            ),
            "blocked_quarantine_count": count_decision("BLOCKED_QUARANTINE"),
            "quarantine_review_allowed_count": count_decision(
                "ALLOWED_BY_QUARANTINE_REVIEW_BINDING"
            ),
            "blocked_retired_count": count_decision("BLOCKED_RETIRED"),
            "retirement_audit_allowed_count": count_decision(
                "ALLOWED_BY_RETIREMENT_AUDIT_BINDING"
            ),
            "unknown_agent_role_count": count_decision("BLOCKED_UNKNOWN_AGENT_ROLE"),
            "unknown_consumer_class_count": count_decision(
                "BLOCKED_UNKNOWN_CONSUMER_CLASS"
            ),
            "unknown_parameter_target_count": count_decision(
                "BLOCKED_PARAMETER_TARGET_UNKNOWN"
            ),
            "unknown_parameter_target_owner_override_satisfied_count": owner_resolved(
                "BLOCKED_PARAMETER_TARGET_UNKNOWN"
            ),
            "row_level_access_allowed_count": sum(
                1
                for evaluation in allowed
                if _present_string(evaluation.attempt.get("atomic_parameter_row_id"))
            ),
            "pattern_level_access_allowed_count": sum(
                1
                for evaluation in allowed
                if _present_string(evaluation.attempt.get("row_pattern_id"))
            ),
            "family_level_access_allowed_count": sum(
                1
                for evaluation in allowed
                if _present_string(evaluation.attempt.get("parameter_family"))
            ),
            "agent_role_level_access_allowed_count": sum(
                1
                for evaluation in allowed
                if evaluation.attempt.get("requesting_agent_role") in AGENT_ROLES
            ),
            "agent_id_level_access_allowed_count": sum(
                1
                for evaluation in allowed
                if _present_string(evaluation.attempt.get("requesting_agent_id"))
            ),
            "runtime_consumer_access_allowed_count": allowed_consumer_in(
                {"RUNTIME_RESOLVER_INPUT"}
            ),
            "live_consumer_access_allowed_count": allowed_consumer_in(
                {"LIVE_ORDER_ROUTING", "LIVE_EXECUTION"}
            ),
            "quantum_backend_consumer_access_allowed_count": allowed_consumer_in(
                {"QUANTUM_BACKEND_EXECUTION"}
            ),
            "optimizer_consumer_access_allowed_count": allowed_consumer_in(
                {"OPTIMIZER_SEARCH", "OPTIMIZER_DEFAULTS"}
            ),
            "risk_consumer_access_allowed_count": allowed_consumer_in(
                {"RISK_MODEL_INPUT"}
            ),
            "sizing_consumer_access_allowed_count": allowed_consumer_in(
                {"SIZING_MODEL_INPUT"}
            ),
            "replay_paper_consumer_access_allowed_count": allowed_consumer_in(
                {"REPLAY_CANDIDATE_SELECTION", "PAPER_CANDIDATE_SELECTION"}
            ),
            "source_evidence_consumer_access_allowed_count": allowed_consumer_in(
                {"SOURCE_EVIDENCE_RETRIEVAL"}
            ),
            "research_consumer_access_allowed_count": allowed_consumer_in(
                {"INVENTORY_INDEX", "RESEARCH_TRIAGE"}
            ),
            "owner_override_access_attempt_count": len(owner_attempts),
            "owner_override_access_allowed_count": sum(
                1 for evaluation in owner_attempts if evaluation.declared_allowed
            ),
            "owner_override_access_blocked_count": sum(
                1 for evaluation in owner_attempts if evaluation.declared_blocked
            ),
            "validators_block_owner_override_count": 0,
            "codex_blocks_owner_override_count": 0,
            "qtt_agents_block_owner_override_count": 0,
            "generated_reports_block_owner_override_count": 0,
            "validation_gates_block_owner_override_count": 0,
            "real_runtime_artifact_created": any(
                attempt.get("real_runtime_artifact_created") is True
                for attempt in attempts
            )
            or boundary.get("real_runtime_artifact_created") is True,
            "real_live_artifact_created": any(
                attempt.get("real_live_artifact_created") is True
                for attempt in attempts
            )
            or boundary.get("real_live_artifact_created") is True,
            "real_order_artifact_created": any(
                attempt.get("real_order_artifact_created") is True
                for attempt in attempts
            )
            or boundary.get("real_order_artifact_created") is True,
            "real_quantum_backend_artifact_created": any(
                attempt.get("real_quantum_backend_artifact_created") is True
                for attempt in attempts
            )
            or boundary.get("real_quantum_backend_artifact_created") is True,
            "real_profit_artifact_created": any(
                attempt.get("real_profit_artifact_created") is True
                for attempt in attempts
            )
            or boundary.get("real_profit_artifact_created") is True,
            "source_acceptance_artifact_created": boundary.get(
                "source_acceptance_artifact_created"
            )
            is True,
            "connector_binding_artifact_created": boundary.get(
                "connector_binding_artifact_created"
            )
            is True,
            "private_state_fetch_created": boundary.get("private_state_fetch_created")
            is True,
            "secret_materialization_created": boundary.get(
                "secret_materialization_created"
            )
            is True,
            "external_repo_clone_created": boundary.get("external_repo_clone_created")
            is True,
            "package_install_created": boundary.get("package_install_created") is True,
            "bundle_file_present": (repo_root / CANONICAL_BUNDLE).exists(),
            "bundle_sha_present": (repo_root / CANONICAL_BUNDLE_SHA).exists(),
            "uses_pr_number_as_authority": boundary.get("uses_pr_number_as_authority")
            is True
            or _uses_pr_number(fixture),
            "final_ready": False,
        }
    )
    false_boundary_fields = (
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
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )
    report["authority_boundary_all_false"] = all(
        report.get(field) is False for field in false_boundary_fields
    )
    return report


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(schema.get("$defs")).get("consumer_gate_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.consumer_gate_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    minimums = {
        "attempted_access_count": 38,
        "allowed_access_count": 20,
        "blocked_access_count": 8,
        "allowed_by_owner_global_override_count": 4,
        "allowed_by_agent_assignment_owner_approved_count": 1,
        "allowed_by_owner_override_satisfied_count": 4,
        "missing_binding_owner_override_satisfied_count": 1,
        "unauthorized_agent_role_owner_override_satisfied_count": 1,
        "unauthorized_agent_id_owner_override_satisfied_count": 1,
        "unauthorized_consumer_class_owner_override_satisfied_count": 1,
        "scope_mismatch_owner_override_satisfied_count": 1,
        "unknown_parameter_target_owner_override_satisfied_count": 1,
        "runtime_consumer_access_allowed_count": 1,
        "live_consumer_access_allowed_count": 1,
        "quantum_backend_consumer_access_allowed_count": 1,
        "optimizer_consumer_access_allowed_count": 1,
        "risk_consumer_access_allowed_count": 1,
        "sizing_consumer_access_allowed_count": 1,
        "replay_paper_consumer_access_allowed_count": 1,
        "source_evidence_consumer_access_allowed_count": 1,
        "research_consumer_access_allowed_count": 1,
        "owner_override_access_attempt_count": 8,
        "owner_override_access_allowed_count": 8,
    }
    for field, minimum in minimums.items():
        if report.get(field, 0) < minimum:
            failures.append(f"report.{field} must be at least {minimum}")

    expected_true_fields = (
        "binding_registry_present",
        "binding_report_present",
        "owner_global_override_report_present",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "authority_boundary_all_false",
    )
    for field in expected_true_fields:
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")

    expected_zero_fields = (
        "owner_override_access_blocked_count",
        "validators_block_owner_override_count",
        "codex_blocks_owner_override_count",
        "qtt_agents_block_owner_override_count",
        "generated_reports_block_owner_override_count",
        "validation_gates_block_owner_override_count",
    )
    for field in expected_zero_fields:
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")

    expected_false_fields = (
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
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )
    for field in expected_false_fields:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")

    if report.get("deterministic_output") is not True:
        failures.append("report.deterministic_output must be true")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must be deterministic sentinel")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is nondeterministic")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    binding_report_path: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    registry, owner_report, upstream_failures = _validate_upstream_foundations(
        repo_root=root,
        registry_path=registry_path,
        binding_report_path=binding_report_path,
    )
    failures.extend(upstream_failures)

    schema, schema_failures = _load_json(root / schema_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_failures)

    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if fixture is not None:
        failures.extend(_validate_fixture_shape(fixture=fixture, schema=schema))

    report: dict[str, Any] | None = None
    if registry is not None and fixture is not None:
        evaluations, evaluation_failures = _evaluate_attempts(
            registry=registry,
            fixture=fixture,
        )
        failures.extend(evaluation_failures)
        report = build_report(
            repo_root=root,
            fixture=fixture,
            evaluations=evaluations,
            owner_report=owner_report,
        )
        second_report = build_report(
            repo_root=root,
            fixture=fixture,
            evaluations=evaluations,
            owner_report=owner_report,
        )
        if report != second_report:
            failures.append(
                "generated parameter-agent binding consumer gate report is not deterministic"
            )
        failures.extend(_validate_report_schema(report, schema))
        failures.extend(_report_safety_failures(report))

    if mode == "final" and (report is None or report.get("final_ready") is not True):
        failures.append(
            "final mode incomplete: AtomicRows parameter-agent binding consumer gate "
            "is a static foundation, not complete bundle readiness"
        )

    if output_path is not None and not failures and report is not None:
        write_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--binding-report", default=str(DEFAULT_BINDING_REPORT))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        binding_report_path=pathlib.Path(args.binding_report),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"attempted={report.get('attempted_access_count', 0)} "
            f"allowed={report.get('allowed_access_count', 0)} "
            f"blocked={report.get('blocked_access_count', 0)} "
            f"owner_override_allowed="
            f"{report.get('owner_override_access_allowed_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
