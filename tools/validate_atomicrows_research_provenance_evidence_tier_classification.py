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

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_research_provenance_evidence_tier_classification.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsResearchProvenanceEvidenceTierClassification.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_research_provenance_evidence_tier_classification.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
)

CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

SCHEMA_VERSION = (
    "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_SCHEMA_V1"
)
CLASSIFICATION_TYPE = "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION"
REPORT_TYPE = "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_REPORT"
SOURCE_OF_CLASSIFICATION_SUBSTANCE = "docs/master_plan/QTT_MasterPlan_Current.md"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
SUCCESS_MARKER = "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_OK"
FAILURE_MARKER = (
    "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_FAILED"
)
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_FINAL_INCOMPLETE"
)
OWNER_OVERRIDE_BASIS = (
    "OWNER_APPROVED_INTERNAL_WORKFLOW_REQUIREMENT_SATISFACTION_NOT_EXTERNAL_FACT_AUTHORITY"
)

CANONICAL_SOURCE_TYPES = (
    "OWNER_SUBMITTED_RESEARCH_SOURCE",
    "PUBLIC_WEBSITE",
    "RESEARCH_ARTICLE",
    "ACADEMIC_RESEARCH_PAPER",
    "X_POST",
    "NEWS_ARTICLE",
    "GITHUB_REPOSITORY",
    "WHITEPAPER",
    "BLOG_POST",
    "FORUM_OR_COMMUNITY_POST",
    "UPLOADED_DOCUMENT",
    "SCREENSHOT_OR_OWNER_NOTE",
    "OFFICIAL_SOURCE_EVIDENCE",
    "OWNER_GLOBAL_OVERRIDE",
)

ALLOWED_EVIDENCE_TIERS = (
    "OWNER_RESEARCH_INPUT",
    "PUBLIC_RESEARCH_INPUT",
    "ACADEMIC_RESEARCH_INPUT",
    "SOCIAL_RESEARCH_SIGNAL",
    "NEWS_RESEARCH_INPUT",
    "CODE_REPOSITORY_RESEARCH_INPUT",
    "NON_AUTHORITATIVE_RESEARCH_INPUT",
    "OWNER_UPLOADED_OR_NOTE_INPUT",
    "OFFICIAL_SOURCE_REVIEW_INPUT",
    "OWNER_INTERNAL_OVERRIDE",
)

ALLOWED_CANDIDATE_ROUTE_KINDS = (
    "OWNER_RESEARCH_TO_CANDIDATE_INTAKE",
    "PUBLIC_RESEARCH_TO_RETRIEVAL_TARGET_OR_CANDIDATE",
    "ACADEMIC_RESEARCH_TO_CANDIDATE_AND_RETRIEVAL_TARGET",
    "SOCIAL_SIGNAL_TO_RESEARCH_REVIEW_ONLY",
    "NEWS_RESEARCH_TO_RETRIEVAL_TARGET_OR_CANDIDATE",
    "CODE_REPOSITORY_TO_QUARANTINED_RESEARCH_REVIEW",
    "NON_AUTHORITATIVE_RESEARCH_TO_REVIEW_ONLY",
    "OWNER_UPLOADED_OR_NOTE_TO_ACCESS_RIGHTS_GATED_REVIEW",
    "OFFICIAL_SOURCE_TO_ACCEPTED_SOURCE_REVIEW_ONLY",
    "OWNER_OVERRIDE_TO_INTERNAL_REQUIREMENT_SATISFACTION_ONLY",
)

AUTHORITY_CLASS_BY_SOURCE_TYPE = {
    "OWNER_SUBMITTED_RESEARCH_SOURCE": (
        "OWNER_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "PUBLIC_WEBSITE": "PUBLIC_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY",
    "RESEARCH_ARTICLE": "PUBLIC_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY",
    "ACADEMIC_RESEARCH_PAPER": (
        "ACADEMIC_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "X_POST": "SOCIAL_RESEARCH_SIGNAL_NOT_EXTERNAL_FACT_AUTHORITY",
    "NEWS_ARTICLE": "NEWS_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY",
    "GITHUB_REPOSITORY": (
        "CODE_REPOSITORY_RESEARCH_INPUT_NOT_SOURCE_FACT_NOT_LIVE_AUTHORITY"
    ),
    "WHITEPAPER": "RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY",
    "BLOG_POST": "NON_AUTHORITATIVE_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY",
    "FORUM_OR_COMMUNITY_POST": (
        "NON_AUTHORITATIVE_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "UPLOADED_DOCUMENT": (
        "OWNER_UPLOADED_DOCUMENT_INPUT_ACCESS_RIGHTS_GATED_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "SCREENSHOT_OR_OWNER_NOTE": (
        "OWNER_NOTE_RESEARCH_INPUT_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "OFFICIAL_SOURCE_EVIDENCE": (
        "OFFICIAL_SOURCE_REVIEW_INPUT_NOT_ACCEPTED_PACKET_BY_THIS_PR"
    ),
    "OWNER_GLOBAL_OVERRIDE": (
        "OWNER_INTERNAL_WORKFLOW_OVERRIDE_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
}

EVIDENCE_TIER_BY_SOURCE_TYPE = {
    "OWNER_SUBMITTED_RESEARCH_SOURCE": "OWNER_RESEARCH_INPUT",
    "PUBLIC_WEBSITE": "PUBLIC_RESEARCH_INPUT",
    "RESEARCH_ARTICLE": "PUBLIC_RESEARCH_INPUT",
    "ACADEMIC_RESEARCH_PAPER": "ACADEMIC_RESEARCH_INPUT",
    "X_POST": "SOCIAL_RESEARCH_SIGNAL",
    "NEWS_ARTICLE": "NEWS_RESEARCH_INPUT",
    "GITHUB_REPOSITORY": "CODE_REPOSITORY_RESEARCH_INPUT",
    "WHITEPAPER": "PUBLIC_RESEARCH_INPUT",
    "BLOG_POST": "NON_AUTHORITATIVE_RESEARCH_INPUT",
    "FORUM_OR_COMMUNITY_POST": "NON_AUTHORITATIVE_RESEARCH_INPUT",
    "UPLOADED_DOCUMENT": "OWNER_UPLOADED_OR_NOTE_INPUT",
    "SCREENSHOT_OR_OWNER_NOTE": "OWNER_UPLOADED_OR_NOTE_INPUT",
    "OFFICIAL_SOURCE_EVIDENCE": "OFFICIAL_SOURCE_REVIEW_INPUT",
    "OWNER_GLOBAL_OVERRIDE": "OWNER_INTERNAL_OVERRIDE",
}

CANDIDATE_ROUTE_KIND_BY_SOURCE_TYPE = {
    "OWNER_SUBMITTED_RESEARCH_SOURCE": "OWNER_RESEARCH_TO_CANDIDATE_INTAKE",
    "PUBLIC_WEBSITE": "PUBLIC_RESEARCH_TO_RETRIEVAL_TARGET_OR_CANDIDATE",
    "RESEARCH_ARTICLE": "PUBLIC_RESEARCH_TO_RETRIEVAL_TARGET_OR_CANDIDATE",
    "ACADEMIC_RESEARCH_PAPER": (
        "ACADEMIC_RESEARCH_TO_CANDIDATE_AND_RETRIEVAL_TARGET"
    ),
    "X_POST": "SOCIAL_SIGNAL_TO_RESEARCH_REVIEW_ONLY",
    "NEWS_ARTICLE": "NEWS_RESEARCH_TO_RETRIEVAL_TARGET_OR_CANDIDATE",
    "GITHUB_REPOSITORY": "CODE_REPOSITORY_TO_QUARANTINED_RESEARCH_REVIEW",
    "WHITEPAPER": "PUBLIC_RESEARCH_TO_RETRIEVAL_TARGET_OR_CANDIDATE",
    "BLOG_POST": "NON_AUTHORITATIVE_RESEARCH_TO_REVIEW_ONLY",
    "FORUM_OR_COMMUNITY_POST": "NON_AUTHORITATIVE_RESEARCH_TO_REVIEW_ONLY",
    "UPLOADED_DOCUMENT": "OWNER_UPLOADED_OR_NOTE_TO_ACCESS_RIGHTS_GATED_REVIEW",
    "SCREENSHOT_OR_OWNER_NOTE": (
        "OWNER_UPLOADED_OR_NOTE_TO_ACCESS_RIGHTS_GATED_REVIEW"
    ),
    "OFFICIAL_SOURCE_EVIDENCE": "OFFICIAL_SOURCE_TO_ACCEPTED_SOURCE_REVIEW_ONLY",
    "OWNER_GLOBAL_OVERRIDE": (
        "OWNER_OVERRIDE_TO_INTERNAL_REQUIREMENT_SATISFACTION_ONLY"
    ),
}

SOURCE_TYPE_DESCRIPTION_BY_SOURCE_TYPE = {
    "OWNER_SUBMITTED_RESEARCH_SOURCE": (
        "Owner-submitted research input that may seed future candidate intake but is "
        "not external fact authority."
    ),
    "PUBLIC_WEBSITE": (
        "Public web research input that may identify retrieval targets or candidates "
        "without accepting facts."
    ),
    "RESEARCH_ARTICLE": (
        "Public research article input that may seed future research routing without "
        "accepted source status."
    ),
    "ACADEMIC_RESEARCH_PAPER": (
        "Academic research paper input that may seed candidate and retrieval review "
        "without proof claims."
    ),
    "X_POST": (
        "Social research signal that may seed owner review but cannot bind agents or "
        "authorize facts."
    ),
    "NEWS_ARTICLE": (
        "News research input that may seed retrieval targets or candidates without "
        "external fact authority."
    ),
    "GITHUB_REPOSITORY": (
        "Code repository research input quarantined for no-clone, no-run, no-install, "
        "and no-secret handling."
    ),
    "WHITEPAPER": (
        "Whitepaper research input that may seed future candidate and retrieval review "
        "without accepted facts."
    ),
    "BLOG_POST": (
        "Non-authoritative blog research input routed to review only before any "
        "future candidate use."
    ),
    "FORUM_OR_COMMUNITY_POST": (
        "Non-authoritative community research input routed to review only before any "
        "future candidate use."
    ),
    "UPLOADED_DOCUMENT": (
        "Owner-uploaded document input requiring private access-rights attestation "
        "before future review."
    ),
    "SCREENSHOT_OR_OWNER_NOTE": (
        "Owner note or screenshot research input that may seed review without external "
        "fact authority."
    ),
    "OFFICIAL_SOURCE_EVIDENCE": (
        "Official source review input type that can route to future accepted-source "
        "review without creating acceptance."
    ),
    "OWNER_GLOBAL_OVERRIDE": (
        "Owner internal workflow override basis that can satisfy internal requirements "
        "without external fact authority."
    ),
}

CLASSIFICATION_REASON_CODE_BY_SOURCE_TYPE = {
    source_type: f"{source_type}_STATIC_RESEARCH_PROVENANCE_CLASSIFICATION"
    for source_type in CANONICAL_SOURCE_TYPES
}
CLASSIFICATION_REASON_CODE_BY_SOURCE_TYPE["OFFICIAL_SOURCE_EVIDENCE"] = (
    "OFFICIAL_SOURCE_REVIEW_INPUT_ONLY_ACCEPTANCE_NOT_CREATED"
)
CLASSIFICATION_REASON_CODE_BY_SOURCE_TYPE["OWNER_GLOBAL_OVERRIDE"] = (
    "OWNER_INTERNAL_WORKFLOW_OVERRIDE_ONLY_NOT_EXTERNAL_FACT_AUTHORITY"
)

CANDIDATE_SEED_SOURCE_TYPES = frozenset(CANONICAL_SOURCE_TYPES[:12])
AGENT_BINDING_SEED_SOURCE_TYPES = frozenset(
    (
        "OWNER_SUBMITTED_RESEARCH_SOURCE",
        "PUBLIC_WEBSITE",
        "RESEARCH_ARTICLE",
        "ACADEMIC_RESEARCH_PAPER",
        "NEWS_ARTICLE",
        "GITHUB_REPOSITORY",
        "WHITEPAPER",
        "UPLOADED_DOCUMENT",
    )
)
FORBIDDEN_SOURCE_TYPE_FALSE_FIELDS = (
    "may_authorize_external_fact",
    "may_create_accepted_source_packet",
    "may_unlock_connector_semantics",
    "may_populate_connector_semantics",
    "may_populate_runtime_cash_semantics",
    "may_create_runtime_artifact",
    "may_create_replay_artifact",
    "may_create_paper_artifact",
    "may_create_order_authority",
    "may_create_live_authority",
    "may_create_profit_evidence",
    "may_create_alpha_evidence",
    "may_create_latency_superiority_evidence",
    "may_create_execution_superiority_evidence",
    "may_create_quantum_advantage_evidence",
    "may_create_quantum_backend_evidence",
    "final_ready_contribution",
)

TOP_LEVEL_FALSE_FIELDS = (
    "owner_override_external_fact_authority",
    "official_source_evidence_acceptance_created",
    "source_retrieval_executed",
    "source_acceptance_executed",
    "accepted_source_packet_created",
    "connector_binding_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "profit_evidence_created",
    "alpha_evidence_created",
    "latency_superiority_evidence_created",
    "execution_superiority_evidence_created",
    "quantum_advantage_evidence_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
)

TOP_LEVEL_REQUIRED_FIELDS = (
    "schema_version",
    "classification_type",
    "source_of_classification_substance",
    "deterministic_output",
    "generated_at_utc",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "owner_override_external_fact_authority",
    "source_type_count",
    "source_types",
    "source_type_ids_canonical_order",
    "owner_submitted_idea_may_become_parameter_candidate",
    "owner_override_may_satisfy_internal_source_evidence_requirement",
    "official_source_evidence_acceptance_created",
    "source_retrieval_executed",
    "source_acceptance_executed",
    "accepted_source_packet_created",
    "connector_binding_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "profit_evidence_created",
    "alpha_evidence_created",
    "latency_superiority_evidence_created",
    "execution_superiority_evidence_created",
    "quantum_advantage_evidence_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
    "authority_boundary_all_false",
)

OPTIONAL_FIXTURE_FIELDS = (
    "fixture_id",
    "fixture_version",
    "mode",
    "execution",
)

SOURCE_TYPE_FIELDS = (
    "ordinal",
    "source_type",
    "source_type_description",
    "evidence_tier",
    "authority_class",
    "classification_reason_code",
    "owner_override_supported",
    "owner_override_satisfaction_basis",
    "source_locator_required_for_future_intake",
    "owner_note_allowed",
    "private_access_rights_attestation_required",
    "no_clone_no_run_required",
    "no_install_required",
    "secret_materialization_blocked",
    "may_seed_parameter_candidate",
    "may_seed_algorithm_candidate",
    "may_seed_agent_binding_request",
    "may_seed_retrieval_target",
    "may_seed_owner_review_request",
    "may_seed_accepted_source_review",
    "may_satisfy_internal_source_evidence_requirement_with_owner_override",
    "future_pr71_intake_supported",
    "future_pr72_candidate_routing_supported",
    "future_parameter_stack_routing_supported",
    "future_trade_context_routing_supported",
    "future_quantum_applicability_routing_supported",
    "future_scoring_ranking_routing_supported",
    "future_quantum_classical_arbitration_routing_supported",
    "candidate_route_kind",
    "external_fact_requires_accepted_source_packet",
    *FORBIDDEN_SOURCE_TYPE_FALSE_FIELDS,
)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _source_type_entry(source_type: str, ordinal: int) -> dict[str, Any]:
    candidate_seed = source_type in CANDIDATE_SEED_SOURCE_TYPES
    official_source = source_type == "OFFICIAL_SOURCE_EVIDENCE"
    owner_override = source_type == "OWNER_GLOBAL_OVERRIDE"
    return {
        "ordinal": ordinal,
        "source_type": source_type,
        "source_type_description": SOURCE_TYPE_DESCRIPTION_BY_SOURCE_TYPE[source_type],
        "evidence_tier": EVIDENCE_TIER_BY_SOURCE_TYPE[source_type],
        "authority_class": AUTHORITY_CLASS_BY_SOURCE_TYPE[source_type],
        "classification_reason_code": (
            CLASSIFICATION_REASON_CODE_BY_SOURCE_TYPE[source_type]
        ),
        "owner_override_supported": True,
        "owner_override_satisfaction_basis": OWNER_OVERRIDE_BASIS,
        "source_locator_required_for_future_intake": not owner_override,
        "owner_note_allowed": True,
        "private_access_rights_attestation_required": (
            source_type == "UPLOADED_DOCUMENT"
        ),
        "no_clone_no_run_required": source_type == "GITHUB_REPOSITORY",
        "no_install_required": source_type == "GITHUB_REPOSITORY",
        "secret_materialization_blocked": True,
        "may_seed_parameter_candidate": candidate_seed,
        "may_seed_algorithm_candidate": candidate_seed,
        "may_seed_agent_binding_request": source_type in AGENT_BINDING_SEED_SOURCE_TYPES,
        "may_seed_retrieval_target": not owner_override,
        "may_seed_owner_review_request": True,
        "may_seed_accepted_source_review": official_source,
        "may_satisfy_internal_source_evidence_requirement_with_owner_override": True,
        "future_pr71_intake_supported": True,
        "future_pr72_candidate_routing_supported": candidate_seed,
        "future_parameter_stack_routing_supported": candidate_seed,
        "future_trade_context_routing_supported": candidate_seed,
        "future_quantum_applicability_routing_supported": candidate_seed,
        "future_scoring_ranking_routing_supported": candidate_seed,
        "future_quantum_classical_arbitration_routing_supported": candidate_seed,
        "candidate_route_kind": CANDIDATE_ROUTE_KIND_BY_SOURCE_TYPE[source_type],
        "external_fact_requires_accepted_source_packet": True,
        **{field: False for field in FORBIDDEN_SOURCE_TYPE_FALSE_FIELDS},
    }


def expected_source_types() -> list[dict[str, Any]]:
    return [
        _source_type_entry(source_type, ordinal)
        for ordinal, source_type in enumerate(CANONICAL_SOURCE_TYPES, start=1)
    ]


def expected_classification_root() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "classification_type": CLASSIFICATION_TYPE,
        "source_of_classification_substance": SOURCE_OF_CLASSIFICATION_SUBSTANCE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "owner_global_override_authority": True,
        "owner_override_satisfies_all_qtt_internal_requirements": True,
        "owner_override_external_fact_authority": False,
        "source_type_count": len(CANONICAL_SOURCE_TYPES),
        "source_types": expected_source_types(),
        "source_type_ids_canonical_order": list(CANONICAL_SOURCE_TYPES),
        "owner_submitted_idea_may_become_parameter_candidate": True,
        "owner_override_may_satisfy_internal_source_evidence_requirement": True,
        "official_source_evidence_acceptance_created": False,
        "source_retrieval_executed": False,
        "source_acceptance_executed": False,
        "accepted_source_packet_created": False,
        "connector_binding_created": False,
        "runtime_artifact_created": False,
        "live_artifact_created": False,
        "order_artifact_created": False,
        "profit_evidence_created": False,
        "alpha_evidence_created": False,
        "latency_superiority_evidence_created": False,
        "execution_superiority_evidence_created": False,
        "quantum_advantage_evidence_created": False,
        "quantum_backend_artifact_created": False,
        "bundle_file_present": False,
        "bundle_sha_present": False,
        "uses_pr_number_as_authority": False,
        "final_ready": False,
        "authority_boundary_all_false": True,
    }


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def load_fixture(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"fixture root must be an object: {path}")
    return value


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


def _require_required_and_allowed_fields(
    value: dict[str, Any],
    *,
    required_fields: set[str],
    allowed_fields: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    missing = sorted(required_fields - set(value))
    unexpected = sorted(set(value) - allowed_fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _source_entry_by_type(payload: dict[str, Any], source_type: str) -> dict[str, Any]:
    entries = payload.get("source_types")
    if not isinstance(entries, list):
        return {}
    for entry in entries:
        if isinstance(entry, dict) and entry.get("source_type") == source_type:
            return entry
    return {}


def _forbidden_source_type_boundary_true_count(
    source_types: list[dict[str, Any]],
) -> int:
    return sum(
        1
        for entry in source_types
        for field in FORBIDDEN_SOURCE_TYPE_FALSE_FIELDS
        if entry.get(field) is True
    )


def validate_classification_payload(
    payload: dict[str, Any],
    *,
    label: str,
) -> list[str]:
    failures: list[str] = []
    allowed_fields = set(TOP_LEVEL_REQUIRED_FIELDS) | set(OPTIONAL_FIXTURE_FIELDS)
    failures.extend(
        _require_required_and_allowed_fields(
            payload,
            required_fields=set(TOP_LEVEL_REQUIRED_FIELDS),
            allowed_fields=allowed_fields,
            label=label,
        )
    )

    expected = expected_classification_root()
    for field, expected_value in expected.items():
        if field == "source_types":
            continue
        if payload.get(field) != expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")

    source_types = payload.get("source_types")
    if not isinstance(source_types, list):
        return failures + [f"{label}.source_types must be a list"]
    if len(source_types) != len(CANONICAL_SOURCE_TYPES):
        failures.append(
            f"{label}.source_types must contain exactly {len(CANONICAL_SOURCE_TYPES)} entries"
        )

    actual_ids = [
        str(entry.get("source_type"))
        for entry in source_types
        if isinstance(entry, dict)
    ]
    if actual_ids != list(CANONICAL_SOURCE_TYPES):
        failures.append(f"{label}.source_types must be in canonical order")

    expected_entries = expected_source_types()
    for index, expected_entry in enumerate(expected_entries):
        entry_label = f"{label}.source_types[{index}]"
        if index >= len(source_types) or not isinstance(source_types[index], dict):
            failures.append(f"{entry_label} must be an object")
            continue
        entry = source_types[index]
        failures.extend(_require_exact_fields(entry, set(SOURCE_TYPE_FIELDS), entry_label))
        for field, expected_value in expected_entry.items():
            if entry.get(field) != expected_value:
                failures.append(f"{entry_label}.{field} must be {expected_value}")

    official = _source_entry_by_type(payload, "OFFICIAL_SOURCE_EVIDENCE")
    if official.get("may_seed_accepted_source_review") is not True:
        failures.append(
            f"{label}.OFFICIAL_SOURCE_EVIDENCE may_seed_accepted_source_review must be true"
        )
    if official.get("may_create_accepted_source_packet") is not False:
        failures.append(
            f"{label}.OFFICIAL_SOURCE_EVIDENCE may_create_accepted_source_packet must be false"
        )
    if official.get("may_unlock_connector_semantics") is not False:
        failures.append(
            f"{label}.OFFICIAL_SOURCE_EVIDENCE may_unlock_connector_semantics must be false"
        )

    github = _source_entry_by_type(payload, "GITHUB_REPOSITORY")
    for field in (
        "no_clone_no_run_required",
        "no_install_required",
        "secret_materialization_blocked",
    ):
        if github.get(field) is not True:
            failures.append(f"{label}.GITHUB_REPOSITORY {field} must be true")

    uploaded = _source_entry_by_type(payload, "UPLOADED_DOCUMENT")
    if uploaded.get("private_access_rights_attestation_required") is not True:
        failures.append(
            f"{label}.UPLOADED_DOCUMENT private_access_rights_attestation_required must be true"
        )

    owner_override = _source_entry_by_type(payload, "OWNER_GLOBAL_OVERRIDE")
    if owner_override.get("may_authorize_external_fact") is not False:
        failures.append(
            f"{label}.OWNER_GLOBAL_OVERRIDE may_authorize_external_fact must be false"
        )

    for index, entry in enumerate(source_types):
        if not isinstance(entry, dict):
            continue
        entry_label = f"{label}.source_types[{index}]"
        for field in FORBIDDEN_SOURCE_TYPE_FALSE_FIELDS:
            if entry.get(field) is not False:
                failures.append(f"{entry_label}.{field} must be false")
        if entry.get("external_fact_requires_accepted_source_packet") is not True:
            failures.append(
                f"{entry_label}.external_fact_requires_accepted_source_packet must be true"
            )

    for field in TOP_LEVEL_FALSE_FIELDS:
        if payload.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    for field in (
        "deterministic_output",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "owner_submitted_idea_may_become_parameter_candidate",
        "owner_override_may_satisfy_internal_source_evidence_requirement",
        "authority_boundary_all_false",
    ):
        if payload.get(field) is not True:
            failures.append(f"{label}.{field} must be true")

    return failures


def validate_fixture_shape(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "fixture_id": (
            "SYNTHETIC_ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_FIXTURE"
        ),
        "fixture_version": (
            "SYNTHETIC_ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_FIXTURE_V1"
        ),
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
    }
    for field, expected_value in expected.items():
        if fixture.get(field) != expected_value:
            failures.append(f"fixture.{field} must be {expected_value}")
    return failures


def _ordered_unique(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def build_report(classification: dict[str, Any]) -> dict[str, Any]:
    source_types = [
        entry
        for entry in classification.get("source_types", [])
        if isinstance(entry, dict)
    ]
    actual_ids = [str(entry.get("source_type")) for entry in source_types]
    missing_ids = [
        source_type
        for source_type in CANONICAL_SOURCE_TYPES
        if source_type not in actual_ids
    ]
    invalid_order_count = sum(
        1
        for index, source_type in enumerate(actual_ids[: len(CANONICAL_SOURCE_TYPES)])
        if source_type != CANONICAL_SOURCE_TYPES[index]
    )
    invalid_ordinal_count = sum(
        1
        for index, entry in enumerate(source_types, start=1)
        if entry.get("ordinal") != index
    )
    authority_mismatch_count = sum(
        1
        for entry in source_types
        if entry.get("authority_class")
        != AUTHORITY_CLASS_BY_SOURCE_TYPE.get(str(entry.get("source_type")))
    )
    evidence_mismatch_count = sum(
        1
        for entry in source_types
        if entry.get("evidence_tier")
        != EVIDENCE_TIER_BY_SOURCE_TYPE.get(str(entry.get("source_type")))
    )
    route_mismatch_count = sum(
        1
        for entry in source_types
        if entry.get("candidate_route_kind")
        != CANDIDATE_ROUTE_KIND_BY_SOURCE_TYPE.get(str(entry.get("source_type")))
    )
    official = _source_entry_by_type(classification, "OFFICIAL_SOURCE_EVIDENCE")
    github = _source_entry_by_type(classification, "GITHUB_REPOSITORY")
    uploaded = _source_entry_by_type(classification, "UPLOADED_DOCUMENT")
    non_authoritative_sources = (
        _source_entry_by_type(classification, "BLOG_POST"),
        _source_entry_by_type(classification, "FORUM_OR_COMMUNITY_POST"),
    )
    candidate_entries = [
        entry
        for entry in source_types
        if entry.get("may_seed_parameter_candidate") is True
    ]

    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_classification_substance": SOURCE_OF_CLASSIFICATION_SUBSTANCE,
        "classification_type": CLASSIFICATION_TYPE,
        "source_type_count": len(source_types),
        "required_source_type_count": len(CANONICAL_SOURCE_TYPES),
        "required_source_types_present_count": (
            len(CANONICAL_SOURCE_TYPES) - len(missing_ids)
        ),
        "missing_source_type_count": len(missing_ids),
        "invalid_source_type_order_count": invalid_order_count,
        "invalid_ordinal_order_count": invalid_ordinal_count,
        "authority_class_mismatch_count": authority_mismatch_count,
        "evidence_tier_mismatch_count": evidence_mismatch_count,
        "candidate_route_kind_mismatch_count": route_mismatch_count,
        "forbidden_source_type_boundary_true_count": (
            _forbidden_source_type_boundary_true_count(source_types)
        ),
        "owner_submitted_research_source_present": (
            "OWNER_SUBMITTED_RESEARCH_SOURCE" in actual_ids
        ),
        "official_source_evidence_type_present": (
            "OFFICIAL_SOURCE_EVIDENCE" in actual_ids
        ),
        "owner_global_override_type_present": "OWNER_GLOBAL_OVERRIDE" in actual_ids,
        "github_repository_no_clone_no_run_required": (
            github.get("no_clone_no_run_required") is True
        ),
        "github_repository_no_install_required": (
            github.get("no_install_required") is True
        ),
        "github_repository_secret_materialization_blocked": (
            github.get("secret_materialization_blocked") is True
        ),
        "uploaded_document_access_rights_attestation_required": (
            uploaded.get("private_access_rights_attestation_required") is True
        ),
        "owner_submitted_idea_may_become_parameter_candidate": (
            classification.get("owner_submitted_idea_may_become_parameter_candidate")
            is True
        ),
        "owner_override_may_satisfy_internal_source_evidence_requirement": (
            classification.get(
                "owner_override_may_satisfy_internal_source_evidence_requirement"
            )
            is True
        ),
        "owner_override_external_fact_authority": (
            classification.get("owner_override_external_fact_authority") is True
        ),
        "non_authoritative_source_external_fact_authority": any(
            entry.get("may_authorize_external_fact") is True
            for entry in non_authoritative_sources
        ),
        "official_source_evidence_acceptance_created": (
            classification.get("official_source_evidence_acceptance_created") is True
            or official.get("may_create_accepted_source_packet") is True
        ),
        "official_source_evidence_unlocks_connector_semantics": (
            official.get("may_unlock_connector_semantics") is True
        ),
        "candidate_seed_source_type_count": sum(
            1
            for entry in source_types
            if entry.get("may_seed_parameter_candidate") is True
        ),
        "algorithm_candidate_seed_source_type_count": sum(
            1
            for entry in source_types
            if entry.get("may_seed_algorithm_candidate") is True
        ),
        "agent_binding_request_seed_source_type_count": sum(
            1
            for entry in source_types
            if entry.get("may_seed_agent_binding_request") is True
        ),
        "retrieval_target_seed_source_type_count": sum(
            1
            for entry in source_types
            if entry.get("may_seed_retrieval_target") is True
        ),
        "owner_review_seed_source_type_count": sum(
            1
            for entry in source_types
            if entry.get("may_seed_owner_review_request") is True
        ),
        "accepted_source_review_seed_source_type_count": sum(
            1
            for entry in source_types
            if entry.get("may_seed_accepted_source_review") is True
        ),
        "future_pr71_intake_supported": all(
            entry.get("future_pr71_intake_supported") is True
            for entry in source_types
        ),
        "future_pr72_candidate_routing_supported": all(
            entry.get("future_pr72_candidate_routing_supported") is True
            for entry in candidate_entries
        ),
        "future_parameter_stack_routing_supported": all(
            entry.get("future_parameter_stack_routing_supported") is True
            for entry in candidate_entries
        ),
        "future_trade_context_routing_supported": all(
            entry.get("future_trade_context_routing_supported") is True
            for entry in candidate_entries
        ),
        "future_quantum_applicability_routing_supported": all(
            entry.get("future_quantum_applicability_routing_supported") is True
            for entry in candidate_entries
        ),
        "future_scoring_ranking_routing_supported": all(
            entry.get("future_scoring_ranking_routing_supported") is True
            for entry in candidate_entries
        ),
        "future_quantum_classical_arbitration_routing_supported": all(
            entry.get("future_quantum_classical_arbitration_routing_supported")
            is True
            for entry in candidate_entries
        ),
        "source_retrieval_executed": (
            classification.get("source_retrieval_executed") is True
        ),
        "source_acceptance_executed": (
            classification.get("source_acceptance_executed") is True
        ),
        "accepted_source_packet_created": (
            classification.get("accepted_source_packet_created") is True
        ),
        "connector_binding_created": (
            classification.get("connector_binding_created") is True
        ),
        "runtime_artifact_created": (
            classification.get("runtime_artifact_created") is True
        ),
        "live_artifact_created": classification.get("live_artifact_created") is True,
        "order_artifact_created": (
            classification.get("order_artifact_created") is True
        ),
        "profit_evidence_created": (
            classification.get("profit_evidence_created") is True
        ),
        "alpha_evidence_created": (
            classification.get("alpha_evidence_created") is True
        ),
        "latency_superiority_evidence_created": (
            classification.get("latency_superiority_evidence_created") is True
        ),
        "execution_superiority_evidence_created": (
            classification.get("execution_superiority_evidence_created") is True
        ),
        "quantum_advantage_evidence_created": (
            classification.get("quantum_advantage_evidence_created") is True
        ),
        "quantum_backend_artifact_created": (
            classification.get("quantum_backend_artifact_created") is True
        ),
        "bundle_file_present": classification.get("bundle_file_present") is True,
        "bundle_sha_present": classification.get("bundle_sha_present") is True,
        "uses_pr_number_as_authority": (
            classification.get("uses_pr_number_as_authority") is True
        ),
        "final_ready": classification.get("final_ready") is True,
        "authority_boundary_all_false": (
            classification.get("authority_boundary_all_false") is True
        ),
        "source_type_ids": list(CANONICAL_SOURCE_TYPES),
        "evidence_tiers_present": [
            tier
            for tier in ALLOWED_EVIDENCE_TIERS
            if tier in {entry.get("evidence_tier") for entry in source_types}
        ],
        "authority_classes_present": _ordered_unique(
            [
                str(entry.get("authority_class"))
                for entry in source_types
                if entry.get("authority_class") is not None
            ]
        ),
        "candidate_route_kinds_present": [
            route
            for route in ALLOWED_CANDIDATE_ROUTE_KINDS
            if route in {entry.get("candidate_route_kind") for entry in source_types}
        ],
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


REPORT_FIELDS = tuple(build_report(expected_classification_root()))


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(TOP_LEVEL_REQUIRED_FIELDS):
        failures.append("schema.required must match classifier required fields")

    defs = _mapping(schema.get("$defs"))
    source_type_id = _mapping(defs.get("source_type_id"))
    if source_type_id.get("enum") != list(CANONICAL_SOURCE_TYPES):
        failures.append("schema.$defs.source_type_id enum must be canonical")
    evidence_tier = _mapping(defs.get("evidence_tier"))
    if evidence_tier.get("enum") != list(ALLOWED_EVIDENCE_TIERS):
        failures.append("schema.$defs.evidence_tier enum must be canonical")
    route_kind = _mapping(defs.get("candidate_route_kind"))
    if route_kind.get("enum") != list(ALLOWED_CANDIDATE_ROUTE_KINDS):
        failures.append("schema.$defs.candidate_route_kind enum must be canonical")

    source_entry = _mapping(defs.get("source_type_entry"))
    if source_entry.get("additionalProperties") is not False:
        failures.append("schema.$defs.source_type_entry.additionalProperties must be false")
    if source_entry.get("required") != list(SOURCE_TYPE_FIELDS):
        failures.append("schema.$defs.source_type_entry.required must be exact")

    report_schema = _mapping(defs.get("research_provenance_report"))
    if report_schema.get("additionalProperties") is not False:
        failures.append(
            "schema.$defs.research_provenance_report.additionalProperties must be false"
        )
    if report_schema.get("required") != list(REPORT_FIELDS):
        failures.append("schema.$defs.research_provenance_report.required must be exact")

    source_types_property = _mapping(_mapping(schema.get("properties")).get("source_types"))
    if source_types_property.get("minItems") != len(CANONICAL_SOURCE_TYPES):
        failures.append("schema.source_types.minItems must be 14")
    if source_types_property.get("maxItems") != len(CANONICAL_SOURCE_TYPES):
        failures.append("schema.source_types.maxItems must be 14")
    prefix_items = source_types_property.get("prefixItems")
    if not isinstance(prefix_items, list) or len(prefix_items) != len(CANONICAL_SOURCE_TYPES):
        failures.append("schema.source_types.prefixItems must have 14 entries")
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(_mapping(schema.get("$defs")).get("research_provenance_report"))
    if not report_schema:
        return ["schema.$defs.research_provenance_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_values: dict[str, Any] = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_classification_substance": SOURCE_OF_CLASSIFICATION_SUBSTANCE,
        "classification_type": CLASSIFICATION_TYPE,
        "source_type_count": len(CANONICAL_SOURCE_TYPES),
        "required_source_type_count": len(CANONICAL_SOURCE_TYPES),
        "required_source_types_present_count": len(CANONICAL_SOURCE_TYPES),
        "missing_source_type_count": 0,
        "invalid_source_type_order_count": 0,
        "invalid_ordinal_order_count": 0,
        "authority_class_mismatch_count": 0,
        "evidence_tier_mismatch_count": 0,
        "candidate_route_kind_mismatch_count": 0,
        "forbidden_source_type_boundary_true_count": 0,
        "owner_submitted_research_source_present": True,
        "official_source_evidence_type_present": True,
        "owner_global_override_type_present": True,
        "github_repository_no_clone_no_run_required": True,
        "github_repository_no_install_required": True,
        "github_repository_secret_materialization_blocked": True,
        "uploaded_document_access_rights_attestation_required": True,
        "owner_submitted_idea_may_become_parameter_candidate": True,
        "owner_override_may_satisfy_internal_source_evidence_requirement": True,
        "owner_override_external_fact_authority": False,
        "non_authoritative_source_external_fact_authority": False,
        "official_source_evidence_acceptance_created": False,
        "official_source_evidence_unlocks_connector_semantics": False,
        "candidate_seed_source_type_count": len(CANDIDATE_SEED_SOURCE_TYPES),
        "algorithm_candidate_seed_source_type_count": len(CANDIDATE_SEED_SOURCE_TYPES),
        "agent_binding_request_seed_source_type_count": len(
            AGENT_BINDING_SEED_SOURCE_TYPES
        ),
        "retrieval_target_seed_source_type_count": len(CANONICAL_SOURCE_TYPES) - 1,
        "owner_review_seed_source_type_count": len(CANONICAL_SOURCE_TYPES),
        "accepted_source_review_seed_source_type_count": 1,
        "future_pr71_intake_supported": True,
        "future_pr72_candidate_routing_supported": True,
        "future_parameter_stack_routing_supported": True,
        "future_trade_context_routing_supported": True,
        "future_quantum_applicability_routing_supported": True,
        "future_scoring_ranking_routing_supported": True,
        "future_quantum_classical_arbitration_routing_supported": True,
        "source_type_ids": list(CANONICAL_SOURCE_TYPES),
    }
    for field in TOP_LEVEL_FALSE_FIELDS:
        expected_values[field] = False
    expected_values["authority_boundary_all_false"] = True
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is nondeterministic")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    try:
        registry = load_registry(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)
    try:
        fixture = load_fixture(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    schema, schema_failures = _load_json(root / schema_path)
    fixture_json, fixture_json_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_json_failures)

    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
        failures.extend(validate_json_schema_subset(registry, schema))
        if fixture_json is not None:
            failures.extend(validate_json_schema_subset(fixture_json, schema))

    failures.extend(validate_classification_payload(registry, label="registry"))
    failures.extend(validate_fixture_shape(fixture))
    failures.extend(validate_classification_payload(fixture, label="fixture"))

    report = build_report(registry)
    second_report = build_report(registry)
    if report != second_report:
        failures.append("generated research provenance report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    failures.extend(
        validate_current_atomicrows_bundle_state(
            root,
            label="AtomicRows research provenance evidence-tier classification",
        )
    )

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: AtomicRows research provenance classification "
            "is static routing only and creates no production readiness"
        )

    if output_path is not None and not failures:
        write_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="dev", choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(marker)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
